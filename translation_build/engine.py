# -*- coding: utf-8 -*-
"""Layout-preserving Korean -> English translation of the course slide PDFs.

    python engine.py spec_l8

The spec module defines SRC, OUT and PAGES = {page_no: [(korean, english, opts), ...]}.
Only the Korean text spans are removed (images and vector graphics stay untouched);
the English is drawn at the original baseline in the deck's own fonts, shrunk only
when it would run into something.

Markup inside English strings:
    {m:..} Cambria Math   {b:..} bold   {r:..} regular   {i:..} Cambria italic
    _{..} subscript       ^{..} superscript (both in the preceding run's font)
Options per item:
    align='center'|'right'   maxw=pt   limit=x   dx dy   size   noscale
    span_range=(i, j)  replace only spans i..j of the matched line
    contains=True      match when the key is contained in the line
    nth=k              only the k-th match on the page
"""
import hashlib
import importlib
import io
import os
import re
import sys

import fitz
import numpy as np
from fontTools import subset as ftsubset
from fontTools.ttLib import TTFont

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, '_fontcache')
FONTDIR = r'C:\Windows\Fonts'
FONT_FILES = {
    'MG': ('malgun.ttf', 0), 'MGB': ('malgunbd.ttf', 0),
    'CM': ('cambria.ttc', 1), 'CAI': ('cambriai.ttf', 0),
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
TAGS = {'m': 'CM', 'b': 'MGB', 'r': 'MG', 'i': 'CAI', 'c': 'CO'}


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


# ----------------------------------------------------------------- main build
def build(spec):
    src = fitz.open(spec.SRC)
    doc = fitz.open(spec.SRC)
    cfg = dict(RIGHT_MARGIN=getattr(spec, 'RIGHT_MARGIN', RIGHT_MARGIN))
    allchars = set()
    for items in spec.PAGES.values():
        for it in items:
            allchars |= chars_of(it[1])
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
        for j in jobs:
            o = j['opts']
            base = 'MGB' if (j['bold'] or o.get('bold')) else 'MG'
            runs, missing = runs_for(parse(j['eng'], base), j['size'])
            if missing:
                report.append('p%d MISSING GLYPHS %r in: %s' % (pno, ''.join(sorted(missing)), j['eng']))
            w = runs_width(runs)
            L = j['line']
            x0 = j['x'] + o.get('dx', 0)
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
