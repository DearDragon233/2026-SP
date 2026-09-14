import pandas as pd
df = pd.read_csv(r"D:\2026-SP\Outputs\intermediate\zenodo_yield_2021_grid.csv")
print("shape:", df.shape)
print("zenodo cols:", [c for c in df.columns if "zenod" in c])
z = df["zenodo_yield_tha"]
print("notna:", z.notna().sum(), "/", len(df))
n = df["n_px"]
print("n_px: max=", n.max(), "| >0:", (n>0).sum(), "| >=5:", (n>=5).sum(), "| >=20:", (n>=20).sum())
v = z.dropna()
if len(v):
    print("yield tha:", round(v.mean(),2), "+-", round(v.std(),2), "range", round(v.min(),2), "-", round(v.max(),2))
print("lon range:", df.lon.min(), "-", df.lon.max(), "| lat range:", round(df.lat.min(),3), "-", round(df.lat.max(),3))
ok = df[n > 0]
if len(ok):
    print("n_px>0 grids lon:", round(ok.lon.min(),3), "-", round(ok.lon.max(),3), "| lat:", round(ok.lat.min(),3), "-", round(ok.lat.max(),3))
