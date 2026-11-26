p = r'D:\2026-SP\Paper\Manuscript_v1.0_Prediction_Level_and_Pattern.md'
s = open(p, encoding='utf-8').read()
n = 0
def rep(old, new):
    global s, n
    assert s.count(old) == 1, f"anchor count {s.count(old)}: {old[:70]}"
    s = s.replace(old, new); n += 1

# ---- 3.5 Results: state what the correlation rests on ----
rep("After re-centring it was 102.6 kg/ha better than its baseline. Observed yields in Pingdingshan are heterogeneous (SD 757 kg/ha) and an oracle constant would still score 628 kg/ha, so in this region most of the available skill lies in the ranking. The result held on the unscreened set of nine county-years (r = 0.90, p = 0.006); the strict set has three county-years and cannot support a rank test.",
    "After re-centring it was 102.6 kg/ha better than its baseline. Observed yields in Pingdingshan are heterogeneous (SD 757 kg/ha) and an oracle constant would still score 628 kg/ha, so in this region most of the available skill lies in the ranking.\n\n"
    "The correlation rests on one county-year. The six county-years share three weather series, and the random forest returned the same prediction (7020.2 kg/ha) for the three counties on one series, so there are only four distinct predictions. Lushan county in 2019 had the lowest observed yield (3930 kg/ha, 1861 kg/ha below the mean of the other five) and also the lowest prediction. Omitting it lowered the correlation to r = 0.52 (n = 5). The model therefore separated one low-yielding county from the rest; it did not reproduce a yield gradient across counties. On the unscreened set of nine county-years the correlation was r = 0.90 (p = 0.006), and the strict set has three county-years and cannot support a rank test.")

# ---- Abstract: do not overstate ----
rep("In Pingdingshan the reverse held: a satellite-trained random forest had the worst MAE and the only significantly positive within-region rank correlation (r = 0.92, p = 0.017, n = 6).",
    "In Pingdingshan the reverse held: a satellite-trained random forest had the worst MAE and the only significantly positive within-region rank correlation (r = 0.92, p = 0.017, n = 6), although that correlation rested on a single low-yielding county.")

# ---- 4.2 Discussion ----
rep("The only positive rank skill appeared with a satellite-trained random forest in the region with the most heterogeneous yields. The finding rests on six county-years, a bootstrap interval of 0.43 to 0.999 and a single model arm, so we report it as a hypothesis. A satellite training label supplies many more spatial units than yearbooks do, and a flexible estimator may learn within-region contrasts from it that a linear model cannot. Testing this requires a larger external panel with more regions.",
    "The only positive rank skill appeared with a satellite-trained random forest in the region with the most heterogeneous yields. The finding rests on six county-years from three weather series, a bootstrap interval of 0.43 to 0.999, a single model arm and, as Section 3.5 shows, one county-year that drives the correlation. We report it as a hypothesis. A satellite training label supplies many more spatial units than yearbooks do, and a flexible estimator may learn within-region contrasts from it that a linear model cannot, but our data do not distinguish that from the model having identified one county with a different weather series. Testing this requires an external panel with more counties, more weather series and more regions.")

# ---- 4.1: soften 'ranked county-years' wording ----
rep("A random forest that ranked county-years with r = 0.92 had the highest MAE in the same test because its level was far too low.",
    "A random forest whose predictions correlated with observed county-year yields at r = 0.92 had the highest MAE in the same test because its level was far too low.")

# ---- Limitations ----
rep("The external evidence covers two prefectures of one province, and the Pingdingshan primary set has six county-years from five counties, two of them from a single county (Yexian) in two successive years.",
    "The external evidence covers two prefectures of one province. The Pingdingshan primary set has six county-years from five counties on three weather series, two of the county-years from Yexian in successive years, and its rank correlation falls to 0.52 when the lowest-yielding county-year is omitted. The Zhoukou set has 19 county-years on seven weather series and no county-year inside the training range of the weather features.")

# ---- Conclusions ----
rep("and the only significant positive rank skill (Pingdingshan, satellite-trained random forest, r = 0.92 on six county-years) came with the highest raw error.",
    "and the only significant positive rank skill (Pingdingshan, satellite-trained random forest, r = 0.92 on six county-years, dependent on one county-year) came with the highest raw error.")

open(p, 'w', encoding='utf-8').write(s)
print("leverage text applied:", n, "edits")
