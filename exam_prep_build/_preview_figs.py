# -*- coding: utf-8 -*-
"""Screenshot every figure on the dark panel background for review."""
import pathlib, sys
from playwright.sync_api import sync_playwright

BASE = pathlib.Path(__file__).parent
names = sys.argv[1:] or sorted(p.stem for p in (BASE / 'fig').glob('*.svg'))
out = BASE / '_preview'
out.mkdir(exist_ok=True)
html = ['<html><body style="background:#0f1218;margin:0;padding:10px;font-family:Segoe UI;color:#ccc">']
for n in names:
    html.append('<div id="%s" style="display:inline-block;background:#161b24;border:1px solid #222a3b;'
                'border-radius:10px;padding:8px;margin:6px;width:700px"><div>%s</div>'
                '<img src="fig/%s.svg" style="width:680px"></div>' % (n, n, n))
html.append('</body></html>')
page = BASE / '_preview.html'
page.write_text(''.join(html), encoding='utf-8')
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={'width': 760, 'height': 800}, device_scale_factor=1.4)
    pg.goto(page.resolve().as_uri())
    pg.wait_for_timeout(500)
    for n in names:
        pg.locator('#' + n).screenshot(path=str(out / (n + '.png')))
    b.close()
print('ok', len(names))
