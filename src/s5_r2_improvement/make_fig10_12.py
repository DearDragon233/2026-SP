# -*- coding: utf-8 -*-
"""出版级图表（Fathom Information Design 风格，600dpi）
fig10: 实验 R² 对比（随机 CV vs 空间分块 CV，分组条形图）
fig11: 分块方式敏感性（3 种空间分块 × E0/E8）
fig12: 观测-预测散点（E0 vs E8，含 1:1 线）
"""
import pandas as pd, numpy as np, json, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from sklearn.metrics import r2_score

ROOT = r"D:\2026-SP"
INT = os.path.join(ROOT, "Outputs", "intermediate")
FIG = os.path.join(ROOT, "Outputs", "figures", "main")
os.makedirs(FIG, exist_ok=True)

NAVY = "#1d3557"; ACCENT = "#b5623b"; INK = "#1e2a38"; HAIR = "#d9dde2"
MUTED = "#5c6b7a"; PAPER = "#fafaf8"; BLUE2 = "#457b9d"

# 中文字体
for f in ["C:/Windows/Fonts/msyh.ttc", "C:/Windows/Fonts/simhei.ttf", "C:/Windows/Fonts/simsun.ttc"]:
    if os.path.exists(f):
        font_manager.fontManager.addfont(f)
        plt.rcParams["font.family"] = font_manager.FontProperties(fname=f).get_name()
        break
plt.rcParams.update({"axes.unicode_minus": False, "font.size": 11})

led = pd.read_csv(os.path.join(INT, "experiments_ledger_v3.csv"))
sp = pd.read_csv(os.path.join(INT, "spatial_cv_ledger.csv"))
vp = json.load(open(os.path.join(INT, "verification_package.json"), encoding="utf-8"))

# ---------- fig10: 随机 CV vs 空间分块 CV ----------
exps = ["E0_base58", "E5_topk25", "E7_topk25_ridge", "E8_resid_idw"]
labels = ["E0 基线\n(58特征)", "E5 特征精简\n(top-25)", "E7 +Ridge混合", "E8 残差IDW\n(混合制图)"]
rand_r2 = [led.loc[led["exp"] == e, "r2_pooled"].iloc[0] for e in exps]
# 空间 CV（纬度分块）对应 S0/S5/S8（E7 无空间版，跳过）
spat_map = {"E0_base58": "S0_base58", "E5_topk25": "S5_topk25", "E8_resid_idw": "S8_resid_idw"}
spat_r2 = [sp.loc[sp["exp"] == spat_map.get(e, ""), "r2_pooled"].iloc[0] if spat_map.get(e, "") in set(sp["exp"]) else np.nan for e in exps]

fig, ax = plt.subplots(figsize=(8.2, 4.8), dpi=600)
fig.patch.set_facecolor(PAPER); ax.set_facecolor(PAPER)
x = np.arange(len(exps)); w = 0.36
b1 = ax.bar(x - w/2, rand_r2, w, color=NAVY, label="随机 5 折 CV")
b2 = ax.bar(x + w/2, [0 if np.isnan(v) else v for v in spat_r2], w, color=ACCENT, label="空间分块 CV（纬度4块）")
for i, (r, s) in enumerate(zip(rand_r2, spat_r2)):
    ax.text(i - w/2, r + 0.015, f"{r:.3f}", ha="center", fontsize=10, color=NAVY, fontweight="bold")
    if not np.isnan(s):
        ax.text(i + w/2, s + 0.015, f"{s:.3f}", ha="center", fontsize=10, color=ACCENT, fontweight="bold")
    else:
        ax.text(i + w/2, 0.02, "未测", ha="center", fontsize=9, color=MUTED)
