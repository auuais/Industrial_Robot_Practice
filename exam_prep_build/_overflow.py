# -*- coding: utf-8 -*-
"""Find elements wider than the printable page (they make Chromium shrink the whole PDF).
    python _overflow.py            (uses _build.html from the last build)"""
import pathlib

from playwright.sync_api import sync_playwright

BASE = pathlib.Path(__file__).parent
JS = r"""
() => {
  const docW = document.documentElement.clientWidth;
  const out = [];
  for (const el of document.querySelectorAll('body *')) {
    const r = el.getBoundingClientRect();
    if (r.width === 0) continue;
    const sec = el.closest('section');
    const box = sec ? sec.getBoundingClientRect() : {right: docW};
    if (r.right > docW + 0.5) {
      out.push({tag: el.tagName, cls: el.className && el.className.baseVal === undefined ? el.className : '',
                right: Math.round(r.right), docW: docW,
                text: (el.textContent || '').trim().slice(0, 90)});
    }
  }
  return {docW, scrollW: document.documentElement.scrollWidth, items: out.slice(0, 40)};
}
"""
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page()
    pg.emulate_media(media='print')
    pg.set_viewport_size({'width': 680, 'height': 1050})
    pg.goto((BASE / '_build.html').resolve().as_uri(), wait_until='load')
    pg.wait_for_timeout(300)
    res = pg.evaluate(JS)
    b.close()
print('docW', res['docW'], 'scrollW', res['scrollW'])
for it in res['items']:
    print(it['tag'], it['cls'], it['right'], '|', it['text'].encode('ascii', 'replace').decode())
