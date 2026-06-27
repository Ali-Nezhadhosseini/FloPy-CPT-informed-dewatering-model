from pathlib import Path
import matplotlib.pyplot as plt
import csv

project_dir = Path(__file__).resolve().parent

figures_dir = project_dir / "figures"
figures_dir.mkdir(exist_ok=True)

data_dir = project_dir / "data"
data_dir.mkdir(exist_ok=True)

# Sensitivity results from manual MODFLOW runs
k_layer3_values = [5.0, 10.0, 20.0]
max_drawdown_values = [1.6026915947103524, 0.869345987282472, 0.4563221049628903]

# Save results as CSV
csv_path = data_dir / "sensitivity_k_layer3_results.csv"

with open(csv_path, mode="w", newline="") as file:
    writer = csv.writer(file)
    writer.writerow(["k_layer3_m_per_day", "max_pumping_drawdown_m"])

    for k, dd in zip(k_layer3_values, max_drawdown_values):
        writer.writerow([k, dd])

print("Sensitivity CSV saved:", csv_path)

# Plot sensitivity curve
plt.figure(figsize=(7, 5))

plt.plot(
    k_layer3_values,
    max_drawdown_values,
    marker="o",
    linewidth=2,
)

plt.xlabel("Layer 3 hydraulic conductivity K (m/day)")
plt.ylabel("Maximum pumping-only drawdown (m)")
plt.title("Sensitivity of Drawdown to Layer 3 Hydraulic Conductivity")
plt.grid(True)

plot_path = figures_dir / "sensitivity_k_layer3_drawdown.png"
plt.savefig(plot_path, dpi=300, bbox_inches="tight")
plt.show()

print("Sensitivity plot saved:", plot_path)