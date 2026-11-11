# -*- coding: utf-8 -*-
"""Layout-preserving Korean -> English translation of the course slide PDFs.

    python engine.py spec_l8

The spec module defines SRC, OUT and PAGES = {page_no: [(korean, english, opts), ...]}.
Only the Korean text spans are removed (images and vector graphics stay untouched);
the English is drawn at the original baseline in the deck's own fonts, shrunk only
when it would run into something.

Markup inside English strings:
    {m:..} Cambria Math   {b:..} bold   {r:..} regular   {i:..} Cambria italic   {z:..} Cambria bold italic
    _{..} subscript       ^{..} superscript (both in the preceding run's font)
Options per item:
    align='center'|'right'   maxw=pt   limit=x   dx dy   size   noscale
    span_range=(i, j)  replace only spans i..j of the matched line
    contains=True      match when the key is contained in the line
    nth=k              only the k-th match on the page
    follow=True        start `gap` pt (default 14) after the previous item's English (legend rows
                       with several entries; give every entry of the row an explicit `limit`)
The spec may also set SUB_SCALE, SUB_DY, SUP_DY to match the deck's own sub/superscripts.

Korean baked into raster images: the spec may define LABELS = {page: [(rect, english, opts), ...]}.
`rect` (page coords) must enclose the Korean label and nothing else of the same colour; the
label pixels are found inside it, erased by inpainting a small patch that is laid over the
untouched original image, and the English is drawn on top as live text.
Label options: bold, size, color, align='center'|'left'|'right', dx, dy, maxw, lh (line
height factor; '\\n' in the English splits lines), rot=90 (reads bottom to top),
mode='all'|'dark'|'color' (which pixels count as text: everything that differs from the
background / only dark grey pixels / pixels near `tc`), thr, keep=[rects to leave alone],
pad (mask growth in px), edge=True (also take ink touching the box), inpaint=True (rebuild
lines running under the label instead of painting the background colour), fill=(r,g,b), bg=(r,g,b).
"""
import hashlib
import importlib
import io
import os
import re
import sys

import cv2
import fitz
import numpy as np
from fontTools import subset as ftsubset
from fontTools.ttLib import TTFont

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, '_fontcache')
FONTDIR = r'C:\Windows\Fonts'
FONT_FILES = {
    'MG': ('malgun.ttf', 0), 'MGB': ('malgunbd.ttf', 0),
    'CM': ('cambria.ttc', 1), 'CAI': ('cambriai.ttf', 0), 'CAZ': ('cambriaz.ttf', 0),
    'CO': ('consola.ttf', 0), 'SY': ('seguisym.ttf', 0), 'MSG': ('msgothic.ttc', 0),
}
FALLBACK = ['MG', 'CM', 'SY', 'MSG']
HANGUL = re.compile('[\uac00-\ud7a3\u3131-\u318e\u1100-\u11ff]')
SUB_SCALE, SUB_DY, SUP_DY = 0.72, 0.22, -0.38
RIGHT_MARGIN = 930.0
GAP = 5.0
MIN_SCALE_WARN = 0.92


def norm(s):
    return re.sub(r'\s+', '', s)


# ----------------------------------------------------------------- fonts
_cmaps, FONTS = {}, {}


def cmap_of(key):
    if key not in _cmaps:
        fn, idx = FONT_FILES[key]
        tt = TTFont(os.path.join(FONTDIR, fn), fontNumber=idx, lazy=True)
        _cmaps[key] = set(tt.getBestCmap().keys())
        tt.close()
    return _cmaps[key]


