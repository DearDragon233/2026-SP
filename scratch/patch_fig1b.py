p = r'D:\2026-SP\src\s5_figures_main\w55_fix_fig1_fig2.py'
s = open(p, encoding='utf-8').read()
# 1. shorter titles
s = s.replace('ax.set_title("(a) Zhoukou counties; green passes the primary screen in all years", loc="left", fontweight="bold")',
              'ax.set_title("(a) Zhoukou counties (green: primary screen passed)", loc="left", fontweight="bold", fontsize=8)')
s = s.replace('ax.set_title("(b) Coverage ratio per candidate county-year", loc="left", fontweight="bold")',
              'ax.set_title("(b) Coverage ratio by county-year", loc="left", fontweight="bold", fontsize=8)')
# 2. limit annotations: place at different heights, and to opposite sides
s = s.replace('ax.text(1.52, 1.72, "upper limit 1.5", fontsize=6, color=OK["grey"]); ax.text(0.68, 1.72, "lower limit 2/3", fontsize=6, color=OK["grey"])',
              'ax.text(len(d) - 0.6, 1.545, "upper limit 1.5", fontsize=6, color=OK["grey"], ha="right")\n'
              'ax.text(len(d) - 0.6, 0.705, "lower limit 2/3", fontsize=6, color=OK["grey"], ha="right")')
# 3. label offsets for the two adjacent counties (Xiangcheng / Shenqiu)
s = s.replace('''    r = cov[cov.county == zh].iloc[0]
    ax.text(r.centre_lon, r.centre_lat, PIN[zh], ha="center", va="center", fontsize=6.3,''',
'''    r = cov[cov.county == zh].iloc[0]
    dx, dy = {"项城": (0.0, -0.045), "沈丘": (0.13, 0.045)}.get(zh, (0.0, 0.0))
    ax.text(r.centre_lon + dx, r.centre_lat + dy, PIN[zh], ha="center", va="center", fontsize=6.3,''')
# 4. unambiguous x labels: Shangshui -> ShS, Shenqiu -> ShQ
s = s.replace('labels = [f"{PIN[r.county][:3]}-{str(r.harvest_year)[2:]}" for r in d.itertuples()]',
              'AB = {"Shangshui": "ShS", "Shenqiu": "ShQ"}\n'
              'labels = [f"{AB.get(PIN[r.county], PIN[r.county][:3])}-{str(r.harvest_year)[2:]}" for r in d.itertuples()]')
open(p, 'w', encoding='utf-8').write(s)
print("fig1 fixes applied")
