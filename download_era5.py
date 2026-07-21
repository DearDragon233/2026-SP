"""
ERA5-Land 逐小时数据下载 + 极端气候指数计算
区域: 平谷区 (116.8-117.5E, 40.0-40.5N)
时间: 1981-2010 生长季 (3-9月)
变量: 2m温度 → Tmax_95p/Tmin_5p, 总降水 → Prec_95p
"""

import cdsapi
import xarray as xr
import numpy as np
import pandas as pd
from pathlib import Path
import time
import sys

# ===== 配置 =====
OUT_DIR = Path(r"D:\2026-SP\Data\ERA5")
OUT_DIR.mkdir(parents=True, exist_ok=True)

YEARS = list(range(1981, 2011))
MONTHS = ["03", "04", "05", "06", "07", "08", "09"]
DAYS = [f"{d:02d}" for d in range(1, 32)]
HOURS = [f"{h:02d}:00" for h in range(24)]

# 平谷区 bbox [N, W, S, E]
AREA = [40.5, 116.8, 40.0, 117.5]

# ===== 下载函数 =====
def download_year(year):
    """下载单年ERA5-Land数据"""
    out_file = OUT_DIR / f"era5_land_pinggu_{year}.nc"
    
    if out_file.exists() and out_file.stat().st_size > 1000:
        print(f"  [{year}] 已存在，跳过 ({out_file.stat().st_size/1024/1024:.1f} MB)")
        return out_file
    
    client = cdsapi.Client(quiet=True)
    request = {
        "variable": ["2m_temperature", "total_precipitation"],
        "year": str(year),
        "month": MONTHS,
        "day": DAYS,
        "time": HOURS,
        "area": AREA,
        "data_format": "netcdf",
    }
    
    print(f"  [{year}] 提交CDS请求...", end=" ", flush=True)
    result = client.retrieve("reanalysis-era5-land", request)
    print(f"下载中...", end=" ", flush=True)
    result.download(str(out_file))
    print(f"完成 ({out_file.stat().st_size/1024/1024:.1f} MB)")
    return out_file


def process_daily(file_path):
    """从逐小时NetCDF提取逐日最高温/最低温/降水量"""
    ds = xr.open_dataset(file_path)
    
    # 2m_temperature: 逐小时瞬时值 (K) → 日最高/最低 (K)
    t2m = ds["t2m"]  # dims: (time, latitude, longitude)
    
    # 按日期分组取max/min
    t2m_max = t2m.resample(time="1D").max()  # 日最高温
    t2m_min = t2m.resample(time="1D").min()  # 日最低温
    
    # total_precipitation: 逐小时累计 (m) → 日总量 (m)
    tp = ds["tp"]
    tp_daily = tp.resample(time="1D").sum()
    
    # 转为DataFrame: 每个格点一行
    lats = ds.latitude.values
    lons = ds.longitude.values
    
    # 空间平均（平谷区65个1km网格中，ERA5-Land约7x5=35个格点）
    # 取区域均值作为平谷代表值
    tmax_mean = t2m_max.mean(dim=["latitude", "longitude"]).values  # (n_days,)
    tmin_mean = t2m_min.mean(dim=["latitude", "longitude"]).values
    prec_mean = tp_daily.mean(dim=["latitude", "longitude"]).values * 1000  # m → mm
    
    dates = t2m_max.time.values
    
    ds.close()
    
    # 构建DataFrame
    df = pd.DataFrame({
        "date": pd.to_datetime(dates),
        "year": pd.to_datetime(dates).year,
        "month": pd.to_datetime(dates).month,
        "day": pd.to_datetime(dates).day,
        "tmax_K": tmax_mean,
        "tmin_K": tmin_mean,
        "prec_mm": prec_mean,
    })
    
    # 清理异常值
    df["tmax_K"] = df["tmax_K"].clip(200, 330)   # -73 ~ 57°C 范围
    df["tmin_K"] = df["tmin_K"].clip(180, 310)
    df["prec_mm"] = df["prec_mm"].clip(0, 500)   # 日降水 ≤500mm
    
    return df


