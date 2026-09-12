# -*- coding: utf-8 -*-
"""v3.4 补强报告: docx + html 双版本，输出到 2026-SP/Outputs/reports 与桌面"""
import html as H
from docx import Document
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn

TITLE = "2026-SP 数据质量补强报告：四缺口解决方案与实证结果"
SUB = "针对 Agronomy 投稿数据质量评估发现的四个严重问题的系统性修复 · 2026-09-12"

METRICS = [
    ("G1", "产量来源敏感性：实测43点 R²≈0，预测234点 R²=0.98，混合 R²=0.30-0.39"),
    ("G2", "空间CV乐观偏差量化：随机CV比纬度块CV虚高 +0.09~+0.04 R²"),
    ("G3", "QRF 不确定性：PICP=0.705（90%名义），区间均值宽 0.592 t/ha"),
    ("G4", "成果落盘：3图×2格式 + 5份CSV + 1个新管线脚本"),
]

# ============ 内容 ============
SECTIONS = [
("一、背景与目标",
 "此前的数据质量评估确认：环境变量侧（234网格×24建模变量，零缺失、VIF→Boruta→SHAP 筛选链完整、QA 六图审计）达到 Agronomy 发表水准；但存在四个严重缺口——G1 产量目标 82% 为空间插值且实测仅 43 点、G2 交叉验证未处理空间自相关、G3 无不确定性量化、G4 单年数据。本报告记录四个缺口的系统性修复过程与实证结果。全部代码收录于 src/s2_model_validation/advance_validation.py，可一键复现。"),
("二、G1 产量来源敏感性分析（最关键发现）",
 "方法：同一特征矩阵分别对三种产量目标建模——A 实测产量（Xiao2024，43 网格）、B 空间预测产量（234 网格）、C 混合产量（贝叶斯融合，234 网格）——用相同的 5 折交叉验证对比性能。结果：目标 B 的 R² 高达 0.977-0.986，而目标 A 的 R² 在 -0.06 至 0.08 之间（三模型全部接近零或为负），目标 C 居中（0.30-0.39）。空间预测与实测的 Pearson r 仅 0.510，预测值标准差（0.056）远小于实测（0.224）。结论：以空间预测产量为目标的高 R² 是循环论证——模型在复现 Ridge 插值 的平滑表面，而非学习真实产量变异；混合目标中约六至七成的「可解释方差」同样来自插值平滑。这一发现把此前的隐患转化为了论文中可写的诚实结论：环境变量对真实田间产量变异的解释能力目前接近于零，混合目标的表观性能主要由目标自身的空间平滑性贡献。对投稿的含义：不能以混合目标的 R²=0.31-0.39 作为主要性能声明单独呈现，必须与 A 口径（真实技能≈0）并列呈现，并将论文定位从「产量预测」调整为「环境-产量关系诊断 + 空间预测方法的敏感性剖析」。这一调整反而更符合 Agronomy 近年发表的批判性方法学文章路线。"),
("三、G2 空间交叉验证方案对比",
 "方法：三种 5 折 CV 方案——随机分配（基准）、纬度五分位块、经纬度 0.03° 棋盘块——对同一特征矩阵与混合产量目标分别评估 XGBoost/LightGBM/RF。结果：随机 CV 的 R²（0.30/0.31/0.39）系统性地高于空间分块 CV（纬度块 0.03/-0.02/0.03；棋盘块 0.22/0.27/0.35），乐观偏差 +0.036 至 +0.088 R²。纬度块的崩塌说明研究区存在强烈的南北梯度混杂：纬度块把气候带整体留出，模型无法「背答案」；棋盘块保留部分跨带信息，性能居中。结论：论文必须采用棋盘块 CV（或更细的空间块）作为主口径，随机 CV 仅作对照；乐观偏差的量化本身即是论文的一个贡献点。"),
("四、G3 分位数随机森林不确定性量化",
 "方法：Quantile Random Forest（Meinshausen 2006；quantile-forest 实现），300 树，纬度空间 5 折，预测 10/50/90 分位。结果：PICP=0.705（名义 90%，实际覆盖 70.5%，区间偏窄即略过度自信）；区间平均宽度 MPW=0.592 t/ha；Q50 的空间 CV R²=0.237。区间宽度分布右偏，部分网格（西南高值区）区间明显更宽，符合异方差直觉。结论：不确定性量化框架已建立并产出逐网格区间（qrf_uncertainty.csv 234 行），论文可呈现「点预测+区间+覆盖诊断」完整链路；PICP 偏低的问题可通过加宽分位（如 5-95%）或 Conformal 校准进一步修正，作为局限性说明。"),
("五、G4 单年数据问题与处置",
 "本季未能新增年份数据（Xiao2024 仅单年、统计公报为区级年均）。处置：不伪造年际数据；在论文中将单年属性明确写入 Data 声明与 Limitations，并把「多年份扩展」列为后续工作。此为诚实处理，Agronomy 审稿可接受单年区域研究，但结论措辞需限定为该生长季。"),
("六、产出清单",
 "新增管线：src/s2_model_validation/advance_validation.py（一键复现全部实验）。新增图表（600dpi，main/）：fig05 CV 方案对比（三模型×三方案）、fig06 QRF 不确定性（区间带+校准散点+宽度分布）、fig07 产量来源敏感性（三口径柱状+实测vs预测散点）。新增中间表（intermediate/）：cv_scheme_comparison.csv、cv_optimism_gap.csv、qrf_uncertainty.csv（234 行逐网格分位数）、qrf_metrics.csv、yield_source_sensitivity.csv。"),
("七、对投稿路线的最终建议",
 "基于以上实证，投稿策略建议调整为：标题与摘要突出「环境指纹能否解释真实产量变异的系统性检验」，主结果呈现三口径敏感性（诚实暴露 B 口径循环论证），空间 CV 乐观偏差与 QRF 不确定性作为方法学贡献，混合目标模型降级为「当前数据条件下的最优可用模型」并配 PICP 区间。此路线把原先最大的软肋（产量数据质量）转化为论文的差异化贡献（对空间产量建模乐观偏差的量化示范），与 Agronomy 近年发表的方法学批判类文章同构，接收概率显著高于硬投「预测精度」路线。"),
]

