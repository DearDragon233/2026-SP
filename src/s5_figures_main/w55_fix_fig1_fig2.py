# -*- coding: utf-8 -*-
"""W55: fix Figure 1 (restore county polygon outlines) and Figure 2 (legend clear of labels)."""
import os, json
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from shapely.geometry import shape

ROOT = r"D:\2026-SP"; REP = os.path.join(ROOT, "Outputs", "reports")
OUT = os.path.join(ROOT, "ManageFiles", "Submission_package_Paper2", "figures")
plt.rcParams.update({"font.family": "sans-serif", "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
                     "font.size": 7.5, "axes.labelsize": 8, "axes.titlesize": 8.5,
                     "xtick.labelsize": 6.8, "ytick.labelsize": 6.8, "legend.fontsize": 6.6,
                     "axes.linewidth": 0.6, "axes.spines.top": False, "axes.spines.right": False,
                     "pdf.fonttype": 42, "figure.dpi": 300, "savefig.dpi": 600})
OK = {"blue": "#0072B2", "orange": "#E69F00", "green": "#009E73", "red": "#D55E00", "grey": "#999999"}
MM = 1/25.4

# ================= Figure 1 =================
cov = pd.read_csv(os.path.join(REP, "w53_zhoukou_coverage.csv"))
gj = json.load(open(os.path.join(ROOT, "Data", "external", "ncp_yield_pairing", "download",
                                 "geoBoundaries-CHN-ADM3.geojson"), encoding="utf-8"))
PIN = {"扶沟": "Fugou", "西华": "Xihua", "商水": "Shangshui", "沈丘": "Shenqiu",
       "郸城": "Dancheng", "太康": "Taikang", "鹿邑": "Luyi", "项城": "Xiangcheng"}
id2zh = {r.shape_id: r.county for r in cov.drop_duplicates("county").itertuples()}
def rings(coords):
    if isinstance(coords[0], (int, float)):
        yield coords
    else:
        for c in coords:
            yield from rings(c)

fig, axes = plt.subplots(1, 2, figsize=(183*MM, 76*MM), gridspec_kw={"width_ratios": [1, 1.25]})
ax = axes[0]
pass_all = cov.groupby("county").pass_primary.all()
for f in gj["features"]:
    sid = f["properties"].get("shapeID")
    if sid not in id2zh: continue
    zh = id2zh[sid]
    col = OK["green"] if pass_all[zh] else OK["red"]
    geom = shape(f["geometry"])
    polys = list(geom.geoms) if geom.geom_type == "MultiPolygon" else [geom]
    for poly in polys:
        for ring in [poly.exterior] + list(poly.interiors):
            pts = np.array(ring.coords)
            ax.plot(pts[:, 0], pts[:, 1], color=col, lw=0.9 if ring is poly.exterior else 0.5)
    r = cov[cov.county == zh].iloc[0]
    dx, dy = {"项城": (0.0, -0.045), "沈丘": (0.13, 0.045)}.get(zh, (0.0, 0.0))
    ax.text(r.centre_lon + dx, r.centre_lat + dy, PIN[zh], ha="center", va="center", fontsize=6.3,
            bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.75))
ax.set_xlim(114.15, 115.75); ax.set_ylim(33.0, 34.4); ax.set_aspect(1 / np.cos(np.radians(33.7)))
ax.set_xlabel("Longitude (E)"); ax.set_ylabel("Latitude (N)")
ax.set_title("(a) Zhoukou counties (green: primary screen passed)", loc="left", fontweight="bold", fontsize=8)

