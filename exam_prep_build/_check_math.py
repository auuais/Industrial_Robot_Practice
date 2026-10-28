# -*- coding: utf-8 -*-
"""Convert every $...$ / $$...$$ in the content files and report failures (does not stop at the first)."""
import pathlib
import re
import sys
from tex2mml import tex_to_mathml, TexError

BASE = pathlib.Path(__file__).parent
folder = sys.argv[1] if len(sys.argv) > 1 else 'content'
bad = 0
for p in sorted((BASE / folder).glob('*.html')):
    t = p.read_text(encoding='utf-8')
    disp = re.findall(r'\$\$(.+?)\$\$', t, re.S)
    rest = re.sub(r'\$\$(.+?)\$\$', ' ', t, flags=re.S)
    inl = re.findall(r'(?<![\\$])\$(?!\$)(.+?)(?<!\\)\$', rest, re.S)
    for s, d in [(x, True) for x in disp] + [(x, False) for x in inl]:
        try:
            from html import unescape; tex_to_mathml(unescape(s), d)
        except (TexError, Exception) as e:
            bad += 1
            print(p.name, '|', str(e)[:160].encode('ascii', 'replace').decode())
    print(p.name, len(disp), 'display,', len(inl), 'inline')
print('failures:', bad)
