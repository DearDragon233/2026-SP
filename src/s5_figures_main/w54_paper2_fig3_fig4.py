# -*- coding: utf-8 -*-
"""W54: paper-2 final figures 3 and 4 (level-pattern scatter; rank-correlation forest plot).
Paper: Manuscript_v1.0_Prediction_Level_and_Pattern.md"""
import os, json
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = r"D:\2026-SP"; REP = os.path.join(ROOT, "Outputs", "reports")
OUT = os.path.join(ROOT, "Outputs", "figures", "paper2"); os.makedirs(OUT, exist_ok=True)
plt.rcParams.update({"font.family": "sans-serif", "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
                     "font.size": 7.5, "axes.labelsize": 8, "axes.titlesize": 8.5,
                     "xtick.labelsize": 6.8, "ytick.labelsize": 6.8, "legend.fontsize": 6.6,
                     "axes.linewidth": 0.6, "axes.spines.top": False, "axes.spines.right": False,
                     "pdf.fonttype": 42, "figure.dpi": 300, "savefig.dpi": 600})
OK = {"blue": "#0072B2", "orange": "#E69F00", "green": "#009E73", "red": "#D55E00", "grey": "#999999"}
MM = 1/25.4

# ---------------- Figure 3 ----------------
oof = pd.read_csv(os.path.join(REP, "w54_zhoukou_oof.csv"))
dec = pd.read_csv(os.path.join(REP, "w54_level_pattern_decomposition_all_sites.csv"))
z = dec[dec.site == "Zhoukou"]
fig, axes = plt.subplots(1, 2, figsize=(183*MM, 72*MM), gridspec_kw={"width_ratios": [1, 1.15]})
ax = axes[0]
obs = oof.reported_kg_ha.values; pred = oof["pred_statistics_ridge"].values
ax.scatter(pred, obs, s=24, color=OK["blue"], edgecolors="white", linewidths=0.5, zorder=3)
# least-squares trend to make the negative slope visible
k, b = np.polyfit(pred, obs, 1)
xs = np.linspace(pred.min() - 30, pred.max() + 30, 20)
ax.plot(xs, k*xs + b, "-", color=OK["blue"], lw=1.0, alpha=0.8, label=f"trend, r = -0.79")
ax.axhline(obs.mean(), color=OK["red"], lw=0.9, ls=":", label="observed regional mean")
ax.axhline(6603.8, color=OK["grey"], lw=0.9, ls="-.", label="training mean (baseline)")
ax.set_xlim(xs[0], xs[-1]); ax.set_ylim(6450, 7850)
ax.set_xlabel("Predicted yield, statistical-label ridge (kg/ha)")
ax.set_ylabel("Observed statistical yield (kg/ha)")
ax.set_title("(a) Zhoukou, statistical-label ridge (n = 19)", loc="left", fontweight="bold")
ax.legend(frameon=False, loc="lower left", fontsize=6)
ax.text(0.98, 0.99, "every point below the red line: all 19 county-years under-predicted",
        transform=ax.transAxes, ha="right", va="top", fontsize=6, color=OK["red"])

ax = axes[1]
arms = [("statistics/ridge", "Ridge\nstat.", OK["blue"]), ("statistics/random_forest", "RF\nstat.", OK["orange"]),
        ("remote/ridge", "Ridge\nsat.", OK["blue"]), ("remote/random_forest", "RF\nsat.", OK["orange"])]
x = np.arange(len(arms)); w = 0.36
raw = [float(z[z.arm == a].advantage_raw.iloc[0]) for a, _, _ in arms]
rec = [float(z[z.arm == a].advantage_after_recentring.iloc[0]) for a, _, _ in arms]
hatch = ["", "", "//", "//"]
for i in range(len(arms)):
    ax.bar(x[i] - w/2, raw[i], w, color=arms[i][2], edgecolor="black", linewidth=0.4)
    ax.bar(x[i] + w/2, rec[i], w, color=arms[i][2], alpha=0.55, hatch="//", edgecolor="black", linewidth=0.4)
    ax.text(x[i] - w/2, raw[i] + (15 if raw[i] >= 0 else -30), f"{raw[i]:+.0f}", ha="center", fontsize=6)
    ax.text(x[i] + w/2, rec[i] + (15 if rec[i] >= 0 else -30), f"{rec[i]:+.0f}", ha="center", fontsize=6)
