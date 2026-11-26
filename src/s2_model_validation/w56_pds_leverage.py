# -*- coding: utf-8 -*-
"""W56: leave-one-out leverage diagnostics for the Pingdingshan rank correlation
(pre-registered primary set, n = 6). The satellite-trained random forest gives
identical predictions to county-years that share a weather series, so the rank
correlation may rest on a single county-year. Quantify it."""
import os, json
import numpy as np, pandas as pd, warnings
warnings.filterwarnings("ignore")
from scipy.stats import pearsonr, spearmanr

ROOT = r"D:\2026-SP"; REP = os.path.join(ROOT, "Outputs", "reports")
fz = pd.read_csv(os.path.join(REP, "w48_pds_frozen.csv"))[
    ["shape_id", "harvest_year", "county", "primary", "weather_series_id", "remote_area_to_stats_sown_area"]
].rename(columns={"primary": "fp"})
oof = pd.read_csv(os.path.join(REP, "w49_pds_oof.csv"))[
    ["shape_id", "harvest_year", "training_label", "model", "stats_kg_ha", "prediction_kg_ha"]
].merge(fz, on=["shape_id", "harvest_year"], validate="many_to_one")
g = oof[(oof.fp) & (oof.training_label == "remote") & (oof.model == "random_forest")].copy()
g = g.sort_values(["harvest_year", "county"]).reset_index(drop=True)
p, o = g.prediction_kg_ha.values, g.stats_kg_ha.values

out = {}
out["n"] = int(len(g))
out["r_all"] = round(float(pearsonr(p, o)[0]), 3)
out["spearman_all"] = round(float(spearmanr(p, o).statistic), 3)
out["distinct_predictions"] = int(pd.Series(p).nunique())
out["distinct_weather_series"] = int(g.weather_series_id.nunique())
out["counties_per_weather_series"] = {str(k): int(v) for k, v in g.groupby("weather_series_id").size().items()}
out["tied_prediction_groups"] = [
    {"prediction": round(float(k), 1), "county_years": [f"{c} {y}" for c, y in zip(v.county, v.harvest_year)]}
    for k, v in g.groupby("prediction_kg_ha") if len(v) > 1
]
# leave-one-out
loo = []
for i in range(len(g)):
    m = np.ones(len(g), bool); m[i] = False
    loo.append({"omitted": f"{g.county[i]} {g.harvest_year[i]}",
                "observed": round(float(o[i]), 1), "predicted": round(float(p[i]), 1),
                "r_without": round(float(pearsonr(p[m], o[m])[0]), 3),
                "spearman_without": round(float(spearmanr(p[m], o[m]).statistic), 3),
                "coverage_ratio": round(float(g.remote_area_to_stats_sown_area[i]), 3)})
loo = pd.DataFrame(loo).sort_values("r_without")
out["leave_one_out_r_range"] = [float(loo.r_without.min()), float(loo.r_without.max())]
out["most_influential"] = loo.iloc[0].to_dict()
out["observed_min"] = round(float(o.min()), 1)
out["observed_mean_without_min"] = round(float(np.sort(o)[1:].mean()), 1)
out["gap_min_to_rest"] = round(float(np.sort(o)[1:].mean() - o.min()), 1)
out["predicted_range"] = [round(float(p.min()), 1), round(float(p.max()), 1)]
out["observed_range"] = [round(float(o.min()), 1), round(float(o.max()), 1)]
# among the five non-extreme county-years: is there any ordering skill?
m5 = o > np.percentile(o, 20)
out["r_without_lowest_observed"] = round(float(pearsonr(p[m5], o[m5])[0]), 3)
out["n_without_lowest_observed"] = int(m5.sum())
loo.to_csv(os.path.join(REP, "w56_pds_leverage.csv"), index=False, encoding="utf-8-sig")
json.dump(out, open(os.path.join(REP, "w56_pds_leverage.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps(out, ensure_ascii=False, indent=1))
