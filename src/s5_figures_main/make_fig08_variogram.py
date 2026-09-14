# -*- coding: utf-8 -*-
"""fig08: variogram 与块尺寸辩护图（诊断线主图 8，Fathom 风格 600dpi）
左：产量/残差经验变差函数 γ(h)；右：块尺寸-变程比示意（棋盘 3.3km = 0.72×range）
数据源: review_response_variogram.json
"""
import json, os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

ROOT = r"D:\2026-SP"
FIG = os.path.join(ROOT, "Outputs", "figures", "main")
vj = json.load(open(os.path.join(ROOT, "Outputs", "intermediate", "review_response_variogram.json"), encoding="utf-8"))
NAVY = "#1d3557"; ACCENT = "#b5623b"; INK = "#1e2a38"; HAIR = "#d9dde2"; PAPER = "#fafaf8"; MUTED = "#5c6b7a"

for f in ["C:/Windows/Fonts/msyh.ttc", "C:/Windows/Fonts/simhei.ttf"]:
    if os.path.exists(f):
        font_manager.fontManager.addfont(f)
        plt.rcParams["font.family"] = font_manager.FontProperties(fname=f).get_name()
        break
plt.rcParams.update({"axes.unicode_minus": False, "font.size": 11})

fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.6), dpi=600)
fig.patch.set_facecolor(PAPER)

ax = axes[0]; ax.set_facecolor(PAPER)
gy = vj["yield_variogram"]; gr = vj["resid_variogram"]
ax.plot([p["lag_km"] for p in gy], [p["gamma"] for p in gy], "-o", color=NAVY, lw=2, ms=5, label="产量 γ(h)")
ax.plot([p["lag_km"] for p in gr], [p["gamma"] for p in gr], "-s", color=ACCENT, lw=2, ms=5, label="CV残差 γ(h)")
ax.axhline(0.95, color=MUTED, lw=1, ls="--")
ax.axvline(4.62, color=INK, lw=1.2, ls=":")
ax.annotate("变程 ≈4.6 km\n(γ 达 0.95·sill)", (4.75, 0.45), fontsize=10, color=INK)
ax.set_xlabel("滞后距离 h (km)"); ax.set_ylabel("标准化半方差 γ(h)")
ax.set_title("(A) 经验变差函数", fontsize=12, color=INK, loc="left")
ax.spines[["top", "right"]].set_visible(False)
ax.spines[["left", "bottom"]].set_color(INK)
ax.grid(color=HAIR, lw=0.6); ax.set_axisbelow(True)
ax.legend(frameon=False, fontsize=10)

ax = axes[1]; ax.set_facecolor(PAPER)
items = [("棋盘块 3.3 km", 3.3, ACCENT), ("纬度块 ~11.5 km", 11.5, NAVY), ("变程 4.6 km", 4.62, INK)]
ypos = np.arange(len(items))
ax.barh(ypos, [it[1] for it in items], color=[it[2] for it in items], alpha=0.85, height=0.55)
for i, (name, v, _c) in enumerate(items):
    ax.text(v + 0.15, i, f"{v:.1f} km", va="center", fontsize=10.5, color=INK, fontweight="bold")
ax.set_yticks(ypos); ax.set_yticklabels([it[0] for it in items], fontsize=10.5)
ax.axvline(4.62, color=INK, lw=1.2, ls=":")
ax.text(4.8, 2.32, "0.72×变程 →\n乐观偏差下界", fontsize=9.5, color=ACCENT)
ax.set_xlim(0, 13.5); ax.invert_yaxis()
ax.set_xlabel("空间尺度 (km)")
ax.set_title("(B) 块尺寸 vs 自相关变程", fontsize=12, color=INK, loc="left")
ax.spines[["top", "right"]].set_visible(False)
ax.spines[["left", "bottom"]].set_color(INK)
ax.grid(axis="x", color=HAIR, lw=0.6); ax.set_axisbelow(True)

plt.tight_layout()
plt.savefig(os.path.join(FIG, "fig08_variogram_block_defense.png"), facecolor=PAPER)
plt.close()
print("fig08 saved")
