# -*- coding: utf-8 -*-
"""W25-R9: fig16 co-construction bias (183mm).
(a) the two published yield products disagree everywhere: NCP grid-level
    correlation r=0.017 (5,652 cells), Pinggu B-vs-D r=0.46 (22 cells);
(b) yet environment explains ~65% of BOTH uncorrelated targets - high R2
    cannot mean 'environment explains yield'; it means each product's
    construction rule is environment-dependent."""
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
MM = 1/25.4
fig, (a, b) = plt.subplots(1, 2, figsize=(183*MM, 72*MM))

# (a) products disagree: scatter RS vs panel on common NCP cells
M = pd.read_csv(os.path.join(INT, "w22_r2_national_EMM.csv"))
R = pd.read_csv(os.path.join(INT, "w25_r2_national_rs_target.csv"))
key = lambda d: d.lon.round(4).astype(str) + "_" + d.lat.round(4).astype(str)
R["_k"] = key(R); M["_k"] = key(M)
D = M.merge(R[["rs_yield_tha", "_k"]], on="_k")
D = D[D.rs_yield_tha.notna()]
rng = np.random.default_rng(3)
idx = rng.choice(len(D), 2500, replace=False)
a.scatter(D.History.values[idx], D.rs_yield_tha.values[idx], s=3.2, alpha=0.35,
          color="#4477AA", edgecolors="none")
r = np.corrcoef(D.History, D.rs_yield_tha)[0, 1]
a.set_xlabel("Xiao et al. 2024 panel yield (optimised rotation, t/ha)")
a.set_ylabel("ChinaWheatYield30m 2021 (actual wheat, t/ha)")
a.set_title("(a)  Two published products disagree (NCP, 5,652 cells)", loc="left")
a.text(0.04, 0.93, f"Pearson r = {r:.3f}", transform=a.transAxes, va="top", fontsize=7)

# (b) same environment model 'explains' both
dual = pd.read_csv(os.path.join(INT, "w25_r3_dual_target.csv"))
schemes = pd.read_csv(os.path.join(INT, "w25_r4_rs_schemes.csv"))
labels = ["Panel target\n(optimised rotation)", "RS target\n(actual wheat)"]
rands = [float(dual[dual.target.str.startswith("panel")].random_cv_r2.iloc[0]),
         float(dual[dual.target.str.startswith("RS")].random_cv_r2.iloc[0])]
chks = [0.6021, float(schemes[schemes.scheme == "checker_2x"].pooled_mean.iloc[0])]
lats = [0.3705, float(schemes[schemes.scheme == "lat_block5"].pooled_mean.iloc[0])]
x = np.arange(2); w = 0.26
b.bar(x - w, rands, w, color="#228833", label="Random CV")
b.bar(x, chks, w, color="#CCBB44", label="Checkerboard")
b.bar(x + w, lats, w, color="#AA3377", label="Latitude blocks")
for i in range(2):
    b.text(x[i]-w, rands[i]+0.012, f"{rands[i]:.2f}", ha="center", fontsize=6)
    b.text(x[i], chks[i]+0.012, f"{chks[i]:.2f}", ha="center", fontsize=6)
    b.text(x[i]+w, lats[i]+0.012, f"{lats[i]:.2f}", ha="center", fontsize=6)
b.set_xticks(x); b.set_xticklabels(labels); b.set_ylim(0, 0.82)
b.set_ylabel(r"Environment-only model, pooled R$^2$")
b.set_title("(b)  ...yet the same environment model 'explains' both", loc="left")
b.legend(frameon=False, loc="lower left")
b.text(0.98, 0.55, "co-construction bias:\nhigh R² on uncorrelated\ntargets = predicting each\nproduct's construction rule",
       transform=b.transAxes, ha="right", fontsize=5.8, style="italic", color="#666666")

fig.tight_layout(w_pad=2.0)
fig.savefig(os.path.join(OUT, "fig16_coconstruction_bias.pdf"))
fig.savefig(os.path.join(OUT, "fig16_coconstruction_bias.png"), dpi=600)
fig.savefig(os.path.join(OUT, "fig16_coconstruction_bias.tiff"), dpi=600, pil_kwargs={"compression": "tiff_lzw"})
print("fig16 saved")
