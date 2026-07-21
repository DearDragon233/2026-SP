import pandas as pd, os
df = pd.read_csv(r'D:\2026-SP\Outputs\pinggu_environmental_data.csv')
soil_cols = ['clay_pct','sand_pct','silt_pct','soc_dgkg','bdod_kgdm3','cec_cmolkg','phh2o']
df = df.drop(columns=[c for c in soil_cols if c in df.columns], errors='ignore')
print(f'Shape: {df.shape}, Columns: {len(df.columns)}')
for c in ['bio1','bio5','bio6','bio12','bio13','GDD_gs','elevation_m']:
    vals=df[c].dropna()
    print(f'  {c}: {vals.min():.1f} ~ {vals.max():.1f}')
group_counts = {'coord':2,'extreme_proxy':3,'bioclim':19,'prec_monthly':12,'tavg_monthly':12,'GDD':14,'terrain':3}
print('Groups:')
for k,v in group_counts.items():
    print(f'  {k}: {v}')
df.to_csv(r'D:\2026-SP\Outputs\pinggu_environmental_data.csv', index=False, float_format='%.4f')
sz = os.path.getsize(r'D:\2026-SP\Outputs\pinggu_environmental_data.csv')
print(f'Size: {sz/1024:.0f} KB')
print('Done')
