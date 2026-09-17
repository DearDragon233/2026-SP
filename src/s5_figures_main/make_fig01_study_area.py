# -*- coding: utf-8 -*-
"""Merged manuscript Fig 1: Study area + four yield targets + provenance flow.
Panels: (A) 234-grid map colored by elevation (the PC1 axis made visible),
A-target (43) outlined, D-target (n_px>=4, 22) marked with triangles;
(B) four-target yield distributions; (C) provenance flow diagram.
Style: config/style_2026sp.mplstyle, 600 dpi png+tiff."""
import os, sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D

ROOT = r"D:\2026-SP"
sys.path.insert(0, os.path.join(ROOT, "src"))
# style_2026sp.mplstyle has GBK-encoded comment bytes; mirror its values here
plt.rcParams.update({"font.family": "sans-serif", "font.size": 10,
                     "axes.labelsize": 11, "axes.titlesize": 12,
                     "xtick.labelsize": 9, "ytick.labelsize": 9, "legend.fontsize": 9,
                     "figure.dpi": 300, "savefig.dpi": 600, "savefig.bbox": "tight",
                     "axes.spines.top": False, "axes.spines.right": False})

INT = os.path.join(ROOT, "Outputs", "intermediate")
OUT = os.path.join(ROOT, "Outputs", "figures", "main")
os.makedirs(OUT, exist_ok=True)

C = {"blue": "#2F5496", "red": "#c5221f", "orange": "#e37400", "green": "#1b8a4a",
     "grey": "#8c8c8c", "purple": "#6a0dad", "teal": "#008080"}

df = pd.read_csv(os.path.join(INT, "zenodo_yield_2021_grid.csv"))
mA = df["wheat_yield_tha"].notna().values                     # A: process-model baseline (43)
mD4 = (df["n_px"] >= 4).values                                # D: RS retrieval, n_px>=4 (22)
mD = (df["n_px"] > 0).values                                  # D loose (23)
targets = {"A_process_model_43": df.loc[mA, "wheat_yield_tha"].values,
           "B_interpolated_234": df["wheat_yield_pred_tha"].values,
           "C_blended_234": df["yield_blended_tha"].values,
           "D_rs_retrieval_22": df.loc[mD4, "zenodo_yield_tha"].values}

fig = plt.figure(figsize=(9.5, 7.6))
gs = fig.add_gridspec(2, 2, width_ratios=[1.25, 1], height_ratios=[1.15, 1],
                      hspace=0.42, wspace=0.28, left=0.07, right=0.97, top=0.93, bottom=0.08)

# ---------- Panel A: study-area map ----------
axA = fig.add_subplot(gs[:, 0])
sc = axA.scatter(df["lon"], df["lat"], c=df["elevation_m"], cmap="viridis",
                 s=34, edgecolors="none", zorder=2)
axA.scatter(df.loc[mA, "lon"], df.loc[mA, "lat"], s=90, facecolors="none",
            edgecolors=C["red"], linewidths=1.4, zorder=3,
            label="A: process-model baseline (43)")
axA.scatter(df.loc[mD4, "lon"], df.loc[mD4, "lat"], marker="^", s=46,
            facecolors="white", edgecolors=C["purple"], linewidths=1.2, zorder=4,
            label="D: RS retrieval, n_px$\\geq$4 (22)")
cb = fig.colorbar(sc, ax=axA, pad=0.015, fraction=0.045)
cb.set_label("Elevation (m)", fontsize=9)
axA.set_xlabel("Longitude ($^\\circ$E)")
axA.set_ylabel("Latitude ($^\\circ$N)")
axA.set_title("(A) 234-grid environmental matrix (0.0417$^\\circ$ $\\approx$ 3.6$\\times$4.6 km)", loc="left", fontsize=11)
handles, labels_ = axA.get_legend_handles_labels()
handles.append(Line2D([], [], marker="o", linestyle="none", color="#440154",
                      markerfacecolor="#440154", markersize=7,
                      label="grid colour = elevation (PC1 axis, r = $-$0.94)"))
axA.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, -0.13),
           ncol=2, frameon=False, fontsize=8.5)
axA.set_aspect(1 / np.cos(np.radians(40.2)))

