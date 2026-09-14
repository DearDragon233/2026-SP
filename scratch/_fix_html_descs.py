with open(r'D:\2026-SP\Agronomy项目启动会_完整版.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Line 293 (0-indexed) has QA-03 old text
# Line 294 (0-indexed) has QA-06 old text

old03 = lines[264]
new03 = '      <strong>内容：</strong>贝叶斯融合产量全格网地图（黑色方框 = Xiao2024 实测点） | 三源产量分布对比（Ensemble / Xiao2024实测 / 县统计先验 6.00 t/ha） | 产量来源饼图（43实测 + 191融合） | 每格网不确定性地图 | 北京统计局官方夏粮公报来源表 | 产量质量评估摘要<br>\n'
lines[264] = new03

old03_2 = lines[265]
new03_2 = '      <strong>结论：</strong>全部 234 个格网已填充产量估计（均值 6.58，标准差 0.35 t/ha）。方差从 Ridge-only 的 0.09 成功恢复到 0.35。43 个实测点保持 Xiao2024 原始值不变，其余 191 个格网通过县统计先验（平谷估算 6.00 t/ha）进行贝叶斯约束——融合结果比纯过程模型（均值 ~7.21 t/ha）更接近统计真实值。数据来源为北京统计局 2021/2023/2025 年夏粮公报（tjj.beijing.gov.cn），平谷因平原灌溉条件（金海湖 + 泃河），常年高于全市均值 8-15%。\n'
lines[265] = new03_2

old06 = lines[293]
new06 = '      <strong>内容：</strong>SHAP 特征重要性 Top-25（Ensemble 产量版） | Boruta 确认/拒绝饼图（4/71 vs 67/71） | 域级变量数 vs 确认数 vs 平均 SHAP 综合图 | 特征选择摘要卡<br>\n'
lines[293] = new06

old06_2 = lines[294]
new06_2 = '      <strong>结论：</strong>基于更真实（方差 0.35）的 Ensemble 产量后，Boruta 确认变量从 Ridge 版的 33 个暴跌至 4 个（bio9 / tavg_12 / bio1 / bio11）。Top-2 均为冬季温度特征——反映北京冬小麦越冬期温度对产量的主导作用。土壤有机碳（soc_dgkg）首次进入前 5，坡度进入前 10——土壤和地形信号在更真实产量目标下被释放出来。SHAP 80% 累积需前 62 个变量（气候 51 + 土壤 8 + 地形 3），无少数变量能单独主导预测。\n'
lines[294] = new06_2

with open(r'D:\2026-SP\Agronomy项目启动会_完整版.html', 'w', encoding='utf-8') as f:
    f.writelines(lines)
print('Done!')
