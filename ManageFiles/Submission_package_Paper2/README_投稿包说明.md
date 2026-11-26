# 论文 2 投稿包 — Agronomy (MDPI)

> 2026-11-26。按用户指示：**闫老师暂不署名、作者列表暂不声明**——本包只含论文本体与投稿 Agronomy 所需的技术材料。
> 状态：论文本体 v1.0 完成；全文 50/50 数字声明通过台账审计；五幅主图按投稿标准重绘。

## 一、论文本体

| 文件 | 说明 |
|---|---|
| [Manuscript_v1.0_Prediction_Level_and_Pattern.md](../../Paper/Manuscript_v1.0_Prediction_Level_and_Pattern.md) | 投稿主稿源文件（摘要/引言/方法/结果/讨论/结论/数据可用性/图注/5 表/16 条参考文献） |
| [Manuscript_v1.0_Prediction_Agronomy_format.pdf](../../Paper/Manuscript_v1.0_Prediction_Agronomy_format.pdf) | 排版版（Agronomy 单栏体例，11 页，图随文嵌入，作者位留空） |
| [Cover_letter.md](Cover_letter.md) | 致编辑信（作者/通讯信息留空待填） |

**题目**：Level and Pattern in Transferred County Wheat Yield Models: Weather Features, Training Labels and a Training-Mean Baseline Across Three North China Regions

**核心主张**（摘要级）： pooled MAE 把"区域产量水平"和"县内排序"两种能力混在一起；分离后，模型排名会变。20 个模型臂中原始优势与去水平优势符号一致 12 个、不一致 8 个。建议县级迁移研究分别报告水平误差与县内排序技能，并保留训练均值基线。

## 二、图表（投稿编号，600 dpi）

| 编号 | 文件 | 内容 |
|---|---|---|
| Figure 1 | `figures/Figure1_zhoukou_coverage.png` | 周口 8 县边界 + 覆盖比筛查（24 县年） |
| Figure 2 | `figures/Figure2_label_swap_development.png` | 冻结面板 label-swap（三方案 × 两标签 × 三模型） |
| Figure 3 | `figures/Figure3_level_pattern_zhoukou.png` | 周口水平-格局分解（散点负相关 + 重定心前后优势） |
| Figure 4 | `figures/Figure4_rank_skill_20arms.png` | 20 臂格局相关森林图（置换 p、bootstrap CI） |
| Figure 5 | `figures/Figure5_sixyear_pattern.png` | 六年卫星格局相关矩阵 |

表格（正文内）：Table 1 开发面板 MAE；Table 2 开发面板分解；Table 3 外部测试；Table 4 符号一致性；Table 5 claim-to-ledger 映射。

## 三、证据台账（每个数字的出处）

- 开发面板：`w44_frozen_panel.csv`、`w44_folds.csv`、`w45_primary_metrics.csv`、`w45_primary_oof.csv`
- 偏移校正：`w46_offset_diagnostic.csv`
- 平顶山：`w48_pds_frozen.csv`、`w49_pds_oof.csv`、`w49_pds_primary_metrics.csv`、`w50_pds_paired_differences.csv`
- 周口：`w53_zhoukou_coverage.csv`、`w53_zhoukou_frozen_external.csv`、`w53_zhoukou_external_scores.csv`、`w54_zhoukou_oof.csv`、`w54_zhoukou_deletion_ranges.csv`、`w54_zhoukou_county_bias.csv`、`w54_zhoukou_decomposition.json`
- 全站分解与检验：`w54_level_pattern_decomposition_all_sites.csv`、`w54_pattern_permutation_tests.csv`
- 对照臂：`w53_r6_control_arm.json`
- 六年矩阵：`w37_pattern_matrix.csv`、`w37_sixyear_grid.csv`
- 审计脚本：`scratch/audit_paper2.py`（50/50 PASS）

## 四、投稿前待办（作者侧）

| # | 事项 | 状态 |
|---|---|---|
| 1 | 作者列表、单位、通讯作者 | ⬜ 按指示暂不声明 |
| 2 | 闫老师署名与编委 APC 减免 | ⬜ 按指示暂不署名；**注意：不署名则减免路径不适用**，APC 约 2,600 CHF 需另行安排（CAU 的 IOAP 10% 折扣仍可用） |
| 3 | MDPI 声明节（Funding / Author Contributions / Conflicts / IRB） | ⬜ 依赖 #1 |
| 4 | 参考文献终核 | ⚠️ 已核 6/7/13/15 四条；其余 12 条沿用论文 1 已核实文献，投稿前建议整表再过一遍 DOI |
| 5 | 配套诊断论文（ref 14）的引用信息 | ⚠️ 当前为 "Manuscript in preparation"，投稿前改为预印本或正式引用 |
| 6 | 英文润色（humanizer 模式扫描） | ⬜ 可选 |

## 五、诚实声明（审稿人可能追问的点）

1. **平顶山格局技能（r=0.90）基于 n=9**，bootstrap CI [0.23, 0.98] 很宽——正文已明确写成"假说"而非结论；
2. **周口"成功"被分解实验推翻**——初稿曾写"模型迁移出真实技能"，经水平/格局分解后更正为"完全是水平效应、县际排序反向"；W51 草稿旧版已同步改写；
3. **Table 4 计数曾写错**（凭印象 11/9，台账实为 12/8），已由程序化审计抓出并修正；
4. **参考文献曾有三处错误**（ref 6 标题与内容、ref 7 第一作者、ref 13 不确定的文献），已核实更正；
5. 外部测试仅覆盖河南两个地市；天气序列粗（周口 8 县仅 7 条）；无站点级实测。