def build_fonts(chars):
    """Subset every font to the characters it must draw: one code point per glyph
    (clean text extraction, no U+00A0 / U+2010 aliases) and small embedded fonts."""
    os.makedirs(CACHE, exist_ok=True)
    chars = set(chars) | set(' ')
    for key, (fn, idx) in FONT_FILES.items():
        cps = sorted(ord(c) for c in chars if ord(c) in cmap_of(key))
        if not cps:
            continue
        tag = hashlib.md5((key + ''.join(map(chr, cps))).encode('utf-8')).hexdigest()[:10]
        out = os.path.join(CACHE, '%s_%s.ttf' % (key, tag))
        if not os.path.exists(out):
            opts = ftsubset.Options()
            opts.font_number = idx
            opts.notdef_outline = True
            opts.name_IDs = ['*']
            opts.name_languages = ['*']
            opts.layout_features = []
            opts.hinting = False
            font = ftsubset.load_font(os.path.join(FONTDIR, fn), opts)
            sub = ftsubset.Subsetter(opts)
            sub.populate(unicodes=cps)
            sub.subset(font)
            ftsubset.save_font(font, out, opts)
        FONTS[key] = fitz.Font(fontfile=out)
        _cmaps[key + '_sub'] = set(cps)


def covers(key, ch):
    return ord(ch) in _cmaps.get(key + '_sub', set())


# ----------------------------------------------------------------- markup
TAGS = {'m': 'CM', 'b': 'MGB', 'r': 'MG', 'i': 'CAI', 'z': 'CAZ', 'c': 'CO'}


def parse(s, base):
    """-> list of (text, fontkey, scale, dy_factor)"""
    out, buf, i = [], '', 0

    def flush():
        nonlocal buf
        if buf:
            out.append((buf, base, 1.0, 0.0))
            buf = ''
    while i < len(s):
        if s[i] == '{' and i + 2 < len(s) and s[i + 1] in TAGS and s[i + 2] == ':':
            flush()
            j = s.index('}', i)
            out.append((s[i + 3:j], TAGS[s[i + 1]], 1.0, 0.0))
            i = j + 1
        elif s[i] in '_^' and i + 1 < len(s) and s[i + 1] == '{':
            flush()
            j = s.index('}', i)
            prev = out[-1][1] if out else base
            out.append((s[i + 2:j], prev, SUB_SCALE, SUB_DY if s[i] == '_' else SUP_DY))
            i = j + 1
        else:
            buf += s[i]
            i += 1
    flush()
    return out


def chars_of(s):
    return set(''.join(t for t, _, _, _ in parse(s, 'MG')))


def runs_for(pieces, size):
    """Split pieces into runs of one font each, applying the fallback chain per char."""
    runs, missing = [], set()
    for text, fk, sc, dyf in pieces:
        for ch in text:
            key = fk if covers(fk, ch) else next((k for k in FALLBACK if covers(k, ch)), None)
            if key is None:
                missing.add(ch)
                continue
            fs = size * sc
            if runs and runs[-1][1] == key and runs[-1][2] == fs and runs[-1][3] == dyf * size:
                runs[-1][0] += ch
            else:
                runs.append([ch, key, fs, dyf * size])
    return runs, missing


def runs_width(runs):
    return sum(FONTS[k].text_length(t, fontsize=fs) for t, k, fs, dy in runs)


def scale_runs(runs, f):
    return [[t, k, fs * f, dy * f] for t, k, fs, dy in runs]


# ----------------------------------------------------------------- page analysis
def page_lines(page):
    out = []
    for b in page.get_text('dict')['blocks']:
        for l in b.get('lines', []):
            spans = [s for s in l['spans'] if s['text'] != '']
            text = ''.join(s['text'] for s in spans)
            if not text.strip():
                continue
            out.append(dict(text=text, key=norm(text), bbox=fitz.Rect(l['bbox']),
                            spans=spans, dir=tuple(round(v, 3) for v in l['dir'])))
    return out


def rgb(c):
    return ((c >> 16) & 255) / 255.0, ((c >> 8) & 255) / 255.0, (c & 255) / 255.0


