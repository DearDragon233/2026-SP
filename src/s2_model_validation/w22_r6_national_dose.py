# -*- coding: utf-8 -*-
"""W22-R6: national-scale block-size dose-response (mirror of W14 Pinggu).
Prediction P4: checker gap INCREASES with block size then saturates at ~195x-range
domain (classic honest behaviour), opposite to Pinggu's structural placebo."""
import os, warnings
import numpy as np, pandas as pd
warnings.filterwarnings("ignore")
from sklearn.model_selection import KFold
from sklearn.metrics import r2_score
from xgboost import XGBRegressor

ROOT = r"D:\2026-SP"; INT = os.path.join(ROOT, "Outputs", "intermediate")
SEEDS = [7, 21, 42]
NEW = dict(n_estimators=428, max_depth=5, learning_rate=0.168, subsample=0.594,
           colsample_bytree=0.821, min_child_weight=6, reg_alpha=3.57, reg_lambda=2.69,
           random_state=42, n_jobs=4, verbosity=0)
M = pd.read_csv(os.path.join(INT, "w22_r2_national_EMM.csv"))
ENV = [c for c in M.columns if c.startswith("wc2.1_2.5m_") or c in ("clay","sand","soc","bdod","cec","phh2o")]
X = M[ENV].values.astype(float); y = M["History"].values.astype(float)
coords = M[["lon","lat"]].values
KM_LON = 111.32*np.cos(np.radians(35.0)); RANGE = 4.62

def checker_splits(edge_deg):
    key = (np.floor(coords[:,0]/edge_deg).astype(int) + 2*np.floor(coords[:,1]/edge_deg).astype(int)) % 2
    return [(np.where(key!=k)[0], np.where(key==k)[0]) for k in (0,1)]

def run(splits, seeds=SEEDS):
    ps = []
    for s in seeds:
        yp = np.zeros(len(y))
        for tr, te in splits:
            m = XGBRegressor(**{**NEW, "random_state": s}).fit(X[tr], y[tr]); yp[te] = m.predict(X[te])
        ps.append(r2_score(y, yp))
    return float(np.mean(ps)), float(np.std(ps)), [round(p,4) for p in ps]

rows = []
sp_rand = list(KFold(5, shuffle=True, random_state=42).split(np.zeros((len(y),1))))
mu, sd, bs = run(sp_rand)
rows.append({"scheme":"random","ratio_x_range":0.0,"edge_km":0.0,"pooled_mean":round(mu,4),
             "pooled_std":round(sd,4),"by_seed":bs})
print(f"R6 random: {mu:.4f} +- {sd:.4f}", flush=True)
for ratio in [0.5, 1.0, 2.0, 4.0]:
    edge_km = ratio * RANGE
    edge_deg = edge_km / KM_LON
    mu, sd, bs = run(checker_splits(edge_deg))
    rows.append({"scheme":f"checker_{ratio}x","ratio_x_range":ratio,"edge_km":round(edge_km,2),
                 "pooled_mean":round(mu,4),"pooled_std":round(sd,4),"by_seed":bs})
    print(f"R6 checker {ratio}x range ({edge_km:.1f} km): {mu:.4f} +- {sd:.4f}", flush=True)
d = pd.DataFrame(rows)
base = d.loc[d.scheme=="random","pooled_mean"].iloc[0]
d["gap_vs_random"] = (base - d.pooled_mean).round(4)
d.to_csv(os.path.join(INT, "w22_r6_national_dose.csv"), index=False, encoding="utf-8-sig")
print(d[["scheme","edge_km","pooled_mean","gap_vs_random"]].to_string(index=False))
print("R6 done")
