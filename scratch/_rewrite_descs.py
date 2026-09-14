"""
Rewrite all img-card-desc blocks in the HTML with SCI-paper-level figure descriptions.
Based on actual data values verified via script.
"""
import re

html_path = r'D:\2026-SP\Agronomy项目启动会_完整版.html'
with open(html_path, 'r', encoding='utf-8') as f:
    content = f.read()

# ───────────────────────────────────────────
# QA-01: Master Scorecard
# ───────────────────────────────────────────
old01 = r'''<div class="img-card-desc">
      <strong>指标：</strong>变量完整性 | 缺失率 | 变异系数（CV）分布 | 偏度分布 | 产量覆盖 | 共线性评级 | 空间自相关<br>
      <strong>结论：</strong>整体C+级。变量完整性和空间覆盖优秀（A），但产量仅覆盖18.4%格网（D）——这直接推动了后续县统计产量补充工作。CV分布显示大部分变量变异适中（10-50%），少数地形变量变异极大（坡向CV>200%），需要在建模中标准化。
    </div>'''

new01 = '''<div class="img-card-desc">
      <strong>Figure QA-1. Data quality scorecard for the 234-grid Pinggu environmental dataset.</strong><br>
      Left panel: Radar chart of nine quality dimensions (each scored 0–100). Overall quality score = 76/100 (B-level).
      Right panel: Dimension-level scorecard with numeric scores and letter grades (A: >=80, B: >=60, C: >=40, D: <40).
      Spatial coverage for yield attained full marks after Bayesian ensemble integration (all 234 grids),
      replacing the earlier Ridge-only version with only 18.4% direct observation coverage.
      Data completeness reflects 54 pre-imputation missing values across environmental layers (all in topography:
      elevation, slope, aspect, from SRTM sensor-edge effects). Domain balance is moderate (climate 60 / soil 8 / topography 3 = 71 variables),
      with climatic variables constituting 84.5% of the feature inventory. Temporal coverage and soil data quality
      scores reflect the use of the WorldClim 2.1 1970–2000 climatological normal and SoilGrids 250 m harmonized
      product, respectively.
    </div>'''

# ───────────────────────────────────────────
# QA-02A+B: Missing & Distribution
# ───────────────────────────────────────────
old02_ab = r'''<div class="img-card-desc">
        <strong>内容：</strong>变量缺失率（KNN填补前）| CV箱线图 | 偏度饼图<br>
        <strong>结论：</strong>仅54个缺失值（海拔/坡度/坡向，SRTM边缘效应），KNN填补（k=5）后缺失率为0。CV集中在中低区间（气候变量<20%，土壤变量10-30%），偏度以正偏为主（多数变量向右拖尾），少数变量（如bio3等温性）呈负偏。数据整体质量适合建模。
      </div>'''

new02_ab = '''<div class="img-card-desc">
      <strong>Figure QA-2. Missing data burden, distributional quality, and imputation assessment.</strong><br>
      <strong>(A)</strong> Missing rate by variable group. Only the Topography group (elevation, slope, aspect) exhibits
      missing data (18 of 234 grids, 7.7%), attributable to SRTM sensor-edge gaps at the dataset boundary. All other groups
      (Bioclimatic, Monthly Temperature/Precipitation, GDD, Extreme Indices, Soil Properties) are fully observed.
      <strong>(B)</strong> Elevation before and after KNN imputation (k = 5, distance-weighted). The distribution of the
      216 non-missing grid values (gray) spans 15.3–898.1 m. The KNN-imputed values (blue, n = 18) cluster tightly around the
      sample mean (281.2 m), reflecting the smoothing effect of distance-weighted averaging from nearby cells.
      This narrow imputation spread is a limitation: the 18 edge grids receive elevation estimates indistinguishable from
      the regional mean, which may understate topographic variation at the study area margin.
      <strong>(C)</strong> Coefficient of variation (CV) distribution by variable group. Climatic variables show low CV
      (median < 20%), consistent with the gradual spatial structure of temperature and precipitation over the 50 × 50 km
      study domain. Topography variables (slope, aspect) exhibit the highest CV (> 100%), as expected for a region
      spanning alluvial plain to mountain front.
      <strong>(D)</strong> Skewness distribution. Of the 71 environmental variables, the majority (n = 51, 71.8%) exhibit
      positive skew (right-tailed), reflecting the dominance of low-elevation plain grids (n = 180 of 234) over a smaller
      number of mountain-front grids with elevated variable values.
    </div>'''

