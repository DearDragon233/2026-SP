# -*- coding: utf-8 -*-
"""
W5 SOURCE UPGRADE STEP1-fix: 裁剪平谷窗口 + 聚合到 234 个 1km 网格
单位修正版：ChinaWheatYield30m 单位为 kg/ha（正值 4887-6835 = 4.9-6.8 t/ha）
处理：valid = arr > 0（正像元即有效产量），均值后 /1000 转 t/ha
"""
import rasterio, numpy as np, pandas as pd, os
from rasterio.windows import from_bounds
from rasterio.transform import rowcol

P = r"D:\2026-SP\Data\2021ChinaWheatYield30m.tif"
OUT = r"D:\2026-SP\Outputs\intermediate\zenodo_yield_2021_grid.csv"
ENS = r"D:\2026-SP\Outputs\intermediate\data_with_yield_ensemble_full.csv"

LON0, LON1 = 116.90, 117.26
LAT0, LAT1 = 40.00, 40.24

with rasterio.open(P) as src:
    win = from_bounds(LON0, LAT0, LON1, LAT1, src.transform)
    arr = src.read(1, window=win)
    transform = src.window_transform(win)
    # 修正：正像元即有效产量（kg/ha），nodata 为负极大值
    valid = arr > 0
    print("valid px:", valid.sum(), "/", arr.size, f"({valid.mean()*100:.1f}%)")
    if valid.sum() > 0:
        vv = arr[valid]
        print(f"valid kg/ha range: {vv.min():.0f}-{vv.max():.0f}, mean={vv.mean():.0f}")
        print(f"in t/ha: {vv.min()/1000:.2f}-{vv.max()/1000:.2f}, mean={vv.mean()/1000:.2f}")

    ens = pd.read_csv(ENS)
    lats, lons = ens['lat'].values, ens['lon'].values
    half = 0.005
    results = []
    for gi, (la, lo) in enumerate(zip(lats, lons)):
        r0, c0 = rowcol(transform, lo - half, la + half)
        r1, c1 = rowcol(transform, lo + half, la - half)
        r0, r1 = max(0, min(r0, arr.shape[0]-1)), max(0, min(r1, arr.shape[0]-1))
        c0, c1 = max(0, min(c0, arr.shape[1]-1)), max(0, min(c1, arr.shape[1]-1))
        if r1 <= r0 or c1 <= c0:
            results.append({'grid_id': gi, 'zenodo_yield_kg_ha': np.nan, 'zenody_yield_tha': np.nan, 'n_px': 0}); continue
        sub = arr[r0:r1+1, c0:c1+1]
        msk = valid[r0:r1+1, c0:c1+1]
        n = msk.sum()
        if n >= 5:
            v_kg = float(sub[msk].mean())
            results.append({'grid_id': gi, 'zenodo_yield_kg_ha': round(v_kg,1),
                            'zenodo_yield_tha': round(v_kg/1000, 3), 'n_px': int(n)})
        else:
            results.append({'grid_id': gi, 'zenodo_yield_kg_ha': np.nan, 'zenodo_yield_tha': np.nan, 'n_px': int(n)})
        if (gi+1) % 60 == 0: print(f"  {gi+1}/234", flush=True)

res = pd.DataFrame(results)
ens_out = ens.merge(res, left_index=True, right_on='grid_id', how='left')
ok = res['zenodo_yield_tha'].notna().sum()
print(f"\n覆盖: {ok}/234 网格有 Zenodo 产量 ({ok/234*100:.0f}%)")
if ok > 0:
    v = res['zenodo_yield_tha'].dropna()
    print(f"Zenodo 2021 产量(t/ha): mean={v.mean():.2f}, std={v.std():.2f}, range=[{v.min():.2f},{v.max():.2f}]")
    obs = ens_out.loc[ens_out['wheat_yield_tha'].notna(), ['wheat_yield_tha', 'zenodo_yield_tha']].dropna()
    if len(obs) > 5:
        r = obs['wheat_yield_tha'].corr(obs['zenodo_yield_tha'])
        print(f"与 Xiao2024 实测交叉验证: r={r:.3f}, n={len(obs)}")
        print(f"  Xiao2024 mean={obs['wheat_yield_tha'].mean():.2f}±{obs['wheat_yield_tha'].std():.2f}")
        print(f"  Zenodo   mean={obs['zenodo_yield_tha'].mean():.2f}±{obs['zenodo_yield_tha'].std():.2f}")
ens_out.to_csv(OUT, index=False, encoding='utf-8-sig')
print("saved:", OUT)
