# -*- coding: utf-8 -*-
"""W53-R2: Zhoukou freeze groundwork - polygon disambiguation by centroid,
RS positive-area extraction (2019/2020/2021), area-ratio screening vs W52
yearbook sown area. Freezes only rows passing the primary rule (2/3-1.5)."""
import os, json, glob, warnings
import numpy as np, pandas as pd
warnings.filterwarnings("ignore")
import rasterio
from rasterio.windows import from_bounds as fb_win
from rasterio.features import geometry_mask
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = r"D:\2026-SP"
GJ = os.path.join(ROOT, "Data", "external", "ncp_yield_pairing", "download", "geoBoundaries-CHN-ADM3.geojson")
CAND = os.path.join(ROOT, "Data", "external", "w52_zhoukou_candidate_stats.csv")
OUT = os.path.join(ROOT, "Outputs", "reports")
FIGDIR = os.path.join(ROOT, "Outputs", "figures", "main")

# ---- 1. disambiguate polygons by centroid in Zhoukou bbox ----
d = json.load(open(GJ, encoding="utf-8"))
pinyin = {"Fugou": "扶沟", "Xihua": "西华", "Shangshui": "商水", "Shenqiu": "沈丘",
          "Dancheng": "郸城", "Taikang": "太康", "Luyi": "鹿邑",
          "Xiangcheng City": "项城", "Xiangcheng County": "襄城(非周口)-check"}
ZK_BBOX = (113.9, 33.05, 116.2, 34.15)   # generous Zhoukou window
def centroid(f):
    xs, ys = [], []
    def walk(a):
        if isinstance(a[0], (int, float)):
            xs.append(a[0]); ys.append(a[1])
        else:
            for s in a: walk(s)
    walk(f["geometry"]["coordinates"])
    return (sum(xs)/len(xs), sum(ys)/len(ys))

sel = {}
for f in d["features"]:
    nm = f["properties"].get("shapeName", "")
    for py, zh in pinyin.items():
        if nm == py or nm.startswith(py + " ") or nm.startswith(py + " County") or nm.startswith(py + " City"):
            cx, cy = centroid(f)
            if ZK_BBOX[0] <= cx <= ZK_BBOX[2] and ZK_BBOX[1] <= cy <= ZK_BBOX[3]:
                key = zh if py != "Xiangcheng County" else nm
                sel.setdefault(key, []).append({"name_en": nm, "shape_id": f["properties"]["shapeID"],
                                                "cx": round(cx, 4), "cy": round(cy, 4),
                                                "geometry": f["geometry"]})
print("polygons kept (in-Zhoukou-bbox):")
for k, v in sel.items():
    print(f"  {k}: {[x['name_en'] for x in v]} shapes={len(v)} centre={v[0]['cx']},{v[0]['cy']}")

# keep the 8 target counties (exclude 川汇/淮阳; Xiangcheng County(襄城) should be outside bbox or flagged)
targets = {}
for zh in ["扶沟", "西华", "商水", "沈丘", "郸城", "太康", "鹿邑", "项城"]:
    if zh in sel and len(sel[zh]) == 1:
        targets[zh] = sel[zh][0]
    elif zh in sel:
        targets[zh] = sel[zh][0]
        print(f"  [warn] {zh} has {len(sel[zh])} candidate polygons, kept first")
print("targets:", list(targets), flush=True)

# ---- 2. RS positive-area extraction per county-year ----
cand = pd.read_csv(CAND)
cand["sown_ha"] = cand["area_thousand_ha"] * 1000.0
rows = []
for zh, rec in targets.items():
    from shapely.geometry import shape
    geom = shape(rec["geometry"])
    for yr in [2019, 2020, 2021]:
        sub = cand[(cand.county.str.startswith(zh)) & (cand.harvest_year == yr)]
        if len(sub) == 0: continue
        sown = float(sub.sown_ha.iloc[0])
        tif = os.path.join(ROOT, "Data", f"{yr}ChinaWheatYield30m.tif")
        with rasterio.open(tif) as s:
            minx, miny, maxx, maxy = geom.bounds
            win = rasterio.windows.from_bounds(minx - 0.001, miny - 0.001, maxx + 0.001, maxy + 0.001,
                                               transform=s.transform)
            win = win.round_offsets().round_lengths()
            m = geometry_mask([geom.__geo_interface__], out_shape=(int(round(win.height)), int(round(win.width))),
                              transform=s.window_transform(win), invert=True)
            arr = s.read(1, window=win)
            px = arr[m]
            pos = px[px > 0]
            n_pos = int(len(pos)); n_tot = int(len(px))
            # ChinaWheatYield30m pixel value = YIELD (kg/ha); positive pixel = wheat mask.
            # RS-derived harvested area = positive pixel count x 0.09 ha (30 m pixel)
            rs_ha = n_pos * 0.09
        ratio = rs_ha / sown if sown else np.nan
        rows.append({"county": zh, "harvest_year": yr, "sown_ha": sown,
                     "rs_positive_ha": round(rs_ha, 1), "rs_n_pos_px": n_pos, "rs_n_px": n_tot,
                     "area_ratio_rs_over_stats": round(ratio, 4),
                     "reported_kg_ha": float(sub.reported_kg_ha.iloc[0]),
                     "shape_id": rec["shape_id"]})
        print(f"  {zh} {yr}: sown={sown:.0f}ha rs_pos={rs_ha:.0f}ha ratio={ratio:.2f} px={n_pos}/{n_tot}", flush=True)

