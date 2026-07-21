# 2026-SP: 育种模型环境指纹矩阵

平谷区冬小麦环境指纹矩阵构建——基于WorldClim/SRTM/SoilGrids/CMIP6多源数据。

## 数据产品

| 文件 | 说明 |
|------|------|
| `Outputs/pinggu_environmental_data.csv` | **主数据**：234网格×73变量环境指纹矩阵 |
| `Data_checklist v2.0.xlsx` | 65维数据获取状态清单 |

## 变量维度 (73列)

- **坐标** (2): lon, lat
- **极端气候代理** (3): bio5/bio6/bio13 → Tmax_95p/Tmin_5p/Prec_95p
- **Bioclimatic** (19): bio1-bio19
- **月度降水** (12): prec_01~12
- **月均温** (12): tavg_01~12
- **GDD** (14): 月度GDD + 生长季GDD + 全年GDD
- **地形** (3): elevation, slope, aspect
- **土壤** (8): clay, sand, silt, SOC, BD, CEC, pH, nitrogen

## 数据来源

| 数据源 | 分辨率 | 引用 |
|--------|--------|------|
| WorldClim 2.1 | 2.5 arc-min (~4.6km) | Fick & Hijmans 2017 |
| SRTM (CGIAR v4) | 90m → 4.6km | Jarvis et al. 2008 |
| SoilGrids 2.0 | 5km → 4.6km | Poggio et al. 2021 |
| CMIP6 (SSP2-4.5/SSP5-8.5) | 年值 | O'Neill et al. 2016 |

## 目录结构

```
2026-SP/
├── Data/                    # 原始数据（不上传GitHub）
│   ├── WorldClim/           # 43 tif (~2.3 GB)
│   ├── SRTM/                # 1 tif (~70 MB)
│   ├── SoilGrids_wgs84/     # 8 tif (~58 MB)
│   ├── CMIP6/               # CO2浓度CSV
│   └── Variety/             # 品种性状模板CSV
├── Outputs/                 # 输出数据产品
│   └── pinggu_environmental_data.csv
├── Scripts/                 # 数据处理脚本
│   └── *.py
├── Personal/                # 私人文档（不上传）
├── *.docx/.md               # 项目文档
└── README.md
```

## 复现步骤

1. 下载原始数据：参考 `数据下载操作手册.md`
2. 提取平谷网格：`python extract_env_data_v2.py`
3. 合并土壤数据：`python merge_soilgrids.py`
4. 修正土壤单位：`python fix_soil_units.py`
5. 验证覆盖范围：`python check_coverage.py`

## 环境要求

```bash
pip install pandas numpy rasterio matplotlib openpyxl
```