ax = axes[1]
d = cov.sort_values(["county", "harvest_year"]).reset_index(drop=True)
AB = {"Shangshui": "ShS", "Shenqiu": "ShQ"}
labels = [f"{AB.get(PIN[r.county], PIN[r.county][:3])}-{str(r.harvest_year)[2:]}" for r in d.itertuples()]
cols = [OK["green"] if p else OK["red"] for p in d.pass_primary]
ax.bar(range(len(d)), d.area_ratio_rs_over_stats, color=cols, width=0.72)
ax.axhline(2/3, color=OK["grey"], ls=":", lw=0.8)
ax.axhline(1.0, color="#444444", lw=0.8)
ax.axhline(1.5, color=OK["grey"], ls=":", lw=0.8)
ax.set_xticks(range(len(d))); ax.set_xticklabels(labels, rotation=60, ha="right", fontsize=6)
ax.set_ylabel("Positive satellite area / yearbook sown area")
ax.set_ylim(0, 1.9)
ax.set_title("(b) Coverage ratio by county-year", loc="left", fontweight="bold", fontsize=8)
ax.text(len(d) - 0.6, 1.545, "upper limit 1.5", fontsize=6, color=OK["grey"], ha="right")
ax.text(len(d) - 0.6, 0.705, "lower limit 2/3", fontsize=6, color=OK["grey"], ha="right")
fig.tight_layout()
fig.savefig(os.path.join(OUT, "Figure1_zhoukou_coverage.png"), bbox_inches="tight"); plt.close(fig)

# ================= Figure 2 =================
pm = pd.read_csv(os.path.join(REP, "w45_primary_metrics.csv"))
pri = pm[pm.scenario == "primary"]
schemes = [("forward_year", "(a) Forward-year (n = 45)"), ("leave_region", "(b) Leave-region (n = 79)"),
           ("region_and_future", "(c) Region and future year (n = 45)")]
models = ["mean", "ridge", "random_forest"]; mlab = ["Mean", "Ridge", "RF"]
mcols = [OK["grey"], OK["blue"], OK["orange"]]
fig, axes = plt.subplots(1, 3, figsize=(183*MM, 66*MM))
x = np.arange(3); w = 0.36
for ax, (sch, ttl) in zip(axes, schemes):
    sub = pri[pri.scheme == sch]
    ymax = 0
    for gi, L in enumerate(["statistics", "remote"]):
        vals = [float(sub[(sub.training_label == L) & (sub.model == m)].mae_kg_ha.iloc[0]) for m in models]
        xpos = x + (-w/2 if gi == 0 else w/2)
        ax.bar(xpos, vals, w, color=mcols, alpha=1.0 if gi == 0 else 0.6,
               hatch="" if gi == 0 else "//", edgecolor="black", linewidth=0.4)
        for xi, v in zip(xpos, vals):
            ax.text(xi, v + ymax * 0.012 + 6, f"{v:.0f}", ha="center", fontsize=5.6)
        ymax = max(ymax, max(vals))
    ax.set_ylim(0, ymax * 1.32)
    ax.set_xticks(x); ax.set_xticklabels(mlab, fontsize=7)
    ax.set_title(ttl, loc="left", fontweight="bold", fontsize=8)
    ax.set_ylabel("MAE (kg/ha)")
# single figure-level legend (no overlap with bars)
from matplotlib.patches import Patch
handles = [Patch(fc=OK["grey"], ec="black", lw=0.4, label="Training mean"),
           Patch(fc=OK["blue"], ec="black", lw=0.4, label="Ridge"),
           Patch(fc=OK["orange"], ec="black", lw=0.4, label="Random forest"),
           Patch(fc="white", ec="black", lw=0.4, label="solid: statistical training label"),
           Patch(fc="white", ec="black", lw=0.4, hatch="//", label="hatched: satellite training label")]
fig.legend(handles=handles, loc="lower center", ncol=5, frameon=False, fontsize=6.3, bbox_to_anchor=(0.5, -0.03))
fig.tight_layout(rect=[0, 0.07, 1, 1])
fig.savefig(os.path.join(OUT, "Figure2_label_swap_development.png"), bbox_inches="tight"); plt.close(fig)
print("Figure 1 and Figure 2 rebuilt")
