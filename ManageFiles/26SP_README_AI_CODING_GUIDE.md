# 2026-SP 育种模型项目: README & AI Coding 指南

> 给 coworker 的项目速查手册。上半部分是项目 README，下半部分是使用 AI (Claw/GPT/Claude) 编码时必须告知 AI 的上下文。

---

## 一、项目 README

### 项目名称

环境-作物-管理互作模型 (Environment-Crop-Management Interaction Model)

对标: Xiao et al. (2024, *Nature Food* 5:59-71)

### 目标

利用公开数据构建"环境指纹 + 品种性状 + 管理方案"三要素模型，产出两套结果:

1. 最优农艺管理推荐 (氮肥、灌溉、秸秆还田)
2. 最优育种改良方向 (哪些性状值得改良、改良幅度与产量增益的关系)

### 技术架构 (5 层数据流)

| 层 | 名称 | 核心工具 |
|---|------|---------|
| 1 | 数据获取 | rasterio, urllib, 手动下载 |
| 2 | 特征工程 | rasterio, geopandas, pandas |
| 3 | 建模 | xgboost, scikit-learn |
| 4 | 优化 | pymoo (NSGA-II) |
| 5 | 解释与部署 | SHAP, Bootstrap, FastAPI |

### 仓库结构

```
2026-SP/
├── .github/workflows/    # CI/CD
├── data/                 # 数据目录 (gitignore, 不上传大文件)
├── src/
│   ├── data_ingest/      # 数据获取
│   ├── features/         # 特征工程
│   ├── models/           # 建模与训练
│   ├── optimization/     # NSGA-II 优化
│   └── visualization/    # 可视化
├── tests/                # 单元测试
├── docs/                 # 文档
├── notebooks/            # Jupyter 探索
├── requirements.txt
├── Dockerfile
├── README.md
└── .gitignore
```

### 环境搭建

```bash
# 方案一: Conda (推荐)
conda create -n 2026sp python=3.11
conda activate 2026sp
pip install numpy pandas xarray rasterio geopandas xgboost shap scikit-learn pymoo optuna matplotlib seaborn jupyter fastapi uvicorn

# 方案二: venv
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

### 分支策略 (GitHub Flow)

- `main`: 永远可运行，只通过 PR 合并，禁止直接 push
- `feature/xxx`: 从 main 创建，一个分支只做一件事 (如 `feature/add-nsga2-optimizer`)
- `fix/xxx`: 紧急修复 (如 `fix/memory-leak-in-rasterio`)

### 提交信息规范 (Conventional Commits)

| 前缀 | 含义 | 示例 |
|-----|------|------|
| feat | 新功能 | feat: 添加 SHAP 特征重要性分析模块 |
| fix | 修复 bug | fix: 修复 rasterio 内存泄漏问题 |
| docs | 文档 | docs: 更新 API 接口文档 |
| refactor | 重构 | refactor: 将数据加载逻辑提取为独立模块 |
| test | 测试 | test: 添加 XGBoost 交叉验证单元测试 |
| chore | 杂项 | chore: 更新 requirements.txt 依赖版本 |

### 团队分工

| 角色 | 负责 | 核心技能 | 交付物 |
|-----|------|---------|-------|
| 数据工程师 | 第1-2层 | rasterio, geopandas, pandas, xarray | 环境指纹矩阵 (CSV/Parquet) |
| 建模工程师 | 第3-4层 | xgboost, scikit-learn, pymoo, optuna | 训练好的模型 (pkl), 优化结果 CSV |
| 分析工程师 | 第5层 | shap, numpy, scipy, R/tidyverse | 特征重要性图, 不确定性区间, 统计报告 |
| 部署工程师 | 第5层 | FastAPI, Docker, GitHub Actions | Docker 镜像, API 文档, 使用手册 |

---

## 二、AI Coding 指南

使用 AI (Claw/GPT/Claude/Copilot) 写代码前，请把以下内容粘贴给 AI，作为项目上下文。

### 2.1 项目概况 (告诉 AI 这是干什么的)

```
本项目是一个农业模型研究项目，目标是用 XGBoost 模拟作物过程模型 (APSIM)
的输出，然后用 NSGA-II 多目标遗传算法搜索最优管理方案。

研究区域: 北京市平谷区
作物: 冬小麦 + 夏玉米轮作
对标论文: Xiao et al. (2024, Nature Food 5:59-71)

