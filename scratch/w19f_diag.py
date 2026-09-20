# -*- coding: utf-8 -*-
"""W19f: diagnose why detection=0 — signal-feature correlation structure +
ridge comparator power on planted regional-shape signals."""
import os, warnings
import numpy as np, pandas as pd
warnings.filterwarnings("ignore")
from sklearn.model_selection import KFold
from sklearn.metrics import r2_score
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from xgboost import XGBRegressor

ROOT = r"D:\2026-SP"; INT = os.path.join(ROOT, "Outputs", "intermediate")
NEW = dict(n_estimators=428, max_depth=5, learning_rate=0.168, subsample=0.594,
           colsample_bytree=0.821, min_child_weight=6, reg_alpha=3.57, reg_lambda=2.69,
           random_state=42, n_jobs=1, verbosity=0)
BRIDGE = {f"bio{i}": f"wc2.1_2.5m_bio_{i}" for i in range(1, 20)}
BRIDGE.update({"clay_pct": "clay", "sand_pct": "sand", "soc_dgkg": "soc",
               "bdod_kgdm3": "bdod", "cec_cmolkg": "cec", "ph": "phh2o"})
NAT = pd.read_csv(os.path.join(INT, "w19_national_grid_features.csv"))
E = pd.read_csv(os.path.join(INT, "data_with_yield_ensemble_full.csv"))
shared = sorted({c for c in BRIDGE if c in E.columns and BRIDGE[c] in NAT.columns})
F = NAT.rename(columns={v: k for k, v in BRIDGE.items()})
Xn, yn = F[shared].values.astype(float), F["y"].values.astype(float)
donor = XGBRegressor(**NEW).fit(Xn, yn)

yA = E["wheat_yield_tha"].values; mA = ~np.isnan(yA)
drop = {"lon","lat","wheat_yield_tha","wheat_yield_pred_tha","yield_uncertainty_tha",
        "yield_source","yield_blended_tha","yield_source_blend"}
FE24 = [c for c in E.columns if c not in drop and E[c].dtype in ("float64","int64")]
XA = E.loc[mA, FE24].values.astype(float)
XAs = E.loc[mA, shared].values.astype(float)
sig_raw = donor.predict(XAs)
print("sig_raw across 43 grids: std =", round(float(sig_raw.std()), 4),
      "| range =", round(float(sig_raw.min()), 3), "-", round(float(sig_raw.max()), 3))
sig = (sig_raw - sig_raw.mean()) / (sig_raw.std() + 1e-12)
top = np.argsort(-np.abs([np.corrcoef(sig, XA[:, i])[0, 1] if XA[:, i].std() > 0 else 0 for i in range(XA.shape[1])]))[:6]
print("top |corr(sig, feature)|:")
for i in top:
    print("   ", FE24[i], round(float(np.corrcoef(sig, XA[:, i])[0, 1]), 3))

# power: ridge vs xgboost on planted y (r2pop=0.3), n_sim=100
y_sd = float(np.nanstd(yA[mA])); r2pop = 0.3; sigma = y_sd*np.sqrt(1-r2pop)
det = {"ridge": 0, "xgb": 0}; N = 100
for s_i in range(N):
    eps = np.random.default_rng(2000+s_i).normal(0, sigma, XA.shape[0])
    y = sig*y_sd*np.sqrt(r2pop) + eps
    for tr, te in KFold(5, shuffle=True, random_state=s_i).split(XA):
        r = make_pipeline(StandardScaler(), Ridge(alpha=1.0)).fit(XA[tr], y[tr])
        if r2_score(y[te], r.predict(XA[te])) > 0.10: det["ridge"] += 1; break
        m3 = XGBRegressor(**NEW).fit(XA[tr], y[tr])
        if r2_score(y[te], m3.predict(XA[te])) > 0.10: det["xgb"] += 1; break
print(f"per-sim ANY-fold OOF R2>0.10 detection (true R2pop=0.3, n=100 sims): ridge={det['ridge']/N:.2f} xgb={det['xgb']/N:.2f}")

# pooled-R2 criterion (same as main pipeline) for ridge
det_p = 0
for s_i in range(N):
    eps = np.random.default_rng(3000+s_i).normal(0, sigma, XA.shape[0])
    y = sig*y_sd*np.sqrt(r2pop) + eps
    yp = np.zeros(len(y))
    for tr, te in KFold(5, shuffle=True, random_state=s_i).split(XA):
        r = make_pipeline(StandardScaler(), Ridge(alpha=1.0)).fit(XA[tr], y[tr]); yp[te] = r.predict(XA[te])
    if r2_score(y, yp) > 0.10: det_p += 1
print(f"ridge pooled-R2>0.10 detection: {det_p/N:.2f}")
