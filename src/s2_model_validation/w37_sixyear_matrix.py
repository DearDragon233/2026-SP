# -*- coding: utf-8 -*-
"""W37: definitive six-year cross-year matrix (2016-2021), ledger-faithful
window (HALF=0.0208 = full grid cell, n_px>=5, matching crop_zenodo_v2.py and
the D-target ledger). Outputs: per-year summary, 15-pair pattern matrix,
per-year env-CV."""
import os, glob, re, warnings
import numpy as np, pandas as pd
warnings.filterwarnings("ignore")
import rasterio
from rasterio.windows import from_bounds
from rasterio.transform import rowcol
from scipy.stats import pearsonr, spearmanr
from sklearn.model_selection import KFold
from sklearn.metrics import r2_score
from xgboost import XGBRegressor

ROOT = r"D:\2026-SP"; INT = os.path.join(ROOT, "Outputs", "intermediate")
LON0, LON1, LAT0, LAT1 = 116.90, 117.26, 40.00, 40.24
HALF = 0.0208
SEEDS = [7, 21, 42]
NEW = dict(n_estimators=428, max_depth=5, learning_rate=0.168, subsample=0.594,
           colsample_bytree=0.821, min_child_weight=6, reg_alpha=3.57, reg_lambda=2.69,
           random_state=42, n_jobs=4, verbosity=0)

ens = pd.read_csv(os.path.join(INT, "data_with_yield_ensemble_full.csv"))
drop = {"lon","lat","wheat_yield_tha","wheat_yield_pred_tha","yield_uncertainty_tha",
        "yield_source","yield_blended_tha","yield_source_blend"}
FE = [c for c in ens.columns if c not in drop and ens[c].dtype in ("float64","int64")]
X_all = ens[FE].values.astype(float)
years = sorted(int(re.search(r"(20\d\d)", os.path.basename(p)).group(1)) for p in glob.glob(os.path.join(ROOT, "Data", "2*ChinaWheatYield30m.tif")))
print("years:", years, flush=True)

Y = {}
for yr in years:
    P = os.path.join(ROOT, "Data", f"{yr}ChinaWheatYield30m.tif")
    with rasterio.open(P) as src:
        win = from_bounds(LON0, LAT0, LON1, LAT1, src.transform)
        arr = src.read(1, window=win)
        transform = src.window_transform(win)
        valid = arr > 0
    v = np.full(len(ens), np.nan)
    for gi, (la, lo) in enumerate(zip(ens.lat.values, ens.lon.values)):
        r0, c0 = rowcol(transform, lo - HALF, la + HALF)
        r1, c1 = rowcol(transform, lo + HALF, la - HALF)
        r0, r1 = max(0, min(r0, arr.shape[0]-1)), max(0, min(r1, arr.shape[0]-1))
        c0, c1 = max(0, min(c0, arr.shape[1]-1)), max(0, min(c1, arr.shape[1]-1))
        if r1 <= r0 or c1 <= c0: continue
        msk = valid[r0:r1+1, c0:c1+1]
        if msk.sum() >= 5:
            v[gi] = float(arr[r0:r1+1, c0:c1+1][msk].mean()) / 1000.0
    Y[yr] = v
    m = ~np.isnan(v)
    print(f"{yr}: n={m.sum()}, {np.nanmean(v):.2f} +- {np.nanstd(v):.2f} t/ha", flush=True)

pd.DataFrame({str(y): Y[y] for y in years}).assign(lon=ens.lon.values, lat=ens.lat.values).to_csv(
    os.path.join(INT, "w37_sixyear_grid.csv"), index=False, encoding="utf-8-sig")

# pairwise pattern matrix (all pairs with >=8 common grids)
rows = []
for i, y1 in enumerate(years):
    for y2 in years[i+1:]:
        m = (~np.isnan(Y[y1])) & (~np.isnan(Y[y2]))
        n = int(m.sum())
        if n >= 8:
            r = pearsonr(Y[y1][m], Y[y2][m]); rs = spearmanr(Y[y1][m], Y[y2][m])
            rows.append({"y1": y1, "y2": y2, "n": n, "pearson_r": round(float(r[0]), 3),
                         "p": round(float(r[1]), 3), "spearman": round(float(rs.statistic), 3)})
            print(f"pair {y1}-{y2}: r={r[0]:.3f} (p={r[1]:.3f}, n={n})", flush=True)
pd.DataFrame(rows).to_csv(os.path.join(INT, "w37_pattern_matrix.csv"), index=False, encoding="utf-8-sig")
if rows:
    rs_all = [r["pearson_r"] for r in rows]
    print(f"pattern r: mean {np.mean(rs_all):.3f}, range [{min(rs_all):.2f},{max(rs_all):.2f}]", flush=True)

# per-year env-CV (E-only, 71 vars)
rows2 = []
for yr in years:
    v = Y[yr]; m = ~np.isnan(v)
    if m.sum() < 8: continue
    Xs, ys = X_all[m], v[m]
    ps = []
    for s in SEEDS:
        yp = np.zeros(len(ys))
        for tr, te in KFold(5, shuffle=True, random_state=s).split(Xs):
            mm = XGBRegressor(**NEW).fit(Xs[tr], ys[tr]); yp[te] = mm.predict(Xs[te])
        ps.append(r2_score(ys, yp))
    rows2.append({"year": yr, "n": int(m.sum()), "env_cv_r2_mean": round(float(np.mean(ps)), 4),
                  "env_cv_r2_std": round(float(np.std(ps)), 4),
                  "by_seed": [round(p, 4) for p in ps]})
    print(f"env-CV {yr}: {np.mean(ps):.4f} +- {np.std(ps):.4f} (n={m.sum()})", flush=True)
pd.DataFrame(rows2).to_csv(os.path.join(INT, "w37_envcv_by_year.csv"), index=False, encoding="utf-8-sig")
print("W37 six-year matrix done")
