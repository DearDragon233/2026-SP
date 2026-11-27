p = r'D:\2026-SP\src\s5_figures_main\w55_build_paper2_pdf.py'
s = open(p, encoding='utf-8').read()
s = s.replace('put("[Author names to be declared]", 11, ITAL, after=4, align=0)',
              'put("Yucheng Peng 1,*, Yangyi Liang 1, Xiaotong Shang 1 and Xihao Lin 1", 11, BODY, after=4, align=0)')
s = s.replace('put("[Affiliations to be declared]", 8.5, ITAL, after=3, align=0)',
              'put("1 College of Future Technology, China Agricultural University, Beijing 100193, China", 8.5, ITAL, after=3, align=0)')
s = s.replace('put("* Correspondence: [to be declared].", 8.5, BODY, after=8, align=0)',
              'put("* Correspondence: [corresponding author email]", 8.5, BODY, after=8, align=0)')
open(p, 'w', encoding='utf-8').write(s)
print('authors hardcoded into builder')
