# -*- coding: utf-8 -*-
"""W19c: deterministic sweep of Pinggu-sized windows over the NCP feature table."""
import os, warnings
import numpy as np, pandas as pd
warnings.filterwarnings("ignore")
from sklearn.model_selection import KFold
from sklearn.metrics import r2_score
from xgboost import XGBRegressor

ROOT = r"D:\2026-SP"; INT = os.path.join(ROOT, "Outputs", "intermediate")
NEW = dict(n_estimators=428, max_depth=5, learning_rate=0.168, subsample=0.594,
           colsample_bytree=0.821, min_child_weight=6, reg_alpha=3.57, reg_lambda=2.69,
           random_state=42, n_jobs=4, verbosity=0)
F = pd.read_csv(os.path.join(INT, "w19_national_grid_features.csv"))
FEATS = [c for c in F.columns if c not in ("lon", "lat", "y")]
W_LAT, W_LON = 0.5, 0.7
rows = []
clons = np.arange(112.6, 122.6, 0.35); clats = np.arange(30.4, 40.2, 0.3)
cands = []
for clon in clons:
    for clat in clats:
        m = (F["lon"].between(clon-W_LON/2, clon+W_LON/2) & F["lat"].between(clat-W_LAT/2, clat+W_LAT/2))
        n = int(m.sum())
        if n >= 80: cands.append((clon, clat, n))
print(f"candidate windows: {len(cands)}", flush=True)
rng = np.random.default_rng(5)
if len(cands) > 60:
    idx = rng.choice(len(cands), 60, replace=False); cands = [cands[i] for i in idx]
for i, (clon, clat, n) in enumerate(cands):
    sub = F[(F["lon"].between(clon-W_LON/2, clon+W_LON/2)) & (F["lat"].between(clat-W_LAT/2, clat+W_LAT/2))]
    Xs = sub[FEATS].values.astype(float); ys = sub["y"].values.astype(float)
    yp = np.zeros(len(ys))
    for tr, te in KFold(5, shuffle=True, random_state=42).split(Xs):
        m2 = XGBRegressor(**NEW).fit(Xs[tr], ys[tr]); yp[te] = m2.predict(Xs[te])
    rows.append({"window": i, "clon": clon, "clat": clat, "n": len(sub),
                 "bio1_sd": round(float(sub["wc2.1_2.5m_bio_1"].std()), 3),
                 "y_sd": round(float(ys.std()), 3), "r2": round(float(r2_score(ys, yp)), 4)})
    if (i+1) % 10 == 0: print(f"  {i+1}/{len(cands)}", flush=True)
wd = pd.DataFrame(rows)
wd.to_csv(os.path.join(INT, "w19_window_distribution.csv"), index=False)
print(f"windows: {len(wd)} | R2 median {wd.r2.median():.3f} IQR [{wd.r2.quantile(.25):.3f},{wd.r2.quantile(.75):.3f}] min {wd.r2.min():.3f} max {wd.r2.max():.3f}", flush=True)
print(f"corr(bio1_sd, r2) = {wd.bio1_sd.corr(wd.r2):.3f}", flush=True)
