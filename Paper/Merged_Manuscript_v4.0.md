# 2026-SP 合并主文稿 v4.0(统一叙事版大纲)
## 模型产量目标的陷阱:县域冬小麦产量制图中目标构建与验证设计的受控诊断
## The Trap of Model-Derived Yield Targets: A Controlled Diagnostic of Target Construction and Validation Design for County-Scale Winter Wheat Yield Mapping

**目标期刊**: Agronomy(Methods / Precision and Digital Agriculture 板块)
**版本**: v4.0-merge(2026-09-15,W15 评审响应:两线合并+F1 目标重标)
**取代**: Outline_v3.1_diagnostic.md(诊断线)与 Draft_v1_hybrid_mapping.md(混合线)--两线内容并入本稿,原文件归档保留

> **W15 重构核心(F1 响应)**:溯源确认全部四类产量目标均为模型产物--A=过程模型基准期模拟(Xiao et al. 2024, WheatYield_ref.tif;43 格 7.21±0.23 t/ha),B=A 的 Ridge 插值,C=A+区级先验贝叶斯融合,D=遥感反演(ChinaWheatYield30m,22 格)。"实测产量"表述全文删除。真实产量锚点仅市级统计口径(北京 2021 小麦 5,241 kg/ha,国家统计局北京调查总队);区县级与田块级真实数据不可公开获得(如实声明,见数据台账缺口 G1/G2)。
> **统一命题**:在真实产量不可得的现实约束下,模型产量目标 + 常规验证设计会系统性地制造虚假精度。本文用受控因子设计量化三重陷阱:**目标构建陷阱**(插值目标 R2=0.98 的循环上界)、**验证设计陷阱**(无变程设计的空间 CV 是安慰剂,剂量响应曲线)、**表征陷阱**(静态环境协变量与动态/管理表征的价值边界)。三条诊断均给出可迁移的核查协议。

---

## 摘要要点(中英双语,380 词)

**Background**: Regional yield mapping increasingly relies on model-derived yield targets-process-model baselines, remotely sensed retrievals, and their interpolations-because field-measured yields are rarely available at grid scale. The joint risks of target construction, validation design, and environmental representation have never been quantified within a single controlled design.

**Data transparency**: All four yield targets examined here are model-derived: (A) process-model baseline simulation (Xiao et al. 2024 Nature Food dataset; 43 grids, 7.21±0.23 t/ha, 38% above the Beijing statistical average of 5.24 t/ha, consistent with potential-yield semantics), (B) Ridge interpolation of A (R2=0.99 on training fit), (C) Bayesian blend of B with a district prior (234 grids), and (D) remotely sensed retrieval (ChinaWheatYield30m; 22 grids). No field-measured grid-level yields are publicly available for the study area (district- and field-level statistics unavailable; see Data Availability). **We therefore claim no ground-truth validation and instead quantify how each model-derived target manufactures apparent skill.**

**Methods**: 234-grid (0.0417° ≈ 3.6×4.6 km) environmental fingerprint matrix (24 modeling variables) × four targets × five validation schemes (random / checkerboard 0.72× range / latitude-block / LOBO / environment-space k-means), XGBoost+RF, 3-5 seeds with min reporting; variogram-informed block-size dose-response (0.5×-4× range); PC1-5 axis regressions; bootstrap CIs (B=2000); split-conformal calibration of QRF intervals; phenology-weighted dynamic features (FDD, HDF).

