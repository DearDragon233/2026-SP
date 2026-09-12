import os, re
html = r'D:\2026-SP\Agronomy项目启动会_完整版.html'
with open(html, 'r', encoding='utf-8') as f:
    content = f.read()

bad = ['第一作者', '第二作者', '第三作者', '第四作者']
for term in bad:
    cnt = content.count(term)
    status = 'CLEAN' if cnt == 0 else f'FOUND {cnt} times'
    print(f'{term}: {status}')

imgs = re.findall('src="(Outputs/figures/[^"]+)"', content)
print(f'\n{len(imgs)} img refs:')
all_ok = True
for img in imgs:
    full = os.path.join(os.path.dirname(html), img)
    ok = os.path.exists(full)
    if not ok:
        all_ok = False
    sz = os.path.getsize(full) // 1024 if ok else 0
    tag = 'OK' if ok else 'MISSING'
    print(f'  [{tag}] {img} ({sz} KB)')

print(f'\nAll images present: {all_ok}')
print(f'Sections: {len(re.findall(r"<h2 id=.s\d.>", content))}')
print(f'HTML size: {len(content)//1024} KB')
