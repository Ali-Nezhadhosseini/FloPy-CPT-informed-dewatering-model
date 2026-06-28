"""
CPT-informed MODFLOW 6 dewatering model using FloPy

This script builds a conceptual three-layer groundwater-flow model.
CPT data are used to support hydrostratigraphic layer interpretation
and to assign approximate scenario hydraulic conductivity values.

Important note:
The hydraulic conductivity values are not calibrated field K values.
They are approximate scenario values derived from qc/Rf-based CPT indicators
and used for conceptual MODFLOW model building.
"""

from pathlib import Path
import os
import shutil

import flopy
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


# ============================================================
# 1. Project paths and MODFLOW executable
# ============================================================

PROJECT_DIR = Path(__file__).resolve().parent
DATA_DIR = PROJECT_DIR / "data"
FIGURES_DIR = PROJECT_DIR / "figures"
MODEL_WS_DIR = PROJECT_DIR / "model_ws"

FIGURES_DIR.mkdir(exist_ok=True)
MODEL_WS_DIR.mkdir(exist_ok=True)

CPT_CSV = DATA_DIR / "processed_cpt_pajaro.csv"

HEAD_FILE = "gwf_dewatering.hds"
BUDGET_FILE = "gwf_dewatering.cbc"


def resolve_mf6_executable():
    """
    Find the MODFLOW 6 executable.

    Priority:
    1. MF6_EXE environment variable
    2. mf6 available in system PATH
    3. Default local Windows installation path
    """

    candidates = [
        os.environ.get("MF6_EXE"),
        shutil.which("mf6"),
        r"C:\Program Files\USGS\ModFlow 6\mf6.7.0_win64\bin\mf6.exe",
    ]

    for candidate in candidates:
        if candidate is not None and Path(candidate).exists():
            return str(Path(candidate))

    raise FileNotFoundError(
        "MODFLOW 6 executable was not found. "
        "Install MODFLOW 6, add it to PATH, or set the MF6_EXE environment variable."
    )


MF6_EXE = resolve_mf6_executable()

print("FloPy version:", flopy.__version__)
print("MODFLOW 6 executable:", MF6_EXE)
print("Project folder:", PROJECT_DIR)


# ============================================================
# 2. Model settings
# ============================================================

# Structured model grid
NLAY = 3
NROW = 60
NCOL = 60

LENGTH_X = 300.0
LENGTH_Y = 300.0

DELR = LENGTH_X / NCOL
DELC = LENGTH_Y / NROW

# Layer elevations based on simplified CPT interpretation
# Layer 1: 0–4 m depth
# Layer 2: 4–10 m depth
# Layer 3: 10–19 m depth
TOP = 0.0
BOTM = [-4.0, -10.0, -19.0]

# Boundary and initial heads
INITIAL_HEAD = -2.0
LEFT_HEAD = -1.0
RIGHT_HEAD = -3.0

# Transient simulation settings
SIMULATION_DAYS = 365.0
NSTEPS = 12

# Recharge and storage
RECHARGE_RATE = 0.0003  # m/day
SPECIFIC_STORAGE = 1e-5
SPECIFIC_YIELD = 0.15

# Pumping wells
# MODFLOW cell indices are zero-based: (layer, row, column)
WELL_SPD = [
    ((2, 20, 25), -80.0),
    ((2, 30, 30), -60.0),
    ((2, 40, 35), -40.0),
]


# ============================================================
# 3. CPT-based K estimation
# ============================================================

def load_cpt_data(cpt_csv):
    """
    Load processed CPT data.

    Expected columns:
    depth_m, qc_MPa, fs_kPa, Rf_percent
    """

    if not cpt_csv.exists():
        print("CPT CSV not found. Using fallback K values.")
        return None

    cpt = pd.read_csv(cpt_csv)

    required_columns = {"depth_m", "qc_MPa", "fs_kPa"}
    missing = required_columns - set(cpt.columns)

    if missing:
        raise ValueError(f"Missing required CPT columns: {missing}")

    # Recalculate Rf if it is missing
    if "Rf_percent" not in cpt.columns:
        cpt["Rf_percent"] = cpt["fs_kPa"] / (cpt["qc_MPa"] * 1000.0) * 100.0

    # Clean invalid values
    cpt = cpt.copy()
    cpt["depth_m"] = pd.to_numeric(cpt["depth_m"], errors="coerce")
    cpt["qc_MPa"] = pd.to_numeric(cpt["qc_MPa"], errors="coerce")
    cpt["fs_kPa"] = pd.to_numeric(cpt["fs_kPa"], errors="coerce")
    cpt["Rf_percent"] = pd.to_numeric(cpt["Rf_percent"], errors="coerce")

    cpt = cpt.dropna(subset=["depth_m", "qc_MPa", "fs_kPa", "Rf_percent"])
    cpt = cpt[(cpt["qc_MPa"] > 0) & (cpt["fs_kPa"] >= 0)]

    return cpt





