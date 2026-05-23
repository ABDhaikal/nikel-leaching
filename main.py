"""
Main Simulation Loop — Sistem Leaching Nikel (Open-Loop / Tanpa Controller)
Alur: Pump(Acid+Slurry) -> Mixer -> Preheater 1 -> Preheater 2 -> Reactor 1 -> Reactor 2 -> Vessel 1 -> Vessel 2
"""
import time

# Import aktuator
from actuator.pump import pump_actuator

# Import plant
from plant.heaterTank import preheater_tank
from plant.reactor import reactor_plant
from plant.vessel import vessel_flash_tank

# Import slurry
from slurry.nikel_slurry import generate_slurry
from slurry.mixed_slurry import mix_acid_and_slurry

# Import MQTT
import connection.mqtt as mqtt

# Konfigurasi simulasi
DT = 0.1  # detik

def main():
    print("Memulai Simulasi Leaching Nikel (Open-Loop)...")
    
    # 1. Jalankan MQTT Client di background
    mqtt_client = mqtt.MQTTClient(mqtt.BROKER, mqtt.PORT, mqtt.CLIENT_ID)
    mqtt_client.connect()
    
    # Beri waktu MQTT connect
    time.sleep(1)

    # 2. Inisialisasi State Variables
    # -- Pumps --
    p_acid_flow = 0.0
    p_slurry_flow = 0.0
    
    # -- Preheater 1 --
    ph1_temp = 34.0
    ph1_flow = 0.0
    
    # -- Preheater 2 --
    ph2_temp = 34.0
    ph2_flow = 0.0
    
    # -- Reactor 1 --
    r1_temp = 34.0
    r1_flow = 0.0
    
    # -- Reactor 2 --
    r2_temp = 34.0
    r2_flow = 0.0
    
    # -- Vessel 1 --
    v1_temp = 34.0
    v1_flow = 0.0
    v1_steam_temp = 0.0
    v1_steam_flow = 0.0
    
    # -- Vessel 2 --
    v2_temp = 34.0
    v2_flow = 0.0
    v2_steam_temp = 0.0
    v2_steam_flow = 0.0

    total_time = 0.0
    last_publish_time = 0.0

    print("Simulasi berjalan. Tekan Ctrl+C untuk berhenti.")
    print("-" * 80)
    
    try:
        while True:
            # ─────────────────────────────────────────────────────────────
            # A. BACA INPUT DARI AVEVA (atau gunakan default)
            # Karena tidak ada controller, nilai dari AVEVA dianggap sebagai 
            # tegangan langsung (0-380V) untuk pemanas dan pompa.
            # ─────────────────────────────────────────────────────────────
            v_pump_acid   = float(mqtt.setpoint_pump_acid) if mqtt.setpoint_pump_acid is not None else 380.0
            v_pump_slurry = float(mqtt.setpoint_pump_slurry) if mqtt.setpoint_pump_slurry is not None else 380.0
            v_reactor1    = float(mqtt.setpoint_suhu_reactor1) if mqtt.setpoint_suhu_reactor1 is not None else 380.0
            v_reactor2    = float(mqtt.setpoint_suhu_reactor2) if mqtt.setpoint_suhu_reactor2 is not None else 380.0

            # ─────────────────────────────────────────────────────────────
            # B. AKTUATOR POMPA
            # ─────────────────────────────────────────────────────────────
            # Max flow disesuaikan agar rasio masuk akal (slurry : acid = 100 : 10)
            p_acid_flow = pump_actuator(voltage=v_pump_acid, current_flow=p_acid_flow, step_time=DT, max_flow=10.0)
            p_slurry_flow = pump_actuator(voltage=v_pump_slurry, current_flow=p_slurry_flow, step_time=DT, max_flow=100.0)

            # ─────────────────────────────────────────────────────────────
            # C. MIXER
            # ─────────────────────────────────────────────────────────────
            base_slurry = generate_slurry()
            mixed_flow, mixed_temp, mixed_density, mixed_comp = mix_acid_and_slurry(
                slurry_flow=p_slurry_flow,
                slurry_comp=base_slurry,
                acid_flow=p_acid_flow
            )

            # ─────────────────────────────────────────────────────────────
            # D. PREHEATER 1 (Dipanaskan oleh Steam dari Vessel 2)
            # ─────────────────────────────────────────────────────────────
            ph1_temp, ph1_press, ph1_flow = preheater_tank(
                current_temp=ph1_temp,
                slurry_temp_in=mixed_temp,
                slurry_flow_in=mixed_flow,
                current_flow_out=ph1_flow,
                steam_temp=v2_steam_temp,  # Feed-back dari Vessel 2 (loop sebelumnya)
                steam_flow=v2_steam_flow,
                step_time=DT
            )

            # ─────────────────────────────────────────────────────────────
            # E. PREHEATER 2 (Dipanaskan oleh Steam dari Vessel 1)
            # ─────────────────────────────────────────────────────────────
            ph2_temp, ph2_press, ph2_flow = preheater_tank(
                current_temp=ph2_temp,
                slurry_temp_in=ph1_temp,
                slurry_flow_in=ph1_flow,
                current_flow_out=ph2_flow,
                steam_temp=v1_steam_temp,  # Feed-back dari Vessel 1 (loop sebelumnya)
                steam_flow=v1_steam_flow,
                step_time=DT
            )

            # ─────────────────────────────────────────────────────────────
            # F. REACTOR 1 (Pemanas Listrik)
            # ─────────────────────────────────────────────────────────────
            r1_temp, r1_press, r1_flow = reactor_plant(
                current_temp=r1_temp,
                slurry_temp_in=ph2_temp,
                slurry_flow_in=ph2_flow,
                current_flow_out=r1_flow,
                voltage=v_reactor1,
                step_time=DT
            )

            # ─────────────────────────────────────────────────────────────
            # G. REACTOR 2 (Pemanas Listrik)
            # ─────────────────────────────────────────────────────────────
            r2_temp, r2_press, r2_flow = reactor_plant(
                current_temp=r2_temp,
                slurry_temp_in=r1_temp,
                slurry_flow_in=r1_flow,
                current_flow_out=r2_flow,
                voltage=v_reactor2,
                step_time=DT
            )

            # ─────────────────────────────────────────────────────────────
            # H. VESSEL 1 (Flash Tank -> Steam ke Preheater 2)
            # ─────────────────────────────────────────────────────────────
            # Tekanan operasi lebih rendah dari reactor agar terjadi flashing (misal 5 bar)
            v1_temp, v1_press, v1_flow, v1_steam_temp, v1_steam_flow = vessel_flash_tank(
                current_temp=v1_temp,
                current_flow_out=v1_flow,
                slurry_temp_in=r2_temp,
                slurry_flow_in=r2_flow,
                operating_pressure=5.0,  
                step_time=DT
            )

            # ─────────────────────────────────────────────────────────────
            # I. VESSEL 2 (Flash Tank -> Steam ke Preheater 1)
            # ─────────────────────────────────────────────────────────────
            # Tekanan operasi lebih rendah dari Vessel 1 (misal 2 bar)
            v2_temp, v2_press, v2_flow, v2_steam_temp, v2_steam_flow = vessel_flash_tank(
                current_temp=v2_temp,
                current_flow_out=v2_flow,
                slurry_temp_in=v1_temp,
                slurry_flow_in=v1_flow,
                operating_pressure=2.0,  
                step_time=DT
            )

            # ─────────────────────────────────────────────────────────────
            # J. PUBLISH KE MQTT (Setiap 2 Detik)
            # ─────────────────────────────────────────────────────────────
            total_time += DT
            
            if total_time - last_publish_time >= 2.0:
                status = 1 if p_slurry_flow > 0 else 0
                
                # Preheaters
                mqtt_client.send_message(mqtt.TOPIC_PREHEATER1_SUHU, round(ph1_temp, 2))
                mqtt_client.send_message(mqtt.TOPIC_PREHEATER1_TEKANAN, round(ph1_press, 2))
                mqtt_client.send_message(mqtt.TOPIC_SLURRY_FLOWP_P1, round(ph1_flow, 2))
                mqtt_client.send_message(mqtt.TOPIC_PREHEATER1_STATUS, status)

                mqtt_client.send_message(mqtt.TOPIC_PREHEATER2_SUHU, round(ph2_temp, 2))
                mqtt_client.send_message(mqtt.TOPIC_PREHEATER2_TEKANAN, round(ph2_press, 2))
                mqtt_client.send_message(mqtt.TOPIC_SLURRY_FLOWP_P2, round(ph2_flow, 2))
                mqtt_client.send_message(mqtt.TOPIC_PREHEATER2_STATUS, status)

                # Reactors
                mqtt_client.send_message(mqtt.TOPIC_REACTOR1_SUHU, round(r1_temp, 2))
                mqtt_client.send_message(mqtt.TOPIC_REACTOR1_TEKANAN, round(r1_press, 2))
                mqtt_client.send_message(mqtt.TOPIC_SLURRY_FLOWP_B1, round(r1_flow, 2))
                mqtt_client.send_message(mqtt.TOPIC_REACTOR1_STATUS, status)

                mqtt_client.send_message(mqtt.TOPIC_REACTOR2_SUHU, round(r2_temp, 2))
                mqtt_client.send_message(mqtt.TOPIC_REACTOR2_TEKANAN, round(r2_press, 2))
                mqtt_client.send_message(mqtt.TOPIC_SLURRY_FLOWP_B2, round(r2_flow, 2))
                mqtt_client.send_message(mqtt.TOPIC_REACTOR2_STATUS, status)

                # Vessels
                mqtt_client.send_message(mqtt.TOPIC_VESSEL1_SUHU, round(v1_temp, 2))
                mqtt_client.send_message(mqtt.TOPIC_VESSEL1_TEKANAN, round(v1_press, 2))
                mqtt_client.send_message(mqtt.TOPIC_SLURRY_FLOWP_V1, round(v1_flow, 2))
                mqtt_client.send_message(mqtt.TOPIC_VESSEL1_STATUS, status)

                mqtt_client.send_message(mqtt.TOPIC_VESSEL2_SUHU, round(v2_temp, 2))
                mqtt_client.send_message(mqtt.TOPIC_VESSEL2_TEKANAN, round(v2_press, 2))
                mqtt_client.send_message(mqtt.TOPIC_SLURRY_FLOWP_V2, round(v2_flow, 2))
                mqtt_client.send_message(mqtt.TOPIC_VESSEL2_STATUS, status)
                
                # Pumps
                mqtt_client.send_message(mqtt.TOPIC_PUMP_ACID, round(p_acid_flow, 2))
                mqtt_client.send_message(mqtt.TOPIC_PUMP_SLURRY, round(p_slurry_flow, 2))

                # Console log singkat
                print(
                    f"\n[Time: {total_time:.1f}s] Flow: {mixed_flow:.1f} m³/h\n"
                    f"-> PH1: {ph1_temp:.1f}°C | PH2: {ph2_temp:.1f}°C | "
                    f"R1: {r1_temp:.1f}°C | R2: {r2_temp:.1f}°C | "
                    f"V1: {v1_temp:.1f}°C (Steam: {v1_steam_temp:.1f}°C) | "
                    f"V2: {v2_temp:.1f}°C (Steam: {v2_steam_temp:.1f}°C)"
                )
                
                last_publish_time = total_time

            # Tunggu real-time
            time.sleep(DT)

    except KeyboardInterrupt:
        print("\nSimulasi dihentikan.")
        mqtt_client.client.loop_stop()
        mqtt_client.client.disconnect()


if __name__ == "__main__":
    main()
