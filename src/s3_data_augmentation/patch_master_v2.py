# -*- coding: utf-8 -*-
"""v2 修复（容错版）：逐点采样 dataset.sample，损坏文件跳过并登记。"""
import rasterio, numpy as np, pandas as pd, os
from pyproj import Transformer

ROOT = r"D:\2026-SP"
INT = os.path.join(ROOT, "Outputs", "intermediate")
SG = os.path.join(ROOT, "Data", "SoilGrids_wgs84")
WC = os.path.join(ROOT, "Data", "WorldClim")

m = pd.read_csv(os.path.join(INT, "augmented_yield_master.csv"), low_memory=False)
new_mask = m["source_batch"] == "Xiao2024_rds_History"
lons = m.loc[new_mask, "lon"].values
lats = m.loc[new_mask, "lat"].values
print("patching rows:", int(new_mask.sum()))

failed = []

def sample_pts(path, lons, lats, label=""):
    """逐点采样：dataset.sample 生成器，天然容错单点；整文件损坏则抛异常由外层捕获"""
    with rasterio.open(path) as src:
        if str(src.crs) != "EPSG:4326":
            tr = Transformer.from_crs("EPSG:4326", src.crs, always_xy=True)
            xs, ys = tr.transform(lons, lats)
        else:
            xs, ys = lons, lats
        out = np.full(len(xs), np.nan)
        coords = [(x, y) for x, y in zip(xs, ys)]
        try:
            for i, val in enumerate(src.sample(coords, masked=True)):
                v = float(val[0]) if val[0] is not None else np.nan
                if v is not None and not np.ma.is_masked(val[0]) and abs(v) < 1e30:
                    out[i] = v
        except Exception as e:
            # 部分瓦片损坏：逐点读取，坏点跳过
            print(f"  {label}: bulk sample failed ({type(e).__name__}), per-point fallback")
            arr_cache = {}
            H = W = None
            for i, (x, y) in enumerate(zip(xs, ys)):
                try:
                    r_, c_ = src.index(x, y)
                    v = float(src.read(1, window=rasterio.windows.Window(c_, r_, 1, 1))[0, 0])
                    if abs(v) < 1e30:
                        out[i] = v
                except Exception:
                    continue
        nv = out[~np.isnan(out)]
        print(f"  {label}: valid {len(nv)}/{len(out)}" + (f" | mean {np.nanmean(nv):.3f}" if len(nv) else ""))
        return out

sg_names = {"bdod": "bdod_0-5cm_mean_5000.tif", "cec": "cec_0-5cm_mean_5000.tif",
            "clay": "clay_0-5cm_mean_5000.tif", "nitrogen": "nitrogen_0-5cm_mean_5000.tif",
            "ph": "phh2o_0-5cm_mean_5000.tif", "sand": "sand_0-5cm_mean_5000.tif",
            "silt": "silt_0-5cm_mean_5000.tif", "soc": "soc_0-5cm_mean_5000.tif"}
for key, fn in sg_names.items():
    p = os.path.join(SG, fn)
    if not os.path.exists(p):
        failed.append((key, "missing")); continue
    try:
        m.loc[new_mask, f"sg_{key}"] = np.round(sample_pts(p, lons, lats, label=f"sg_{key}"), 4)
    except Exception as e:
        print(f"  sg_{key}: FILE FAILED -> {type(e).__name__}: {str(e)[:80]}")
        failed.append((key, "corrupt"))

# elev 兜底
elev_files = [f for f in os.listdir(WC) if "elev" in f.lower()]
if elev_files:
    try:
        ev = sample_pts(os.path.join(WC, elev_files[0]), lons, lats, label="wc_elev")
        gap = m.loc[new_mask, "elev_m"].isna().values
        m.loc[new_mask, "elev_m"] = np.where(gap, np.round(ev, 2), m.loc[new_mask, "elev_m"])
        print("elev gaps filled:", int(gap.sum()))
    except Exception as e:
        failed.append(("wc_elev", type(e).__name__))

m.to_csv(os.path.join(INT, "augmented_yield_master_v2.csv"), index=False, encoding="utf-8-sig")
print("\nFINAL:", m.shape)
print("failed files:", failed if failed else "none")

env_cols = [c for c in m.columns if c.startswith(("sg_", "bio_", "tavg_", "prec_", "elev"))]
cov = m.loc[new_mask, env_cols].notna().mean().sort_values()
print("\n=== 增量行环境列覆盖率（最低 8 列，%）===")
print((cov.head(8) * 100).round(1).to_string())
print("mean coverage:", f"{cov.mean()*100:.1f}%")
