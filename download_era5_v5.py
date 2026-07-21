"""
ERA5-Land 极端气候指数计算 v5
策略: 逐月、每5年一组下载
"""
import cdsapi, xarray as xr, numpy as np, pandas as pd
import zipfile, time, shutil
from pathlib import Path

OUT_DIR = Path(r"D:\2026-SP\Data\ERA5")
OUT_DIR.mkdir(parents=True, exist_ok=True)
TMP_DIR = OUT_DIR / "_tmp"
TMP_DIR.mkdir(exist_ok=True)

MONTHS = ["03", "04", "05", "06", "07", "08", "09"]
ALL_YEARS = list(range(1981, 2011))
YEAR_GROUPS = [ALL_YEARS[i:i+5] for i in range(0, len(ALL_YEARS), 5)]
DAYS = [f"{d:02d}" for d in range(1, 32)]
HOURS = [f"{h:02d}:00" for h in range(24)]
AREA = [40.5, 116.8, 40.0, 117.5]

total_requests = len(MONTHS) * len(YEAR_GROUPS)
print(f"策略: {len(MONTHS)}月 × {len(YEAR_GROUPS)}组(每组5年) = {total_requests} 次请求")
print(f"每组项目数: 5×31×24×2 = 7,440 个字段")
print("=" * 60)

client = cdsapi.Client()
all_dfs = []
n = 0

for month in MONTHS:
    for grp in YEAR_GROUPS:
        n += 1
        yrange = f"{grp[0]}-{grp[-1]}"
        zip_file = TMP_DIR / f"era5_m{month}_y{yrange}.zip"
        nc_file  = TMP_DIR / f"era5_m{month}_y{yrange}.nc"
        label = f"[{n}/{total_requests}] {yrange} M{month}"
        
        if nc_file.exists() and nc_file.stat().st_size > 1000:
            print(f"{label} 缓存已有")
        else:
            try:
                print(f"{label} 请求...", end=" ", flush=True)
                result = client.retrieve("reanalysis-era5-land", {
                    "variable": ["2m_temperature", "total_precipitation"],
                    "year": [str(y) for y in grp],
                    "month": [month],
                    "day": DAYS,
                    "time": HOURS,
                    "area": AREA,
                    "data_format": "netcdf",
                })
                result.download(str(zip_file))
                
                with zipfile.ZipFile(zip_file) as z:
                    z.extract("data_0.nc", TMP_DIR)
                shutil.move(str(TMP_DIR / "data_0.nc"), str(nc_file))
                zip_file.unlink()
                sz = nc_file.stat().st_size / 1024
                print(f"OK {sz:.0f} KB")
            except Exception as e:
                err = str(e)[:120]
                if "cost limits" in err.lower():
                    print(f"超额! 需更小分组")
                else:
                    print(f"失败: {err}")
                continue
        
        # 提取
        try:
            ds = xr.open_dataset(nc_file, engine="netcdf4")
            t2m = ds["t2m"].resample(time="1D")
            tp = ds["tp"].resample(time="1D")
            
            df = pd.DataFrame({
                "date": pd.to_datetime(t2m.max().time.values),
                "tmax_K": t2m.max().mean(dim=["latitude", "longitude"]).values,
                "tmin_K": t2m.min().mean(dim=["latitude", "longitude"]).values,
                "prec_mm": tp.sum().mean(dim=["latitude", "longitude"]).values * 1000,
            })
            df["year"] = df["date"].dt.year
            df["month"] = df["date"].dt.month
            df["day"] = df["date"].dt.day
            all_dfs.append(df)
            ds.close()
        except Exception as e:
            print(f"  处理失败: {e}")
        
        time.sleep(0.5)

print("\n▶ 合并与计算...")
full = pd.concat(all_dfs, ignore_index=True).sort_values("date").reset_index(drop=True)
full["tmax_K"] = full["tmax_K"].clip(200, 330)
full["tmin_K"] = full["tmin_K"].clip(180, 310)  
full["prec_mm"] = full["prec_mm"].clip(0, 500)

gs = full[full["month"].between(3, 9)]
Tmax_95p = float(gs["tmax_K"].quantile(0.95))
Tmin_5p  = float(gs["tmin_K"].quantile(0.05))
Prec_95p = float(gs["prec_mm"].quantile(0.95))

print(f"\n=== 平谷区 1981-2010 生长季(3-9月) 极端气候指数 ===")
print(f"  记录数: {len(full)} 天")
print(f"  Tmax_95p = {Tmax_95p:.2f}K ({Tmax_95p-273.15:.1f}°C)")
print(f"  Tmin_5p  = {Tmin_5p:.2f}K ({Tmin_5p-273.15:.1f}°C)")
print(f"  Prec_95p = {Prec_95p:.1f} mm/day")

# 保存
full.to_csv(OUT_DIR / "era5_daily_pinggu_1981-2010.csv", index=False)
full.groupby("year").agg(
    Tmax_95p=("tmax_K", lambda x: x.quantile(0.95)),
    Tmin_5p=("tmin_K", lambda x: x.quantile(0.05)),
    Prec_95p=("prec_mm", lambda x: x.quantile(0.95)),
).to_csv(OUT_DIR / "era5_yearly_extremes.csv", float_format="%.3f")

pd.DataFrame({"indicator": ["Tmax_95p_K","Tmax_95p_C","Tmin_5p_K","Tmin_5p_C","Prec_95p_mm"],
              "value": [round(Tmax_95p,2), round(Tmax_95p-273.15,1),
                       round(Tmin_5p,2), round(Tmin_5p-273.15,1),
                       round(Prec_95p,1)]
}).to_csv(OUT_DIR / "era5_climate_indices.csv", index=False)

shutil.rmtree(TMP_DIR, ignore_errors=True)
print("✅ 完成!")
