from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent

RAW_DIR = ROOT / "data" / "raw" / "usgs_pajaro"
DATA_DIR = ROOT / "data"
FIG_DIR = ROOT / "figures"

raw_files = sorted(RAW_DIR.glob("*_raw.txt"))

print("Project root:", ROOT)
print("Raw folder:", RAW_DIR)
print("Number of raw files:", len(raw_files))

for file in raw_files:
    print(file.name)


def get_metadata(lines, key):
    for line in lines:
        if key in line:
            parts = line.split("\t")
            if len(parts) > 1:
                return parts[1].strip().replace('"', "")
    return None


def read_cpt_file(file_path):
    file_path = Path(file_path)
    lines = file_path.read_text(encoding="utf-8", errors="ignore").splitlines()

    point_id = file_path.stem.replace("_raw", "")
    utm_x = get_metadata(lines, "UTM-X")
    utm_y = get_metadata(lines, "UTM-Y")
    elevation = get_metadata(lines, "Elevation")
    total_depth = get_metadata(lines, "Total depth")
    water_depth = get_metadata(lines, "Water depth")

    header_index = None
    for i, line in enumerate(lines):
        if line.startswith("Depth"):
            header_index = i
            break

    df = pd.read_csv(
        file_path,
        sep=r"\t+",
        skiprows=header_index + 1,
        header=None,
        names=["depth_m", "qc_MPa", "fs_kPa", "inclination_degree", "s_wave_travel_time_ms"],
        engine="python"
    )

    df["point_id"] = point_id
    df["utm_x_m"] = pd.to_numeric(utm_x, errors="coerce")
    df["utm_y_m"] = pd.to_numeric(utm_y, errors="coerce")
    df["elevation_m"] = pd.to_numeric(elevation, errors="coerce")
    df["total_depth_m"] = pd.to_numeric(total_depth, errors="coerce")
    df["water_depth_m"] = pd.to_numeric(water_depth, errors="coerce")

    for col in ["depth_m", "qc_MPa", "fs_kPa"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=["depth_m", "qc_MPa", "fs_kPa"])

    # remove bad/end-marker values
    df = df[df["qc_MPa"] > 0]
    df = df[df["fs_kPa"] >= 0]

    df["Rf_percent"] = df["fs_kPa"] / (df["qc_MPa"] * 1000) * 100

    return df


all_cpt = pd.concat([read_cpt_file(f) for f in raw_files], ignore_index=True)

output_path = DATA_DIR / "processed_cpt_pajaro.csv"
all_cpt.to_csv(output_path, index=False)

print("Saved:", output_path)
print("Rows:", len(all_cpt))
print(all_cpt.head())


# =========================
# Plot CPT profiles
# =========================

processed_path = DATA_DIR / "processed_cpt_pajaro.csv"
cpt = pd.read_csv(processed_path)

print("Loaded:", processed_path)
print("Rows:", len(cpt))
print("Points:", cpt["point_id"].unique())

# quick data check
print("\nBasic check:")
print(cpt[["depth_m", "qc_MPa", "fs_kPa", "Rf_percent"]].describe())

# plot qc, fs, Rf for all CPT points
points = sorted(cpt["point_id"].unique())

fig, axes = plt.subplots(1, 3, figsize=(12, 8), sharey=True)

for point in points:
    dfp = cpt[cpt["point_id"] == point].sort_values("depth_m")

    axes[0].plot(dfp["qc_MPa"], dfp["depth_m"], label=point)
    axes[1].plot(dfp["fs_kPa"], dfp["depth_m"], label=point)
    axes[2].plot(dfp["Rf_percent"], dfp["depth_m"], label=point)

axes[0].set_xlabel("qc [MPa]")
axes[0].set_title("Tip resistance")

axes[1].set_xlabel("fs [kPa]")
axes[1].set_title("Sleeve friction")

axes[2].set_xlabel("Rf [%]")
axes[2].set_title("Friction ratio")

axes[0].set_ylabel("Depth [m]")

for ax in axes:
    ax.grid(True)
    ax.invert_yaxis()

axes[2].legend(loc="lower right", fontsize=8)

fig.suptitle("CPT Profiles - Pajaro Site", y=0.95)
plt.tight_layout()

plot_path = FIG_DIR / "cpt_profiles_all_points.png"
plt.savefig(plot_path, dpi=300, bbox_inches="tight")
plt.show()

print("Saved:", plot_path)



# =========================
# Add interpreted layer boundaries
# =========================

layer_bounds = [4, 10]

fig, axes = plt.subplots(1, 3, figsize=(12, 8), sharey=True)

for point in points:
    dfp = cpt[cpt["point_id"] == point].sort_values("depth_m")

    axes[0].plot(dfp["qc_MPa"], dfp["depth_m"], label=point)
    axes[1].plot(dfp["fs_kPa"], dfp["depth_m"], label=point)
    axes[2].plot(dfp["Rf_percent"], dfp["depth_m"], label=point)

for ax in axes:
    for z in layer_bounds:
        ax.axhline(z, color="black", linestyle="--", linewidth=1)
    ax.grid(True)
    ax.invert_yaxis()

axes[0].set_xlabel("qc [MPa]")
axes[0].set_ylabel("Depth [m]")
axes[0].set_title("Tip resistance")

axes[1].set_xlabel("fs [kPa]")
axes[1].set_title("Sleeve friction")

axes[2].set_xlabel("Rf [%]")
axes[2].set_title("Friction ratio")
axes[2].legend(loc="lower right", fontsize=8)

fig.suptitle("CPT Profiles with Interpreted Layer Boundaries", y=0.95)
plt.tight_layout()

plot_path2 = FIG_DIR / "cpt_profiles_with_layers.png"
plt.savefig(plot_path2, dpi=300, bbox_inches="tight")
plt.show()

print("Saved:", plot_path2)