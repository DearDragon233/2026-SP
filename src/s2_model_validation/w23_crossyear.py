# -*- coding: utf-8 -*-
"""W23: cross-year validation of the RS-derived target (ChinaWheatYield30m 2016-2021).
For each available year tif: extract Pinggu 234-grid yields (same window/aggregation
as crop_zenodo_to_grid.py, n_px>=4), then (i) year-level summary, (ii) grid-level
inter-annual pattern stability (pairwise Pearson r between years), (iii) per-year
environment-only CV (E 71 vars, random 5-fold x3 seeds) mirroring the D-target check.
Outputs: Outputs/intermediate/w23_crossyear_targets.csv,
         w23_crossyear_pattern_corr.csv, w23_crossyear_env_cv.csv"""
import os, glob, warnings
import numpy as np, pandas as pd
warnings.filterwarnings("ignore")
import rasterio
from rasterio.windows import from_bounds
from rasterio.transform import rowcol
from sklearn.model_selection import KFold
from sklearn.metrics import r2_score
from xgboost import XGBRegressor

ROOT = r"D:\2026-SP"; INT = os.path.join(ROOT, "Outputs", "intermediate")
LON0, LON1, LAT0, LAT1 = 116.90, 117.26, 40.00, 40.24
SEEDS = [7, 21, 42]
NEW = dict(n_estimators=428, max_depth=5, learning_rate=0.168, subsample=0.594,
           colsample_bytree=0.821, min_child_weight=6, reg_alpha=3.57, reg_lambda=2.69,
           random_state=42, n_jobs=1, verbosity=0)
ens = pd.read_csv(os.path.join(INT, "data_with_yield_ensemble_full.csv"))
drop = {"lon","lat","wheat_yield_tha","wheat_yield_pred_tha","yield_uncertainty_tha",
        "yield_source","yield_blended_tha","yield_source_blend"}
FE = [c for c in ens.columns if c not in drop and ens[c].dtype in ("float64","int64")]
X_all = ens[FE].values.astype(float)

years = sorted(int(os.path.basename(p)[:4]) for p in glob.glob(os.path.join(ROOT, "Data", "*ChinaWheatYield30m.tif")))
print("available years:", years, flush=True)
Y = {}
for yr in years:
    P = os.path.join(ROOT, "Data", f"{yr}ChinaWheatYield30m.tif")
    with rasterio.open(P) as src:
        win = from_bounds(LON0, LAT0, LON1, LAT1, src.transform)
        arr = src.read(1, window=win)
        transform = src.window_transform(win)
        valid = arr > 0
    half = 0.005
    vals = np.full(len(ens), np.nan); npx = np.zeros(len(ens), int)
    for gi, (la, lo) in enumerate(zip(ens.lat.values, ens.lon.values)):
        r0, c0 = rowcol(transform, lo-half, la+half)
        r1, c1 = rowcol(transform, lo+half, la-half)
        r0, r1 = max(0, min(r0, arr.shape[0]-1)), max(0, min(r1, arr.shape[0]-1))
        c0, c1 = max(0, min(c0, arr.shape[1]-1)), max(0, min(c1, arr.shape[1]-1))
        if r1 <= r0 or c1 <= c0: continue
        sub = arr[r0:r1+1, c0:c1+1]; msk = valid[r0:r1+1, c0:c1+1]
        npx[gi] = int(msk.sum())
        if msk.sum() >= 4:
            vals[gi] = float(sub[msk].mean()) / 1000.0
    Y[yr] = vals
    print(f"{yr}: valid grids (n_px>=4) = {np.sum(~np.isnan(vals))}, mean {np.nanmean(vals):.2f} +- {np.nanstd(vals):.2f} t/ha", flush=True)

rows = []
for yr, v in Y.items():
    m = ~np.isnan(v)
    rows.append({"year": yr, "n_grids": int(m.sum()),
                 "yield_mean": round(float(np.nanmean(v)), 3), "yield_sd": round(float(np.nanstd(v)), 3)})
pd.DataFrame(rows).to_csv(os.path.join(INT, "w23_crossyear_targets.csv"), index=False, encoding="utf-8-sig")

# inter-annual pattern stability (grid-level Pearson r, common valid grids)
pc = []
yrs = [y for y in years if np.sum(~np.isnan(Y[y])) >= 15]
for i, y1 in enumerate(yrs):
    for y2 in yrs[i+1:]:
        m = ~np.isnan(Y[y1]) & ~np.isnan(Y[y2])
        if m.sum() >= 15:
            r = float(np.corrcoef(Y[y1][m], Y[y2][m])[0, 1])
            pc.append({"year1": y1, "year2": y2, "n_common": int(m.sum()), "pearson_r": round(r, 3)})
pd.DataFrame(pc).to_csv(os.path.join(INT, "w23_crossyear_pattern_corr.csv"), index=False, encoding="utf-8-sig")
print("pattern corr:", [(p['year1'], p['year2'], p['pearson_r']) for p in pc], flush=True)

# per-year environment-only CV
rows2 = []
for yr in yrs:
    v = Y[yr]; m = ~np.isnan(v)
    if m.sum() < 15: continue
    Xs, ys = X_all[m], v[m]
    ps = []
    for s in SEEDS:
        yp = np.zeros(len(ys))
        for tr, te in KFold(5, shuffle=True, random_state=s).split(Xs):
            mm = XGBRegressor(**NEW).fit(Xs[tr], ys[tr]); yp[te] = mm.predict(Xs[te])
        ps.append(r2_score(ys, yp))
    rows2.append({"year": yr, "n": int(m.sum()), "env_random_cv_r2_mean": round(float(np.mean(ps)), 4),
                  "env_random_cv_r2_std": round(float(np.std(ps)), 4)})
    print(f"env-CV {yr}: {np.mean(ps):.4f} +- {np.std(ps):.4f} (n={m.sum()})", flush=True)
pd.DataFrame(rows2).to_csv(os.path.join(INT, "w23_crossyear_env_cv.csv"), index=False, encoding="utf-8-sig")
print("W23 done")