ax.axhline(0, color="black", lw=0.7)
ax.set_xticks(x); ax.set_xticklabels([a[1] for a in arms], fontsize=6.6)
ax.set_ylabel("MAE advantage over training mean (kg/ha)")
ax.set_title("(b) MAE advantage vs training mean, before and after re-centring", loc="left", fontweight="bold")
ax.set_ylim(-260, 980)
ax.text(0.98, 0.99, "positive = model better than mean\noracle constant: MAE 27.6 kg/ha",
        transform=ax.transAxes, ha="right", va="top", fontsize=6, color="#444444")
fig.tight_layout()
fig.savefig(os.path.join(OUT, "paper2_fig3_level_pattern.png"), bbox_inches="tight")
fig.savefig(os.path.join(OUT, "paper2_fig3_level_pattern.pdf"), bbox_inches="tight")
plt.close(fig)

# ---------------- Figure 4 ----------------
pt = pd.read_csv(os.path.join(REP, "w54_pattern_permutation_tests.csv"))
lab = {"Zhoukou": "Zhoukou", "Pingdingshan": "Pingdingshan",
       "Hebei-Shandong": "Dev."}
def lab2(site, arm):
    parts = arm.split("/")
    if site == "Hebei-Shandong":
        sch, L, m = parts
    else:
        sch, L, m = "", parts[0], parts[1]
    mname = {"ridge": "Ridge", "random_forest": "RF"}[m]; lname = {"statistics": "stat", "remote": "sat"}[L]
    sname = {"forward_year": "fwd", "leave_region": "reg", "region_and_future": "joint", "": "ext"}[sch]
    return f"{lab[site]} {sname} {mname} {lname}"
pt["label"] = [lab2(s, a) for s, a in zip(pt.site, pt.arm)]
order = {"Zhoukou": 0, "Pingdingshan": 1, "Hebei-Shandong": 2}
pt["o"] = pt.site.map(order) * 10 + pt.arm.str.contains("statistics").astype(int) * -1
pt = pt.sort_values(["o", "r"]).reset_index(drop=True)
fig, ax = plt.subplots(figsize=(120*MM, 120*MM))
ypos = np.arange(len(pt))[::-1]
for yi, (_, r) in zip(ypos, pt.iterrows()):
    col = OK["red"] if r.site == "Zhoukou" else (OK["green"] if r.site == "Pingdingshan" else OK["blue"])
    filled = bool(r.significant_5pct)
    ax.plot([r.ci_lo, r.ci_hi], [yi, yi], color=col, lw=1.1, alpha=0.8)
    ax.plot(r.r, yi, "o" if filled else "o", ms=5.5, mfc=col if filled else "white", mec=col, mew=1.2)
ax.axvline(0, color="black", lw=0.8)
ax.axvspan(-0.3, 0.3, color="#EEEEEE", zorder=0)
ax.set_yticks(ypos); ax.set_yticklabels(pt.label, fontsize=6.4)
ax.set_xlim(-1.05, 1.05); ax.set_xlabel("Within-region rank correlation, prediction vs observed (95% bootstrap CI)")
ax.set_title("Rank skill of the 20 fitted arms; filled = significant at 5% (permutation)", loc="left", fontweight="bold")
ax.text(0.99, 0.985, "red: Zhoukou  green: Pingdingshan  blue: development panel", transform=ax.transAxes,
        ha="right", va="top", fontsize=6, color="#444444")
fig.tight_layout()
fig.savefig(os.path.join(OUT, "paper2_fig4_rank_forest.png"), bbox_inches="tight")
fig.savefig(os.path.join(OUT, "paper2_fig4_rank_forest.pdf"), bbox_inches="tight")
plt.close(fig)
print("fig3 + fig4 saved")
