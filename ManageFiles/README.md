# 2026-SP 项目管理文件使用指南 v2

写给coworker的项目管理文件阅读指南。路径：`D:\2026-SP\ManageFiles\`

---

## 核心原则

本文件夹汇总了2026-SP育种模型项目的全部管理、参考和指南文档。数据文件、代码脚本、实际产出不在此处（分别在 `Data/`、`src/`、`Outputs/` 路径下）。

## 仓库快速导航

| 你要做什么 | 去哪里 |
|------|------|
| 了解项目全貌 | 本文件（按三阶段阅读） |
| 开始写代码 | `src/<你的角色代号>/` |
| 找数据 | `Data/` → 各子文件夹 |
| 存放产出 | `Outputs/` → figures/models/intermediate/reports |
| 探索分析 | `notebooks/` |
| 配置环境 | `config/` |
| 读论文原文 | `Paper/`（10篇PDF已下载） |

## 源代码文件夹 (src/)

```
src/
├── r1_feature_engineering/    ← 特征工程（数据清洗→构建→降维→筛选）
├── r2_modeling/               ← 建模优化（基线→集成→Optuna→QRF→NSGA-II）
├── r3_shap_interpretation/    ← 模型解释（SHAP→Bootstrap→打包交付）
├── s1_feature_audit/          ← 独立审计R1
├── s2_model_validation/       ← 独立验证R2
├── s5_figures_main/           ← Fig 1-7（600 DPI TIFF）
├── s6_figures_supp/           ← Fig S1-S12（300 DPI PNG）+ 风格表
└── utils/                     ← 共享工具（空间函数、绘图辅助等）
```

每个 `src/` 子文件夹内有 `.gitkeep`，提交代码后自动消失。脚本按数字前缀排序命名（如 `01_clean_data.py`、`02_engineer_features.py`）。

## 输出文件夹 (Outputs/)

```
Outputs/
├── pinggu_environmental_data.csv    ← 环境指纹矩阵 (234×73)
├── figures/
│   ├── main/                        ← S5产出：Fig 1-7 (600 DPI TIFF)
│   └── supp/                        ← S6产出：Fig S1-S12 (300 DPI PNG)
├── models/                          ← 训练好的模型文件 (.pkl)
├── intermediate/                    ← 中间CSV（清洗后数据、特征矩阵、预测结果）
└── reports/                         ← 自动生成的文字报告
```

## 配置文件 (config/)

- `style_2026sp.mplstyle` — matplotlib全局风格表（S6维护，S5和S6共同引用）
- `environment.yml` — 待创建，conda环境声明

## 项目当前状态 (2026-07-28)

- **研究区域：** 北京市平谷区（234个1km网格）
- **作物体系：** 冬小麦-夏玉米一年两熟轮作
- **品种数据：** 8小麦 + 8玉米 = 16品种（全部文献提取）
- **环境数据：** 234x73 CSV 就绪（WorldClim + SoilGrids + SRTM）
- **管理数据：** 两套来源
  - 自主设计14情景（基于Chen 2014 Nature + Bai 2024 Nature Food）
  - Xiao et al.(2024) Nature Food Figshare公开数据（CC BY 4.0，已下载4文件61 MB）
- **参考文献：** 34篇精读指南 + 10篇OA论文PDF已下载
- **项目架构：** 3R+5S 双轨交叉验证（v4定稿）
- **下一步：** 启动特征工程R1和S1审计

---

## 推荐阅读顺序

### 第一轮：了解项目（必读，约1小时）

| 顺序 | 文件 | 内容 | 篇幅 |
|:--:|------|------|:--:|
| 1 | 26SP_项目分工说明_v4_3R5S.docx | 3R+5S架构、角色职责、17天日程、里程碑 | 52 KB |
| 2 | 26SP_分工说明及实现教程.docx | 每人从零到实现完整教程，含方法选择对比 | 68 KB |
| 3 | 26SP_参考文献精读与使用指南.docx | 34篇文献精读+按论文段落引用索引 | 53 KB |

### 第二轮：深入技术（按角色选读）

| 角色 | 必读文件 | 辅助文件 |
|------|------|------|
| R1 特征工程 | 实现教程第2-3章 | 模型数据清单与技术答疑 |
| R2 建模优化 | 实现教程第3章 | 技术培训手册（模型部分） |
| R3 模型解释 | 实现教程第4章 | 技术培训手册（SHAP部分） |
| S1 特征审计 | 实现教程第5章 | 模型数据清单与技术答疑 |
| S2 模型验证 | 实现教程第5章 | 技术培训手册 |
| S4 论文写作 | 参考文献精读与使用指南（全文） | Xiao et al.(2024)原文 |
| S5 主体图 | 可视化全案设计 | 实现教程第6章 |
| S6 附录图 | 可视化全案设计 | 实现教程第6章 |

### 第三轮：备查参考

| 文件 | 什么时候看 |
|------|------|
| 26SP_育种模型项目技术培训手册.docx (1.2 MB) | 深入理解决策树/XGBoost/SHAP/Bootstrap原理 |
| 26SP_模型数据清单与技术答疑.docx (75 KB) | 确认数据维度获取状态 |
| 26SP_README_AI_CODING_GUIDE.md (11 KB) | AI协作编程提示词和流程 |
| 数据来源与获取记录.md | 各数据源下载方法 |
| 数据获取状态清单.docx | 65个数据维度的逐项状态 |
| 26SP_数据检查清单_v2.0.xlsx | 数据维度Excel检查表 |

---

## ManageFiles 完整文件清单 (15个文件, ~3.3 MB)

```
ManageFiles/
├── 📖 核心指导文档
│   ├── 26SP_项目分工说明_v4_3R5S.docx       (52 KB)  分工架构+日程+里程碑
│   ├── 26SP_项目分工说明_v4_3R5S.pdf        (151 KB) 同上PDF版
│   ├── 26SP_分工说明及实现教程.docx          (68 KB)  从零到实现完整教程
│   ├── 26SP_参考文献精读与使用指南.docx       (53 KB)  34篇文献精读+引用索引
│   └── 26SP_参考文献精读与使用指南.pdf        (241 KB) 同上PDF版
│
├── 📊 数据与清单
│   ├── 26SP_模型数据清单与技术答疑.docx       (75 KB)  数据清单+Coworker问答
│   ├── 26SP_模型数据清单与技术答疑.pdf        (303 KB) 同上PDF版
│   ├── 数据获取状态清单.docx                         65维度逐项状态
│   ├── 数据来源与获取记录.md                           各数据源下载方法
│   └── 26SP_数据检查清单_v2.0.xlsx                   数据维度Excel表
│
├── 🛠️ 技术手册与指南
│   ├── 26SP_育种模型项目技术培训手册.docx     (1.2 MB) 决策树→XGBoost→SHAP全链条
│   ├── 26SP_模型项目技术手册.pdf             (959 KB) 项目技术手册PDF
│   ├── 26SP_模型须知与AI编程指南.pdf         (207 KB) AI编程指南PDF
│   ├── 26SP_AIcoding指导.docx               (53 KB)  AI协作编程Word版
│   └── 26SP_README_AI_CODING_GUIDE.md        (11 KB)  AI协作编程Markdown版
│
├── 📦 历史版本（存档）
│   ├── 26SP_项目分工_v3_3R5S双轨验证.docx            v3版本（已被v4替代）
│   └── 26SP_项目分工与工作日程.docx                   v2版本（已被v4替代）
│
└── README.md                               (5 KB)   本文档
```

---

## 数据文件位置（非ManageFiles）

| 类型 | 路径 |
|------|------|
| 环境指纹CSV | `Outputs/pinggu_environmental_data.csv` (234x73) |
| 冬小麦品种性状 | `Data/Variety/Variety_Wheat_Traits.csv` (8品种) |
| 夏玉米品种性状 | `Data/Variety/Variety_Maize_Traits.csv` (8品种) |
| 自主管理情景 | `Data/Management/management_scenarios.csv` (14情景) |
| 默认管理参数 | `Data/Management/management_grid_default.csv` (234网格) |
| Xiao 2024管理数据 | `Data/Management/Xiao2024/` (4文件, 61 MB, CC-BY-4.0) |
| 气候TIFF | `Data/WorldClim/` (47 tif) |
| 土壤TIFF | `Data/SoilGrids_wgs84/` (8 tif) |
| 地形TIFF | `Data/SRTM/` (srtm_60_04.tif) |
| 参考文献PDF | `Paper/` (10篇已下载, 17 MB) |
| 数据注册表 | `26SP_data_registry.json` |
| Python脚本 | `D:\2026-SP-Scripts\` (11个脚本) |

---

## Xiao et al. (2024) 管理数据说明

**来源：** Xiao et al. (2024) "Spatiotemporal co-optimization of agricultural management practices" *Nature Food* 5:59-71

**获取方式：** Figshare 公开数据集 (DOI: 10.6084/m9.figshare.24471919.v5)

**许可证：** CC BY 4.0 — 完全公开，无需申请，使用时标注来源即可

**已下载文件：**

| 文件 | 大小 | 内容 |
|------|:--:|------|
| Allregions.rds | 57.3 MB | 完整管理数据集（R格式） |
| N_ref.tif | 1.3 MB | 基准期施氮量（1km） |
| Irrigation_ref.tif | 1.4 MB | 基准期灌溉量 |
| WheatYield_ref.tif | 1.3 MB | 基准期小麦产量 |

**注意事项：**
- Allregions.rds 需R语言读取（`readRDS()`），建议转换为CSV供Python使用
- Figshare主站（figshare.com）国内被墙，但ndownloader.figshare.com数据通道通畅
- 此数据覆盖小麦和玉米两季，与我们的轮作体系完全匹配

---

## 更新记录

- 2026-07-28: 创建ManageFiles文件夹，统一26SP_前缀命名
- 2026-07-28: 三份核心文档去AI化（移除·符号、优化表格10pt+深蓝表头）
- 2026-07-28: 散落文件集中（v2/v3存档、数据清单、操作手册）
- 2026-07-28: 新增玉米品种数据（8品种）、Xiao 2024管理数据下载
- 2026-07-28: README v2更新 — 轮作体系说明、文件清单重组、Xiao数据说明
