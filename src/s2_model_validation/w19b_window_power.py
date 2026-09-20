# -*- coding: utf-8 -*-
"""W19b: Two supporting experiments for the detectability framework.

Exp A — Pinggu-sized windows across the NCP: same feature table as
w19_external_validation.py, slide 0.7deg x 0.5deg windows (Pinggu's footprint,
~234 grids). If window-level R2 collapses toward the Pinggu null while the
full-gradient R2 stays high, the framework is shown to be a *faithful signal
detector* whose readings scale with environmental variance.

Exp B — Statistical power on the 43-grid A-target: plant KNOWN synthetic
signal (R2_pop in {0.05,0.1,0.2,0.3,0.5}) into the real 43-grid feature
matrix, run the identical CV pipeline, and report detection rates. Low power
at realistic effect sizes turns "R2 ~ 0" into "R2 below the detectable
ceiling of n=43 at this signal-to-noise geometry".
Outputs: w19_window_distribution.csv, w19_power_analysis.csv
"""
import os, warnings
import numpy as np
import pandas as pd
warnings.filterwarnings("ignore")
from sklearn.model_selection import KFold
from sklearn.metrics import r2_score
from xgboost import XGBRegressor

ROOT = r"D:\2026-SP"; INT = os.path.join(ROOT, "Outputs", "intermediate")
SEEDS = [7, 21, 42]
NEW = dict(n_estimators=428, max_depth=5, learning_rate=0.168, subsample=0.594,
           colsample_bytree=0.821, min_child_weight=6, reg_alpha=3.57, reg_lambda=2.69,
           random_state=42, n_jobs=4, verbosity=0)
F = pd.read_csv(os.path.join(INT, "w19_national_grid_features.csv"))
FEATS = [c for c in F.columns if c not in ("lon", "lat", "y")]

# ---------- Exp A: Pinggu-sized windows ----------
print("[A] Pinggu-sized windows ...", flush=True)
W_LAT, W_LON = 0.5, 0.7          # Pinggu footprint (lat x lon)
N_WIN = 40
rng = np.random.default_rng(11)
centers = []
for _ in range(2000):
    clon = rng.uniform(112.6, 122.5); clat = rng.uniform(30.2, 40.2)
    m = (F["lon"].between(clon - W_LON/2, clon + W_LON/2) &
         F["lat"].between(clat - W_LAT/2, clat + W_LAT/2))
    if m.sum() >= 150:
        centers.append((clon, clat, int(m.sum())))
    if len(centers) >= N_WIN: break
rows = []
for i, (clon, clat, n) in enumerate(centers):
    sub = F[(F["lon"].between(clon - W_LON/2, clon + W_LON/2)) &
            (F["lat"].between(clat - W_LAT/2, clat + W_LAT/2))]
    Xs = sub[FEATS].values.astype(float); ys = sub["y"].values.astype(float)
    yp = np.zeros(len(ys))
    for tr, te in KFold(5, shuffle=True, random_state=42).split(Xs):
        m2 = XGBRegressor(**NEW).fit(Xs[tr], ys[tr]); yp[te] = m2.predict(Xs[te])
    r2 = r2_score(ys, yp)
    rows.append({"window": i, "n": len(sub),
                 "bio1_sd": round(float(sub["wc2.1_2.5m_bio_1"].std()), 3),
                 "y_sd": round(float(ys.std()), 3), "r2": round(float(r2), 4)})
    if (i + 1) % 10 == 0: print(f"    {i+1}/{len(centers)} windows done", flush=True)
wd = pd.DataFrame(rows)
wd.to_csv(os.path.join(INT, "w19_window_distribution.csv"), index=False)
print(f"    windows: n={len(wd)} | R2 median {wd.r2.median():.3f}, IQR "
      f"[{wd.r2.quantile(.25):.3f},{wd.r2.quantile(.75):.3f}] | min {wd.r2.min():.3f}", flush=True)
print(f"    full-gradient reference: 0.690 (n=7784)", flush=True)

# ---------- Exp B: power analysis on the 43-grid A-target ----------
print("[B] power analysis (n=43) ...", flush=True)
E = pd.read_csv(os.path.join(INT, "data_with_yield_ensemble_full.csv"))
yA = E["wheat_yield_tha"].values; mA = ~np.isnan(yA)
drop = {"lon","lat","wheat_yield_tha","wheat_yield_pred_tha","yield_uncertainty_tha",
        "yield_source","yield_blended_tha","yield_source_blend"}
FE = [c for c in E.columns if c not in drop and E[c].dtype in ("float64","int64")]
XA = E.loc[mA, FE].values.astype(float)
# standardise features, build a synthetic "true" environmental component via a
# fixed linear combination + mild nonlinearity, scale to target share of y-var
Z = (XA - XA.mean(0)) / (XA.std(0) + 1e-9)
rng = np.random.default_rng(2026)
w = rng.normal(size=XA.shape[1]); w /= np.linalg.norm(w)
lin = Z @ w
nl = lin + 0.5 * np.tanh(lin)          # mild nonlinearity
nl = (nl - nl.mean()) / nl.std()
y_sd = float(np.nanstd(yA[mA]))        # observed A-target SD (0.23)
rows = []
for r2pop in [0.05, 0.10, 0.20, 0.30, 0.50]:
    sigma = y_sd * np.sqrt(1 - r2pop)   # noise SD so that Var(f)/Var(y) = r2pop
    det05, det10, r2s = 0, 0, []
    N_SIM = 200
    for s_i in range(N_SIM):
        eps = rng.normal(0, sigma, XA.shape[0])
        y = nl * y_sd * np.sqrt(r2pop) + eps
        yp = np.zeros(len(y))
        for tr, te in KFold(5, shuffle=True, random_state=s_i).split(XA):
            m3 = XGBRegressor(**NEW).fit(XA[tr], y[tr]); yp[te] = m3.predict(XA[te])
        r2 = r2_score(y, yp); r2s.append(r2)
        det05 += r2 > 0.05; det10 += r2 > 0.10
    rows.append({"r2_pop": r2pop, "n_sim": N_SIM,
                 "det_rate_r2gt0.05": round(det05 / N_SIM, 3),
                 "det_rate_r2gt0.10": round(det10 / N_SIM, 3),
                 "median_r2": round(float(np.median(r2s)), 4),
                 "note": "n=43, XGBoost optuna428, 5-fold CV; true signal planted in real Pinggu feature space"})
    print(f"    R2pop={r2pop}: median {np.median(r2s):.3f}, det(>0.05)={det05/N_SIM:.2f}, det(>0.10)={det10/N_SIM:.2f}", flush=True)
pd.DataFrame(rows).to_csv(os.path.join(INT, "w19_power_analysis.csv"), index=False)
print("W19b done")
