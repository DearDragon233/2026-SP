# -*- coding: utf-8 -*-
"""W56: polish pass for paper 2 (humanizer + nature-polishing), file mode.
Prose only. Also applies factual corrections found during the read-through:
 - section navigation in the Introduction
 - Pingdingshan rank statistics on the PRE-REGISTERED primary set (n=6)
 - figure captions brought in line with the rebuilt figures
Numbers are taken from: w56_level_pattern_decomposition_preregistered.csv,
w56_pds_by_set.csv, w56_pds_primary_bootstrap.json."""
import re
p = r'D:\2026-SP\Paper\Manuscript_v1.0_Prediction_Level_and_Pattern.md'
s = open(p, encoding='utf-8').read()
orig = s
n = 0
def rep(old, new, count=1):
    global s, n
    assert s.count(old) == count, f"anchor count {s.count(old)} != {count}: {old[:70]}"
    s = s.replace(old, new); n += 1

# ---------------- Abstract ----------------
rep("County-scale winter wheat yield models are often judged by mean absolute error (MAE) against held-out statistics, yet MAE mixes two different abilities: getting the yield level of a region right and ranking counties within it. We separated the two for weather-driven models across three regions of the North China Plain.",
    "County-scale winter wheat yield models are usually judged by mean absolute error (MAE) against held-out statistics. MAE combines two abilities that can be separated: estimating the yield level of a region and ranking the counties within it. We separated them for weather-driven models across three regions of the North China Plain.")
rep("In Pingdingshan the opposite occurred: a satellite-trained random forest had the worst MAE and the only significantly positive within-region rank correlation (r = 0.90, p = 0.005, n = 9).",
    "In Pingdingshan the reverse held: a satellite-trained random forest had the worst MAE and the only significantly positive within-region rank correlation (r = 0.92, p = 0.017, n = 6).")

# ---------------- Introduction ----------------
rep("Weather-driven statistical models remain the simplest way to produce such forecasts. A second question has joined the first: which yields the models should be trained on.",
    "Weather-driven statistical models remain the simplest way to produce them. A second question concerns the yields the models are trained on.")
rep("Most of these studies report accuracy metrics that pool all errors. Mean absolute error and root mean squared error do not distinguish a model that gets the regional yield level right from one that ranks counties correctly within a region. The distinction matters when a model is applied to a new region, because yield levels differ strongly between regions while within-region differences are comparatively small. A model can lower pooled MAE by shifting its predictions toward the new region's level without knowing which counties are better than others, and it can be penalised for the opposite.",
    "Most of these studies report accuracy metrics that pool all errors. Mean absolute error and root mean squared error do not separate a model that estimates the regional yield level from one that ranks counties within the region. The two come apart when a model is applied to a new region, because yield levels differ strongly between regions and much less within them. A model can lower pooled MAE by shifting its predictions toward the new region's level while knowing nothing about which counties yield more, and a model with the right ranking can be penalised for a poor level.")
rep("Two further design choices affect the conclusion. Random cross-validation lets neighbouring counties and adjacent years appear on both sides of the split; spatial and temporal blocking are the recommended alternative [8–11]. And a training-mean predictor is a necessary baseline for small county-year panels, because flexible estimators can fit noise when the number of independent weather series is low [12,13]. Calls for standardised benchmark practice in crop prediction make the same point: fixed cohorts, declared baselines and validation splits released with the results [16].",
    "Two design choices also affect the conclusion. Random cross-validation lets neighbouring counties and adjacent years appear on both sides of the split, so spatial and temporal blocking are recommended instead [8–11]. A training-mean predictor is a necessary baseline for small county-year panels, because flexible estimators can fit noise when few independent weather series are available [12,13]. Recent calls for standardised benchmark practice in crop prediction ask for fixed cohorts, declared baselines and released validation splits [16].")
rep("The present study asks three questions on official county-year statistics of winter wheat in the North China Plain. First, under blocked validation, do weather features add skill over a training-mean predictor, and does the answer depend on the training-label source? Second, when a model transfers to a region absent from training, is its error a level error or a pattern error? Third, how consistent are the model rankings obtained from pooled MAE with those obtained after removing the level? Section 2 describes the data sources and the rules fixed before any result was produced, Section 3 the estimators and the decomposition, Section 4 the results for the development panel and the two external tests, and Section 5 the implications.",
    "Using official county-year statistics of winter wheat in the North China Plain, we ask three questions. Under blocked validation, do weather features add skill over a training-mean predictor, and does the answer depend on the training-label source? When a model transfers to a region absent from training, is its error a level error or a pattern error? How consistent are model rankings from pooled MAE with those from the de-levelled comparison? Section 2 describes the data and the rules fixed before any result was produced, Section 3 the estimators and the decomposition, Section 4 the results, and Section 5 their implications.")

