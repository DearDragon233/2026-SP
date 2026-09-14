# 2026-SP 论文大纲 v3.1(审稿响应修订版)
## 环境指纹能否解释中国小农区冬小麦产量变异?--基于北京平谷区多源农业数据的空间建模诊断
## Can Environmental Fingerprints Explain Winter Wheat Yield Variability in Smallholder Landscapes? A Spatial Modeling Diagnostic Based on Multi-Source Agricultural Data in Pinggu, Beijing

**目标期刊**: Agronomy (MDPI, JCR Q1-Q2) 或 Field Crops Research (Elsevier, Q1)
**定位**: 诊断型方法学论文 = **区域产量制图的最小基准协议(minimal benchmarking protocol)**
**团队**: 彭宇程(数据/管线/论文)+ 3 人(分工见 Roadmap v3.0)
**当前状态**: v3.0 大纲基础上,按导师评估与 Agronomy 模拟审稿意见完成 v3.1 修订(2026-09-14)

> **v3.1 修订说明**:本次修订将模拟审稿的 8 条主要意见全部落实(详见 指引落实对照表)。核心变化:
> 1贡献声明改用 benchmark 语言;2新增 3 种子重复实验(全部 CV 对比带 mean±SD);
> 3QRF 补 split-conformal 校准实验(PICP 0.705→0.862);4目标 B 循环验证升级为定量上界论证;
> 5棋盘块尺寸以 variogram 变程(4.6km)定量辩护;6管理因素假说明确标注并给出检验路径;
> 7文献锚定扩展至空间预测评估谱系(Meyer & Pebesma 2022、Raudaschl 2021、Roberts 2017、Ploton 2020);
> 8摘要明示单年单区局限;9复现包承诺(固定折划分文件+种子+环境清单)。

---

## 摘要要点(中英双语,320词)

**Background**: Spatial yield prediction using environmental covariates is widely adopted, yet the influence of spatial autocorrelation on reported accuracy and the quality of yield targets themselves are rarely scrutinized. We present a **minimal benchmarking protocol** for regional yield mapping that fixes validation splits, interrogates target provenance, and reports multi-dimensional metrics - mirroring standardization efforts in adjacent plant-science prediction domains.

**Methods**: We assembled a 234-grid (0.0417° ≈ 3.6 × 4.6 km, anisotropic) environmental fingerprint matrix (24 modeling variables from WorldClim, SoilGrids, SRTM) and evaluated four yield target constructions: (A) observed farm-level yields (n=43), (B) spatially interpolated yields (n=234), (C) Bayesian-blended yields (n=234), and (D) independently sourced remote-sensing-derived yields (ChinaWheatYield30m, n=22). Three models (XGBoost, LightGBM, RF) were evaluated under three CV schemes (random, latitude-block, 2D-checkerboard), each repeated over **three random seeds (mean ± SD)**, with QRF uncertainty quantification **plus split-conformal calibration**. Block size was justified against the empirical variogram range of yields and residuals (≈4.6 km; checkerboard block 3.3 km ≈ 0.72 × range).

**Results**: Random CV inflated pooled R2 by +0.020-0.061 relative to spatial CV (fold-mean口径 +0.036-0.088; 3-seed SD ≤ 0.025). The observed-yield target yielded R2 ≈ 0 across all models, while the spatially interpolated target reached R2 = 0.98 - a circular-validation upper bound, because pure spatial interpolation of the 43 underlying observations attains only R2 = 0.20-0.27 (leave-one-out IDW), so any target an environment model can "predict" at 0.98 must encode the environment model itself. The blended target yielded intermediate R2 = 0.30-0.39, substantially attributable to target smoothness. Raw QRF 90% intervals under-covered (PICP = 0.705); after split-conformal calibration PICP rose to 0.862 (MPW 0.62→0.79 t/ha). The independent data source confirmed minimal spatial predictive capacity. **All findings derive from a single season in one district; cross-year and cross-region generalization remain untested.**

