"""
ERA5-Land 逐月下载 + 极端气候指数计算 v4
修复: CDS API返回ZIP包, 需解压data_0.nc
"""
import cdsapi
import xarray as xr
import numpy as np
import pandas as pd
import zipfile, time, shutil
from pathlib import Path

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

total = len(MONTHS)  # let's do one month at a time across all years
print(f"策略: 逐月下载 (每月含全部{len(YEARS)}年)")
print(f"{len(MONTHS)} 次请求, 每次 {len(YEARS)}年")
print("=" * 60)

all_dfs = []

for mi, month in enumerate(MONTHS):
    zip_file = TMP_DIR / f"era5_month{month}.zip"
    nc_file = TMP_DIR / f"data_{month}.nc"
    label = f"[{mi+1}/{len(MONTHS)}] 月份{month}"
    
    if nc_file.exists() and nc_file.stat().st_size > 1000:
        print(f"{label} 已有缓存NC, 跳过下载")
    else:
        try:
            print(f"{label} 提交CDS请求 ({len(YEARS)}年全量)...", end=" ", flush=True)
            result = client.retrieve("reanalysis-era5-land", {
                "variable": ["2m_temperature", "total_precipitation"],
                "year": [str(y) for y in YEARS],
                "month": [month],
                "day": DAYS,
                "time": HOURS,
                "area": AREA,
                "data_format": "netcdf",
            })
            result.download(str(zip_file))
            sz_zip = zip_file.stat().st_size / 1024 / 1024
            
            # 解压
            with zipfile.ZipFile(zip_file) as z:
                z.extract("data_0.nc", TMP_DIR)
            shutil.move(str(TMP_DIR / "data_0.nc"), str(nc_file))
            zip_file.unlink()
            sz_nc = nc_file.stat().st_size / 1024 / 1024
            print(f"完成 ({sz_zip:.1f}MB zip → {sz_nc:.1f}MB nc)")
        except Exception as e:
            print(f"失败: {str(e)[:150]}")
            continue
        time.sleep(1)
    
    # 提取逐日极值
    print(f"{label} 提取逐日统计...", end=" ", flush=True)
    try:
        ds = xr.open_dataset(nc_file, engine="netcdf4")
        t2m = ds["t2m"]
        tp = ds["tp"]
        
        t2m_daily = t2m.resample(time="1D")
        tmax_vals = t2m_daily.max().mean(dim=["latitude", "longitude"]).values
        tmin_vals = t2m_daily.min().mean(dim=["latitude", "longitude"]).values
        prec_vals = tp.resample(time="1D").sum().mean(dim=["latitude", "longitude"]).values * 1000
        dates = pd.to_datetime(t2m_daily.max().time.values)
        ds.close()
        
        df = pd.DataFrame({
            "date": dates, "year": dates.year, "month": dates.month,
            "day": dates.day, "tmax_K": tmax_vals, "tmin_K": tmin_vals,
            "prec_mm": prec_vals,
        })
        all_dfs.append(df)
        print(f"{len(df)} 天")
    except Exception as e:
        print(f"处理失败: {e}")

print("\n▶ 合并 & 计算极端指数...")
full = pd.concat(all_dfs, ignore_index=True).sort_values("date").reset_index(drop=True)
full["tmax_K"] = full["tmax_K"].clip(200, 330)
full["tmin_K"] = full["tmin_K"].clip(180, 310)
full["prec_mm"] = full["prec_mm"].clip(0, 500)

gs = full[full["month"].between(3, 9)]
Tmax_95p = float(gs["tmax_K"].quantile(0.95))
Tmin_5p  = float(gs["tmin_K"].quantile(0.05))
Prec_95p = float(gs["prec_mm"].quantile(0.95))

print(f"\n=== 平谷区 1981-2010 生长季(3-9月) 极端气候指数 ===")
print(f"  Tmax_95p  = {Tmax_95p:.2f} K  ({Tmax_95p - 273.15:.1f} °C)")
print(f"  Tmin_5p   = {Tmin_5p:.2f} K  ({Tmin_5p - 273.15:.1f} °C)")
print(f"  Prec_95p  = {Prec_95p:.1f} mm/day")
print(f"  总记录数: {len(full)} 天")

# 输出
full.to_csv(OUT_DIR / "era5_daily_pinggu_1981-2010.csv", index=False)

yearly = gs.groupby("year").agg(
    Tmax_95p=("tmax_K", lambda x: x.quantile(0.95)),
    Tmin_5p=("tmin_K", lambda x: x.quantile(0.05)),
    Prec_95p=("prec_mm", lambda x: x.quantile(0.95)),
).reset_index()
yearly["Tmax_95p_C"] = yearly["Tmax_95p"] - 273.15
yearly["Tmin_5p_C"] = yearly["Tmin_5p"] - 273.15
yearly.to_csv(OUT_DIR / "era5_yearly_extremes.csv", index=False, float_format="%.3f")

pd.DataFrame({
    "indicator": ["Tmax_95p_K", "Tmax_95p_C", "Tmin_5p_K", "Tmin_5p_C", "Prec_95p_mm_day"],
    "value": [round(Tmax_95p, 2), round(Tmax_95p - 273.15, 1),
              round(Tmin_5p, 2), round(Tmin_5p - 273.15, 1),
              round(Prec_95p, 1)],
}).to_csv(OUT_DIR / "era5_climate_indices.csv", index=False)

shutil.rmtree(TMP_DIR, ignore_errors=True)
print("\n✅ 完成!")