# ---------------- Methods 2.2 (not X, but Y) ----------------
rep("The ratio is a measure of spatial support, not of map accuracy.",
    "The ratio measures spatial support; it says nothing about map accuracy.")

# ---------------- Results 3.2 ----------------
rep("The best estimator therefore depended on the validation scheme. Changing the coverage screen changed which estimator was best in the statistical arm under forward-year validation, so the forward-year ranking should not be read as stable.",
    "The best estimator thus depended on the validation scheme. It also depended on the coverage screen: under forward-year validation a different screen changed which estimator was best in the statistical arm, so that ranking is not stable.")

# ---------------- Results 3.3 ----------------
rep("Observed yields vary far more between county-years than the models' predictions do. On the forward-year folds the standard deviation of observed yield was 593 kg/ha, the standard deviation of ridge predictions 196 and that of random forest predictions 328 (Table 2). A constant placed at the true mean of each test set would score 391 kg/ha, lower than every fitted model.",
    "Observed yields vary far more between county-years than the models' predictions. On the forward-year folds the standard deviation of observed yield was 593 kg/ha, against 196 for ridge predictions and 328 for random forest predictions (Table 2). A constant placed at the true mean of each test set would score 391 kg/ha, less than any fitted model.")
rep("None of the within-region rank correlations on the development folds reached significance after re-centring except the forward-year random forest with statistical labels (r = 0.32, permutation p = 0.029), whose bootstrap interval crosses zero.",
    "On the development folds only the forward-year random forest with statistical labels had a rank correlation with a permutation p below 0.05 (r = 0.32, p = 0.029), and its bootstrap interval crosses zero (-0.10 to 0.67).")

# ---------------- Results 3.4 ----------------
rep("On the development folds the statistical-label arm had lower error than the satellite-label arm for every scheme and estimator. The sign reversed in the external tests.",
    "On the development folds the statistical-label arm had lower error than the satellite-label arm for every scheme and estimator. The external tests gave the opposite sign.")
rep("A training-fold offset correction that adds the mean difference between paired labels reduced the satellite-trained ridge error on the forward-year folds from 543.8 to 466.3 kg/ha, which shows that part of the satellite-arm penalty is a level offset inherited from the labels.",
    "Adding the mean difference between paired labels, computed from the training fold only, reduced the satellite-trained ridge error on the forward-year folds from 543.8 to 466.3 kg/ha. Part of the penalty of the satellite arm is therefore a level offset inherited from its labels.")

# ---------------- Results 3.5 (pre-registered n=6) ----------------
i = s.find("### 3.5. Pingdingshan"); j = s.find("**Table 3.**")
assert i > 0 and j > i
s = s[:i] + """### 3.5. Pingdingshan: the mean leads, yet one model ranks counties correctly

All four fitted models had a higher MAE than their own training mean in Pingdingshan (Table 3). On the six county-years of the primary set the excess ranged from 389 to 636 kg/ha and stayed positive when one harvest year, county or weather series at a time was omitted from the scoring. The rank results differed. The satellite-trained random forest ordered the six county-years with r = 0.92 (permutation p = 0.017; bootstrap 95% interval 0.43 to 0.999), the only significantly positive rank correlation among the 20 arms, although its MAE was the highest of all. After re-centring it was 102.6 kg/ha better than its baseline. Observed yields in Pingdingshan are heterogeneous (SD 757 kg/ha) and an oracle constant would still score 628 kg/ha, so in this region most of the available skill lies in the ranking. The result held on the unscreened set of nine county-years (r = 0.90, p = 0.006); the strict set has three county-years and cannot support a rank test.

""" + s[j:]; n += 1