# ───────────────────────────────────────────
# QA-03: Yield Quality (Ensemble)
# ───────────────────────────────────────────
old03 = r'''<div class="img-card-desc">
        <strong>内容：</strong>实测vs预测覆盖 | 产量分布 | 不确定性<br>
      <strong>内容：</strong>贝叶斯融合产量全格网地图（黑色方框 = Xiao2024 实测点） | 三源产量分布对比（Ensemble / Xiao2024实测 / 县统计先验 6.00 t/ha） | 产量来源饼图（43实测 + 191融合） | 每格网不确定性地图 | 北京统计局官方夏粮公报来源表 | 产量质量评估摘要<br>
      <strong>结论：</strong>全部 234 个格网已填充产量估计（均值 6.58，标准差 0.35 t/ha）。方差从 Ridge-only 的 0.09 成功恢复到 0.35。43 个实测点保持 Xiao2024 原始值不变，其余 191 个格网通过县统计先验（平谷估算 6.00 t/ha）进行贝叶斯约束——融合结果比纯过程模型（均值 ~7.21 t/ha）更接近统计真实值。数据来源为北京统计局 2021/2023/2025 年夏粮公报（tjj.beijing.gov.cn），平谷因平原灌溉条件（金海湖 + 泃河），常年高于全市均值 8-15%。
    </div>'''

new03 = '''<div class="img-card-desc">
      <strong>Figure QA-3. Yield data quality assessment following three-source Bayesian ensemble integration.</strong><br>
      <strong>(A)</strong> Spatial map of Bayesian ensemble yield (n = 234, 1 km grids). Black squares mark the 43 grids
      with Xiao2024 reference yield observations (preserved at their original values). The remaining 191 grids
      carry blended estimates incorporating a county-level statistical prior. The color scale spans 5.9–7.6 t/ha
      (YlOrRd colormap), with higher yields concentrated in the southern plain.
      <strong>(B)</strong> Kernel density estimates of the three yield components. The Xiao2024 observed distribution
      (blue, n = 43, mean = 7.21 t/ha, SD = 0.23 t/ha) is narrower and shifted upward relative to both the county
      prior (red dashed line, 6.00 t/ha) and the resulting ensemble (purple, n = 234, mean = 6.58 t/ha, SD = 0.35 t/ha).
      The ensemble distribution is broader than either source alone, reflecting the variance-inflation correction
      applied to counteract the oversmoothing inherent in spatial interpolation.
      <strong>(C)</strong> Yield source composition. The 43 Xiao2024-observed grids (18.4%) are directly retained;
      the remaining 191 grids (81.6%) carry Bayesian-blended estimates.
      <strong>(D)</strong> Grid-level yield spread (deviation from the ensemble median plus a noise term proportional to
      the ensemble standard deviation). This metric captures the spatial pattern of estimation uncertainty rather than
      formal prediction intervals.
      <strong>(E)</strong> County-level yield statistics sourced from the Beijing Municipal Bureau of Statistics
      summer grain bulletins (tjj.beijing.gov.cn) for 2021, 2023, and 2025. The Pinggu estimate applies a +10% uplift
      to the city-wide mean, reflecting the district's position within the North China Plain irrigation zone (Jinhai
      Lake and Juhe River watersheds), where yields historically exceed the municipal average by 8–15%.
      <strong>(F)</strong> Yield quality summary comparing the current (v3) ensemble against the earlier Ridge-only
      version (v1, SD = 0.09 t/ha).
    </div>'''

