# 2026-SP 重构版 README

# 环境指纹能否解释区域产量变异？| Can Environmental Fingerprints Explain Regional Yield Variability?

> 系统性诊断空间产量建模中的循环验证与乐观偏差 —— 以北京平谷区 234 网格冬小麦为例
>
> **在线工具**: [桃园农事气象助手](https://taoyuan-weather.pages.dev/) (实践延伸)
> **License**: MIT

[![Status](https://img.shields.io/badge/Status-Manuscript_in_prep-yellow)]()
[![Target](https://img.shields.io/badge/Target-Agronomy%20%2F%20Field_Crops_Res-green)]()
[![Data](https://img.shields.io/badge/Data-Open--Meteo%20%2B%20WorldClim%20%2B%20SoilGrids-blue)]()

## 核心发现（三句话版本）

1. **随机 CV 比空间分块 CV 虚高 R² 0.036-0.088**——空间自相关导致的乐观偏差被量化证实
2. **以空间插值产量为目标的模型 R²=0.98，但以实测产量为目标的 R²≈0**——循环验证被直接暴露
3. **独立数据源（ChinaWheatYield30m 2021）确认环境变量在 3.5km 尺度不解释真实产量变异**

## 项目结构

```
2026-SP/
├── Paper/                    # 论文大纲、核心文献 PDF
│   └── Outline_v3.0_diagnostic.md  # 当前大纲（诊断型重构版）
├── Data/                     # 原始数据（Xiao2024 等）
├── Outputs/
│   ├── pinggu_environmental_data.csv  # 原始环境矩阵
│   ├── figures/main/         # 出版级图表（fig01-07, 600dpi png+tiff）
│   ├── figures/qa/           # 质量审计图（qa01-06）
│   ├── figures/supp/         # 补充图
│   ├── intermediate/         # 中间表（筛选结果/CV对比/QRF/敏感性）
│   └── reports/              # 补强报告 (docx+html)
├── src/
│   ├── s1_feature_audit/     # 特征审计管线
│   ├── s2_county_yield/      # 区级产量整合（贝叶斯融合）
│   ├── s2_model_validation/  # ★ 本轮补强：advance_validation.py + zenodo_cv.py
│   ├── s1_feature_audit/     # 质量评估与图表重生成
│   └── r2_modeling/          # 原始建模管线（W1-3）
└── config/                   # 配置
```

## 一键复现

```bash
# 环境: Python 3.13 + pandas/numpy/sklearn/xgboost/lightgbm/quantile-forest/shap/rasterio
cd src/s2_model_validation
python advance_validation.py   # G1+G2+G3 全部实验 (~10min)
python zenodo_cv.py            # 独立数据源验证 (~2min)
```

## 关键数据

| 文件 | 内容 |
|---|---|
| `cv_scheme_comparison.csv` | 3 CV 方案 × 3 模型的 R²/RMSE |
| `cv_optimism_gap.csv` | 随机 CV 相对空间 CV 的乐观偏差 |
| `qrf_uncertainty.csv` | 234 网格 Q10/Q50/Q90 逐格区间 |
| `yield_source_sensitivity.csv` | 四产量目标 × 三模型性能矩阵 |
| `zenodo_cv_results.csv` | 独立数据源（ChinaWheatYield30m）CV 结果 |

## 团队

- **彭宇程**（未来技术学院强基计划）— 项目设计、数据管线、论文
- 其余 3 人分工待定

## 致谢

Open-Meteo（气象数据）、WorldClim/SoilGrids/SRTM（环境变量）、Zhao et al. 2023 ESSD（ChinaWheatYield30m）、北京市统计局。
