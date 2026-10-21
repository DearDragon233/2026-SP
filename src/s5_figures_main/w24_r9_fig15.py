# -*- coding: utf-8 -*-
"""W24-R9: fig15 target-semantics diagnostics (183mm double column).
(a) scenario-response fingerprint: optimised-reference targets peak at the
    reference point (any perturbation reduces or saturates yield);
(b) model-target agreement: two model yield maps of the same district share
    only ~21% of spatial variance (B vs D, n=22)."""
import os
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = r"D:\2026-SP"; INT = os.path.join(ROOT, "Outputs", "intermediate")
OUT = os.path.join(ROOT, "Outputs", "figures", "main")
plt.rcParams.update({"font.family": "sans-serif", "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
                     "font.size": 7, "axes.labelsize": 7.5, "axes.titlesize": 8,
                     "xtick.labelsize": 6.5, "ytick.labelsize": 6.5, "legend.fontsize": 6.2,
                     "axes.linewidth": 0.6, "axes.spines.top": False, "axes.spines.right": False,
                     "pdf.fonttype": 42, "figure.dpi": 300, "savefig.dpi": 600})
MN = "#CC3311"; WN = "#EE7733"; MI = "#0077BB"; WI = "#33BBEE"; GREY = "#888888"
MM = 1/25.4

fig, (a, b) = plt.subplots(1, 2, figsize=(183*MM, 72*MM), gridspec_kw={"width_ratios": [1.35, 1]})

# (a) scenario fingerprint
d = pd.read_csv(os.path.join(INT, "w24_r6_scenario_curves.csv"))
varmap = {"maize_N_kgha": ("Maize N rate", MN, "o"), "wheat_N_kgha": ("Wheat N rate", WN, "o"),
          "maize_irrig_mm": ("Maize irrigation", MI, "s"), "wheat_irrig_mm": ("Wheat irrigation", WI, "s")}
for key, (lab, col, mk) in varmap.items():
    s = d[d.perturbed == key].sort_values("factor")
    a.plot(s.factor, s.delta_vs_base, marker=mk, color=col, lw=1.1, ms=3.4, label=lab)
a.axhline(0, color=GREY, lw=0.6); a.axvline(1.0, color=GREY, lw=0.6, ls=":")
a.set_xlabel("Management perturbation (× reference level)")
a.set_ylabel(r"$\Delta$ predicted annual yield (t/ha)")
a.set_title("(a)  Scenario fingerprint: optimised-reference target peaks at reference", loc="left")
a.legend(frameon=False, ncol=2, loc="lower right")
a.annotate("surplus irrigation\npenalised", xy=(1.5, -1.36), xytext=(1.18, -2.6), fontsize=5.8, color="#666666",
           arrowprops=dict(arrowstyle="->", lw=0.6, color="#666666"))

# (b) target agreement
t = pd.read_csv(os.path.join(INT, "zenodo_yield_2021_grid.csv"))
mD = t.n_px >= 4
B = t.loc[mD, "wheat_yield_pred_tha"]; D = t.loc[mD, "zenodo_yield_tha"]
b.scatter(B, D, s=14, color="#228833", edgecolors="white", linewidths=0.4, zorder=3)
r = np.polyfit(B, D, 1); xs = np.linspace(B.min(), B.max(), 50)
b.plot(xs, np.polyval(r, xs), color="#CC3311", lw=1.0, ls="--")
b.set_xlabel("Target B: interpolated process-model yield (t/ha)")
b.set_ylabel("Target D: RS retrieval (t/ha)")
b.set_title("(b)  Two model yield maps share only ~21% of variance", loc="left")
b.text(0.04, 0.93, f"n = 22 grids\nPearson r = 0.46 (p = 0.03)", transform=b.transAxes,
       va="top", fontsize=6.2)

fig.tight_layout(w_pad=2.0)
fig.savefig(os.path.join(OUT, "fig15_target_semantics.pdf"))
fig.savefig(os.path.join(OUT, "fig15_target_semantics.png"), dpi=600)
fig.savefig(os.path.join(OUT, "fig15_target_semantics.tiff"), dpi=600, pil_kwargs={"compression": "tiff_lzw"})
print("fig15 saved")