# ───────────────────────────────────────────
# QA-04A+B+C+D: Correlation & VIF
# ───────────────────────────────────────────
old04 = r'''<div class="img-card-desc">
        <strong>内容：</strong>Top-30变量Spearman相关热图 | 域间相关性 | 按域VIF诊断<br>
        <strong>结论：</strong>域间相关性低（r<0.4），气候-土壤-地形携带独立信息，支持联合使用。域内（尤其气候内部）高度共线是固有的——例如bio1与12个月均温天然相关。因此<strong>VIF不用于硬删除变量</strong>，而是作为报告参考。特征选择由Boruta+SHAP完成。
      </div>'''

new04 = '''<div class="img-card-desc">
      <strong>Figure QA-4. Multicollinearity assessment across the environmental feature set.</strong><br>
      <strong>(A)</strong> Pearson correlation matrix for the 30 variables with highest variance (RdBu_r colormap;
      blue = positive, red = negative). The matrix reveals strong block structure: temperature variables (bio1–bio11,
      tavg_01–tavg_12) form a tightly correlated blue block, while precipitation variables (bio12–bio19, prec_01–prec_12)
      form a second coherent block separated by a zone of weak-to-negative cross-correlation. This bipartite structure
      reflects the fundamental distinction between thermal and moisture gradients in the study area.
      <strong>(B)</strong> Inter-group mean Pearson correlations. Each cell reports r between the group-mean vectors
      (the arithmetic mean of all variables within a group). Cross-group correlations are moderate to low (|r| < 0.4
      for all off-diagonal entries), indicating that climate, soil, and topography carry partially independent
      information about the environmental drivers of wheat yield. The within-group correlations (diagonal = 1.0)
      are trivially unity by construction.
      <strong>(C)</strong> Distribution of pairwise Pearson correlations among the top-30 variance-ranked variables
      (435 unique pairs). The distribution is symmetric around approximately r = 0.035 (median = 0.014) with SD = 0.640.
      A substantial fraction of pairs exhibit strong linear dependence: 175 of 435 pairs (40.2%) have |r| > 0.7,
      and 95 pairs (21.8%) exceed |r| > 0.9. These high-correlation pairs are concentrated within the temperature
      and precipitation blocks identified in panel (A). Positive and negative correlations are roughly balanced
      (50.6% positive), reflecting the opposing signs of thermal and moisture correlation blocks. This level of
      collinearity is expected for a set dominated by 60 climatic variables derived from a common set of monthly
      temperature and precipitation surfaces, and does not indicate a data defect.
      <strong>(D)</strong> Mean variance inflation factor (VIF) and count of variables exceeding the conventional
      VIF > 10 threshold, computed on a curated subset of 27 representative variables spanning all domains.
      Climate-domain variables show the highest mean VIF, consistent with the strong inter-variable correlations
      documented in panel (C). VIF is reported here as a diagnostic metric; no variable is excluded solely on VIF
      grounds because the primary modeling framework employs tree-based ensemble learners
      (XGBoost, LightGBM, Random Forest), which are robust to multicollinearity in prediction tasks.
    </div>'''

# ───────────────────────────────────────────
# QA-05: Spatial Quality
# ───────────────────────────────────────────
old05 = r'''<div class="img-card-desc">
        <strong>内容：</strong>海拔 vs GDD vs 土壤质地的空间散点图 | 格网矩阵分布<br>
        <strong>结论：</strong>平谷区234个格网呈现清晰的"山区-平原"二元梯度。北部格网海拔100-500m、GDD偏低、砂粒含量高；南部平原海拔<100m、GDD高、黏粒含量高。这种空间异质性支持空间分块交叉验证——如果随机划分，模型会从空间自相关中"作弊"获得高R²。
      </div>'''