# ---------- Panel B: target distributions ----------
axB = fig.add_subplot(gs[0, 1])
data, labels, cols = [], [], []
for k, (name, v) in enumerate(targets.items()):
    data.append(v[~np.isnan(v)])
    labels.append(f"{name.split('_')[0]} (n={len(data[-1])})")
    cols.append([C["red"], C["blue"], C["green"], C["purple"]][k])
bp = axB.boxplot(data, tick_labels=labels, widths=0.55, patch_artist=True, showfliers=False,
                 medianprops=dict(color="black", linewidth=1.2))
for patch, c in zip(bp["boxes"], cols):
    patch.set_facecolor(c); patch.set_alpha(0.55); patch.set_edgecolor(c)
for i, v in enumerate(data, 1):
    axB.scatter(np.random.default_rng(7).normal(i, 0.05, len(v)), v, s=7, color=cols[i-1],
                alpha=0.65, edgecolors="none", zorder=3)
    axB.text(i, np.max(v), f"$\\mu$={np.mean(v):.2f}", ha="center", va="bottom", fontsize=8)
axB.axhline(5.241, color=C["grey"], linestyle="--", linewidth=1)
axB.text(0.55, 5.28, "Beijing statistical mean 5.24 t/ha", fontsize=7.5, color=C["grey"], va="bottom", ha="left")
axB.set_ylabel("Yield (t/ha)")
axB.set_title("(B) Four model-derived yield targets", loc="left", fontsize=11)

# ---------- Panel C: provenance flow ----------
axC = fig.add_subplot(gs[1, 1])
axC.set_xlim(0, 12); axC.set_ylim(0, 10); axC.axis("off")
def box(x, y, w, h, text, fc, ec, fs=6.9):
    axC.add_patch(mpatches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.12",
                 facecolor=fc, edgecolor=ec, linewidth=1.1))
    axC.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs)
def arrow(x1, y1, x2, y2):
    axC.annotate("", xy=(x2, y2), xytext=(x1, y1),
                 arrowprops=dict(arrowstyle="->", color=C["grey"], lw=1.2))
box(0.1, 7.3, 3.4, 2.2, "Xiao et al. 2024\n(Nature Food) process\nmodel, baseline 1-km\nraster", "#fdf2f0", C["red"])
box(4.3, 7.3, 2.4, 2.2, "A (43)\n7.21$\\pm$0.23\nt/ha", "#fdf2f0", C["red"])
box(8.0, 7.3, 3.9, 2.2, "D (22)\nChinaWheatYield30m\nSentinel retrieval", "#f5effa", C["purple"])
box(5.0, 4.2, 2.8, 2.2, "B (234)\nRidge interpolation\n(train fit R$^2$=0.99)", "#eef3fb", C["blue"])
box(5.0, 1.1, 2.8, 2.2, "C (234)\nBayesian blend\n+ district prior 6.0", "#eef7f0", C["green"])
arrow(3.55, 8.4, 4.25, 8.4); arrow(6.75, 8.4, 7.95, 8.4)
axC.text(9.95, 6.82, "independent source", ha="center", fontsize=6.9, color=C["grey"], style="italic")
arrow(6.4, 7.25, 6.4, 6.5); arrow(6.4, 4.15, 6.4, 3.4)
axC.text(6.85, 3.78, "district prior 6.0 t/ha", fontsize=6.9, color=C["grey"], ha="left")
axC.text(0.1, 2.2, "No field-measured target\navailable (district/field\nlevels = gaps G1/G2)",
         fontsize=6.9, color=C["red"], ha="left", va="center", style="italic")
axC.text(0, 10.35, "(C) Target provenance flow", fontsize=11, ha="left")

fig.savefig(os.path.join(OUT, "fig01_study_area.png"), dpi=600)
fig.savefig(os.path.join(OUT, "fig01_study_area.tiff"), dpi=600, pil_kwargs={"compression": "tiff_lzw"})
print("fig01 saved:", os.path.join(OUT, "fig01_study_area.png"))
print("A grids:", int(mA.sum()), "| D n_px>=4:", int(mD4.sum()), "| D n_px>0:", int(mD.sum()))
