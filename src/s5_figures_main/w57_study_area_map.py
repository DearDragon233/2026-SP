# -*- coding: utf-8 -*-
"""W57: study-area overview map for paper 2.
Background: wheat harvested area (CHN_2021.tif band 'whea', 10 km; figshare
10.6084/m9.figshare.26028769) over the North China Plain.
Overlays: counties of the four study areas (geoBoundaries CHN ADM3); only the
counties that enter the analysis are drawn.
Layout: (a) regional map; (b-e) one panel per study area."""
import os, json, textwrap
import numpy as np, pandas as pd
import rasterio
from rasterio.windows import from_bounds
from shapely.geometry import shape
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.lines import Line2D
import matplotlib.patheffects as pe

ROOT = r"D:\2026-SP"
REP = os.path.join(ROOT, "Outputs", "reports")
OUT = os.path.join(ROOT, "ManageFiles", "Submission_package_Paper2", "figures")
os.makedirs(OUT, exist_ok=True)
NL = chr(10)
MM = 1 / 25.4
plt.rcParams.update({"font.family": "sans-serif", "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
                     "font.size": 7.5, "axes.labelsize": 8, "axes.titlesize": 8.5,
                     "xtick.labelsize": 6.5, "ytick.labelsize": 6.5, "legend.fontsize": 6.4,
                     "axes.linewidth": 0.6, "pdf.fonttype": 42, "figure.dpi": 300, "savefig.dpi": 600})
COL = {"hebei": "#0072B2", "shandong": "#E69F00", "henan": "#009E73"}

# ---------- counties that enter the analysis ----------
def used(path, flag=None, prov=None):
    d = pd.read_csv(path)
    if prov is not None and "province" in d.columns:
        d = d[d.province.str.contains(prov)]
    if flag is not None and flag in d.columns:
        d = d[d[flag].astype(bool)]
    return sorted(d.shape_id.unique())

units = [
    ("Shijiazhuang (Hebei)", used(os.path.join(REP, "w44_frozen_panel.csv"), "primary", "河北"),
     COL["hebei"], "Development panel: 12 counties, 56 county-years"),
    ("Tai'an (Shandong)", used(os.path.join(REP, "w44_frozen_panel.csv"), "primary", "山东"),
     COL["shandong"], "Development panel: 5 counties, 23 county-years"),
    ("Pingdingshan (Henan)", used(os.path.join(REP, "w48_pds_frozen.csv"), "primary"),
     COL["henan"], "External test: 5 counties, 6 county-years"),
    ("Zhoukou (Henan)", used(os.path.join(REP, "w53_zhoukou_frozen_external.csv")),
     COL["henan"], "External test: 7 counties, 19 county-years"),
]
gj = json.load(open(os.path.join(ROOT, "Data", "external", "ncp_yield_pairing", "download",
                                 "geoBoundaries-CHN-ADM3.geojson"), encoding="utf-8"))
geoms = {f["properties"]["shapeID"]: shape(f["geometry"]) for f in gj["features"]}
for name, ids, col, cap in units:
    bb = np.array([geoms[i].bounds for i in ids if i in geoms])
    print(f"{name}: {len(bb)} counties | bbox "
          f"{tuple(round(float(x), 2) for x in (bb[:, 0].min(), bb[:, 1].min(), bb[:, 2].max(), bb[:, 3].max()))}")

def rings(g):
    polys = list(g.geoms) if g.geom_type == "MultiPolygon" else [g]
    for poly in polys:
        xy = np.array(poly.exterior.coords)
        yield xy[:, 0], xy[:, 1]

# ---------- wheat background ----------
LON0, LON1, LAT0, LAT1 = 110.0, 123.0, 30.5, 41.0
with rasterio.open(os.path.join(ROOT, "Data", "CropArea_figshare", "CHN_2021.tif")) as s:
    bi = list(s.descriptions).index("whea") + 1
    win = from_bounds(LON0, LAT0, LON1, LAT1, s.transform).round_offsets().round_lengths()
    arr = s.read(bi, window=win).astype(float)
    # no nodata tag in the file; NaN = no data, 0 = no wheat, >0 = wheat area (ha per cell)
    arr = np.where(np.isfinite(arr), arr, np.nan)
    left, bottom, right, top = rasterio.windows.bounds(win, s.transform)
ext = (left, right, bottom, top)            # imshow order is (left, right, bottom, top)
vmax = float(np.nanpercentile(arr, 99))
pos = arr[arr > 0]
print(f"window {arr.size} cells | wheat>0 in {100 * pos.size / arr.size:.1f}% | "
      f"median {np.median(pos):.0f} ha | max {np.nanmax(arr):.0f} ha")

# ---------- figure ----------
fig = plt.figure(figsize=(183 * MM, 168 * MM))
gs = fig.add_gridspec(2, 1, height_ratios=[1.4, 1], hspace=0.40,
                      left=0.065, right=0.925, top=0.955, bottom=0.055)
ax = fig.add_subplot(gs[0, :])
cmap = plt.get_cmap("YlOrBr").copy(); cmap.set_bad("white")
im = ax.imshow(np.ma.masked_invalid(arr), cmap=cmap, vmin=0, vmax=vmax, extent=ext,
               origin="upper", interpolation="nearest", zorder=0)
COL_FILL = {"Shijiazhuang (Hebei)": "#b3cde0", "Tai'an (Shandong)": "#fddbc7",
            "Pingdingshan (Henan)": "#d9f0d3", "Zhoukou (Henan)": "#e5d8bd"}
