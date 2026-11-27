import re, os

# ===== 1. Affiliation update across all files =====
files = [
    'Paper/Manuscript_v1.0_Prediction_Level_and_Pattern.md',
    'ManageFiles/Submission_package_Paper2/Title_page.md',
    'ManageFiles/Submission_package_Paper2/Cover_letter.md',
]
for f in files:
    if not os.path.exists(f): continue
    s = open(f, encoding='utf-8').read()
    for old, new in [
        ('College of Agronomy and Biotechnology', 'College of Future Technology'),
        ('College of Agronomy / National Maize Improvement Center', 'College of Future Technology'),
        ('College of Agronomy, China Agricultural University', 'College of Future Technology, China Agricultural University'),
    ]:
        s = s.replace(old, new)
    open(f, 'w', encoding='utf-8').write(s)
print("1. affiliations updated")

# ===== 2. humanizer AI-word cleanup on paper 2 =====
p2 = 'Paper/Manuscript_v1.0_Prediction_Level_and_Pattern.md'
s = open(p2, encoding='utf-8').read()
ai_subs = [
    ('Additionally, ', 'In addition, '),
    ('crucial ', 'critical '),
    ('delve into ', 'examine '),
    ('underscores ', 'underlines '),
    ('showcasing ', 'demonstrating '),
    ('landscape of ', 'situation of '),
    ('pivotal ', 'central '),
]
cnt = 0
for old, new in ai_subs:
    c = s.count(old)
    if c:
        s = s.replace(old, new)
        cnt += c
# also check fulltext for same patterns
p1 = 'Paper/Manuscript_v1.0_fulltext.md'
s1 = open(p1, encoding='utf-8').read()
c1 = 0
for old, new in ai_subs:
    c = s1.count(old)
    if c:
        s1 = s1.replace(old, new)
        c1 += c
open(p1, 'w', encoding='utf-8').write(s1)
print(f"2. AI-word replacements: paper2 {cnt}, fulltext {c1}")

# ===== 3. em-dash cleanup =====
for pp in [p1, p2]:
    ss = open(pp, encoding='utf-8').read()
    nd = len(re.findall(r'[\u2014]', ss))
    if nd:
        ss = re.sub(r' [\u2014] ', ', ', ss)
        ss = re.sub(r'\u2014', '-', ss)
        open(pp, 'w', encoding='utf-8').write(ss)
        print(f"  {pp}: {nd} em-dashes removed")

print("3. done")