**Results**: (1) **Target trap**: the interpolated target yields pooled R2=0.98 although leave-one-out IDW of its 43 source values reaches only R2=0.20-0.27 - circular validation quantified as an upper bound. (2) **Validation trap**: within a domain only ~5× the variogram range wide, the checkerboard family is **structurally a placebo** - its between-block nearest-neighbour distance stays at 2.3-2.4 km regardless of block size, and the optimism gap vanishes not because large blocks grow honest but because large-grid checkerboards silently degenerate into random splitting (gap +0.113 at 0.5× range → -0.006 at 4× range); large gaps arise only from schemes that cut the elevation gradient or environmental continuity (latitude-block +0.288, LOBO +0.276, env-space +0.54). **Range-aware block sizing is powerless in small domains; domain size in range units must be reported alongside block size.** (3) **Representation trap**: the environment is effectively one elevation axis (PC1 = 66% variance, r(PC1, elevation)=-0.94), PC1-5 jointly explain only R2=0.24 of target A, winter-wheat-appropriate thermal features (Tbase=0 °C seasonal GDD, vernalisation days, deep-freeze days, grain-fill heat) add +0.006 on C and exactly 0 on A, and even the process-model baseline's own spatial pattern cannot be captured (all schemes ≤0.20 on A) - static covariates, same-sensor features, and correctly-parameterised dynamic aggregates all fail. (4) QRF intervals (PICP 0.705→0.862 after conformal calibration; MPW 0.62-0.79 t/ha ≈ 2.6× target SD) support only trend screening, not insurance-grade pricing - a decision-suitability matrix is provided.

**Conclusions**: For model-derived targets, apparent skill is manufactured by target construction, validation design, and representation limits - not by environmental information. We release a transferable **pre-mapping audit protocol**: (i) declare target provenance and its training fit; (ii) estimate the variogram range **and the domain size in range units** before choosing block sizes - if the domain spans ≲5 ranges, checkerboard/block families are structurally uninformative and gradient-stripe, LOBO, or environment-space designs must be used instead; (iii) test the elevation/PC1 axis before celebrating multi-variable importance; (iv) report interval width against the decision it must support.

---

## 章节结构(合并稿:九章 + 复现包)

### 1. Introduction
- 1.1 产量制图对模型产量目标的依赖:真实产量不可得 → 模型产品补位( Xiao2024/ChinaWheatYield30m/SPAM 等)
- 1.2 三重风险未被联合量化:目标构建(循环)、验证设计(空间 CV 安慰剂)、表征(静态快照)
- 1.3 贡献(benchmark-first 语言):可迁移的 pre-mapping audit protocol(四步核查协议)+ 受控因子诊断 + 诚实定位(无 ground-truth 声明)
- 关键引用:Ploton 2020; Roberts 2017; Meyer & Pebesma 2022; Raudaschl 2021; Wadoux 2021; Zhao 2023 ESSD; Xiao 2024 Nature Food; Agronomy 2026 benchmark Perspective

### 2. Study Area, Targets, and the Provenance Audit(重写)
- 2.1 研究区:234 网格,0.0417° 各向异性(3.6×4.6 km),北山南原(海拔 15-898 m)
- 2.2 环境矩阵:24 建模变量(WorldClim 2.1 + SoilGrids 2.0 + SRTM 派生),来源版本/单位/VIF 全表(Table 1)
- 2.3 **四类产量目标与溯源声明(F1 重标)**:
  - A = 过程模型基准期模拟(Xiao et al. 2024 基准期 WheatYield_ref 1km 聚合,43 格,7.21±0.23 t/ha)--**非实测**
  - B = A 的 Ridge 插值(训练拟合 R2=0.99,234 格)
  - C = B 与区级先验的贝叶斯融合(234 格)
  - D = ChinaWheatYield30m 2021 遥感反演(22 格,n_px≥4 有效像元阈值;23 格为 n_px≥1 口径,正文统一 ≥4)
  - 真实统计锚点:北京市 2021 小麦单产 5,241 kg/ha(市级,国家统计局北京调查总队);区县级/田块级不可得(缺口声明)
  - A 比市级统计高 38% → 潜力产量语义的独立旁证
