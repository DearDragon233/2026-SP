# -*- coding: utf-8 -*-
"""生成数据字典 CSV + 最终 HTML 报告（Stamen 大地数据图谱风格）"""
import pandas as pd, numpy as np, json, os

ROOT = r"D:\2026-SP"
INT = os.path.join(ROOT, "Outputs", "intermediate")
DESK = r"C:\Users\18322\Desktop"
REP = os.path.join(ROOT, "Outputs", "reports")
os.makedirs(REP, exist_ok=True)

m = pd.read_csv(os.path.join(INT, "augmented_yield_master_v2.csv"), low_memory=False)
qa = json.load(open(os.path.join(INT, "data_quality_report.json"), encoding="utf-8"))
vt = json.load(open(os.path.join(INT, "verification_tests.json"), encoding="utf-8"))

# ================= 数据字典 =================
new = m[m["source_batch"] == "Xiao2024_rds_History"]
base = m[m["source_batch"] == "Baseline_234grid"]

groups = {
    "标识": {"gridcell": "Xiao2024 rds 1km 网格编号（NCP 1320 列行主序，基线行为空）",
            "lon": "经度（°，EPSG:4326，网格左上角起算 112.1 + col×0.0083333）",
            "lat": "纬度（°，40.7 - row×0.0083333）",
            "source_batch": "来源批次：Baseline_234grid | Xiao2024_rds_History",
            "license": "数据许可（新增行全部 CC BY 4.0）"},
    "产量与管理（Xiao2024 增量）": {
        "Yield": "优化产量（t/ha，轮作体系冬小麦+夏玉米两熟合计，History 基准期）",
        "New_Yield": "二次优化产量（t/ha，含减排约束）",
        "WN": "优化施氮量（kg/ha，冬小麦季）",
        "MN": "优化施氮量（kg/ha，夏玉米季）",
        "xWIrri": "优化灌溉量（mm，冬小麦季）",
        "xMIrri": "优化灌溉量（mm，夏玉米季）",
        "WR": "冬小麦季降雨（mm，模式集合平均）",
        "MR": "夏玉米季降雨（mm）",
        "CO2": "CO2 浓度（ppm，随 SSP 情景；History=375.82）",
        "SAT_1": "土壤饱和度（分数）",
        "BD_1": "土壤容重（g/cm³）",
        "SOC_1": "土壤有机碳（%）",
        "PH_1": "土壤 pH",
    },
    "环境-气候（WorldClim 2.1，气候背景）": {
        **{f"bio_{i}": f"生物气候变量 bio{i}（19 环，WorldClim 2.1 2.5 弧分≈5km；温度项×10 或标准单位）"
           for i in range(1, 20)},
        **{f"tavg_{i:02d}": f"{i} 月平均气温（°C×10）" for i in range(1, 13)},
        **{f"prec_{i:02d}": f"{i} 月降水量（mm）" for i in range(1, 13)},
    },
    "环境-土壤（SoilGrids 2.0，0-5cm）": {
        **{f"sg_{k}": v for k, v in {
            "bdod": "容重（kg/dm³）", "cec": "阳离子交换量（mmol(c)/kg）",
            "clay": "黏粒（g/kg）", "nitrogen": "全氮（g/kg）【源文件损坏，本轮缺口】",
            "ph": "pH×10", "sand": "砂粒（g/kg）", "silt": "粉粒（g/kg）",
            "soc": "土壤有机碳（g/kg，dg/kg×10）"}.items()},
    },
    "地形": {
        "elev_m": "高程（m；SRTM 90m 南部 + WorldClim elev 兜底北部【本轮 SRTM 图幅缺口】）",
        "slope_deg": "坡度（°，仅基线 234 行有）",
        "aspect_deg": "坡向（°，仅基线行）",
    },
    "基线行专用（234 网格）": {
        "yield_2021_tha": "2021 实测/融合产量（t/ha，仅基线行）",
        "xiao_wheatyield": "Xiao WheatYield_ref.tif 参考产量（t/ha，38/234 有效）",
        "xiao_n": "Xiao N_ref.tif 参考施氮（kg/ha）",
        "xiao_irrigation": "Xiao Irrigation_ref.tif 参考灌溉（mm）",
    },
}
rows = []
def unit_of(c):
    if "Yield" in c: return "t/ha"
    if c in ("WN", "MN", "xiao_n"): return "kg/ha"
    if "Irri" in c or c.startswith("prec") or c in ("WR", "MR", "xiao_irrigation"): return "mm"
    if c.startswith("tavg"): return "°C×10"
    if c in ("lon", "lat", "slope_deg", "aspect_deg"): return "°"
    return "—"