**Conclusions**: Environmental fingerprints at 0.0417° (≈3.6 × 4.6 km) resolution explain limited true yield variability in this smallholder-dominated landscape. Apparent model performance is primarily driven by target construction and spatial autocorrelation, not environmental information. We release fixed fold assignments, seeds, and environment files, and recommend spatial CV with variogram-informed block sizes plus target-source sensitivity analysis as standard reporting.

---

## 十章大纲(v3.1 修订点以 【v3.1】 标注)

### 1. Introduction
- 1.1 空间产量建模的广泛应用与环境变量作为主要预测源的惯例
- 1.2 现有文献的两大盲区:(a) 目标变量来源对模型性能的影响被忽视;(b) 空间自相关导致的 CV 乐观偏差普遍存在但少有量化
- 1.3 中国小农经济背景下区域尺度产量建模的特殊挑战(田块破碎、统计口径不一、遥感反演与实测差距)
- 1.4 【v3.1 重写】本研究的贡献--用 benchmark 语言表述:
  - (i) 一个**可迁移的区域产量制图最小基准协议**:固定且版本化的验证划分(随机/纬度块/棋盘三类,分别回答不同问题)、目标来源敏感性分析、多维指标(R2/RMSE/PICP/MPW)、复现包(固定折划分+种子+环境文件)
  - (ii) 四种产量目标构建的受控因子实验,暴露目标来源对精度声明的支配性影响
  - (iii) 循环验证的定量上界论证(新)
  - 定位句:与植物基因组预测领域的标准化呼声(Agronomy 2026 benchmark Perspective)同构,把"空间产量制图"纳入同一评估方法学谱系
- **【v3.1 扩充】关键引用**: Ploton et al. 2020 Nat Commun; Roberts et al. 2017 Ecography; **Meyer & Pebesma 2022 Nat Commun; Raudaschl et al. 2021 (spatial CV evaluation); Meyer & Pebesma 2021 Remote Sens Ecol (AOA)**; Zhao et al. 2023 ESSD; Lobell et al. 2015 Science; **Agronomy 2026 标准化基准 Perspective(同构领域锚点)**
- 术语统一(按导师建议,全稿执行):spatial CV / block CV / extrapolation 严格区分--spatial CV 泛指所有空间分块交叉验证;block CV 特指分块机制;extrapolation 仅指训练点覆盖范围之外或环境空间之外的预测(引用 Meyer & Pebesma 的 AOA 定义)

### 2. Study Area and Data
- 2.1 研究区:北京市平谷区(234 网格,0.0417° 分辨率 ≈ 3.6 km(经向) × 4.6 km(纬向) 各向异性,单格 ≈16.4 km2),华北平原北部山前平原,冬小麦-玉米轮作。【口径说明】早期文档曾称 "3.5 km"(仅经向跨度)或 "~4.6 km"(仅纬向跨度/对角线),两者各取一向;正确表述为各向异性网格,全稿统一。
- 2.2 环境变量矩阵(24 建模变量):WorldClim bio1-bio19 + 月值温度/降水 + GDD + SoilGrids(clay/sand/silt/SOC/Bd/CEC/pH/N)+ SRTM(elevation/slope/aspect)
- 【v3.1】Table 1 升级:每变量标注单位、数据源版本(WorldClim 2.1、SoilGrids 2.0 及土层深度 0-5/5-15cm)、VIF 阈值(保留 VIF<10,报告最大 VIF)
- 2.3 产量数据来源与属性表:A 实测 43 网格 / B 空间插值(Ridge 训练 R2=0.99)/ C 贝叶斯融合 / D ChinaWheatYield30m 2021(22 网格)
- 【v3.1】2.3 补一句:来源 D 许可确认(CC BY 4.0,Zhao et al. 2023 ESSD 数据说明);来源 A/B/C 为项目内部构建,构建脚本公开
- 【W12 新增 2.5】**扩充主表 augmented_yield_master.csv(1,786 行)的定位**:它是 W9 数据补强产出的**数据资源层**(面板列 New_Yield/SAT/CO2 等 1552 网格非空),不是诊断线四目标框架的成员(n=43/234/22),也不是 250m 线(301 网格)--角色 = 1第二目标复检(6.7 节)的数据底座;2管理假说检验路径 (a) 的 N/水管理列来源;3未来第三篇(管理情景/时序)的候选素材。README 中从"数据补强头条"降级到"数据资源"一节
- 2.4 数据审计:零缺失(24 建模变量)、坐标系统一(EPSG:4326)、单位标准化(t/ha)