SOURCES = [
    "Meinshausen 2006 Quantile Regression Forests (JMLR) — Paper/Akiba 与 Paper/ 目录已存",
    "Ploton et al. 2020 Nature Communications — spatial autocorrelation inflates CV performance",
    "Roberts et al. 2017 Ecography — standard practice for spatial cross-validation",
    "Xiao 2024 — 43 grid wheat yield observations (Data/Management/Xiao2024/)",
    "北京市统计局夏粮公报 — county_yield_stats.json 内含 URL",
]

# ============ DOCX ============
def build_docx(path):
    doc = Document()
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Cm(21), Cm(29.7)
    sec.left_margin = sec.right_margin = Cm(3.2)
    sec.top_margin = sec.bottom_margin = Cm(2.5)
    def set_font(run, size=12, bold=False, cn="宋体"):
        run.font.name = "Times New Roman"
        run._element.rPr.rFonts.set(qn("w:eastAsia"), cn)
        run.font.size = Pt(size); run.font.bold = bold
    def para(text, size=12, bold=False, cn="宋体", align=None, indent=True):
        p = doc.add_paragraph(); p.paragraph_format.line_spacing = 1.5; p.paragraph_format.space_after = Pt(0)
        if indent: p.paragraph_format.first_line_indent = Pt(size*2)
        if align is not None: p.alignment = align
        set_font(p.add_run(text), size, bold, cn)
    def heading(t, size=14): para(t, size, True, "黑体", indent=False)
    para(TITLE, 16, True, "黑体", WD_ALIGN_PARAGRAPH.CENTER, indent=False)
    para(SUB, 10.5, False, "宋体", WD_ALIGN_PARAGRAPH.CENTER, indent=False)
    doc.add_paragraph()
    for t, b in SECTIONS:
        heading(t, 14); para(b, 12, False)
    heading("附：来源与参考", 14)
    for s in SOURCES: para(s, 10.5, False, indent=False)
    doc.save(path)
    print("docx ->", path)

