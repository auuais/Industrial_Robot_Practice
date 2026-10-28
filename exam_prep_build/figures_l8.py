# -*- coding: utf-8 -*-
"""Figures for the Lecture 8 notes: graph snapshots (hand-built SVG) and one matplotlib plot."""
import math
import pathlib

FIG = pathlib.Path(__file__).parent / 'fig'
FIG.mkdir(exist_ok=True)

COL = dict(edge='#5d6880', text='#dfe4ec', muted='#a3acbd', faint='#737e92', node='#1c2230',
           ring='#8a94a7', teal='#2dd4bf', blue='#60a5fa', orange='#fb923c', rose='#fb7185',
           green='#4ade80', amber='#fbbf24', violet='#a78bfa', bg='#161b24', cyan='#22d3ee')

LECT_POS = {'S': (40, 150), 'A': (150, 60), 'C': (290, 60), 'G': (410, 150),
            'B': (150, 240), 'E': (290, 240), 'D': (40, 300)}
LECT_EDGES = [('S', 'A', 2, 1), ('A', 'C', 5, 1), ('C', 'G', 3, 1), ('S', 'B', 6, -1), ('A', 'B', 1, 1),
              ('B', 'C', 2, -1), ('B', 'E', 1, -1), ('E', 'G', 6, -1), ('S', 'D', 1, 1), ('D', 'E', 10, 1)]
OPT = {('S', 'A'), ('A', 'B'), ('B', 'C'), ('C', 'G')}


def defs():
    out = ['<defs>']
    for name, c in COL.items():
        out.append('<marker id="ar-%s" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6.5" markerHeight="6.5" '
                   'orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" fill="%s"/></marker>' % (name, c))
    out.append('</defs>')
    return ''.join(out)


def text(x, y, s, color=COL['text'], size=12, anchor='middle', weight=400, family='Segoe UI', italic=False):
    st = 'font-style:italic;' if italic else ''
    return ('<text x="%.1f" y="%.1f" text-anchor="%s" style="fill:%s;font-size:%spx;font-weight:%s;'
            'font-family:%s;%s">%s</text>' % (x, y, anchor, color, size, weight, family, st, s))


def graph(pos, edges, ox=0, oy=0, title=None, node_style=None, edge_style=None, notes=None,
          r=15, label_dist=11, extra=''):
    """edges: (u, v, cost, side). edge_style[(u,v)] = (color, width, dash, label_override)."""
    node_style = node_style or {}
    edge_style = edge_style or {}
    notes = notes or {}
    out = ['<g transform="translate(%d,%d)">' % (ox, oy)]
    if title:
        out.append(text(0, -14, title, COL['muted'], 12.5, 'start', 600))
    for (u, v, c, side) in edges:
        (x1, y1), (x2, y2) = pos[u], pos[v]
        dx, dy = x2 - x1, y2 - y1
        L = math.hypot(dx, dy)
        ux, uy = dx / L, dy / L
        sx, sy = x1 + ux * (r + 1), y1 + uy * (r + 1)
        ex, ey = x2 - ux * (r + 3), y2 - uy * (r + 3)
        color, width, dash, lab = edge_style.get((u, v), ('edge', 1.4, None, None))
        cval = COL[color]
        da = ' stroke-dasharray="%s"' % dash if dash else ''
        out.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" stroke-width="%s"%s '
                   'marker-end="url(#ar-%s)"/>' % (sx, sy, ex, ey, cval, width, da, color))
        mx, my = (x1 + x2) / 2 - uy * label_dist * side, (y1 + y2) / 2 + ux * label_dist * side
        lab = str(c) if lab is None else lab
        lc = cval if color not in ('edge',) else COL['muted']
        out.append(text(mx, my + 4.5, lab, lc, 13, 'middle', 600 if color != 'edge' else 400, 'Cambria, serif'))
    for n, (x, y) in pos.items():
        fill, ring, tcol = node_style.get(n, (COL['node'], COL['ring'], COL['text']))
        out.append('<circle cx="%d" cy="%d" r="%d" fill="%s" stroke="%s" stroke-width="1.8"/>' % (x, y, r, fill, ring))
        out.append(text(x, y + 5, n, tcol, 15, 'middle', 600, 'Cambria, serif'))
    for n, items in notes.items():
        x, y = pos[n]
        for (dx, dy, s, color, anchor) in items:
            out.append(text(x + dx, y + dy, s, COL.get(color, color), 12, anchor, 600))
    out.append(extra)
    out.append('</g>')
    return ''.join(out)


