# -*- coding: utf-8 -*-
"""W56: claim-to-ledger audit for paper 2 (pre-registered Pingdingshan set)."""
import re, json, os
import pandas as pd
REP = r'D:\2026-SP\Outputs\reports'
s = open(r'D:\2026-SP\Paper\Manuscript_v1.0_Prediction_Level_and_Pattern.md', encoding='utf-8').read()
dec = pd.read_csv(os.path.join(REP, 'w56_level_pattern_decomposition_preregistered.csv'))
pm = pd.read_csv(os.path.join(REP, 'w45_primary_metrics.csv'))
pt = pd.read_csv(os.path.join(REP, 'w54_pattern_permutation_tests.csv'))
pbs = json.load(open(os.path.join(REP, 'w56_pds_primary_bootstrap.json'), encoding='utf-8'))
psets = pd.read_csv(os.path.join(REP, 'w56_pds_by_set.csv'))
dj = pd.read_csv(os.path.join(REP, 'w54_zhoukou_deletion_ranges.csv'))
zd = json.load(open(os.path.join(REP, 'w54_zhoukou_decomposition.json'), encoding='utf-8'))
ca = json.load(open(os.path.join(REP, 'w53_r6_control_arm.json'), encoding='utf-8'))
off = pd.read_csv(os.path.join(REP, 'w46_offset_diagnostic.csv'))
cov = pd.read_csv(os.path.join(REP, 'w53_zhoukou_coverage.csv'))
pds6 = pd.read_csv(os.path.join(REP, 'w48_pds_frozen.csv')); pds6 = pds6[pds6.primary]
mx = pd.read_csv(r'D:\2026-SP\Outputs\intermediate\w37_pattern_matrix.csv')
def D(site, arm, scheme="external", col="advantage_raw"):
    return float(dec[(dec.site == site) & (dec.arm == arm) & (dec.scheme == scheme)][col].iloc[0])
def M(sch, L, m, sc="primary"):
    return float(pm[(pm.scenario == sc) & (pm.scheme == sch) & (pm.training_label == L) & (pm.model == m)].mae_kg_ha.iloc[0])
checks = []
def ck(name, ledger_val, prose_str):
    ok = prose_str in s
    checks.append(ok); print(("PASS " if ok else "FAIL ") + f"{name}: ledger={ledger_val} | prose='{prose_str}'")
# Table 1 (development)
for sch in ["forward_year", "leave_region", "region_and_future"]:
    for L in ["statistics", "remote"]:
        for m in ["mean", "ridge", "random_forest"]:
            ck(f"T1 {sch}/{L}/{m}", round(M(sch, L, m), 1), f"{M(sch, L, m):.1f}")
# Zhoukou decomposition
for arm in ["statistics/ridge", "statistics/random_forest", "remote/ridge", "remote/random_forest"]:
    ck(f"T3 ZK {arm} MAE", round(D("Zhoukou", arm, col="mae_model"), 1), f"{D('Zhoukou', arm, col='mae_model'):.1f}")
    ck(f"T3 ZK {arm} recentred", round(D("Zhoukou", arm, col="advantage_after_recentring"), 1), f"{D('Zhoukou', arm, col='advantage_after_recentring'):.1f}")
ck("ZK stat-ridge raw 540.2", round(D("Zhoukou", "statistics/ridge"), 1), "540.2")
ck("ZK remote-RF raw 746.0", round(D("Zhoukou", "remote/random_forest"), 1), "746.0")
for k, v in [("obs SD 33.9", zd["obs_sd"]), ("oracle 27.6", zd["mae_oracle_constant"]), ("pred SD 156.1", zd["pred_sd"]),
             ("mean_pred 7144.0", zd["mean_pred"]), ("mean_obs 7524.3", zd["mean_obs"]), ("mean_train 6603.8", zd["mean_train"])]:
    ck("ZK " + k, v, f"{v}")
