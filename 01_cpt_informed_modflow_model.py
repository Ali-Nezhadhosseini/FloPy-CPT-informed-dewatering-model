# Import required Python libraries
import flopy
from pathlib import Path

# Import libraries for numerical arrays and plotting
import numpy as np
import matplotlib.pyplot as plt

# Define the full path to the MODFLOW 6 executable
mf6_path = r"C:\Program Files\USGS\ModFlow 6\mf6.7.0_win64\bin\mf6.exe"


# Create a workspace folder where all MODFLOW input and output files will be stored
project_dir = Path(__file__).resolve().parent

workspace = project_dir / "model_ws" / "cpt_informed_dewatering_model"
workspace.mkdir(parents=True, exist_ok=True)

figures_dir = project_dir / "figures"
figures_dir.mkdir(exist_ok=True)


# Check installed FloPy version, MODFLOW 6 executable path, and workspace location
print("FloPy version:", flopy.__version__)
print("MF6 exists:", Path(mf6_path).exists())
print("Workspace folder:", workspace.resolve())


# Create the main MODFLOW 6 simulation object
sim = flopy.mf6.MFSimulation(
    sim_name="dewatering",
    version="mf6",
    exe_name=mf6_path,
    sim_ws=workspace,
)
print("Simulation object created successfully.")


# Define the time discretization package for a 365-day transient simulation
tdis = flopy.mf6.ModflowTdis(
    sim,
    time_units="DAYS",
    nper=1,
    perioddata=[(365.0, 12, 1.0)],
)
print("TDIS package created successfully.")


# Create the groundwater flow model inside the MODFLOW 6 simulation
gwf = flopy.mf6.ModflowGwf(
    sim,
    modelname="gwf_dewatering",
    save_flows=True,
)

print("Groundwater flow model created successfully.")


# Create the numerical solver for the groundwater flow model
ims = flopy.mf6.ModflowIms(
    sim,
    print_option="SUMMARY",
    complexity="SIMPLE",
)

# Connect the solver to the groundwater flow model
sim.register_ims_package(ims, [gwf.name])

print("IMS solver package created and connected successfully.")



# Define the structured model grid and layer elevations
# The vertical layering is based on the simplified CPT interpretation:
# Layer 1: 0–4 m depth
# Layer 2: 4–10 m depth
# Layer 3: 10–19 m depth

nlay = 3
nrow = 60
ncol = 60

length_x = 300.0
length_y = 300.0

delr = length_x / ncol
delc = length_y / nrow

top = 0.0
botm = [-4.0, -10.0, -19.0]

idomain = 1


# Create the discretization package for the groundwater flow model
dis = flopy.mf6.ModflowGwfdis(
    gwf,
    nlay=nlay,
    nrow=nrow,
    ncol=ncol,
    delr=delr,
    delc=delc,
    top=top,
    botm=botm,
    idomain=idomain,
)

print("DIS package created successfully.")


# Define the initial hydraulic head at the beginning of the simulation
initial_head = -2.0

# Create the initial conditions package for the groundwater flow model
ic = flopy.mf6.ModflowGwfic(
    gwf,
    strt=initial_head,
)

print("IC package created successfully.")


# Define the hydraulic conductivity of the aquifer material
# Define CPT-informed hydraulic conductivity values
# Units: m/day

k_layer1 = 1.0     # Layer 1: shallow loose/mixed material
k_layer2 = 3.0     # Layer 2: intermediate sandy-silty layer
k_layer3 = 10.0    # Layer 3: denser sandy layer

k_array = np.zeros((nlay, nrow, ncol))

k_array[0, :, :] = k_layer1
k_array[1, :, :] = k_layer2
k_array[2, :, :] = k_layer3

k_array[1, 20:40, 20:40] = 0.3

# Create the Node Property Flow package
npf = flopy.mf6.ModflowGwfnpf(
    gwf,
    icelltype=[1, 0, 0],
    k=k_array,
    save_specific_discharge=True,
)

print("NPF package created successfully with 3 CPT-informed layers.")


# Define storage properties for the transient groundwater model
specific_storage = 1e-5
specific_yield = 0.15


# Create the storage package for transient groundwater flow
sto = flopy.mf6.ModflowGwfsto(
    gwf,
    iconvert=[1, 0, 0],
    ss=specific_storage,
    sy=specific_yield,
    transient={0: True},
)

print("STO package created successfully.")



# Define constant head values on the left and right boundaries
left_head = -1.0
right_head = -3.0


# Create constant head boundary cells for both model layers
chd_spd = []

for lay in range(nlay):
    for row in range(nrow):
        chd_spd.append(((lay, row, 0), left_head))
        chd_spd.append(((lay, row, ncol - 1), right_head))


# Create the constant head package for the groundwater flow model
chd = flopy.mf6.ModflowGwfchd(
    gwf,
    stress_period_data=chd_spd,
)

print("CHD package created successfully.")



# Define output file names for hydraulic head and water budget
head_file = "gwf_dewatering.hds"
budget_file = "gwf_dewatering.cbc"



# Define areal recharge from rainfall or infiltration
recharge_rate = 0.0003


# Create the recharge package for the groundwater flow model
rch = flopy.mf6.ModflowGwfrcha(
    gwf,
    recharge=recharge_rate,
)

print("RCH package created successfully.")



# Define pumping wells for the dewatering scenario
# Wells are placed in Layer 3 because the deeper CPT-informed layer has higher K