def get_layer_k_values(cpt):
    """
    Assign one representative scenario K value to each model layer.

    CPT data are used through a relative permeability indicator:

        K_index = median(qc / (Rf + 0.5))

    where:
    - higher qc generally indicates denser/coarser material
    - lower Rf generally indicates more sand-like behavior

    The K_index is used only for relative ranking of the three layers.
    The final K values are scenario values for conceptual MODFLOW modelling,
    not calibrated field hydraulic conductivities.
    """

    # Scenario K classes used for the conceptual groundwater model
    low_k = 1.0
    medium_k = 3.0
    high_k = 10.0

    # Fallback values if CPT data are not available
    fallback_k = [low_k, medium_k, high_k]

    if cpt is None:
        print("No CPT data available. Using fallback K values.")
        return fallback_k[0], fallback_k[1], fallback_k[2]

    layer_intervals = {
        0: (0.0, 4.0),
        1: (4.0, 10.0),
        2: (10.0, 19.0),
    }

    layer_summaries = []

    print("\nCPT-based layer summary:")

    for layer, (zmin, zmax) in layer_intervals.items():
        if layer < 2:
            subset = cpt[(cpt["depth_m"] >= zmin) & (cpt["depth_m"] < zmax)]
        else:
            subset = cpt[(cpt["depth_m"] >= zmin) & (cpt["depth_m"] <= zmax)]

        if subset.empty:
            qc_median = np.nan
            rf_median = np.nan
            k_index = np.nan
        else:
            qc_median = subset["qc_MPa"].median()
            rf_median = subset["Rf_percent"].median()

            # Relative CPT permeability indicator
            # Higher qc and lower Rf generally indicate more permeable sandy behavior.
            k_index = (subset["qc_MPa"] / (subset["Rf_percent"] + 0.5)).median()

        layer_summaries.append(
            {
                "layer": layer,
                "zmin": zmin,
                "zmax": zmax,
                "qc_median": qc_median,
                "rf_median": rf_median,
                "k_index": k_index,
            }
        )

    # Rank layers by K_index and assign low / medium / high scenario K
    valid_layers = [item for item in layer_summaries if not np.isnan(item["k_index"])]

    if len(valid_layers) == 3:
        ranked_layers = sorted(valid_layers, key=lambda item: item["k_index"])

        assigned_k = {}

        assigned_k[ranked_layers[0]["layer"]] = low_k
        assigned_k[ranked_layers[1]["layer"]] = medium_k
        assigned_k[ranked_layers[2]["layer"]] = high_k

    else:
        print("Incomplete CPT data. Using fallback K values.")
        assigned_k = {
            0: fallback_k[0],
            1: fallback_k[1],
            2: fallback_k[2],
        }

    k_values = []

    for item in layer_summaries:
        layer = item["layer"]
        k_value = assigned_k[layer]
        k_values.append(k_value)

        print(
            f"Layer {layer + 1}: depth {item['zmin']:.0f}-{item['zmax']:.0f} m | "
            f"qc_median={item['qc_median']:.2f} MPa | "
            f"Rf_median={item['rf_median']:.2f}% | "
            f"K_index={item['k_index']:.2f} | "
            f"assigned scenario K={k_value:.2f} m/day"
        )

    return k_values[0], k_values[1], k_values[2]



def build_k_array(k_layer1, k_layer2, k_layer3):
    """
    Build 3D hydraulic conductivity array.

    A schematic low-K zone is added in Layer 2 to represent
    a possible silt/clay lens or lower-permeability interval.
    """

    k_array = np.zeros((NLAY, NROW, NCOL))

    k_array[0, :, :] = k_layer1
    k_array[1, :, :] = k_layer2
    k_array[2, :, :] = k_layer3

    # Schematic low-K zone in Layer 2
    k_array[1, 20:40, 20:40] = 0.3

    return k_array


# ============================================================
# 4. MODFLOW model builder
# ============================================================

