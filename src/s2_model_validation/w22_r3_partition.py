# -*- coding: utf-8 -*-
"""W22-R3: national-scale variance partitioning E / M / E+M.
Prediction P1 (pre-registered): M-only random-CV R2 > 0.3; E+M > E (0.690).
Schemes: random 5-fold x3 seeds + checkerboard 1x-range."""
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
MGMT = ["WN", "WR", "xWIrri", "MN", "MR", "xMIrri"]
ENV = [c for c in M.columns if c.startswith("wc2.1_2.5m_") or c in ("clay","sand","soc","bdod","cec","phh2o")]
y = M["History"].values.astype(float)
coords = M[["lon","lat"]].values

def cv_run(X, splits):
    ps = []
    for sp, s in zip(splits, SEEDS):
        yp = np.zeros(len(y))
        for tr, te in sp:
            m = XGBRegressor(**NEW).fit(X[tr], y[tr]); yp[te] = m.predict(X[te])
        ps.append(r2_score(y, yp))
    return float(np.mean(ps)), float(np.std(ps)), [round(p,4) for p in ps]

rows = []
for tag, cols in [("E_only", ENV), ("M_only", MGMT), ("E+M", ENV+MGMT)]:
    X = M[cols].values.astype(float)
    sp_rand = [list(KFold(5, shuffle=True, random_state=s).split(np.zeros((len(y),1)))) for s in SEEDS]
    edge = 0.10
    key = (np.floor(coords[:,0]/edge).astype(int) + 2*np.floor(coords[:,1]/edge).astype(int)) % 2
    sp_chk = [[(np.where(key!=k)[0], np.where(key==k)[0]) for k in (0,1)]]*3
    for scheme, splits in [("random", sp_rand), ("checker_1x", sp_chk)]:
        mu, sd, bs = cv_run(X, splits)
        rows.append({"set":tag,"n_feat":len(cols),"scheme":scheme,"pooled_mean":round(mu,4),
                     "pooled_std":round(sd,4),"by_seed":bs})
        print(f"R3 {tag:7s} {scheme:11s}: {mu:.4f} +- {sd:.4f}", flush=True)
pd.DataFrame(rows).to_csv(os.path.join(INT, "w22_r3_partition.csv"), index=False, encoding="utf-8-sig")
print("R3 done")