- 2.4 数据审计:24 建模变量按变量分列缺失表(Table 1 附列;**71 列现役特征零缺失**,W15 报告所指 18 格地形缺失不在现役数据源,澄清见回复信 F3)
- 2.5 扩充主表（1,786 行）定位：数据资源层（面板 History 基准 + 2030s/2060s 情景），非诊断四目标成员
- 2.6 【W16 补】**姊妹 250m 线数据**（本稿 §8.1 引用的外推谱线证据来源）：301 个 250m 耕作网格（ChinaWheatYield30m 30m 聚合，≥16/64 有效像元），72 特征（58 环境基线 + 2021 年特异气候 7 + 距平 4 + 交互 3，另含 Open-Meteo ERA5-Land 逐日层）；目标同为 D 线遥感反演（301 格，5.868±0.264 t/ha）；验证方案（随机/纬度块/LOBO8）与折划分文件同包发布（Outputs/repro_package/）。详细管线见归档 Draft_v1_hybrid_mapping.md 与 src/s5_r2_improvement/

### 3. Methods
- 3.1 特征工程与筛选(VIF→Boruta→SHAP;SHAP 背景数据集=训练折;色板 viridis)
- 3.2 验证设计(五方案谱系 + 剂量响应):
  - 随机 5 折 / 棋盘 1× 变程(主口径,W16 统一;0.72× 降为灵敏度档)/ 纬度 4 分位块 / LOBO(KMeans8)/ 环境空间 KMeans4
  - **3.2.4 块尺寸剂量响应与退化机制(W14 设计、W16 重解读)**:0.5×~4× 变程 × 2 模型 × 3 种子。**W16 关键更正**:gap 归零并非"块大变诚实",而是棋盘在 ≲5× 变程的小域内**结构性失效**--全棋盘档的平均最近异块邻距离恒定在 2.3-2.4 km(不随块尺寸变化),4× 处 gap=-0.006 是分块静默退化为随机的签名;真正的大 gap 只出现在切断海拔/环境连续性的方案(lat4 +0.288/LOBO +0.276/环境分块 +0.54)。**域尺度(变程单位)必须与块尺寸一起报告**;w16_p1_degeneration.csv
- 3.3 模型与参数来源声明:XGBoost(optuna428,**迁移自 250m 独立管线的折内调优**,e6_tuned_params.json 在案)+ 嵌套重调参敏感性(诊断数据内 Optuna 12trial×3 折:random 0.401/checker 0.373/lat4 0.196--结论对超参不敏感);RF(500)
- 3.4 重复协议:3 种子主口径 + 5 种子扩展 + min(最差种子)报告
- 3.5 QRF + split-conformal(70/70/94,q̂=2.08)
- 3.6 PCA 表征诊断:PC1-5 逐轴 + 联合对 A/C 回归
- 3.7 物候期动态特征:FDD(越冬冻害积寒)+ HDF(灌浆期高温日数),Open-Meteo 2021 逐日构造;**W16 补小麦适生热量组**:Tbase=0°C 季节积温、春化日数(12-2 月 0-10°C 窗口)、深冬极端冻害日(Tmin≤-10°C)、灌浆期 ≥30°C 高温日--修正 F4 的 Tbase=10 玉米型错配
- 3.8 bootstrap CI(B=2000)与等效性表述规范
- 3.9 GDD 定义文档化:**Tbase=10°C 是上游数据生成器参数**(数据反推 R2=0.995,零 GDD 月 tavg 上界 9.99°C 自洽),GDD_m=days×max(0, tavg_m-Tbase)--**W16 更名声明:GDD_gs 实为 AT10(≥10°C 活动积温,玉米型指标),非冬小麦生理基准**(冬小麦文献值 0-4.4°C);小麦适生热量指标另行构造(见 3.7),防止读者生理学误读

### 4. Results I: The Target Trap(目标构建陷阱)
- 4.1 四目标 × 模型矩阵(Table 3):A R2≈0(CI [-0.20,-0.02] 等效性表述)/ B 0.98 循环上界(LOO-IDW 0.20-0.27)/ C 0.40(CI [0.25,0.51])/ D 双口径分歧正文化
- 4.2 **循环上界论证**(定量):插值目标训练拟合=环境模型可复原上界
- 4.3 A 目标量级对账:7.21 vs 市级统计 5.24(+38%→潜力产量语义旁证)
- 4.4 D 目标与真实锚点量级一致(5.78 vs 5.24,+10%)→ 遥感反演目标的表观技能仍受验证设计支配(4.5 独立源 checker 全负)