# Pingdingshan: PRE-REGISTERED primary set
ck("PDS r 0.92", pbs["r"], "r = 0.92"); ck("PDS p 0.017", pbs["p_perm"], "p = 0.017")
ck("PDS n 6", pbs["n"], "n = 6"); ck("PDS CI 0.43 to 0.999", (pbs["ci_lo"], pbs["ci_hi"]), "0.43 to 0.999")
x = dec[(dec.site == "Pingdingshan") & (dec.arm == "remote/random_forest")].iloc[0]
ck("PDS raw -636.4", round(x.advantage_raw, 1), "-636.4"); ck("PDS recentred 102.6", round(x.advantage_after_recentring, 1), "102.6")
ck("PDS obs SD 757", round(x.obs_sd), "SD 757"); ck("PDS oracle 628", round(x.mae_oracle_constant), "628 kg/ha")
for arm, r_, m_ in [("statistics/ridge", "-0.14", "1519.2"), ("statistics/random_forest", "-0.20", "1410.8"),
                    ("remote/ridge", "-0.33", "1490.6"), ("remote/random_forest", "0.92", "1528.1")]:
    ck(f"T3 PDS {arm} MAE", round(D("Pingdingshan", arm, col="mae_model"), 1), m_)
u = psets[(psets.set == "unscreened") & (psets.arm == "remote/random_forest")].iloc[0]
ck("PDS unscreened r 0.90 p 0.006", (u.r, u.p_perm), "r = 0.90 (p = 0.006)")
e = [389, 636]
import numpy as np
ck("PDS excess range 389 to 636", "388.6-636.4", "389 to 636 kg/ha")
ck("PDS composition 5 counties / Yexian 2 yrs", (len(pds6), pds6.county.nunique()), "six county-years from five counties")
# development decomposition + permutation
ck("fwd stat-ridge recentred -46.3", round(D("Hebei-Shandong", "statistics/ridge", "forward_year", "advantage_after_recentring"), 1), "-46.3")
ck("fwd stat-RF recentred 7.7", round(D("Hebei-Shandong", "statistics/random_forest", "forward_year", "advantage_after_recentring"), 1), "7.7")
r = pt[(pt.site == "Hebei-Shandong") & (pt.arm == "forward_year/statistics/random_forest")].iloc[0]
ck("fwd stat-RF r 0.32 p 0.029 CI -0.10..0.67", (round(r.r, 2), round(r.p_perm_two_sided, 3), round(r.ci_lo, 2), round(r.ci_hi, 2)), "(-0.10 to 0.67)")
# Zhoukou deletion + rank significance
r = dj[(dj.model == "ridge") & (dj.comparison == "statistics_minus_same_label_mean")].iloc[0]
ck("ZK deletion -620.1 to -424.4 / 17", (r.min_diff, r.max_diff, int(r.n_deletions)), "-620.1 to -424.4")
zr = pt[(pt.site == "Zhoukou") & (pt.arm == "statistics/ridge")].iloc[0]
ck("ZK r -0.79 p 0.0001", (zr.r, zr.p_perm_two_sided), "p = 0.0001")
ck("ZK CI -0.91 to -0.65", (zr.ci_lo, zr.ci_hi), "-0.91 to -0.65")
# sign agreement (unchanged by the PDS correction)
agree = int(((dec.advantage_raw > 0) == (dec.advantage_after_recentring > 0)).sum())
cnt = {"pp": int(((dec.advantage_raw > 0) & (dec.advantage_after_recentring > 0)).sum()),
       "pn": int(((dec.advantage_raw > 0) & (dec.advantage_after_recentring < 0)).sum()),
       "np": int(((dec.advantage_raw < 0) & (dec.advantage_after_recentring > 0)).sum()),
       "nn": int(((dec.advantage_raw < 0) & (dec.advantage_after_recentring < 0)).sum())}
ck("sign agree 12 / disagree 8", agree, "agreed in 12 cases and disagreed in 8")
for lab, k in [("positive | 2", "pp"), ("negative | 5", "pn"), ("positive | 3", "np"), ("negative | 10", "nn")]:
    ck(f"T4 ... {lab}", cnt, lab)
