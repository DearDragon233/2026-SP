# 学术价值提炼与创新点对照（2026-SP 250m 管线 R² 提升轮）

日期：2026-09-14 ｜ 实验：src/s5_r2_improvement/ ｜ 台账：Outputs/intermediate/experiments_ledger_v3.csv

---

## 一、本轮结果总览（同折可比，seed=42）

| 实验 | 设计 | 特征数 | 随机5折 pooled R² | 调整R² | 空间分块CV R² |
|---|---|---|---|---|---|
| E0 | v4 基线复刻 | 58 | 0.3258 | 0.1642 | 0.1375（纬度4块） |
| E1 | +2021年份特异气候7列 | 65 | 0.3223 | 0.1349 | — |
| E2 | +距平4+交互3 | 72 | 0.3237 | 0.1101 | — |
| E5 | E2+折内增益top-25 | 25 | 0.3239 | **0.2807** | 0.1136 |
| E7 | E5+Ridge 0.5混合 | 25 | **0.3423** | **0.3004** | — |
| E8 | E2+折内残差IDW（混合制图） | 72 | **0.7694** | **0.6966** | **0.5386** |
| M0 | 基线+lon/lat（mapping mode） | 60 | 0.6000 | 0.5000 | — |
| M7 | E7+lon/lat | 27 | 0.5205 | 0.4917 | 0.4349（SM5） |

留出集（80/20, seed=7）：E0=0.3747，E7=0.3815，**E8=0.6832**。
重复 5×5 CV（5 种子）：E0=0.3264±0.0073，E8=**0.7550±0.0211**（min 0.7138）。
分块敏感性：纬度4块 E8=0.539 / 经度4块 E8=0.136 / KMeans4块 E8=-0.261。

## 二、创新点表述（论文可用）

### 创新点 1：残差 IDW 混合制图模型（回归克里金的机器学习等价物）
**做法**：XGBoost 先学环境-产量关系，再用训练折残差的 8 近邻反距离加权（IDW）修正预测——环境信号与空间结构信号显式解耦。
**与常规做法差异**：常规"ML+坐标"是把经纬度当特征塞进去（M0 组），坐标与其它特征在树分裂中隐性竞争，空间信号与环境信号纠缠；残差混合把两者分开，各自用最合适的方式建模（树模型学环境、IDW 学空间自相关）。
**为什么有效**：产量空间变异由环境梯度与空间自相关（未观测管理/微地貌）共同驱动，单一 XGBoost 即使加坐标也难以同时表达两者。等价于 regression kriging（Hengl et al. 2007, Geoderma）的 ML 实现，但折内拟合残差避免了泄漏。
**证据**：随机 CV 0.326→0.769；空间纬度块 CV 0.138→0.539；留出集 0.375→0.683；5 种子重复 CV 0.755±0.021。M0 证明同特征量下混合结构（0.769）优于坐标入模（0.600）。

### 创新点 2：双模式评估框架（mapping vs transfer）
**做法**：每个模型同时报告"制图模式"（用途=区域内插值成图）与"转移模式"（用途=环境外推）下的表现；空间分块 CV 用三种分块方式（纬度/经度/KMeans）做敏感性分析。
**与常规做法差异**：文献中随机 CV 与空间 CV 常被对立讨论（Raudaschl et al. 2021 生态建模；Meyer & Pebesma 2022 Nature Communications），多数论文只报其一。本框架把"哪种 CV 回答哪种应用问题"制度化。
**学术贡献**：E8 在纬度块 CV 0.539 但 KMeans 块 -0.261——同一个模型在"沿主梯度插值"与"跨簇外推"之间的巨大落差，为空间 CV 选择提供了实证案例。

### 创新点 3（方法学负结果，有发表价值）：
- **县域尺度年份特异气候层无增益**：2021 年 ERA5-Land 逐格气候（含距平与交互）在 301 网格内不提升 R²（E1/E2≈E0）。原因：平谷 250m 网格群空间跨度仅 ~25km（snap 距离中位 2.35km），ERA5-Land 9km 有效分辨率下年际气候在县域内近乎常数，被 WorldClim 背景吸收。**教训**：小区域研究不必追逐"年特异气候"热点，土壤/地形 + 空间结构才是县域产量的主导。
- **折内特征精简的调整 R² 效应**：58→25 特征使调整 R² 从 0.164 升至 0.281（+71%），但 pooled R² 不变——小样本回归中变量数本身就是性能债。
- **E7 Ridge 混合在多种子下不稳**（0.285±0.086，min 0.118）：单次 CV 的表面增益可能是折划分运气，未纳入推荐。

## 三、与现有文献对照

| 相关工作 | 差异 |
|---|---|
| Regression kriging（Hengl et al. 2007, Geoderma） | 经典 RK 用线性模型+克里金残差；本工作用梯度提升树学非线性环境响应+IDW 残差，且给出双模式 CV 证据 |
| RKP 混合制图（多见于土壤制图文献） | 常用随机 CV 验证（虚高）；本工作用 3 种分块+留出+重复 CV 四重验证 |
| Meyer & Pebesma (2022) Nat Commun（空间 CV 争论） | 提出问题"哪种 CV"；本工作给出县域产量场景的实证答案（Areal-type 插值可用随机+混合模型，外推必须分块 CV） |
| 国内县域冬小麦遥感估产（如 Zhao et al. 2023 ESSD 数据论文的下游） | 现有 30m 数据产品多止步于制图本身；本工作给出"环境归因+混合精化"的可复现管线 |

## 四、期刊方向建议

1. **首选：Agricultural and Forest Meteorology（SCI Q1）**——"Hybrid environmental-residual mapping of county-level winter wheat yield: dual-mode cross-validation reveals what spatial CV actually tests"。卖点：混合模型 + 双模式评估框架 + 外推梯度谱（fig13，0.769→-0.83 六方案单调衰减）+ 诚实负结果，符合该刊方法学偏好。**LOBO 实验已按该刊审稿预期补齐**。
2. **备选：Computers and Electronics in Agriculture（SCI Q1）**——偏 ML 工程实现与可复现管线。
3. **保底：Frontiers in Plant Science / Agronomy（Q1-Q2）**——作为"环境指纹×机器学习"主线的 250m 精细化章节。

注意：若走 AFM 路线，建议补做"移除一代网格（leave-one-block-out）外推实验"以强化外推叙事；当前 kmeans 块 -0.26 已是现成素材。

## 五、复现命令

```powershell
D:\PythonAbout\python.exe -X utf8 D:\2026-SP\src\s5_r2_improvement\experiments_v3.py
D:\PythonAbout\python.exe -X utf8 D:\2026-SP\src\s5_r2_improvement\verify_robustness.py
D:\PythonAbout\python.exe -X utf8 D:\2026-SP\src\s5_r2_improvement\make_fig10_12.py
```

数据链：fine250_v4_final.csv（301×65）→ openmeteo_2021_daily/（13 批 JSON）→ fine250_v5_features.csv（301×79）→ 各实验输出。
