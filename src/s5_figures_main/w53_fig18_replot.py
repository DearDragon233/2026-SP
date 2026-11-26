# -*- coding: utf-8 -*-
"""W53-R2b: replot fig18 with pinyin labels (CJK glyphs unavailable in Arial)."""
import os
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = r"D:\2026-SP"
dd = pd.read_csv(os.path.join(ROOT, "Outputs", "reports", "w53_zhoukou_coverage.csv"))
PIN = {"扶沟": "Fugou", "西华": "Xihua", "商水": "Shangshui", "沈丘": "Shenqiu",
       "郸城": "Dancheng", "太康": "Taikang", "鹿邑": "Luyi", "项城": "Xiangcheng"}
dd["pinyin"] = dd.county.map(PIN)
plt.rcParams.update({"font.family": "sans-serif", "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
                     "font.size": 8, "axes.titlesize": 9, "axes.spines.top": False,
                     "axes.spines.right": False, "figure.dpi": 300, "savefig.dpi": 600,
                     "pdf.fonttype": 42})
fig, axes = plt.subplots(1, 2, figsize=(10, 4.6))
ax = axes[0]
for _, r in dd[dd.harvest_year == 2019].iterrows():
    col = "#009E73" if r.pass_primary else "#D55E00"
    ax.plot(r.centre_lon, r.centre_lat, "o", ms=9, color=col)
    ax.text(r.centre_lon, r.centre_lat + 0.03, r.pinyin, ha="center", fontsize=6.8)
ax.set_xlabel("Longitude (E)"); ax.set_ylabel("Latitude (N)")
ax.set_title("(a) Zhoukou pilot counties (dot colour = screen outcome)", loc="left", fontsize=9)
ax = axes[1]
dd_s = dd.sort_values(["county", "harvest_year"])
labels = [f"{dd_s.pinyin.iloc[i][:3]}-{dd_s.harvest_year.iloc[i]%100:02d}" for i in range(len(dd_s))]
cols = ["#009E73" if p else "#D55E00" for p in dd_s.pass_primary]
ax.bar(range(len(dd_s)), dd_s.area_ratio_rs_over_stats, color=cols, width=0.72)
ax.axhline(2/3, color="#999999", ls=":", lw=0.8)
ax.axhline(1.0, color="#444444", lw=0.8)
ax.axhline(1.5, color="#999999", ls=":", lw=0.8)
ax.set_xticks(range(len(dd_s))); ax.set_xticklabels(labels, rotation=60, ha="right", fontsize=6)
ax.set_ylabel("RS positive area / stats sown area")
ax.set_title("(b) Coverage-ratio screen (green = primary pass)", loc="left", fontsize=9)
fig.tight_layout()
fig.savefig(os.path.join(ROOT, "Outputs", "figures", "main", "fig18_zhoukou_freeze.png"), dpi=300)
fig.savefig(os.path.join(ROOT, "Outputs", "figures", "main", "fig18_zhoukou_freeze.tiff"),
            pil_kwargs={"compression": "tiff_lzw"})
print("fig18 replotted (pinyin labels)")