项目代码仓库路径: D:\2026-SP\
数据目录: D:\2026-SP\Data\
```

### 2.2 固定参数 (必须硬编码或配置化)

以下参数是整个项目的"物理常数"，任何代码都应使用这些值，**AI 不能随意改动**:

```yaml
# 空间参数
target_crs: "EPSG:4326"           # 统一坐标系 WGS84
resolution: 0.008333              # 约 1km (度)
grid_points: 65                   # 平谷区 1km 网格点数
study_area: "北京市平谷区"

# 时间参数
growing_season: [3, 4, 5, 6, 7, 8, 9]  # 生长季月份
base_temperatures: [0, 5, 10, 15, 20, 25]  # GDD 基温阈值

# 特征维度 (总计约 55-75 维)
n_bio_vars: 19                    # WorldClim 生物气候变量
n_monthly_clim: 14                # 3-9月月均温 + 月降水
n_terrain: 3                      # 海拔、坡度、坡向
n_soil: 8                         # 砂粒、粉粒、黏粒、SOC、pH、BD、CEC、N
n_co2: 1                          # 大气 CO2 浓度
n_variety: 8                      # 品种性状 (来自品种审定公告)

# 模型目标变量
targets:
  - wheat_yield                    # 小麦产量
  - maize_yield                    # 玉米产量
  - n_leaching                     # 氮淋溶量
  - delta_soc                      # 土壤有机碳变化

# XGBoost 默认超参 (可通过 Optuna 调优)
xgb_defaults:
  n_estimators: 500
  max_depth: 6
  learning_rate: 0.05
  subsample: 0.8
  colsample_bytree: 0.8
  random_state: 42

# NSGA-II 默认参数
nsga2_defaults:
  pop_size: 200
  n_gen: 500
  decision_vars:                   # 管理方案决策变量及其范围
    nitrogen_rate: [0, 300]        # kg/ha
    irrigation_amount: [0, 400]    # mm
    straw_return_rate: [0, 1]      # 0-1 比例

# Bootstrap 不确定性量化
bootstrap:
  n_iterations: 1000
  ci_level: 0.95                   # 95% 置信区间
```

### 2.3 命名与格式规范 (AI 必须遵守)

```
所有代码严格遵循以下规范，违反即为错误:

1. 变量/函数/文件名: snake_case (如 extract_features, build_matrix.py)
2. 列名: 英文小写 + 下划线 (如 bio_1, gdd_10, sand_pct)
3. 缺失值: NaN (决不允许用 -999, -9999 等魔法数字)
4. 类名: PascalCase (如 EnvironmentalFingerprintBuilder)
5. 常量: UPPER_SNAKE_CASE (如 TARGET_CRS, GRID_RESOLUTION)
6. 文件头: 必须包含模块 docstring
7. 可执行代码: 必须放在 if __name__ == "__main__" 中
8. 可配置参数: 抽取到 config.yaml, 禁止硬编码在 Python 中
9. 随机种子: 全局固定为 42 (np.random.seed(42), random_state=42)
```

### 2.4 模块间接口规范 (数据格式约定)

```
所有模块间传递的数据遵循以下约定:

格式: CSV 或 Parquet
行定义: 每一行 = 一个地理位置点 (网格)
列命名: snake_case (如 gdd_10, slope_deg)
缺失值: NaN (不是 -999!)
空间参考: WGS84 (EPSG:4326)
分辨率: 0.008333 度 (约 1km)
坐标列: lon, lat (必须保留)

示例一行数据:
lon,lat,year,bio_1,bio_2,...,gdd_10,...,sand_pct,...,wheat_yield
116.9,40.1,2020,12.5,3.2,...,1850.3,...,42.1,...,6.8
```

### 2.5 关键代码模式 (给 AI 的模板)

**特征工程模块模板:**

```python
"""
特征工程模块: 从原始栅格数据构建环境指纹矩阵

输入: Data/WorldClim/*.tif, Data/SRTM/*.tif, Data/SoilGrids/*.tif
输出: features_matrix.parquet
用法: python -m src.features.build_matrix --config config.yaml
"""
import rasterio
import numpy as np
import pandas as pd
from pathlib import Path


