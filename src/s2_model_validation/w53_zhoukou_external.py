# -*- coding: utf-8 -*-
"""W53-R3: Zhoukou weather fingerprints (W44 protocol) -> freeze external test
design -> run external test: models trained on the frozen W44 panel (statistics
and remote labels) score against Zhoukou statistical yields. Training-mean
baseline included; deletion sensitivity over year/county/weather-series."""
import os, json, hashlib, warnings
import numpy as np, pandas as pd
warnings.filterwarnings("ignore")
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error

ROOT = r"D:\2026-SP"; INT = os.path.join(ROOT, "Outputs", "intermediate")
REP = os.path.join(ROOT, "Outputs", "reports")

# ---- fingerprints from fetched POWER JSONs ----
PIN_DIR = os.path.join(ROOT, "Data", "external", "ncp_yield_pairing", "download", "power_zhoukou")
cov = pd.read_csv(os.path.join(REP, "w53_zhoukou_coverage.csv"))
PIN = {"扶沟": "Fugou", "西华": "Xihua", "商水": "Shangshui", "沈丘": "Shenqiu",
       "郸城": "Dancheng", "太康": "Taikang", "鹿邑": "Luyi", "项城": "Xiangcheng"}

def gdd0(tavg): return max(0.0, float(tavg))
rows = []
for county, py in PIN.items():
    fp = os.path.join(PIN_DIR, f"{py}.json")
    sha = hashlib.sha256(open(fp, "rb").read()).hexdigest()
    d = json.load(open(fp, encoding="utf-8"))
    rec = d["properties"]["parameter"]
    alg = rec["ALLSKY_SFC_SW_DNI"] if False else None
    t2m = rec["T2M"]; tmin = rec["T2M_MIN"]; tmax = rec["T2M_MAX"]; pr = rec["PRECTOTCORR"]
    dates = sorted(t2m.keys())
    df = pd.DataFrame({"date": dates, "tavg": [t2m[k] for k in dates],
                       "tmin": [tmin[k] for k in dates], "tmax": [tmax[k] for k in dates],
                       "pr": [pr[k] for k in dates]})
    df["date"] = pd.to_datetime(df["date"])
    df = df[(df.tavg > -900) & (df.pr > -900)]          # CMA fill values -999
    df["month"] = df.date.dt.month; df["year"] = df.date.dt.year
    for hy in [2019, 2020, 2021]:
        w = df[((df.date >= f"{hy-1}-10-01") & (df.date <= f"{hy}-04-30"))]
        on = w[w.month.isin([10, 11])]; wi = w[w.month.isin([12, 1, 2])]
        sp = w[w.month.isin([3, 4])]; ap = w[w.month == 4]
        rows.append({"county": county, "harvest_year": hy, "weather_series_id": sha[:16],
                     "autumn_gdd0": float((on.tavg.clip(lower=0)).sum()),
                     "winter_cold_days": float((wi.tmin < -5).sum()),
                     "winter_precip_mm": float(wi.pr.sum()),
                     "spring_gdd0": float((sp.tavg.clip(lower=0)).sum()),
                     "spring_precip_mm": float(sp.pr.sum()),
                     "april_hot_days": float((ap.tmax >= 25).sum())})
fp_df = pd.DataFrame(rows)
fp_df.to_csv(os.path.join(ROOT, "Outputs", "reports", "w53_zhoukou_fingerprints.csv"), index=False, encoding="utf-8-sig")
print("fingerprints:", len(fp_df), "county-years | sample:")
print(fp_df.head(3).to_string())

# ---- freeze: primary-pass county-years with complete fingerprints ----
pri = cov[cov.pass_primary].merge(fp_df, on=["county", "harvest_year"])
pri = pri.dropna(subset=[c for c in pri.columns if c.startswith(("autumn", "winter", "spring", "april"))])
pri.to_csv(os.path.join(REP, "w53_zhoukou_frozen_external.csv"), index=False, encoding="utf-8-sig")
print(f"frozen external test set: {len(pri)} county-years")

# ---- external test: train on W44 frozen panel, test Zhoukou stats ----
panel = pd.read_csv(os.path.join(ROOT, "Outputs", "reports", "w44_frozen_panel.csv"))
FEATS = ["autumn_gdd0", "winter_cold_days", "winter_precip_mm", "spring_gdd0",
         "spring_precip_mm", "april_hot_days"]
panel = panel.dropna(subset=FEATS).reset_index(drop=True)  # 4 Fangshan rows: weather series missing (W41 coverage-anomaly county)
print(f"training panel after Fangshan exclusion: {len(panel)} county-years")
Xp = panel[FEATS].values.astype(float)
TE = pri[FEATS].values.astype(float)
yZ = pri.reported_kg_ha.values.astype(float)
rows = []
for lab, ycol in [("statistics", "stats_kg_ha"), ("remote", "remote_winter_wheat_kg_ha")]:
    yp_lab = panel[ycol].values.astype(float)
    mean_v = float(np.mean(yp_lab))
    ridge = make_pipeline(StandardScaler(), Ridge(alpha=1.0)).fit(Xp, yp_lab)
    rf = RandomForestRegressor(n_estimators=200, min_samples_leaf=2, random_state=42, n_jobs=4).fit(Xp, yp_lab)
    base = np.full(len(yZ), mean_v)
    preds = {"mean": base, "ridge": ridge.predict(TE), "rf": rf.predict(TE)}
    for mname, p in preds.items():
        mae = mean_absolute_error(yZ, p); rm = float(np.sqrt(mean_squared_error(yZ, p)))
        rows.append({"training_label": lab, "model": mname, "test_rows": len(yZ),
                     "mae_kg_ha": round(mae, 1), "rmse_kg_ha": round(rm, 1),
                     "bias_kg_ha": round(float(np.mean(p - yZ)), 1)})
        print(f"[{lab:10s}] {mname:5s}: MAE {mae:.1f} | RMSE {rm:.1f} | bias {np.mean(p-yZ):+.1f}", flush=True)
r = pd.DataFrame(rows)
r.to_csv(os.path.join(REP, "w53_zhoukou_external_scores.csv"), index=False, encoding="utf-8-sig")
print("W53 external test done (deletion sensitivity follow-up)")
