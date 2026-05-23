"""
Simulasi Sederhana Reaktor Pemanasan - Sistem Leaching Nikel
Fungsi: input voltage dan step time → output temperatur akhir
"""
import math
import time


def reaktor_pemanasan(current_temp=34, ambient_temp=34, voltage=380, step_time=0.1,
                      resistance=8, tau=30, K=12, efficiency=0.85):
    """
    Simulasi reaktor pemanasan orde 1.

    Parameter:
        current_temp: suhu reaktor saat ini (°C) - berubah tiap iterasi
        ambient_temp: suhu lingkungan tetap (°C) - referensi untuk target
        voltage     : tegangan input (V)
        step_time   : waktu simulasi (detik)
        resistance  : resistansi heater (Ohm)
        tau         : time constant (detik)
        K           : gain (°C per kW)
        efficiency  : efisiensi thermal

    Return:
        temperatur akhir (°C)
    """
    power = (voltage ** 2) / resistance / 1000  # kW
    heat_input = power * efficiency
    target_temp = ambient_temp + K * heat_input  # pakai ambient tetap, bukan current_temp

    # Respons orde 1: T(t) = T_target - (T_target - T_awal) * e^(-t/tau)
    temp_akhir = target_temp - (target_temp - current_temp) * math.exp(-step_time / tau)
    return temp_akhir


# ============ CONTOH PENGGUNAAN ============
if __name__ == "__main__":
    V = 380         # Volt
    dt = 0.1        # detik (step time)
    temp = 34.0     # suhu awal (°C)
    ambient = 34.0  # suhu lingkungan tetap (°C)
    total_time = 0

    print(f"{'Waktu (s)':<12}{'Temperatur (°C)':<20}{'Target (°C)':<15}{'Daya (kW)'}")
    print("-" * 60)

    try:
        while True:
            temp = reaktor_pemanasan(current_temp=temp, ambient_temp=ambient,
                                     voltage=V, step_time=dt)
            total_time += dt

            # Print setiap 1 detik
            if round(total_time % 1, 1) == 0:
                power = (V ** 2) / 8 / 1000
                target = ambient + 12 * power * 0.85
                print(f"{total_time:<12.1f}{temp:<20.4f}{target:<15.1f}{power:.2f}")

            time.sleep(dt)

    except KeyboardInterrupt:
        print(f"\nSimulasi dihentikan.")
        print(f"Temperatur akhir: {temp:.4f} °C")
        print(f"Total waktu: {total_time:.1f} s")