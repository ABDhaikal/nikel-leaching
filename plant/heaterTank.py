"""
Simulasi Preheater Tank — Sistem Leaching Nikel
Fungsi: pemanasan slurry menggunakan steam dari vessel (tanpa elemen listrik).
Model orde 1 untuk respons termal.
Output: suhu, tekanan, laju alir slurry keluar.
"""
import math
import time


def _clamp(value, min_val, max_val):
    return max(min_val, min(value, max_val))


def _vapor_pressure_bar(temp_c):
    """
    Perkiraan tekanan uap air jenuh (bar) pada suhu tertentu.
    Menggunakan pendekatan Antoine untuk air (range 1-200°C).
    """
    if temp_c <= 0:
        return 0.0
    # Antoine approximation → kPa, then convert to bar
    P_kPa = math.exp(16.3872 - 3885.70 / (temp_c + 230.170))
    return P_kPa / 100.0  # bar


def preheater_tank(
    current_temp=34.0,
    ambient_temp=34.0,
    slurry_temp_in=34.0,
    slurry_flow_in=0.0,
    current_flow_out=0.0,
    steam_temp=0.0,
    steam_flow=0.0,
    step_time=0.1,
    UA=5.0,
    volume=2.0,
    slurry_density=1400.0,
    Cp=3.5,
    tau=25.0,
    tau_flow=10.0,
    liquid_height=1.5,
):
    """
    Simulasi preheater tank orde 1 (steam-heated).

    Parameter:
        current_temp    : suhu slurry dalam tank saat ini (°C)
        ambient_temp    : suhu lingkungan referensi (°C)
        slurry_temp_in  : suhu slurry masuk dari upstream (°C)
        slurry_flow_in  : laju alir slurry masuk (m³/h)
        current_flow_out: laju alir slurry keluar saat ini (m³/h) — state
        steam_temp      : suhu steam dari vessel (°C)
        steam_flow      : laju alir steam (kg/h), 0 = belum ada steam
        step_time       : waktu simulasi (detik)
        UA              : koefisien perpindahan panas × luas (kW/°C)
        volume          : volume tank (m³)
        slurry_density  : densitas slurry (kg/m³)
        Cp              : kapasitas panas spesifik slurry (kJ/(kg·°C))
        tau             : time constant termal (detik)
        tau_flow        : time constant laju alir keluar (detik)
        liquid_height   : tinggi cairan dalam tank (m)

    Return:
        (temp_out, pressure_out, flow_out)
        - temp_out     : suhu slurry keluar (°C)
        - pressure_out : tekanan dalam tank (bar)
        - flow_out     : laju alir slurry keluar (m³/h)
    """
    # ── Step 1: Heat from steam ──
    if steam_flow > 0 and steam_temp > current_temp:
        Q_steam = UA * (steam_temp - current_temp)          # kW
    else:
        Q_steam = 0.0

    # ── Step 2: Mixing effect from incoming slurry ──
    M_tank = volume * slurry_density                        # kg
    C_tank = M_tank * Cp                                    # kJ/°C

    flow_rate_kg = slurry_flow_in * slurry_density / 3600.0 # kg/s
    Q_mixing = flow_rate_kg * Cp * (slurry_temp_in - current_temp)  # kW

    # ── Step 3: Target temperature & first-order response ──
    Q_total = Q_steam + Q_mixing                            # kW
    target_temp = current_temp + (Q_total / C_tank) * tau   # °C

    temp_out = target_temp - (target_temp - current_temp) * math.exp(-step_time / tau)

    # ── Step 4: Pressure calculation ──
    P_atm = 1.013                                           # bar
    P_hydro = (slurry_density * 9.81 * liquid_height) / 100000.0  # bar
    P_vapor = _vapor_pressure_bar(temp_out)

    pressure_out = P_atm + P_hydro + P_vapor                # bar

    # ── Step 5: Output flow (first-order lag toward input flow) ──
    flow_out = current_flow_out + (slurry_flow_in - current_flow_out) * (
        1.0 - math.exp(-step_time / tau_flow)
    )
    flow_out = max(flow_out, 0.0)

    return temp_out, pressure_out, flow_out


# ============ CONTOH PENGGUNAAN ============
if __name__ == "__main__":
    dt = 0.1
    temp = 34.0
    flow = 0.0
    ambient = 34.0
    total_time = 0.0

    mock_steam_temp = 180.0
    mock_steam_flow = 50.0
    mock_slurry_flow = 10.0
    mock_slurry_temp = 34.0

    print(f"{'Waktu (s)':<12}{'Temp (°C)':<14}{'Tekanan (bar)':<16}{'Flow Out (m³/h)'}")
    print("-" * 60)

    try:
        while True:
            temp, pressure, flow = preheater_tank(
                current_temp=temp,
                ambient_temp=ambient,
                slurry_temp_in=mock_slurry_temp,
                slurry_flow_in=mock_slurry_flow,
                current_flow_out=flow,
                steam_temp=mock_steam_temp,
                steam_flow=mock_steam_flow,
                step_time=dt,
            )
            total_time += dt

            if round(total_time % 1, 1) == 0:
                print(f"{total_time:<12.1f}{temp:<14.4f}{pressure:<16.4f}{flow:.4f}")

            time.sleep(dt)

    except KeyboardInterrupt:
        print(f"\nSimulasi dihentikan.")
        print(f"Temp akhir: {temp:.4f} °C | Tekanan: {pressure:.4f} bar | Flow: {flow:.4f} m³/h")
