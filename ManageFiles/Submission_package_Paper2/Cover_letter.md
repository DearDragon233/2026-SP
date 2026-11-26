# Cover Letter

*(Author names, affiliations and the corresponding author are left blank deliberately and must be inserted before submission.)*

Dear Editors of Agronomy,

Please consider our manuscript "Level and Pattern in Transferred County Wheat Yield Models: Weather Features, Training Labels and a Training-Mean Baseline Across Three North China Regions" for publication as a research article.

County-scale yield models are usually judged by pooled error against held-out statistics. We show that this metric mixes two abilities that come apart when a model is transferred to a new region: getting the yield level right and ranking counties within the region. Using official county-year statistics from four prefectures of the North China Plain (2017 to 2021), six weather features available by 30 April, and three fixed estimators, we trained models on statistical and on satellite-derived labels and scored both against the same held-out statistical yields under blocked validation and two external tests in Henan province.

The results change how the models should be ranked. Weather features beat a training-mean baseline only in forward-year validation within the same prefectures. In the Zhoukou external test, ridge regression appeared to transfer skill (MAE 380 versus 920 kg/ha, stable under 17 group deletions), but its county-year ordering was inverse to observation (r = -0.79, stable under leave-one-out) and its whole gain came from extrapolating the regional mean upward. In Pingdingshan the opposite happened: a satellite-trained random forest had the worst pooled error and the only significantly positive rank correlation (r = 0.92 on six county-years), a result that rests on a single low-yielding county and that we report as a hypothesis. Across 20 fitted model arms, raw and de-levelled advantage agreed in sign in 12 and disagreed in 8.

We think this fits Agronomy because it concerns how yield models should be evaluated before they are used for county-scale mapping, and because it offers a reporting rule rather than a new estimator: give the level error and the within-region rank skill separately, keep the training-mean baseline, and compare training-label sources on a common statistical target. The design follows the journal's recent call for standardised benchmark practice [Agronomy 2026, 16, 1131]: cohorts, folds and model settings were frozen before any result was produced, and every number in the manuscript regenerates from a stored ledger.

All data are public. Yearbook tables were obtained from municipal statistics bureaus and every record carries its source; county boundaries are the geoBoundaries ADM3 snapshot; satellite yields are the ChinaWheatYield30m product; weather is the NASA POWER daily service. The manuscript is original, is not under consideration elsewhere, and all authors have approved submission. There are no conflicts of interest.

Suggested reviewers (no collaboration in the past five years): researchers working on spatial and temporal validation of crop yield models, on satellite-derived yield products for winter wheat in China, and on county-scale agricultural statistics.

Yours sincerely,

[Corresponding author]
[Affiliation]
[Email]
