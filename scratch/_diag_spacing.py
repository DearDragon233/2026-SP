import rasterio, numpy as np, pandas as pd
from rasterio.windows import from_bounds
from rasterio.transform import rowcol

# 核查：234 网格的 lat/lon 间隔是 0.0208°（~2.3km），不是 1km！
# 234 网格分布在 0.708°lon × 0.5°lat 上 → 每格约 0.0208° ≈ 2.3km
# 所以聚合窗口应该是 half = 0.0104（对角半径），而不是 0.005
df = pd.read_csv(r"D:\2026-SP\Outputs\intermediate\data_with_yield_ensemble_full.csv")
lons = sorted(df.lon.unique())
lats = sorted(df.lat.unique())
print("unique lon:", len(lons), "step:", round(lons[1]-lons[0], 5))
print("unique lat:", len(lats), "step:", round(lats[1]-lats[0], 5))
print("grid spacing ~", round((lons[1]-lons[0]) * 85, 1), "km (at lat 40)")
# 半格 = 0.0104°lon ≈ 890m, 0.0104°lat ≈ 1150m → 每网格约 30m 像元 60×77 = 4600 像元
print("expected px per grid (30m):", int(0.0104*2/0.00026949) * int(0.0104*2/0.00026949))
