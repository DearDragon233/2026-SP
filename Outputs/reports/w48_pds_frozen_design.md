# W48 平顶山独立检验设计

本轮在查看模型误差前冻结方案。开发集是 W44 的冀鲁主口径 79 条县年。河南平顶山只用于测试，保留 2019、2020、2021 三个收获年。每个测试年只用更早的冀鲁县年重新训练。使用 W44 截止 4 月 30 日的六项天气指纹和 W45 的训练均值、Ridge、随机森林及原参数。每个模型分别用统计和遥感单产训练，均对同一批留出的平顶山官方统计单产计分。MAE 为主指标，同时保留 RMSE、偏差和逐行预测。主试验前无河南数据参与训练、模型选择或阈值制定。

主分析沿用 W42 预设的正值遥感面积与统计播种面积比 2/3–1.50。严格口径为 0.80–1.25，诊断口径只要求有正值遥感覆盖。模型训练始终用开发集主口径，只有测试纳入规则变化，便于比较样本组成。另按是否有气象特征落在训练逐列最小值和最大值之外报告覆盖与误差。用删一收获年、删一天气序列和删一县后的配对 MAE 差异作为敏感性范围。三年和少数气象序列无法支持稳定的总体区间。

| 收获年 | 正值覆盖县年 | 主分析 | 严格口径 |
|---|---:|---:|---:|
| 2019 | 6 | 4 | 3 |
| 2020 | 1 | 1 | 0 |
| 2021 | 2 | 1 | 0 |
| 合计 | 9 | 6 | 3 |

全部候选县对应 4 套不同的气象日值序列，主分析对应 3 套，与冀鲁开发集无相同县或相同日值序列。三个被主口径排除的县年均因遥感覆盖偏大。2019 年叶县的面积比为 1.50211，严格按预定 1.50 阈值执行。严格口径只覆盖 2019 年，比较时需并列检查样本构成。收获年遥感覆盖和统计面积仅作回溯资格筛查，业务预测需要另行核实资料可用日期。

从仓库根目录重跑。先按 W41 说明取得同版县界与 2021 年完整栅格，完整栅格 MD5 为 `98c9ef3723874893177b4c67c7fdfcba`。2019–2020 年由脚本取得平顶山窗口并记录 SHA-256。原始大文件存放在 `Data/external/ncp_yield_pairing/download/`。

```bash
stats=Data/external/w47_pds_wheat_statistics.csv
download=Data/external/ncp_yield_pairing/download
for year in 2019 2020; do
    python src/s2_model_validation/w43_fetch_yield_windows.py "$year" --statistics "$stats" --prefix w48
    python src/s2_model_validation/w41_pair_county_yield.py "$year" --only-additional --additional-stats "$stats" --raster "$download/w48_${year}_counties.sparse.tif" --output "Outputs/reports/w48_pds_pairing_$year.csv"
done
python src/s2_model_validation/w41_pair_county_yield.py 2021 --only-additional --additional-stats "$stats" --raster "$download/2021ChinaWheatYield30m.tif" --output Outputs/reports/w48_pds_pairing_2021.csv
python src/s2_model_validation/w48_freeze_pds.py
```

[县年冻结表](w48_pds_frozen.csv) · [2019 遥感字节清单](w48_remote_windows_2019.json) · [2020 遥感字节清单](w48_remote_windows_2020.json) · [天气来源与哈希](w48_pds_power_sources.json) · [县界与完整栅格](../../Data/external/w41_county_yield_pairing.md)
