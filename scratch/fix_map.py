p = r'D:\2026-SP\src\s5_figures_main\w57_study_area_map.py'
s = open(p, encoding='utf-8').read()
old = s[s.find("ext = (LON0 + (win.col_off)"):s.find("vmax = np.nanpercentile")]
new = '''# geographic extent of the window, computed from the window's own transform
# (bounds = (left, bottom, right, top))
b = rasterio.windows.bounds(win, s.transform)
ext = (b[0], b[1], b[2], b[3])
'''
s = s.replace(old, new)
# development-panel label: Tai'an is Shandong, so use a neutral outline colour for both development areas
s = s.replace('"Shijiazhuang (Hebei)":   dict(ids=ids(os.path.join(REP, "w44_frozen_panel.csv"), "河北"), col=COL["Hebei"],',
              '"Shijiazhuang (Hebei)":   dict(ids=ids(os.path.join(REP, "w44_frozen_panel.csv"), "河北"), col=COL["Hebei"],')
s = s.replace('''ax.legend(handles=[Line2D([], [], color=COL["Hebei"], lw=1.3, label="Development panel (Hebei, Shandong)"),
                   Line2D([], [], color=COL["Henan"], lw=1.3, label="External tests (Henan)")],''',
'''ax.legend(handles=[Line2D([], [], color=COL["Hebei"], lw=1.3, label="Development panel: Shijiazhuang (Hebei)"),
                   Line2D([], [], color=COL["Shandong"], lw=1.3, label="Development panel: Tai'an (Shandong)"),
                   Line2D([], [], color=COL["Henan"], lw=1.3, label="External tests (Henan)")],''')
# only the counties actually used (primary set) are drawn, so counts match the text
s = s.replace('''units = {
    "Shijiazhuang (Hebei)":   dict(ids=ids(os.path.join(REP, "w44_frozen_panel.csv"), "河北"), col=COL["Hebei"],   n="12 units, 60 county-years"),
    "Tai'an (Shandong)":      dict(ids=ids(os.path.join(REP, "w44_frozen_panel.csv"), "山东"), col=COL["Shandong"], n="5 units, 30 county-years"),
    "Pingdingshan (Henan)":   dict(ids=ids(os.path.join(REP, "w48_pds_frozen.csv")),            col=COL["Henan"],   n="5 counties, 9 county-years"),
    "Zhoukou (Henan)":        dict(ids=ids(os.path.join(REP, "w53_zhoukou_frozen_external.csv")), col=COL["Henan"], n="7 counties, 19 county-years"),
}''',
'''def used(path, flag=None, prov=None):
    """shape_ids of counties that enter the analysis (flag column when given)."""
    d = pd.read_csv(path)
    if prov is not None and "province" in d.columns:
        d = d[d.province.str.contains(prov)]
    if flag is not None and flag in d.columns:
        d = d[d[flag].astype(bool)]
    return sorted(d.shape_id.unique())
units = {
    "Shijiazhuang (Hebei)":   dict(ids=used(os.path.join(REP, "w44_frozen_panel.csv"), "primary", "河北"), col=COL["Hebei"],
                                  n="12 counties; 56 county-years pass the primary screen"),
    "Tai'an (Shandong)":      dict(ids=used(os.path.join(REP, "w44_frozen_panel.csv"), "primary", "山东"), col=COL["Shandong"],
                                  n="5 counties; 23 county-years pass the primary screen"),
    "Pingdingshan (Henan)":   dict(ids=used(os.path.join(REP, "w48_pds_frozen.csv"), "primary"), col=COL["Henan"],
                                  n="5 counties; 6 county-years in the primary set"),
    "Zhoukou (Henan)":        dict(ids=used(os.path.join(REP, "w53_zhoukou_frozen_external.csv")), col=COL["Henan"],
                                  n="7 counties; 19 county-years pass the primary screen"),
}''')
open(p, 'w', encoding='utf-8').write(s)
print("map script fixed: true window bounds + primary-set counties")
