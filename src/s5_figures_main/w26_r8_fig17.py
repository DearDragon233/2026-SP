# -*- coding: utf-8 -*-
"""W26-R8: fig17 cross-year stability & statistical arbitration (183mm).
(a) inter-annual pattern correlations are intermittent (2016-2021 r=0.88,
    2020 breaks: r~ -0.1 to both) - pairwise reporting required;
(b) NBS statistics arbitrate: RS provincial ranks match (rho=0.89), panel
    do not (rho=-0.04) - yet E 'explains' both equally."""
import os
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

ROOT = r"D:\2026-SP"; INT = os.path.join(ROOT, "Outputs", "intermediate")
OUT = os.path.join(ROOT, "Outputs", "figures", "main")
plt.rcParams.update({"font.family": "sans-serif", "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
                     "font.size": 7, "axes.labelsize": 7.5, "axes.titlesize": 8,
                     "xtick.labelsize": 6.5, "ytick.labelsize": 6.5, "legend.fontsize": 6.2,
                     "axes.linewidth": 0.6, "axes.spines.top": False, "axes.spines.right": False,
                     "pdf.fonttype": 42, "figure.dpi": 300, "savefig.dpi": 600})
MM = 1/25.4
fig, (a, b) = plt.subplots(1, 2, figsize=(183*MM, 76*MM))

# (a) pairwise pattern-corr matrix heat cells
pm = pd.read_csv(os.path.join(INT, "w26_r1_pattern_matrix.csv"))
yrs = [2016, 2020, 2021]
Mx = np.full((3, 3), np.nan)
for _, r in pm.iterrows():
    i, j = yrs.index(int(r.y1)), yrs.index(int(r.y2))
    Mx[i, j] = Mx[j, i] = r.r
np.fill_diagonal(Mx, 1.0)
im = a.imshow(Mx, cmap="RdYlBu_r", vmin=-1, vmax=1)
a.set_xticks(range(3)); a.set_yticks(range(3))
a.set_xticklabels(yrs); a.set_yticklabels(yrs)
for i in range(3):
    for j in range(3):
        if not np.isnan(Mx[i, j]):
            a.text(j, i, f"{Mx[i, j]:.2f}", ha="center", va="center", fontsize=7,
                   color="white" if abs(Mx[i, j]) > 0.6 else "black")
a.set_title("(a)  RS pattern agreement is intermittent", loc="left")
cb = fig.colorbar(im, ax=a, fraction=0.045, pad=0.02); cb.set_label("Pearson r", fontsize=6.5)

# (b) provincial arbitration
g = pd.read_csv(os.path.join(INT, "w26_r4_province_audit.csv"))
x = np.arange(len(g)); w = 0.27
b.bar(x - w, g.stat, w, color="#4477AA", label="NBS statistics (survey)")
b.bar(x, g.rs, w, color="#228833", label="ChinaWheatYield30m")
b.bar(x + w, g.panel, w, color="#CC3311", label="Xiao 2024 panel")
b.set_xticks(x); b.set_xticklabels(g.prov, rotation=28, ha="right")
b.set_ylabel("Provincial mean yield (t/ha)")
b.set_title("(b)  Statistics arbitrate: RS real, panel detached", loc="left")
b.legend(frameon=False, loc="upper left", fontsize=5.8)
b.annotate("", xy=(2.6, 7.3), xytext=(2.6, 15.9), arrowprops=dict(arrowstyle="<->", lw=0.7, color="#666666"))
b.text(2.72, 11.2, "optimised-rotation\nsemantics (+8-9 t/ha)", fontsize=5.4, color="#666666", va="center")
b.text(0.02, 0.02, "Spearman vs NBS:  RS 0.89 (p=.007)   panel −0.04 (p=.94)",
       transform=b.transAxes, fontsize=6)

fig.tight_layout(w_pad=2.2)
fig.savefig(os.path.join(OUT, "fig17_crossyear_arbitration.pdf"))
fig.savefig(os.path.join(OUT, "fig17_crossyear_arbitration.png"), dpi=600)
fig.savefig(os.path.join(OUT, "fig17_crossyear_arbitration.tiff"), dpi=600, pil_kwargs={"compression": "tiff_lzw"})
print("fig17 saved")
