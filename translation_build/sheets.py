# -*- coding: utf-8 -*-
"""2x2 contact sheets of a PDF for visual review: python sheets.py file.pdf tag [first last]"""
import os
import sys

import fitz

pdf, tag = sys.argv[1], sys.argv[2]
d = fitz.open(pdf)
first = int(sys.argv[3]) if len(sys.argv) > 3 else 1
last = int(sys.argv[4]) if len(sys.argv) > 4 else d.page_count
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), '_review')
os.makedirs(out, exist_ok=True)
W = 800
pages = list(range(first - 1, last))
for s in range(0, len(pages), 4):
    H = int(W * d[0].rect.height / d[0].rect.width)
    sheet = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 2 * W + 10, 2 * H + 10), False)
    sheet.set_rect(sheet.irect, (40, 40, 40))
    for k, p in enumerate(pages[s:s + 4]):
        z = W / d[p].rect.width
        pix = d[p].get_pixmap(matrix=fitz.Matrix(z, z), alpha=False)
        pix.set_origin((k % 2) * (W + 10), (k // 2) * (H + 10))
        sheet.copy(pix, pix.irect)
    sheet.save(os.path.join(out, '%s_%02d.png' % (tag, pages[s] + 1)))
print('ok')