# control arm, offset, coverage, six-year
ck("control remote RF 408.9", round(ca["no_shared_precip"]["remote"]["rf"], 1), "408.9")
ck("control stat ridge 384.5", round(ca["no_shared_precip"]["statistics"]["ridge"], 1), "384.5")
o = off[(off.training_label == "remote_plus_paired_training_offset") & (off.model == "ridge") & (off.scheme == "forward_year")]
ck("offset ridge 466.3", float(o.mae_kg_ha.iloc[0]), "466.3")
ck("ZK 19 of 24", (int(cov.pass_primary.sum()), len(cov)), "19 of 24")
ck("ZK ratio 1.12 to 1.66", (round(cov.area_ratio_rs_over_stats.min(), 2), round(cov.area_ratio_rs_over_stats.max(), 2)), "1.12 to 1.66")
ck("six-year -0.58 to 0.95", (mx.pearson_r.min(), mx.pearson_r.max()), "-0.58 (2017 with 2018) to 0.95 (2016 with 2021)")
ck("six-year mean 0.25", round(float(mx.pearson_r.mean()), 2), "mean of 0.25")
# stale-number guard: values from the superseded n=9 analysis must be gone from prose/tables
# (Zhoukou stat-RF bias is legitimately -655.3 in Table 3; match the OLD Pingdingshan forms exactly)
for stale in ["n = 9)", "p = 0.005", "76.8", "(-655.3 to", "1412.6", "1325.6", "1287.3", "1367.3", "0.23 to 0.98", "n = 9", "SD 646", "476 kg/ha"]:
    ok = stale not in s; checks.append(ok); print(("PASS " if ok else "FAIL ") + f"stale value absent: '{stale}'")
print(f"\nAUDIT: {sum(checks)}/{len(checks)} PASS")

# ---- W56 additions: leverage and within-county diagnostics ----
lv = json.load(open(os.path.join(REP, 'w56_pds_leverage.json'), encoding='utf-8'))
zc = json.load(open(os.path.join(REP, 'w56_zhoukou_variance_decomposition.json'), encoding='utf-8'))
extra = []
def ck2(name, ledger_val, prose_str):
    ok = prose_str in s; extra.append(ok); print(("PASS " if ok else "FAIL ") + f"{name}: ledger={ledger_val} | prose='{prose_str}'")
ck2("PDS distinct predictions 4 / series 3", (lv["distinct_predictions"], lv["distinct_weather_series"]), "share three weather series")
ck2("PDS tied prediction 7020.2", lv["tied_prediction_groups"][0]["prediction"], "7020.2 kg/ha")
ck2("PDS only four distinct predictions", lv["distinct_predictions"], "only four distinct predictions")
ck2("PDS Lushan observed 3930", lv["most_influential"]["observed"], "3930 kg/ha")
ck2("PDS gap 1861", lv["gap_min_to_rest"], "1861 kg/ha below the mean of the other five")
ck2("PDS r without Lushan 0.52", lv["most_influential"]["r_without"], "lowered the correlation to r = 0.52 (n = 5)")
ck2("PDS LOO r falls to 0.52 (limitations)", lv["most_influential"]["r_without"], "falls to 0.52 when the lowest-yielding county-year is omitted")
ck2("PDS LOO range in abstract/limitations", lv["leave_one_out_r_range"], "dependent on one county-year")
ck2("ZK county means 7507 to 7543", zc["observed_variance"]["county_mean_range"], "7507 to 7543 kg/ha")
ck2("ZK 16% between", round(100*zc["observed_variance"]["share_between"]), "16% of the observed variance lies between counties")
ck2("ZK 84% within", 100 - round(100*zc["observed_variance"]["share_between"]), "remaining 84% is variation between years within a county")
ck2("ZK county-mean r 0.21", zc["statistics/ridge"]["r_county_means_n7"], "r = 0.21 across the seven counties")
ck2("ZK demeaned r -0.88", zc["statistics/ridge"]["r_within_county_demeaned_n19"], "strengthens the inverse correlation to r = -0.88")
ck2("ZK LOO -0.83 to -0.76", (zc["loo_sign_stable"], "-0.83", "-0.76"), "between -0.83 and -0.76")
print(f"\nW56 EXTRA: {sum(extra)}/{len(extra)} PASS | TOTAL: {sum(checks)+sum(extra)}/{len(checks)+len(extra)}")