pumping_rate1 = -80.0
pumping_rate2 = -60.0
pumping_rate3 = -40.0

well_spd = [
    ((2, 20, 25), pumping_rate1),
    ((2, 30, 30), pumping_rate2),
    ((2, 40, 35), pumping_rate3),
]

# Create the well package for groundwater extraction
wel = flopy.mf6.ModflowGwfwel(
    gwf,
    stress_period_data=well_spd,
)

print("WEL package created successfully.")




# Create the output control package to save model results
oc = flopy.mf6.ModflowGwfoc(
    gwf,
    head_filerecord=head_file,
    budget_filerecord=budget_file,
    saverecord=[("HEAD", "ALL"), ("BUDGET", "ALL")],
    printrecord=[("HEAD", "LAST"), ("BUDGET", "LAST")],
)

print("OC package created successfully.")


# Write all MODFLOW 6 input files to the workspace folder
sim.write_simulation()

print("MODFLOW 6 input files written successfully.")


# Run the MODFLOW 6 simulation
success, buff = sim.run_simulation()

if success:
    print("MODFLOW 6 simulation ran successfully.")

    # Read the simulated hydraulic head file
    head_path = workspace / head_file
    head_obj = flopy.utils.HeadFile(head_path)

    # Get the hydraulic head from the last simulation time
    times = head_obj.get_times()
    head = head_obj.get_data(totim=times[-1])

    # Select hydraulic head from Layer 3, where pumping wells are located
    head_layer3 = head[2]

    # Create x and y coordinates for plotting
    x = np.linspace(delr / 2, length_x - delr / 2, ncol)
    y = np.linspace(delc / 2, length_y - delc / 2, nrow)
    X, Y = np.meshgrid(x, y)

    # Plot hydraulic head map with contour lines
    plt.figure(figsize=(7, 6))
    image = plt.imshow(
        head_layer3,
        extent=[0, length_x, 0, length_y],
        origin="lower",
    )

    plt.colorbar(image, label="Hydraulic head (m)")
    plt.contour(X, Y, head_layer3, levels=10, colors="black", linewidths=0.5)


    # Add pumping well locations to the plot
    well_x = []
    well_y = []

    for cell, rate in well_spd:
        layer, row, col = cell
        well_x.append((col + 0.5) * delr)
        well_y.append((row + 0.5) * delc)

    plt.scatter(well_x, well_y, marker="x", s=80, label="Pumping wells", color="red",
   linewidths=2)
    
    plt.legend()


    
    plt.title("Head with Wells - Layer 3")
    plt.xlabel("x (m)")
    plt.ylabel("y (m)")

    # Save and show the figure
    plot_path = workspace / "head_with_recharge_and_wells_layer3.png"
    plt.savefig(plot_path, dpi=300, bbox_inches="tight")
    plt.show()

    print("Baseline head plot saved:", plot_path)




        # Plot hydraulic conductivity distribution in Layer 2
    plt.figure(figsize=(7, 6))

    k_image = plt.imshow(
        k_array[1],
        extent=[0, length_x, 0, length_y],
        origin="lower",
    )

    plt.colorbar(k_image, label="Hydraulic conductivity K (m/day)")
    plt.title("Low-K Zone in Layer 2")
    plt.xlabel("x (m)")
    plt.ylabel("y (m)")

    k_plot_path = figures_dir / "hydraulic_conductivity_layer2_low_k_zone.png"
    plt.savefig(k_plot_path, dpi=300, bbox_inches="tight")
    plt.show()

    print("K distribution plot saved:", k_plot_path)


        # Read and print water budget information
    budget_path = workspace / budget_file
    budget_obj = flopy.utils.CellBudgetFile(budget_path)

    print("Available budget terms:")
    print(budget_obj.get_unique_record_names())



        # Summarize main water budget terms
    def get_budget_total(budget_obj, term):
        data = budget_obj.get_data(text=term)[-1]

        if hasattr(data, "dtype") and data.dtype.names is not None:
            if "q" in data.dtype.names:
                return float(data["q"].sum())

        return float(np.asarray(data).sum())


    budget_terms = ["CHD", "WEL", "RCHA", "STO-SS", "STO-SY"]

    print("\nWater budget summary at final time:")
    for term in budget_terms:
        try:
            total = get_budget_total(budget_obj, term)
            print(f"{term:8s}: {total:12.3f} m3/day")
        except Exception as e:
            print(f"{term:8s}: could not read ({e})")


    # Calculate drawdown in Layer 3 relative to the initial head
    drawdown_layer3 = initial_head - head_layer3

    print(
        "Layer 3 drawdown range:",
        np.nanmin(drawdown_layer3),
        "to",
        np.nanmax(drawdown_layer3),
        "m"
    )

    # Plot drawdown map
    plt.figure(figsize=(7, 6))

    dd_image = plt.imshow(
        drawdown_layer3,
        extent=[0, length_x, 0, length_y],
        origin="lower",
    )

    plt.colorbar(dd_image, label="Drawdown relative to initial head (m)")
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
    plt.title("Drawdown with Pumping Wells - Layer 3")
    plt.xlabel("x (m)")
    plt.ylabel("y (m)")

    drawdown_plot_path = figures_dir / "drawdown_layer3_pumping_wells.png"
    plt.savefig(drawdown_plot_path, dpi=300, bbox_inches="tight")
    plt.show()

    print("Drawdown plot saved:", drawdown_plot_path)


















else:
    print("MODFLOW 6 simulation failed.")