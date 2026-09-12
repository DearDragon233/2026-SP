# -*- coding: utf-8 -*-
"""
W5 STEP1-fix2: 网格间距修正版聚合
关键发现：234 网格的间距是 0.0417°（≈3.5km），不是 1km！
→ 每网格对应 30m 像元约 155×155 = 24000 个，聚合窗口 half=0.0208°
→ 之前 half=0.005 只取了网格中心一小块，导致覆盖只有 10/234
"""
import rasterio, numpy as np, pandas as pd, os
from rasterio.windows import from_bounds
from rasterio.transform import rowcol

P = r"D:\2026-SP\Data\2021ChinaWheatYield30m.tif"
ENS = r"D:\2026-SP\Outputs\intermediate\data_with_yield_ensemble_full.csv"
OUT = r"D:\2026-SP\Outputs\intermediate\zenodo_yield_2021_grid.csv"

LON0, LON1, LAT0, LAT1 = 116.90, 117.26, 40.00, 40.24
HALF = 0.0208  # 半格（网格间距 0.0417° 的一半）

with rasterio.open(P) as src:
    win = from_bounds(LON0, LAT0, LON1, LAT1, src.transform)
    arr = src.read(1, window=win)
    transform = src.window_transform(win)
    valid = arr > 0
    print("valid px:", valid.sum(), f"({valid.mean()*100:.1f}%)")

    ens = pd.read_csv(ENS)
    lats, lons = ens['lat'].values, ens['lon'].values
    results = []
    for gi, (la, lo) in enumerate(zip(lats, lons)):
        r0, c0 = rowcol(transform, lo - HALF, la + HALF)
        r1, c1 = rowcol(transform, lo + HALF, la - HALF)
        r0, r1 = max(0, r0), min(arr.shape[0]-1, r1)
        c0, c1 = max(0, c0), min(arr.shape[1]-1, c1)
        if r1 <= r0 or c1 <= c0:
            results.append({'grid_id': gi, 'zenodo_yield_tha': np.nan, 'n_px': 0}); continue
        sub = arr[r0:r1+1, c0:c1+1]
        msk = valid[r0:r1+1, c0:c1+1]
        n = int(msk.sum())
        if n >= 5:
            v_kg = float(sub[msk].mean())
            results.append({'grid_id': gi, 'zenodo_yield_tha': round(v_kg/1000, 3), 'n_px': n})
        else:
            results.append({'grid_id': gi, 'zenodo_yield_tha': np.nan, 'n_px': n})
        if (gi+1) % 78 == 0: print(f"  {gi+1}/234", flush=True)

res = pd.DataFrame(results)
ens_out = ens.merge(res, left_index=True, right_on='grid_id', how='left')
ok = res['zenodo_yield_tha'].notna().sum()
print(f"\n覆盖: {ok}/234 ({ok/234*100:.0f}%)")
n = res['n_px']
print(f"n_px: max={n.max()} | >0: {(n>0).sum()} | >=5: {(n>=5).sum()} | >=100: {(n>=100).sum()}")
v = res['zenodo_yield_tha'].dropna()
if len(v):
    print(f"Zenodo 2021 (t/ha): mean={v.mean():.2f}±{v.std():.2f} range=[{v.min():.2f},{v.max():.2f}]")
obs = ens_out.loc[ens_out['wheat_yield_tha'].notna(), ['wheat_yield_tha', 'zenodo_yield_tha']].dropna()
if len(obs) > 5:
    r = obs['wheat_yield_tha'].corr(obs['zenodo_yield_tha'])
    print(f"与 Xiao2024 交叉验证: r={r:.3f}, n={len(obs)}")
    print(f"  Xiao2024: {obs['wheat_yield_tha'].mean():.2f}±{obs['wheat_yield_tha'].std():.2f}")
    print(f"  Zenodo:   {obs['zenodo_yield_tha'].mean():.2f}±{obs['zenodo_yield_tha'].std():.2f}")
# 清理旧列
drop_cols = [c for c in ens_out.columns if 'zenody' in c or c == 'zenodo_yield_kg_ha']
ens_out = ens_out.drop(columns=drop_cols, errors='ignore')
ens_out.to_csv(OUT, index=False, encoding='utf-8-sig')
print("saved:", OUT)