def build_and_run_model(workspace_name, k_array, with_pumping):
    """
    Build and run a MODFLOW 6 model.

    Parameters
    ----------
    workspace_name : str
        Name of the model workspace folder.
    k_array : np.ndarray
        3D hydraulic conductivity array.
    with_pumping : bool
        If True, pumping wells are included.
    """

    workspace = MODEL_WS_DIR / workspace_name
    workspace.mkdir(parents=True, exist_ok=True)

    sim = flopy.mf6.MFSimulation(
        sim_name=workspace_name,
        version="mf6",
        exe_name=MF6_EXE,
        sim_ws=workspace,
    )

    flopy.mf6.ModflowTdis(
        sim,
        time_units="DAYS",
        nper=1,
        perioddata=[(SIMULATION_DAYS, NSTEPS, 1.0)],
    )

    gwf = flopy.mf6.ModflowGwf(
        sim,
        modelname="gwf_dewatering",
        save_flows=True,
    )

    ims = flopy.mf6.ModflowIms(
        sim,
        print_option="SUMMARY",
        complexity="SIMPLE",
    )

    sim.register_ims_package(ims, [gwf.name])

    flopy.mf6.ModflowGwfdis(
        gwf,
        nlay=NLAY,
        nrow=NROW,
        ncol=NCOL,
        delr=DELR,
        delc=DELC,
        top=TOP,
        botm=BOTM,
        idomain=1,
    )

    flopy.mf6.ModflowGwfic(
        gwf,
        strt=INITIAL_HEAD,
    )

    flopy.mf6.ModflowGwfnpf(
        gwf,
        icelltype=[1, 0, 0],
        k=k_array,
        save_specific_discharge=True,
    )

    flopy.mf6.ModflowGwfsto(
        gwf,
        iconvert=[1, 0, 0],
        ss=SPECIFIC_STORAGE,
        sy=SPECIFIC_YIELD,
        transient={0: True},
    )

    chd_spd = []

    for lay in range(NLAY):
        for row in range(NROW):
            chd_spd.append(((lay, row, 0), LEFT_HEAD))
            chd_spd.append(((lay, row, NCOL - 1), RIGHT_HEAD))

    flopy.mf6.ModflowGwfchd(
        gwf,
        stress_period_data=chd_spd,
    )

    flopy.mf6.ModflowGwfrcha(
        gwf,
        recharge=RECHARGE_RATE,
    )

    if with_pumping:
        flopy.mf6.ModflowGwfwel(
            gwf,
            stress_period_data=WELL_SPD,
        )

    flopy.mf6.ModflowGwfoc(
        gwf,
        head_filerecord=HEAD_FILE,
        budget_filerecord=BUDGET_FILE,
        saverecord=[("HEAD", "ALL"), ("BUDGET", "ALL")],
        printrecord=[("HEAD", "LAST"), ("BUDGET", "LAST")],
    )

    sim.write_simulation()
    success, _ = sim.run_simulation()

    if not success:
        raise RuntimeError(f"MODFLOW 6 simulation failed: {workspace_name}")

    head_path = workspace / HEAD_FILE
    head_obj = flopy.utils.HeadFile(head_path)
    times = head_obj.get_times()
    head = head_obj.get_data(totim=times[-1])

    budget_path = workspace / BUDGET_FILE

    print(f"Finished model: {workspace_name}")

    return head, budget_path


# ============================================================
# 5. Plotting helper functions
# ============================================================

def get_grid_coordinates():
    """Create x-y grid coordinates for plotting."""

    x = np.linspace(DELR / 2, LENGTH_X - DELR / 2, NCOL)
    y = np.linspace(DELC / 2, LENGTH_Y - DELC / 2, NROW)
    return np.meshgrid(x, y)


def get_well_coordinates():
    """Convert MODFLOW well row/column indices to x-y plot coordinates."""

    well_x = []
    well_y = []

    for cell, _rate in WELL_SPD:
        _layer, row, col = cell
        well_x.append((col + 0.5) * DELR)
        well_y.append((row + 0.5) * DELC)

    return well_x, well_y


def plot_head_layer3(head_with_pumping):
    """Plot hydraulic head in Layer 3 for the pumping scenario."""

    head_layer3 = head_with_pumping[2]
    X, Y = get_grid_coordinates()
    well_x, well_y = get_well_coordinates()

    plt.figure(figsize=(7, 6))

    image = plt.imshow(
        head_layer3,
        extent=[0, LENGTH_X, 0, LENGTH_Y],
        origin="lower",
    )

    plt.colorbar(image, label="Hydraulic head (m)")
    plt.contour(X, Y, head_layer3, levels=10, colors="black", linewidths=0.5)

    plt.scatter(
        well_x,
        well_y,
        marker="x",
        s=80,
        label="Pumping wells",
        color="red",
        linewidths=2,
    )

    plt.legend()
    plt.title("Hydraulic Head with Pumping Wells - Layer 3")
    plt.xlabel("x (m)")
    plt.ylabel("y (m)")
    plt.tight_layout()

    plot_path = FIGURES_DIR / "head_with_recharge_and_wells_layer3.png"
    plt.savefig(plot_path, dpi=300, bbox_inches="tight")
    plt.show()

    print("Head plot saved:", plot_path)


