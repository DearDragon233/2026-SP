# CV 台账唯一口径声明（W12-A2）

**唯一权威口径 = `review_response_diag_seeds.csv`**：
- 分块定义：纬度 4 分位块（pd.qcut(lat, q=4)）
- 模型：Optuna 调优参数（n_estimators=428, max_depth=5, lr=0.168, subsample=0.594, colsample_bytree=0.821, min_child_weight=6, reg_alpha=3.57, reg_lambda=2.69）
- 统计量：pooled R² 主口径 + 折级 mean±SD 辅助 + 3 种子（7/21/42）
- 目标：C_blend_234

**`cv_scheme_comparison.csv` 自 W12 起标记 DEPRECATED**（保留文件仅供溯源）：
- 分块定义：纬度 5 分位块（qcut q=5）——与上者不同
- 模型：轻量旧参数（200 树, lr=0.05）——与上者不同
- 统计量：折级均值为表头主列——与上者不同
- 因此其 lat_block XGB fold 0.0262±0.1474 与权威台账 0.113±0.006 **不是矛盾，是两套口径**（W12 2×2 因子实验 w12_a2_latblock_factorial.csv 证实：块定义与参数代各贡献显著差异）

**250m 线唯一口径 = `review_response_250m_seeds.csv`**（E0/E8 × 随机/纬度4块/LOBO8，3 种子）。
诊断线旧台账引用规则：论文与 README 一律引用权威口径；旧 csv 不得再被新增引用。

— 2026-09-14 W12 检查响应