### 5. Results II: The Validation Trap(验证设计陷阱)
- 5.1 五方案谱系(fig08B):随机 0.40 / 棋盘 0.37 / 纬度 0.11 / LOBO 0.12 / 环境分块 -0.14
- 5.2 **三段式乐观偏差(W16 机制更正)**:棋盘族 gap≈0 的机制不是"块大变诚实",而是小域内分块退化为随机(邻距离恒定 2.3-2.4 km,w16_p1_degeneration.csv);纬度 +0.288/LOBO +0.276/环境分块 +0.54 的 gap 来自切断海拔梯度/环境连续性--**gap 的决定因素是"是否切断主导梯度"而非"块尺寸大小"**
- 5.3 **剂量响应曲线(W16 重解读)**(fig08C):gap 从 0.5× 变程的 +0.11 收敛到 4× 的 -0.006(不降反微升,退化为随机的签名);**在 ≲5× 变程的小域内棋盘/方块族不存在可修复的块尺寸--结构性安慰剂;变程感知设计只在大域(≫变程)有效**--协议第 (ii) 步由此升级为"变程+域尺度双判据"
- 5.4 折级 vs pooled 双口径规范(lat4 折级 -0.205 的机制:4 块折级方差巨大)

### 6. Results III: The Representation Trap(表征陷阱)
- 6.1 PCA:PC1=海拔轴(66.3%,r=-0.936),n80=3--"多维指纹"一阶近似是山-原二元梯度
- 6.2 PC1-5 联合对 A 仅 R2=0.238--共线性批评免疫(连潜变量都解释不了)
- 6.3 SHAP 冬季温度变量的海拔代理声明 + 越冬生理学解读(bio9≈-3.9°C 冻害窗口)
- 6.4 动态特征敏感性【W16 双重验证】:玉米型指标(FDD/HDF,Tbase=10°C)无增益(+0.006);**小麦适生热量组(Tbase=0 季节积温/春化日数/深冬冻害日/灌浆高温日)在 C +0.006、在 A 逐位零增益**--修正生理学错配后表征陷阱结论闭合:静态与正确参数化的动态聚合在县域内同界(w16_p2_wheat_thermal.csv)
- 6.5 跨作物旁证:Xiao2024 面板 1552 格(周年优化产量目标)随机 0.499 / 棋盘 0.165

### 7. Results IV: Uncertainty and Decision Value
- 7.1 QRF 区间与 conformal 校准(PICP 0.705→0.862;MPW 0.62→0.79)
- 7.2 **决策适用性矩阵**(F5,审稿人点名):保险定价(需宽度<SD)❌ / 趋势筛查 ⚠️ / 预警分带 ✅ / 碳 MRV 计量 ❌--数字的价值由它能支撑的决策定义
- 7.3 校准为演示级定位(n_cal=70 抽样波动 ±3-4pp)

### 8. Discussion
- 8.1 三陷阱的统一机制:模型产量目标的空间变异由管理/构建过程主导--静态环境协变量、同源传感特征、动态聚合均无法捕捉;与姊妹 250m 线互证(混合模型增益=空间连续性,外推单调衰减至 -0.83)
- 8.2 与空间预测评估文献对话(Ploton/Meyer & Pebesma/Roberts/Raudaschl):本文把"要用空间 CV"推进到"空间 CV 需变程诊断"的可操作先验
- 8.3 目标来源批判:插值目标≠观测;过程模型基准≠实测;量级对账(+38%)作为快速自查工具
- 8.4 **Pre-mapping audit protocol(四步核查协议,转 Supplementary S1 九步自评表)**:
  (i) 目标溯源声明+训练拟合披露;(ii) variogram 变程先估、块尺寸按比例设计;(iii) PC1/海拔轴先验检验再谈多变量重要性;(iv) 区间宽度对照决策需求
