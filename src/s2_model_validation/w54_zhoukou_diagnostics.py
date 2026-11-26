# -*- coding: utf-8 -*-
"""W54: Zhoukou deletion sensitivity + per-county bias + train-range diagnostics.
Companion to w53 external test. Mirrors W50 design (Pingdingshan).
Outputs: w54_zhoukou_paired_differences.csv, w54_zhoukou_oof.csv,
         w54_zhoukou_diagnostics.json"""
import os, json, warnings
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
yt = zk["reported_kg_ha"].values.astype(float)

# ---- predictions per label x model ----
preds = {}
for L, ycol in [("statistics", "stats_kg_ha"), ("remote", "remote_winter_wheat_kg_ha")]:
    yp = panel[ycol].values.astype(float)
    preds[(L, "mean")] = np.full(len(yt), yp.mean())
    preds[(L, "ridge")] = make_pipeline(StandardScaler(), Ridge(alpha=1.0)).fit(Xp, yp).predict(Xt)
    preds[(L, "random_forest")] = RandomForestRegressor(
        n_estimators=200, min_samples_leaf=2, random_state=42, n_jobs=4).fit(Xp, yp).predict(Xt)

err = {k: np.abs(v - yt) for k, v in preds.items()}
oof = zk[["county", "harvest_year", "weather_series_id", "shape_id", "reported_kg_ha"]].copy()
for (L, m), v in preds.items():
    oof[f"pred_{L}_{m}"] = np.round(v, 1)
oof.to_csv(os.path.join(REP, "w54_zhoukou_oof.csv"), index=False, encoding="utf-8-sig")

# ---- paired differences with deletion ranges ----
rows = []
def paired(a, b, mask=None):
    m = np.ones(len(yt), bool) if mask is None else mask
    return float(np.mean(err[a][m]) - np.mean(err[b][m]))
for model in ["ridge", "random_forest"]:
    a = (f"statistics", model); b = ("statistics", "mean")
    rows.append({"model": model, "comparison": "statistics_minus_same_label_mean",
                 "omission_unit": "all", "omitted": "", "test_rows": len(yt),
                 "mae_difference_kg_ha": round(paired(a, b), 2)})
    a = (f"remote", model); b = ("remote", "mean")
    rows.append({"model": model, "comparison": "remote_minus_same_label_mean",
                 "omission_unit": "all", "omitted": "", "test_rows": len(yt),
                 "mae_difference_kg_ha": round(paired(a, b), 2)})
    a = ("remote", model); b = ("statistics", model)
    rows.append({"model": model, "comparison": "remote_minus_statistics",
                 "omission_unit": "all", "omitted": "", "test_rows": len(yt),
                 "mae_difference_kg_ha": round(paired(a, b), 2)})
# deletion ranges (test-side only, predictions fixed)
del_rows = []
for model in ["ridge", "random_forest"]:
    for comp, a, b in [("statistics_minus_same_label_mean", ("statistics", model), ("statistics", "mean")),
                       ("remote_minus_same_label_mean", ("remote", model), ("remote", "mean")),
                       ("remote_minus_statistics", ("remote", model), ("statistics", model))]:
        vals = []
        for unit in ["harvest_year", "county", "weather_series_id"]:
            for g in zk[unit].unique():
                m = (zk[unit] != g).values
                if m.sum() >= 4:
                    vals.append((unit, g, paired(a, b, m)))
        d = pd.DataFrame(vals, columns=["unit", "omitted", "diff"])
        del_rows.append({"model": model, "comparison": comp,
                         "min_diff": round(float(d["diff"].min()), 2), "max_diff": round(float(d["diff"].max()), 2),
                         "n_deletions": len(d),
                         "min_at": d.loc[d["diff"].idxmin(), "omitted"], "max_at": d.loc[d["diff"].idxmax(), "omitted"]})
pd.DataFrame(rows).to_csv(os.path.join(REP, "w54_zhoukou_paired_differences.csv"), index=False, encoding="utf-8-sig")
dd = pd.DataFrame(del_rows)
dd.to_csv(os.path.join(REP, "w54_zhoukou_deletion_ranges.csv"), index=False, encoding="utf-8-sig")

# ---- per-county bias sign + train-range diagnostics ----
bias = {k: v - yt for k, v in preds.items()}
county_bias = pd.DataFrame({"county": zk.county, "year": zk.harvest_year, "obs": yt})
for L in ["statistics", "remote"]:
    for m in ["ridge", "random_forest"]:
        county_bias[f"bias_{L}_{m}"] = np.round(bias[(L, m)], 1)
county_bias.to_csv(os.path.join(REP, "w54_zhoukou_county_bias.csv"), index=False, encoding="utf-8-sig")
rng_lo, rng_hi = Xp.min(0), Xp.max(0)
inside = ((Xt >= rng_lo) & (Xt <= rng_hi)).sum(1)
ylo, yhi = panel.stats_kg_ha.min(), panel.stats_kg_ha.max()
diag = {
 "n_test": int(len(yt)), "years": {int(y): int((zk.harvest_year == y).sum()) for y in sorted(zk.harvest_year.unique())},
 "counties": int(zk.county.nunique()), "weather_series": int(zk.weather_series_id.nunique()),
 "train_stats_yield_range": [round(float(ylo), 1), round(float(yhi), 1)],
 "train_stats_yield_mean": round(float(panel.stats_kg_ha.mean()), 1),
 "test_yield_mean": round(float(yt.mean()), 1),
 "test_rows_all6_features_in_train_range": int((inside == 6).sum()),
 "test_rows_5plus_in_range": int((inside >= 5).sum()),
 "mean_bias_by_county": {c: round(float(np.mean(bias[("statistics","ridge")][zk.county.values == c])), 1)
                          for c in sorted(zk.county.unique())},
 "bias_sign_consistency_stat_ridge": {"negative": int((bias[("statistics","ridge")] < 0).sum()),
                                       "positive": int((bias[("statistics","ridge")] > 0).sum())},
}
json.dump(diag, open(os.path.join(REP, "w54_zhoukou_diagnostics.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps(diag, ensure_ascii=False, indent=1))
print(dd.to_string(index=False))
print(pd.DataFrame(rows).to_string(index=False))
