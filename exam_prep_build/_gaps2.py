# -*- coding: utf-8 -*-
"""List pages whose content ends early (large blank area at the bottom), excluding chapter ends."""
import fitz

import sys
d = fitz.open(sys.argv[1] if len(sys.argv) > 1 else '../Exam Prep Notes (Lectures 1-7).pdf')
toc = d.get_toc()
chapter_starts = {p for lvl, t, p in toc if lvl == 1}
H = d[0].rect.height
for i in range(1, d.page_count - 1):
    page = d[i]
    ys = []
    for b in page.get_text('blocks'):
        if 50 < b[1] and b[3] < H - 46:
            ys.append(b[3])
    for img in page.get_image_info():
        ys.append(img['bbox'][3])
    for dr in page.get_drawings():
        r = dr['rect']
        if r.y1 < H - 46 and r.height < H * 0.9 and r.y0 > 40:
            ys.append(r.y1)
    bottom = max(ys) if ys else 0
    free = (H - 46 - bottom) / (H - 46 - 45)
    nxt_is_chapter = (i + 2) in chapter_starts
    if free > 0.22 and not nxt_is_chapter:
        nxt = d[i + 1].get_text('blocks')
        first = next((b[4].strip().replace('\n', ' ')[:70] for b in nxt if b[1] > 50), '')
        print('page %3d  blank %3d%%  next page starts: %s' % (i + 1, round(free * 100), first.encode('ascii', 'replace').decode()))