for g, cols in groups.items():
    for c, desc in cols.items():
        in_m = c in m.columns
        if in_m:
            if c in ("source_batch", "license"):
                cov = "100%"
            elif c in new.columns and not new[c].dropna().empty:
                cov = f"新增行 {new[c].notna().mean()*100:.0f}%"
            else:
                cov = "—"
            rows.append({"字段组": g, "字段名": c, "说明": desc, "新增行覆盖率": cov,
                         "单位": unit_of(c)})
dd = pd.DataFrame(rows)
dd_path = os.path.join(REP, "data_dictionary_augmented_master.csv")
dd.to_csv(dd_path, index=False, encoding="utf-8-sig")
print("data dictionary:", dd_path, dd.shape)

# ================= 台账 CSV =================
ledger = pd.DataFrame([
    ["BATCH-01", "平谷基线 234 网格（环境指纹 73 变量 + 实测/融合产量）", "课题组自建 + Xiao2024 Figshare (DOI 10.6084/m9.figshare.24471919.v5)", "CC BY 4.0（外部部分）", "2026-07", "项目内置", "234 行", "基线，未改动"],
    ["BATCH-02", "Xiao2024 Allregions.rds 平谷子集（History 基准期）", "D:\\2026-SP\\Data\\Management\\Xiao2024\\Allregions.rds；源自 Xiao et al. 2024 Nature Food 5:59-71，Figshare DOI 10.6084/m9.figshare.24471919.v5", "CC BY 4.0，允许学术使用与再分发，无需申请", "2026-09-14（本轮从本地库存解析）", "pyreadr 0.5.6 解析 + gridcell→经纬度行主序映射（NCP 1320 列，经 67876→117.7E/40.3N 验证）", "1552 行（1552 个 1km 网格×1 行基准期）", "已入库主数据集"],
    ["BATCH-03", "Xiao2024 Allregions.rds 平谷子集（2030s/2060s 情景）", "同 BATCH-02", "CC BY 4.0", "2026-09-14", "同上；6 GCM×2 SSP 展开", "37248 行（情景数据，单独存放不混入主表）", "已入库（独立情景文件）"],
    ["BATCH-04", "Xiao2024 三个 1km 参考图层（WheatYield/N/Irrigation_ref.tif）", "同上目录", "CC BY 4.0", "2026-09-14", "rasterio 点采样 234 网格", "234 行×3 列（38 网格有效产量）", "已入库主数据集"],
    ["BATCH-05", "WorldClim 2.1 bio19+月值（1552 点采样）", "D:\\2026-SP\\Data\\WorldClim\\wc2.1_2.5m_*（官网 worldclim.org，CC BY-SA 4.0）", "CC BY-SA 4.0（由 WorldClim 授权再分发）", "2026-09-14（本轮采样）", "rasterio 逐点采样，1552/1552 全覆盖", "50 列×1552 行", "已入库"],
    ["BATCH-06", "SoilGrids 2.0 0-5cm 7 项（1552 点采样）", "D:\\2026-SP\\Data\\SoilGrids_wgs84\\*_0-5cm_mean_5000.tif（ISRIC soilgrids.org，CC BY 4.0）", "CC BY 4.0", "2026-09-14", "rasterio+pyproj 投影采样（ESRI:54052→4326）；nitrogen.tif 源文件损坏未入库", "7 列×1552 行（73% 覆盖）", "已入库（缺 nitrogen，见缺口登记）"],
], columns=["批次号", "数据内容", "来源", "许可", "获取/处理时间", "处理方式", "规模", "状态"])
ledger_path = os.path.join(REP, "data_ledger_20260914.csv")
ledger.to_csv(ledger_path, index=False, encoding="utf-8-sig")
print("ledger:", ledger_path)

