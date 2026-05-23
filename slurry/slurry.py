"""
Slurry generator untuk simulasi proses leaching nikel.
Menghasilkan komposisi slurry acak per batch.
"""
import random
import time


def _clamp(value, min_value, max_value):
	return max(min_value, min(value, max_value))


def generate_slurry(
	nickel_range=(0.8, 2.5),
	iron_range=(6.0, 12.0),
	cobalt_range=(0.05, 0.2),
	silica_range=(10.0, 20.0),
	moisture_range=(30.0, 45.0),
	ph_range=(1.5, 3.0),
	density_range=(1.2, 1.6),
):
	"""
	Generate satu sample slurry dengan randomisasi kandungan.

	Semua komposisi logam/silika dinyatakan dalam persen berat
	terhadap solid. Moisture adalah persen berat slurry total.
	"""
	nickel = random.uniform(*nickel_range)
	iron = random.uniform(*iron_range)
	cobalt = random.uniform(*cobalt_range)
	silica = random.uniform(*silica_range)

	# Normalisasi komponen solid agar tidak melebihi 100%
	total_solids = nickel + iron + cobalt + silica
	if total_solids > 100.0:
		scale = 100.0 / total_solids
		nickel *= scale
		iron *= scale
		cobalt *= scale
		silica *= scale

	moisture = _clamp(random.uniform(*moisture_range), 0.0, 80.0)
	solids_fraction = _clamp(100.0 - moisture, 0.0, 100.0)

	ph = random.uniform(*ph_range)
	density = random.uniform(*density_range)

	return {
		"nickel_pct_solid": round(nickel, 3),
		"iron_pct_solid": round(iron, 3),
		"cobalt_pct_solid": round(cobalt, 3),
		"silica_pct_solid": round(silica, 3),
		"moisture_pct": round(moisture, 2),
		"solids_pct": round(solids_fraction, 2),
		"ph": round(ph, 2),
		"density": round(density, 3),
	}


if __name__ == "__main__":
	try:
		while True:
			sample = generate_slurry()
			print(
				"Slurry | "
				f"Ni {sample['nickel_pct_solid']}% | "
				f"Fe {sample['iron_pct_solid']}% | "
				f"Co {sample['cobalt_pct_solid']}% | "
				f"SiO2 {sample['silica_pct_solid']}% | "
				f"Moist {sample['moisture_pct']}% | "
				f"Solids {sample['solids_pct']}% | "
				f"pH {sample['ph']} | "
				f"rho {sample['density']}"
			)
			time.sleep(2)
	except KeyboardInterrupt:
		print("\nGenerator slurry dihentikan.")
