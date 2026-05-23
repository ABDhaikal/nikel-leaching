"""
Simulasi Mixer Slurry dan Asam Sulfat — Sistem Leaching Nikel
Fungsi: Mencampur aliran dari pompa slurry dan pompa asam sebelum masuk ke Preheater 1.
"""
import math


def mix_acid_and_slurry(
    slurry_flow=0.0,
    slurry_temp=34.0,
    slurry_density=1400.0,
    slurry_cp=3.5,
    slurry_comp=None,
    acid_flow=0.0,
    acid_temp=34.0,
    acid_density=1840.0,
    acid_cp=1.4,
    acid_ph=1.0,
):
    """
    Menghitung parameter campuran slurry dan asam (massa, energi, dan komposisi).

    Parameter:
        slurry_flow    : Laju alir slurry (m³/h)
        slurry_temp    : Suhu slurry masuk (°C)
        slurry_density : Densitas slurry (kg/m³)
        slurry_cp      : Kapasitas panas spesifik slurry (kJ/kg·°C)
        slurry_comp    : Dictionary komposisi slurry (Ni, Fe, pH, solids, dll)
        acid_flow      : Laju alir asam sulfat (m³/h)
        acid_temp      : Suhu asam masuk (°C)
        acid_density   : Densitas asam (kg/m³)
        acid_cp        : Kapasitas panas spesifik asam (kJ/kg·°C)
        acid_ph        : pH dari asam sulfat pekat

    Return:
        (mixed_flow, mixed_temp, mixed_density, mixed_comp)
    """
    if slurry_comp is None:
        slurry_comp = {
            "nickel_pct_solid": 1.5,
            "iron_pct_solid": 8.0,
            "cobalt_pct_solid": 0.1,
            "silica_pct_solid": 15.0,
            "moisture_pct": 60.0,
            "solids_pct": 40.0,
            "ph": 7.0,
        }

    # 1. Laju alir massa (kg/h)
    slurry_mass_flow = slurry_flow * slurry_density
    acid_mass_flow = acid_flow * acid_density

    total_mass_flow = slurry_mass_flow + acid_mass_flow
    total_vol_flow = slurry_flow + acid_flow

    # Jika tidak ada aliran, kembalikan nilai default slurry
    if total_vol_flow == 0 or total_mass_flow == 0:
        return 0.0, slurry_temp, slurry_density, slurry_comp

    # 2. Densitas campuran
    mixed_density = total_mass_flow / total_vol_flow

    # 3. Suhu campuran (Neraca Energi)
    slurry_enthalpy = slurry_mass_flow * slurry_cp * slurry_temp
    acid_enthalpy = acid_mass_flow * acid_cp * acid_temp

    mixed_cp = (slurry_mass_flow * slurry_cp + acid_mass_flow * acid_cp) / total_mass_flow
    mixed_temp = (slurry_enthalpy + acid_enthalpy) / (total_mass_flow * mixed_cp)

    # Efek eksotermis: pencampuran asam sulfat pekat dengan air menghasilkan panas (heat of dilution)
    # Pendekatan sederhana: kenaikan suhu proporsional dengan rasio massa asam
    acid_mass_ratio = acid_mass_flow / total_mass_flow
    heat_of_dilution_temp_rise = acid_mass_ratio * 40.0  # Asumsi maks naik 40°C
    mixed_temp += heat_of_dilution_temp_rise

    # 4. Komposisi campuran (Pengenceran / Dilution)
    # Persentase solid terhadap total slurry berkurang karena penambahan asam cair
    dilution_factor = slurry_mass_flow / total_mass_flow

    mixed_comp = {
        # Persentase mineral terhadap partikel solid tetap tidak berubah (sebelum leaching)
        "nickel_pct_solid": slurry_comp.get("nickel_pct_solid", 0.0),
        "iron_pct_solid": slurry_comp.get("iron_pct_solid", 0.0),
        "cobalt_pct_solid": slurry_comp.get("cobalt_pct_solid", 0.0),
        "silica_pct_solid": slurry_comp.get("silica_pct_solid", 0.0),
        
        # Persentase cairan (moisture) naik, solid turun terhadap total slurry
        "moisture_pct": round(slurry_comp.get("moisture_pct", 0.0) * dilution_factor + (1 - dilution_factor) * 100.0, 2),
        "solids_pct": round(slurry_comp.get("solids_pct", 0.0) * dilution_factor, 2),
    }

    # 5. pH campuran (Pendekatan ion H+)
    h_slurry = 10 ** (-slurry_comp.get("ph", 7.0))
    h_acid = 10 ** (-acid_ph)

    # Rata-rata konsentrasi ion H+ berdasarkan volume
    h_mixed = (h_slurry * slurry_flow + h_acid * acid_flow) / total_vol_flow

    if h_mixed > 0:
        mixed_comp["ph"] = round(-math.log10(h_mixed), 2)
    else:
        mixed_comp["ph"] = 7.0

    return total_vol_flow, mixed_temp, mixed_density, mixed_comp


# ============ CONTOH PENGGUNAAN ============
if __name__ == "__main__":
    print("=== Uji Coba Mixer Slurry dan Acid ===")
    
    # Simulasi 100 m³/h slurry dan 10 m³/h asam sulfat
    test_slurry_flow = 100.0
    test_acid_flow = 10.0
    
    # Komposisi slurry awal
    awal_comp = {
        "nickel_pct_solid": 1.5,
        "iron_pct_solid": 8.0,
        "cobalt_pct_solid": 0.1,
        "silica_pct_solid": 15.0,
        "moisture_pct": 60.0,
        "solids_pct": 40.0,
        "ph": 6.5,
    }

    flow, temp, density, comp = mix_acid_and_slurry(
        slurry_flow=test_slurry_flow,
        slurry_comp=awal_comp,
        acid_flow=test_acid_flow
    )

    print(f"\n--- Input ---")
    print(f"Slurry : {test_slurry_flow} m³/h | 34.0 °C | pH {awal_comp['ph']} | Solid {awal_comp['solids_pct']}%")
    print(f"Asam   : {test_acid_flow} m³/h | 34.0 °C | pH 1.0")
    
    print(f"\n--- Output (Mixed) ---")
    print(f"Flow    : {flow:.2f} m³/h")
    print(f"Suhu    : {temp:.2f} °C (Termasuk efek eksotermis)")
    print(f"Densitas: {density:.2f} kg/m³")
    print(f"pH      : {comp['ph']}")
    print(f"Solid   : {comp['solids_pct']}%")
    print(f"Liquid  : {comp['moisture_pct']}%")