def seg_xmin_in_band(p, q, top, bot):
    """Smallest x of segment pq inside the horizontal band [top, bot], or None."""
    (x1, y1), (x2, y2) = (p.x, p.y), (q.x, q.y)
    if max(y1, y2) < top or min(y1, y2) > bot:
        return None
    if abs(y2 - y1) < 1e-6:
        return min(x1, x2)
    xs = []
    for yy in (top, bot):
        t = (yy - y1) / (y2 - y1)
        if 0 <= t <= 1:
            xs.append(x1 + t * (x2 - x1))
    for (xx, yy) in ((x1, y1), (x2, y2)):
        if top <= yy <= bot:
            xs.append(xx)
    return min(xs) if xs else None


def drawing_xmin_in_band(d, top, bot, xstart):
    """Left-most x >= xstart of a drawing inside the band (None if it does not reach the band)."""
    best = None
    for it in d['items']:
        if it[0] == 'l':
            pts = [(it[1], it[2])]
        elif it[0] == 'c':
            pts = [(it[1], it[2]), (it[2], it[3]), (it[3], it[4])]
        elif it[0] == 're':
            r = it[1]
            pts = [(r.tl, r.tr), (r.tr, r.br), (r.br, r.bl), (r.bl, r.tl)]
        elif it[0] == 'qu':
            qd = it[1]
            pts = [(qd.ul, qd.ur), (qd.ur, qd.lr), (qd.lr, qd.ll), (qd.ll, qd.ul)]
        else:
            continue
        for p, q in pts:
            x = seg_xmin_in_band(p, q, top, bot)
            if x is None:
                continue
            # the part of the segment to the right of xstart
            if max(p.x, q.x) < xstart:
                continue
            x = max(x, xstart)
            best = x if best is None else min(best, x)
    return best


def is_container(d, rect):
    r = d['rect']
    closed = d.get('closePath') or any(it[0] in ('re', 'qu') for it in d['items']) or d.get('fill') is not None
    return closed and r.width > 20 and r.height > 10 and r.x0 <= rect.x0 + 0.5 and r.x1 >= rect.x1 - 0.5 \
        and r.y0 <= rect.y0 + 0.5 and r.y1 >= rect.y1 - 0.5 and r.width < 700


# ----------------------------------------------------------------- labels inside images
def page_images(page):
    out = []
    for img in page.get_images(full=True):
        xref, w, h = img[0], img[2], img[3]
        for r, m in page.get_image_rects(xref, transform=True):
            if abs(m.b) > 1e-3 * abs(m.a) or abs(m.c) > 1e-3 * abs(m.d) or m.a <= 0 or m.d <= 0:
                continue            # rotated / flipped placements are not handled
            out.append(dict(xref=xref, rect=fitz.Rect(r)))
    return out


def image_rgb(doc, xref):
    pix = fitz.Pixmap(doc, xref)
    if pix.alpha:
        pix = fitz.Pixmap(pix, 0)
    if pix.n != 3:
        pix = fitz.Pixmap(fitz.csRGB, pix)
    return np.frombuffer(pix.samples, np.uint8).reshape(pix.h, pix.w, 3).copy()


def modal_color(pts):
    q = pts // 16
    keys = q[:, 0] * 256 + q[:, 1] * 16 + q[:, 2]
    vals, cnt = np.unique(keys, return_counts=True)
    return pts[keys == vals[cnt.argmax()]].mean(axis=0)


