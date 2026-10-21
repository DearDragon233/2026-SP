# The Trap of Model-Derived Yield Targets: A Controlled Diagnostic of Target Construction, Validation Design, and Co-Construction Bias in County-Scale Yield Mapping

**Full-text manuscript v5.0** | 2026-10-21 | Target: Agronomy (MDPI), Section: Precision and Digital Agriculture / Methods

> Status: prose under construction (W27 writing loop). Structure and all numbers traceable to frozen ledgers (Outputs/intermediate/w14–w26 series). Figure plan: figs 01–17 (main), S1 protocol self-assessment.

---

## Abstract

Regional yield mapping relies on model-derived targets because grid-scale field measurements are rare. We audited what such targets do to the apparent skill of environmental machine learning in Pinggu, Beijing (234 grids, 0.0417 degrees, 24 variables), where a provenance audit showed that all four obtainable yield targets are model products: a process-model baseline (43 grids, 7.21 plus or minus 0.23 t/ha), its interpolation, a Bayesian blend, and a satellite retrieval. The interpolated target yields cross-validated R2 = 0.98 although leave-one-out interpolation of its own sources reaches only 0.20 to 0.27, bounding circular validation. Checkerboard cross-validation is structurally inert in a domain 5.6 variogram ranges wide (between-block distance pinned at 2.3 to 2.4 km; optimism gap from +0.113 to -0.006), whereas gradient-cutting schemes reveal gaps up to +0.54. The same framework recovers R2 = 0.690 on a 7,784-grid regional gradient yet detects nothing at n = 43 even for planted true signals of R2 = 0.5: county-scale nulls are detectability limits. Two national products correlate at r = 0.017 while one environmental model explains both at R2 near 0.65; provincial statistics arbitrate (rho = 0.893 vs -0.04), proving co-construction bias. We release a six-step pre-mapping audit protocol that turns each trap into a checkable pre-condition.

**Keywords:** yield mapping; spatial cross-validation; circular validation; co-construction bias; model-derived targets; detectability; audit protocol

---

## 1. Introduction

Maps of crop yield are the operational currency of food-security monitoring, crop-insurance design, and climate-impact assessment [1–3]. Because combine-measured yields are almost never available at the grid scales these applications demand, the standard workflow trains machine-learning models of yield against *model-derived targets*: process-based crop-model outputs [4], satellite retrievals [5], or interpolations of sparse ground points. The community has grown adept at reporting high cross-validated skill for such models; it has been far less diligent in asking what, exactly, that skill measures.

Three methodological risks travel with this workflow, each documented in isolation. First, **target construction can manufacture skill**: a model evaluated against a spatial interpolation of its own training inputs recovers the interpolation, not the field (circular validation) [6,7]. Second, **validation design can conceal optimism**: random cross-validation under spatial autocorrelation inflates apparent accuracy, and block designs are the recommended remedy [8–10]–yet the remedy itself is rarely audited for whether the blocks actually separate training from validation neighbourhoods. Third, **environmental representation sets a detectability ceiling**: static covariates compress an environment that crops experience dynamically, and at small spatial extents the remaining signal may fall below any honest estimator's detection floor [11,12]. What no study has done is quantify the three risks *jointly, in one controlled design, on public data*–and then ask the question that emerges only when they are seen together: if a model reports high skill against two targets that disagree with each other, what is it actually predicting?

We answer these questions with a diagnostic study built on Beijing's Pinggu district and the public data ecosystem around it. The study began as a conventional exercise–predict winter-wheat yield from a 234-grid environmental fingerprint–and was progressively converted into an audit when its own results failed conventional expectations. A provenance audit established that every locally available yield target, including one initially labelled "observed", is a model product (Section 2). Controlled factorial experiments then quantified each trap: circular validation bounded analytically and empirically; checkerboard blocking shown to be structurally inert in small domains through a dose–response and nearest-neighbour analysis; and the one-axis structure of the environmental matrix exposed by principal-component screening. Two external checks generalise the diagnosis: the same framework recovers strong, genuine environmental signal across a 7,784-grid North China Plain gradient (R²=0.69), demonstrating that the county-scale null is a detectability outcome; and a statistical arbitration against official provincial surveys shows that two national yield products correlate at r=0.017 grid-to-grid while environmental models "explain" both equally–co-construction bias, proved directionally by the fact that only one of the two products carries statistical signal.

