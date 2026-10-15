# -*- coding: utf-8 -*-
"""Build the exam-prep PDF: content/*.html -> one HTML -> Chromium PDF (2 passes for the TOC)."""
import html as htmlmod
import pathlib
import re
import sys

import fitz
from playwright.sync_api import sync_playwright

from tex2mml import convert_html

BASE = pathlib.Path(__file__).parent
CONTENT = BASE / 'content'
OUT = BASE.parent / 'Exam Prep Notes (Lectures 1-7).pdf'

# (file, chapter key, TOC number label, accent var)
CHAPTERS = [
    ('L1.html', 'l1', '1', '#60a5fa'),
    ('L2.html', 'l2', '2', '#22d3ee'),
    ('L3.html', 'l3', '3', '#a78bfa'),
    ('L4.html', 'l4', '4', '#fbbf24'),
    ('L6.html', 'l6', '6', '#fb7185'),
    ('L7.html', 'l7', '7', '#4ade80'),
    ('S_synthesis.html', 'syn', 'S', '#fb923c'),
    ('G_glossary.html', 'glo', 'G', '#2dd4bf'),
]

ICONS = {
    'key': '<svg viewBox="0 0 16 16"><path d="M8 1.4l1.7 4.3 4.6.3-3.5 2.9 1.1 4.5L8 10.9l-3.9 2.5 1.1-4.5L1.7 6l4.6-.3z" fill="currentColor"/></svg>',
    'intuition': '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M5.6 10.6C4.3 9.7 3.5 8.2 3.5 6.6a4.5 4.5 0 0 1 9 0c0 1.6-.8 3.1-2.1 4v1.5H5.6z"/><path d="M6.2 14.3h3.6"/></svg>',
    'example': '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"><path d="M10.8 2.2l3 3-8.3 8.3-3.5.5.5-3.5z"/><path d="M9.3 3.7l3 3"/></svg>',
    'pitfall': '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round" stroke-linecap="round"><path d="M8 1.8l6.5 11.7h-13z"/><path d="M8 6.2v3.4M8 11.6v.1"/></svg>',
    'tip': '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="8" cy="8" r="6"/><circle cx="8" cy="8" r="3"/><circle cx="8" cy="8" r=".9" fill="currentColor"/></svg>',
    'beyond': '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="8" cy="8" r="6.2"/><path d="M10.6 5.4L9 9l-3.6 1.6L7 7z"/></svg>',
    'formula': '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3H4l4.5 5L4 13h8"/></svg>',
    'recall': '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M13 8a5 5 0 1 1-1.5-3.6"/><path d="M12 1.8v2.8H9.2"/></svg>',
}
DEFAULT_TITLES = {
    'key': 'Key idea', 'intuition': 'Intuition', 'example': 'Worked example',
    'pitfall': 'Watch out', 'tip': 'Exam tip', 'beyond': 'Beyond the slides',
    'formula': 'Key formulas', 'recall': 'Quick recall',
}
QTYPES = {'concept': 'Concept', 'apply': 'Apply', 'analyze': 'Analyze', 'derive': 'Derive'}


def slug(s):
    return re.sub(r'[^a-z0-9]+', '-', s.lower()).strip('-')[:48]


def process_callouts(text):
    def rep(m):
        kinds = m.group(1).split()
        kind = next((k for k in kinds if k in ICONS), None)
        attrs = m.group(2) or ''
        if kind is None:
            return m.group(0)
        t = re.search(r'data-t="([^"]*)"', attrs)
        title = t.group(1) if t else DEFAULT_TITLES[kind]
        rest = re.sub(r'\s*data-t="[^"]*"', '', attrs)
        return '<div class="co %s"%s><div class="co-t">%s<span>%s</span></div>' % (
            ' '.join(kinds), rest, ICONS[kind], title)
    return re.sub(r'<div class="co ([^"]+)"([^>]*)>', rep, text)


def find_page(pages, key):
    """Outline titles can come out doubled when a heading starts a page; fall back to prefix match."""
    if key in pages:
        return pages[key]
    for k, v in pages.items():
        if k.startswith(key):
            return v
    return ''


def process_questions(text, label):
    n = [0]

    def rep(m):
        n[0] += 1
        attrs = m.group(1)
        qt = re.search(r'data-type="(\w+)"', attrs).group(1)
        lvl = int(re.search(r'data-level="(\d)"', attrs).group(1))
        body = m.group(2)
        plain = re.sub(r'<[^>]+>', '', body)
        keep = ' keep' if len(plain) < 1100 else ''
        dots = ''.join('<i class="on"></i>' if i < lvl else '<i></i>' for i in range(3))
        head = ('<div class="q-head"><span class="q-num">Q%d</span><span class="q-tag %s">%s</span>'
                '<span class="q-lvl">%s</span></div>' % (n[0], qt, QTYPES[qt], dots))
        body = body.replace('<div class="q">', '<div class="q">' + head, 1)
        body = body.replace('<div class="a">', '<div class="a"><div class="a-head">Answer</div>', 1)
        return '<div class="qa%s" id="%s-q%d">%s</div><!--/qa-->' % (keep, label, n[0], body)
    return re.sub(r'<div class="qa"([^>]*)>(.*?)</div><!--/qa-->', rep, text, flags=re.S)


def process_sections(text, key, label, toc):
    n = [0]

    def rep(m):
        n[0] += 1
        title = m.group(1).strip()
        sid = 's-%s-%d' % (key, n[0])
        num = '%s.%d' % (label, n[0])
        plain = htmlmod.unescape(re.sub(r'<[^>]+>', '', title))
        toc.append(('sec', key, num, plain, sid))
        return '<h2 class="sec" id="%s"><span class="num">%s</span><span>%s</span></h2>' % (sid, num, title)
    return re.sub(r'<h2>(.*?)</h2>', rep, text, flags=re.S)


