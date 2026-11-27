# -*- coding: utf-8 -*-
"""Fill the Feature Paper Application Form for paper 2."""
from docx import Document
from docx.shared import Pt
import os

doc = Document(r'C:\Users\18322\Desktop\Feature Paper Application Form for author.docx')
t = doc.tables[0]

abstract = ("County-scale winter wheat yield models are usually judged by mean absolute error (MAE) against "
"held-out statistics. MAE combines two abilities that can be separated: estimating the yield level of a "
"region and ranking the counties within it. We separated them for weather-driven models across three "
"regions of the North China Plain. County-year yields from official yearbooks (Shijiazhuang, Tai'an, "
"Pingdingshan and Zhoukou, 2017 to 2021) were paired with six weather features derived from daily NASA "
"POWER data available by 30 April. Three fixed estimators (training mean, ridge regression, random "
"forest) were trained separately on statistical and satellite-derived labels and scored against the same "
"held-out statistical yields under forward-year, leave-region and joint holdouts, with two external "
"tests in Henan province. Models trained on statistical labels beat the training mean only in "
"forward-year validation (ridge MAE 426.9 versus 496.0 kg/ha); under joint geographic and temporal "
"holdout the training mean was best (470.4 versus 519.1 kg/ha and above). In the Zhoukou external test, "
"ridge appeared to transfer skill (MAE 380.2 versus 920.4 kg/ha, robust to 17 group deletions), but its "
"predictions ranked county-years inversely to observation (r = -0.79, permutation p = 0.0001; stable "
"when any one county-year is omitted); the whole gain came from extrapolating the regional mean "
"upward, and re-centring removed it. In Pingdingshan the reverse held: a satellite-trained random "
"forest had the worst MAE and the only significantly positive within-region rank correlation "
"(r = 0.92, p = 0.017, n = 6), although that correlation rested on a single low-yielding county. "
"Across 20 fitted model arms, the sign of the raw MAE advantage and of the advantage after re-centring "
"agreed in 12 cases and disagreed in 8. We recommend reporting level error and within-region rank skill "
"separately and retaining the training-mean baseline in every transfer test.")

t.rows[0].cells[1].text = ("Level and Pattern in Transferred County Wheat Yield Models: Weather Features, "
                           "Training Labels and a Training-Mean Baseline Across Three North China Regions")
t.rows[1].cells[1].text = "Article"
t.rows[2].cells[1].text = "3100"
t.rows[3].cells[1].text = abstract
t.rows[4].cells[1].text = ("Yucheng Peng (pengyucheng@cau.edu.cn); "
                           "Yangyi Liang (email@cau.edu.cn); "
                           "Xiaotong Shang (email@cau.edu.cn); "
                           "Xihao Lin (email@cau.edu.cn)")
t.rows[5].cells[1].text = ("Yucheng Peng, College of Future Technology, "
                           "China Agricultural University, Beijing 100193, China. "
                           "Email: pengyucheng@cau.edu.cn")
t.rows[6].cells[1].text = "College of Future Technology, China Agricultural University, Beijing 100193, China"

out = r'D:\2026-SP\ManageFiles\Submission_package_Paper2\Feature_Paper_Application_Form_filled.docx'
doc.save(out)
print("form saved:", os.path.getsize(out), "bytes")
