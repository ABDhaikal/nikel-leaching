from actuator import reactor_heater

"""
Simulasi Reaktor Plant — Sistem Leaching Nikel
Fungsi: menggabungkan mixing slurry masuk + pemanasan listrik (reaktor_pemanasan actuator).
Output: suhu, tekanan, laju alir slurry keluar.
"""
import math
import time


def _clamp(value, min_val, max_val):
    return max(min_val, min(value, max_val))


def _vapor_pressure_bar(temp_c):
    """
    Perkiraan tekanan uap air jenuh (bar) pada suhu tertentu.
    """
    if temp_c <= 0:
        return 0.0
    P_kPa = math.exp(16.3872 - 3885.70 / (temp_c + 230.170))
    return P_kPa / 100.0


def reactor_plant(
    current_temp=34.0,
    ambient_temp=34.0,
    slurry_temp_in=34.0,
    slurry_flow_in=0.0,
    current_flow_out=0.0,
    voltage=0.0,
    step_time=0.1,
    rated_voltage=380.0,
    resistance=8.0,
    tau_heater=30.0,
    K=12.0,
    efficiency=0.85,
    volume=3.0,
    slurry_density=1400.0,
    Cp=3.5,
    tau_mixing=20.0,
    tau_flow=10.0,
    liquid_height=2.0,
):
    """
    Simulasi reaktor plant: mixing slurry masuk + pemanasan listrik.

    Parameter:
        current_temp    : suhu slurry dalam reaktor saat ini (°C)
        ambient_temp    : suhu lingkungan referensi (°C)
        slurry_temp_in  : suhu slurry masuk dari upstream (°C)
        slurry_flow_in  : laju alir slurry masuk (m³/h)
        current_flow_out: laju alir slurry keluar saat ini (m³/h) — state
        voltage         : tegangan ke elemen pemanas (V), diatur PID
        step_time       : waktu simulasi (detik)
        rated_voltage   : tegangan nominal heater (V)
        resistance      : resistansi elemen pemanas (Ohm)
        tau_heater      : time constant heater (detik)
        K               : gain heater (°C per kW)
        efficiency      : efisiensi termal heater (0-1)
        volume          : volume reaktor (m³)
        slurry_density  : densitas slurry (kg/m³)
        Cp              : kapasitas panas spesifik slurry (kJ/(kg·°C))
        tau_mixing      : time constant pencampuran (detik)
        tau_flow        : time constant laju alir keluar (detik)
        liquid_height   : tinggi cairan dalam reaktor (m)

    Return:
        (temp_out, pressure_out, flow_out)
        - temp_out     : suhu slurry keluar reaktor (°C)
        - pressure_out : tekanan dalam reaktor (bar)
        - flow_out     : laju alir slurry keluar (m³/h)
    """
    # ── Step 1: Mixing incoming slurry with tank contents ──
    flow_rate_kg = slurry_flow_in * slurry_density / 3600.0
    M_tank = volume * slurry_density

    if M_tank > 0 and flow_rate_kg > 0:
        mix_fraction = _clamp((flow_rate_kg * step_time) / M_tank, 0.0, 1.0)
    else:
        mix_fraction = 0.0

    temp_mixed = current_temp + mix_fraction * (slurry_temp_in - current_temp)

    # ── Step 2: Apply electric heating via actuator ──
    temp_heated = reactor_heater.reaktor_pemanasan(
        current_temp=temp_mixed,
        ambient_temp=ambient_temp,
        voltage=voltage,
        step_time=step_time,
        resistance=resistance,
        tau=tau_heater,
        K=K,
        efficiency=efficiency,
    )

    # ── Step 3: Pressure calculation ──
    P_atm = 1.013
    P_hydro = (slurry_density * 9.81 * liquid_height) / 100000.0
    P_vapor = _vapor_pressure_bar(temp_heated)

    pressure_out = P_atm + P_hydro + P_vapor

    # ── Step 4: Output flow (first-order lag toward input flow) ──
    flow_out = current_flow_out + (slurry_flow_in - current_flow_out) * (
        1.0 - math.exp(-step_time / tau_flow)
    )
    flow_out = max(flow_out, 0.0)

    return temp_heated, pressure_out, flow_out


# ============ CONTOH PENGGUNAAN ============
if __name__ == "__main__":
    dt = 0.1
    temp = 34.0
    flow = 0.0
    ambient = 34.0
    total_time = 0.0

    mock_slurry_temp_in = 80.0
    mock_slurry_flow_in = 10.0
    mock_voltage = 380.0

    print(f"{'Waktu (s)':<12}{'Temp (°C)':<14}{'Tekanan (bar)':<16}{'Flow Out (m³/h)':<18}{'Voltage (V)'}")
    print("-" * 75)

    try:
        while True:
            temp, pressure, flow = reactor_plant(
                current_temp=temp,
                ambient_temp=ambient,
                slurry_temp_in=mock_slurry_temp_in,
                slurry_flow_in=mock_slurry_flow_in,
                current_flow_out=flow,
                voltage=mock_voltage,
                step_time=dt,
            )
            total_time += dt

            if round(total_time % 1, 1) == 0:
                print(f"{total_time:<12.1f}{temp:<14.4f}{pressure:<16.4f}{flow:<18.4f}{mock_voltage:.0f}")

            time.sleep(dt)

    except KeyboardInterrupt:
        print(f"\nSimulasi dihentikan.")
        print(f"Temp: {temp:.4f} °C | Tekanan: {pressure:.4f} bar | Flow: {flow:.4f} m³/h")