# Table 3 Pingdingshan rows -> primary set
old_pds = """| Pingdingshan | Statistics | Mean | 9 | 896.7 | -896.7 | - | - | - |
| Pingdingshan | Statistics | Ridge | 9 | 1367.3 | -1367.3 | -0.15 | 0.74 | -42.2 |
| Pingdingshan | Statistics | Random forest | 9 | 1287.3 | -1287.3 | -0.07 | 0.88 | -17.3 |
| Pingdingshan | Satellite | Mean | 9 | 757.3 | -757.3 | - | - | - |
| Pingdingshan | Satellite | Ridge | 9 | 1325.6 | -1325.6 | -0.27 | 0.52 | -91.4 |
| Pingdingshan | Satellite | Random forest | 9 | 1412.6 | -1412.6 | 0.90 | 0.005 | 76.8 |"""
new_pds = """| Pingdingshan | Statistics | Mean | 6 | 1022.2 | -1022.2 | - | - | - |
| Pingdingshan | Statistics | Ridge | 6 | 1519.2 | -1519.2 | -0.14 | 0.77 | -45.7 |
| Pingdingshan | Statistics | Random forest | 6 | 1410.8 | -1410.8 | -0.20 | 0.77 | -27.3 |
| Pingdingshan | Satellite | Mean | 6 | 891.7 | -891.7 | - | - | - |
| Pingdingshan | Satellite | Ridge | 6 | 1490.6 | -1490.6 | -0.33 | 0.48 | -102.1 |
| Pingdingshan | Satellite | Random forest | 6 | 1528.1 | -1528.1 | 0.92 | 0.017 | 102.6 |"""
rep(old_pds, new_pds)
rep("**Table 3.** External tests, primary sets. Test target is held-out statistical yield.",
    "**Table 3.** External tests on the pre-registered primary sets. Test target is held-out statistical yield in every case.")

# ---------------- Results 3.6 ----------------
rep("The advantage of 540.2 kg/ha survived all 17 admissible group deletions, with a range from -620.1 to -424.4 kg/ha, and the satellite-trained random forest kept a 746.0 kg/ha advantage under the same procedure. Read alone, this is a successful transfer.\n\nThe decomposition shows otherwise.",
    "The advantage of 540.2 kg/ha survived all 17 admissible group deletions, with a range from -620.1 to -424.4 kg/ha, and the satellite-trained random forest kept a 746.0 kg/ha advantage under the same procedure. Judged by MAE alone, both models transferred successfully.\n\nThe decomposition gives a different account.")
rep("Ridge predictions varied much more (SD 156.1) and in the wrong direction; their correlation with observed yield was -0.79",
    "Ridge predictions varied much more (SD 156.1) and in the wrong direction, with a correlation to observed yield of -0.79")
rep("The gain therefore came from a single number. Ridge moved the predicted regional mean",
    "The gain came from the regional mean alone. Ridge moved it")

# ---------------- Results 3.7 ----------------
rep("The shared-input explanation is not supported at this level, although shared temperature inputs and any county-year calibration overlap in the product remain unresolved.",
    "Shared precipitation inputs do not explain the Zhoukou result. Shared temperature inputs remain untested, and the product's county-year calibration overlap cannot be checked because no calibration ledger is published.")

# ---------------- Results 3.8 ----------------
rep("Only one arm combined a significantly positive rank correlation with a positive de-levelled advantage.",
    "One arm combined a significantly positive rank correlation with a positive de-levelled advantage: the satellite-trained random forest in Pingdingshan.")
rep("| Raw negative, de-levelled positive | 3 | Pingdingshan random forest, satellite (-655.3 to +76.8) |",
    "| Raw negative, de-levelled positive | 3 | Pingdingshan random forest, satellite (-636.4 to +102.6) |")

# ---------------- Results 3.9 ----------------
rep("The product did reproduce a regional signal: the 2018 mean of 5.01 t/ha was below every other year, consistent with the late-spring frost of that year in the North China Plain. Year-to-year level variation is captured; the within-region spatial pattern is not stable.",
    "The product did reproduce a regional signal: the 2018 mean of 5.01 t/ha was below every other year, consistent with the late-spring frost of that year in the North China Plain. The year-to-year level is therefore captured, whereas the within-region spatial pattern changes from year to year.")

# ---------------- Discussion 4.1 ----------------
rep("The main result is a measurement result. In three regions and two label arms, the ranking of models by pooled MAE changed once the level was removed. A linear model with no ability to rank counties obtained the largest apparent transfer gain of the study, because its extrapolation happened to raise the regional mean toward the truth. A random forest that ranked counties with r = 0.90 was ranked last by MAE in the same test, because its level was far too low. Any evaluation that reports only pooled error will misjudge both models.",
    "Our main result concerns measurement. Across three regions and two label arms, the ranking of models by pooled MAE changed once the level was removed. A linear model unable to rank counties obtained the largest apparent transfer gain of the study because its extrapolation happened to raise the regional mean toward the observed value. A random forest that ranked county-years with r = 0.92 had the highest MAE in the same test because its level was far too low. An evaluation that reports pooled error alone misjudges both.")