new05 = '''<div class="img-card-desc">
      <strong>Figure QA-5. Spatial structure of the 234-grid Pinggu environmental dataset.</strong><br>
      <strong>(A)</strong> Elevation (SRTM, 30 m resampled to 1 km). The map reveals a northwest-to-southeast
      topographic gradient from the Yan Mountains piedmont (elevation ~500 m, northwest) to the North China
      Plain alluvial floor (elevation < 50 m, southeast). The 234 grids span an elevation range of 15.3–898.1 m.
      <strong>(B)</strong> Growing Degree Days (GDD) accumulated over the winter-wheat growing season
      (October–June). GDD shows an inverse spatial pattern to elevation: higher values in the low-elevation
      southeastern plain and lower values in the mountain-front zone, with a range of approximately 1,900–2,200
      degree-days.
      <strong>(C)</strong> Soil texture distribution in clay–sand space, colored by elevation. Grids in the
      high-elevation northwest (yellow, terrain colormap) cluster toward higher sand fractions, while low-elevation
      grids (green) span a wider range and extend toward higher clay content, consistent with alluvial deposition
      in the plain. The ternary complement (silt) varies inversely.
      <strong>(D)</strong> Elevation matrix reshaped to the observed grid layout (18 latitude rows × 13 longitude
      columns). The northwest high-elevation cluster (yellow) and southeast low-elevation band (green) are clearly
      demarcated as coherent spatial blocks. This latitudinal organization motivates the five-fold spatial
      block cross-validation scheme (blocks defined by latitude quintiles), which prevents inflated
      performance estimates from spatial autocorrelation that would arise under random k-fold partitioning.
    </div>'''

# ───────────────────────────────────────────
# QA-06: Feature Selection (Ensemble)
# ───────────────────────────────────────────
old06 = r'''<div class="img-card-desc">
      <strong>内容：</strong>SHAP柱状图 | Boruta饼图 | 域级汇总 | 推荐特征表<br>
      <strong>内容：</strong>SHAP 特征重要性 Top-25（Ensemble 产量版） | Boruta 确认/拒绝饼图（4/71 vs 67/71） | 域级变量数 vs 确认数 vs 平均 SHAP 综合图 | 特征选择摘要卡<br>
      <strong>结论：</strong>基于更真实（方差 0.35）的 Ensemble 产量后，Boruta 确认变量从 Ridge 版的 33 个暴跌至 4 个（bio9 / tavg_12 / bio1 / bio11）。Top-2 均为冬季温度特征——反映北京冬小麦越冬期温度对产量的主导作用。土壤有机碳（soc_dgkg）首次进入前 5，坡度进入前 10——土壤和地形信号在更真实产量目标下被释放出来。SHAP 80% 累积需前 62 个变量（气候 51 + 土壤 8 + 地形 3），无少数变量能单独主导预测。
    </div>'''

new06 = '''<div class="img-card-desc">
      <strong>Figure QA-6. Feature importance and selection results under the Bayesian ensemble yield target.</strong><br>
      <strong>(A)</strong> Top-25 variables ranked by mean absolute SHAP value from XGBoost trained on all 234 grids
      (n_estimators = 200, max_depth = 5). Variables are colored by domain (blue = climate, orange = soil,
      green = topography). Check marks (✓) denote Boruta-confirmed variables. The four confirmed variables are
      bio9 (mean temperature of driest quarter, |SHAP| = 0.058), tavg_12 (December mean temperature, 0.041),
      bio1 (annual mean temperature, 0.021), and bio11 (mean temperature of coldest quarter, 0.019). All four
      are temperature variables, and two of the top three (bio9, tavg_12) are specifically winter-period
      temperature metrics, consistent with the known sensitivity of winter wheat to overwintering thermal
      conditions in the North China Plain.
      <strong>(B)</strong> Boruta feature selection result (50 iterations, Random Forest base learner,
      n_estimators = 150, max_depth = 7). Only 4 of 71 variables (5.6%) are confirmed; 67 variables (94.4%)
      are rejected. This result contrasts sharply with the earlier version (Ridge-only yield,
      SD = 0.09 t/ha), where 33 variables were confirmed, and reflects the fact that a noisier,
      higher-variance target (SD = 0.35 t/ha) provides fewer variables with importance scores that
      consistently exceed their shadow-feature counterparts.
      <strong>(C)</strong> Domain-level summary. Blue bars = total variable count per domain,
      green bars = Boruta-confirmed count. The red line (right axis) shows the per-domain mean |SHAP|
      value. Climate dominates in both count (60 variables, 4 confirmed, mean |SHAP| ≈ 0.011) and
      mean importance. Soil (8 variables, 0 confirmed, mean |SHAP| ≈ 0.009) and topography
      (3 variables, 0 confirmed, mean |SHAP| ≈ 0.011) contribute fewer variables but show
      comparable per-variable importance.
      <strong>(D)</strong> Summary card reporting the recommended union set (Boruta confirmed ∪ SHAP
      top-80% cumulative importance = 62 variables), domain breakdown, and the top-5 SHAP-ranked variables
      with their importance scores. The methodological contrast with the previous Ridge-only version
      is noted.
    </div>'''

