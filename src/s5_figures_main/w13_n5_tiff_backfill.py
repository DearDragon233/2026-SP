# -*- coding: utf-8 -*-
"""W13-N5: 补齐 fig08-fig13 的 tiff（LZW 压缩，600dpi）——从现有 png 转换并保持分辨率。
fig09-13 与 fig08 均为 600dpi png，用 PIL 转 tiff 不损失质量。
"""
from PIL import Image
import os
FIG = r"D:\2026-SP\Outputs\figures\main"
targets = ["fig08_variogram_block_defense", "fig09_learning_curve", "fig10_experiment_comparison",
           "fig11_block_sensitivity", "fig12_obs_pred_scatter", "fig13_extrapolation_spectrum"]
for name in targets:
    png = os.path.join(FIG, name + ".png")
    tif = os.path.join(FIG, name + ".tiff")
    if not os.path.exists(tif):
        im = Image.open(png)
        dpi = im.info.get("dpi", (600, 600))
        im.save(tif, compression="tiff_lzw", dpi=dpi)
        print(f"{name}.tiff saved ({im.size[0]}x{im.size[1]}, dpi={dpi[0]:.0f})")
    else:
        print(f"{name}.tiff exists")
