# -*- coding: utf-8 -*-
"""重建 2026SP_发表质量整改台账.xlsx
按用户文档偏好：中文宋体/英文 Times New Roman，纯白底黑细线边框，无 AI 感彩底。
两个 sheet：① 整改台账 ② 数据台账（外部数据集）"""
import os
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, Border, Side
from openpyxl.utils import get_column_letter

OUT = r"C:\Users\18322\Desktop\2026SP_发表质量整改台账.xlsx"

wb = Workbook()

thin = Side(style="thin", color="000000")
medium = Side(style="medium", color="000000")
border = Border(left=thin, right=thin, top=thin, bottom=thin)
header_border = Border(left=thin, right=thin, top=medium, bottom=medium)

def style_sheet(ws, widths, n_rows, n_cols, header_row=1):
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w
    for r in range(1, n_rows + 1):
        for c in range(1, n_cols + 1):
            cell = ws.cell(row=r, column=c)
            cell.border = header_border if r == header_row else border
            if r == header_row:
                cell.font = Font(name="Times New Roman", bold=True, size=11)
                cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            else:
                cell.font = Font(name="Times New Roman", size=10.5)
                cell.alignment = Alignment(vertical="center", wrap_text=True)
    ws.freeze_panes = f"A{header_row+1}"

# ============ Sheet 1: 整改台账 ============
ws1 = wb.active
ws1.title = "发表质量整改台账"
rows1 = [
    ["编号", "问题（缺口）", "严重程度", "整改方案", "验证结果", "状态", "证据文件"],
    ["G1", "产量目标 82% 为空间插值，实测仅 43/234 点，模型无统计功效", "高",
     "敏感性实验：实测/插值/混合三目标对比；引入 Zenodo 2021 独立源；250m 细尺度重建（n=43→301）",
     "实测 R²≈0，插值 R²=0.98（循环验证确认）；250m 随机 CV R²=0.3225±0.1219",
     "已完成", "yield_source_sensitivity.csv; fine250_v4_results.csv; fig07"],
    ["G2", "全部 CV 为随机分折，空间自相关导致乐观偏差未量化", "高",
     "三方案 CV：随机/纬度块/棋盘，同数据同模型对比",
     "乐观偏差 +0.036~+0.088 R²；纬度块 CV 崩塌揭示南北气候梯度混杂",
     "已完成", "cv_scheme_comparison.csv; cv_optimism_gap.csv; fig05"],
    ["G3", "无预测不确定性量化", "中",
     "QRF 分位回归（10/50/90），300 树",
     "90% 名义水平 PICP=0.705，MPW=0.592 t/ha；Q50 R²=0.238",
     "已完成", "qrf_uncertainty.csv; qrf_metrics.csv; fig06"],
    ["G4", "产量仅单年（2021），无年际稳健性", "中",
     "Zenodo 2016-2020 五年份数据获取（待网络/授权）→ 跨年验证",
     "2021 年已入库并完成独立目标 CV；其余年份待获取",
     "进行中", "zenodo_cv_results.csv; external_validation_results.csv"],
    ["G5", "n=43 样本量过小，特征/样本比 0.56（闫老师诊断：严重过拟合）", "高",
     "分析尺度 3.5km→250m，样本量 43→301，特征筛选 24→14",
     "特征/样本比降至 0.046；环境信号首次可检测（R²=0.32）",
     "已完成", "fine250_v4_final.csv; fine250_v4_shap.csv"],
    ["G6", "题目承诺「预测+优化」但无玉米产量、无农艺措施数据", "高",
     "题目转为诊断型：环境指纹能否解释产量变异（037691d 已确认）",
     "大纲 v3.0 十章结构完成；Title 已定稿",
     "已完成", "Paper/Outline_v3.0_diagnostic.md"],
]
for r in rows1:
    ws1.append(r)
style_sheet(ws1, [6, 34, 8, 38, 36, 8, 34], len(rows1), 7)
for r in range(2, len(rows1) + 1):
    ws1.row_dimensions[r].height = 52

# ============ Sheet 2: 数据台账 ============
ws2 = wb.create_sheet("数据台账（外部数据集）")
rows2 = [
    ["编号", "数据集", "来源（链接已核验 2026-09-14）", "许可", "分辨率", "覆盖年份", "获取方式", "获取时间", "状态"],
    ["EXT-1", "ChinaWheatYield30m", "Zenodo 10.5281/zenodo.7360753；论文 DOI 10.5194/essd-15-4047-2023（Zhao et al. 2023, ESSD 15, 4047-4063）", "CC-BY-4.0", "30m", "2016-2021", "Zenodo 网页下载（API 被 403 拦截）", "2026-09-12", "2021 年已入库（1088MB）；2016-2020 待获取"],
    ["EXT-2", "Xiao2024 实测产量", "课题组内部数据", "内部使用", "3.5km 网格", "2021", "项目内置", "2026-07", "已入库（43 点实测 + 234 点预测）"],
    ["EXT-3", "WorldClim 2.1", "https://www.worldclim.org/data/worldclim21.html", "CC-BY-SA 4.0", "2.5 弧分", "1970-2000 均值", "官网下载", "2026-07", "已入库（bio1-19 + 月值 tavg/prec）"],
    ["EXT-4", "SoilGrids 250m", "https://soilgrids.org/（ISRIC）", "CC-BY-4.0", "250m/5000m", "当前", "官网下载", "2026-07", "已入库（8 项土壤理化；CRS=ESRI:54052 需投影转换）"],
    ["EXT-5", "SRTM DEM", "https://earthexplorer.usgs.gov/", "公共领域", "30m", "—", "官网下载", "2026-07", "已入库（srtm_60_04，高程/坡度/朝向）"],
    ["EXT-6", "中国冬小麦分布图", "Li et al. 2026, Scientific Data / PMC", "待确认", "30m", "2000-2024", "PMC 论文附录（获取前需确认许可）", "未获取", "可用于麦田掩膜精化"],
]
for r in rows2:
    ws2.append(r)
style_sheet(ws2, [7, 20, 46, 12, 10, 14, 26, 12, 30], len(rows2), 9)
for r in range(2, len(rows2) + 1):
    ws2.row_dimensions[r].height = 40

os.makedirs(os.path.dirname(OUT), exist_ok=True)
wb.save(OUT)
print("saved:", OUT, "|", os.path.getsize(OUT), "bytes")