### 3. Methods
- 3.1 特征工程与筛选:VIF → Boruta(50 iter, 5 shadow) → SHAP 重要性 → 联合推荐集(SHAP 背景数据集明确为训练折【v3.1】)
- 3.2 空间交叉验证方案:
  - 随机 5 折(对照组)
  - 纬度五分位块(处理南北梯度)
  - 经纬度 0.03° 棋盘 5 折(主口径)
  - 乐观偏差定义:随机 CV R2 - 最优空间 CV R2
- 【v3.1 新增 3.2.4】**块尺寸辩护(variogram)**:经验变差函数估计产量与 CV 残差的自相关变程均 ≈4.6 km;棋盘块 0.03°≈3.3 km = 0.72×变程,属于"部分阻断自相关"的中间强度分块--因此棋盘 CV 与随机 CV 的差值(+0.036~0.088)应解读为自相关乐观偏差的**下界**;纬度块(跨度约 12 km > 变程)测到的是梯度混杂而非纯自相关。附 review_response_variogram.json 证据。
- 3.3 模型:XGBoost(200,depth=5,lr=0.05) / LightGBM(同参) / RF(200,depth=7)
- 【v3.1】3.3.1 **重复协议**:所有 CV 方案在 3 个随机种子(7/21/42)下重复,报告折级 R2 mean±SD 与 pooled R2;分块方案的块划分固定、种子仅影响折内随机性,仍然报告(benchmark 标准)
- 3.4 QRF 不确定性量化:300 树,纬度空间 5 折,10/50/90 分位,PICP 与 MPW 诊断
- 【v3.1 新增 3.4.1】**Split-conformal 校准**:训练/校准/测试 = 70/70/94;不合格分数 s=max((y-q50)/spread,(q50-y)/spread),q̂ 取 90% 分位;报告校准前后 PICP/MPW
- 3.5 目标来源敏感性实验设计:同特征 × 四目标 × 两 CV 方案的完整因子设计
- 3.6 独立数据源交叉验证:D 目标用不同数据源重复全部实验
- 3.7 统计检验:Pearson r、R2(pooled/fold-mean)、RMSE、MAE、PICP、MPW;【v3.1】三种子配对样本的 Welch t 检验用于随机 vs 空间 CV 的 R2 差值显著性

### 4. Results I: Environmental Fingerprint Audit
- 4.1 变量描述统计(Table 1:24 变量 mean±std/min/max/CV%/VIF+单位+数据版本)
- 4.2 Boruta 筛选结果（fig02）
- 4.3 SHAP 重要性排序（fig03：Top-30，色板 colorblind-safe viridis【v3.1】，图注注明背景数据集=训练折）
- 4.4 累计 SHAP 曲线（fig02 dashboard 内嵌）

### 5. Results II: CV Scheme Comparison (G2)
- 5.1 三方案×三模型的 R2/RMSE 对比表(Table 2 升级为 mean±SD over 3 seeds)与 fig04
- 5.2 乐观偏差量化【主口径 pooled】:pooled R2 随机-棋盘 = +0.020(RF) 至 +0.061(XGB);折级均值口径 +0.036(RF) 至 +0.088(XGB) 作辅助,两种口径均在正文标注,避免审稿人复算不一致。3 种子下稳定(SD ≤ 0.025),Welch t 检验 p<0.05
- 5.3 纬度块崩塌现象:南北气候梯度作为强混杂因素
- 5.4 棋盘块 CV 作为主口径的理由(引用 3.2.4 variogram 辩护:0.72×变程,下界性质)

