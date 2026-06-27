import flopy
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt


# =========================
# Paths
# =========================

project_dir = Path(__file__).resolve().parent

mf6_path = r"C:\Program Files\USGS\ModFlow 6\mf6.7.0_win64\bin\mf6.exe"

figures_dir = project_dir / "figures"
figures_dir.mkdir(exist_ok=True)

print("FloPy version:", flopy.__version__)
print("MF6 exists:", Path(mf6_path).exists())


# =========================
# Model settings
# =========================

nlay = 3
nrow = 60
ncol = 60

length_x = 300.0
length_y = 300.0

delr = length_x / ncol
delc = length_y / nrow

top = 0.0
botm = [-4.0, -10.0, -19.0]

initial_head = -2.0

left_head = -1.0
right_head = -3.0

recharge_rate = 0.0003

specific_storage = 1e-5
specific_yield = 0.15

head_file = "gwf_dewatering.hds"
budget_file = "gwf_dewatering.cbc"


# =========================
# CPT-informed K array
# =========================

k_layer1 = 1.0
k_layer2 = 3.0
k_layer3 = 10.0

k_array = np.zeros((nlay, nrow, ncol))

k_array[0, :, :] = k_layer1
k_array[1, :, :] = k_layer2
k_array[2, :, :] = k_layer3

# Low-K zone in Layer 2
k_array[1, 20:40, 20:40] = 0.3


# =========================
# Well locations
# =========================

well_spd = [
    ((2, 20, 25), -80.0),
    ((2, 30, 30), -60.0),
    ((2, 40, 35), -40.0),
]


# =========================
# Function to build and run model
# =========================

def run_model(workspace_name, with_pumping):
    workspace = project_dir / "model_ws" / workspace_name
    workspace.mkdir(parents=True, exist_ok=True)

    sim = flopy.mf6.MFSimulation(
        sim_name=workspace_name,
        version="mf6",
        exe_name=mf6_path,
        sim_ws=workspace,
    )

    flopy.mf6.ModflowTdis(
        sim,
        time_units="DAYS",
        nper=1,
        perioddata=[(365.0, 12, 1.0)],
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
        nlay=nlay,
        nrow=nrow,
        ncol=ncol,
        delr=delr,
        delc=delc,
        top=top,
        botm=botm,
        idomain=1,
    )

    flopy.mf6.ModflowGwfic(
        gwf,
        strt=initial_head,
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
        ss=specific_storage,
        sy=specific_yield,
        transient={0: True},
    )

    chd_spd = []

    for lay in range(nlay):
        for row in range(nrow):
            chd_spd.append(((lay, row, 0), left_head))
            chd_spd.append(((lay, row, ncol - 1), right_head))

    flopy.mf6.ModflowGwfchd(
        gwf,
        stress_period_data=chd_spd,
    )

    flopy.mf6.ModflowGwfrcha(
        gwf,
        recharge=recharge_rate,
    )

    if with_pumping:
        flopy.mf6.ModflowGwfwel(
            gwf,
            stress_period_data=well_spd,
        )

    flopy.mf6.ModflowGwfoc(
        gwf,
        head_filerecord=head_file,
        budget_filerecord=budget_file,
        saverecord=[("HEAD", "ALL"), ("BUDGET", "ALL")],
        printrecord=[("HEAD", "LAST"), ("BUDGET", "LAST")],
    )

    sim.write_simulation()

    success, buff = sim.run_simulation()

    if not success:
        raise RuntimeError(f"MODFLOW failed for {workspace_name}")

    head_path = workspace / head_file
    head_obj = flopy.utils.HeadFile(head_path)
    times = head_obj.get_times()
    head = head_obj.get_data(totim=times[-1])

    print(f"Finished model: {workspace_name}")

    return head


# =========================
# Run two models
# =========================

head_no_pumping = run_model(
    workspace_name="baseline_no_pumping",
    with_pumping=False,
)

head_with_pumping = run_model(
    workspace_name="scenario_with_pumping",
    with_pumping=True,
)


# =========================
# Pumping-only drawdown
# =========================

head_no_pumping_layer3 = head_no_pumping[2]
head_with_pumping_layer3 = head_with_pumping[2]

pumping_drawdown_layer3 = head_no_pumping_layer3 - head_with_pumping_layer3

print(
    "Pumping-only drawdown range:",
    np.nanmin(pumping_drawdown_layer3),
    "to",
    np.nanmax(pumping_drawdown_layer3),
    "m",
)


# =========================
# Plot pumping-only drawdown
# =========================

x = np.linspace(delr / 2, length_x - delr / 2, ncol)
y = np.linspace(delc / 2, length_y - delc / 2, nrow)
X, Y = np.meshgrid(x, y)

well_x = []
well_y = []

for cell, rate in well_spd:
    layer, row, col = cell
    well_x.append((col + 0.5) * delr)
    well_y.append((row + 0.5) * delc)

plt.figure(figsize=(7, 6))

image = plt.imshow(
    pumping_drawdown_layer3,
    extent=[0, length_x, 0, length_y],
    origin="lower",
)

plt.colorbar(image, label="Pumping-only drawdown (m)")
plt.contour(X, Y, pumping_drawdown_layer3, levels=10, colors="black", linewidths=0.5)

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

plot_path = figures_dir / "pumping_only_drawdown_layer3.png"
plt.savefig(plot_path, dpi=300, bbox_inches="tight")
plt.show()

print("Pumping-only drawdown plot saved:", plot_path)