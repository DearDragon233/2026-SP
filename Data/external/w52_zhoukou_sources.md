# W52 周口县年统计候选数据

从周口市统计局下载三期电子年鉴，三个 ZIP 均通过压缩包完整性检查。每期使用 `excel/3-15.xlsx`（播种面积）、`excel/3-16.xlsx`（总产）和 `excel/3-17.xlsx`（单位面积产量）的 G 列，按 A 列县名配对。原表分别使用千公顷、万吨和千克/公顷。

| 收获年 | 年鉴 | 原始 ZIP SHA-256 |
|---|---|---|
| 2019 | [周口统计年鉴 2020](https://tjj.zhoukou.gov.cn/sitesources/tjj/page_pc/tjfw/tjsj/tjnj/articleD7BB8F30910B4E9CA3E33A0352632F34.html) | `91ee20b34fed410c3b122ac4bf1ef86fb9efcfb0e684840ead914689d5206e03` |
| 2020 | [周口统计年鉴 2021](https://tjj.zhoukou.gov.cn/sitesources/tjj/page_pc/tjfw/tjsj/tjnj/article1cbc5ffc13f74a2298528088c325b2ea.html) | `5decdc540239a5dc6045e287c64418a7edd618a6f1971eae69ac4b822326e301` |
| 2021 | [周口统计年鉴 2022](https://tjj.zhoukou.gov.cn/sitesources/tjj/page_pc/tjfw/tjsj/tjnj/article9be64ef4759c4569a8e81137a3d628a6.html) | `f9e5f6acbbf1c2fd9dc2c38a5abe9f9c7d2044e225333f6d2f68dd992d329e4a` |

[24 条候选县年](w52_zhoukou_candidate_stats.csv)记录原表值、版次和单元格。扶沟、西华、商水、沈丘、郸城、太康、鹿邑及项城各有三年。面积和总产均为正值，按原始量纲换算的单产与原表相差小于 1 kg/ha。初始候选限三年同名的县或县级市。淮阳跨年由县改列区，待查县界与统计连续性。川汇区、开发区及周口市汇总暂不纳入。

表中原作物名称为小麦。周口位于公开研究覆盖的河南冬小麦区，县年主要季型与统计范围仍需核证。后续核对县界和实际气象网格，检查遥感正值覆盖，按既有规则锁定测试样本。当前这 24 条记录是统计候选，尚未参与训练或打分。[河南冬小麦面积研究](https://www.chinaagrisci.com/CN/10.3864/j.issn.0578-1752.2021.11.005) · [先前外部试验规则](../../Outputs/reports/w48_pds_frozen_design.md)
