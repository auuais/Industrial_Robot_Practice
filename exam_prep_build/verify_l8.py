# -*- coding: utf-8 -*-
"""Recompute every Lecture 8 example (slides + new practice problems) with traces."""
import heapq
import math

INF = math.inf
LECT = {('S', 'A'): 2, ('A', 'C'): 5, ('C', 'G'): 3, ('S', 'B'): 6, ('A', 'B'): 1,
        ('B', 'C'): 2, ('B', 'E'): 1, ('E', 'G'): 6, ('S', 'D'): 1, ('D', 'E'): 10}
H_L = {'S': 7, 'A': 5, 'B': 4, 'C': 2, 'D': 9, 'E': 4, 'G': 0}
PRAC = {('S', 'A'): 4, ('S', 'B'): 1, ('B', 'A'): 2, ('A', 'C'): 1, ('B', 'D'): 6,
        ('C', 'D'): 2, ('C', 'G'): 5, ('D', 'G'): 1, ('S', 'E'): 1, ('E', 'G'): 8}
H_P = {'S': 6, 'A': 4, 'B': 5, 'C': 3, 'D': 1, 'E': 8, 'G': 0}


def succ(E, u):
    return [(v, c) for (a, v), c in sorted(E.items()) if a == u]


def pred(E, v):
    return [(u, c) for (u, b), c in sorted(E.items()) if b == v]


def nodes(E):
    return sorted({n for e in E for n in e})


def fmt(x):
    return '∞' if x == INF else ('%g' % x)


def best_first(E, h, eps=1.0, start='S', goal='G', label='', g0=None, parent0=None, open0=None):
    """A*/Dijkstra/weighted A* with a trace. Ties: smaller f, then larger g, then name."""
    g = dict(g0) if g0 else {n: INF for n in nodes(E)}
    parent = dict(parent0) if parent0 else {n: None for n in nodes(E)}
    if not g0:
        g[start] = 0
    OPEN = set(open0) if open0 is not None else {start}
    CLOSED = set()
    key = lambda n: (g[n] + eps * h[n], -g[n], n)
    print('\n==== %s (eps=%g)' % (label, eps))
    step = 0
    while OPEN:
        u = min(OPEN, key=key)
        step += 1
        opened = ', '.join('%s:%s' % (n, fmt(g[n] + eps * h[n])) for n in sorted(OPEN, key=key))
        print('step %d  OPEN[%s]  -> pop %s (g=%s, f=%s)' % (step, opened, u, fmt(g[u]), fmt(g[u] + eps * h[u])))
        OPEN.remove(u)
        if u == goal:
            path, n = [], goal
            while n:
                path.append(n)
                n = parent[n]
            print('   PATH', '-'.join(reversed(path)), 'cost', g[goal], 'expanded', sorted(CLOSED))
            return g, parent, OPEN, CLOSED
        CLOSED.add(u)
        for v, c in succ(E, u):
            if v in CLOSED:
                continue
            t = g[u] + c
            if t < g[v]:
                print('     relax %s->%s: %s + %s = %s < %s  => g(%s)=%s, parent=%s' % (u, v, fmt(g[u]), c, fmt(t), fmt(g[v]), v, fmt(t), u))
                g[v], parent[v] = t, u
                OPEN.add(v)
            else:
                print('     relax %s->%s: %s + %s = %s  not < %s' % (u, v, fmt(g[u]), c, fmt(t), fmt(g[v])))
    return g, parent, OPEN, CLOSED


def all_pairs_to(E, goal='G'):
    d = {n: INF for n in nodes(E)}
    d[goal] = 0
    for _ in range(len(d)):
        for (u, v), c in E.items():
            d[u] = min(d[u], c + d[v])
    return d


def check_h(E, h, name):
    hs = all_pairs_to(E)
    adm = all(h[n] <= hs[n] for n in h)
    bad = [(u, v) for (u, v), c in E.items() if h[u] > c + h[v]]
    print('\n%s: h* =' % name, {n: fmt(v) for n, v in hs.items()}, '| admissible', adm, '| inconsistent edges', bad)


def lpa_repair(E, g, label, h=None):
    """LPA* (h = 0 unless given) starting from a previous g. Prints each pop."""
    h = h or {n: 0 for n in g}
    g = dict(g)

    def rhs(v):
        if v == 'S':
            return 0
        return min([g[u] + c for u, c in pred(E, v)] or [INF])

    def key(v):
        m = min(g[v], rhs(v))
        return (m + h[v], m)
    U = {v for v in g if g[v] != rhs(v)}
    print('\n==== LPA* repair:', label, '| inconsistent at start:', {v: (fmt(g[v]), fmt(rhs(v))) for v in sorted(U)})
    while U:
        u = min(U, key=lambda v: (key(v), v))
        if key(u) >= key('G') and g['G'] == rhs('G'):
            break
        U.remove(u)
        before = (g[u], rhs(u))
        if g[u] > rhs(u):
            g[u] = rhs(u)
            todo = [v for v, c in succ(E, u)]
            kind = 'g>rhs apply rhs'
        else:
            g[u] = INF
            todo = [v for v, c in succ(E, u)] + [u]
            kind = 'g<rhs invalidate'
        for v in todo:
            if g[v] != rhs(v):
                U.add(v)
            else:
                U.discard(v)
        print('  pop %s key=%s (g,rhs) %s -> %s  [%s]  OPEN=%s' % (
            u, tuple(fmt(k) for k in key(u)) if False else '(%s,%s)' % (fmt(min(before)), fmt(min(before))),
            tuple(fmt(x) for x in before), (fmt(g[u]), fmt(rhs(u))), kind,
            {v: (fmt(g[v]), fmt(rhs(v))) for v in sorted(U)}))
    print('  result g:', {v: fmt(g[v]) for v in sorted(g)})
    return g


