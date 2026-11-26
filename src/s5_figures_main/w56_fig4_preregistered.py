# -*- coding: utf-8 -*-
"""W56: Figure 4 on the pre-registered Pingdingshan set (n=6)."""
import os
import numpy as np, pandas as pd, json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = r"D:\2026-SP"; REP = os.path.join(ROOT, "Outputs", "reports")
OUT = os.path.join(ROOT, "ManageFiles", "Submission_package_Paper2", "figures")
plt.rcParams.update({"font.family": "sans-serif", "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
                     "font.size": 7.5, "axes.labelsize": 8, "axes.titlesize": 8.5,
                     "xtick.labelsize": 6.8, "ytick.labelsize": 6.8, "legend.fontsize": 6.6,
                     "axes.linewidth": 0.6, "axes.spines.top": False, "axes.spines.right": False,
                     "pdf.fonttype": 42, "figure.dpi": 300, "savefig.dpi": 600})
OK = {"blue": "#0072B2", "orange": "#E69F00", "green": "#009E73", "red": "#D55E00", "grey": "#999999"}
MM = 1/25.4

pt = pd.read_csv(os.path.join(REP, "w54_pattern_permutation_tests.csv"))          # Zhoukou + development (unchanged)
psets = pd.read_csv(os.path.join(REP, "w56_pds_by_set.csv"))
pbs = json.load(open(os.path.join(REP, "w56_pds_primary_bootstrap.json"), encoding="utf-8"))
# permutation p for the other three Pingdingshan primary arms come from w56_pds_by_set (20,000 perms each)
rows = []
for _, r in pt.iterrows():
    if r.site == "Pingdingshan": continue
    parts = r.arm.split("/")
    sch, L, m = parts if r.site == "Hebei-Shandong" else ("", parts[0], parts[1])
    rows.append({"site": r.site, "sch": sch, "L": L, "m": m, "n": r.n, "r": r.r, "lo": r.ci_lo, "hi": r.ci_hi,
                 "sig": bool(r.significant_5pct)})
for _, r in psets[psets.set == "primary"].iterrows():
    L, m = r.arm.split("/")
    sig = (r.p_perm < 0.05) and ((r.r > 0 and pbs["ci_lo"] > 0) if r.arm == "remote/random_forest" else True) if r.arm == "remote/random_forest" else (r.p_perm < 0.05)
    if r.arm == "remote/random_forest":
        lo, hi = pbs["ci_lo"], pbs["ci_hi"]
    else:   # other PDS arms: bootstrap on n=6, computed here for the CI bars
        rng = np.random.default_rng(7)
        print("  (CI for", r.arm, "requires the oof file; filled below)")
        lo = hi = np.nan
    rows.append({"site": "Pingdingshan", "sch": "", "L": L, "m": m, "n": r.n, "r": r.r, "lo": lo, "hi": hi, "sig": bool(sig)})

# bootstrap CIs for the remaining PDS primary arms, straight from the frozen predictions
from scipy.stats import pearsonr
fz = pd.read_csv(os.path.join(REP, "w48_pds_frozen.csv"))[["shape_id", "harvest_year", "primary"]].rename(columns={"primary": "fp"})
oof = pd.read_csv(os.path.join(REP, "w49_pds_oof.csv")).merge(fz, on=["shape_id", "harvest_year"])
rng = np.random.default_rng(2026)
for row in rows:
    if row["site"] == "Pingdingshan" and np.isnan(row["lo"]):
        g = oof[(oof.fp) & (oof.training_label == row["L"]) & (oof.model == row["m"])]
        p, o = g.prediction_kg_ha.values, g.stats_kg_ha.values
        bs = []
        for _ in range(20000):
            i = rng.integers(0, len(o), len(o))
            if p[i].std() > 0 and o[i].std() > 0: bs.append(pearsonr(p[i], o[i])[0])
        row["lo"], row["hi"] = np.percentile(bs, [2.5, 97.5])

def lab(row):
    mname = {"ridge": "Ridge", "random_forest": "RF"}[row["m"]]; lname = {"statistics": "stat", "remote": "sat"}[row["L"]]
    sname = {"forward_year": "fwd", "leave_region": "reg", "region_and_future": "joint", "": "ext"}[row["sch"]]
    return f"{row['site']} {sname} {mname} {lname}"
d = pd.DataFrame(rows); d["label"] = d.apply(lab, axis=1)
order = {"Zhoukou": 0, "Pingdingshan": 1, "Hebei-Shandong": 2}
d["o"] = d.site.map(order) * 10 + (d.L == "statistics").astype(int) * -1
d = d.sort_values(["o", "r"]).reset_index(drop=True)
fig, ax = plt.subplots(figsize=(120*MM, 120*MM))
yp = np.arange(len(d))[::-1]
for yi, (_, r) in zip(yp, d.iterrows()):
    col = OK["red"] if r.site == "Zhoukou" else (OK["green"] if r.site == "Pingdingshan" else OK["blue"])
    ax.plot([r.lo, r.hi], [yi, yi], color=col, lw=1.1, alpha=0.8)
    ax.plot(r.r, yi, "o", ms=5.5, mfc=col if r.sig else "white", mec=col, mew=1.2)
ax.axvline(0, color="black", lw=0.8); ax.axvspan(-0.3, 0.3, color="#EEEEEE", zorder=0)
ax.set_yticks(yp); ax.set_yticklabels(d.label, fontsize=6.4)
ax.set_xlim(-1.05, 1.05); ax.set_xlabel("Within-region rank correlation, prediction vs observed (95% bootstrap CI)")
ax.set_title("Rank skill of the 20 fitted arms; filled = significant at 5% (permutation)", loc="left", fontweight="bold")
ax.text(0.99, 0.985, "red: Zhoukou   green: Pingdingshan   blue: development panel", transform=ax.transAxes,
        ha="right", va="top", fontsize=6, color="#444444")
fig.tight_layout()
fig.savefig(os.path.join(OUT, "Figure4_rank_skill_20arms.png"), bbox_inches="tight")
fig.savefig(os.path.join(OUT, "Figure4_rank_skill_20arms.pdf"), bbox_inches="tight")
d.to_csv(os.path.join(REP, "w56_figure4_data.csv"), index=False, encoding="utf-8-sig")
print(d[["label", "n", "r", "lo", "hi", "sig"]].round(3).to_string(index=False))
