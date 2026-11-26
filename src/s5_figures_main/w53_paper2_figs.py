# -*- coding: utf-8 -*-
"""W53-R8: Paper-2 main figures (3), unified style, English/pinyin labels only.
figA: label-swap on frozen panel; figB: Zhoukou external + control arm;
figC: six-year pattern matrix heatmap."""
import os, json
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = r"D:\2026-SP"
OUT = os.path.join(ROOT, "Outputs", "figures", "paper2")
os.makedirs(OUT, exist_ok=True)
plt.rcParams.update({"font.family": "sans-serif", "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
                     "font.size": 7.5, "axes.labelsize": 8, "axes.titlesize": 8.5,
                     "xtick.labelsize": 6.8, "ytick.labelsize": 6.8, "legend.fontsize": 6.6,
                     "axes.linewidth": 0.6, "axes.spines.top": False, "axes.spines.right": False,
                     "pdf.fonttype": 42, "figure.dpi": 300, "savefig.dpi": 600})
OK = {"blue": "#0072B2", "orange": "#E69F00", "green": "#009E73", "red": "#D55E00",
      "purple": "#CC79A7", "sky": "#56B4E9", "grey": "#999999"}
MM = 1/25.4
INT = os.path.join(ROOT, "Outputs", "reports")
REP = os.path.join(ROOT, "Outputs", "reports")

def save(fig, name):
    fig.savefig(os.path.join(OUT, name + ".png"), dpi=300, bbox_inches="tight")
    fig.savefig(os.path.join(OUT, name + ".pdf"), bbox_inches="tight")
    print("saved", name)

# ---------------- Paper2 figA: label swap on frozen panel ----------------
pm = pd.read_csv(os.path.join(INT, "w45_primary_metrics.csv"))
pri = pm[pm.scenario == "primary"]
schemes = [("forward_year", "Forward-year\n(n=45)"), ("leave_region", "Leave-region\n(n=79)"),
           ("region_and_future", "Region + future year\n(n=45)")]
models = [("mean", "Training mean", OK["grey"]), ("ridge", "Ridge", OK["blue"]),
          ("random_forest", "Random forest", OK["orange"])]

# clean rebuild with explicit bars per scheme
fig, axes = plt.subplots(1, 3, figsize=(120*MM, 58*MM))
for ax, (sch, slab) in zip(axes, schemes):
    sub = pri[pri.scheme == sch]
    x = np.arange(3); w = 0.36
    for gi, (L, edge_ls) in enumerate([("statistics", "-"), ("remote", "--")]):
        vals = [float(sub[(sub.training_label == L) & (sub.model == m)].mae_kg_ha.iloc[0]) for m, _, _ in models]
        xpos = x + (-w/2 if gi == 0 else w/2)
        ax.bar(xpos, vals, w, color=[OK["grey"], OK["blue"], OK["orange"]],
               alpha=1.0 if gi == 0 else 0.55, hatch="//" if gi else "",
               edgecolor="black", linewidth=0.4,
               label=("trained on statistics" if gi == 0 else "trained on satellite"))
        for xi, v in zip(xpos, vals):
            ax.text(xi, v + 14, f"{v:.0f}", ha="center", fontsize=5.4, rotation=0)
    ax.set_xticks(x); ax.set_xticklabels(["Mean", "Ridge", "RF"], fontsize=6.8)
    ax.set_ylabel("MAE (kg/ha)")
    ax.set_title(slab, loc="left", fontsize=8.5)
axes[0].set_ylim(0, 780)
handles, labs = axes[0].get_legend_handles_labels()
axes[2].legend(handles[:2], labs[:2], frameon=False, fontsize=6, loc="upper left")
fig.suptitle("Label-source swap on the frozen Hebei-Shandong panel (test target = statistics yields)",
             fontsize=8.5, y=1.0)
fig.tight_layout()
save(fig, "paper2_figA_labelswap")

