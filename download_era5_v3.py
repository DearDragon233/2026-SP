"""
ERA5-Land 逐月下载 + 极端气候指数计算
策略: 逐月请求 → 逐日提取 → 合并且计算95/5分位数
区域: 平谷区 (116.8-117.5E, 40.0-40.5N)
时间: 1981-2010 生长季 (3-9月)
"""
import cdsapi
import xarray as xr
import numpy as np
import pandas as pd
from pathlib import Path
import time, shutil

OUT_DIR = Path(r"D:\2026-SP\Data\ERA5")
OUT_DIR.mkdir(parents=True, exist_ok=True)
TMP_DIR = OUT_DIR / "_tmp"
TMP_DIR.mkdir(exist_ok=True)

YEARS = list(range(1981, 2011))
MONTHS = ["03", "04", "05", "06", "07", "08", "09"]
DAYS = [f"{d:02d}" for d in range(1, 32)]
HOURS = [f"{h:02d}:00" for h in range(24)]
AREA = [40.5, 116.8, 40.0, 117.5]

client = cdsapi.Client()

total = len(YEARS) * len(MONTHS)
print(f"目标: {len(YEARS)}年 x {len(MONTHS)}月 = {total} 次请求")
print(f"如果全部成功: {total * len(DAYS) * len(HOURS)} 小时数据点")
print("=" * 60)

all_dfs = []
n = 0
failures = []

for year in YEARS:
    year_dfs = []
    for month in MONTHS:
        n += 1
        fname = TMP_DIR / f"era5_{year}_{month}.nc"
        label = f"[{n:03d}/{total}] {year}-{month}"
        
        if fname.exists() and fname.stat().st_size > 1000:
            print(f"{label} 已有缓存")
        else:
            try:
                result = client.retrieve("reanalysis-era5-land", {
                    "variable": ["2m_temperature", "total_precipitation"],
                    "year": [str(year)],
                    "month": [month],
                    "day": DAYS,
                    "time": HOURS,
                    "area": AREA,
                    "data_format": "netcdf",
                })
                result.download(str(fname))
                sz = fname.stat().st_size / 1024 / 1024
                print(f"{label} 下载 {sz:.1f} MB")
            except Exception as e:
                msg = str(e)[:120]
                print(f"{label} 失败: {msg}")
                failures.append(f"{year}-{month}: {msg}")
                continue
            time.sleep(0.5)
        
        # 提取逐日统计
        try:
            ds = xr.open_dataset(fname)
            t2m = ds["t2m"]
            tp = ds["tp"]
            t2m_daily = t2m.resample(time="1D")
            tp_daily = tp.resample(time="1D")
            
            tmax = t2m_daily.max().mean(dim=["latitude", "longitude"]).values
            tmin = t2m_daily.min().mean(dim=["latitude", "longitude"]).values
            prec = tp_daily.sum().mean(dim=["latitude", "longitude"]).values * 1000
            dates = pd.to_datetime(t2m_daily.max().time.values)
            ds.close()
            
            year_dfs.append(pd.DataFrame({
                "date": dates, "year": dates.year, "month": dates.month,
                "day": dates.day, "tmax_K": tmax, "tmin_K": tmin, "prec_mm": prec,
            }))
        except Exception as e:
            print(f"  ⚠ 处理异常: {e}")
    
    if year_dfs:
        all_dfs.append(pd.concat(year_dfs, ignore_index=True))

if failures:
    print(f"\n失败 {len(failures)} 项:")
    for f in failures:
        print(f"  {f}")

print("\n▶ 合并...")
full = pd.concat(all_dfs, ignore_index=True).sort_values("date").reset_index(drop=True)
full["tmax_K"] = full["tmax_K"].clip(200, 330)
full["tmin_K"] = full["tmin_K"].clip(180, 310)
full["prec_mm"] = full["prec_mm"].clip(0, 500)

gs = full[full["month"].between(3, 9)]
Tmax_95p = gs["tmax_K"].quantile(0.95)
Tmin_5p  = gs["tmin_K"].quantile(0.05)
Prec_95p = gs["prec_mm"].quantile(0.95)

print(f"\n=== 平谷区 1981-2010 生长季极端气候指数 ===")
print(f"  Tmax_95p  = {Tmax_95p:.2f} K  ({Tmax_95p - 273.15:.1f} °C)")
print(f"  Tmin_5p   = {Tmin_5p:.2f} K  ({Tmin_5p - 273.15:.1f} °C)")
print(f"  Prec_95p  = {Prec_95p:.1f} mm/day")

# 保存
full.to_csv(OUT_DIR / "era5_daily_pinggu_1981-2010.csv", index=False)
print(f"逐日数据: {OUT_DIR / 'era5_daily_pinggu_1981-2010.csv'} ({len(full)} 行)")

yearly = gs.groupby("year").agg(
    tmax_95p=("tmax_K", lambda x: x.quantile(0.95)),
    tmin_5p=("tmin_K", lambda x: x.quantile(0.05)),
    prec_95p=("prec_mm", lambda x: x.quantile(0.95)),
).reset_index()
yearly["tmax_95p_C"] = yearly["tmax_95p"] - 273.15
yearly["tmin_5p_C"] = yearly["tmin_5p"] - 273.15
yearly.to_csv(OUT_DIR / "era5_yearly_extremes.csv", index=False, float_format="%.3f")

pd.DataFrame({
    "variable": ["Tmax_95p_K", "Tmax_95p_C", "Tmin_5p_K", "Tmin_5p_C", "Prec_95p_mm"],
    "value": [Tmax_95p, Tmax_95p - 273.15, Tmin_5p, Tmin_5p - 273.15, Prec_95p],
}).to_csv(OUT_DIR / "era5_climate_indices.csv", index=False)

shutil.rmtree(TMP_DIR, ignore_errors=True)
print("✅ 完成!")