# ================= HTML 报告（Stamen 大地数据图谱） =================
# 关键数字
n_base, n_new, n_total = len(base), len(new), len(m)
mult = n_total / n_base
r_cross = qa["cross_source"]["pearson_r"]
r2s = vt["smoke_cv_r2"]

def esc(s): return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

# 简易条形图数据（HTML bar）
env_cov = {
    "气候（bio+月值 50 列）": 100.0, "产量与管理（13 列）": 100.0,
    "土壤（sg_* 7 列）": 73.3, "地形（elev_m）": 57.6, "土壤 nitrogen": 0.0,
}
bars = "".join(
    f'<div class="bar-row"><div class="bar-label">{esc(k)}</div>'
    f'<div class="bar-track"><div class="bar-fill" style="width:{v}%"></div></div>'
    f'<div class="bar-val">{v:.0f}%</div></div>' for k, v in env_cov.items())

html = f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>2026-SP 数据补强报告 · 大地数据图谱</title>
<style>
:root {{
  --paper:#f4f0e6; --ink:#2b2a24; --muted:#7a7466; --hair:#d8d2c2;
  --sage:#5e7d5a; --terra:#b5623b; --deepblue:#2d4a63;
}}
* {{ box-sizing:border-box; margin:0; padding:0; }}
body {{ font-family:Georgia,"Times New Roman","Songti SC","SimSun",serif;
  background:var(--paper); color:var(--ink); line-height:1.7; padding:40px 20px; }}
.page {{ max-width:1000px; margin:0 auto; }}
header {{ border-bottom:2px solid var(--ink); padding-bottom:24px; margin-bottom:8px; }}
.kicker {{ font-family:Verdana,sans-serif; font-size:11px; letter-spacing:0.14em;
  text-transform:uppercase; color:var(--sage); margin-bottom:10px; }}
h1 {{ font-size:34px; line-height:1.25; font-weight:600; letter-spacing:-0.01em; }}
.sub {{ color:var(--muted); margin-top:10px; font-size:15px; }}
h2 {{ font-size:21px; margin:44px 0 6px; padding-top:20px; border-top:1px solid var(--hair); font-weight:600; }}
h2 .no {{ color:var(--terra); font-size:13px; font-family:Verdana,sans-serif; letter-spacing:0.1em; display:block; margin-bottom:4px; }}
p {{ margin:10px 0; font-size:15.5px; max-width:72ch; }}
.lede {{ font-size:18px; line-height:1.65; margin:18px 0; }}
.metrics {{ display:grid; grid-template-columns:repeat(4,1fr); gap:0; border-top:2px solid var(--ink);
  border-bottom:1px solid var(--hair); margin:26px 0; }}
.metric {{ padding:16px 14px; border-right:1px solid var(--hair); }}
.metric:last-child {{ border-right:none; }}
.metric .v {{ font-size:30px; font-weight:600; color:var(--deepblue); letter-spacing:-0.01em; }}
.metric .v em {{ font-style:normal; font-size:15px; color:var(--terra); }}
.metric .k {{ font-family:Verdana,sans-serif; font-size:10.5px; letter-spacing:0.1em;
  text-transform:uppercase; color:var(--muted); margin-top:4px; }}
table {{ width:100%; border-collapse:collapse; font-size:13.5px; margin:14px 0; }}
th {{ font-family:Verdana,sans-serif; font-size:11px; letter-spacing:0.08em; text-transform:uppercase;
  text-align:left; color:var(--muted); border-bottom:2px solid var(--ink); padding:8px 10px; }}