def do_labels(src, page, pno, labels, report):
    """Erase the Korean label pixels and draw the English; returns the changed page regions."""
    regions, work, patches, texts = [], {}, [], []
    imgs = page_images(page)
    for it in labels:
        R, eng = fitz.Rect(it[0]), it[1]
        o = it[2] if len(it) > 2 else {}
        c = fitz.Point((R.x0 + R.x1) / 2, (R.y0 + R.y1) / 2)
        hit = [im for im in imgs if im['rect'].contains(c)]
        if not hit:
            report.append('p%d LABEL OUTSIDE IMAGES: %s' % (pno, eng))
            continue
        im = hit[-1]
        x = im['xref']
        if x not in work:
            A = image_rgb(src, x)
            work[x] = (A, A.copy(), im['rect'])
        A, W, ir = work[x]
        sx, sy = A.shape[1] / ir.width, A.shape[0] / ir.height

        def px(rr):
            return (max(int(np.floor((rr.x0 - ir.x0) * sx)), 0), max(int(np.floor((rr.y0 - ir.y0) * sy)), 0),
                    min(int(np.ceil((rr.x1 - ir.x0) * sx)), A.shape[1]),
                    min(int(np.ceil((rr.y1 - ir.y0) * sy)), A.shape[0]))
        i0, j0, i1, j1 = px(R)
        inR = A[j0:j1, i0:i1].astype(int)
        h, w = inR.shape[:2]
        mode = o.get('mode', 'all')

        def find_ink(bg):
            """Text pixels: differ from the background, pass the mode filter, and belong to a
            connected component that does not touch the search box (borders, arrows, plot
            lines run out of the box; glyphs do not)."""
            dist = np.abs(inR - bg).max(axis=2)
            ink = dist > o.get('thr', 60)
            if mode == 'dark':
                lum, sat = inR.mean(axis=2), inR.max(axis=2) - inR.min(axis=2)
                ink &= (lum < o.get('lum', 130)) & (sat < o.get('sat', 45))
            elif mode == 'color':
                ink &= np.abs(inR - np.array(o['tc'])).max(axis=2) < o.get('tol', 70)
            for kr in o.get('keep', []):
                k0, k1, k2, k3 = px(fitz.Rect(kr))
                ink[max(k1 - j0, 0):max(k3 - j0, 0), max(k0 - i0, 0):max(k2 - i0, 0)] = False
            n, lab, stats, _ = cv2.connectedComponentsWithStats(ink.astype(np.uint8), connectivity=8)
            ok = np.zeros(n, bool)
            for k in range(1, n):
                x0, y0, ww, hh = stats[k, :4]
                touches = x0 == 0 or y0 == 0 or x0 + ww >= w or y0 + hh >= h
                ok[k] = o.get('edge', False) or not touches
            return dist, ok[lab], lab, stats, ok

        bg = np.array(o['bg'], float) if 'bg' in o else modal_color(inR.reshape(-1, 3))
        dist, text, lab, stats, ok = find_ink(bg)
        if 'bg' not in o and text.any():
            t8 = text.astype(np.uint8)
            ring = (cv2.dilate(t8, np.ones((9, 9), np.uint8)) > 0) & ~(cv2.dilate(t8, np.ones((3, 3), np.uint8)) > 0)
            if ring.sum() > 20:
                bg = modal_color(inR[ring])            # the background right around the glyphs
                dist, text, lab, stats, ok = find_ink(bg)
        big = np.zeros_like(text)
        for k in np.nonzero(ok)[0]:
            if stats[k, cv2.CC_STAT_AREA] >= o.get('speck', 4):
                big |= lab == k
        if not big.any():
            report.append('p%d LABEL NO INK: %s' % (pno, eng))
            continue
        ys, xs = np.nonzero(big)
        T = fitz.Rect(ir.x0 + (i0 + xs.min()) / sx, ir.y0 + (j0 + ys.min()) / sy,
                      ir.x0 + (i0 + xs.max() + 1) / sx, ir.y0 + (j0 + ys.max() + 1) / sy)
        dd = dist[big]
        col = np.median(inR[big][dd >= np.percentile(dd, 70)], axis=0)
        M = 6
        ci0, cj0 = max(i0 - M, 0), max(j0 - M, 0)
        ci1, cj1 = min(i1 + M, A.shape[1]), min(j1 + M, A.shape[0])
        mask = np.zeros((cj1 - cj0, ci1 - ci0), np.uint8)
        mask[j0 - cj0:j1 - cj0, i0 - ci0:i1 - ci0][text] = 255
        pad = o.get('pad', 3)
        mask = cv2.dilate(mask, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * pad + 1, 2 * pad + 1)))
        Wsub = W[cj0:cj1, ci0:ci1]
        if o.get('flat') or 'fill' in o:
            Wsub[mask > 0] = np.clip(np.array(o.get('fill', bg)), 0, 255).astype(np.uint8)
        else:
            out = cv2.inpaint(np.ascontiguousarray(Wsub[:, :, ::-1]), mask, o.get('radius', 4), cv2.INPAINT_TELEA)
            Wsub[:] = out[:, :, ::-1]
        ys2, xs2 = np.nonzero(mask)
        patches.append((x, (max(ci0 + xs2.min() - 1, 0), max(cj0 + ys2.min() - 1, 0),
                            min(ci0 + xs2.max() + 2, A.shape[1]), min(cj0 + ys2.max() + 2, A.shape[0]))))
        texts.append(dict(T=T, eng=eng, o=o, color=tuple(col / 255.0)))
        report.append('p%d LABEL %-28s ink (%.1f,%.1f)-(%.1f,%.1f) h=%.1f w=%.1f col #%02x%02x%02x bg #%02x%02x%02x' % (
            pno, eng.replace('\n', '/')[:28], T.x0, T.y0, T.x1, T.y1, T.height, T.width,
            *[int(v) for v in col], *[int(v) for v in bg]))
    for x, (a0, b0, a1, b1) in patches:
        A, W, ir = work[x]
        sx, sy = A.shape[1] / ir.width, A.shape[0] / ir.height
        rr = fitz.Rect(ir.x0 + a0 / sx, ir.y0 + b0 / sy, ir.x0 + a1 / sx, ir.y0 + b1 / sy)
        ok, buf = cv2.imencode('.png', np.ascontiguousarray(W[b0:b1, a0:a1, ::-1]))
        page.insert_image(rr, stream=buf.tobytes(), keep_proportion=False)
        regions.append(rr)
    for t in texts:
        regions += draw_label(page, pno, t, report)
    return regions