def plot_k_layer2(k_array):
    """Plot hydraulic conductivity distribution in Layer 2."""

    plt.figure(figsize=(7, 6))

    image = plt.imshow(
        k_array[1],
        extent=[0, LENGTH_X, 0, LENGTH_Y],
        origin="lower",
    )

    plt.colorbar(image, label="Hydraulic conductivity K (m/day)")
    plt.title("Hydraulic Conductivity Distribution - Layer 2")
    plt.xlabel("x (m)")
    plt.ylabel("y (m)")
    plt.tight_layout()

    plot_path = FIGURES_DIR / "hydraulic_conductivity_layer2_low_k_zone.png"
    plt.savefig(plot_path, dpi=300, bbox_inches="tight")
    plt.show()

    print("K distribution plot saved:", plot_path)


def plot_pumping_only_drawdown(head_no_pumping, head_with_pumping):
    """
    Plot pumping-only drawdown.

    This is the correct drawdown definition for isolating dewatering effects:
    drawdown = head_without_pumping - head_with_pumping
    """

    drawdown_layer3 = head_no_pumping[2] - head_with_pumping[2]

    print(
        "Pumping-only drawdown range:",
        np.nanmin(drawdown_layer3),
        "to",
        np.nanmax(drawdown_layer3),
        "m",
    )

    X, Y = get_grid_coordinates()
    well_x, well_y = get_well_coordinates()

    plt.figure(figsize=(7, 6))

    image = plt.imshow(
        drawdown_layer3,
        extent=[0, LENGTH_X, 0, LENGTH_Y],
        origin="lower",
    )

    plt.colorbar(image, label="Pumping-only drawdown (m)")
    plt.contour(X, Y, drawdown_layer3, levels=10, colors="black", linewidths=0.5)

    plt.scatter(
        well_x,
        well_y,
        marker="x",
        s=80,
        label="Pumping wells",
        color="red",
        linewidths=2,
    )

    plt.legend()
    plt.title("Pumping-only Drawdown - Layer 3")
    plt.xlabel("x (m)")
    plt.ylabel("y (m)")
    plt.tight_layout()

    plot_path = FIGURES_DIR / "pumping_only_drawdown_layer3.png"
    plt.savefig(plot_path, dpi=300, bbox_inches="tight")
    plt.show()

    print("Pumping-only drawdown plot saved:", plot_path)


# ============================================================
# 6. Water budget helper function
# ============================================================

def get_budget_total(budget_obj, term):
    """Return the summed value of a MODFLOW budget term."""

    data = budget_obj.get_data(text=term)[-1]

    if hasattr(data, "dtype") and data.dtype.names is not None:
        if "q" in data.dtype.names:
            return float(data["q"].sum())

    return float(np.asarray(data).sum())


def print_water_budget(budget_path):
    """Print main water-budget terms for the pumping scenario."""

    budget_obj = flopy.utils.CellBudgetFile(budget_path)

    budget_terms = ["CHD", "WEL", "RCHA", "STO-SS", "STO-SY"]

    print("\nAvailable budget terms:")
    print(budget_obj.get_unique_record_names())

    print("\nWater budget summary at final time:")
    for term in budget_terms:
        try:
            total = get_budget_total(budget_obj, term)
            print(f"{term:8s}: {total:12.3f} m3/day")
        except Exception as error:
            print(f"{term:8s}: could not read ({error})")


# ============================================================
# 7. Main workflow
# ============================================================

def main():
    """
    Run the complete CPT-informed conceptual dewatering workflow.
    """

    print("\nStarting CPT-informed MODFLOW 6 dewatering model...")

    # Load CPT data and estimate approximate layer K values
    cpt = load_cpt_data(CPT_CSV)
    k_layer1, k_layer2, k_layer3 = get_layer_k_values(cpt)

    print("\nAssigned model K values:")
    print(f"Layer 1 K: {k_layer1:.2f} m/day")
    print(f"Layer 2 K: {k_layer2:.2f} m/day")
    print(f"Layer 3 K: {k_layer3:.2f} m/day")
    print("Layer 2 low-K zone: 0.30 m/day")

    k_array = build_k_array(
        k_layer1=k_layer1,
        k_layer2=k_layer2,
        k_layer3=k_layer3,
    )

    # Run baseline and pumping scenarios
    head_no_pumping, _budget_no_pumping = build_and_run_model(
        workspace_name="baseline_no_pumping",
        k_array=k_array,
        with_pumping=False,
    )

    head_with_pumping, budget_with_pumping = build_and_run_model(
        workspace_name="scenario_with_pumping",
        k_array=k_array,
        with_pumping=True,
    )

    # Create final outputs
    plot_head_layer3(head_with_pumping)
    plot_k_layer2(k_array)
    plot_pumping_only_drawdown(head_no_pumping, head_with_pumping)
    print_water_budget(budget_with_pumping)

    print("\nWorkflow completed successfully.")


if __name__ == "__main__":
    main()