# ---------------- Paper2 figB: Zhoukou external + control arm ----------------
ctrl = json.load(open(os.path.join(REP, "w53_r6_control_arm.json"), encoding="utf-8"))
fig, axes = plt.subplots(1, 2, figsize=(120*MM, 58*MM))
xt = np.arange(3); w = 0.36
for gi, (L, lcol) in enumerate([("statistics", OK["blue"]), ("remote", OK["red"])]):
    vals = [ctrl["full_features"][L][m] for m in ["mean", "ridge", "rf"]]
    xpos = xt + (-w/2 if gi == 0 else w/2)
    axes[0].bar(xpos, vals, w, color=[OK["grey"], OK["blue"], OK["orange"]],
                alpha=1.0 if gi == 0 else 0.6, hatch="//" if gi else "",
                edgecolor="black", linewidth=0.4, label=f"trained on {L}")
    for xi, v in zip(xpos, vals):
        axes[0].text(xi, v + 14, f"{v:.0f}", ha="center", fontsize=5.6)
axes[0].set_xticks(xt); axes[0].set_xticklabels(["Training mean", "Ridge", "Random forest"], fontsize=6.2)
axes[0].set_ylabel("MAE (kg/ha)")
axes[0].set_title("(a) Zhoukou external test (n=19, full features)", loc="left", fontweight="bold")
axes[0].legend(frameon=False, fontsize=6, loc="upper left")

# control arm: remote RF full vs no-shared-precip
cfg = ["full_features", "no_shared_precip"]
cfg_lab = ["All 6 features", "Without shared\nprecip columns"]
vals = [ctrl[c]["remote"]["rf"] for c in cfg]
vals_mean = [ctrl[c]["remote"]["mean"] for c in cfg]
ax2 = axes[1]
bars = ax2.bar(cfg_lab, vals, 0.5, color=[OK["red"], OK["red"]], alpha=0.9)
for xi, v in zip(cfg_lab, vals):
    ax2.text(xi, v + 12, f"{v:.0f}", ha="center", fontsize=6.5)
ax2.set_ylabel("Remote-trained RF, MAE (kg/ha)")
ax2.set_title("(b) Control: drop satellite-shared precip inputs", loc="left", fontweight="bold")
ax2.set_ylim(0, 1900)
ax2.annotate("transfer skill persists", xy=(1, 408.9), xytext=(0.42, 1200), fontsize=6.5,
             arrowprops=dict(arrowstyle="->", lw=0.7, color="#666666"))
fig.tight_layout()
save(fig, "paper2_figB_zhoukou_control")

# ---------------- Paper2 figC: six-year pattern matrix ----------------
mx = pd.read_csv(os.path.join(ROOT, "Outputs", "intermediate", "w37_pattern_matrix.csv"))
yrs = sorted(set(list(mx.y1) + list(mx.y2)))
M = np.full((len(yrs), len(yrs)), np.nan)
for _, r in mx.iterrows():
    i, j = yrs.index(int(r.y1)), yrs.index(int(r.y2))
    M[i, j] = M[j, i] = r.pearson_r
np.fill_diagonal(M, 1.0)
fig, ax = plt.subplots(figsize=(62*MM, 58*MM))
im = ax.imshow(M, cmap="RdBu_r", vmin=-1, vmax=1)
ax.set_xticks(range(len(yrs))); ax.set_yticks(range(len(yrs)))
ax.set_xticklabels(yrs); ax.set_yticklabels(yrs)
for i in range(len(yrs)):
    for j in range(len(yrs)):
        if not np.isnan(M[i, j]):
            ax.text(j, i, f"{M[i, j]:.2f}", ha="center", va="center", fontsize=6.2,
                    color="white" if abs(M[i, j]) > 0.6 else "black")
ax.set_title("Satellite-yield pattern correlation\nbetween years (pairwise, n = 15-22)", fontsize=7.5)
cb = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.03); cb.set_label("Pearson r", fontsize=6.5)
fig.tight_layout()
save(fig, "paper2_figC_sixyear_matrix")
print("paper2 figures done")
