# -*- coding: utf-8 -*-
"""测试 rds gridcell ID → 经纬度映射假设（行主序 over 1068x1320 NCP extent）
并抽取平谷网格的全部行（History + 12 情景）。"""
import pyreadr, numpy as np, pandas as pd

# NCP 参考图层范围（与 WheatYield_ref.tif 一致）
LON0, LAT1, RES = 112.1, 40.7, 0.008333333333333333
NCOL = 1320

r = pyreadr.read_r(r"D:\2026-SP\Data\Management\Xiao2024\Allregions.rds")
df = list(r.values())[0]
print("total rows:", len(df), "| unique gridcells:", df["gridcell"].nunique())

g = df.drop_duplicates("gridcell")["gridcell"].values
row = (g // NCOL).astype(int); col = (g % NCOL).astype(int)
lon = LON0 + col * RES
lat = LAT1 - row * RES
print("implied lon range:", lon.min().round(3), lon.max().round(3))
print("implied lat range:", lat.min().round(3), lat.max().round(3))

# 平谷 bbox（与 234 网格一致：116.81-117.53E, 39.98-40.48N，略放宽）
m = (lon >= 116.75) & (lon <= 117.60) & (lat >= 39.93) & (lat <= 40.53)
print("gridcells in Pinggu bbox:", m.sum())
if m.sum() > 0:
    demo = pd.DataFrame({"gridcell": g[m][:10], "lon": lon[m].round(4)[:10], "lat": lat[m].round(4)[:10]})
    print(demo.to_string(index=False))
    ids = g[m]
    sub = df[df["gridcell"].isin(ids)].copy()
    sub["lon"] = sub["gridcell"].map(dict(zip(g, lon)))
    sub["lat"] = sub["gridcell"].map(dict(zip(g, lat)))
    print("\nPinggu rows:", len(sub))
    print("Period counts:", sub["Period"].value_counts().to_dict())
    print("Yield stats by Period:")
    print(sub.groupby("Period")["Yield"].agg(["count","min","mean","max"]).round(3).to_string())
    sub.to_csv(r"D:\2026-SP\Outputs\intermediate\xiao2024_rds_pinggu_raw.csv", index=False, encoding="utf-8-sig")
    print("saved xiao2024_rds_pinggu_raw.csv")
else:
    # 映射假设失败，尝试其他 NCOL（如 1320 之外的宽度）
    for ncol_test in (1000, 1100, 1200, 1400, 1500, 1600):
        row2 = (g // ncol_test).astype(int); col2 = (g % ncol_test).astype(int)
        lon2 = LON0 + col2 * RES; lat2 = LAT1 - row2 * RES
        m2 = (lon2 >= 116.75) & (lon2 <= 117.60) & (lat2 >= 39.93) & (lat2 <= 40.53)
        print(f"  ncol={ncol_test}: in-bbox {m2.sum()}")
