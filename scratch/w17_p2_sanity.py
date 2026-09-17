# -*- coding: utf-8 -*-
"""W17 sanity check: A-target bit-exact zero change under +wheat_thermal4.
Replicates w16_p1p2_experiments.py P2 construction, then compares OOF preds
and thermal-feature gains on the 43 A grids."""
import pandas as pd, numpy as np, json, glob, os, warnings
warnings.filterwarnings("ignore")
from sklearn.model_selection import KFold
from sklearn.metrics import r2_score
from scipy.spatial import cKDTree
from xgboost import XGBRegressor

ROOT = r"D:\2026-SP"; INT = os.path.join(ROOT, "Outputs", "intermediate")
df = pd.read_csv(os.path.join(INT, "data_with_yield_ensemble_full.csv"))
coords = df[["lon", "lat"]].values
yA = df["wheat_yield_tha"].values; mA = ~np.isnan(yA)
SEEDS = [7, 21, 42]
NEW = dict(n_estimators=428, max_depth=5, learning_rate=0.168, subsample=0.594,
           colsample_bytree=0.821, min_child_weight=6, reg_alpha=3.57, reg_lambda=2.69,
           random_state=42, n_jobs=2, verbosity=0)
drop = {"lon","lat","wheat_yield_tha","wheat_yield_pred_tha","yield_uncertainty_tha",
        "yield_source","yield_blended_tha","yield_source_blend"}
FEATS = [c for c in df.columns if c not in drop and df[c].dtype in ("float64","int64")]

files = sorted(glob.glob(os.path.join(INT, "openmeteo_2021_daily", "batch_*.json")))
pts = []
for fp in files:
    j = json.load(open(fp, encoding="utf-8"))
    for r in (j if isinstance(j, list) else [j]):
        d = r["daily"]; t = pd.to_datetime(d["time"]); mth = t.month
        tavg = np.array(d["temperature_2m_mean"], float); tmin = np.array(d["temperature_2m_min"], float)
        tmax = np.array(d["temperature_2m_max"], float)
        ins = mth <= 6
        pts.append({"lat": r["latitude"], "lon": r["longitude"],
                    "w_gdd0_season": float(np.sum(np.clip(tavg[ins]-0, 0, None))),
                    "w_vernal_days": int(np.sum((tavg>=0)&(tavg<=10)&((mth<=2)|(mth==12)))),
                    "w_deepcold_days": int(np.sum(tmin<=-10)),
                    "w_hdf30_grain": int(np.sum((tmax>=30)&(mth<=6)))})
ph = pd.DataFrame(pts)
dd, nn = cKDTree(ph[["lon","lat"]].values).query(coords, k=1)
df2 = df.copy()
for c in ["w_gdd0_season","w_vernal_days","w_deepcold_days","w_hdf30_grain"]:
    df2[c] = ph[c].values[nn]
TH = ["w_gdd0_season","w_vernal_days","w_deepcold_days","w_hdf30_grain"]
FEATS5 = FEATS + TH
print("thermal std on A grids:", {c: round(float(df2.loc[mA,c].std()),3) for c in TH})

ya = yA[mA]; res = {}
for tag, fset in [("base", FEATS), ("wheat", FEATS5)]:
    X = np.nan_to_num(df2.loc[mA, fset].values.astype(float), nan=0.0)
    preds = np.zeros((len(SEEDS), int(mA.sum()))); ps = []
    for i, s in enumerate(SEEDS):
        yp = np.zeros(len(ya))
        for tr, te in KFold(5, shuffle=True, random_state=s).split(X):
            m = XGBRegressor(**NEW).fit(X[tr], ya[tr]); yp[te] = m.predict(X[te])
        ps.append(r2_score(ya, yp)); preds[i] = yp
    res[tag] = (float(np.mean(ps)), preds)
    print(f"{tag}: pooled {np.mean(ps):.6f}")
print("bit-exact OOF preds:", bool(np.array_equal(res["base"][1], res["wheat"][1])))
Xw = np.nan_to_num(df2.loc[mA, FEATS5].values.astype(float), nan=0.0)
m = XGBRegressor(**NEW).fit(Xw, ya)
g = m.get_booster().get_score(importance_type="gain")
print("thermal gains on full A:", {c: float(g.get(c, 0.0)) for c in TH})
# persist thermal features for reproducibility
df2[["lon","lat"]+TH].to_csv(os.path.join(INT, "w16_p2_thermal_features_persisted.csv"), index=False)
print("persisted -> w16_p2_thermal_features_persisted.csv")