# ============ HTML ============
def build_html(path):
    def esc(s): return H.escape(str(s))
    metrics_html = '<div class="rich-metrics">' + "".join(
        f'<div class="rich-metric"><strong>{esc(k)}</strong><br><span class="muted">{esc(v)}</span></div>'
        for k, v in METRICS) + '</div>'
    secs = "".join(f'<h2>{esc(t)}</h2><p>{esc(b)}</p>' for t, b in SECTIONS)
    srcs = "".join(f"<li>{esc(s)}</li>" for s in SOURCES)
    html = f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc(TITLE)}</title><style>
:root{{--ink:#1c1917;--muted:#57534e;--accent:#047857;--soft:#ecfdf5;--line:#e7e5e4;}}
*{{box-sizing:border-box;margin:0;padding:0;}}
body{{font-family:-apple-system,"PingFang SC","Microsoft YaHei",sans-serif;background:#fafaf9;color:var(--ink);line-height:1.75;padding:36px 16px;}}
.page{{max-width:900px;margin:0 auto;background:#fff;border:1px solid var(--line);border-radius:14px;padding:44px 52px;box-shadow:0 1px 3px rgba(0,0,0,.05);}}
header{{border-bottom:3px double var(--line);padding-bottom:18px;margin-bottom:24px;}}
h1{{font-size:24px;letter-spacing:1px;}}
.meta{{color:var(--muted);font-size:13px;margin-top:6px;}}
h2{{font-size:17px;color:var(--accent);border-left:4px solid var(--accent);padding-left:10px;margin:28px 0 10px;}}
p{{font-size:14px;text-align:justify;margin-bottom:8px;}}
.rich-metrics{{display:flex;gap:12px;flex-wrap:wrap;margin:16px 0;}}
.rich-metric{{flex:1;min-width:200px;background:var(--soft);border:1px solid #a7f3d0;border-radius:10px;padding:12px 14px;font-size:13px;}}
.muted{{color:var(--muted);font-size:12px;}}
ul{{padding-left:1.4em;}} li{{font-size:13.5px;margin:4px 0;}}
footer{{border-top:1px solid var(--line);margin-top:30px;padding-top:14px;color:var(--muted);font-size:12px;text-align:center;}}
@media print{{body{{background:#fff;padding:0;}} .page{{border:none;box-shadow:none;}}}}
</style></head><body><div class="page">
<header><h1>{esc(TITLE)}</h1><div class="meta">{esc(SUB)}</div></header>
{metrics_html}
{secs}
<h2>附：来源与参考</h2><ul>{srcs}</ul>
<footer>2026-SP 项目 · 补强管线 src/s2_model_validation/advance_validation.py · 结果可一键复现</footer>
</div></body></html>"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    print("html ->", path)

REPORT_DIR = r"D:\2026-SP\Outputs\reports"
import os; os.makedirs(REPORT_DIR, exist_ok=True)
build_docx(os.path.join(REPORT_DIR, "W4_advance_report_v3.4.docx"))
build_html(os.path.join(REPORT_DIR, "W4_advance_report_v3.4.html"))
import shutil
shutil.copy(os.path.join(REPORT_DIR, "W4_advance_report_v3.4.html"),
            r"C:\Users\18322\Desktop\2026SP_补强报告.html")
shutil.copy(os.path.join(REPORT_DIR, "W4_advance_report_v3.4.docx"),
            r"C:\Users\18322\Desktop\2026SP_补强报告.docx")
print("copied to Desktop")
