p = r'D:\2026-SP\Paper\Manuscript_v1.0_Prediction_Level_and_Pattern.md'
s = open(p, encoding='utf-8').read()
n = 0
def rep(old, new):
    global s, n
    assert s.count(old) == 1, f"anchor count {s.count(old)}: {old[:70]}"
    s = s.replace(old, new); n += 1

# Abstract
rep("but its predictions ranked counties inversely to observation (r = -0.79, permutation p = 0.0001); the whole gain came from extrapolating the regional mean upward, and re-centring removed it.",
    "but its predictions were inversely ordered against observed county-year yields (r = -0.79, permutation p = 0.0001; stable when any one county-year is omitted); the whole gain came from extrapolating the regional mean upward, and re-centring removed it.")

# 3.6 second paragraph
rep("Ridge predictions varied much more (SD 156.1) and in the wrong direction, with a correlation to observed yield of -0.79 (permutation p = 0.0001, bootstrap interval -0.91 to -0.65). All 19 predictions were below observation, with a mean bias of -380.2 kg/ha and county means between -349.9 and -399.5. None of the 19 test county-years had all six weather features inside the training range.",
    "Ridge predictions varied much more (SD 156.1) and in the wrong direction, with a correlation to observed yield of -0.79 (permutation p = 0.0001, bootstrap interval -0.91 to -0.65). The sign did not depend on any single county-year: omitting one at a time gave r between -0.83 and -0.76. All 19 predictions were below observation, with a mean bias of -380.2 kg/ha and county means between -349.9 and -399.5. None of the 19 test county-years had all six weather features inside the training range.\n\n"
    "The inverse order is a within-county, year-to-year effect. Observed county means in Zhoukou span only 7507 to 7543 kg/ha, and 16% of the observed variance lies between counties; the remaining 84% is variation between years within a county. County means are not ordered inversely (r = 0.21 across the seven counties). Removing county means from both series strengthens the inverse correlation to r = -0.88. The model reversed which year was the better one within a county, which is the component that weather features, varying mainly from year to year, would be expected to capture.")

# Figure 3 caption
rep("the model under-predicts every county-year and orders them inversely.", "the model under-predicts every county-year and orders the county-years inversely to observed yield.")

open(p, 'w', encoding='utf-8').write(s)
print("Zhoukou within-county text applied:", n, "edits")
print("remaining 'ranked counties inversely':", s.count("ranked counties inversely"), "| 'rank counties inversely':", s.count("rank counties inversely"))
