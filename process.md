# Nickel Leaching Simulation — Step-by-Step Procedure

## Process Overview

```
  ┌───────────┐
  │ PUMP ACID │────┐
  └───────────┘    │    ┌──────────────┐    ┌──────────────┐    ┌────────────────┐    ┌────────────────┐    ┌──────────┐    ┌──────────┐
                   ├───►│ PREHEATER 1  │───►│ PREHEATER 2  │───►│REACTOR HEATER 1│───►│REACTOR HEATER 2│───►│ VESSEL 1 │───►│ VESSEL 2 │
  ┌───────────┐    │    │(steam from   │    │(steam from   │    │(electric       │    │(electric       │    │(flash    │    │(flash    │
  │PUMP SLURRY│────┘    │ Vessel 2)    │    │ Vessel 1)    │    │ element)       │    │ element)       │    │ tank)    │    │ tank)    │
  └───────────┘         └──────────────┘    └──────────────┘    └────────────────┘    └────────────────┘    └──────────┘    └──────────┘
                              ▲                   ▲                                                             │              │
                              │                   │                                                             │              │
                              │                   └──────────────── steam ──────────────────────────────────────┘              │
                              │                                                                                                │
                              └──────────────────────────── steam ─────────────────────────────────────────────────────────────┘
```

### Flow Path (Serial)
```
Pump Acid ──┐
            ├──► COMBINED ──► Preheater 1 ──► Preheater 2 ──► Reactor Heater 1 ──► Reactor Heater 2 ──► Vessel 1 ──► Vessel 2
Pump Slurry─┘
```

### Steam Cross-Connection (Heat Recovery)
- **Vessel 1** steam output → heats **Preheater 2**
- **Vessel 2** steam output → heats **Preheater 1**

This creates a counter-current heat recovery: the hottest vessel (Vessel 2, end of line) sends steam back to the first preheater, and Vessel 1 sends steam to the second preheater.

---

## Current Code Status

### ✅ Already Built
| Module | File | Status |
|--------|------|--------|
| Pump actuator | `actuator/pump.py` | Complete — first-order response model |
| Reactor heater actuator | `actuator/reactor_heater.py` | Complete — first-order thermal model |
| Slurry generator | `slurry/slurry.py` | Complete — random composition per batch |
| MQTT connection | `connection/mqtt.py` | Complete — all topics defined, pub/sub working |
| Reactor (plant) | `plant/reactor.py` | Minimal — only calls `reaktor_pemanasan()` |

### ❌ Not Yet Built
| Module | File | Status |
|--------|------|--------|
| Heater Tank (preheater plant) | `plant/heaterTank.py` | Empty |
| Vessel (flash tank plant) | `plant/vessel.py` | Empty |
| Controller logic | `controller/` | Empty directory |
| Main simulation loop | `main.py` | Empty |

---

## Step-by-Step Implementation Procedure

### STEP 1: Complete the Preheater Plant Model (`plant/heaterTank.py`)

**Purpose:** Model the preheater as a heat-exchanger tank that receives incoming slurry and heats it using steam from a vessel (no electric element — steam-heated only).

**What to implement:**
1. Define `preheater_tank()` function with parameters:
   - `current_temp` — current slurry temperature inside preheater (°C)
   - `steam_temp` — temperature of incoming steam from the cross-connected vessel (°C)
   - `steam_flow` — flow rate of steam (determines heat transfer rate)
   - `slurry_flow_in` — flow rate of incoming slurry (m³/h)
   - `slurry_temp_in` — temperature of incoming slurry (°C)
   - `volume` — tank volume (m³)
   - `UA` — overall heat transfer coefficient × area (kW/°C)
   - `step_time` — simulation time step (s)
2. Model the energy balance:
   - Heat gained from steam: `Q_steam = UA * (steam_temp - current_temp)`
   - Heat carried in by slurry: mixing of incoming cold slurry with tank contents
   - Calculate `dT/dt` and update temperature
3. Return: `output_temp`, `output_pressure`, `output_flow`
4. **Preheater 1** receives steam from **Vessel 2**
5. **Preheater 2** receives steam from **Vessel 1**

---

