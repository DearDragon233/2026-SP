# -*- coding: utf-8 -*-
"""W26-R3: co-construction bias robustness - E->RS on 2016/2020 targets.
Re-samples the SAME national lattice cells from the 2016/2020 tifs, joins
environment features, runs the identical random-CV pipeline.
Output: w26_r3_bias_by_year.csv"""
import os, warnings
import numpy as np, pandas as pd
warnings.filterwarnings("ignore")
import rasterio
from rasterio.windows import Window
from rasterio.transform import rowcol
from sklearn.model_selection import KFold
from sklearn.metrics import r2_score
from xgboost import XGBRegressor

ROOT = r"D:\2026-SP"; INT = os.path.join(ROOT, "Outputs", "intermediate")
R21 = pd.read_csv(os.path.join(INT, "w25_r2_national_rs_target.csv"))
cells = R21[R21.rs_yield_tha.notna()].reset_index(drop=True)
ENV = None
M = pd.read_csv(os.path.join(INT, "w22_r2_national_EMM.csv"))
key = lambda d: d.lon.round(4).astype(str) + "_" + d.lat.round(4).astype(str)
M["_k"] = key(M)
ENV = [c for c in M.columns if c.startswith("wc2.1_2.5m_") or c in ("clay","sand","soc","bdod","cec","phh2o")]
NEW = dict(n_estimators=428, max_depth=5, learning_rate=0.168, subsample=0.594,
           colsample_bytree=0.821, min_child_weight=6, reg_alpha=3.57, reg_lambda=2.69,
           random_state=42, n_jobs=4, verbosity=0)
rows = []
for yr in [2016, 2020, 2021]:
    vals = np.full(len(cells), np.nan)
    with rasterio.open(os.path.join(ROOT, "Data", f"{yr}ChinaWheatYield30m.tif")) as src:
        tr = src.transform
        for i, (lo, la) in enumerate(zip(cells.lon.values, cells.lat.values)):
            r0, c0 = rowcol(tr, lo - 0.0009, la + 0.0009)
            r1, c1 = rowcol(tr, lo + 0.0009, la - 0.0009)
            r0, r1 = max(0, min(r0, src.height-1)), max(0, min(r1, src.height-1))
            c0, c1 = max(0, min(c0, src.width-1)), max(0, min(c1, src.width-1))
            if r1 <= r0 or c1 <= c0: continue
            try:
                sub = src.read(1, window=Window(c0, r0, c1-c0+1, r1-r0+1))
                m = sub > 0
                if m.sum() >= 2: vals[i] = float(sub[m].mean()) / 1000.0
            except Exception: pass
            if (i+1) % 1500 == 0: print(f"  {yr} {i+1}/{len(cells)}", flush=True)
    ok = ~np.isnan(vals)
    sub2 = cells[ok].copy(); sub2["y"] = vals[ok]; sub2["_k"] = key(sub2)
    T = sub2.merge(M[["_k"] + ENV], on="_k")
    X = T[ENV].values.astype(float); y = T["y"].values.astype(float)
    ps = []
    for s in [7, 21, 42]:
        yp = np.zeros(len(y))
        for tr_, te_ in KFold(5, shuffle=True, random_state=s).split(X):
            mm = XGBRegressor(**NEW).fit(X[tr_], y[tr_]); yp[te_] = mm.predict(X[te_])
        ps.append(r2_score(y, yp))
    rows.append({"year": yr, "n": len(y), "env_random_cv_r2": round(float(np.mean(ps)), 4),
                 "std": round(float(np.std(ps)), 4)})
    print(f"R3 E->RS {yr}: {np.mean(ps):.4f} +- {np.std(ps):.4f} (n={len(y)})", flush=True)
pd.DataFrame(rows).to_csv(os.path.join(INT, "w26_r3_bias_by_year.csv"), index=False, encoding="utf-8-sig")
print("R3 done")
