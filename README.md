# CPT-Informed MODFLOW 6 Dewatering Model using FloPy

A compact groundwater-modeling portfolio project focused on **practical MODFLOW 6 model building with FloPy**. CPT data are used as supporting field information to build a simplified hydrostratigraphic concept, which is then translated into a three-layer dewatering model.

---

## Key model outputs

### Pumping-only drawdown, Layer 3

![Pumping-only drawdown](figures/pumping_only_drawdown_layer3.png)

This result isolates the drawdown caused by pumping wells by comparing two simulations:

```text
drawdown = head_without_pumping - head_with_pumping
```

The maximum pumping-only drawdown in the base case is approximately:

```text
0.87 m
```

---

### Hydraulic conductivity sensitivity

![Sensitivity analysis](figures/sensitivity_k_layer3_drawdown.png)

The sensitivity test shows that the simulated drawdown strongly depends on the hydraulic conductivity assigned to the deeper sandy layer.

| Layer 3 K (m/day) | Maximum pumping-only drawdown (m) |
| ----------------: | --------------------------------: |
|                 5 |                              1.60 |
|                10 |                              0.87 |
|                20 |                              0.46 |

---

### CPT-informed hydrostratigraphic interpretation

![CPT profiles with interpreted layers](figures/cpt_profiles_with_layers.png)

The CPT profiles were used to define a simplified three-layer conceptual model:

| Layer | Depth interval | Conceptual interpretation         |
| ----: | -------------: | --------------------------------- |
|     1 |          0–4 m | Shallow mixed / loose material    |
|     2 |         4–10 m | Intermediate sandy-silty material |
|     3 |        10–19 m | Deeper, denser sandy layer        |

---

### Low-permeability zone in Layer 2

![Low-K zone](figures/hydraulic_conductivity_layer2_low_k_zone.png)

A low-permeability zone was added in Layer 2 to represent a possible silt/clay lens.

```text
Layer 2 background K = 3.0 m/day
Low-K zone K         = 0.3 m/day
```

---

### Simulated hydraulic head, Layer 3

![Hydraulic head Layer 3](figures/head_with_recharge_and_wells_layer3.png)

The model produces a regional hydraulic gradient from the left boundary to the right boundary, with local drawdown around the pumping wells.

---

## Project focus

This project was designed to demonstrate practical groundwater model-building skills:

* processing CPT data in Python
* interpreting simplified hydrostratigraphic layers
* building a three-layer MODFLOW 6 model with FloPy
* assigning CPT-informed hydraulic conductivity values
* adding heterogeneity through a low-K zone
* simulating dewatering wells
* checking the water budget
* separating pumping-only drawdown from the regional gradient
* testing sensitivity to hydraulic conductivity

---

## Model setup

| Item                |                Value |
| ------------------- | -------------------: |
| Model code          |            MODFLOW 6 |
| Python interface    |                FloPy |
| Domain size         |        300 m × 300 m |
| Grid                | 60 rows × 60 columns |
| Layers              |                    3 |
| Top elevation       |                  0 m |
| Bottom elevations   |   -4 m, -10 m, -19 m |
| Simulation time     |             365 days |
| Recharge            |         0.0003 m/day |
| Left boundary head  |                 -1 m |
| Right boundary head |                 -3 m |
| Total pumping rate  |           180 m³/day |

---

## Hydraulic conductivity setup

|   Layer | K (m/day) |
| ------: | --------: |
| Layer 1 |         1 |
| Layer 2 |         3 |
| Layer 3 |        10 |

A schematic low-K zone was added inside Layer 2:

```text
K = 0.3 m/day
```

---

## Water budget check

The final model budget confirms that pumping demand is mainly supplied by recharge and constant-head boundary inflow.

Example base-case budget:

| Budget term   | Flow (m³/day) |
| ------------- | ------------: |
| Constant head |        +151.2 |
| Recharge      |         +26.1 |
| Wells         |        -180.0 |

This confirms that the model is numerically consistent and that the pumping wells are balanced by boundary inflow and recharge.

---

## Repository structure

```text
data/
figures/
notebooks/
01_cpt_informed_modflow_model.py
02_pumping_drawdown_comparison.py
03_sensitivity_k_layer3.py
04_sensitivity_summary_plot.py
README.md
requirements.txt
```

---

## Limitations

This is a conceptual portfolio model, not a calibrated site model.

Main limitations:

* CPT interpretation is simplified.
* Hydraulic conductivity values are assumed and not calibrated.
* Boundary conditions are simplified.
* The low-K zone is schematic.
* No field groundwater-level calibration is included.

---

## Purpose

The purpose of this project is to demonstrate a practical workflow for connecting CPT-based conceptual interpretation with MODFLOW 6 groundwater-flow and dewatering modeling using Python and FloPy.
