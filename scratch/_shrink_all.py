from PIL import Image
import os
files = [
    r"D:\2026-SP\Outputs\figures\main\fig01_feature_audit_dashboard.tiff",
    r"D:\2026-SP\Outputs\figures\main\fig03_model_comparison.tiff",
    r"D:\2026-SP\Outputs\figures\main\fig04_feature_selection_dashboard.tiff",
    r"D:\2026-SP\Outputs\figures\main\fig05_cv_scheme_comparison.tiff",
    r"D:\2026-SP\Outputs\figures\main\fig06_qrf_uncertainty.tiff",
]
for f in files:
    if os.path.exists(f):
        im = Image.open(f)
        im.save(f, compression="tiff_lzw", dpi=(600,600))
        print(os.path.basename(f), round(os.path.getsize(f)/1048576,1), "MB")