def load_chapters():
    toc, parts = [], []
    for fn, key, label, color in CHAPTERS:
        p = CONTENT / fn
        if not p.exists():
            print('  (missing %s)' % fn)
            continue
        t = p.read_text(encoding='utf-8')
        h1 = re.search(r'<h1>(.*?)</h1>', t, re.S)
        title = htmlmod.unescape(re.sub(r'<[^>]+>', '', h1.group(1))).strip() if h1 else key
        toc.append(('ch', key, label, title, 'ch-' + key, color))
        t = process_sections(t, key, label, toc)
        t = process_questions(t, key)
        t = process_callouts(t)
        parts.append(t)
    return toc, parts


def norm(s):
    return re.sub(r'\s+', '', htmlmod.unescape(s))


def toc_html(toc, pages):
    out = ['<div class="toc">']
    color = '#60a5fa'
    first = True
    for item in toc:
        if item[0] == 'ch':
            _, key, label, title, aid, color = item
            pg = find_page(pages, norm(title))
            if not first:
                out.append('</div>')
            first = False
            out.append('<div class="tblock" style="--c:%s">' % color)
            out.append('<a class="tch" href="#%s"><span class="tn">%s</span>'
                       '<span class="tt">%s</span><span class="tp">%s</span></a>'
                       % (aid, label, htmlmod.escape(title), pg))
        else:
            _, key, num, title, sid = item
            pg = find_page(pages, norm(num + title))
            out.append('<a class="tsec" href="#%s"><span class="sn">%s</span>'
                       '<span>%s</span><span class="tp">%s</span></a>'
                       % (sid, num, htmlmod.escape(title), pg))
    out.append('</div></div>')
    return '\n'.join(out)


def assemble(toc, parts, pages):
    css = (BASE / 'style.css').read_text(encoding='utf-8')
    cover = (CONTENT / '00_cover.html').read_text(encoding='utf-8')
    front = (CONTENT / '01_front.html').read_text(encoding='utf-8')
    front = process_callouts(front).replace('{{TOC}}', toc_html(toc, pages))
    body = cover + front + '\n'.join(parts)
    body = convert_html(body)
    return ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
            '<title>Intelligent Robot Practice — Exam Prep Notes (Lectures 1–7)</title>'
            '<style>%s</style></head><body>%s</body></html>' % (css, body))


def render(html_text, out_pdf):
    tmp = BASE / '_build.html'
    tmp.write_text(html_text, encoding='utf-8')
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page()
        pg.goto(tmp.resolve().as_uri(), wait_until='load')
        pg.wait_for_timeout(300)
        pg.pdf(path=str(out_pdf), prefer_css_page_size=True, print_background=True,
               outline=True, tagged=True)
        b.close()


def outline_pages(pdf_path):
    doc = fitz.open(str(pdf_path))
    pages = {}
    for lvl, title, page in doc.get_toc():
        pages.setdefault(norm(title), page)
    n = doc.page_count
    doc.close()
    return pages, n


def heading_titles(html_text):
    """Map whitespace-free heading text -> properly spaced title (for the PDF outline)."""
    out = {}
    for m in re.finditer(r'<h([123])[^>]*>(.*?)</h\1>', html_text, re.S):
        inner = m.group(2)
        num = re.search(r'<span class="num">(.*?)</span>', inner)
        text = re.sub(r'<span class="num">.*?</span>', '', inner)
        text = re.sub(r'<math.*?</math>', '', text, flags=re.S)
        text = ' '.join(htmlmod.unescape(re.sub(r'<[^>]+>', ' ', text)).split())
        text = re.sub(r'\s+([,.:;])', r'\1', text)
        pretty = (num.group(1) + '  ' + text) if num else text
        out[norm((num.group(1) if num else '') + text)] = pretty
    return out


def fix_outline(pdf_path, titles):
    doc = fitz.open(str(pdf_path))
    toc = []
    for lvl, title, page in doc.get_toc():
        if lvl > 3:
            continue
        key = norm(title)
        pretty = titles.get(key)
        if pretty is None:
            cands = [k for k in titles if key.startswith(k)]
            pretty = titles[max(cands, key=len)] if cands else title
        toc.append([lvl, pretty, page])
    doc.set_toc(toc)
    doc.set_metadata({'title': 'Intelligent Robot Practice — Exam Prep Notes (Lectures 1–7)',
                      'subject': 'Exam preparation notes: modeling, calibration, odometry, Kalman filters, EKF/UKF, pose graphs, optimization',
                      'creator': 'Chromium via Playwright', 'producer': 'PyMuPDF'})
    tmp = pathlib.Path(str(pdf_path) + '.tmp')
    doc.save(str(tmp), garbage=3, deflate=True)
    doc.close()
    tmp.replace(pdf_path)


def main():
    toc, parts = load_chapters()
    tmp_pdf = BASE / '_pass1.pdf'
    html1 = assemble(toc, parts, {})
    render(html1, tmp_pdf)
    pages, n1 = outline_pages(tmp_pdf)
    missing = [t for t in toc if find_page(pages, norm(t[3] if t[0] == 'ch' else t[2] + t[3])) == '']
    if missing:
        print('outline entries not found:', [m[3] for m in missing][:8])
    html2 = assemble(toc, parts, pages)
    render(html2, OUT)
    pages2, n2 = outline_pages(OUT)
    drift = [k for k, v in pages.items() if pages2.get(k) != v]
    fix_outline(OUT, heading_titles(html2))
    print('pages: pass1 %d, final %d%s' % (n1, n2, (' | page drift: %s' % drift[:5]) if drift else ''))
    print('->', OUT)


if __name__ == '__main__':
    main()
