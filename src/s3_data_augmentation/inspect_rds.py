# -*- coding: utf-8 -*-
"""检查 Allregions.rds 结构：对象名、列名、行数、覆盖区域与时段"""
import pyreadr, pandas as pd

r = pyreadr.read_r(r"D:\2026-SP\Data\Management\Xiao2024\Allregions.rds")
print("objects:", list(r.keys()))
for k, df in r.items():
    print(f"\n=== {k} ===")
    print("shape:", df.shape)
    print("columns:", list(df.columns))
    print(df.head(3).to_string())
    for c in df.columns:
        nu = df[c].nunique()
        if nu <= 15:
            print(f"  [levels] {c}: {sorted(map(str, df[c].unique()))[:15]}")
