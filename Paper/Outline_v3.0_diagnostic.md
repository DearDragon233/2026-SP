# 2026-SP 论文大纲 v3.0（诊断型重构版）
## 环境指纹能否解释区域冬小麦产量变异？——基于平谷区 234 网格的多源数据系统性检验
## Can environmental fingerprints explain regional winter wheat yield variability? A systematic assessment with multi-source data in Pinggu District, Beijing

**目标期刊**: Agronomy (MDPI, JCR Q1-Q2) 或 Field Crops Research (Elsevier, Q1)
**定位**: 诊断型方法学论文（非预测型）
**团队**: 彭宇程（第一作者/数据/管线/论文）+ 3 人（分工待定）
**当前状态**: 数据分析与实验已完成，大纲 v3.0 重构完成，待写作启动

---

## 摘要要点（中英双语，300词）

**Background**: Spatial yield prediction using environmental covariates is widely adopted, yet the influence of spatial autocorrelation on reported accuracy and the quality of yield targets themselves are rarely scrutinized.

**Methods**: We assembled a 234-grid (3.5 km) environmental fingerprint matrix (24 modeling variables from WorldClim, SoilGrids, SRTM) and evaluated four yield target constructions: (A) observed farm-level yields (n=43), (B) spatially interpolated yields (n=234), (C) Bayesian-blended yields (n=234), and (D) independently sourced remote-sensing-derived yields (ChinaWheatYield30m, n=22 with valid winter wheat pixels). Three models (XGBoost, LightGBM, RF) were evaluated under three CV schemes (random, latitude-block, 2D-checkerboard) with QRF uncertainty quantification.

**Results**: Random CV inflated R² by +0.036–0.088 relative to spatial CV. The observed-yield target yielded R² ≈ 0 across all models, while the spatially interpolated target reached R² = 0.98, revealing circular validation. The blended target yielded intermediate R² = 0.30–0.39, substantially attributable to target smoothness rather than genuine environmental signal. QRF 90% intervals achieved PICP = 0.705 (under-covered). An independent data source (ChinaWheatYield30m) confirmed minimal spatial predictive capacity.

**Conclusions**: Environmental fingerprints at 3.5 km resolution explain limited true yield variability in this smallholder-dominated landscape. Apparent model performance in spatial yield mapping is primarily driven by target construction and spatial autocorrelation, not environmental information. We recommend spatial CV as mandatory practice and target-source sensitivity analysis as standard reporting for regional yield modeling studies.

---

## 十章大纲

### 1. Introduction
- 1.1 空间产量建模的广泛应用与环境变量作为主要预测源的惯例
- 1.2 现有文献的两大盲区：(a) 目标变量来源对模型性能的影响被忽视；(b) 空间自相关导致的 CV 乐观偏差普遍存在但少有量化
- 1.3 中国小农经济背景下区域尺度产量建模的特殊挑战（田块破碎、统计口径不一、遥感反演与实测差距）
- 1.4 本研究的目的与贡献：系统性检验 + 方法学透明化框架
- **关键引用**: Ploton et al. 2020 Nat Commun; Roberts et al. 2017 Ecography; Zhao et al. 2023 ESSD; Lobell et al. 2015 Science

### 2. Study Area and Data
- 2.1 研究区：北京市平谷区（234 网格，3.5km 分辨率），华北平原北部山前平原，冬小麦-玉米轮作
- 2.2 环境变量矩阵（24 建模变量）：WorldClim bio1-bio19 + 月值温度/降水 + GDD + SoilGrids（clay/sand/silt/SOC/Bd/CEC/pH/N）+ SRTM（elevation/slope/aspect）
- 2.3 产量数据来源与属性表：
  - 来源 A：Xiao2024 实测 43 网格（单年，7.36±0.10 t/ha）
  - 来源 B：空间插值产量（Ridge 回归基于 A 训练，R²=0.99 对训练集）
  - 来源 C：贝叶斯融合（B + 区级统计先验 6.0 t/ha）
  - 来源 D：ChinaWheatYield30m 2021（Zhao et al. 2023 ESSD，22 网格有冬麦像元，5.78±0.20 t/ha）
- 2.4 数据审计：零缺失（24 建模变量）、坐标系统一（EPSG:4326）、单位标准化（t/ha）

### 3. Methods
- 3.1 特征工程与筛选：VIF → Boruta(50 iter, 5 shadow) → SHAP 重要性 → 联合推荐集
- 3.2 空间交叉验证方案：
  - 随机 5 折（对照组）
  - 纬度五分位块（处理南北梯度）
  - 经纬度 0.03° 棋盘 5 折（主口径）
  - 乐观偏差定义：随机 CV R² − 最优空间 CV R²
- 3.3 模型：XGBoost(200,depth=5,lr=0.05) / LightGBM(同参) / RF(200,depth=7)
- 3.4 QRF 不确定性量化：300 树，纬度空间 5 折，10/50/90 分位，PICP 与 MPW 诊断
- 3.5 目标来源敏感性实验设计：同特征 × 四目标 × 两 CV 方案的完整因子设计
- 3.6 独立数据源交叉验证：D 目标用不同数据源（ChinaWheatYield30m）重复全部实验
- 3.7 统计检验：Pearson r、R²(pooled/fold-mean)、RMSE、MAE、PICP

