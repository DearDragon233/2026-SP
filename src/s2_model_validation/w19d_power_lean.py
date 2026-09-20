# -*- coding: utf-8 -*-
"""W19d: lean power analysis (n_jobs=1 - thread sync dominates on tiny data)."""
import os, warnings
import numpy as np, pandas as pd
warnings.filterwarnings("ignore")
from sklearn.model_selection import KFold
from sklearn.metrics import r2_score
from xgboost import XGBRegressor

ROOT = r"D:\2026-SP"; INT = os.path.join(ROOT, "Outputs", "intermediate")
NEW = dict(n_estimators=428, max_depth=5, learning_rate=0.168, subsample=0.594,
           colsample_bytree=0.821, min_child_weight=6, reg_alpha=3.57, reg_lambda=2.69,
           random_state=42, n_jobs=1, verbosity=0)
E = pd.read_csv(os.path.join(INT, "data_with_yield_ensemble_full.csv"))
yA = E["wheat_yield_tha"].values; mA = ~np.isnan(yA)
drop = {"lon","lat","wheat_yield_tha","wheat_yield_pred_tha","yield_uncertainty_tha",
        "yield_source","yield_blended_tha","yield_source_blend"}
FE = [c for c in E.columns if c not in drop and E[c].dtype in ("float64","int64")]
XA = E.loc[mA, FE].values.astype(float)
Z = (XA - XA.mean(0)) / (XA.std(0) + 1e-9)
rng = np.random.default_rng(2026)
w = rng.normal(size=XA.shape[1]); w /= np.linalg.norm(w)
lin = Z @ w; nl = lin + 0.5*np.tanh(lin); nl = (nl - nl.mean())/nl.std()
y_sd = float(np.nanstd(yA[mA]))
N_SIM = 200
rows = []
for r2pop in [0.05, 0.10, 0.20, 0.30, 0.50]:
    sigma = y_sd*np.sqrt(1-r2pop)
    det05 = det10 = 0; r2s = []
    for s_i in range(N_SIM):
        eps = rng.normal(0, sigma, XA.shape[0])
        y = nl*y_sd*np.sqrt(r2pop) + eps
        yp = np.zeros(len(y))
        for tr, te in KFold(5, shuffle=True, random_state=s_i).split(XA):
            m3 = XGBRegressor(**NEW).fit(XA[tr], y[tr]); yp[te] = m3.predict(XA[te])
        r2 = r2_score(y, yp); r2s.append(r2)
        det05 += r2 > 0.05; det10 += r2 > 0.10
    rows.append({"r2_pop": r2pop, "n_sim": N_SIM,
                 "det_rate_r2gt0.05": round(det05/N_SIM, 3),
                 "det_rate_r2gt0.10": round(det10/N_SIM, 3),
                 "median_r2": round(float(np.median(r2s)), 4)})
    print(f"R2pop={r2pop}: median {np.median(r2s):.3f} det(>0.05)={det05/N_SIM:.2f} det(>0.10)={det10/N_SIM:.2f}", flush=True)
pd.DataFrame(rows).to_csv(os.path.join(INT, "w19_power_analysis.csv"), index=False)
print("done")
