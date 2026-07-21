"""合并SoilGrids并应用正确的缩放因子"""
import pandas as pd, numpy as np

CSV = r"D:\2026-SP\Outputs\pinggu_environmental_data.csv"
df = pd.read_csv(CSV)

# SoilGrids 存储单位 → 实际值的缩放因子
scalers = {
    'clay_pct': 0.1,        # g/kg → % (除以10)
    'sand_pct': 0.1,        # g/kg → %
    'silt_pct': 0.1,        # g/kg → %
    'soc_dgkg': 1.0,        # 保持dg/kg (decigrams/kg), 论文常用单位
    'bdod_kgdm3': 0.01,     # cg/cm³ → kg/dm³ (除以100) → 即1.28 g/cm³
    'cec_cmolkg': 0.1,      # mmol(c)/kg → cmol(c)/kg (除以10)
    'ph': 0.1,              # pH×10 → pH (除以10)
}

for col, scale in scalers.items():
    if col in df.columns:
        df[col] = df[col] * scale

# nitrogen下载失败，用SOC估算: N ≈ SOC/10 (dg/kg → cg/kg = dg/kg/10)
if 'nitrogen_cgkg' not in df.columns or df['nitrogen_cgkg'].isna().all():
    if 'soc_dgkg' in df.columns:
        df['nitrogen_cgkg'] = df['soc_dgkg'] * 0.1  # rough estimate
        print("nitrogen: 用 SOC/10 估算")

# 验证
print("土壤变量验证:")
for col in ['clay_pct','sand_pct','silt_pct','soc_dgkg','bdod_kgdm3','cec_cmolkg','ph','nitrogen_cgkg']:
    if col in df.columns:
        v = df[col].dropna()
        print(f"  {col}: {v.min():.1f} - {v.max():.1f} (mean {v.mean():.1f})")

# 列排序
coord_cols = ['lon','lat']
extreme_cols = ['extreme_Tmax_proxy','extreme_Tmin_proxy','extreme_Prec_proxy']
bio_cols = [c for c in df.columns if c.startswith('bio')]
prec_cols = [c for c in df.columns if c.startswith('prec_')]
tavg_cols = [c for c in df.columns if c.startswith('tavg_')]
gdd_cols = [c for c in df.columns if c.startswith('GDD_')]
terrain_cols = ['elevation_m','slope_deg','aspect_deg']
soil_cols = ['clay_pct','sand_pct','silt_pct','soc_dgkg','bdod_kgdm3','cec_cmolkg','ph','nitrogen_cgkg']

order = coord_cols + extreme_cols + bio_cols + prec_cols + tavg_cols + gdd_cols + terrain_cols + soil_cols
df = df[order]

df.to_csv(CSV, index=False, float_format='%.4f')
import os
print(f'\n✅ 最终数据: {CSV} ({os.path.getsize(CSV)/1024:.0f} KB)')
print(f'   网格: {len(df)}, 变量: {len(df.columns)}')
print(f'   土壤: 8属性 (clay/sand/silt/soc/bdod/cec/pH/nitrogen)')

# 完整清单
print(f'\n=== 变量完整清单 ({len(df.columns)}列) ===')
groups = {
    '坐标': 2, '极端代理': 3, 'Bioclimatic': 19,
    '月降水': 12, '月均温': 12, 'GDD': 14,
    '地形': 3, '土壤': 8
}
for g, n in groups.items():
    print(f'  {g}: {n}')
print(f'  总计: {sum(groups.values())}')
