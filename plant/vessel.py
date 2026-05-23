"""
Simulasi Vessel (Flash Tank) — Sistem Leaching Nikel
Fungsi: penurunan tekanan slurry panas → menghasilkan steam (flashing).
Steam output dikirim ke preheater (heat recovery).
Output: suhu, tekanan, laju alir slurry keluar, suhu steam, laju alir steam.
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


def _saturation_temp(pressure_bar):
    """
    Perkiraan suhu saturasi (°C) pada tekanan tertentu (bar).
    Inverse Antoine equation.
    """
    P_kPa = pressure_bar * 100.0
    if P_kPa <= 0:
        return 0.0
    T_sat = 3993.0 / (11.78 - math.log(P_kPa)) - 233.0
    return T_sat


def vessel_flash_tank(
    current_temp=34.0,
    current_flow_out=0.0,
    slurry_temp_in=34.0,
    slurry_flow_in=0.0,
    operating_pressure=2.0,
    step_time=0.1,
    volume=4.0,
    slurry_density=1400.0,
    Cp=3.5,
    latent_heat=2260.0,
    moisture_fraction=0.35,
    tau=20.0,
    tau_flow=10.0,
    liquid_height=2.0,
):
    """
    Simulasi vessel flash tank.

    Parameter:
        current_temp      : suhu cairan dalam vessel saat ini (°C)
        current_flow_out  : laju alir slurry keluar saat ini (m³/h) — state
        slurry_temp_in    : suhu slurry masuk dari upstream (°C)
        slurry_flow_in    : laju alir slurry masuk (m³/h)
        operating_pressure: tekanan operasi vessel (bar) — lebih rendah dari upstream
        step_time         : waktu simulasi (detik)
        volume            : volume vessel (m³)
        slurry_density    : densitas slurry (kg/m³)
        Cp                : kapasitas panas spesifik slurry (kJ/(kg·°C))
        latent_heat       : panas laten penguapan air (kJ/kg)
        moisture_fraction : fraksi air dalam slurry (0-1)
        tau               : time constant termal (detik)
        tau_flow          : time constant laju alir keluar (detik)
        liquid_height     : tinggi cairan dalam vessel (m)

    Return:
        (temp_out, pressure_out, flow_out, steam_temp, steam_flow)
        - temp_out     : suhu cairan slurry dalam vessel (°C)
        - pressure_out : tekanan dalam vessel (bar)
        - flow_out     : laju alir slurry keluar (m³/h)
        - steam_temp   : suhu steam yang dihasilkan (°C)
        - steam_flow   : laju alir steam (kg/h)
    """
    # ── Step 1: Saturation temperature at operating pressure ──
    T_sat = _saturation_temp(operating_pressure)

    # ── Step 2: Mix incoming slurry with tank contents ──
    M_tank = volume * slurry_density                            # kg
    flow_rate_kg = slurry_flow_in * slurry_density / 3600.0     # kg/s

    if M_tank > 0 and flow_rate_kg > 0:
        mix_fraction = _clamp((flow_rate_kg * step_time) / M_tank, 0.0, 1.0)
    else:
        mix_fraction = 0.0

    temp_mixed = current_temp + mix_fraction * (slurry_temp_in - current_temp)

    # ── Step 3: Flash calculation ──
    if temp_mixed > T_sat and slurry_flow_in > 0:
        # Excess heat available for flashing
        Q_excess = M_tank * Cp * (temp_mixed - T_sat)           # kJ

        # Maximum water available
        M_water = M_tank * moisture_fraction                    # kg

        # Steam generated (capped at 5% of water per step for stability)
        steam_mass = min(Q_excess / latent_heat, M_water * 0.05)  # kg
        steam_mass = max(steam_mass, 0.0)

        # Steam properties
        steam_temp = T_sat
        steam_flow = (steam_mass / step_time) * 3600.0          # kg/h

        # Liquid cools due to latent heat removal
        Q_removed = steam_mass * latent_heat                    # kJ
        if M_tank * Cp > 0:
            temp_liquid = temp_mixed - Q_removed / (M_tank * Cp)
        else:
            temp_liquid = temp_mixed
    else:
        # No flashing — slurry below boiling point
        steam_temp = temp_mixed
        steam_flow = 0.0
        temp_liquid = temp_mixed

    # ── Step 4: First-order thermal lag ──
    temp_out = temp_liquid - (temp_liquid - current_temp) * math.exp(-step_time / tau)

    # ── Step 5: Pressure calculation ──
    P_atm = 1.013
    P_hydro = (slurry_density * 9.81 * liquid_height) / 100000.0
    P_vapor = _vapor_pressure_bar(temp_out)
    pressure_out = P_atm + P_hydro + P_vapor

    # ── Step 6: Output liquid flow (first-order lag) ──
    flow_out = current_flow_out + (slurry_flow_in - current_flow_out) * (
        1.0 - math.exp(-step_time / tau_flow)
    )
    flow_out = max(flow_out, 0.0)

    return temp_out, pressure_out, flow_out, steam_temp, steam_flow


# ============ CONTOH PENGGUNAAN ============
if __name__ == "__main__":
    dt = 0.1
    temp = 34.0
    flow = 0.0
    total_time = 0.0

    # Simulasi: slurry panas masuk dari reactor pada 250°C
    mock_slurry_temp_in = 250.0
    mock_slurry_flow_in = 10.0
    mock_operating_pressure = 2.0   # bar

    T_sat = _saturation_temp(mock_operating_pressure)
    print(f"Tekanan operasi: {mock_operating_pressure} bar | T saturasi: {T_sat:.1f} °C")
    print(f"{'Waktu (s)':<12}{'Temp (°C)':<14}{'Tekanan (bar)':<16}{'Flow (m³/h)':<14}{'Steam T (°C)':<14}{'Steam (kg/h)'}")
    print("-" * 85)

    try:
        while True:
            temp, pressure, flow, s_temp, s_flow = vessel_flash_tank(
                current_temp=temp,
                current_flow_out=flow,
                slurry_temp_in=mock_slurry_temp_in,
                slurry_flow_in=mock_slurry_flow_in,
                operating_pressure=mock_operating_pressure,
                step_time=dt,
            )
            total_time += dt

            if round(total_time % 1, 1) == 0:
                print(f"{total_time:<12.1f}{temp:<14.4f}{pressure:<16.4f}{flow:<14.4f}{s_temp:<14.1f}{s_flow:.2f}")

            time.sleep(dt)

    except KeyboardInterrupt:
        print(f"\nSimulasi dihentikan.")
        print(f"Temp: {temp:.4f} °C | Tekanan: {pressure:.4f} bar | Flow: {flow:.4f} m³/h")
        print(f"Steam: {s_temp:.1f} °C | {s_flow:.2f} kg/h")
