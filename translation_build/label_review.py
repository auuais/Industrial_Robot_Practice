# -*- coding: utf-8 -*-
"""Before/after crops of the image areas that carry LABELS: python label_review.py spec_l9 [page ...]
Top: source with the spec's search boxes in red.  Bottom: the translated page."""
import importlib
import os
import sys

import fitz

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
spec = importlib.import_module(sys.argv[1])
only = [int(a) for a in sys.argv[2:]]
out = os.path.join(HERE, '_review')
os.makedirs(out, exist_ok=True)
a, b = fitz.open(spec.SRC), fitz.open(spec.OUT)
for pno, labels in sorted(spec.LABELS.items()):
    if only and pno not in only:
        continue
    pa = a[pno - 1]
    u = None
    for it in labels:
        r = fitz.Rect(it[0])
        u = r if u is None else u | r
    for info in pa.get_image_info():
        r = fitz.Rect(info['bbox'])
        if r.intersects(u):
            u |= r
    u = (u + (-6, -6, 6, 6)) & pa.rect
    tmp = fitz.open()
    tmp.insert_pdf(a, from_page=pno - 1, to_page=pno - 1)
    sh = tmp[0].new_shape()
    for it in labels:
        sh.draw_rect(fitz.Rect(it[0]))
    sh.finish(color=(1, 0, 0), width=0.4)
    sh.commit()
    z = min(3.0, 1600 / u.width)
    p1 = tmp[0].get_pixmap(matrix=fitz.Matrix(z, z), clip=u, alpha=False)
    p2 = b[pno - 1].get_pixmap(matrix=fitz.Matrix(z, z), clip=u, alpha=False)
    sheet = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, p1.w, p1.h + p2.h + 8), False)
    sheet.set_rect(sheet.irect, (60, 60, 60))
    p1.set_origin(0, 0)
    sheet.copy(p1, p1.irect)
    p2.set_origin(0, p1.h + 8)
    sheet.copy(p2, p2.irect)
    sheet.save(os.path.join(out, 'lab_p%02d.png' % pno))
print('ok')