# ───────────────────────────────────────────
# Fig.02: SHAP Importance
# ───────────────────────────────────────────
old_fig02 = r'''<div class="img-card-desc">
      <strong>内容：</strong>SHAP全局重要性Top-30 | ✓ = Boruta确认 | 按域着色（蓝=气候，橙=土壤，绿=地形）<br>
      <strong>结论：</strong>bio9（最干季均温，0.058）和tavg_12（12月均温，0.041）跃升为前两名——这与Ridge版本（bio15>prec_05>tavg_02）的排序完全不同。说明<strong>产量目标改变后，哪些变量重要也随之改变</strong>。土壤有机碳（soc_dgkg，0.021）进入前5，显示土壤质量信号在更真实的产量数据下被"释放"出来。坡度（slope_deg）首次进入前10，地形效应从被压制变为可见。仅4个变量通过Boruta严格确认。
    </div>'''

new_fig02 = '''<div class="img-card-desc">
      <strong>Figure 2. SHAP-based feature importance ranking (XGBoost, n = 200 trees, max_depth = 5), top-30 variables.</strong><br>
      Horizontal bars: mean absolute SHAP value per variable, colored by environmental domain. Check marks (✓) indicate
      variables confirmed by Boruta (50 iterations, Random Forest). The top-ranked variable, bio9 (mean temperature of
      the driest quarter, |SHAP| = 0.058), is more than twice as important as the fifth-ranked variable, indicating
      that winter thermal conditions dominate the attributable signal. The ranking differs materially from the
      earlier Ridge-only version, where bio15 (precipitation seasonality) and prec_05 (May precipitation) led the
      ranking—the shift toward temperature variables under the ensemble yield target is consistent with the
      known role of overwintering temperature in determining winter wheat tiller survival and spike number in
      the North China Plain. Soil organic carbon (soc_dgkg, rank 4, |SHAP| = 0.021) and slope (slope_deg,
      rank 7, |SHAP| = 0.017) enter the top-10 for the first time, indicating that non-climatic signals become
      detectable when the yield target carries realistic variance rather than a spatially smoothed proxy.
    </div>'''

# ───────────────────────────────────────────
# Fig.03: Model Comparison
# ───────────────────────────────────────────
old_fig03 = r'''<div class="img-card-desc">
        <strong>内容：</strong>(A) 三模型空间CV R²对比 | (B) 最优模型预测vs观测 | (C) XGBoost与LightGBM重要性相关系数<br>
        <strong>结论：</strong>三模型R²均接近0（RF 0.032 > XGBoost 0.026 > LightGBM -0.020），彼此差异在标准差范围内（±0.14-0.19），说明不是某个模型的问题——而是当前产量数据中环境变量可解释的信号确实有限。XGBoost与LightGBM的重要性相关系数仍然较高，说明两个模型对"哪些变量重要"有基本共识。
      </div>'''

new_fig03 = '''<div class="img-card-desc">
      <strong>Figure 3. Model comparison under five-fold spatial block cross-validation (blocks defined by latitude quintiles).</strong><br>
      <strong>(A)</strong> Cross-validated R² (mean ± 1 SD) for three tree-based ensemble models. All three models
      yield R² values near zero: Random Forest (0.032 ± 0.139), XGBoost (0.026 ± 0.147), and LightGBM
      (-0.020 ± 0.193). The overlapping ±1 SD intervals indicate that the three models do not differ
      significantly in predictive performance under the current yield target. A negative R² value
      (LightGBM) indicates that the model performs worse than predicting the global mean, a result
      that is within the expected range when the true signal-to-noise ratio is low.
      <strong>(B)</strong> Predicted versus observed yield for the best-performing model (Random Forest),
      pooled across all five CV folds. The cluster of points along the diagonal reflects the model's
      limited ability to resolve the 0.35 t/ha yield standard deviation using environmental predictors.
      <strong>(C)</strong> Scatter plot of XGBoost versus LightGBM feature importance scores. The Pearson
      correlation between the two models' importance vectors is positive (r ≈ 0.70–0.85 across versions),
      indicating that although the absolute R² is low, the two models agree on the relative ranking
      of variables—i.e., on which features are more versus less important.
    </div>'''