if __name__ == '__main__':
    check_h(LECT, H_L, 'lecture graph')
    best_first(LECT, {n: 0 for n in H_L}, label='Dijkstra, lecture graph')
    best_first(LECT, H_L, label='A*, lecture graph')
    g1, p1, open1, closed1 = best_first(LECT, H_L, eps=2, label='Weighted A* / ARA* iteration 1')
    print('   ARA* stored g:', {n: fmt(v) for n, v in g1.items()}, 'OPEN after:', sorted(open1 | {'G'}))
    best_first(LECT, H_L, eps=1, label='ARA* iteration 2 (reuse g, parent; OPEN = old OPEN incl. G)',
               g0=g1, parent0=p1, open0=open1 | {'G'})
    gD = {'S': 0, 'A': 2, 'B': 3, 'C': 5, 'D': 1, 'E': 4, 'G': 8}
    closed = dict(LECT)
    closed[('B', 'C')] = INF
    lpa_repair(closed, gD, 'B->C closed (2 -> inf)')
    cheaper = dict(LECT)
    cheaper[('S', 'B')] = 1
    lpa_repair(cheaper, gD, 'S->B cheaper (6 -> 1)')
    gto = all_pairs_to(LECT)
    print('\nD* Lite cost-to-go g_to:', {n: fmt(v) for n, v in gto.items()})
    gto2 = all_pairs_to(closed)
    print('after B->C closed g_to:', {n: fmt(v) for n, v in gto2.items()})
    print('rhs_to(B) before', min(2 + gto['C'], 1 + gto['E']), 'after', min(INF + 3, 1 + gto2['E']))
    # key modifier example
    print('\nkm example: K_old', (7 + 5 + 0, 7), 'K_new', (7 + 4 + 3, 7), 'no-correction k1', 7 + 4)
    # practice graph
    check_h(PRAC, H_P, 'practice graph')
    best_first(PRAC, {n: 0 for n in H_P}, label='PRACTICE Dijkstra')
    best_first(PRAC, H_P, label='PRACTICE A*')
    best_first(PRAC, H_P, eps=3, label='PRACTICE weighted A*')
    H_bad = dict(H_P)
    H_bad['A'] = 1
    check_h(PRAC, H_bad, 'practice graph with h(A)=1')
    gP = all_pairs_to({(b, a): c for (a, b), c in PRAC.items()}, 'S')
    print('practice forward g:', {n: fmt(v) for n, v in gP.items()})
    cl = dict(PRAC)
    cl[('C', 'D')] = INF
    lpa_repair(cl, gP, 'PRACTICE C->D closed')
    # FSM trace
    print('\nFSM trace')
    seq = [(0, 0, 1), (0, 0, 0), (1, 0, 1), (0, 0, 1), (0, 1, 1)]
    for k, (a, d, r) in enumerate(seq):
        st = 'Hold' if a else ('Arrived' if d else ('FollowRoute' if r else 'Replan'))
        print(' k=%d a=%d d=%d r=%d -> %s' % (k, a, d, r, st))
    print('priority d->a->r variant at k=4 with a=1,d=1:', 'Arrived')
    # hysteresis
    dJ = [0.5, -0.3, 0.6, -0.1, 2.6, 1.1, -0.4, -2.6]
    for delta in (0, 2):
        cur, sw, hist = 'A', 0, []
        for x in dJ:
            if delta == 0:
                new = 'B' if x > 0 else 'A'
            else:
                new = 'B' if (cur == 'A' and x > delta) else ('A' if (cur == 'B' and x < -delta) else cur)
            if new != cur:
                sw += 1
            cur = new
            hist.append(cur)
        print('delta', delta, hist, 'switches', sw)
    dJ2 = [1.0, 2.5, 1.5, -1.0, 3.2, -0.5, -2.5, 0.0]
    for delta in (0, 2):
        cur, sw, hist = 'A', 0, []
        for x in dJ2:
            if delta == 0:
                new = 'B' if x > 0 else ('A' if x < 0 else cur)
            else:
                new = 'B' if (cur == 'A' and x > delta) else ('A' if (cur == 'B' and x < -delta) else cur)
            sw += new != cur
            cur = new
            hist.append(cur)
        print('PRACTICE delta', delta, hist, 'switches', sw)