### STEP 2: Complete the Vessel Plant Model (`plant/vessel.py`)

**Purpose:** Model the vessel as a flash tank where hot slurry from Reactor Heater 2 (via Vessel 1) releases steam due to pressure drop.

**What to implement:**
1. Define `vessel_flash_tank()` function with parameters:
   - `current_temp` — current temperature in the vessel (°C)
   - `current_pressure` — current pressure in the vessel (bar)
   - `inlet_temp` — temperature of slurry entering (°C)
   - `inlet_flow` — flow rate of slurry entering (m³/h)
   - `flash_pressure` — operating pressure of the vessel (bar)
   - `volume` — vessel volume (m³)
   - `step_time` — simulation time step (s)
2. Model the flash process:
   - When hot slurry enters a lower-pressure vessel, some water flashes to steam
   - `steam_generated = f(inlet_temp, flash_pressure)` — based on enthalpy balance
   - `steam_temp` — saturated steam temperature at flash_pressure
   - Remaining liquid slurry cools down after steam release
3. Return: `liquid_temp`, `steam_temp`, `steam_flow`, `vessel_pressure`
4. **Vessel 1** receives from **Reactor Heater 2**, outputs steam to **Preheater 2**, liquid to **Vessel 2**
5. **Vessel 2** receives liquid from **Vessel 1**, outputs steam to **Preheater 1**

---

### STEP 3: Complete the Reactor Plant Model (`plant/reactor.py`)

**Purpose:** Combine the reactor heater actuator with a tank model — slurry flows through two reactors in series, heated by electric elements.

**What to implement:**
1. Import `reaktor_pemanasan` from `actuator/reactor_heater.py`
2. Define `reactor_plant()` function that:
   - Receives slurry from the upstream equipment (Preheater 2 output for Reactor 1, Reactor 1 output for Reactor 2)
   - Applies `reaktor_pemanasan()` to heat the slurry via electric element
   - Models the leaching reaction (Ni dissolution as function of temp, acid, time)
   - Tracks slurry volume/level in reactor
3. Return: `output_temp`, `output_pressure`, `output_flow`, `leach_efficiency`
4. **Reactor Heater 1** receives from **Preheater 2**
5. **Reactor Heater 2** receives from **Reactor Heater 1**

---

### STEP 4: Build the Controller Module (`controller/`)

**Purpose:** Implement PID controllers for temperature and flow setpoints.

**What to implement:**
1. Create `controller/pid.py`:
   - PID controller class with `Kp`, `Ki`, `Kd` tuning parameters
   - `compute(setpoint, process_variable, dt)` → returns control output
   - Anti-windup clamping on integrator
2. Create `controller/process_controller.py`:
   - **Pump controller**: controls pump voltage based on desired flow setpoint
   - **Reactor heater controller**: controls heater voltage to reach target temperature
   - Note: preheaters have NO electric element — temperature depends only on steam from vessels
3. Map MQTT setpoints (received from AVEVA) to controller setpoints:
   - `setpoint_suhu_reactor1` → PID for Reactor Heater 1 voltage
   - `setpoint_suhu_reactor2` → PID for Reactor Heater 2 voltage
   - `setpoint_pump_acid` → Pump Acid voltage/flow
   - `setpoint_pump_slurry` → Pump Slurry voltage/flow

---

### STEP 5: Wire the Full Process in `main.py`

**Purpose:** Create the main simulation loop connecting all components in the correct serial order.

**What to implement:**