class EnvironmentalFingerprintBuilder:
    """环境指纹构建器"""

    def __init__(self, config):
        self.data_dir = Path(config["data_dir"])
        self.grid_points = pd.read_parquet(config["grid_file"])
        self.target_crs = "EPSG:4326"

    def extract_worldclim_bio(self):
        """提取 19 个生物气候变量"""
        pass

    def extract_all(self):
        """执行完整提取流水线"""
        pass


if __name__ == "__main__":
    main()
```

**模型训练必须使用空间分块交叉验证:**

```
由于空间自相关 (相邻网格环境相似), 简单随机划分会导致过拟合。
必须使用 Spatial Block CV:
- 将 65 个网格按地理位置分为 5 块
- 每次用 4 块训练, 1 块验证
- 旋转 5 次

AI 写模型代码时必须使用此策略, 不能用 train_test_split 简单随机划分。
```

### 2.6 可视化规范

```
所有图表遵循:
- 字体: Times New Roman
- 配色: 色盲友好调色板 (viridis / cividis / ggsci::scale_color_npg)
- 字号: >= 8pt
- 子图标签: (a)(b)(c) 格式 (不是 1,2,3)
- 导出格式: PDF 或 600 DPI TIFF (不是 PNG/JPG)
```

### 2.7 常见坑点 (AI 必须知道的)

```
1. rasterio 在 Windows 上必须用 conda 安装, 不能用 pip
   (conda install -c conda-forge rasterio)

2. 训练前必须检查 NaN:
   df.isnull().sum() 和 np.isinf(X).sum()

3. 大文件 (>100MB) 不上传 Git, 使用 .gitignore 排除

4. SHAP 与某些 matplotlib 版本不兼容:
   使用 shap >= 0.42 + matplotlib >= 3.7

5. R ggplot2 中文显示问题:
   安装 showtext 包 + font_add() 注册中文字体

6. 数据单位间留空格: "180 kg/ha" 不是 "180kg/ha"

7. 缩写首次出现给出全称:
   "Growing Degree Days (GDD)"

8. SoilGrids 数据获取需要使用 vsicurl + COG VRT 方式,
   不是直接下载整个文件
```

### 2.8 快速启动指令 (告诉 AI 的环境)

```
项目根目录: D:\2026-SP
Python 环境: conda activate 2026sp (Python 3.11)
数据目录: D:\2026-SP\Data\
  已有数据（全部就绪，无需额外下载）:
    D:\2026-SP\Data\WorldClim\             (43 tif, 生物气候+月温+月降水)
    D:\2026-SP\Data\SRTM\                  (srtm_60_04.tif, 平谷区DEM)
    D:\2026-SP\Data\SoilGrids_wgs84\       (8 tif, 0-5cm全属性)
    D:\2026-SP\Data\Variety\               (小麦8品种 + 玉米8品种 CSV)
    D:\2026-SP\Data\Management\            (14情景 + Xiao2024公开数据)
    D:\2026-SP\Outputs\                    (环境指纹CSV 234×73)
  
  已否决方案（不再需要）:
    CHELSA (WorldClim已覆盖) | ERA5 (CDS国内不可用)
    CMIP6 (非必需) | 中国土壤数据库 (SoilGrids已覆盖)
```

---

## 附录: 术语速查表

| 英文 | 中文 | 释义 |
|-----|------|------|
| XGBoost | 极限梯度提升 | 结构化数据建模首选算法 |
| SHAP | Shapley 加法解释 | 基于博弈论的模型解释方法 |
| NSGA-II | 非支配排序遗传算法 II | 多目标进化优化算法 |
| GDD | 生长度日 | 作物发育热量累积指标 (度C-日) |
| Bootstrap | 自助法 | 有放回重采样估计统计量分布 |
| Raster | 栅格数据 | 规则网格组成的空间数据 |
| CRS | 坐标参考系 | 地理坐标与平面坐标转换系统 |
| Affine Transform | 仿射变换 | 栅格像素行列号与地理坐标的线性变换 |
| Feature Engineering | 特征工程 | 将原始数据转化为模型可用特征向量 |
| Environmental Fingerprint | 环境指纹 | 每个网格点的多维环境特征向量 (55-75维) |
| Spatial Block CV | 空间分块交叉验证 | 按地理位置分块的交叉验证策略 |
| Pareto Front | 帕累托前沿 | 多目标优化中非支配解的集合 |
| Surrogate Model | 代理模型 | 代替复杂过程模型的简化模型 |