### 6. Results III: Yield Target Source Sensitivity (G1)
- 6.1 四目标 × 三模型 × 两 CV 方案的性能矩阵(Table 3)与 fig05
- 6.2 目标 B 的循环论证:R2=0.98 的机制解析
- 【v3.1 升级 6.2.1】**循环验证的定量上界论证**(审稿意见 #6):
  - 插值目标的训练拟合 R2=0.99 给出环境模型可复现的上限
  - 新证据:43 个真实观测点的留一 IDW 纯空间插值仅达 R2=0.20(k=8)/0.27(k=4)--真实产量中可被空间结构解释的部分有限
  - 推理链:目标 B 若由环境特征驱动的 Ridge 插值产生,则任何足够灵活的环境模型都能"复原"该表面 → R2 上界≈插值训练拟合(0.99)→ 观测 0.98 贴近上界 = 循环成立的定量证据
  - 误差传播草图:Var(B-ŷ) ≥ Var(B)-R2_interp·Var(A):目标 B 的表观可预测性由构建过程注入,与农田真实变异无关
  - 【v3.1 W12 升格】本论证从 review_response 附件升格为 Discussion 正式段落(§8.3 引用)并配小图(LOO-IDW 自插值 R2 0.20-0.43 vs 目标 B 0.98 对比条图)
- 6.3 目标 A 的真实技能:R2≈0(三模型一致,n=43 有效样本下置信区间宽,如实报告)
- 6.4 目标 C 的表观性能来源分解:平滑性贡献 vs 环境信号贡献
- 6.5 目标 D 独立源验证:checker CV R2 全负
- 【v3.1 W12 新增 6.5.1】**D 目标(n=22)fold-mean 与 pooled 巨大分歧的正文化**(审稿人必问):checker 折级 -1.03~-1.31 但 pooled -0.09~-0.21;random 折级 0.16~0.24 但 pooled 0.99。机制:22 样本分 5 折后每折仅 4-5 个网格,折级 R2 对单折均值偏移极度敏感(方差巨大);而 pooled R2 被目标本身的簇状结构主导(相邻网格产量高度相似,随机折内近邻泄漏)。处理:两种口径都报告,明确"n<30 时 fold-mean 与 pooled 不可互推";pooled 0.99 不作为技能声明,仅作为循环机制演示
- 6.6 r(obs, pred)=0.510:空间预测系统性低估变异(pred std 0.056 vs obs std 0.224)
- 【v3.1 W12 新增 6.7】**第二目标复检:Xiao2024 面板 1552 网格(跨目标稳健性检验)**:New_Yield(15.71±0.31 t/ha,与 234 诊断网格零重叠)上同特征重跑--随机 CV pooled 0.499(折级 0.499±0.051),棋盘 CV pooled 0.165(折级 0.165±0.126,块 0.0417°)。解读:面板目标上环境信号存在但棋盘分块后大幅衰减(-0.33),与主线"随机 CV 乐观偏差"结论方向一致;量级差异源于目标性质(Xiao2024 本身是模型反演产物,含环境信息)--这恰好再次印证"目标来源决定表观性能"的主线论点。台账 w12_b2_panel_check.csv。**单年局限由此从"未检验"升格为"已做第二目标稳健性复检,跨年仍待 Zenodo 2016-2020"**

### 7. Results IV: QRF Uncertainty Quantification (G3)
- 7.1 PICP 与 MPW（fig07A：区间带+观测叠加）
- 7.2 校准散点（fig07B）
- 7.3 区间宽度分布（fig07C：异方差模式）
- 【v3.1 重写 7.4】**欠覆盖的诊断与 conformal 校准**(审稿意见 #5):
  - 原始 QRF:PICP=0.705(名义 90%),欠覆盖确认
  - Split-conformal 校准后:PICP=0.862,MPW 0.623→0.789 t/ha(+27% 宽度换取 +15.7pp 覆盖)
  - **残余 3.8pp 欠覆盖的解释**:n_cal=70 时 conformal 分位数 q̂ 的抽样波动约为 ±1.96·√(0.9·0.1/70)≈±0.07,对应 PICP 波动 ±3-4pp--本轮单次校准的 0.862 与名义 0.90 在抽样误差内相容;宽度代价 MPW +27% 是保覆盖的必然成本;报告两种口径供审稿人复算
  - 剩余 4pp 欠覆盖来源:校准/测试分裂的单次随机性 + 异方差残差;定位为"演示级校准",完整方案(CV+ 与 weighted conformal)列为展望
  - 结论口径:QRF 区间**未经校准时不可用于风险决策**;conformal 校准是此类研究的最低配置

### 8. Discussion
- 8.1 为什么环境指纹在 0.041° 网格尺度不解释产量变异?
  - 【v3.1 定性调整】管理因素假说(施肥/灌溉/品种)--**明确标注为"待检验假说"而非结论**(审稿意见 #4);给出三条检验路径:(a) 若村级/农户级管理数据可获得,做方差分解;(b) 品种固定效应粗对照(若 Data 可用);(c) 与文献效应量对照:小农区管理效应通常占产量变异 30-60%,环境主导区 <20%--本文 R2≈0 与管理主导假说一致但不证明
  - 环境变量分辨率与农艺过程尺度不匹配
  - 小农田块异质性超出网格平均表征能力
  - 【v3.1 新增】与姊妹论文(250m 混合制图线)的证据互引:250m 尺度下随机 CV R2=0.77 完全来自空间连续性(外推梯度谱单调衰减至 -0.83),支持"空间结构/管理背景主导"而非环境因果解释
- 8.2 空间产量建模文献中的乐观偏差普遍性:与 Ploton 2020、Meyer & Pebesma 2022 对话【v3.1 扩展】
- 8.3 目标来源的批判性审视:空间插值目标≠独立观测(引用 6.2.1 上界论证)
- 8.4 【v3.1 升格】**区域产量制图报告清单(checklist,MDPI 读者可复用产出)**:
  任何区域产量制图研究必须声明:
  - (a) 产量目标的来源、构建方法、构建参数(含插值/融合的训练拟合度)
  - (b) 空间 CV 口径:块尺寸相对自相关变程的比例(附 variogram 图),或明确说明块尺寸选择依据
  - (c) 随机 CV 与空间 CV 的 R2 差值(乐观偏差下界)
  - (d) 重复种子数与折级 SD
  - (e) 不确定性区间的校准状态(未校准 PICP 必须报告)
  - (f) 目标的独立来源敏感性检验(至少一个外部数据源)
  - (g) 有效样本量与评估网格差异的声明(不同目标不可直接比较时)
- 8.5 局限性:【v3.1 提前至摘要+首条】**单年单区数据**--主诊断基于 2021 生长季平谷区;【W12 更新】已在 Xiao2024 面板 1552 网格上完成第二目标复检(6.7 节,方向一致),跨年泛化仍待 Zenodo 2016-2020 多年份下载;43 实测点样本量限制;QRF 区间校准为演示级;遥感反演系统性偏差;管理变量缺失使 R2≈0 的解释停留在假说层面【W12 补】假说检验路径落地顺序:(a) Xiao2024 面板 N/水管理列入模对照(数据现成,首选)> (b) management_scenarios.csv 14 文献情景敏感性边界演示 > (c) 品种固定效应--**已确认无网格-品种映射数据,路径 (c) 放弃并写入正文**

### 9. Conclusions
- 三个可检验命题的结果与含义
- 方法学贡献:可迁移的最小基准协议(benchmark-first 表述)
- 后续工作:多年份扩展(Zenodo 2016-2020 已在下载队列)、管理变量纳入(假说检验三路径)、田块尺度研究

### 10. Data Availability & Code Availability & Reproducibility Package
- 代码:GitHub ( DearDragon233/2026-SP )
- 数据:环境变量来源 URL、产量数据获取方式与许可
- 【v3.1 新增】**复现包承诺**(审稿意见 #8):
  - 固定折划分文件(fold_assignments_{scheme}.csv,随机/纬度/棋盘三套,随代码发布)
  - 全部随机种子(7/21/42)与调参日志
  - requirements.txt / environment.yml(Python 3.13, scikit-learn, xgboost 版本号)
  - 一键复现:advance_validation.py → review_response_experiments.py → review_response_diag.py
  - 数据版本:WorldClim 2.1 / SoilGrids 2.0 / ChinaWheatYield30m v2023(DOI 固定)

---

## 图表清单(8 主图 + 2 补充图 + 5 表)

| 编号 | 内容 | 状态 |
|---|---|---|
| Fig 1 | 研究区地图 + 234 网格 + 产量来源分布 | 待制 |
| Fig 2 | 特征审计 Dashboard（Boruta 三色，原 fig01_feature_audit_dashboard） | ✅（W12 重编号） |
| Fig 3 | SHAP 重要性 Top-30（viridis 色板，原 fig02） | ✅（W12 重编号） |
| Fig 4 | CV 方案对比（原 fig05） | ✅（W12 重编号） |
| Fig 5 | 产量目标敏感性（原 fig07） | ✅（W12 重编号） |
| Fig 6 | 独立源验证（原 fig08） | ✅（W12 重编号） |
| Fig 7 | QRF 不确定性（原 fig06） | ✅（W12 重编号） |
| Fig 8 | variogram：产量/残差 γ(h) 曲线 + 块尺寸-变程比标注 | ✅（W12 新增，make_fig08_variogram.py） |
| Fig 9-13 | 250m 姊妹线图（learning curve/实验对比/分块/散点/外推谱），跨线引用 | ✅ |
| Table 1 | 24 变量描述统计（+单位+数据版本+VIF） | 数据就绪 |
| Table 2 | CV 方案对比（3 种子 mean±SD） | ✅ review_response_diag_seeds.csv |
| Table 3 | 四目标×三模型敏感性矩阵 | 数据就绪 |
| Table 4 | QRF 指标汇总（+conformal 前后对照） | ✅ review_response_conformal.csv |
| Table 5 | 区域产量制图报告清单（checklist 表格版） | 随 8.4 节成稿 |

**【W12 图号规范】**诊断线主图序列 = fig01-fig08（study_area / feature_audit / shap / cv_scheme / source_sensitivity / independent_validation / qrf / variogram）；250m 线 = fig09-fig13。旧 fig03_model_comparison 与 fig04_feature_selection_dashboard 移入 `figures/diagnostic_reserve/`（不在投稿序列，仅备用）。

## 与 v3.0 的差异

| v3.0 | v3.1(审稿响应) |
|---|---|
| 贡献声明=案例研究 | 贡献声明=可迁移最小基准协议 |
| CV 对比单种子 | 3 种子重复,全表 mean±SD,Welch t 检验 |
| QRF 欠覆盖只诊断不修 | split-conformal 校准实验(PICP 0.705→0.862) |
| 目标 B 循环论证为叙事 | 定量上界论证(IDW LOO R2=0.20-0.27 vs 目标 B 0.98) |
| 棋盘 0.03° 无辩护 | variogram 变程 4.6km,块=0.72×变程,偏差下界论证 |
| 管理主导为断言 | 明确标注假说+三条检验路径 |
| 文献锚定较窄 | 补 Meyer & Pebesma 2022、Raudaschl 2021 等,术语统一 |
| 局限性在 8.5 一笔带过 | 单年单区局限前置于摘要 |
| 无复现包细节 | 固定折划分+种子+环境文件承诺 |
