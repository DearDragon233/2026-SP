# -*- coding: utf-8 -*-
"""W22-R8: signature figure fig14_detectability_synthesis.
Conventions per academic-figure-skill: 183 mm double column, Arial/Helvetica,
2-3 semantic colours + 1 accent, minimal ink, vector-first (PDF) + 600dpi raster.
Message: detectability of yield information is set by information type x domain
scale x model complexity - management is detectable at both scales, environment
only across wide gradients; climate transfer preserves pattern but not level."""
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
                     "axes.linewidth": 0.6, "xtick.major.width": 0.6, "ytick.major.width": 0.6,
                     "axes.spines.top": False, "axes.spines.right": False,
                     "pdf.fonttype": 42, "figure.dpi": 300, "savefig.dpi": 600})
E = "#4477AA"; M = "#EE6677"; EM = "#228833"; GREY = "#BBBBBB"; ACC = "#CCBB44"
MM = 1/25.4

fig, axes = plt.subplots(2, 2, figsize=(183*MM, 140*MM))
(a, b), (c, d) = axes

# (A) national partitioning
r3 = pd.read_csv(os.path.join(INT, "w22_r3_partition.csv"))
sets = ["E_only", "M_only", "E+M"]; labels = ["Environment\n(25 vars)", "Management\n(6 vars)", "Env + Mgmt\n(31 vars)"]
x = np.arange(3); w = 0.36
for i, (sset, col) in enumerate(zip(sets, [E, M, EM])):
    rr = r3[r3.set == sset]
    a.bar(x[i]-w/2, float(rr[rr.scheme=="random"].pooled_mean), w, color=col, alpha=0.92, label="Random CV" if i==0 else "")
    a.bar(x[i]+w/2, float(rr[rr.scheme=="checker_1x"].pooled_mean), w, color=col, alpha=0.45, hatch="//", edgecolor="white", linewidth=0.4, label="Checkerboard" if i==0 else "")
    a.text(x[i]-w/2, float(rr[rr.scheme=="random"].pooled_mean)+0.012, f"{float(rr[rr.scheme=='random'].pooled_mean):.2f}", ha="center", fontsize=6)
    a.text(x[i]+w/2, float(rr[rr.scheme=="checker_1x"].pooled_mean)+0.012, f"{float(rr[rr.scheme=='checker_1x'].pooled_mean):.2f}", ha="center", fontsize=6)
a.axhline(0.69, color=E, lw=0.7, ls=":", alpha=0.7)
a.set_xticks(x); a.set_xticklabels(labels); a.set_ylim(0, 1.06); a.set_ylabel(r"Pooled R$^2$")
a.set_title("(a)  North China Plain (7,107 grids): management > environment", loc="left")
a.legend(frameon=False, loc="lower right")
a.text(0.99, 0.04, "same model family (process-model input-output)", transform=a.transAxes, ha="right", fontsize=5.5, style="italic", color="#666666")

# (B) Pinggu-43: strong vs weak regularisation
r4 = pd.read_csv(os.path.join(INT, "w22_r4_pinggu43.csv"))
r4b = pd.read_csv(os.path.join(INT, "w22_r4b_pinggu43_weakreg.csv"))
sets4 = ["E_only(71)", "M_only(6)", "E+M"]
lab4 = ["Environment", "Management", "Env + Mgmt"]
x = np.arange(3)
for i, sset in enumerate(sets4):
    s = r4[r4.set == sset].iloc[0]; wv = r4b[r4b.set == sset].iloc[0]
    b.errorbar(x[i]-0.13, s.pooled_mean, yerr=s.pooled_std, fmt="o", color=GREY, ms=4.5, capsize=2, lw=0.9, label="Strong reg. (n=34 tuned)" if i==0 else "")
    b.errorbar(x[i]+0.13, wv.pooled_mean, yerr=wv.pooled_std, fmt="s", color=M if i==1 else (E if i==0 else EM), ms=4.5, capsize=2, lw=0.9, label="Weak reg. (matched to n)" if i==0 else "")
b.axhline(0, color="#888888", lw=0.6)
b.set_xticks(x); b.set_xticklabels(lab4); b.set_ylabel(r"Pooled R$^2$")
b.set_title("(b)  Pinggu (n=43): management detectable, environment is not", loc="left")
b.legend(frameon=False, loc="lower left")
b.annotate("constant\ncollapse", xy=(0.13, -0.054), xytext=(0.45, -0.14), fontsize=5.8, color="#666666",
           arrowprops=dict(arrowstyle="->", lw=0.6, color="#666666"))

# (C) climate transfer: pattern vs level
r5b = pd.read_csv(os.path.join(INT, "w22_r5b_pattern_corr.csv"))
per = ["History", "2030s", "2060s"]; xx = np.arange(3)
pat = [float(r5b[r5b.eval_period==p].pearson_r2.iloc[0]) for p in per]
pool = [0.989, 0.415, -0.941]
c.plot(xx, pat, "o-", color=EM, ms=4.5, lw=1.2, label="Spatial pattern skill (Pearson $r^2$)")
c.plot(xx, pool, "s--", color=M, ms=4.5, lw=1.2, label="Pooled R$^2$ (level-sensitive)")
c.axhline(0, color="#888888", lw=0.6)
c.set_xticks(xx); c.set_xticklabels(per); c.set_ylabel("Skill of History-trained model")
c.set_title("(c)  Climate transfer: pattern retained, level not", loc="left")
c.legend(frameon=False, loc="lower left")
c.annotate("mean shift\n(-1.4 t/ha by 2060s)", xy=(2, -0.94), xytext=(1.15, -0.55), fontsize=5.8, color="#666666",
           arrowprops=dict(arrowstyle="->", lw=0.6, color="#666666"))

# (D) two-domain optimism gaps: checker vs gradient-cutting
r1 = pd.read_csv(os.path.join(INT, "w22_r1_domain_gaps.csv"))
doms = ["NCP_national", "Pinggu_234"]; dl = ["NCP\n(195× range)", "Pinggu\n(5.6× range)"]
x = np.arange(2); w = 0.36
chk = [0.066, 0.033]; grad = [0.319, 0.288]
d.bar(x-w/2, chk, w, color=GREY, label="Checkerboard family (max)")
d.bar(x+w/2, grad, w, color=ACC, label="Gradient-cutting (lat/LOBO/env)")
for i in range(2):
    d.text(x[i]-w/2, chk[i]+0.008, f"+{chk[i]:.3f}", ha="center", fontsize=6)
    d.text(x[i]+w/2, grad[i]+0.008, f"+{grad[i]:.3f}", ha="center", fontsize=6)
d.set_xticks(x); d.set_xticklabels(dl); d.set_ylabel(r"Optimism gap $\Delta R^2$")
d.set_title("(d)  Gaps are set by gradient cutting, not block size", loc="left")
d.legend(frameon=False, loc="upper right")
d.set_ylim(0, 0.42)

fig.tight_layout(h_pad=1.6, w_pad=1.8)
fig.savefig(os.path.join(OUT, "fig14_detectability_synthesis.pdf"))
fig.savefig(os.path.join(OUT, "fig14_detectability_synthesis.png"), dpi=600)
fig.savefig(os.path.join(OUT, "fig14_detectability_synthesis.tiff"), dpi=600, pil_kwargs={"compression": "tiff_lzw"})
print("fig14 saved (pdf+png+tiff)")