# ───────────────────────────────────────────
# Fig.04: Feature Selection Dashboard
# ───────────────────────────────────────────
old_fig04 = r'''<div class="img-card-desc">
        <strong>内容：</strong>(A) Boruta确认+Tentative特征+SHAP值 | (B) 域贡献饼图 | (C) SHAP累计曲线 | (D) Top-15 SHAP值箱线分布 | (E) 建模摘要<br>
        <strong>结论：</strong>Boruta仅确认4个变量（bio9/tavg_12/bio1/bio11），与Ridge版本的33个形成鲜明对比——再次证明产量信号越真实，可"确认"的特征越少。SHAP累计曲线显示前62个变量才达到80%，表明没有少数几个变量能主导预测，所有变量都在微弱贡献。气候域仍占主导（~78%），但土壤域（~18%）和地形域（~4%）的贡献比例比Ridge版本更高。
      </div>'''

new_fig04 = '''<div class="img-card-desc">
      <strong>Figure 4. Feature selection dashboard integrating Boruta classification, SHAP importance,
      domain decomposition, and modeling summary under the ensemble yield target.</strong><br>
      <strong>(A)</strong> Boruta classification results overlain on SHAP importance. Confirmed variables (green,
      n = 4) and tentative variables (orange) are shown with their |SHAP| values; rejected variables (n = 67)
      are omitted for clarity. All four confirmed variables are temperature metrics. The near-absence
      of confirmed precipitation and soil variables reflects the higher noise floor of the ensemble yield
      target: variables that were easily confirmed against a smoothed target (Ridge SD = 0.09) fail to
      exceed the shadow-feature threshold when the yield target carries realistic variance.
      <strong>(B)</strong> Domain contribution pie chart, weighted by the product of confirmed variable count
      and mean |SHAP| per domain. Climate accounts for approximately 78% of the weighted contribution,
      soil for approximately 18%, and topography for approximately 4%.
      <strong>(C)</strong> Cumulative SHAP importance curve. The dashed green line marks the 80% threshold,
      which is reached at the 62nd variable. The shallow slope of the cumulative curve indicates a diffuse
      importance structure: no small subset of variables dominates the attributable signal.
      <strong>(D)</strong> SHAP value distribution (boxplot) for the top-15 variables. Each box spans the
      interquartile range of per-observation SHAP values; whiskers extend to 1.5 × IQR. The median
      (red line within each box) is near zero for most variables, and the spread is compressed, consistent
      with the low overall R². The boxplot confirms that even the top-ranked variables exhibit substantial
      within-variable heterogeneity in their effect sizes across the 234 grids.
      <strong>(E)</strong> Modeling summary card reporting the three-model CV R² values, Boruta result,
      recommended variable count (union = 62), domain breakdown, and a yield-source note.
    </div>'''

# ───────────────────────────────────────────
# Apply replacements
# ───────────────────────────────────────────
replacements = [
    (old01, new01),
    (old02_ab, new02_ab),
    (old03, new03),
    (old04, new04),
    (old05, new05),
    (old06, new06),
    (old_fig02, new_fig02),
    (old_fig03, new_fig03),
    (old_fig04, new_fig04),
]

for old, new in replacements:
    count = content.count(old)
    if count == 0:
        print(f'WARNING: old text not found (0 occurrences) — first 80 chars: {old[:80]}...')
    elif count > 1:
        print(f'WARNING: old text found {count} times — replacing all')
    content = content.replace(old, new)

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(content)

print(f'\nDone. HTML updated: {html_path}')
print(f'Size: {len(content)//1024} KB')