def draw_label(page, pno, t, report):
    T, o = t['T'], t['o']
    rot = o.get('rot', 0)
    base = o.get('font') or ('MGB' if o.get('bold') else 'MG')
    color = o.get('color', t['color'])
    if isinstance(color, int):
        color = rgb(color)
    size = o.get('size', (T.width if rot else T.height) / 0.94)
    lines = t['eng'].split('\n')
    runs_l = []
    for ln in lines:
        runs, missing = runs_for(parse(ln, base), size)
        if missing:
            report.append('p%d MISSING GLYPHS %r in label: %s' % (pno, ''.join(sorted(missing)), ln))
        runs_l.append(runs)
    ws = [runs_width(r) for r in runs_l]
    f = 1.0
    if 'maxw' in o and max(ws) > o['maxw']:
        f = o['maxw'] / max(ws)
    runs_l = [scale_runs(r, f) for r in runs_l]
    ws = [w * f for w in ws]
    size *= f
    lh = o.get('lh', 1.2) * size
    n = len(lines)
    cx = (T.x0 + T.x1) / 2 + o.get('dx', 0)
    cy = (T.y0 + T.y1) / 2 + o.get('dy', 0)
    al = o.get('align', 'center')
    rects = []
    for k, (runs, w) in enumerate(zip(runs_l, ws)):
        y = cy - (n - 1) * lh / 2 + k * lh + 0.35 * size
        if rot:
            x = cx - w / 2
        else:
            x = {'center': cx - w / 2, 'left': T.x0 + o.get('dx', 0), 'right': T.x1 + o.get('dx', 0) - w}[al]
        tw = fitz.TextWriter(page.rect, color=color)
        xx = x
        for tt, kk, fs, dy in runs:
            tw.append((xx, y + dy), tt, font=FONTS[kk], fontsize=fs)
            xx += FONTS[kk].text_length(tt, fontsize=fs)
        if rot:
            tw.write_text(page, morph=(fitz.Point(cx, cy), fitz.Matrix(rot)))
            rects.append(fitz.Rect(cx - 0.7 * size, cy - w / 2, cx + 0.7 * size, cy + w / 2))
        else:
            tw.write_text(page)
            rects.append(fitz.Rect(x, y - 0.9 * size, x + w, y + 0.3 * size))
    return rects


