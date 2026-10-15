from playwright.sync_api import sync_playwright
import fitz, pathlib
html = '''<html><body style="width:300px">
<h1 aria-label="Course map: what an intelligent robot does">Course map: what an intelligent robot does</h1>
<h1>Course map: what an intelligent robot does plain</h1>
<h2><span>1.1</span><span>Sense, compute, act</span></h2>
<h2 aria-label="1.2 The stack"><span>1.2</span><span>The stack</span></h2>
</body></html>'''
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(); pg.set_content(html)
    pg.pdf(path='_t.pdf', outline=True, tagged=True); b.close()
print(fitz.open('_t.pdf').get_toc())
