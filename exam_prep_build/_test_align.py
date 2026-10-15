# -*- coding: utf-8 -*-
from playwright.sync_api import sync_playwright
from tex2mml import tex_to_mathml

eq = tex_to_mathml(r'\begin{aligned} k_1 &= f(x) \\ x_{k+1}+yyy &= x_k + h \end{aligned}', True)
css = ('math{font-family:"Cambria Math";font-size:30px} '
       'mtd.al-r{text-align:right} mtd.al-l{text-align:left}')
html = '<html><head><style>%s</style></head><body>%s</body></html>' % (css, eq)
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page()
    pg.set_content(html)
    print(pg.evaluate('''() => Array.from(document.querySelectorAll('mtd')).map(m =>
        [m.className, getComputedStyle(m).textAlign,
         Math.round(m.getBoundingClientRect().left), Math.round(m.getBoundingClientRect().width),
         Math.round(m.firstElementChild.getBoundingClientRect().left),
         Math.round(m.firstElementChild.getBoundingClientRect().width)])'''))
    b.close()