ax.set_xticks(x); ax.set_xticklabels(labels, fontsize=10)
ax.set_ylabel("池化 R²", fontsize=11)
ax.set_ylim(0, 0.92)
ax.spines[["top", "right"]].set_visible(False)
ax.spines[["left", "bottom"]].set_color(INK)
ax.grid(axis="y", color=HAIR, lw=0.6); ax.set_axisbelow(True)
ax.legend(frameon=False, fontsize=10, loc="upper left")
plt.tight_layout()
plt.savefig(os.path.join(FIG, "fig10_experiment_comparison.png"), facecolor=PAPER)
plt.close()
print("fig10 saved")

# ---------- fig11: 分块敏感性 ----------
vb = pd.DataFrame(vp["spatial_blocks"])
blocks = ["lat4", "lon4", "kmeans4"]
bl = ["纬度4块", "经度4块", "KMeans4块"]
e0v = [vb[(vb["block"] == b) & (vb["exp"] == "E0")]["spatial_r2"].iloc[0] for b in blocks]
e8v = [vb[(vb["block"] == b) & (vb["exp"] == "E8")]["spatial_r2"].iloc[0] for b in blocks]
fig, ax = plt.subplots(figsize=(7.6, 4.6), dpi=600)
fig.patch.set_facecolor(PAPER); ax.set_facecolor(PAPER)
x = np.arange(3); w = 0.36
ax.bar(x - w/2, e0v, w, color=NAVY, label="E0 纯环境模型")
ax.bar(x + w/2, e8v, w, color=ACCENT, label="E8 残差IDW混合")
for i, (a, b) in enumerate(zip(e0v, e8v)):
    ax.text(i - w/2, a + (0.015 if a >= 0 else -0.045), f"{a:.3f}", ha="center", fontsize=10, color=NAVY, fontweight="bold")
    ax.text(i + w/2, b + (0.015 if b >= 0 else -0.045), f"{b:.3f}", ha="center", fontsize=10, color=ACCENT, fontweight="bold")
ax.axhline(0, color=INK, lw=1)
ax.set_xticks(x); ax.set_xticklabels(bl, fontsize=11)
ax.set_ylabel("空间分块 CV 池化 R²", fontsize=11)
ax.spines[["top", "right"]].set_visible(False)
ax.spines[["left", "bottom"]].set_color(INK)
ax.grid(axis="y", color=HAIR, lw=0.6); ax.set_axisbelow(True)
ax.legend(frameon=False, fontsize=10)
plt.tight_layout()
plt.savefig(os.path.join(FIG, "fig11_block_sensitivity.png"), facecolor=PAPER)
plt.close()
print("fig11 saved")

# ---------- fig12: 观测-预测散点 ----------
pr = pd.read_csv(os.path.join(INT, "all_predictions_v3.csv"))
fig, axes = plt.subplots(1, 2, figsize=(9.6, 4.9), dpi=600)
fig.patch.set_facecolor(PAPER)
for ax, col, ttl, c in [(axes[0], "E0", "E0 基线（R²=0.326）", NAVY), (axes[1], "E8", "E8 残差IDW混合（R²=0.769）", ACCENT)]:
    ax.set_facecolor(PAPER)
    yt, yp = pr[col].values, pr[col + "_p"].values
    ax.scatter(yt, yp, s=14, alpha=0.65, color=c, edgecolors="none")
    lim = [min(yt.min(), yp.min()) - 0.2, max(yt.max(), yp.max()) + 0.2]
    ax.plot(lim, lim, color=INK, lw=1, ls="--")
    r2 = r2_score(yt, yp)
    ax.set_xlim(lim); ax.set_ylim(lim)
    ax.set_xlabel("观测产量 (t/ha)", fontsize=10.5)
    ax.set_ylabel("预测产量 (t/ha)", fontsize=10.5)
    ax.set_title(ttl, fontsize=11.5, color=INK, pad=8)
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["left", "bottom"]].set_color(INK)
    ax.grid(color=HAIR, lw=0.5); ax.set_axisbelow(True)
plt.tight_layout()
plt.savefig(os.path.join(FIG, "fig12_obs_pred_scatter.png"), facecolor=PAPER)
plt.close()
print("fig12 saved")