### 4. Results I: Environmental Fingerprint Audit
- 4.1 变量描述统计（Table 1：24 变量的 mean±std/min/max/CV%/VIF）
- 4.2 Boruta 筛选结果（fig04A：Confirmed/Tentative/Rejected 三色）
- 4.3 SHAP 重要性排序（fig02：Top-30 按领域着色，✓标记 Boruta Confirmed）
- 4.4 累计 SHAP 曲线（fig04C：Top-N 达 80%）

### 5. Results II: CV Scheme Comparison (G2)
- 5.1 三方案×三模型的 R²/RMSE 对比表（Table 2 = cv_scheme_comparison.csv）与 fig05
- 5.2 乐观偏差量化：Random − Spatial_best = +0.036(RF) 至 +0.088(XGB)
- 5.3 纬度块崩塌现象的分析：南北气候梯度作为强混杂因素
- 5.4 建议：棋盘块 CV 作为主口径的理由

### 6. Results III: Yield Target Source Sensitivity (G1)
- 6.1 四目标 × 三模型 × 两 CV 方案的性能矩阵（Table 3 = yield_source_sensitivity.csv + zenodo_cv_results.csv）与 fig07
- 6.2 目标 B 的循环论证：R²=0.98 的机制解析（模型复现 Ridge 插值表面）
- 6.3 目标 A 的真实技能：R²≈0（三模型一致），环境变量对 43 点真实变异无解释力
- 6.4 目标 C 的表观性能来源分解：平滑性贡献 vs 环境信号贡献
- 6.5 目标 D 独立源验证：checker CV R² 全负，随机 CV pooled=0.99 的原因
- 6.6 r(obs, pred)=0.510 的含义：空间预测系统性低估变异（pred std 0.056 vs obs std 0.224）

### 7. Results IV: QRF Uncertainty Quantification (G3)
- 7.1 PICP 与 MPW（fig06A：区间带+观测叠加）
- 7.2 校准散点（fig06B：covered vs outside）
- 7.3 区间宽度分布（fig06C：异方差模式，西南高值区更宽）
- 7.4 PICP 偏低的诊断与改进方向（Conformal 校准）

### 8. Discussion
- 8.1 为什么环境指纹在 3.5km 尺度不解释产量变异？
  - 管理因素（施肥/灌溉/品种）主导产量变异
  - 环境变量的空间分辨率与农艺过程的尺度不匹配
  - 小农经济的田块异质性超出网格平均的表征能力
- 8.2 空间产量建模文献中的乐观偏差普遍性：与 Ploton 2020 等全球证据对话
- 8.3 目标来源的批判性审视：空间插值目标≠独立观测
- 8.4 本研究对区域产量建模的实践建议：
  - 必须使用空间 CV（随机 CV 不可接受）
  - 必须报告产量目标的来源与不确定性
  - 建议多目标敏感性分析作为标准报告项
- 8.5 局限性：单年数据（G4）、43 实测点样本量、QRF 区间未校准、遥感反演系统性偏差

### 9. Conclusions
- 三个可检验命题的结果与含义
- 方法学贡献：透明化诊断框架
- 后续工作方向：多年份扩展、管理变量纳入、田块尺度研究

### 10. Data Availability & Code Availability
- 代码：GitHub ( DearDragon233/2026-SP )
- 数据：环境变量来源 URL、产量数据的获取方式与限制
- 复现：advance_validation.py 一键运行

---

## 图表清单（8 主图 + 2 补充图 + 4 表）

| 编号 | 内容 | 状态 |
|---|---|---|
| Fig 1 | 研究区地图 + 234 网格 + 产量来源分布 | 待制 |
| Fig 2 | SHAP 重要性 Top-30（已产出） | ✅ |
| Fig 3 | CV 方案对比（fig05，已产出） | ✅ |
| Fig 4 | 产量目标敏感性（fig07，已产出） | ✅ |
| Fig 5 | QRF 不确定性（fig06，已产出） | ✅ |
| Fig 6 | 特征筛选 Dashboard（fig04，已产出） | ✅ |
| Fig 7 | 独立源验证结果（待制：Zenodo CV 结果可视化） | 待制 |
| Table 1 | 24 变量描述统计 | 数据就绪 |
| Table 2 | CV 方案对比 | 数据就绪 |
| Table 3 | 四目标×三模型敏感性矩阵 | 数据就绪 |
| Table 4 | QRF 指标汇总 | 数据就绪 |

## 与旧版大纲的差异

| 旧版 v2.x | 新版 v3.0 |
|---|---|
| 定位：产量预测模型 | 定位：环境-产量关系的系统性诊断 |
| 主结果：混合目标 R²=0.31-0.39 | 主结果：三口径敏感性对比 + 乐观偏差量化 |
| CV：单一随机 CV | CV：三方案对比 + 乐观偏差作为贡献 |
| 不确定性：未涉及 | QRF + PICP/MPW 作为方法学贡献 |
| 独立验证：无 | 第四产量目标（Zenodo 独立源）交叉验证 |
| 目标变量来源：一笔带过 | 目标来源作为核心研究对象 |