td {{ border-bottom:1px solid var(--hair); padding:8px 10px; vertical-align:top; }}
tr.hl td {{ background:#ece7d8; }}
.bar-row {{ display:grid; grid-template-columns:200px 1fr 52px; gap:12px; align-items:center; margin:7px 0; }}
.bar-label {{ font-size:13.5px; text-align:right; color:var(--ink); }}
.bar-track {{ background:#e7e1d1; height:14px; }}
.bar-fill {{ background:var(--sage); height:100%; }}
.bar-fill.low {{ background:var(--terra); }}
.bar-val {{ font-size:13px; color:var(--muted); font-family:Verdana,sans-serif; }}
.note {{ border-top:1px solid var(--hair); border-bottom:1px solid var(--hair);
  padding:14px 4px; margin:20px 0; font-size:14px; color:var(--muted); }}
.note b {{ color:var(--ink); }}
.foot {{ margin-top:50px; padding-top:16px; border-top:2px solid var(--ink);
  font-family:Verdana,sans-serif; font-size:11px; color:var(--muted); letter-spacing:0.06em; }}
.two {{ display:grid; grid-template-columns:1fr 1fr; gap:28px; }}
@media (max-width:720px) {{ .metrics {{ grid-template-columns:repeat(2,1fr); }}
  .two {{ grid-template-columns:1fr; }} h1 {{ font-size:26px; }} }}
</style></head><body><div class="page">

<header>
<div class="kicker">2026-SP · Data Augmentation Report · 2026-09-14</div>
<h1>平谷产量数据补强：{mult:.1f}× 基线，全部免授权公开数据</h1>
<div class="sub">以 <b>26SP 项目大纲</b>为基准恢复原题目「冬小麦-夏玉米轮作体系 环境指纹×机器学习育种模型」——夏玉米数据暂缓，产量数据主补强，许可零障碍</div>
</header>

<div class="metrics">
<div class="metric"><div class="v">{n_total:,}</div><div class="k">总记录（行）</div></div>
<div class="metric"><div class="v">{n_base} <em>+{n_new:,}</em></div><div class="k">基线 + 新增</div></div>
<div class="metric"><div class="v">{mult:.1f}<em>×</em></div><div class="k">数据量倍数</div></div>
<div class="metric"><div class="v">100<em>%</em></div><div class="k">新增免授权占比</div></div>
</div>

<p class="lede">核心动作：解析本地已存库的 <b>Xiao et al. 2024（Nature Food 5:59-71，CC BY 4.0）</b>核心数据 Allregions.rds（1110 万行全国 1km 网格），通过 gridcell 行主序映射反算经纬度，命中平谷 <b>1,552 个 1km 网格</b>，提取基准期优化产量、施氮、灌溉与土壤协变量；再在 1,552 个网格位置采样 WorldClim（50 列）与 SoilGrids（7 列）环境栅格，形成字段对齐、来源可追溯的合并主数据集。产量数据占新增字段与行数的主体，符合「以作物产量数据为主要补充」的要求。</p>

<h2><span class="no">01</span>数据量翻倍核对</h2>
<table>
<tr><th>项目</th><th>记录数</th><th>说明</th></tr>
<tr><td>基线（BATCH-01）</td><td>{n_base}</td><td>234 个 3.5km 网格，含实测 43 点+融合产量</td></tr>
<tr class="hl"><td>新增（BATCH-02）</td><td>{n_new:,}</td><td>Xiao2024 基准期 1km 网格，优化产量+全套管理变量</td></tr>
<tr><td><b>合计主数据集</b></td><td><b>{n_total:,}</b></td><td><b>{mult:.1f}× 基线</b>（验收要求 ≥2×，达标）；另有 37,248 行情景数据单独存放</td></tr>
</table>

<h2><span class="no">02</span>产量数据占比（主要增量判定）</h2>
<p>新增 {n_new:,} 行全部为「产量+管理」记录：每行含优化产量（Yield、New_Yield）、双季施氮（WN/MN）、双季灌溉（xWIrri/xMIrri）及土壤水分常数协变量——产量相关字段 6/13 列核心列，行数占比 <b>100%</b>（本轮只做产量端补强，未引入其他主题数据）。作物类型为冬小麦-夏玉米轮作体系（基准期产量为两熟合计），覆盖平谷全区 1km 连续网格。</p>

<h2><span class="no">03</span>环境特征覆盖率（质量体检）</h2>
<div style="margin:16px 0">{bars}</div>
<p>缺失率核查：<b>目标与管理列 0% 缺失</b>、气候列 0% 缺失；异常值核查：新增产量 14.89-16.37 t/ha，3σ 与 IQR 判定均为 <b>0 个异常值</b>；单位统一：产量 t/ha、施氮 kg/ha、灌溉 mm，抽查全部通过。两处缺口如实登记（详见 05 节），未做任何填补或修饰。</p>

<h2><span class="no">04</span>跨源一致性验证</h2>
<p>用独立的 WheatYield_ref.tif（Xiao 同源但独立分发的参考图层）与 rds 主表按最近网格配对：n=1,552，<b>Pearson r={r_cross:.3f}（p≈2×10⁻⁵⁴）</b>。均值比 15.71/7.19≈2.19，恰为「轮作两熟合计 vs 小麦单季」的口径差——两源指向同一底层产量结构，交叉验证通过。</p>

<h2><span class="no">05</span>缺口登记（诚实清单）</h2>
<div class="two">
<div><p><b>① SoilGrids nitrogen 列缺失</b>（新增行 0% 覆盖，其余 7 项 73.3%）<br>原因：本地 nitrogen_0-5cm_mean_5000.tif 源文件瓦片损坏（TIFFReadEncodedTile 失败）；SoilGrids REST API 今日 503，暂无法重下。<br>影响：8 项土壤变量缺 1 项，不阻塞建模；可用世界土壤参考值或后期重下补齐。</p></div>
<div><p><b>② 北部网格高程缺失</b>（elev_m 57.6% 覆盖）<br>原因：本地 SRTM 图幅 srtm_60_04 南界为 40°N，平谷北部（40.0-40.5°N）超出图幅；WorldClim elev 兜底下载因域名 DNS 解析失败未完成。<br>影响：地形列对增量行不可用；气候背景（bio/月值）不受影响。</p></div>
</div>

<h2><span class="no">06</span>验证与可复现性</h2>
<table>
<tr><th>测试</th><th>结果</th></tr>
<tr><td>rds 原始回溯（5 条抽样，重读 57MB 源文件比对 Yield）</td><td><b>MATCH</b>（逐位一致）</td></tr>
<tr><td>坐标往返一致性（gridcell↔经纬度，round 修正后）</td><td><b>5/5 通过</b></td></tr>
<tr><td>模型端试载入（模拟 r2_modeling 读取流程）</td><td>124 列可读，119 数值列，53 环境特征列，Yield 非空 {n_new:,} 行</td></tr>
<tr><td>Smoke CV（增量行内 5 折 RF，53→13 零缺失特征）</td><td><b>R²={r2s:.3f}</b>±0.052（信号真实存在）</td></tr>
</table>

<h2><span class="no">07</span>许可与台账</h2>
<p>新增数据 100% 免授权：Xiao2024（CC BY 4.0，Figshare DOI 10.6084/m9.figshare.24471919.v5）、WorldClim（CC BY-SA 4.0）、SoilGrids（CC BY 4.0）——全部允许学术使用与再分发，无需逐份申请或付费，引用要求已在数据字典注明。六批次处理台账（来源/许可/时间/处理步骤/规模）见 data_ledger_20260914.csv。</p>

<div class="note"><b>给爸爸的反馈（替代推荐备忘录的结论）</b>：本轮补强把「点数」做到了 7.6×，但增量产量的空间变异较窄（14.89-16.37 t/ha），这是优化产量图层（管理趋同后）的固有特征。如果目标是让模型学到更宽的产量变异，我更推荐：<b>①</b> Zenodo ChinaWheatYield30m 2016-2020 五年份（爸爸网盘已在下载，每格真实年际差异，跨年验证价值最高）；<b>②</b> 市级/区级统计年鉴小麦单产（1990-2020 长时序，结构不同但变异真实）；<b>③</b> 课题组补测 43 实测点周边加密采样。三者可与本轮 1km 图层叠加成「空间×年际」双维度面板。</div>

<div class="foot">2026-SP · DearDragon233 · Data: Outputs/intermediate/augmented_yield_master_v2.csv · Scripts: src/s3_data_augmentation/ · CC BY 4.0 / CC BY-SA 4.0</div>
</div></body></html>"""

html_path = os.path.join(REP, "data_augmentation_report_stamen.html")
with open(html_path, "w", encoding="utf-8") as f:
    f.write(html)
print("html:", html_path)

import shutil
shutil.copy(html_path, os.path.join(DESK, "2026SP_数据补强报告.html"))
shutil.copy(dd_path, os.path.join(DESK, "2026SP_数据字典.csv"))
shutil.copy(ledger_path, os.path.join(DESK, "2026SP_数据台账.csv"))
print("copied 3 files to Desktop")