rep("The practical consequence is that two numbers should be reported for every transferred model: the level error, which a regional yield survey can correct after the season, and the within-region rank skill, which is what a county-scale map is used for. The rank skill can be assessed against the training mean after both have been re-centred, and we suggest that this de-levelled comparison accompany the raw one.",
    "Every transferred model should therefore be reported with two numbers: the level error, which a regional yield survey can correct after the season, and the within-region rank skill, which is what a county-scale map depends on. The rank skill can be compared with that of the training mean after both are re-centred, and we suggest reporting this de-levelled comparison next to the raw one.")

# ---------------- Discussion 4.2 ----------------
rep("This agrees with the small number of independent weather series: 9 series for 18 development units, so that leave-region folds test whether a model fitted on six Hebei series transfers to three Shandong series. Under those conditions the fitted models mostly reproduced the training level.",
    "The number of independent weather series is consistent with this: 9 series for 18 development units, so leave-region folds test whether a model fitted on six Hebei series transfers to three Shandong series. Under those conditions the fitted models mostly reproduced the training level.")
rep("The only positive rank skill appeared with a satellite-trained random forest in the region with the most heterogeneous yields. The finding rests on 9 county-years, a wide bootstrap interval and a single model arm, so we report it as a hypothesis.",
    "The only positive rank skill appeared with a satellite-trained random forest in the region with the most heterogeneous yields. The finding rests on six county-years, a bootstrap interval of 0.43 to 0.999 and a single model arm, so we report it as a hypothesis.")

# ---------------- Discussion 4.3 ----------------
rep("The satellite-label arm was uniformly worse on the development folds and better in two external comparisons. An offset correction using only training-fold information recovered part of the development-fold penalty, which suggests that the labels differ mainly in level.",
    "The satellite-label arm was worse in every development comparison and better in two external ones. An offset correction that uses training-fold information only recovered part of the development penalty, which suggests that the two labels differ mainly in level.")
rep("Where satellite labels are attractive for their coverage, a paired comparison on a common statistical target, as done here, is the minimum check.",
    "Where satellite labels are attractive for their coverage, a paired comparison on a common statistical target of the kind made here is the minimum check.")

# ---------------- Discussion 4.4 ----------------
rep("The two findings of this study are connected. A pooled error metric rewards a model for approaching the regional yield level, and a model-derived target can supply that level through its own construction. When a yield map or a process-model output is used both to train and to evaluate a model, the level is shared by construction and the pooled score is high before any county is ranked correctly. Official statistics remove that particular sharing, and blocked validation with a training-mean baseline, as used here, shows whether anything remains. In our tests what remained was small: one arm with a positive rank correlation out of twenty. We therefore treat level-and-pattern decomposition, and not a change of target or estimator, as the step that makes a county-scale transfer test interpretable.",
    "The two findings are connected. A pooled error metric rewards a model for approaching the regional yield level, and a model-derived target supplies that level through its own construction. When a yield map or a process-model output serves both to train and to evaluate a model, the level is shared and the pooled score is high before any county is ranked. Official statistics remove that sharing, and blocked validation with a training-mean baseline, as used here, shows what remains. In our tests little did: one arm in twenty had a significantly positive rank correlation. Level-and-pattern decomposition is therefore the step that makes a county-scale transfer test interpretable.")

# ---------------- Limitations ----------------
rep("The external evidence covers two prefectures of one province, and the Pingdingshan primary set has 6 county-years in the rank analysis and 9 in the paired analysis.",
    "The external evidence covers two prefectures of one province, and the Pingdingshan primary set has six county-years from four counties.")

# ---------------- Conclusions ----------------
rep("and the only significant positive rank skill (Pingdingshan, satellite-trained random forest) came with the worst raw error.",
    "and the only significant positive rank skill (Pingdingshan, satellite-trained random forest, r = 0.92 on six county-years) came with the highest raw error.")

# ---------------- Figure captions (match rebuilt figures) ----------------
rep("(a) County centroids within Zhoukou prefecture; dot colour marks whether the county passed the primary coverage screen in all its years.",
    "(a) County boundaries within Zhoukou prefecture; a county is drawn in green when it passed the primary coverage screen in all three years and in red otherwise.")
rep("(a) Observed statistical yield against prediction for statistical-label ridge, with the 1:1 line; the model under-predicts every county-year and orders them inversely.",
    "(a) Observed statistical yield against prediction for statistical-label ridge, with the fitted trend line, the observed regional mean and the training mean; the model under-predicts every county-year and orders them inversely.")

open(p, 'w', encoding='utf-8').write(s)
print(f"edits applied: {n}; words before {len(orig.split())} -> after {len(s.split())}")
