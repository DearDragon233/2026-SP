"""Plot the primary Pingdingshan model comparisons and deletion sensitivity."""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]


def main():
    differences = pd.read_csv(ROOT / "Outputs/reports/w50_pds_paired_differences.csv")
    figure, axis = plt.subplots(figsize=(6.8, 3.4), layout="constrained")
    levels = [
        ("ridge", "statistics", "Ridge · statistics"),
        ("random_forest", "statistics", "Random forest · statistics"),
        ("ridge", "remote", "Ridge · remote sensing"),
        ("random_forest", "remote", "Random forest · remote sensing"),
    ]
    for index, (model, label, _) in enumerate(levels):
        rows = differences.loc[differences.model.eq(model)
                               & differences.comparison.eq(f"{label}_minus_same_label_mean")]
        estimate = rows.loc[rows.omission_unit.eq("all"), "mae_difference_kg_ha"].item()
        reduced = rows.loc[rows.omission_unit.ne("all"), "mae_difference_kg_ha"]
        color = {"statistics": "#126773", "remote": "#994D2B"}[label]
        axis.hlines(index, reduced.min(), reduced.max(), color=color, linewidth=2.2)
        axis.plot(estimate, index, "o", color=color, markersize=7, markeredgecolor="white")
    axis.set_yticks(range(len(levels)), [name for _, _, name in levels])
    axis.invert_yaxis()
    axis.axvline(0, color="#484C51", linewidth=1)
    axis.grid(axis="x", color="#E5E8EA")
    axis.set_axisbelow(True)
    axis.set_xlim(-37, 830)
    axis.spines[["top", "right", "left"]].set_visible(False)
    axis.tick_params(axis="y", length=0, pad=7)
    axis.set_xlabel("MAE above the same-label training mean (kg/ha)", labelpad=8)
    axis.set_title("Pingdingshan geographic and forward-year holdout", loc="left", pad=12)
    figure.savefig(ROOT / "Outputs/figures/main/w51_pds_excess_error.png", dpi=300)
    plt.close(figure)


if __name__ == "__main__":
    main()