```
INITIALIZATION:
  1. Initialize MQTT client and connect to broker
  2. Initialize all plant states (temperatures, pressures, flows = ambient/zero)
  3. Initialize slurry generator
  4. Initialize PID controllers
  5. Set simulation step time (dt = 0.1s)
  6. Initialize steam feedback variables (vessel1_steam, vessel2_steam)
     — First iteration uses default/zero steam values

MAIN LOOP (every dt seconds):
  ┌─────────────────────────────────────────────────────────────────┐
  │  A. READ SETPOINTS from MQTT (from AVEVA dashboard)            │
  │     - pump_acid voltage/flow setpoint                          │
  │     - pump_slurry voltage/flow setpoint                        │
  │     - reactor1 temperature setpoint                            │
  │     - reactor2 temperature setpoint                            │
  ├─────────────────────────────────────────────────────────────────┤
  │  B. GENERATE SLURRY                                            │
  │     - Call slurry.generate_slurry()                            │
  │     - Get composition: Ni%, Fe%, Co%, SiO2%, moisture, pH, ρ   │
  ├─────────────────────────────────────────────────────────────────┤
  │  C. COMPUTE PUMP OUTPUTS                                       │
  │     - pump_acid_flow  = pump_actuator(voltage_acid, ...)       │
  │     - pump_slurry_flow = pump_actuator(voltage_slurry, ...)    │
  │     - combined_flow = pump_acid_flow + pump_slurry_flow        │
  │     - combined_temp = weighted average of acid & slurry temps   │
  ├─────────────────────────────────────────────────────────────────┤
  │  D. PREHEATER 1  (steam from Vessel 2)                         │
  │     - preheater1_out = preheater_tank(                         │
  │         slurry_in = combined from pumps,                       │
  │         steam = vessel2_steam from previous step)              │
  ├─────────────────────────────────────────────────────────────────┤
  │  E. PREHEATER 2  (steam from Vessel 1)                         │
  │     - preheater2_out = preheater_tank(                         │
  │         slurry_in = preheater1 output,                         │
  │         steam = vessel1_steam from previous step)              │
  ├─────────────────────────────────────────────────────────────────┤
  │  F. REACTOR HEATER 1  (PID-controlled electric heating)        │
  │     - voltage1 = pid1.compute(setpoint_reactor1, reactor1_temp)│
  │     - reactor1_out = reactor_plant(                            │
  │         slurry_in = preheater2 output, voltage = voltage1)     │
  ├─────────────────────────────────────────────────────────────────┤
  │  G. REACTOR HEATER 2  (PID-controlled electric heating)        │
  │     - voltage2 = pid2.compute(setpoint_reactor2, reactor2_temp)│
  │     - reactor2_out = reactor_plant(                            │
  │         slurry_in = reactor1 output, voltage = voltage2)       │
  ├─────────────────────────────────────────────────────────────────┤
  │  H. VESSEL 1  (flash tank — steam goes to Preheater 2)        │
  │     - vessel1_out = vessel_flash_tank(                         │
  │         slurry_in = reactor2 output)                           │
  │     - vessel1_steam = {temp, flow} → saved for Preheater 2    │
  ├─────────────────────────────────────────────────────────────────┤
  │  I. VESSEL 2  (flash tank — steam goes to Preheater 1)        │
  │     - vessel2_out = vessel_flash_tank(                         │
  │         slurry_in = vessel1 liquid output)                     │
  │     - vessel2_steam = {temp, flow} → saved for Preheater 1    │
  ├─────────────────────────────────────────────────────────────────┤
  │  J. PUBLISH ALL SENSOR DATA via MQTT                           │
  │     - All temperatures, pressures, flows, statuses             │
  │     - Pump flows, slurry compositions                          │
  ├─────────────────────────────────────────────────────────────────┤
  │  K. WAIT dt seconds, then repeat                               │
  └─────────────────────────────────────────────────────────────────┘
```

**Note on steam feedback loop:** The steam values from Vessel 1 and Vessel 2 computed in the current iteration are used by Preheater 2 and Preheater 1 respectively in the **next** iteration. This avoids circular dependency while maintaining the heat recovery feedback.

---

### STEP 6: Test Individual Components

**Order of testing:**
1. **Pump alone** — run `actuator/pump.py` standalone, verify flow ramps up with first-order response
2. **Reactor heater alone** — run `actuator/reactor_heater.py` standalone, verify temperature rises to target
3. **Slurry generator** — run `slurry/slurry.py` standalone, verify composition values are in range
4. **Preheater** — test `plant/heaterTank.py` with mock steam input, verify slurry temp rises
5. **Vessel** — test `plant/vessel.py` with mock hot slurry input, verify steam generation
6. **MQTT** — run `connection/mqtt.py` with Mosquitto broker, verify publish/subscribe cycle

---
