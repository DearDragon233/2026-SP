from PIL import Image
import os
for f in [r'D:\\2026-SP\\Outputs\\figures\\main\\fig02_shap_importance.tiff', r'D:\\2026-SP\\Outputs\\figures\\main\\fig07_source_sensitivity.tiff']:
    im = Image.open(f)
    im.save(f, compression='tiff_lzw', dpi=(600,600))
    print(f, round(os.path.getsize(f)/1048576,1), 'MB')