COL_EDGE = {"Shijiazhuang (Hebei)": COL["hebei"], "Tai'an (Shandong)": COL["shandong"],
            "Pingdingshan (Henan)": COL["henan"], "Zhoukou (Henan)": COL["henan"]}
hl = [pe.withStroke(linewidth=2.6, foreground="white")]
letters = ["b", "c", "d", "e"]
for i, (name, ids, col, cap) in enumerate(units):
    bb = np.array([geoms[k].bounds for k in ids if k in geoms])
    x0, y0, x1, y1 = bb[:, 0].min(), bb[:, 1].min(), bb[:, 2].max(), bb[:, 3].max()
    p = 0.12
    ax.add_patch(Rectangle((x0 - p, y0 - p), (x1 - x0) + 2 * p, (y1 - y0) + 2 * p, fill=False,
                           edgecolor=col, lw=1.4, zorder=5, path_effects=hl))
    ax.text(x0 - p, y1 + p + 0.16, f"({letters[i]})", color=col, fontsize=8.5, fontweight="bold",
            zorder=6, path_effects=hl)
    for k in ids:
        if k not in geoms:
            continue
        poly = geoms[k]
        polys = list(poly.geoms) if poly.geom_type == "MultiPolygon" else [poly]
        for poly in polys:
            xy = np.array(poly.exterior.coords)
            ax.fill(xy[:, 0], xy[:, 1], color=COL_FILL[name], alpha=0.45, zorder=3)
            ax.plot(xy[:, 0], xy[:, 1], color=col, lw=0.8, zorder=4)
ax.set_xlim(LON0, LON1); ax.set_ylim(LAT0, LAT1)
ax.set_aspect(1 / np.cos(np.radians(35.7)))
ax.set_xlabel("Longitude (E)"); ax.set_ylabel("Latitude (N)")
ax.xaxis.set_major_formatter(plt.FormatStrFormatter("%.0f"))
ax.set_title("(a) Winter wheat harvested area, 2021, and the four study areas", loc="left", fontweight="bold")
ax.text(121.4, 39.7, "Bohai Sea", fontsize=6.5, color="#557799", style="italic", ha="center")
ax.legend(handles=[Line2D([], [], color=COL["hebei"], lw=1.4, label="Development: Shijiazhuang (Hebei)"),
                   Line2D([], [], color=COL["shandong"], lw=1.4, label="Development: Tai'an (Shandong)"),
                   Line2D([], [], color=COL["henan"], lw=1.4, label="External tests (Henan)")],
          loc="upper left", bbox_to_anchor=(0.0, -0.12), ncol=2, frameon=False, handlelength=1.6,
          columnspacing=1.6)
cax = fig.add_axes([0.935, 0.415, 0.011, 0.52])
cb = fig.colorbar(im, cax=cax); cb.set_label("Wheat area per 10 km cell (ha)", fontsize=7)

# inset row: place axes by hand with widths proportional to each area's longitude span
bbox_all = fig.get_size_inches()
row_top, row_h = 0.005, 0.255                  # figure fraction (bottom, height) of the inset row
gap = 0.045
x_left, x_right = 0.035, 0.985
spans = []
for name, ids, col, cap in units:
    bb = np.array([geoms[k].bounds for k in ids if k in geoms])
    cy = float(bb[:, 1].mean()); spans.append((bb[:, 2].max() - bb[:, 0].min()) / np.cos(np.radians(cy)))
scale = (x_right - x_left - gap * (len(units) - 1)) / sum(spans)
x = x_left
letters = ["b", "c", "d", "e"]
for i, (name, ids, col, cap) in enumerate(units):
    w = spans[i] * scale
    pad = 0.012
    a = fig.add_axes([x + pad, row_top, w - 2 * pad, row_h])
    for k in ids:
        if k not in geoms:
            continue
        for xs, ys in rings(geoms[k]):
            a.fill(xs, ys, color=col, alpha=0.20, lw=0)
            a.plot(xs, ys, color=col, lw=0.9)
    bb = np.array([geoms[k].bounds for k in ids if k in geoms])
    x0, y0, x1, y1 = bb[:, 0].min(), bb[:, 1].min(), bb[:, 2].max(), bb[:, 3].max()
    a.set_xlim(x0 - 0.06, x1 + 0.06); a.set_ylim(y0 - 0.06, y1 + 0.06)
    a.set_aspect(1 / np.cos(np.radians((y0 + y1) / 2)))
    a.set_title(f"({letters[i]}) {name}", loc="left", fontsize=7.2, fontweight="bold")
    a.xaxis.set_major_locator(plt.MaxNLocator(4)); a.yaxis.set_major_locator(plt.MaxNLocator(3))
    a.xaxis.set_major_formatter(plt.FormatStrFormatter("%.1f"))
    a.yaxis.set_major_formatter(plt.FormatStrFormatter("%.1f"))
    a.tick_params(labelsize=5.8)
    a.text(0.5, -0.20, NL.join(textwrap.wrap(cap, 30)), transform=a.transAxes,
           ha="center", va="top", fontsize=6.0, color="#444444")
    x += w + gap

for ext_ in ("png", "pdf", "tiff"):
    kw = {"pil_kwargs": {"compression": "tiff_lzw"}} if ext_ == "tiff" else {}
    fig.savefig(os.path.join(OUT, f"Figure_S1_study_area_map.{ext_}"), bbox_inches="tight", **kw)
print("study-area map saved")