# ===== 主流程 =====
print("=" * 60)
print("ERA5-Land 平谷区极端气候指数计算")
print("=" * 60)
print(f"年份: {YEARS[0]}-{YEARS[-1]} ({len(YEARS)}年)")
print(f"月份: 3-9月 (生长季)")
print(f"变量: 2m温度 + 总降水")
print(f"输出: {OUT_DIR}")
print("=" * 60)

# Phase 1: 下载
print("\n▶ Phase 1: 下载ERA5-Land数据\n")
all_dfs = []

for year in YEARS:
    try:
        f = download_year(year)
        df = process_daily(f)
        all_dfs.append(df)
        # 删除原始NetCDF节省空间
        f.unlink()
        print(f"  → 已提取 {len(df)} 天逐日数据，删除原始NC")
    except Exception as e:
        print(f"  [{year}] 失败: {e}")
        continue
    time.sleep(2)  # CDS API限速

# Phase 2: 合并 + 计算极端指数
print("\n▶ Phase 2: 计算极端气候指数\n")

full_df = pd.concat(all_dfs, ignore_index=True)
full_df = full_df.sort_values("date").reset_index(drop=True)

print(f"总计: {len(full_df)} 天逐日记录")

# 生长季筛选（保留已下载的3-9月数据）
gs_df = full_df[full_df["month"].between(3, 9)].copy()

# 计算极端分位数
tmax_95p = gs_df["tmax_K"].quantile(0.95)
tmin_5p  = gs_df["tmin_K"].quantile(0.05)
prec_95p = gs_df["prec_mm"].quantile(0.95)

print(f"\n平谷区 1981-2010 生长季(3-9月) 极端气候指数:")
print(f"  Tmax_95p = {tmax_95p:.2f} K ({tmax_95p - 273.15:.1f} °C)")
print(f"  Tmin_5p  = {tmin_5p:.2f} K ({tmin_5p - 273.15:.1f} °C)")
print(f"  Prec_95p = {prec_95p:.1f} mm/day")

# 按年份分别计算（用于后续环境指纹拼接）
yearly_stats = gs_df.groupby("year").agg(
    tmax_95p=("tmax_K", lambda x: x.quantile(0.95)),
    tmin_5p=("tmin_K", lambda x: x.quantile(0.05)),
    prec_95p=("prec_mm", lambda x: x.quantile(0.95)),
    tmax_mean=("tmax_K", "mean"),
    tmin_mean=("tmin_K", "mean"),
    prec_mean=("prec_mm", "mean"),
).reset_index()

yearly_stats["tmax_95p_C"] = yearly_stats["tmax_95p"] - 273.15
yearly_stats["tmin_5p_C"] = yearly_stats["tmin_5p"] - 273.15

# Phase 3: 输出
print("\n▶ Phase 3: 保存结果\n")

# 完整逐日数据
daily_out = OUT_DIR / "era5_daily_pinggu_1981-2010.csv"
full_df.to_csv(daily_out, index=False)
print(f"逐日数据: {daily_out} ({daily_out.stat().st_size/1024:.1f} KB)")

# 年统计
yearly_out = OUT_DIR / "era5_yearly_extremes_1981-2010.csv"
yearly_stats.to_csv(yearly_out, index=False, float_format="%.3f")
print(f"年统计:   {yearly_out}")

# 30年气候态汇总（用于数据清单）
summary = pd.DataFrame({
    "指标": ["Tmax_95p (K)", "Tmax_95p (°C)", "Tmin_5p (K)", "Tmin_5p (°C)", "Prec_95p (mm/day)"],
    "数值": [round(tmax_95p, 2), round(tmax_95p - 273.15, 1),
             round(tmin_5p, 2), round(tmin_5p - 273.15, 1),
             round(prec_95p, 1)],
})
summary_out = OUT_DIR / "era5_climate_indices_summary.csv"
summary.to_csv(summary_out, index=False)
print(f"极端指数摘要: {summary_out}")

# 打印年度变化
print("\n年度极端指数变化:")
print(yearly_stats[["year", "tmax_95p_C", "tmin_5p_C", "prec_95p"]].to_string(index=False))

print("\n✅ 完成! ERA5-Land极端气候指数已就绪，可接入环境指纹矩阵。")