dd = pd.DataFrame(rows)
dd["pass_primary"] = (dd.area_ratio_rs_over_stats >= 2/3) & (dd.area_ratio_rs_over_stats <= 1.5)
dd["pass_strict"] = (dd.area_ratio_rs_over_stats >= 0.8) & (dd.area_ratio_rs_over_stats <= 1.25)
dd["centre_lon"] = [targets[r.county]["cx"] for r in dd.itertuples()]
dd["centre_lat"] = [targets[r.county]["cy"] for r in dd.itertuples()]
dd.to_csv(os.path.join(OUT, "w53_zhoukou_coverage.csv"), index=False, encoding="utf-8-sig")
pri = dd[dd.pass_primary]
print(f"\nfreeze: primary-pass {len(pri)}/{len(dd)} county-years")
print(pri[["county","harvest_year","sown_ha","rs_positive_ha","area_ratio_rs_over_stats"]].to_string(index=False))

# ---- 3. Zhoukou coverage visualization ----
plt.rcParams.update({"font.family": "sans-serif", "font.sans-serif": ["Arial", "DejaVu Sans"],
                     "font.size": 8, "axes.titlesize": 9})
fig, axes = plt.subplots(1, 2, figsize=(10, 4.6))
ax = axes[0]
for zh, rec in targets.items():
    g = rec["geometry"]
    def walk(a, pts):
        if isinstance(a[0], (int, float)): pts.append(a)
        else:
            for s in a: walk(s, pts)
    pts = []; walk(g["coordinates"], pts)
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    sub = dd[dd.county == zh]
    col = "#009E73" if bool(sub.pass_primary.iloc[0]) else "#D55E00"
    ax.plot(xs, ys, color=col, lw=0.9, alpha=0.8)
    ax.text(rec["cx"], rec["cy"], zh[:2], ha="center", fontsize=7)
ax.set_xlabel("Longitude (E)"); ax.set_ylabel("Latitude (N)")
ax.set_title("(a) Zhoukou counties: green = primary screen pass", loc="left", fontsize=9)
ax = axes[1]
dd_sorted = dd.sort_values(["county", "harvest_year"])
labels = [f"{r.county[:2]}\n{r.harvest_year}" for r in dd_sorted.itertuples()]
cols = ["#009E73" if p else "#D55E00" for p in dd_sorted.pass_primary]
ax.bar(range(len(dd_sorted)), dd_sorted.area_ratio_rs_over_stats, color=cols, width=0.7)
ax.axhline(2/3, color="#999999", ls=":", lw=0.8)
ax.axhline(1.5, color="#999999", ls=":", lw=0.8)
ax.axhline(1.0, color="#444444", lw=0.8)
ax.set_xticks(range(len(dd_sorted))); ax.set_xticklabels(labels, rotation=60, ha="right", fontsize=6)
ax.set_ylabel("RS positive area / stats sown area")
ax.set_title("(b) Coverage ratio screen (pass 2/3-1.5)", loc="left", fontsize=9)
fig.tight_layout()
fig.savefig(os.path.join(FIGDIR, "fig18_zhoukou_freeze.png"), dpi=300)
print("fig18 saved")
json.dump({k: {kk: vv for kk, vv in v.items() if kk != "geometry"} for k, v in targets.items()},
          open(os.path.join(OUT, "w53_zhoukou_shapes.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("W53-R2 done")
