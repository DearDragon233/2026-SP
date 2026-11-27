p = r'D:\2026-SP\src\s5_figures_main\w57_study_area_map.py'
s = open(p, encoding='utf-8').read()
# layout: regional map on top spanning all columns; four insets in a row with equal width
old_layout = s[s.find("fig = plt.figure(figsize=(183*MM, 150*MM))"):s.find("letters = \"bcdef\"")]
new_layout = '''fig = plt.figure(figsize=(183*MM, 165*MM))
gs = fig.add_gridspec(2, 4, height_ratios=[1.35, 1], hspace=0.38, wspace=0.30,
                      left=0.06, right=0.93, top=0.96, bottom=0.06)
ax = fig.add_subplot(gs[0, :])
cmap = plt.get_cmap("YlOrBr").copy(); cmap.set_bad("white")
im = ax.imshow(np.ma.masked_invalid(arr), cmap=cmap, vmin=0, vmax=vmax, extent=ext, origin="upper", interpolation="nearest", zorder=0)
'''
s = s.replace(old_layout, new_layout)
# legend: outside the map, below the colour bar side, so it never covers the raster
s = s.replace('''          loc="lower right", frameon=False, fontsize=6.6)''',
              '''          loc="upper left", bbox_to_anchor=(0.0, -0.14), ncol=3, frameon=False, fontsize=6.4)''')
s = s.replace('cb = fig.colorbar(im, ax=ax, fraction=0.03, pad=0.01); cb.set_label("Wheat area per 10 km cell (ha)", fontsize=7)',
              'cax = fig.add_axes([0.945, 0.40, 0.012, 0.54])\n'
              'cb = fig.colorbar(im, cax=cax); cb.set_label("Wheat area per 10 km cell (ha)", fontsize=7)')
# insets: force each to a common physical width so none collapses
s = s.replace('''    a = fig.add_subplot(gs[1, i])''',
              '''    a = fig.add_subplot(gs[1, i])   # one column each; aspect is handled by set_aspect below''')
s = s.replace('''    a.set_aspect(1 / np.cos(np.radians((y0 + y1) / 2)))
    a.set_title(f"({letters[i]}) {name}", loc="left", fontsize=7.6, fontweight="bold")
    a.text(0.5, -0.3, u["n"], transform=a.transAxes, ha="center", fontsize=6.2, color="#444444")
    a.tick_params(labelsize=5.5)''',
'''    a.set_aspect(1 / np.cos(np.radians((y0 + y1) / 2)))
    a.set_title(f"({letters[i]}) {name}", loc="left", fontsize=7.4, fontweight="bold")
    a.tick_params(labelsize=5.5)
    a.xaxis.set_major_locator(plt.MaxNLocator(4)); a.yaxis.set_major_locator(plt.MaxNLocator(4))
    a.xaxis.set_major_formatter(plt.FormatStrFormatter('%.1f')); a.yaxis.set_major_formatter(plt.FormatStrFormatter('%.1f'))
    # caption under the panel, wrapped so it stays inside its column
    import textwrap
    a.text(0.5, -0.26, "\n".join(textwrap.wrap(u["n"], 30)), transform=a.transAxes, ha="center", va="top", fontsize=6.0, color="#444444")''')
# shorter captions
s = s.replace('n="12 counties; 56 county-years pass the primary screen"', 'n="12 counties, 56 county-years"')
s = s.replace('n="5 counties; 23 county-years pass the primary screen"', 'n="5 counties, 23 county-years"')
s = s.replace('n="5 counties; 6 county-years in the primary set"', 'n="5 counties, 6 county-years"')
s = s.replace('n="7 counties; 19 county-years pass the primary screen"', 'n="7 counties, 19 county-years"')
# "Bohai Sea" label sits on land now; move it to the actual sea (north-east corner)
s = s.replace('ax.text(0.005, 0.985, "Bohai Sea", transform=ax.transAxes, fontsize=6.5, color="#557799", style="italic", va="top")',
              'ax.text(121.3, 39.6, "Bohai Sea", fontsize=6.5, color="#557799", style="italic", ha="center")')
open(p, 'w', encoding='utf-8').write(s)
print("layout fixed")
