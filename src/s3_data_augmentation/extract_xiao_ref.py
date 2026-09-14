# -*- coding: utf-8 -*-
"""Xiao2024 参考图层（WheatYield_ref / N_ref / Irrigation_ref, 1km, CC BY 4.0）
裁剪平谷 → 提取 234 网格值 → xiao2024_ref_grid.csv"""
import rasterio, numpy as np, pandas as pd, os
from rasterio.mask import mask
from rasterio.warp import transform_bounds
from pyproj import Transformer

ROOT = r"D:\2026-SP"
base = pd.read_csv(os.path.join(ROOT, "Outputs", "intermediate", "data_with_yield_ensemble_full.csv"))
lons = base["lon"].values; lats = base["lat"].values
print("grids:", len(base), "| lon range", lons.min(), lons.max(), "| lat range", lats.min(), lats.max())

for name in ["WheatYield_ref", "N_ref", "Irrigation_ref"]:
    p = os.path.join(ROOT, "Data", "Management", "Xiao2024", f"{name}.tif")
    with rasterio.open(p) as src:
        print(f"\n=== {name} === crs={src.crs} shape={src.shape} nodata={src.nodata}")
        print("  bounds:", src.bounds)
        print("  res:", src.res)
        # 网格中心点 → 栅格坐标
        if str(src.crs) != "EPSG:4326":
            tr = Transformer.from_crs("EPSG:4326", src.crs, always_xy=True)
            xs, ys = tr.transform(lons, lats)
        else:
            xs, ys = lons, lats
        vals = []
        for x, y in zip(xs, ys):
            try:
                row, col = src.index(x, y)
                v = src.read(1)[row, col]
                v = float(v) if v != src.nodata else np.nan
            except Exception:
                v = np.nan
            vals.append(v)
        vals = np.array(vals)
        valid = vals[~np.isnan(vals)]
        print(f"  valid: {len(valid)}/{len(vals)} | range {np.nanmin(valid):.3f} ~ {np.nanmax(valid):.3f} | mean {np.nanmean(valid):.3f}")
        base[f"xiao_{name.replace('_ref','').lower()}"] = np.round(vals, 4)

out = os.path.join(ROOT, "Outputs", "intermediate", "xiao2024_ref_grid.csv")
base.to_csv(out, index=False, encoding="utf-8-sig")
print("\nsaved:", out, base.shape)
