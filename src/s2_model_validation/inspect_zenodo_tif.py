# -*- coding: utf-8 -*-
"""检查 2021ChinaWheatYield30m.tif 元数据 + 平谷范围预览（不载入全图）"""
import rasterio
p = r"D:\2026-SP\Data\2021ChinaWheatYield30m.tif"
with rasterio.open(p) as src:
    print("size:", src.width, "x", src.height)
    print("crs:", src.crs)
    print("bounds:", src.bounds)
    print("transform:", src.transform)
    print("nodata:", src.nodata)
    print("dtype:", src.dtypes)
    print("res:", src.res)
    # 平谷范围（WGS84）：lon 116.92-117.24, lat 40.02-40.22
    # 数据 CRS 若为 EPSG:4326 则直接可算行列窗口
    b = src.bounds
    print("\n覆盖检查（EPSG:4326 假设）:")
    print("  平谷 lon 116.92-117.24 在 bounds 内:", b.left <= 116.92 and 117.24 <= b.right)
    print("  平谷 lat 40.02-40.22 在 bounds 内:", b.bottom <= 40.02 and 40.22 <= b.top)
    if src.crs and src.crs.to_epsg() == 4326:
        from rasterio.windows import from_bounds
        try:
            win = from_bounds(116.90, 40.00, 117.26, 40.24, src.transform)
            print("  平谷窗口:", win)
            print("  窗口大小:", round(win.width), "x", round(win.height), "像元")
        except Exception as e:
            print("  window error:", e)
