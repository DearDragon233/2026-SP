# -*- coding: utf-8 -*-
"""W56: Zhoukou deletion sensitivity - leave-one-county-out MAE.
Models: training mean, ridge, random forest. Labels: statistics and remote."""
import os, warnings
import numpy as np, pandas as pd
warnings.filterwarnings("ignore")
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.ensemble import RandomForestRegressor

ROOT = r"D:\2026-SP"; REP = os.path.join(ROOT, "Outputs", "reports")
FEATS = ["autumn_gdd0", "winter_cold_days", "winter_precip_mm", "spring_gdd0",
         "spring_precip_mm", "april_hot_days"]
panel = pd.read_csv(os.path.join(REP, "w44_frozen_panel.csv")).dropna(subset=FEATS).reset_index(drop=True)
zk = pd.read_csv(os.path.join(REP, "w53_zhoukou_frozen_external.csv")).dropna(subset=FEATS).reset_index(drop=True)
Xp = panel[FEATS].values.astype(float)
Xt = zk[FEATS].values.astype(float)
yt = zk.reported_kg_ha.values.astype(float)
counties = zk.county.values

SEED = 42
def fit_ridge(X, y):
    return make_pipeline(StandardScaler(), Ridge(alpha=1.0)).fit(X, y)
def fit_rf(X, y):
    return RandomForestRegressor(n_estimators=200, min_samples_leaf=2, random_state=SEED, n_jobs=4).fit(X, y)

rows = []
for lab, ycol in [("statistics", "stats_kg_ha"), ("remote", "remote_winter_wheat_kg_ha")]:
    yp = panel[ycol].values.astype(float)
    mean_v = float(np.mean(yp))
    ridge = make_pipeline(StandardScaler(), Ridge(alpha=1.0)).fit(Xp, yp)
    rf = RandomForestRegressor(**dict(n_estimators=200, min_samples_leaf=2, random_state=SEED, n_jobs=4)).fit(Xp, yp)
    for g in sorted(zk.county.unique()):
        m = counties == g
        if m.sum() < 3: continue
        yte = yt[m]
        p_mean = np.full(m.sum(), mean_v)
        p_ridge = ridge.predict(Xt[m])
        p_rf = rf.predict(Xt[m])
        rows.append({"omitted_county": g, "kept_rows": int(m.sum()),
                     "mae_mean_stat": round(float(np.mean(np.abs(p_mean - yte))), 1),
                     "mae_ridge_stat": round(float(np.mean(np.abs(p_ridge - yte))), 1),
                     "mae_rf_stat": round(float(np.mean(np.abs(p_rf - yte))), 1)})

d = pd.DataFrame(rows)
d.to_csv(os.path.join(REP, "w56_zhoukou_deletion_sensitivity.csv"), index=False, encoding="utf-8-sig")
print(d.to_string(index=False))
print(f"\nobserved yield: mean {yt.mean():.0f}, SD {yt.std():.0f}")
print("ridge predictions range:", [round(float(np.nanmin(pred_ridge)),1) if False else 0, 0])
print("W56 done")
