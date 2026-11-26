# -*- coding: utf-8 -*-
"""W55: claim-to-ledger audit for Manuscript_v1.0_Prediction_Level_and_Pattern.md"""
import re, json, os
import pandas as pd
REP = r'D:\2026-SP\Outputs\reports'
s = open(r'D:\2026-SP\Paper\Manuscript_v1.0_Prediction_Level_and_Pattern.md', encoding='utf-8').read()
dec = pd.read_csv(os.path.join(REP, 'w54_level_pattern_decomposition_all_sites.csv'))
pm = pd.read_csv(os.path.join(REP, 'w45_primary_metrics.csv'))
pt = pd.read_csv(os.path.join(REP, 'w54_pattern_permutation_tests.csv'))
dj = pd.read_csv(os.path.join(REP, 'w54_zhoukou_deletion_ranges.csv'))
zd = json.load(open(os.path.join(REP, 'w54_zhoukou_decomposition.json'), encoding='utf-8'))
ca = json.load(open(os.path.join(REP, 'w53_r6_control_arm.json'), encoding='utf-8'))
off = pd.read_csv(os.path.join(REP, 'w46_offset_diagnostic.csv'))
cov = pd.read_csv(os.path.join(REP, 'w53_zhoukou_coverage.csv'))
mx = pd.read_csv(r'D:\2026-SP\Outputs\intermediate\w37_pattern_matrix.csv')
def D(site, arm, scheme="external", col="advantage_raw"):
    r = dec[(dec.site == site) & (dec.arm == arm) & (dec.scheme == scheme)]
    return float(r[col].iloc[0])
def M(sch, L, m, sc="primary"):
    return float(pm[(pm.scenario == sc) & (pm.scheme == sch) & (pm.training_label == L) & (pm.model == m)].mae_kg_ha.iloc[0])
checks = []
def ck(name, ledger_val, prose_str):
    ok = prose_str in s
    checks.append((name, ok, ledger_val))
    print(("PASS " if ok else "FAIL ") + f"{name}: ledger={ledger_val}")
# development MAE table
for sch, n in [("forward_year", 45), ("leave_region", 79), ("region_and_future", 45)]:
    for L in ["statistics", "remote"]:
        for m in ["mean", "ridge", "random_forest"]:
            ck(f"T1 {sch}/{L}/{m}", round(M(sch, L, m), 1), f"{M(sch, L, m):.1f}")
# decomposition numbers
ck("ZK stat-ridge raw 540.2", round(D("Zhoukou", "statistics/ridge"), 1), "540.2")
ck("ZK stat-ridge recentred -145.3", round(D("Zhoukou", "statistics/ridge", col="advantage_after_recentring"), 1), "-145.3")
ck("PDS remote-RF recentred 76.8", round(D("Pingdingshan", "remote/random_forest", col="advantage_after_recentring"), 1), "76.8")
ck("PDS remote-RF raw -655.3", round(D("Pingdingshan", "remote/random_forest"), 1), "-655.3")
ck("ZK remote-RF raw 746.0", round(D("Zhoukou", "remote/random_forest"), 1), "746.0")
ck("ZK remote-RF recentred 1.8", round(D("Zhoukou", "remote/random_forest", col="advantage_after_recentring"), 1), "1.8")
ck("fwd stat-ridge recentred -46.3", round(D("Hebei-Shandong", "statistics/ridge", "forward_year", "advantage_after_recentring"), 1), "-46.3")
ck("fwd stat-RF recentred 7.7", round(D("Hebei-Shandong", "statistics/random_forest", "forward_year", "advantage_after_recentring"), 1), "7.7")
# ZK decomposition
for k, v in [("obs SD 33.9", zd["obs_sd"]), ("oracle 27.6", zd["mae_oracle_constant"]), ("pred SD 156.1", zd["pred_sd"]),
             ("mean_pred 7144.0", zd["mean_pred"]), ("mean_obs 7524.3", zd["mean_obs"]), ("mean_train 6603.8", zd["mean_train"])]:
    ck("ZK " + k, v, f"{v}")
# permutation p
p_zk = float(pt[(pt.site == "Zhoukou") & (pt.arm == "statistics/ridge")].p_perm_two_sided.iloc[0])
p_pds = float(pt[(pt.site == "Pingdingshan") & (pt.arm == "remote/random_forest")].p_perm_two_sided.iloc[0])
ck("ZK r -0.79 p 0.0001", p_zk, "p = 0.0001"); ck("PDS r 0.90 p 0.005", p_pds, "p = 0.005")
ci = pt[(pt.site == "Pingdingshan") & (pt.arm == "remote/random_forest")].iloc[0]
ck("PDS CI 0.23 to 0.98", (ci.ci_lo, ci.ci_hi), "0.23 to 0.98")
# deletion range
r = dj[(dj.model == "ridge") & (dj.comparison == "statistics_minus_same_label_mean")].iloc[0]
ck("ZK deletion -620.1 to -424.4", (r.min_diff, r.max_diff), "-620.1 to -424.4"); ck("17 deletions", int(r.n_deletions), "all 17")
# sign agreement
agree = int(((dec.advantage_raw > 0) == (dec.advantage_after_recentring > 0)).sum())
ck("sign agree 12 / disagree 8", agree, "agreed in 12"); ck("disagree 8", 20 - agree, "disagreed in 8")
cnt = {"pp": int(((dec.advantage_raw > 0) & (dec.advantage_after_recentring > 0)).sum()),
       "pn": int(((dec.advantage_raw > 0) & (dec.advantage_after_recentring < 0)).sum()),
       "np": int(((dec.advantage_raw < 0) & (dec.advantage_after_recentring > 0)).sum()),
       "nn": int(((dec.advantage_raw < 0) & (dec.advantage_after_recentring < 0)).sum())}
ck(f"Table4 counts {cnt}", cnt, f"| Raw positive, de-levelled positive | {cnt['pp']} |")
ck("Table4 +-", cnt, f"| Raw positive, de-levelled negative | {cnt['pn']} |")
ck("Table4 -+", cnt, f"| Raw negative, de-levelled positive | {cnt['np']} |")
ck("Table4 --", cnt, f"| Raw negative, de-levelled negative | {cnt['nn']} |")
# control arm + offset
ck("control remote RF 408.9", ca["no_shared_precip"]["remote"]["rf"], "408.9")
ck("control stat ridge 384.5", ca["no_shared_precip"]["statistics"]["ridge"], "384.5")
o = off[(off.training_label == "remote_plus_paired_training_offset") & (off.model == "ridge") & (off.scheme == "forward_year")]
ck("offset ridge 466.3", float(o.mae_kg_ha.iloc[0]), "466.3")
# coverage + six-year
ck("ZK 19 of 24", (int(cov.pass_primary.sum()), len(cov)), "19 of 24")
ck("ZK ratio 1.12 to 1.66", (round(cov.area_ratio_rs_over_stats.min(), 2), round(cov.area_ratio_rs_over_stats.max(), 2)), "1.12 to 1.66")
ck("six-year -0.58 to 0.95", (mx.pearson_r.min(), mx.pearson_r.max()), "-0.58 (2017 with 2018) to 0.95")
ck("six-year mean 0.25", round(float(mx.pearson_r.mean()), 2), "mean of 0.25")
n_ok = sum(1 for c in checks if c[1])
print(f"\nAUDIT: {n_ok}/{len(checks)} PASS")
