p = r'D:\2026-SP\Paper\Manuscript_v1.0_Prediction_Level_and_Pattern.md'
s = open(p, encoding='utf-8').read()
n = 0
def rep(old, new):
    global s, n
    assert s.count(old) == 1, f"anchor count {s.count(old)}: {old[:70]}"
    s = s.replace(old, new); n += 1
rep("A linear model unable to rank counties obtained the largest apparent transfer gain of the study because its extrapolation happened to raise the regional mean toward the observed value.",
    "A linear model that ordered county-years inversely obtained the largest apparent transfer gain of the study because its extrapolation happened to raise the regional mean toward the observed value.")
rep("In the external tests, the largest raw gain (Zhoukou, ridge) was entirely a level effect with county rankings inversely related to observation,",
    "In the external tests, the largest raw gain (Zhoukou, ridge) was entirely a level effect, and its county-year ordering was inverse to observation within counties (r = -0.88 after removing county means),")
# claim-to-ledger map: add the new ledgers
rep("| 3.6 deletions | w54_zhoukou_deletion_ranges.csv; w54_zhoukou_county_bias.csv |",
    "| 3.6 deletions | w54_zhoukou_deletion_ranges.csv; w54_zhoukou_county_bias.csv |\n| 3.5 leverage; 3.6 within-county | w56_pds_leverage.json; w56_zhoukou_leverage.json; w56_zhoukou_variance_decomposition.json; w56_pds_by_set.csv; w56_pds_primary_bootstrap.json |")
rep("| 3.2, Table 1 | w45_primary_metrics.csv |", "| 3.2, Table 1 | w45_primary_metrics.csv |\n| Table 3 (Pingdingshan rows) | w56_level_pattern_decomposition_preregistered.csv (pre-registered primary set, n = 6) |")
open(p, 'w', encoding='utf-8').write(s)
print("final wording edits:", n)
