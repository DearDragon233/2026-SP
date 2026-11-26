# Level and Pattern in Transferred County Wheat Yield Models: Weather Features, Training Labels and a Training-Mean Baseline Across Three North China Regions

**Manuscript v1.0** | 2026-11-26 | Target: Agronomy (MDPI) | Authors: [to be declared]

> Author list, affiliations, corresponding author and funding are deliberately left open at this stage. Every number in this manuscript regenerates from a frozen ledger in the repository (section mapping in Table 5).

---

## Abstract

County-scale winter wheat yield models are often judged by mean absolute error (MAE) against held-out statistics, yet MAE mixes two different abilities: getting the yield level of a region right and ranking counties within it. We separated the two for weather-driven models across three regions of the North China Plain. County-year yields from official yearbooks (Shijiazhuang, Tai'an, Pingdingshan and Zhoukou, 2017 to 2021) were paired with six weather features derived from daily NASA POWER data available by 30 April. Three fixed estimators (training mean, ridge regression, random forest) were trained separately on statistical and satellite-derived labels and scored against the same held-out statistical yields under forward-year, leave-region and joint holdouts, with two external tests in Henan province. Models trained on statistical labels beat the training mean only in forward-year validation (ridge MAE 426.9 versus 496.0 kg/ha); under joint geographic and temporal holdout the training mean was best (470.4 versus 519.1 kg/ha and above). In the Zhoukou external test, ridge appeared to transfer skill (MAE 380.2 versus 920.4 kg/ha, robust to 17 group deletions), but its predictions ranked counties inversely to observation (r = -0.79, permutation p = 0.0001); the whole gain came from extrapolating the regional mean upward, and re-centring removed it. In Pingdingshan the opposite occurred: a satellite-trained random forest had the worst MAE and the only significantly positive within-region rank correlation (r = 0.90, p = 0.005, n = 9). Across 20 fitted model arms, the sign of the raw MAE advantage and of the advantage after re-centring agreed in 12 cases and disagreed in 8. We recommend reporting level error and within-region rank skill separately and retaining the training-mean baseline in every transfer test.

**Keywords:** winter wheat; county yield; transfer validation; training-mean baseline; yield label source; level and pattern decomposition

---

## 1. Introduction

Forecasts of county-scale crop yield are used for food-security assessments, insurance design and early-warning systems, and their value depends on skill in seasons and places not represented in the training data [1–3]. Weather-driven statistical models remain the simplest way to produce such forecasts. A second question has joined the first: which yields the models should be trained on. Official statistics are available for many counties but arrive late and at coarse resolution, whereas satellite-derived yield products cover every pixel and can be used as substitutes [4,5]. Recent work has coupled crop growth models with remote sensing and machine learning for phenology-driven wheat prediction in the North China Plain [6,13], and public benchmarks of administrative-unit yields with pre-defined forecast dates have been built [7].

Most of these studies report accuracy metrics that pool all errors. Mean absolute error and root mean squared error do not distinguish a model that gets the regional yield level right from one that ranks counties correctly within a region. The distinction matters when a model is applied to a new region, because yield levels differ strongly between regions while within-region differences are comparatively small. A model can lower pooled MAE by shifting its predictions toward the new region's level without knowing which counties are better than others, and it can be penalised for the opposite.

Two further design choices affect the conclusion. Random cross-validation lets neighbouring counties and adjacent years appear on both sides of the split; spatial and temporal blocking are the recommended alternative [8–11]. And a training-mean predictor is a necessary baseline for small county-year panels, because flexible estimators can fit noise when the number of independent weather series is low [12,13]. Calls for standardised benchmark practice in crop prediction make the same point: fixed cohorts, declared baselines and validation splits released with the results [16].

The present study asks three questions on official county-year statistics of winter wheat in the North China Plain. First, under blocked validation, do weather features add skill over a training-mean predictor, and does the answer depend on the training-label source? Second, when a model transfers to a region absent from training, is its error a level error or a pattern error? Third, how consistent are the model rankings obtained from pooled MAE with those obtained after removing the level? Section 2 describes the data sources and the rules fixed before any result was produced, Section 3 the estimators and the decomposition, Section 4 the results for the development panel and the two external tests, and Section 5 the implications.

---

## 2. Materials and Methods

### 2.1. Study regions and statistical yields

The development panel covers 18 county-level units in Shijiazhuang prefecture (Hebei, 12 units), Tai'an prefecture (Shandong, 5 units after exclusion of Taishan district) and the Fangshan district of Beijing (one unit, used only for a coverage diagnosis), with harvest years 2017 to 2021. The external tests use 5 county-level units in Pingdingshan prefecture (Henan) and 8 in Zhoukou prefecture (Henan). All are within the winter wheat zone of the North China Plain.

Statistical yield was computed as official wheat production divided by sown area for each county-year and stored in kg/ha. Shijiazhuang reports winter wheat explicitly; Tai'an and the Henan prefectures report wheat under a summer-harvest heading, and the autumn-sown season was confirmed from the yearbook tables and local evidence. Each record keeps the yearbook edition, table number, page and source URL. County polygons were taken from a single geoBoundaries ADM3 snapshot; polygons with the same romanised name in other provinces were excluded by requiring the polygon centroid to fall inside the prefecture bounding box. Two units were excluded before pairing: Taishan district, whose yearbook area refers to a scenic zone that does not match the polygon, and Chuanhui district and Huaiyang, whose administrative status changed during the period.

### 2.2. Satellite-derived yields

County yields from the ChinaWheatYield30m product [4] for 2016 to 2021 were computed as the area-weighted mean of valid positive 30 m pixels inside the county polygon. The ratio of positive-pixel area to reported sown area was recorded for every county-year. The ratio is a measure of spatial support, not of map accuracy. The primary analysis required the ratio to lie between 2/3 and 1.5; a strict interval of 0.80 to 1.25 and an unscreened set were retained as sensitivity analyses. Fangshan 2021 had a ratio of about 0.02 and was therefore never eligible.

### 2.3. Weather features

Daily NASA POWER data (MERRA-2) at the centroid of each county bounding box were summarised over the window 1 October of the preceding year to 30 April of the harvest year [14]. Six features were computed with fixed calendar windows: growing degree days above 0 °C for October to November, days with minimum temperature below -5 °C for December to February, cumulative precipitation for the same winter months, growing degree days above 0 °C for March to April, cumulative precipitation for March to April, and the number of April days with maximum temperature of at least 25 °C. No yield, area, yearbook or coordinate variable entered the feature set. The source response for every county was stored with its SHA-256 hash. The weather series are coarse: the 18 development units share 9 distinct daily series (6 in Hebei, 3 in Shandong), and the 8 Zhoukou counties share 7.

### 2.4. Rules fixed before pairing

The following were fixed before any paired result was produced and are recorded in the frozen design file. The primary sample is the Shijiazhuang and Tai'an county-year intersection for 2017 to 2021 passing the primary coverage screen. Three validation schemes are used: leave-region, with each prefecture in turn held out; forward-year, with the years 2019, 2020 and 2021 each predicted from earlier years only; and joint region-and-future holdout, with each prefecture in turn held out for each of those years using only earlier years from the other prefecture. Every fold contains at least two harvest years in training. Random splits and the held-out region's own labels are never used in training. County-year membership is identical for the two label arms.

### 2.5. External tests

Pingdingshan county-years were paired for 2019 to 2021 and Zhoukou for the same years, using the same yearbook, polygon, coverage and weather rules. Each external test year was predicted from all earlier development-panel years. Training membership did not change when the external coverage rule changed. The Pingdingshan primary set has 6 county-years and the Zhoukou primary set 19 (5 in 2019, 7 in 2020 and 7 in 2021).

### 2.6. Estimators

Three estimators were used without tuning: the mean of the training labels, ridge regression with within-fold standardisation and a regularisation constant of 1, and a random forest with 200 trees, a minimum of two training rows per terminal leaf and random seed 42. Each estimator was trained twice, once on statistical labels and once on satellite-derived labels, and both were scored against the same held-out statistical yields. Model parameters were not adjusted after seeing any result.

### 2.7. Metrics and decomposition

We report MAE in kg/ha as the primary metric, with root mean squared error and signed bias. For the external tests the paired MAE difference between two arms was recomputed after omitting one harvest year, one county or one weather series at a time, with predictions held fixed.

Each model's predictions were then decomposed into a level component and a pattern component. The level error is the difference between the mean prediction and the mean observation over the test set. The pattern component is the prediction after subtracting its own mean, and its quality is measured by the Pearson correlation between predictions and observations across the test counties (the within-region rank skill) and by the MAE after re-centring both the model and the baseline to the observed mean. A positive rank correlation means the model orders counties correctly; re-centring removes any advantage that comes only from a better regional mean. Significance of the correlation was assessed by 20,000 permutations of the observed values and 5,000 bootstrap resamples for a 95% interval.

### 2.8. Reproducibility

Yearbook sources, paired county-years, frozen cohorts, fold membership, all out-of-fold predictions and the scripts are in the repository. Source rasters come from Zenodo and weather from NASA POWER and are checked against recorded hashes. A single command regenerates every table and figure from the checked-in frozen files.

---

## 3. Results

### 3.1. Paired sample and coverage

Of the 94 county-years paired in the development panel, 79 passed the primary coverage screen (56 in Hebei and 23 in Shandong), 60 passed the strict screen and 85 were unscreened. In the Zhoukou candidates the coverage ratio ranged from 1.12 to 1.66, and 19 of 24 county-years passed the primary screen; Fugou county failed in all three years with a stable ratio of about 1.64, and Shangshui and Taikang failed marginally in 2019 (Figure 1).

### 3.2. Development panel: weather features beat the mean only forward in time

Table 1 gives MAE on the primary folds. In forward-year validation, ridge trained on statistical labels had the lowest error of the six arms (426.9 kg/ha over 45 test county-years) against a training-mean baseline of 496.0; the random forest reached 434.8. Trained on satellite labels, ridge was again the best of its arm (543.8) but worse than the statistical mean. Under leave-region validation the training mean was best for both label sources (473.6 and 563.6 kg/ha over 79 test county-years), and ridge with statistical labels rose to 810.8. Under the joint region-and-future holdout the training mean remained best (470.4 and 544.4 over 45 county-years); ridge reached 1663.9 with statistical labels because single folds extrapolated far outside the training range (Figure 2).

The best estimator therefore depended on the validation scheme. Changing the coverage screen changed which estimator was best in the statistical arm under forward-year validation, so the forward-year ranking should not be read as stable.

**Table 1.** MAE (kg/ha) on the primary development folds. Test target is held-out statistical yield in every case.

| Scheme | Test county-years | Training label | Training mean | Ridge | Random forest |
|---|---|---|---|---|---|
| Forward-year | 45 | Statistics | 496.0 | 426.9 | 434.8 |
| Forward-year | 45 | Satellite | 603.2 | 543.8 | 636.4 |
| Leave-region | 79 | Statistics | 473.6 | 810.8 | 478.0 |
| Leave-region | 79 | Satellite | 563.6 | 1076.5 | 787.3 |
| Region and future year | 45 | Statistics | 470.4 | 1663.9 | 519.1 |
| Region and future year | 45 | Satellite | 544.4 | 1147.1 | 719.5 |

### 3.3. The level explains most of the development-panel error

Observed yields vary far more between county-years than the models' predictions do. On the forward-year folds the standard deviation of observed yield was 593 kg/ha, the standard deviation of ridge predictions 196 and that of random forest predictions 328 (Table 2). A constant placed at the true mean of each test set would score 391 kg/ha, lower than every fitted model. After re-centring predictions and baselines to the observed mean, the advantage of the statistical random forest fell from 61.1 to 7.7 kg/ha and that of ridge from 69.0 to -46.3. None of the within-region rank correlations on the development folds reached significance after re-centring except the forward-year random forest with statistical labels (r = 0.32, permutation p = 0.029), whose bootstrap interval crosses zero.

**Table 2.** Level and pattern decomposition for the development folds, statistical-label arm.

| Scheme | Model | Raw advantage over mean | Rank r | Permutation p | Advantage after re-centring | MAE of oracle constant |
|---|---|---|---|---|---|---|
| Forward-year | Ridge | 69.0 | 0.06 | 0.72 | -46.3 | 390.8 |
| Forward-year | Random forest | 61.1 | 0.32 | 0.03 | 7.7 | 390.8 |
| Leave-region | Ridge | -337.2 | -0.20 | 0.07 | -245.7 | 456.7 |
| Leave-region | Random forest | -4.5 | -0.04 | 0.73 | 13.0 | 456.7 |
| Region and future | Ridge | -1193.5 | -0.15 | 0.33 | -1478.4 | 390.8 |
| Region and future | Random forest | -48.7 | -0.12 | 0.43 | -30.3 | 390.8 |

### 3.4. Training-label source changes errors and rankings without a consistent direction

On the development folds the statistical-label arm had lower error than the satellite-label arm for every scheme and estimator. The sign reversed in the external tests. In Pingdingshan the satellite-trained mean was better than the statistics-trained mean (891.7 against 1022.2 kg/ha), and in Zhoukou the satellite-trained random forest was the best of the four fitted models (435.8 kg/ha) while the satellite-trained ridge was the worst (696.8). A training-fold offset correction that adds the mean difference between paired labels reduced the satellite-trained ridge error on the forward-year folds from 543.8 to 466.3 kg/ha, which shows that part of the satellite-arm penalty is a level offset inherited from the labels.

### 3.5. Pingdingshan: the mean leads, yet one model ranks counties correctly

All four fitted models had higher MAE than their own training mean in Pingdingshan (Table 3). The excess ranged from 389 to 636 kg/ha on the six primary county-years and remained positive under every single-group deletion. The pattern result differed. The satellite-trained random forest ranked the nine paired counties with r = 0.90 (permutation p = 0.005; bootstrap 95% interval 0.23 to 0.98), the only significantly positive rank correlation among the 20 arms, although its MAE was the worst of all. After re-centring, this model was 76.8 kg/ha better than its baseline. Observed yields in Pingdingshan are heterogeneous (SD 646 kg/ha), and an oracle constant would still score 476 kg/ha, so ranking carries most of the achievable skill in this region.

**Table 3.** External tests, primary sets. Test target is held-out statistical yield.

| Region | Training label | Model | n | MAE | Bias | Rank r | Permutation p | Advantage after re-centring |
|---|---|---|---|---|---|---|---|---|
| Pingdingshan | Statistics | Mean | 9 | 896.7 | -896.7 | - | - | - |
| Pingdingshan | Statistics | Ridge | 9 | 1367.3 | -1367.3 | -0.15 | 0.74 | -42.2 |
| Pingdingshan | Statistics | Random forest | 9 | 1287.3 | -1287.3 | -0.07 | 0.88 | -17.3 |
| Pingdingshan | Satellite | Mean | 9 | 757.3 | -757.3 | - | - | - |
| Pingdingshan | Satellite | Ridge | 9 | 1325.6 | -1325.6 | -0.27 | 0.52 | -91.4 |
| Pingdingshan | Satellite | Random forest | 9 | 1412.6 | -1412.6 | 0.90 | 0.005 | 76.8 |
| Zhoukou | Statistics | Mean | 19 | 920.4 | -920.4 | - | - | - |
| Zhoukou | Statistics | Ridge | 19 | 380.2 | -380.2 | -0.79 | 0.0001 | -145.3 |
| Zhoukou | Statistics | Random forest | 19 | 655.3 | -655.3 | -0.60 | 0.009 | -12.4 |
| Zhoukou | Satellite | Mean | 19 | 1181.9 | -1181.9 | - | - | - |
| Zhoukou | Satellite | Ridge | 19 | 696.8 | -696.8 | -0.79 | 0.0001 | -124.6 |
| Zhoukou | Satellite | Random forest | 19 | 435.8 | -435.8 | 0.34 | 0.16 | 1.8 |

### 3.6. Zhoukou: a large apparent gain that is entirely a level effect

Statistical-label ridge reached 380.2 kg/ha in Zhoukou against a baseline of 920.4 (Table 3). The advantage of 540.2 kg/ha survived all 17 admissible group deletions, with a range from -620.1 to -424.4 kg/ha, and the satellite-trained random forest kept a 746.0 kg/ha advantage under the same procedure. Read alone, this is a successful transfer.

The decomposition shows otherwise. County yields in Zhoukou are nearly uniform: the standard deviation across the 19 test county-years was 33.9 kg/ha, so a constant at the observed mean would score 27.6 kg/ha. Ridge predictions varied much more (SD 156.1) and in the wrong direction; their correlation with observed yield was -0.79 (permutation p = 0.0001, bootstrap interval -0.91 to -0.65). All 19 predictions were below observation, with a mean bias of -380.2 kg/ha and county means between -349.9 and -399.5. None of the 19 test county-years had all six weather features inside the training range.

The gain therefore came from a single number. Ridge moved the predicted regional mean from the training mean of 6603.8 to 7144.0 kg/ha, closer to the observed 7524.3, by extrapolating along its linear coefficients. Re-centring the predictions to the observed level turned the 540.2 kg/ha advantage into a 145.3 kg/ha deficit (Figure 3). The satellite-trained random forest behaved differently: its predictions varied little (SD 18.5), its rank correlation was positive but not significant (r = 0.34), and re-centring left it 1.8 kg/ha better than its baseline.

### 3.7. Control for shared weather inputs

The satellite product uses temperature and precipitation from months that overlap our weather features. Dropping the two precipitation features from both training and test sets changed the satellite-trained random forest MAE in Zhoukou from 435.8 to 408.9 kg/ha and the statistical-label ridge from 380.2 to 384.5. The shared-input explanation is not supported at this level, although shared temperature inputs and any county-year calibration overlap in the product remain unresolved.

### 3.8. Agreement between raw and de-levelled rankings

Across the 20 fitted model arms, the sign of the raw MAE advantage and the sign of the advantage after re-centring agreed in 12 cases and disagreed in 8 (Table 4). The disagreements were of both kinds. Five arms had a raw advantage that disappeared or reversed after re-centring, including both Zhoukou ridge arms and the forward-year ridge arm on the development folds. Three arms showed the reverse, a raw disadvantage with a positive de-levelled advantage: the satellite-trained random forest in Pingdingshan and in Zhoukou, and the statistical random forest under leave-region validation. Only one arm combined a significantly positive rank correlation with a positive de-levelled advantage.

**Table 4.** Sign agreement between raw MAE advantage and de-levelled advantage across the 20 fitted arms.

| Pattern | Number of arms | Examples |
|---|---|---|
| Raw positive, de-levelled positive | 2 | Forward-year random forest, statistics (+61.1 to +7.7); Zhoukou random forest, satellite (+746.0 to +1.8) |
| Raw positive, de-levelled negative | 5 | Zhoukou ridge, statistics (+540.2 to -145.3) |
| Raw negative, de-levelled positive | 3 | Pingdingshan random forest, satellite (-655.3 to +76.8) |
| Raw negative, de-levelled negative | 10 | Joint holdout ridge, satellite (-602.7 to -420.0) |

### 3.9. Six-year consistency of the satellite product

Grid-level yields of the satellite product over 234 cells in the Pinggu district, extracted with the same window for 2016 to 2021, agreed between some years and not others. Across the 15 year pairs the Pearson correlation ranged from -0.58 (2017 with 2018) to 0.95 (2016 with 2021), with a mean of 0.25. The product did reproduce a regional signal: the 2018 mean of 5.01 t/ha was below every other year, consistent with the late-spring frost of that year in the North China Plain. Year-to-year level variation is captured; the within-region spatial pattern is not stable.

---

## 4. Discussion

### 4.1. Pooled MAE does not identify transferable skill

The main result is a measurement result. In three regions and two label arms, the ranking of models by pooled MAE changed once the level was removed. A linear model with no ability to rank counties obtained the largest apparent transfer gain of the study, because its extrapolation happened to raise the regional mean toward the truth. A random forest that ranked counties with r = 0.90 was ranked last by MAE in the same test, because its level was far too low. Any evaluation that reports only pooled error will misjudge both models.

The practical consequence is that two numbers should be reported for every transferred model: the level error, which a regional yield survey can correct after the season, and the within-region rank skill, which is what a county-scale map is used for. The rank skill can be assessed against the training mean after both have been re-centred, and we suggest that this de-levelled comparison accompany the raw one.

### 4.2. When weather features help

Weather features added skill over the training mean only when the test years were later than the training years within the same prefectures, and only with statistical labels. Once a whole prefecture was held out, with or without a year shift, the mean was better. This agrees with the small number of independent weather series: 9 series for 18 development units, so that leave-region folds test whether a model fitted on six Hebei series transfers to three Shandong series. Under those conditions the fitted models mostly reproduced the training level.

The only positive rank skill appeared with a satellite-trained random forest in the region with the most heterogeneous yields. The finding rests on 9 county-years, a wide bootstrap interval and a single model arm, so we report it as a hypothesis. A satellite training label supplies many more spatial units than yearbooks do, and a flexible estimator may learn within-region contrasts from it that a linear model cannot. Testing this requires a larger external panel with more regions.

### 4.3. Training-label source

The satellite-label arm was uniformly worse on the development folds and better in two external comparisons. An offset correction using only training-fold information recovered part of the development-fold penalty, which suggests that the labels differ mainly in level. The product is also calibrated against statistical data, and a county-year calibration ledger is not published, so the independence of satellite labels from the held-out statistical target cannot be fully established. Where satellite labels are attractive for their coverage, a paired comparison on a common statistical target, as done here, is the minimum check.

### 4.4. Relation to target-construction effects

The two findings of this study are connected. A pooled error metric rewards a model for approaching the regional yield level, and a model-derived target can supply that level through its own construction. When a yield map or a process-model output is used both to train and to evaluate a model, the level is shared by construction and the pooled score is high before any county is ranked correctly. Official statistics remove that particular sharing, and blocked validation with a training-mean baseline, as used here, shows whether anything remains. In our tests what remained was small: one arm with a positive rank correlation out of twenty. We therefore treat level-and-pattern decomposition, and not a change of target or estimator, as the step that makes a county-scale transfer test interpretable.

### 4.5. Limitations

The external evidence covers two prefectures of one province, and the Pingdingshan primary set has 6 county-years in the rank analysis and 9 in the paired analysis. Weather series are too coarse to resolve within-county exposure, and county centroids of bounding boxes are not representative of cropped area. Administrative statistics and the satellite product describe different spatial supports. The six features use fixed calendar windows rather than observed phenology. Real-time availability of the same data version by 30 April was not verified. Site-level yield observations were not available; a national agrometeorological station yield dataset exists [15] but could not be obtained through public search at the time of writing. With a sample of this size, rank correlations and their intervals should be read as indicative.

---

## 5. Conclusions

Under blocked validation on official county-year statistics of North China winter wheat, six weather features and three fixed estimators, we found the following. Weather features beat a training-mean baseline only in forward-year validation within the same prefectures. Under leave-region and joint holdout the mean was best. In the external tests, the largest raw gain (Zhoukou, ridge) was entirely a level effect with county rankings inversely related to observation, and the only significant positive rank skill (Pingdingshan, satellite-trained random forest) came with the worst raw error. Raw and de-levelled advantage agreed in sign for 12 of the 20 fitted model arms. We recommend that county-scale transfer studies report level error and within-region rank skill separately, retain the training-mean baseline, and run a paired label-source comparison on a common statistical target before adopting satellite-derived training labels.

---

## Data Availability Statement

Yearbook tables were obtained from the statistics bureaus of Shijiazhuang, Tai'an, Pingdingshan and Zhoukou; every record carries the edition, table, page and URL. County boundaries are the geoBoundaries CHN ADM3 snapshot (snapshot 1c423398df24). Satellite yields are from ChinaWheatYield30m (Zenodo, DOI 10.5281/zenodo.7360753; years 2016 to 2021). Weather data are from the NASA POWER daily API (MERRA-2), with request URLs and SHA-256 hashes of every response stored. Frozen cohorts, fold membership, out-of-fold predictions and all scripts are in the project repository.

---

## Figure Captions

**Figure 1.** Zhoukou external-test counties and the coverage screen. (a) County centroids within Zhoukou prefecture; dot colour marks whether the county passed the primary coverage screen in all its years. (b) Ratio of positive satellite-pixel area to yearbook sown area for each of the 24 candidate county-years; dotted lines mark the primary interval (2/3 to 1.5) and the solid line a ratio of one.

**Figure 2.** Label-source swap on the frozen development panel. MAE of the training mean, ridge and random forest under (a) forward-year, (b) leave-region and (c) joint region-and-future holdout. Solid bars are models trained on statistical labels, hatched bars models trained on satellite labels; the test target is held-out statistical yield in every case.

**Figure 3.** Level and pattern in the Zhoukou external test (n = 19). (a) Observed statistical yield against prediction for statistical-label ridge, with the 1:1 line; the model under-predicts every county-year and orders them inversely. (b) MAE before and after re-centring predictions and baselines to the observed mean, for all four fitted arms; the oracle constant is shown for reference.

**Figure 4.** Within-region rank correlation of predictions with observed yield for the 20 fitted arms, with permutation p-values and bootstrap 95% intervals. Filled markers are significant at 5%; the vertical line marks zero correlation.

**Figure 5.** Six-year consistency of the satellite product in Pinggu district. Pearson correlation of grid-level satellite yield between each pair of years, 2016 to 2021 (n = 15 to 22 grids per pair).

---

**Table 5.** Claim-to-ledger map for every number in this manuscript.

| Section | Ledger file |
|---|---|
| 3.1 | w44_frozen_design.md; w53_zhoukou_coverage.csv |
| 3.2, Table 1 | w45_primary_metrics.csv |
| 3.3, Table 2 | w54_level_pattern_decomposition_all_sites.csv; w54_pattern_permutation_tests.csv |
| 3.4 | w45_primary_metrics.csv; w46_offset_diagnostic.csv |
| 3.5, 3.6, Table 3 | w49_pds_primary_metrics.csv; w53_zhoukou_external_scores.csv; w54_zhoukou_decomposition.json |
| 3.6 deletions | w54_zhoukou_deletion_ranges.csv; w54_zhoukou_county_bias.csv |
| 3.7 | w53_r6_control_arm.json |
| 3.8, Table 4 | w54_level_pattern_decomposition_all_sites.csv |
| 3.9 | w37_pattern_matrix.csv; w37_sixyear_grid.csv |

---

## References

1. Lobell, D.B.; Roberts, M.J.; Schlenker, W.; Braun, N.; Little, B.B.; Rejesus, R.M.; Hammer, G.L. Greater sensitivity to drought accompanies maize yield increase in the U.S. Midwest. *Science* 2014, 344, 516-519.
2. Ray, D.K.; Gerber, J.S.; MacDonald, G.K.; West, P.C. Climate variation explains a third of global crop yield variability. *Nat. Commun.* 2015, 6, 5989.
3. van Klompenburg, T.; Kassahun, A.; Catal, C. Crop yield prediction using machine learning: A systematic literature review. *Comput. Electron. Agric.* 2020, 177, 105709.
4. Zhao, X.; et al. A 30 m annual winter wheat yield dataset of China (2016-2021). *Earth Syst. Sci. Data* 2023, 15, 4047-4063. DOI: 10.5194/essd-15-4047-2023.
5. Li, X.; Yu, L.; Du, Z.; Liu, X. Tracking spatiotemporal dynamics of crop-specific areas through machine learning and statistics disaggregating. *Sci. Data* 2025. DOI: 10.1038/s41597-025-05572-x.
6. Zhang, G.; et al. Integrating multi-source remote sensing and crop growth model for phenology-driven wheat yield prediction in the North China Plain. *J. Sci. Food Agric.* 2026, 106, 9468-9478. DOI: 10.1002/jsfa.70947.
7. Kallenberg, M.; Paudel, D.; Ofori-Ampofo, S.; Baja, H.; et al. CY-Bench: a comprehensive benchmark dataset for sub-national crop yield forecasting. *Earth Syst. Sci. Data* 2026, 18, 3997-4018. DOI: 10.5194/essd-18-3997-2026.
8. Roberts, D.R.; Bahn, V.; Ciuti, S.; et al. Cross-validation strategies for data with temporal, spatial, hierarchical, or phylogenetic structure. *Ecography* 2017, 40, 913-929.
9. Ploton, P.; Mortier, F.; Rejou-Mechain, M.; et al. Spatial validation reveals poor predictive performance of large-scale ecological mapping models. *Nat. Commun.* 2020, 11, 4540.
10. Meyer, H.; Pebesma, E. Machine learning-based global maps of ecological variables and the challenge of assessing them. *Nat. Commun.* 2022, 13, 2208.
11. Wadoux, A.M.J.-C.; Heuvelink, G.B.M.; de Bruin, S.; Brus, D.J. Spatial cross-validation is not the right way to evaluate map accuracy. *Ecol. Model.* 2021, 401, 115211.
12. Raudaschl, R.S.; et al. On the subsampling strategy for cross-validation of spatially autocorrelated data. *Ecol. Model.* 2022, 467, 109920.
13. Zhao, Y.; Xiao, D.; Bai, H.; et al. The prediction of wheat yield in the North China Plain by coupling crop model with machine learning algorithms. *Agriculture* 2023, 13, 99.
14. NASA Langley Research Center. Prediction Of Worldwide Energy Resources (POWER): Daily Point Data API. Available online: https://power.larc.nasa.gov/docs/services/api/temporal/daily/ (accessed on 24 November 2026).
15. Gao, J.; Liao, J.; Liu, Y. Development of crop yield dataset for China from 1981 to 2022. *Chin. J. Agrometeorol.* 2026, 47, 456-472. DOI: 10.3969/j.issn.1000-6362.2026.03.012.
16. Yan, M.; Wang, W.; Zhang, Y.; et al. Standardizing benchmarks for plant genomic prediction. *Agronomy* 2026, 16, 1131. DOI: 10.3390/agronomy16121131.