def svg(w, h, body):
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d" '
            'font-family="Segoe UI">%s%s</svg>' % (w, h, w, h, defs(), body))


def save(name, s):
    (FIG / (name + '.svg')).write_text(s, encoding='utf-8')
    print('  fig', name)


CLOSED = ('#16343a', COL['teal'], COL['text'])
OPENN = (COL['node'], COL['orange'], COL['text'])
CUR = ('#4a2a14', COL['orange'], COL['text'])
DIM = ('#141820', '#3a4560', COL['faint'])
GOALS = ('#13261d', COL['green'], COL['text'])


def path_style(path_edges, color='teal', width=3):
    return {e: (color, width, None, None) for e in path_edges}


def lect_base():
    st = path_style(OPT)
    body = graph(LECT_POS, LECT_EDGES, 20, 30, None, edge_style=st,
                 notes={'S': [(0, 34, 'start', 'muted', 'middle')], 'G': [(0, 34, 'goal', 'muted', 'middle')]})
    save('l8_graph', svg(470, 360, body))


def g_notes(g, side=None):
    side = side or {}
    pos_off = {'S': (0, -24), 'A': (0, -24), 'C': (0, -24), 'G': (0, -24), 'B': (-22, 5), 'E': (0, 34), 'D': (30, 5)}
    out = {}
    for n, val in g.items():
        dx, dy = side.get(n, pos_off[n])
        out[n] = [(dx, dy, val, 'amber', 'middle' if dx == 0 else ('start' if dx > 0 else 'end'))]
    return out