# ----------------------------------------------------------------- main build
def build(spec):
    global SUB_SCALE, SUB_DY, SUP_DY     # decks set subscripts differently (Lecture 10: 0.53 size, 0.19 drop)
    SUB_SCALE = getattr(spec, 'SUB_SCALE', SUB_SCALE)
    SUB_DY = getattr(spec, 'SUB_DY', SUB_DY)
    SUP_DY = getattr(spec, 'SUP_DY', SUP_DY)
    src = fitz.open(spec.SRC)
    doc = fitz.open(spec.SRC)
    cfg = dict(RIGHT_MARGIN=getattr(spec, 'RIGHT_MARGIN', RIGHT_MARGIN))
    allchars = set()
    for items in spec.PAGES.values():
        for it in items:
            allchars |= chars_of(it[1])
    for items in getattr(spec, 'LABELS', {}).values():
        for it in items:
            allchars |= chars_of(it[1].replace('\n', ''))
    build_fonts(allchars)
    report, diff_regions = [], {}
    for pno in range(1, doc.page_count + 1):
        page = doc[pno - 1]
        lines = page_lines(page)
        drawings = page.get_drawings()
        items = spec.PAGES.get(pno, [])
        jobs = []
        for it in items:
            kor, eng = it[0], it[1]
            opts = it[2] if len(it) > 2 else {}
            k = norm(kor)
            if opts.get('contains'):
                matches = [L for L in lines if k in L['key']]
            else:
                matches = [L for L in lines if L['key'] == k]
            if 'nth' in opts:
                matches = matches[opts['nth']:opts['nth'] + 1]
            if not matches:
                report.append('p%d UNUSED: %s' % (pno, kor))
                continue
            for L in matches:
                sr = opts.get('span_range')
                spans = L['spans'][sr[0]:sr[1] + 1] if sr else L['spans']
                nxt = L['spans'][sr[1] + 1] if sr and sr[1] + 1 < len(L['spans']) else None
                main = max(spans, key=lambda s: (bool(HANGUL.search(s['text'])), s['size']))
                jobs.append(dict(line=L, spans=spans, eng=eng, opts=opts, next_span=nxt,
                                 x=spans[0]['origin'][0], y=spans[0]['origin'][1],
                                 size=opts.get('size', main['size']), color=rgb(main['color']),
                                 bold='Bold' in main['font'],
                                 rect=fitz.Rect(spans[0]['bbox']) | fitz.Rect(spans[-1]['bbox'])))
        done = {id(j['line']) for j in jobs if not j['opts'].get('span_range')}
        for L in lines:
            if HANGUL.search(L['text']) and id(L) not in done:
                covered = [j for j in jobs if j['line'] is L]
                left = L['text']
                for j in covered:
                    for s in j['spans']:
                        left = left.replace(s['text'], '')
                if HANGUL.search(left):
                    report.append('p%d UNTRANSLATED: %s' % (pno, L['text']))
        # ---- redact the selected spans only
        keep_before = [L['text'] for L in lines if not any(j['line'] is L for j in jobs)]
        for j in jobs:
            for s in j['spans']:
                r = fitz.Rect(s['bbox'])
                h = r.height
                rr = fitz.Rect(r.x0 + 0.4, r.y0 + 0.22 * h, r.x1 - 0.4, r.y1 - 0.22 * h)
                page.add_redact_annot(rr, fill=False, cross_out=False)
        page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE,
                              graphics=fitz.PDF_REDACT_LINE_ART_NONE,
                              text=fitz.PDF_REDACT_TEXT_REMOVE)
        page = doc.reload_page(page)
        after = norm(page.get_text())
        for t in keep_before:
            if norm(t) and norm(t) not in after:
                report.append('p%d REDACTION MISMATCH (lost): %s' % (pno, t))
        # ---- draw
        drawn = []
        last_end = None
        for j in jobs:
            o = j['opts']
            base = 'MGB' if (j['bold'] or o.get('bold')) else 'MG'
            runs, missing = runs_for(parse(j['eng'], base), j['size'])
            if missing:
                report.append('p%d MISSING GLYPHS %r in: %s' % (pno, ''.join(sorted(missing)), j['eng']))
            w = runs_width(runs)
            L = j['line']
            x0 = j['x'] + o.get('dx', 0)
            if o.get('follow') and last_end is not None:
                x0 = last_end + o.get('gap', 14)     # legend rows: start after the previous item's English
            y = j['y'] + o.get('dy', 0)
            s = j['size']
            top, bot = y - 0.8 * s, y + 0.25 * s
            # containers (boxes) around the line
            conts = [d for d in drawings if is_container(d, L['bbox'])]
            cont = min(conts, key=lambda d: abs(d['rect'])) if conts else None
            align = o.get('align')
            if align is None and cont is not None:
                cr = cont['rect']
                if abs((L['bbox'].x0 + L['bbox'].x1) / 2 - (cr.x0 + cr.x1) / 2) < 3.5 and L['bbox'].x0 - cr.x0 > 6:
                    align = 'center-box'
            if align in ('center', 'center-box', 'right'):
                if align == 'center-box':
                    cr = cont['rect']
                    cx, avail = (cr.x0 + cr.x1) / 2, cr.width - 12
                else:
                    cx = (L['bbox'].x0 + L['bbox'].x1) / 2 + o.get('dx', 0)
                    avail = o.get('maxw', max(L['bbox'].width + 30, w))
                avail = min(avail, o.get('maxw', avail))
                f = 1.0 if (w <= avail or o.get('noscale')) else avail / w
                runs = scale_runs(runs, f)
                w2 = runs_width(runs)
                if align == 'right':
                    x0 = L['bbox'].x1 + o.get('dx', 0) - w2
                else:
                    x0 = cx - w2 / 2
            else:
                lim = o.get('limit')
                if lim is None:
                    lim = cfg['RIGHT_MARGIN']
                    if j['next_span'] is not None:
                        lim = min(lim, j['next_span']['bbox'][0] - 2)
                    for L2 in lines:
                        if L2 is L:
                            continue
                        b = L2['bbox']
                        if b.y1 <= top + 1.5 or b.y0 >= bot - 1.5:
                            continue
                        if b.x0 >= x0 + 2:
                            lim = min(lim, b.x0 - GAP)
                    for d in drawings:
                        r = d['rect']
                        if r.y1 < top or r.y0 > bot or r.x1 <= x0:
                            continue
                        if r.height < 1.6 and r.width > 3:
                            continue    # horizontal rules / underlines
                        if is_container(d, L['bbox']):
                            lim = min(lim, r.x1 - 6)
                            continue
                        xm = drawing_xmin_in_band(d, top, bot, x0 + 1)
                        if xm is not None and xm > x0 + 1:
                            lim = min(lim, xm - GAP)
                    lim = max(lim, L['bbox'].x1 + 6) if j['next_span'] is None else lim
                if 'maxw' in o:
                    lim = min(lim, x0 + o['maxw'])
                f = 1.0
                if x0 + w > lim and not o.get('noscale'):
                    f = (lim - x0) / w
                runs = scale_runs(runs, f)
                if f < MIN_SCALE_WARN:
                    report.append('p%d SCALED %.2f: %s' % (pno, f, j['eng']))
            tw = fitz.TextWriter(page.rect, color=j['color'])
            x = x0
            for t, k, fs, dy in runs:
                tw.append((x, y + dy), t, font=FONTS[k], fontsize=fs)
                x += FONTS[k].text_length(t, fontsize=fs)
            tw.write_text(page)
            last_end = x
            fs0 = max(r[2] for r in runs) if runs else s
            nr = fitz.Rect(x0, y - 0.82 * fs0, x, y + 0.24 * fs0)
            drawn.append((nr, j))
        # ---- collisions between new text and other text
        others = [L['bbox'] for L in page_lines(page)]
        for nr, j in drawn:
            for b in others:
                inter = nr & b
                if inter.is_empty or abs(inter) < 4:
                    continue
                # the new text itself is in the list; skip near-identical rects
                if abs(b.x0 - nr.x0) < 1.5 and abs(b.y1 - nr.y1) < 4:
                    continue
                if abs(inter) > 0.25 * min(abs(nr), abs(b)):
                    report.append('p%d OVERLAP: "%s" with text at %s' % (pno, j['eng'][:50], tuple(round(v) for v in b)))
            if nr.x1 > cfg['RIGHT_MARGIN'] + 1:
                report.append('p%d PAST MARGIN: %s' % (pno, j['eng'][:50]))
        diff_regions[pno] = [fitz.Rect(s['bbox']) for j in jobs for s in j['spans']] + [nr for nr, _ in drawn]
        if pno in getattr(spec, 'LABELS', {}):
            diff_regions[pno] += do_labels(src, page, pno, spec.LABELS[pno], report)
    doc.subset_fonts()
    doc.save(spec.OUT, garbage=4, deflate=True)
    doc.close()
    report += verify(spec, diff_regions)
    return report


