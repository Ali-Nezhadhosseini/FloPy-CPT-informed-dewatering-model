\# CPT-informed groundwater flow model using FloPy and MODFLOW 6



This project demonstrates a simplified CPT-informed groundwater flow and dewatering model using FloPy and MODFLOW 6.



The aim is to show how direct-push CPT data can be used to support the development of a conceptual hydrostratigraphic model and then translated into a numerical groundwater flow model.



\## Project objective



The main objective is to build a small but transparent groundwater-flow modelling workflow:



1\. Read and process CPT raw data.

2\. Calculate basic CPT parameters such as tip resistance, sleeve friction, and friction ratio.

3\. Interpret simplified hydrostratigraphic layers from CPT profiles.

4\. Build a three-layer MODFLOW 6 groundwater model in FloPy.

5\. Assign CPT-informed hydraulic conductivity values to the model layers.

6\. Add a low-permeability zone representing a possible silt/clay lens.

7\. Simulate a dewatering scenario with pumping wells.

8\. Evaluate head distribution, pumping-only drawdown, water budget, and sensitivity to hydraulic conductivity.



\## Input data



The project uses publicly available CPT data from the Pajaro site. The raw CPT files contain:



\* depth

\* tip resistance

\* sleeve friction

\* inclination

\* S-wave travel time

\* coordinates and elevation metadata



The processed CPT data are stored in:



```text

data/processed\\\\\\\\\\\\\\\_cpt\\\\\\\\\\\\\\\_pajaro.csv

```



\## CPT interpretation



The CPT profiles were used to define a simplified three-layer conceptual model:



```text

Layer 1: 0–4 m      shallow mixed / loose material

Layer 2: 4–10 m     intermediate sandy-silty material

Layer 3: 10–19 m    denser sandy material

```



The hydraulic conductivity values used in the base model are:



```text

Layer 1: K = 1 m/day

Layer 2: K = 3 m/day

Layer 3: K = 10 m/day

```



A low-permeability zone was added in Layer 2 with:



```text

K = 0.3 m/day

```



This represents a possible silt/clay lens.



\## MODFLOW model setup



The groundwater model is a simplified three-dimensional structured MODFLOW 6 model.



Main model settings:



```text

Model size: 300 m × 300 m

Grid: 60 rows × 60 columns

Layers: 3

Top elevation: 0 m

Bottom elevations: -4 m, -10 m, -19 m

Simulation time: 365 days

Recharge: 0.0003 m/day

Left boundary head: -1 m

Right boundary head: -3 m

```



Three pumping wells are placed in Layer 3:



```text

Well 1: -80 m³/day

Well 2: -60 m³/day

Well 3: -40 m³/day

```



Total pumping rate:



```text

\\\\\\\\-180 m³/day

```



\## Main outputs



The project produces the following outputs:



```text

figures/cpt\\\\\\\\\\\\\\\_profiles\\\\\\\\\\\\\\\_all\\\\\\\\\\\\\\\_points.png

figures/cpt\\\\\\\\\\\\\\\_profiles\\\\\\\\\\\\\\\_with\\\\\\\\\\\\\\\_layers.png

figures/hydraulic\\\\\\\\\\\\\\\_conductivity\\\\\\\\\\\\\\\_layer2\\\\\\\\\\\\\\\_low\\\\\\\\\\\\\\\_k\\\\\\\\\\\\\\\_zone.png

figures/head\\\\\\\\\\\\\\\_with\\\\\\\\\\\\\\\_recharge\\\\\\\\\\\\\\\_and\\\\\\\\\\\\\\\_wells\\\\\\\\\\\\\\\_layer3.png

figures/pumping\\\\\\\\\\\\\\\_only\\\\\\\\\\\\\\\_drawdown\\\\\\\\\\\\\\\_layer3.png

figures/sensitivity\\\\\\\\\\\\\\\_k\\\\\\\\\\\\\\\_layer3\\\\\\\\\\\\\\\_drawdown.png

```



\## Water budget



The final model water budget shows that the pumping demand is supplied by recharge and inflow from the constant-head boundaries.



Example budget terms:



```text

WEL  = pumping wells

RCHA = recharge

CHD  = constant-head boundaries

STO  = storage

```



The total pumping rate is approximately:



```text

180 m³/day

```



\## Pumping-only drawdown



To isolate the effect of pumping, two models were run:



```text

1\\\\\\\\. Baseline model without pumping

2\\\\\\\\. Scenario model with pumping

```



The pumping-only drawdown was calculated as:



```text

drawdown = head\\\\\\\\\\\\\\\_without\\\\\\\\\\\\\\\_pumping - head\\\\\\\\\\\\\\\_with\\\\\\\\\\\\\\\_pumping

```



The maximum pumping-only drawdown in Layer 3 is approximately:



```text

0.87 m

```



for the base case with:



```text

Layer 3 K = 10 m/day

```



\## Sensitivity analysis



A simple sensitivity analysis was carried out by changing the hydraulic conductivity of Layer 3.



Results:



| Layer 3 K (m/day) | Maximum pumping-only drawdown (m) |

| ----------------: | --------------------------------: |

|                 5 |                              1.60 |

|                10 |                              0.87 |

|                20 |                              0.46 |



The results show that the simulated drawdown is sensitive to the hydraulic conductivity assigned to the deeper CPT-informed sandy layer.



Lower hydraulic conductivity leads to higher drawdown, while higher hydraulic conductivity leads to lower drawdown.



\## Limitations



This is a conceptual portfolio model, not a calibrated site model.



Main limitations:



\* CPT-based layer interpretation is simplified.

\* Hydraulic conductivity values are assumed from conceptual soil behavior and are not calibrated.

\* The model uses simplified boundary conditions.

\* The low-K zone is schematic.

\* No field groundwater-level calibration is included.



\## Purpose



This project is intended as a practical demonstration of groundwater modelling skills, including CPT data processing, conceptual model development, MODFLOW 6 setup, dewatering simulation, water-budget checking, and sensitivity analysis using Python and FloPy.

