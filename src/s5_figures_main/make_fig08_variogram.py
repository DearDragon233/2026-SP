# -*- coding: utf-8 -*-
"""fig08 W14 signature figure（三面板，Fathom 风格 600dpi）：
(A) variogram γ(h) 产量/残差 + 变程标注
(B) 五方案验证谱系 pooled R²（随机/棋盘/纬度块/LOBO/环境空间分块）——插值到外推
(C) 块尺寸-乐观偏差剂量响应曲线（0.5×~4× 变程 + 随机基线）
数据源: review_response_variogram.json + w14_q2_spectrum.csv + w14_dose_response.csv
"""
import json, os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

ROOT = r"D:\2026-SP"
INT = os.path.join(ROOT, "Outputs", "intermediate")
FIG = os.path.join(ROOT, "Outputs", "figures", "main")
NAVY = "#1d3557"; ACCENT = "#b5623b"; INK = "#1e2a38"; HAIR = "#d9dde2"; PAPER = "#fafaf8"; MUTED = "#5c6b7a"; GREEN = "#4a7c59"

for f in ["C:/Windows/Fonts/msyh.ttc", "C:/Windows/Fonts/simhei.ttf"]:
    if os.path.exists(f):
        font_manager.fontManager.addfont(f)
        plt.rcParams["font.family"] = font_manager.FontProperties(fname=f).get_name()
        break
plt.rcParams.update({"axes.unicode_minus": False, "font.size": 10.5})

vj = json.load(open(os.path.join(INT, "review_response_variogram.json"), encoding="utf-8"))
spec = pd.read_csv(os.path.join(INT, "w14_q2_spectrum.csv"))
dose = pd.read_csv(os.path.join(INT, "w14_dose_response.csv"))

fig, axes = plt.subplots(1, 3, figsize=(15.5, 4.8), dpi=600)
fig.patch.set_facecolor(PAPER)

# (A) variogram
ax = axes[0]; ax.set_facecolor(PAPER)
gy, gr = vj["yield_variogram"], vj["resid_variogram"]
ax.plot([p["lag_km"] for p in gy], [p["gamma"] for p in gy], "-o", color=NAVY, lw=1.8, ms=4, label="产量 γ(h)")
ax.plot([p["lag_km"] for p in gr], [p["gamma"] for p in gr], "-s", color=ACCENT, lw=1.8, ms=4, label="CV残差 γ(h)")
ax.axhline(0.95, color=MUTED, lw=0.9, ls="--")
ax.axvline(4.62, color=INK, lw=1.1, ls=":")
ax.annotate("变程 ≈4.6 km", (4.85, 0.4), fontsize=9.5, color=INK)
ax.set_xlabel("滞后距离 h (km)"); ax.set_ylabel("标准化半方差 γ(h)")
ax.set_title("(A) 经验变差函数", fontsize=11.5, color=INK, loc="left")
ax.spines[["top", "right"]].set_visible(False); ax.spines[["left", "bottom"]].set_color(INK)
ax.grid(color=HAIR, lw=0.55); ax.set_axisbelow(True)
ax.legend(frameon=False, fontsize=9.5, loc="lower right")

# (B) 五方案谱系
ax = axes[1]; ax.set_facecolor(PAPER)
names = ["随机5折", "棋盘0.72×", "纬度4块", "LOBO8", "环境KMeans4"]
keys = ["random", "checker_1x", "lat4", "lobo8", "env_kmeans4"]
vals = [float(spec[spec.scheme == k]["pooled_mean"].iloc[0]) for k in keys]
errs = [float(spec[spec.scheme == k]["pooled_std"].iloc[0]) for k in keys]
colors = [NAVY, NAVY, ACCENT, ACCENT, ACCENT]
ax.axhline(0, color=INK, lw=0.9)
bars = ax.bar(range(5), vals, yerr=errs, color=colors, alpha=0.88, width=0.62,
              error_kw=dict(ecolor=INK, lw=1.1, capsize=3))
for i, v in enumerate(vals):
    ax.annotate(f"{v:.2f}", (i, v + (0.03 if v >= 0 else -0.06)), ha="center", fontsize=9.5,
                color=colors[i], fontweight="bold")
ax.axvspan(-0.5, 1.5, color=NAVY, alpha=0.05); ax.axvspan(1.5, 4.5, color=ACCENT, alpha=0.05)
ax.text(0.5, 0.47, "制图", ha="center", fontsize=9.5, color=NAVY)
ax.text(3.0, 0.47, "外推", ha="center", fontsize=9.5, color=ACCENT)
ax.set_xticks(range(5)); ax.set_xticklabels(names, fontsize=9)
ax.set_ylabel("pooled R²"); ax.set_ylim(-0.28, 0.52)
ax.set_title("(B) 五方案验证谱系（XGB, 3种子）", fontsize=11.5, color=INK, loc="left")
ax.spines[["top", "right"]].set_visible(False); ax.spines[["left", "bottom"]].set_color(INK)
ax.grid(axis="y", color=HAIR, lw=0.55); ax.set_axisbelow(True)

# (C) 剂量响应
ax = axes[2]; ax.set_facecolor(PAPER)
rand = dose[dose.block_ratio_x_range == 0].set_index("model")
for model, color, mk in [("XGB", NAVY, "o"), ("RF", GREEN, "s")]:
    d = dose[(dose.model == model) & (dose.block_ratio_x_range > 0)].sort_values("block_ratio_x_range")
    gap = [d.pooled_mean.iloc[i] - rand.loc[model, "pooled_mean"] for i in range(len(d))]
    x = list(d.block_ratio_x_range)
    ax.plot(x, gap, f"-{mk}", color=color, lw=2, ms=5.5, label=model)
    for xi, gi in zip(x, gap):
        ax.annotate(f"{gi:+.2f}", (xi, gi), textcoords="offset points", xytext=(0, -13 if gi < 0.05 else 7),
                    ha="center", fontsize=8.5, color=color)
ax.axhline(0, color=INK, lw=0.9, ls="--")
ax.axvspan(0.4, 0.8, color=ACCENT, alpha=0.10)
ax.annotate("当前主口径\n0.72×变程", (0.82, 0.10), fontsize=8.5, color=ACCENT)
ax.set_xlabel("棋盘块边长 / 变程比"); ax.set_ylabel("pooled 乐观偏差（随机 − 棋盘）")
ax.set_title("(C) 块尺寸剂量响应", fontsize=11.5, color=INK, loc="left")
ax.spines[["top", "right"]].set_visible(False); ax.spines[["left", "bottom"]].set_color(INK)
ax.grid(color=HAIR, lw=0.55); ax.set_axisbelow(True)
ax.legend(frameon=False, fontsize=9.5)
ax.set_ylim(-0.06, 0.20)

plt.tight_layout()
plt.savefig(os.path.join(FIG, "fig08_variogram_block_defense.png"), facecolor=PAPER)
plt.savefig(os.path.join(FIG, "fig08_variogram_block_defense.tiff"), facecolor=PAPER,
            pil_kwargs={"compression": "tiff_lzw"}, dpi=600)
plt.close()
print("fig08 signature figure saved (png+tiff)")