def dijkstra_panels():
    snaps = [
        ('Step 1 · pop S, relax A, B, D', {'S': CLOSED, 'A': OPENN, 'B': OPENN, 'D': OPENN},
         {'S': 'g=0', 'A': 'g=2', 'B': 'g=6', 'D': 'g=1'}, {('S', 'A'), ('S', 'B'), ('S', 'D')}),
        ('Step 3 · pop A: B improves 6 → 3', {'S': CLOSED, 'D': CLOSED, 'A': CUR, 'B': OPENN, 'C': OPENN, 'E': OPENN},
         {'S': 'g=0', 'D': 'g=1', 'A': 'g=2', 'B': 'g=3', 'C': 'g=7', 'E': 'g=11'}, {('S', 'A'), ('S', 'D'), ('A', 'B'), ('A', 'C'), ('D', 'E')}),
        ('Step 5 · pop E: G found with g = 10 (not final!)', {'S': CLOSED, 'D': CLOSED, 'A': CLOSED, 'B': CLOSED, 'E': CUR, 'C': OPENN, 'G': OPENN},
         {'S': 'g=0', 'D': 'g=1', 'A': 'g=2', 'B': 'g=3', 'C': 'g=5', 'E': 'g=4', 'G': 'g=10'}, {('S', 'A'), ('S', 'D'), ('A', 'B'), ('B', 'C'), ('B', 'E'), ('E', 'G')}),
        ('Step 7 · pop G with g = 8 → stop', {n: CLOSED for n in 'SDABEC'} | {'G': GOALS},
         {'S': 'g=0', 'D': 'g=1', 'A': 'g=2', 'B': 'g=3', 'C': 'g=5', 'E': 'g=4', 'G': 'g=8'}, {('S', 'A'), ('S', 'D'), ('A', 'B'), ('B', 'C'), ('B', 'E'), ('C', 'G')}),
    ]
    body = []
    for i, (title, ns, gv, tree) in enumerate(snaps):
        ox, oy = 20 + (i % 2) * 480, 44 + (i // 2) * 385
        st = {e: ('blue', 2.4, None, None) for e in tree}
        if i == 3:
            st.update(path_style(OPT))
        body.append(graph(LECT_POS, LECT_EDGES, ox, oy, title, node_style=ns, edge_style=st, notes=g_notes(gv)))
    leg = ('<g transform="translate(20,790)">'
           '<circle cx="8" cy="0" r="7" fill="#16343a" stroke="%s" stroke-width="1.8"/>%s'
           '<circle cx="128" cy="0" r="7" fill="%s" stroke="%s" stroke-width="1.8"/>%s'
           '<circle cx="232" cy="0" r="7" fill="#4a2a14" stroke="%s" stroke-width="1.8"/>%s'
           '<line x1="352" y1="0" x2="382" y2="0" stroke="%s" stroke-width="2.4"/>%s'
           '<line x1="560" y1="0" x2="590" y2="0" stroke="%s" stroke-width="3"/>%s</g>' % (
               COL['teal'], text(22, 4, 'CLOSED (final)', COL['muted'], 12, 'start'),
               COL['node'], COL['orange'], text(142, 4, 'in OPEN', COL['muted'], 12, 'start'),
               COL['orange'], text(246, 4, 'just popped', COL['muted'], 12, 'start'),
               COL['blue'], text(390, 4, 'parent links (best so far)', COL['muted'], 12, 'start'),
               COL['teal'], text(598, 4, 'final shortest path, cost 8', COL['muted'], 12, 'start')))
    body.append(leg)
    save('l8_dijkstra', svg(960, 805, ''.join(body)))


def astar_panels():
    hv = {'S': 7, 'A': 5, 'B': 4, 'C': 2, 'D': 9, 'E': 4, 'G': 0}
    hnotes = {n: [(0, -24 if n in 'SACG' else 34, ('h=%d*' if n in 'SE' else 'h=%d') % v, 'violet' if n not in 'SE' else 'faint', 'middle')] for n, v in hv.items()}
    hnotes['B'] = [(-22, 5, 'h=4', 'violet', 'end')]
    hnotes['D'] = [(30, 5, 'h=9', 'violet', 'start')]
    p1 = graph(LECT_POS, LECT_EDGES, 20, 44, 'Heuristic h (estimated cost to G)', notes=hnotes,
               edge_style=path_style(set(), 'teal'))
    fn = {'A': [(0, -24, '2+5=7', 'orange', 'middle')], 'B': [(0, 34, '6+4=10', 'amber', 'middle')],
          'D': [(30, 5, '1+9=10', 'amber', 'start')], 'S': [(0, -24, '0+7=7', 'muted', 'middle')]}
    fn['B'] = [(-22, 5, '6+4=10', 'amber', 'end')]
    st = {('S', 'A'): ('orange', 2.6, None, None), ('S', 'B'): ('amber', 2, None, None), ('S', 'D'): ('amber', 2, None, None)}
    p2 = graph(LECT_POS, LECT_EDGES, 500, 44, 'After expanding S: f = g + h', node_style={'S': CLOSED, 'A': CUR, 'B': OPENN, 'D': OPENN},
               notes=fn, edge_style=st)
    ns = {n: CLOSED for n in 'SABC'} | {'G': GOALS, 'D': DIM, 'E': OPENN}
    p3 = graph(LECT_POS, LECT_EDGES, 20, 430, 'A*: expanded S, A, B, C → G (4 expansions)', node_style=ns,
               edge_style=path_style(OPT), notes={'D': [(30, 5, 'never reached', 'faint', 'start')], 'E': [(0, 34, 'in OPEN, f=8', 'orange', 'middle')]})
    ns2 = {n: CLOSED for n in 'SABCDE'} | {'G': GOALS}
    p4 = graph(LECT_POS, LECT_EDGES, 500, 430, 'Dijkstra: expanded S, D, A, B, E, C → G (6)', node_style=ns2,
               edge_style=path_style(OPT))
    note = text(250, 18, '* h(S)=7 and h(E)=4 are not on the slides; chosen so that h stays consistent.', COL['faint'], 11.5, 'start')
    save('l8_astar', svg(960, 790, p1 + p2 + p3 + p4 + '<g transform="translate(20,770)">' + note + '</g>'))


def weighted_panel():
    st = path_style(OPT, 'teal', 2.2)
    for e in OPT:
        st[e] = ('teal', 2, '5 4', None)
    st.update({('S', 'A'): ('orange', 3, None, None), ('A', 'C'): ('orange', 3, None, None), ('C', 'G'): ('orange', 3, None, None)})
    ns = {'S': CLOSED, 'A': CLOSED, 'C': CLOSED, 'G': GOALS, 'B': OPENN, 'D': OPENN}
    notes = {'S': [(0, -24, 'f=0+14=14', 'muted', 'middle')], 'A': [(0, -24, 'f=2+10=12', 'muted', 'middle')],
             'C': [(0, -24, 'f=7+4=11', 'orange', 'middle')], 'B': [(-22, 5, 'f=3+8=11 (tie)', 'amber', 'end')],
             'G': [(0, -24, 'g=10', 'orange', 'middle')], 'D': [(30, 5, 'f=1+18=19', 'amber', 'start')]}
    body = graph(LECT_POS, LECT_EDGES, 20, 44, 'Weighted A* with ε = 2: f = g + 2h', node_style=ns, edge_style=st, notes=notes)
    leg = ('<g transform="translate(500,110)">%s%s%s%s%s%s</g>' % (
        '<line x1="0" y1="0" x2="34" y2="0" stroke="%s" stroke-width="3"/>' % COL['orange'],
        text(44, 4, 'path found: S–A–C–G, cost 10', COL['text'], 13, 'start'),
        '<line x1="0" y1="34" x2="34" y2="34" stroke="%s" stroke-width="2" stroke-dasharray="5 4"/>' % COL['teal'],
        text(44, 38, 'optimal path: S–A–B–C–G, cost 8', COL['text'], 13, 'start'),
        text(0, 84, 'Guarantee: J(P) ≤ ε·J* = 2 × 8 = 16  ✓', COL['amber'], 13, 'start', 600),
        text(0, 112, 'Only 3 expansions (S, A, C), but 2 units more expensive.', COL['muted'], 12.5, 'start')))
    save('l8_weighted', svg(960, 400, body + leg))


def changes_panels():
    e1 = list(LECT_EDGES)
    st1 = {('B', 'C'): ('rose', 2.4, '6 4', '2 → ∞')}
    st1.update({('S', 'A'): ('teal', 3, None, None), ('A', 'C'): ('teal', 3, None, None), ('C', 'G'): ('teal', 3, None, None)})
    p1 = graph(LECT_POS, e1, 20, 44, 'B→C closed: old path invalid, J* 8 → 10', edge_style=st1,
               notes={'G': [(0, -24, 'J*=10', 'teal', 'middle')]})
    st2 = {('S', 'B'): ('green', 2.8, None, '6 → 1')}
    st2.update({('B', 'C'): ('teal', 3, None, None), ('C', 'G'): ('teal', 3, None, None)})
    st2[('S', 'B')] = ('teal', 3, None, '6 → 1')
    p2 = graph(LECT_POS, e1, 500, 44, 'S→B cheaper: old path not optimal, J* 8 → 6', edge_style=st2,
               notes={'G': [(0, -24, 'J*=6', 'teal', 'middle')]})
    note = text(0, 0, 'Teal = new best path. Tie at 10 on the left: S–A–C–G and S–A–B–E–G both cost 10.', COL['faint'], 12, 'start')
    save('l8_changes', svg(960, 410, p1 + p2 + '<g transform="translate(20,398)">' + note + '</g>'))


def dstar_panels():
    gto = {'S': 'g=8', 'A': 'g=6', 'B': 'g=5', 'C': 'g=3', 'D': 'g=16', 'E': 'g=6', 'G': 'g=0'}
    st = {('S', 'A'): ('ring', 3.4, None, None), ('A', 'B'): ('ring', 3.4, None, None),
          ('B', 'C'): ('blue', 2.6, None, None), ('C', 'G'): ('blue', 2.6, None, None)}
    ns = {'B': CUR, 'S': DIM, 'A': DIM}
    p1 = graph(LECT_POS, LECT_EDGES, 20, 44, 'Cost-to-go g (node → G); robot has driven S→A→B', node_style=ns,
               edge_style=st, notes=g_notes(gto))
    gto2 = {'S': 'g=8', 'A': 'g=6 → ∞', 'B': 'g=5 → ∞ → 7', 'C': 'g=3', 'D': 'g=16', 'E': 'g=6', 'G': 'g=0'}
    st2 = {('S', 'A'): ('ring', 3.4, None, None), ('A', 'B'): ('ring', 3.4, None, None),
           ('B', 'C'): ('rose', 2.4, '6 4', '∞'), ('B', 'E'): ('green', 3, None, None), ('E', 'G'): ('green', 3, None, None)}
    nt = g_notes(gto2)
    nt['B'] = [(-22, 5, 'g=5 → ∞ → 7', 'amber', 'end')]
    nt['A'] = [(0, -24, 'g=6 → ∞', 'amber', 'middle')]
    p2 = graph(LECT_POS, LECT_EDGES, 500, 44, 'At B the robot sees B→C closed: repair, then move to E', node_style=ns,
               edge_style=st2, notes=nt)
    save('l8_dstar', svg(960, 400, p1 + p2))


def km_figure():
    s = 46
    ox, oy = 30, 30
    grid = []
    for i in range(7):
        grid.append('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="#29324a" stroke-width="1"/>' % (ox + i * s, oy, ox + i * s, oy + 3 * s))
    for j in range(4):
        grid.append('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="#29324a" stroke-width="1"/>' % (ox, oy + j * s, ox + 6 * s, oy + j * s))
    A, B, X = (ox, oy + 3 * s), (ox + 2 * s, oy + 2 * s), (ox + 5 * s, oy + 3 * s)
    pts = ''.join('<circle cx="%d" cy="%d" r="15" fill="%s" stroke="%s" stroke-width="1.8"/>%s' % (
        x, y, f, r, text(x, y + 5, n, COL['text'], 15, 'middle', 600, 'Cambria, serif'))
        for (x, y), n, f, r in ((A, 'A', COL['node'], COL['ring']), (B, 'B', '#4a2a14', COL['orange']), (X, 'X', '#16343a', COL['teal'])))
    path = '<polyline points="%d,%d %d,%d %d,%d" fill="none" stroke="%s" stroke-width="2.4" marker-end="url(#ar-orange)"/>' % (
        A[0] + 15, A[1], A[0] + 2 * s, A[1], B[0], B[1] + 17, COL['orange'])
    labels = (text(A[0] - 14, A[1] + 34, 'robot moves A→B: h(A,B) = 3, so kₘ: 0 → 3', COL['orange'], 12, 'start', 600) +
              text(X[0], X[1] - 26, 'X: g=8, rhs=7', COL['teal'], 12, 'middle', 600) +
              text(ox + 6 * s + 18, oy + 20, 'h(A,X) = 5', COL['muted'], 12.5, 'start') +
              text(ox + 6 * s + 18, oy + 42, 'h(B,X) = 4', COL['muted'], 12.5, 'start') +
              text(ox + 6 * s + 18, oy + 64, 'unit steps, Manhattan h', COL['faint'], 12, 'start'))
    save('l8_km', svg(460, 212, ''.join(grid) + path + pts + labels))


def hpa_figure():
    pos = {'S': (40, 60), 'a': (150, 40), 'b': (260, 40), 'c': (110, 140), 'e': (330, 140),
           'd': (110, 230), 'f': (330, 230), 'g': (175, 320), 'h': (285, 320), 'G': (420, 320)}
    edges = [('S', 'a', 6, -1), ('S', 'c', 4, 1), ('a', 'b', 1, -1), ('a', 'c', 6, 1), ('b', 'e', 8, -1),
             ('c', 'd', 1, 1), ('e', 'f', 1, -1), ('d', 'g', 5, 1), ('f', 'h', 5, -1), ('g', 'h', 1, 1),
             ('h', 'G', 7, 1), ('f', 'G', 4, -1)]
    chosen = {('S', 'c'), ('c', 'd'), ('d', 'g'), ('g', 'h'), ('h', 'G')}
    st = {e: ('green', 3, None, None) for e in chosen}
    for e in [('S', 'a'), ('a', 'c'), ('b', 'e'), ('f', 'h'), ('e', 'f'), ('f', 'G'), ('a', 'b')]:
        st[e] = ('edge', 1.4, None, None)
    # draw undirected: strip arrowheads by using lines without markers
    body = graph(pos, edges, 30, 44, 'Abstract graph with S and G inserted (costs = stored inner paths)', edge_style=st,
                 node_style={'S': CUR, 'G': GOALS})
    body = body.replace('marker-end="url(#ar-edge)"', '').replace('marker-end="url(#ar-green)"', '')
    cl = ('<g transform="translate(540,60)">%s%s%s%s%s%s</g>' % (
        text(0, 0, 'Candidate routes on the abstract graph', COL['muted'], 12.5, 'start', 600),
        text(0, 28, 'S–c–d–g–h–G = 4+1+5+1+7 = 18', COL['green'], 13.5, 'start', 600),
        text(0, 52, 'S–a–b–e–f–G = 6+1+8+1+4 = 20', COL['text'], 13.5, 'start'),
        text(0, 76, 'S–c–d–g–h–f–G = 4+1+5+1+5+4 = 20', COL['text'], 13.5, 'start'),
        text(0, 116, 'A* picks 18; the true grid optimum is 16.', COL['amber'], 13, 'start', 600),
        text(0, 140, 'The 2 extra cells come from where the portals sit.', COL['muted'], 12.5, 'start')))
    save('l8_hpa', svg(960, 410, body + cl))


def ch_figure():
    pos = {'u': (40, 110), 'v': (130, 20), 'w': (220, 110), 'z': (130, 200)}
    edges = [('u', 'v', 2, 1), ('v', 'w', 3, 1), ('u', 'z', 3, -1), ('z', 'w', 3, -1)]
    def und(s):
        return s.replace('marker-end="url(#ar-edge)"', '').replace('marker-end="url(#ar-blue)"', '') \
                .replace('marker-end="url(#ar-rose)"', '').replace('marker-end="url(#ar-green)"', '')
    p1 = graph(pos, edges, 30, 50, '① Original: d(u,w) = 5 via v', edge_style={('u', 'v'): ('blue', 2.6, None, None), ('v', 'w'): ('blue', 2.6, None, None)},
               node_style={'v': CUR})
    e2 = [('u', 'z', 3, -1), ('z', 'w', 3, -1)]
    pos2 = dict(pos)
    p2 = graph({k: v for k, v in pos2.items() if k != 'v'}, e2, 350, 50, '② Remove v, no shortcut: d = 6 ✗',
               edge_style={('u', 'z'): ('rose', 2.6, None, None), ('z', 'w'): ('rose', 2.6, None, None)})
    e3 = [('u', 'w', 5, 1), ('u', 'z', 3, -1), ('z', 'w', 3, -1)]
    p3 = graph({k: v for k, v in pos.items() if k != 'v'}, e3, 670, 50, '③ Add shortcut u–w (5): d = 5 ✓',
               edge_style={('u', 'w'): ('green', 2.6, '7 5', None)},
               notes={'u': [(110, -46, 'unpacks to u→v→w', 'green', 'middle')]})
    note = text(30, 300, 'Witness test: shortest u→w path avoiding v is u→z→w = 6 > 5, so the shortcut is needed.  '
                'Edge Difference = 1 added − 2 removed = −1.', COL['muted'], 12.5, 'start')
    save('l8_ch', svg(960, 315, und(p1 + p2 + p3) + note))


def fsm_figure():
    boxes = {'FollowRoute': (60, 40, 'runs a valid route'), 'Hold': (480, 40, 'paused'),
             'Replan': (480, 210, 'one replan on entry'), 'Arrived': (60, 210, 'mission over')}
    out = []
    for name, (x, y, sub) in boxes.items():
        col = {'FollowRoute': COL['blue'], 'Hold': COL['amber'], 'Replan': COL['rose'], 'Arrived': COL['green']}[name]
        out.append('<rect x="%d" y="%d" width="190" height="62" rx="10" fill="#1c2230" stroke="%s" stroke-width="1.8"/>' % (x, y, col))
        out.append(text(x + 95, y + 27, name, col, 16, 'middle', 700))
        out.append(text(x + 95, y + 48, sub, COL['muted'], 12, 'middle'))

    def arrow(d, color, label, lx, ly, anchor='middle'):
        out.append('<path d="%s" fill="none" stroke="%s" stroke-width="1.8" marker-end="url(#ar-%s)"/>' % (d, COL[color], color))
        out.append(text(lx, ly, label, COL[color], 12.5, anchor, 600))
    arrow('M 250 58 C 330 22, 400 22, 478 58', 'amber', 'a = 1 (hold request)', 364, 22)
    arrow('M 478 86 C 400 118, 330 118, 252 86', 'blue', 'a = 0 and r = 1', 364, 128)
    arrow('M 230 104 C 330 150, 420 190, 478 228', 'rose', 'r = 0 (route invalid)', 500, 176, 'start')
    arrow('M 478 258 C 380 262, 290 210, 232 106', 'green', 'new route verified', 340, 268)
    arrow('M 140 104 L 140 208', 'ring', 'd = 1 (mission done)', 132, 162, 'end')
    save('l8_fsm', svg(720, 290, ''.join(out)))


def family_figure():
    cols = [('Find the cheapest path', 'blue', ['Relaxation', 'Dijkstra', 'A*']),
            ('Short on time', 'amber', ['Weighted A*', 'reuse g, parent', 'ARA* (anytime)']),
            ('Map changes', 'rose', ['LPA* (g vs rhs)', 'D* Lite (robot moves)', 'key modifier kₘ']),
            ('Map is huge', 'violet', ['HPA* (clusters, portals)', 'CH (shortcuts, ranks)']),
            ('Execute the route', 'green', ['FSM: follow / hold / replan', 'guards + priority', 'hysteresis'])]
    out = []
    for i, (title, c, items) in enumerate(cols):
        x = 10 + i * 190
        out.append('<rect x="%d" y="10" width="178" height="40" rx="9" fill="#1c2230" stroke="%s" stroke-width="1.6"/>' % (x, COL[c]))
        out.append(text(x + 89, 35, title, COL[c], 13.5, 'middle', 700))
        for j, it in enumerate(items):
            y = 66 + j * 40
            out.append('<rect x="%d" y="%d" width="178" height="32" rx="7" fill="#161b24" stroke="#29324a"/>' % (x, y))
            out.append(text(x + 89, y + 21, it, COL['text'], 12.5, 'middle'))
            if j:
                out.append('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="%s" stroke-width="1.4" marker-end="url(#ar-%s)"/>' % (
                    x + 89, y - 8, x + 89, y - 1, COL[c], c))
    save('l8_family', svg(960, 190, ''.join(out)))


def small_graphs():
    # negative edge counterexample
    pos = {'S': (40, 90), 'A': (190, 30), 'B': (190, 150)}
    e = [('S', 'A', 2, 1), ('S', 'B', 3, -1), ('B', 'A', '−2', -1)]
    body = graph(pos, e, 20, 30, None, edge_style={('B', 'A'): ('rose', 2.4, None, '−2')},
                 notes={'A': [(26, 5, 'Dijkstra: 2 (final too early)', 'rose', 'start'), (26, 23, 'true: 3 − 2 = 1', 'green', 'start')]})
    save('l8_negative', svg(470, 210, body))
    # inconsistent heuristic → re-expansion
    pos = {'S': (40, 100), 'A': (170, 30), 'B': (170, 170), 'G': (320, 170)}
    e = [('S', 'A', 1, 1), ('S', 'B', 4, -1), ('A', 'B', 1, 1), ('B', 'G', 3, -1)]
    notes = {'S': [(0, -24, 'h=0', 'violet', 'middle')], 'A': [(0, -24, 'h=4', 'violet', 'middle')],
             'B': [(0, 34, 'h=0', 'violet', 'middle')], 'G': [(0, 34, 'h=0', 'violet', 'middle')]}
    body = graph(pos, e, 20, 20, None, notes=notes, edge_style={('A', 'B'): ('rose', 2.4, None, None)})
    body += text(230, 60, 'h(A)=4 > c(A,B)+h(B) = 1', COL['rose'], 12.5, 'start', 600)
    save('l8_reexp', svg(470, 240, body))
    # practice graph
    pos = {'S': (40, 150), 'A': (170, 60), 'B': (170, 240), 'C': (300, 60), 'D': (300, 240), 'E': (40, 300), 'G': (420, 150)}
    e = [('S', 'A', 4, 1), ('S', 'B', 1, -1), ('B', 'A', 2, -1), ('A', 'C', 1, 1), ('B', 'D', 6, -1),
         ('C', 'D', 2, 1), ('C', 'G', 5, 1), ('D', 'G', 1, -1), ('S', 'E', 1, 1)]
    epos = dict(pos)
    body = graph(epos, e, 20, 34, None,
                 notes={'S': [(0, -24, 'h=6', 'violet', 'middle')], 'A': [(0, -24, 'h=4', 'violet', 'middle')],
                        'B': [(0, 34, 'h=5', 'violet', 'middle')], 'C': [(0, -24, 'h=3', 'violet', 'middle')],
                        'D': [(0, 34, 'h=1', 'violet', 'middle')], 'E': [(26, 5, 'h=8', 'violet', 'start')],
                        'G': [(0, -24, 'h=0', 'violet', 'middle')]})
    # E→G long edge drawn as a curve
    ex, ey = 20 + 40, 34 + 300
    gx, gy = 20 + 420, 34 + 150
    body += ('<path d="M %d %d C %d %d, %d %d, %d %d" fill="none" stroke="%s" stroke-width="1.4" marker-end="url(#ar-edge)"/>' % (
        ex + 16, ey + 2, 260, ey + 50, gx + 30, gy + 120, gx + 6, gy + 17, COL['edge']))
    body += text(330, 368, '8', COL['muted'], 13, 'middle', 400, 'Cambria, serif')
    save('l8_practice', svg(470, 390, body))


def hysteresis_plot():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    C = dict(text='#dfe4ec', muted='#a3acbd', gray='#8a94a7', grid='#263044', spine='#3a4560')
    plt.rcParams.update({'font.family': 'Segoe UI', 'font.size': 8.6, 'text.color': C['text'], 'axes.labelcolor': C['muted'],
                         'axes.edgecolor': C['spine'], 'xtick.color': C['gray'], 'ytick.color': C['gray'],
                         'axes.facecolor': 'none', 'figure.facecolor': 'none', 'savefig.transparent': True,
                         'axes.grid': True, 'grid.color': C['grid'], 'grid.linewidth': 0.6, 'svg.fonttype': 'path',
                         'axes.spines.top': False, 'axes.spines.right': False, 'legend.frameon': False})
    dJ = [0.5, -0.3, 0.6, -0.1, 2.6, 1.1, -0.4, -2.6]
    k = list(range(8))

    def run(delta):
        cur, hist = 'A', []
        for x in dJ:
            if delta == 0:
                cur = 'B' if x > 0 else 'A'
            elif cur == 'A' and x > delta:
                cur = 'B'
            elif cur == 'B' and x < -delta:
                cur = 'A'
            hist.append(cur)
        return hist
    fig, axs = plt.subplots(3, 1, figsize=(6.6, 3.9), sharex=True, gridspec_kw=dict(hspace=0.25, height_ratios=[1.5, 1, 1]))
    ax = axs[0]
    ax.axhspan(-2, 2, color='#fb7185', alpha=0.08, lw=0)
    ax.axhline(2, color='#fb7185', lw=0.9, ls='--')
    ax.axhline(-2, color='#fb7185', lw=0.9, ls='--')
    ax.plot(k, dJ, '-o', color='#60a5fa', ms=4)
    ax.set_ylabel(r'$\Delta J = J_A - J_B$')
    ax.set_xlim(-0.7, 7.6)
    ax.text(7.3, 2.0, '+δ', color='#fb7185', va='center', fontsize=8.5)
    ax.text(7.3, -2.0, '−δ', color='#fb7185', va='center', fontsize=8.5)
    ax.set_title('Cost difference of two valid routes (values read from slide 23, approximate)', loc='left')
    for ax, delta, col, ttl in ((axs[1], 0, '#fbbf24', 'Always pick the cheaper route: 6 switches'),
                                (axs[2], 2, '#4ade80', 'Hysteresis with δ = 2: 2 switches')):
        h = run(delta)
        y = [1 if s == 'A' else 0 for s in h]
        ax.step([-0.5] + k, [1] + y, where='post', color=col, lw=2)
        ax.set_yticks([0, 1])
        ax.set_yticklabels([r'$R_B$', r'$R_A$'])
        ax.set_ylim(-0.4, 1.5)
        ax.set_title(ttl, loc='left', color=col)
    axs[2].set_xlabel('time step k')
    fig.savefig(FIG / 'l8_hyst.svg', bbox_inches='tight', pad_inches=0.04)
    plt.close(fig)
    print('  fig l8_hyst')


if __name__ == '__main__':
    lect_base()
    dijkstra_panels()
    astar_panels()
    weighted_panel()
    changes_panels()
    dstar_panels()
    km_figure()
    hpa_figure()
    ch_figure()
    fsm_figure()
    family_figure()
    small_graphs()
    hysteresis_plot()