def verify(spec, regions, zoom=1.25):
    out = []
    a, b = fitz.open(spec.SRC), fitz.open(spec.OUT)
    txt = ''.join(p.get_text() for p in b)
    out.append('CHECK hangul=%d nbsp=%d u2010=%d pages=%d/%d' % (
        len(HANGUL.findall(txt)), txt.count('\u00a0'), txt.count('\u2010'), b.page_count, a.page_count))
    for pno in range(1, a.page_count + 1):
        m = fitz.Matrix(zoom, zoom)
        pa, pb = a[pno - 1].get_pixmap(matrix=m, alpha=False), b[pno - 1].get_pixmap(matrix=m, alpha=False)
        A = np.frombuffer(pa.samples, np.uint8).reshape(pa.h, pa.w, 3).astype(int)
        B = np.frombuffer(pb.samples, np.uint8).reshape(pb.h, pb.w, 3).astype(int)
        diff = np.abs(A - B).max(axis=2) > 40
        mask = np.zeros_like(diff)
        for r in regions.get(pno, []):
            x0, y0 = max(int((r.x0 - 3) * zoom), 0), max(int((r.y0 - 3) * zoom), 0)
            x1, y1 = int((r.x1 + 3) * zoom) + 1, int((r.y1 + 3) * zoom) + 1
            mask[y0:y1, x0:x1] = True
        bad = diff & ~mask
        if bad.sum() > 20:
            ys, xs = np.nonzero(bad)
            out.append('p%d PIXELS CHANGED OUTSIDE TEXT: %d px, bbox (%d,%d)-(%d,%d) pt' % (
                pno, bad.sum(), xs.min() / zoom, ys.min() / zoom, xs.max() / zoom, ys.max() / zoom))
    return out


if __name__ == '__main__':
    sys.path.insert(0, HERE)
    spec = importlib.import_module(sys.argv[1])
    rep = build(spec)
    io.open(os.path.join(HERE, 'report_%s.txt' % sys.argv[1]), 'w', encoding='utf-8').write('\n'.join(rep))
    for line in rep:
        print(line)