The contribution is fourfold: (i) quantified upper bounds for the target-construction and validation-design traps; (ii) a detectability framework (domain size × environmental variance × sample size × model complexity) that reconciles "environment matters" at regional gradients with honest nulls at county scale; (iii) directional proof of co-construction bias and its antidote–inter-target agreement audit with statistical arbitration; and (iv) a six-step pre-mapping audit protocol that converts every finding into a checkable pre-condition for any regional yield-mapping study.

---

## 2. Study Area, Targets, and the Provenance Audit

### 2.1 Study area and environmental matrix

Pinggu district (116.90–117.26 °E, 40.00–40.24 °N) spans a mountain-to-plain transition on the northern North China Plain, with elevations from 15 to 898 m across only ~26 km. We discretised the district into 234 grids on a 0.0417° lattice (≈3.6 × 4.6 km, anisotropic) and attached 24 modelling variables from WorldClim 2.1 [13] (19 bioclimatic plus monthly temperature and precipitation aggregates), SoilGrids 2.0 topsoil properties [14], and SRTM terrain derivatives. An empirical variogram of the yield-trap targets gives a spatial range of 4.62 km; the district spans only ~5.6 such ranges–a fact that becomes central in Section 5.

### 2.2 The four local targets and their provenance

The audit that anchors this paper established that **no grid-scale field-measured yield is publicly available for the study area**, and that all four obtainable targets are model products. Target **A** (43 grids; 7.21 ± 0.23 t/ha) is the baseline-period output of the process-model optimisation of Xiao et al. [4], extracted from their published 1-km raster (figshare DOI 10.6084/m9.figshare.24471919); its label as "observed" in early project documents was a provenance error, corrected here. Its magnitude–38% above the Beijing statistical mean of 5.24 t/ha–matches potential-yield semantics. Target **B** is a Ridge interpolation of A across all 234 grids (training-fit R² = 0.99). Target **C** blends B with a district-level prior of 6.0 t/ha. Target **D** is the ChinaWheatYield30m satellite retrieval for 2021 [5] (22 grids at a ≥4-valid-pixel threshold; 5.82 ± 0.21 t/ha on the common extraction window), +10% above the statistical mean.

### 2.3 External data for generalisation and arbitration

Three public assets extend the diagnostic beyond Pinggu. (i) The full History period of the Xiao et al. panel [4], aggregated to the same lattice, yields **7,784 national grids** with matching environment features; its scenario periods (2030s, 2060s under SSP2-4.5 and SSP5-8.5) provide climate-transfer testbeds, and its six management-reference columns (N rates, irrigation, and their ratios for both rotation crops) provide the management-information arm. (ii) The ChinaWheatYield30m product for 2016, 2020, and 2021 (1-km national rasters) provides the inter-annual arm. (iii) The National Bureau of Statistics 2021 summer-grain announcement provides provincial survey yields (real-cut, real-measure methodology) as an **independent arbiter**. All source files, checksums, and acquisition paths are released in the data manifest; large rasters ship via the repository's data release.

---

## 3. Methods

### 3.1 Factorial design

All experiments follow one controlled design: {feature set} × {validation scheme} × {model} × {target}, with feature sets spanning environment-only (E, 24–71 columns depending on line), management-only (M, six columns), and their union (E+M). Every cell reports pooled out-of-fold R² over 3–5 random seeds (mean ± SD, minimum reported), with fold-mean statistics as a secondary, explicitly labelled convention. Hyperparameters are fixed at the XGBoost configuration transferred from an independent 250-m pipeline (428 trees, depth 5, learning rate 0.168; provenance in e6_tuned_params.json); a nested re-tuning sensitivity check on the diagnostic data reproduces all qualitative conclusions (random 0.401 / checker 0.373 / lat-block 0.196).

### 3.2 Validation-design family and dose–response

