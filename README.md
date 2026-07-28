# 2026-SP — Winter Wheat × Summer Maize Breeding Model

基于环境指纹与机器学习的平谷区冬小麦-夏玉米轮作体系产量预测与管理优化

## 项目状态

- **区域:** 北京市平谷区（234个1km网格）
- **作物:** 冬小麦-夏玉米一年两熟轮作
- **品种:** 8小麦 + 8玉米 = 16品种
- **架构:** 3R+5S 双轨交叉验证（v4定稿）
- **环境指纹:** 234×73 CSV 就绪
- **阶段:** 特征工程待启动

## 仓库结构

```
2026-SP/
├── src/                              ← 源代码（按角色模块）
│   ├── r1_feature_engineering/         R1 特征工程架构师
│   ├── r2_modeling/                    R2 建模与优化工程师
│   ├── r3_shap_interpretation/         R3 模型解释与交付工程师
│   ├── s1_feature_audit/              S1 特征审计员
│   ├── s2_model_validation/           S2 模型验证员
│   ├── s5_figures_main/               S5 主体图设计师
│   ├── s6_figures_supp/               S6 附录图+规范设计师
│   └── utils/                         共享工具函数
│
├── Data/                              ← 所有源数据
│   ├── WorldClim/                     WorldClim 2.1 (43 tif, 2.5min)
│   ├── SoilGrids_wgs84/               SoilGrids 250m (8 tif, 5km)
│   ├── SRTM/                          SRTM 90m (srtm_60_04.tif)
│   ├── Management/                    管理情景CSV + Xiao2024公开数据
│   │   └── Xiao2024/                   Xiao et al.(2024) Nature Food (CC-BY-4.0)
│   ├── Variety/                       品种性状CSV (8小麦+8玉米)
│   ├── processed/                     ← 清洗/特征工程后的中间数据
│   └── external/                      其他第三方数据
│
├── Outputs/                           ← 所有产出
│   ├── pinggu_environmental_data.csv   环境指纹矩阵 (234×73)
│   ├── figures/
│   │   ├── main/                      Fig 1-7 (600 DPI TIFF)
│   │   └── supp/                      Fig S1-S12 (300 DPI PNG)
│   ├── models/                        训练好的模型 (.pkl)
│   ├── intermediate/                  中间CSV (清洗/预测/特征矩阵)
│   └── reports/                       自动生成的文字报告
│
├── ManageFiles/                       ← 项目管理文档（纯PDF+MD）
│   ├── README.md                      使用指南（从这里开始）
│   ├── 26SP_项目分工与日历_v4_3R5S.pdf
│   ├── 26SP_分工内容实现技术教程.pdf
│   ├── 26SP_参考文献精读与使用指南.pdf
│   ├── 26SP_育种模型项目技术培训手册.pdf
│   └── ...
│
├── Paper/                             ← 参考文献PDF（10篇已下载）
├── notebooks/                         ← Jupyter探索笔记本
├── config/                            ← 配置文件
│   └── style_2026sp.mplstyle          matplotlib全局风格表（S6维护）
│
├── .gitignore
├── 26SP_data_registry.json            数据注册表
└── README.md                          本文件
```

## 快速开始

1. 打开 `ManageFiles/README.md` → 按三阶段阅读
2. 确认你的角色 → 查看 `ManageFiles/26SP_项目分工与日历_v4_3R5S.pdf`
3. 打开对应 `src/<你的角色>/` 文件夹开始写代码
4. 数据在 `Data/` 下，产出放 `Outputs/`

## 环境

```bash
conda env create -f config/environment.yml   # 待创建
```

## 论文目标期刊

Primary: Journal of Integrative Agriculture (JIA, IF 4.0)
Fallback: Agronomy-Basel (IF 3.5) / PeerJ (IF 2.5)

## Coworker

见 `ManageFiles/README.md` 中的角色分配和阅读顺序
