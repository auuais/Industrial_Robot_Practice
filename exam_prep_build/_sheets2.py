# -*- coding: utf-8 -*-
"""Contact sheets of PDF pages for layout review: python _sheets.py first last tag"""
import sys
import fitz

first, last, tag = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
d = fitz.open(sys.argv[4] if len(sys.argv) > 4 else '../Exam Prep Notes (Lectures 1-7).pdf')
pages = list(range(first - 1, min(last, d.page_count)))
W, H = 420, 594
for s in range(0, len(pages), 6):
    chunk = pages[s:s + 6]
    sheet = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 3 * W + 20, 2 * H + 10), False)
    sheet.set_rect(sheet.irect, (70, 70, 70))
    for k, p in enumerate(chunk):
        z = W / d[p].rect.width
        pix = d[p].get_pixmap(matrix=fitz.Matrix(z, z), alpha=False)
        pix.set_origin((k % 3) * (W + 10), (k // 3) * (H + 10))
        sheet.copy(pix, pix.irect)
    sheet.save('_preview/sheet_%s_%d.png' % (tag, s // 6))
print('sheets:', (len(pages) + 5) // 6)