- 8.5 局限:单年单区(跨年待 Zenodo 多年份);无 ground-truth(本文的研究动机与结论边界,不是疏忽);管理变量缺失(假说检验路径 a/b);QRF 校准演示级
- 8.6 静态快照性质与管理主导假说(假说标注+检验路径,路径 (c) 品种固定效应因无映射数据放弃)【W16 补 A/D 落差旁证】A 目标(潜力语义,比市级统计 +38%)与 D 目标(遥感实际语义,+10%)对同一统计锚点的落差 ≈28 个百分点--**可实现产量与实际产量的差=管理可缩小的差距**,为管理主导假说提供外部定量旁证(零成本证据,写作时纳入 §8.6)

### 9. Conclusions
- 三重陷阱量化 + 四步核查协议 + "数字的价值由决策定义"
- 后续:Zenodo 多年份跨年检验、管理面板列入模(路径 a)、田块尺度真值研究(数据不可得是领域痛点,正是本协议存在的理由)

### 10. Data Availability & Reproducibility Package
- 全部台账(目标溯源链、真实数据台账 w15_real_yield_data_ledger.md、实验台账 v2/gap/dose-response/spectrum/bootstrap)
- 复现承诺:折划分文件+种子+environment.yml(R1 遗留,成稿时兑现)
- 一键复现链:advance_validation → review_response_* → w12/w13/w14/w15 实验包

## 图表清单(合并稿连续编号)

| 编号 | 内容 | 来源线 |
|---|---|---|
| Fig 1 | 研究区+四目标分布(含溯源流程小图) | 诊断线(待制) |
| Fig 2 | 特征审计 Dashboard | 诊断线 fig02 |
| Fig 3 | SHAP Top-30 | 诊断线 fig03 |
| Fig 4 | 五方案谱系+剂量响应(=原 fig08 三面板) | W14 合并 |
| Fig 5 | 四目标×模型敏感性 | 诊断线 fig05 |
| Fig 6 | 目标 B 循环上界条图(LOO-IDW vs 0.98) | 新制(写作期) |
| Fig 7 | QRF+conformal | 诊断线 fig07 |
| Fig 8 | 250m 混合线五联图(学习曲线/实验对比/分块/散点/外推谱,可拆补充图) | 混合线 fig09-13 |
| Fig 9 | PCA 双图(载荷+PC 逐轴 R2) | W15 新制 |
| Table 1 | 变量表(+缺失分列) | 数据就绪 |
| Table 2 | 验证方案对比(多种子+min) | review_response_diag_seeds_v2 + w14_q6 |
| Table 3 | 四目标敏感性矩阵 | 数据就绪 |
| Table 4 | QRF+conformal | review_response_conformal |
| Table 5 | 决策适用性矩阵 | W15 新制 |
| Table S1 | 九步基准化自评表 | 写作期 |
| Graphical Abstract | 四目标×五方案热图+一句话结论 | 写作期 |

## 与旧版的差异(v3.1/v1 → v4.0)

| 维度 | 旧(两线分立) | v4.0(合并+重标) |
|---|---|---|
| 目标 A 身份 | "实测 43 网格"(错误) | 过程模型基准模拟(溯源链+量级对账双证据) |
| 真实数据 | 未声明 | 市级统计锚点 5.24 t/ha + 区县/田块缺口声明 |
| 主线 | 诊断+混合两条独立故事线 | 三重陷阱统一命题(目标/验证/表征) |
| 验证 | 三方案+外推谱 | 五方案+剂量响应(signature) |
| 表征 | 变量重要性叙事 | PC1 海拔轴先行诊断+动态特征边界 |
| 不确定性 | PICP/MPW 报告 | +决策适用性矩阵(价值由决策定义) |
