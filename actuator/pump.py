"""
Simulasi sederhana aktuator pompa.
Fungsi: input voltage dan step time -> output flow rate.
"""
import time


def pump_actuator(
	voltage=380.0,
	current_flow=0.0,
	step_time=0.1,
	rated_voltage=380.0,
	max_flow=100.0,
	tau=8.0,
	efficiency=0.9,
	deadband=0.0,
):
	"""
	Simulasi pompa orde 1.

	Parameter:
		voltage      : tegangan input (V)
		current_flow : laju alir saat ini (mis. m3/h)
		step_time    : waktu simulasi (detik)
		rated_voltage: tegangan nominal (V)
		max_flow     : laju alir maksimum pada tegangan nominal
		tau          : time constant (detik)
		efficiency   : efisiensi pompa (0-1)
		deadband     : tegangan minimum agar pompa mulai bekerja

	Return:
		laju alir akhir
	"""
	if voltage < deadband:
		target_flow = 0.0
	else:
		ratio = max(0.0, min(voltage / rated_voltage, 1.2))
		target_flow = max_flow * ratio * efficiency

	# Respons orde 1 menuju target
	flow_akhir = target_flow - (target_flow - current_flow) * (2.718281828 ** (-step_time / tau))
	return max(flow_akhir, 0.0)


if __name__ == "__main__":
	V = 380.0
	dt = 0.1
	flow = 0.0
	total_time = 0.0

	print(f"{'Waktu (s)':<12}{'Flow (unit)':<16}{'Target (unit)':<16}{'Voltage (V)'}")
	print("-" * 60)

	try:
		while True:
			flow = pump_actuator(voltage=V, current_flow=flow, step_time=dt)
			total_time += dt

			if round(total_time % 1, 1) == 0:
				ratio = max(0.0, min(V / 380.0, 1.2))
				target = 100.0 * ratio * 0.9
				print(f"{total_time:<12.1f}{flow:<16.4f}{target:<16.2f}{V:.0f}")

			time.sleep(dt)
	except KeyboardInterrupt:
		print("\nSimulasi dihentikan.")
		print(f"Flow akhir: {flow:.4f}")
		print(f"Total waktu: {total_time:.1f} s")