Five schemes span the interpolation–extrapolation spectrum: random 5-fold; checkerboard blocking at 0.5×–4× the variogram range (dose–response); latitude quartile blocks; leave-one-block-out (K-means, k=8); and environment-space K-means blocks. For each scheme we compute the **optimism gap** (random minus scheme pooled R², positive = scheme more honest) and the **mean nearest-neighbour distance between blocks**–the mechanism probe that distinguishes genuine blocking from silent degeneration into random splits. Variogram ranges are estimated from the *target field itself* (Pinggu range 4.62 km; national History-yield range ≈462 km), a distinction that proves decisive.

### 3.3 Representation diagnostics and power analysis

Principal-component screening quantifies the effective dimensionality of the "environmental fingerprint" and its elevation-axis content. Detection power is measured by planting synthetic signals of known population R² (0.05–0.5) into the real 43-grid feature space, using two signal shapes: adversarial random directions and the **regionally learned response** (the national E-model's prediction on the Pinggu grids, correlation ~0.7 with April temperature and precipitation–physically well-formed). Detection is declared at out-of-fold R² > 0.10. A weakly regularised comparator (100 trees, depth 2) tests the model-complexity-matching principle.

### 3.4 Uncertainty quantification

Quantile random forests (300 trees) supply 10/50/90 percentiles; split-conformal calibration (70/70/94 split, q̂ = 2.08) recalibrates the 90% intervals. Reporting follows the decision-suitability matrix: interval width is compared against the precision each use case (insurance pricing, trend screening, warning zonation, carbon MRV) actually requires.

### 3.5 Inter-target agreement and statistical arbitration

Wherever two independently constructed targets overlap, we report grid-level Pearson and Spearman correlations; where an official statistical anchor exists, we assign lattice cells to provinces by nearest-provincial-centroid Voronoi and compare provincial means by Spearman rank correlation against the survey. The alarm pattern motivating protocol step (vii) is **low inter-target correlation combined with high per-target environmental R²**.

### 3.6 Reproducibility

All folds (five released fold-assignment files), seeds, parameters, and requirements are frozen in the repository; every number in this manuscript is regenerated by one of the scripted ledgers (w14–w26 series), and Section 10 lists the one-command reproduction chain.

---

## 4. Results I: The Target-Construction Trap

Against target A–the process-model baseline whose provenance is documented–the environmental models show no skill under any scheme (all pooled R² ≤ 0.20; random CV −0.05 ± 0.02 with tuned trees). Against target B, the Ridge interpolation of A, the same models report pooled R² = 0.98. The gap is the trap, and it is bounded: leave-one-out inverse-distance interpolation of B's own 43 source values attains only R² = 0.20–0.27, so any environmental model "predicting" B at 0.98 must be reproducing the interpolation rule itself. Two magnitude checks triangulate semantics: A sits +38% above the Beijing statistical mean (potential-yield semantics), while the satellite target D sits +10% above it (actual-yield semantics); the ~28-point gap is itself a management-gap signature (Section 7). The blended target C inherits smoothness rather than signal–its correlation with D on common grids is −0.01, the district prior having flattened what spatial structure remained.

## 5. Results II: The Validation-Design Trap

The five-scheme spectrum on target C reads: random 0.400 ± 0.015; checkerboard (1× range) 0.367; latitude blocks 0.113 pooled (fold-level −0.205–the two statistics disagree exactly as small-block variance theory predicts); LOBO 0.124; environment-space blocks −0.136. The dose–response experiment explains why the checkerboard family never joins this ranking: from 0.5× to 4× the variogram range, the optimism gap decays from +0.113 to −0.006 **while the mean nearest-neighbour distance between blocks never leaves 2.3–2.4 km**–blocks large enough to span the domain silently degenerate into random splits. In a domain only ~5.6 ranges wide, checkerboard blocking is structurally a placebo; the honest schemes are those that cut the dominant gradient (latitude +0.288, LOBO +0.276, environment-space +0.54).

The national lattice reproduces the mechanism with the sign structure intact and adds a scale correction: with the range estimated from the national yield field itself (≈462 km), the North China Plain spans only ~2 of its own ranges, and checkerboard gaps never exceed +0.07 at any sub-range block size while latitude blocking costs +0.32–gradient cutting, not block size, generates informative gaps in both domains, and block sizes must be expressed in **target-field** range units (protocol step ii).

## 6. Results III: Representation and Detectability

### 6.1 One axis wearing twenty-four hats

The "24-variable environmental fingerprint" is, to first order, a single elevation axis: PC1 explains 66.3% of variance and correlates with elevation at r = −0.94; the top SHAP variables (bio9, December mean temperature, bio11) are winter-temperature expressions of the same mountain–plain gradient, physically coherent with overwintering stress but rank-unstable within the collinear block. PC1–PC5 jointly explain only R² = 0.24 of target A–collinearity cannot rescue the null. Winter-wheat-appropriate thermal features (Tbase = 0 °C seasonal GDD, vernalisation days, deep-freeze days, grain-fill heat) add +0.006 on target C and exactly zero on A (bit-identical out-of-fold predictions; the four features receive zero split gain)–correcting the physiology of the covariates does not change the county-scale verdict.

### 6.2 The null is a detectability outcome, not a verdict on environmental control

The identical framework, features, and hyperparameters recover R² = 0.690 ± 0.006 on the 7,784-grid national gradient (0.689 on the 25-column subset shared with Pinggu; 0.450 at the 1-km fine level, separating genuine signal from aggregation smoothing). Two experiments then locate the county-scale boundary. Sliding 60 Pinggu-sized windows across the national dataset yields a median R² of 0.163 (IQR 0.027–0.272; 60% of windows below 0.2): near-nulls are the norm at this domain size, not a Pinggu anomaly. And the power analysis plants regionally learned signals (true R²pop = 0.05–0.5) into the real 43-grid feature space: tuned tree ensembles detect nothing (pooled detection probability 0.00 even at R²pop = 0.5, predictions collapsing toward a constant, SD 0.018 against a target SD of 0.224), while a weakly regularised comparator senses the signal fold-wise (40% detection at R²pop = 0.3) but loses it after pooling (3%). The county null is therefore the honest read of a sampling geometry whose detection ceiling lies below the true signal–model complexity must match sample size, and no re-tuning conjures skill from n = 43.

## 7. Results IV: Management Information and Climate Transfer

### 7.1 Management dominates where it can be seen

On the national lattice, six management-reference columns out-predict twenty-five environmental ones: M-only R² = 0.913, E-only 0.690, E+M 0.948 (random CV; checkerboard 0.897/0.625/0.932). SHAP attributes 0.95 of the M-model importance to the rotation-maize N rate–coherent with an annual-rotation target. Because the management surface and the panel yields share a process-model lineage, this number is a within-family consistency bound rather than independent field evidence (the same-source caveat that governs all Xiao-panel results); the National Bureau of Statistics arbitration in Section 8 is what separates the two data families. At Pinggu, tuned trees collapse all feature sets to constants (Section 6.2), but the weakly regularised comparator recovers management signal on the 43-grid target A (0.218 ± 0.054 across three seeds, all positive) while environment stays null (−0.17) and E+M is diluted by noise columns (0.05)–management information is detectable at county scale where environment is not, with the strict semantics caveat that target A itself is a process-model product.

### 7.2 Climate transfer: pattern retained, level lost

A model trained on the History period and applied unchanged to the scenario periods loses pooled R² from 0.96 (in-sample era) through 0.40 (2030s) to −0.95 (2060s), but spatial-pattern skill–Pearson correlation with the period's yield field–declines only from 0.961 through 0.888 to 0.861, with deeper losses under SSP5-8.5 (0.089) than SSP2-4.5. The negative pooled values are mean-shift artifacts: the static-covariate model preserves the *relative* map while remaining blind to the −1.4 t/ha climate-driven level change. Mapping transfers; impact assessment does not.

## 8. Results V: Co-Construction Bias and Statistical Arbitration

The two national products disagree almost everywhere: grid-level correlation between the satellite retrieval and the optimised panel on 5,652 common cells is **r = 0.017**. Yet the environmental model "explains" both at R² = 0.651 and 0.658–high skill on mutually uncorrelated targets cannot reflect a shared yield process; it reflects each product's *construction rule* being environment-dependent. We call this co-construction bias. Three further facts close the case. The bias is year-robust (E→RS = 0.861/0.709/0.649 for 2016/2020/2021). Inter-annual pattern agreement of the satellite product itself is intermittent–2016 vs 2021 grids correlate at 0.881 and 2017 joins the family (0.44 with both), but 2020 breaks against all three (−0.61 to −0.07, its spatial SD halved), so cross-year audits must report pairwise. And the **official statistics arbitrate**: provincial survey ranks match the satellite product at Spearman ρ = 0.893 (p = 0.007; absolute errors < 0.25 t/ha) but not the optimised panel (ρ = −0.036). One product carries real signal, the other does not, and the environmental model cannot tell them apart–directional proof that at least the panel share of the environmental R² is construction, not yield.

## 9. Uncertainty and Decision Value

Raw QRF 90% intervals under-cover (PICP = 0.705); split-conformal calibration lifts coverage to 0.862 at the price of width (mean prediction interval width 0.62 → 0.79 t/ha ≈ 2.6 × the target SD). The decision-suitability matrix converts these numbers into usable statements: at current precision the intervals support trend screening and warning zonation, marginally support relative comparison, and **cannot support insurance-grade pricing or carbon-MRV accounting**, both of which require widths below the process noise they are meant to price. A number's value is defined by the decision it can support–an uncertainty statement without its decision context is incomplete reporting.

## 10. Discussion

**The three traps share one mechanism.** Target construction, validation design, and co-construction bias are not three failure modes but one: apparent skill accrues to whatever process generated the target's spatial structure–interpolation rules, panel optimisation logic, satellite-retrieval calibration–and honest models inherit that structure unless the evaluation design separates them. Our controlled factorials make each inheritance visible and, importantly, **measurable in advance**: the circular upper bound from a leave-one-out interpolation, the placebo checkerboard from a nearest-neighbour distance, the co-construction alarm from an inter-target correlation.

**Detectability reframes "environment does not explain yield".** The same framework that yields honest nulls at Pinggu recovers R² = 0.69 across the regional gradient; the difference is geometry–environmental variance, domain size in target-field range units, and sample size–not doctrine. This is the quantitative reconciliation between the agricultural-systems consensus (environment shapes yields) and the county-scale null: the question is never whether environment matters but whether a given sampling geometry can see it. The management result sharpens the picture: where information exists (six management columns) and the estimator is matched to n (weak regularisation), county-scale detection succeeds.

**Limitations.** Grid-scale ground truth remains absent for the study area; our strongest arbitrated comparison lives at provincial resolution. The management arm shares lineage with its panel target (within-family evidence), and the climate-transfer arm tests transfer within one model family's scenario space. Inter-annual conclusions rest on four years at Pinggu (2016/2017/2020/2021: the three non-2020 years correlate at 0.44–0.88 while 2020 correlates negatively with all three, r = −0.61 to −0.07; county-scale environment-CV negative in every year, −0.14 to −0.28), with 2018–2019 acquisition in progress. QRF calibration is demonstration-grade (n_cal = 70, ±3–4 pp sampling wobble). None of these caveats touches the protocol, whose steps consume only pre-modelling information. A final boundary is geographic and crop-system scope: every empirical result here comes from Chinese winter-wheat systems, and the protocol itself, while domain-agnostic by construction, has yet to be exercised on other crops and continents; we encourage such transfer tests and release all tooling to enable them.

## 11. Conclusions

For model-derived yield targets, apparent skill is manufactured by target construction, validation design, and representation limits–not by environmental information, which our own framework confirms to be large (R² = 0.69) wherever gradients are wide enough to detect. We release a six-step pre-mapping audit protocol: (i) declare target provenance and training fit; (ii) estimate the variogram range *from the target field* and report domain size in its own range units–checkerboard families are structurally inert near or below one range and across small domains; (iii) screen PC1/elevation before celebrating multi-variable importance; (iv) report interval width against the decision it must support; (v) benchmark the sampling-geometry signal ceiling (domain × environmental variance × n × model complexity) before interpreting a null; and (vi) audit inter-target agreement, with official statistics as arbiter where they exist. Every step costs minutes, requires no new data, and would have caught every trap documented here before publication.

---

## Figure Captions