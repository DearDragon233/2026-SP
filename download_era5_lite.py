"""
ERA5-Land 逐月下载 + 极端气候指数计算 (轻量版)
策略: 逐月请求，避免CDS单次请求字段数超限
区域: 平谷区 (116.8-117.5E, 40.0-40.5N)
时间: 1981-2010 生长季 (3-9月)
"""
import cdsapi
import xarray as xr
import numpy as np
import pandas as pd
from pathlib import Path
import time

OUT_DIR = Path(r"D:\2026-SP\Data\ERA5")
OUT_DIR.mkdir(parents=True, exist_ok=True)
TMP_DIR = OUT_DIR / "tmp"
TMP_DIR.mkdir(exist_ok=True)

YEARS = list(range(1981, 2011))
MONTHS = ["03", "04", "05", "06", "07", "08", "09"]
DAYS = [f"{d:02d}" for d in range(1, 32)]
HOURS = [f"{h:02d}:00" for h in range(24)]
AREA = [40.5, 116.8, 40.0, 117.5]

client = cdsapi.Client(quiet=True)

print("=" * 60)
print("ERA5-Land 平谷区极端气候指数计算 (逐月模式)")
print(f"总计: {len(YEARS)}年 × {len(MONTHS)}月 = {len(YEARS)*len(MONTHS)} 次请求")
print("=" * 60)

all_dfs = []
n_total = len(YEARS) * len(MONTHS)
n_done = 0

for year in YEARS:
    year_dfs = []
    for month in MONTHS:
        n_done += 1
        out_file = TMP_DIR / f"era5_{year}_{month}.nc"
        
        # 跳过已有
        if out_file.exists() and out_file.stat().st_size > 1000:
            print(f"[{n_done}/{n_total}] {year}-{month} 已有，跳过")
        else:
            request = {
                "variable": ["2m_temperature", "total_precipitation"],
                "year": str(year),
                "month": [month],
                "day": DAYS,
                "time": HOURS,
                "area": AREA,
                "data_format": "netcdf",
            }
            try:
                result = client.retrieve("reanalysis-era5-land", request)
                result.download(str(out_file))
                sz = out_file.stat().st_size / 1024 / 1024
                print(f"[{n_done}/{n_total}] {year}-{month} 下载完成 ({sz:.1f} MB)")
            except Exception as e:
                print(f"[{n_done}/{n_total}] {year}-{month} 失败: {e}")
                continue
            time.sleep(1)
        
        # 提取逐日极值
        try:
            ds = xr.open_dataset(out_file)
            t2m = ds["t2m"].resample(time="1D")
            tmax = t2m.max().mean(dim=["latitude", "longitude"]).values
            tmin = t2m.min().mean(dim=["latitude", "longitude"]).values
            tp = ds["tp"].resample(time="1D").sum().mean(dim=["latitude", "longitude"]).values * 1000
            times = pd.to_datetime(ds["t2m"].resample(time="1D").max().time.values)
            ds.close()
            
            n = len(times)
            df = pd.DataFrame({
                "date": times,
                "year": times.year,
                "month": times.month,
                "day": times.day,
                "tmax_K": tmax,
                "tmin_K": tmin,
                "prec_mm": tp,
            })
            year_dfs.append(df)
        except Exception as e:
            print(f"  → 处理失败: {e}")
    
    if year_dfs:
        all_dfs.append(pd.concat(year_dfs, ignore_index=True))

# 合并
print("\n▶ 合并数据...")
full_df = pd.concat(all_dfs, ignore_index=True).sort_values("date").reset_index(drop=True)
full_df["tmax_K"] = full_df["tmax_K"].clip(200, 330)
full_df["tmin_K"] = full_df["tmin_K"].clip(180, 310)
full_df["prec_mm"] = full_df["prec_mm"].clip(0, 500)

print(f"总计: {len(full_df)} 天逐日记录")

# 极端指数
gs = full_df[full_df["month"].between(3, 9)]
tmax_95p = gs["tmax_K"].quantile(0.95)
tmin_5p  = gs["tmin_K"].quantile(0.05)
prec_95p = gs["prec_mm"].quantile(0.95)

print(f"\n平谷区 1981-2010 生长季(3-9月) 极端气候指数:")
print(f"  Tmax_95p = {tmax_95p:.2f} K ({tmax_95p - 273.15:.1f} °C)")
print(f"  Tmin_5p  = {tmin_5p:.2f} K ({tmin_5p - 273.15:.1f} °C)")
print(f"  Prec_95p = {prec_95p:.1f} mm/day")

# 年统计
yearly = gs.groupby("year").agg(
    tmax_95p=("tmax_K", lambda x: x.quantile(0.95)),
    tmin_5p=("tmin_K", lambda x: x.quantile(0.05)),
    prec_95p=("prec_mm", lambda x: x.quantile(0.95)),
    tmax_mean=("tmax_K", "mean"),
    tmin_mean=("tmin_K", "mean"),
    prec_mean=("prec_mm", "mean"),
).reset_index()

yearly["tmax_95p_C"] = yearly["tmax_95p"] - 273.15
yearly["tmin_5p_C"] = yearly["tmin_5p"] - 273.15

# 输出
full_df.to_csv(OUT_DIR / "era5_daily_pinggu_1981-2010.csv", index=False)
yearly.to_csv(OUT_DIR / "era5_yearly_extremes_1981-2010.csv", index=False, float_format="%.3f")

pd.DataFrame({
    "指标": ["Tmax_95p (K)", "Tmax_95p (°C)", "Tmin_5p (K)", "Tmin_5p (°C)", "Prec_95p (mm/day)"],
    "数值": [round(tmax_95p, 2), round(tmax_95p - 273.15, 1),
             round(tmin_5p, 2), round(tmin_5p - 273.15, 1),
             round(prec_95p, 1)],
}).to_csv(OUT_DIR / "era5_climate_indices_summary.csv", index=False)

# 清理临时文件
import shutil
shutil.rmtree(TMP_DIR, ignore_errors=True)

print("\n✅ 完成! 极端气候指数已就绪。")
