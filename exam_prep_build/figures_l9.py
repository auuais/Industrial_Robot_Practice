# -*- coding: utf-8 -*-
"""Figures for the Lecture 9 notes (local trajectory planning). Dark theme, SVG.
    python figures_l9.py            # all
    python figures_l9.py frenet ... # selected (function names without the fig_ prefix)"""
import math
import pathlib
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle, FancyArrowPatch, Polygon, Rectangle

FIG = pathlib.Path(__file__).parent / 'fig'
FIG.mkdir(exist_ok=True)
C = dict(text='#dfe4ec', muted='#a3acbd', gray='#8a94a7', faint='#5d6880', grid='#263044', spine='#3a4560',
         teal='#2dd4bf', blue='#60a5fa', orange='#fb923c', rose='#fb7185', green='#4ade80', amber='#fbbf24',
         violet='#a78bfa', cyan='#22d3ee', node='#1c2230', panel='#161b24')
plt.rcParams.update({'font.family': 'Segoe UI', 'font.size': 8.6, 'text.color': C['text'], 'axes.labelcolor': C['muted'],
                     'axes.edgecolor': C['spine'], 'xtick.color': C['gray'], 'ytick.color': C['gray'],
                     'axes.facecolor': 'none', 'figure.facecolor': 'none', 'savefig.transparent': True,
                     'axes.grid': True, 'grid.color': C['grid'], 'grid.linewidth': 0.6, 'svg.fonttype': 'path',
                     'axes.spines.top': False, 'axes.spines.right': False, 'legend.frameon': False,
                     'mathtext.fontset': 'cm', 'axes.titlesize': 9.2, 'axes.titleweight': 600})
LAT_COL = {-2.0: C['orange'], 0.0: C['violet'], 2.0: C['teal']}
LAT_NAME = {-2.0: 'right 2 m', 0.0: 'path keeping', 2.0: 'left 2 m'}


def save(fig, name):
    fig.savefig(FIG / (name + '.svg'), bbox_inches='tight', pad_inches=0.04)
    plt.close(fig)
    print('  fig', name)


def arrow(ax, p, q, color, lw=1.6, ms=9, z=5, ls='-'):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle='-|>', mutation_scale=ms, color=color, lw=lw, zorder=z,
                                 shrinkA=0, shrinkB=0, linestyle=ls))


def circle_path(R, s):
    th = np.asarray(s) / R
    r = np.stack([R * np.sin(th), R - R * np.cos(th)], -1)
    t = np.stack([np.cos(th), np.sin(th)], -1)
    n = np.stack([-np.sin(th), np.cos(th)], -1)
    return r, t, n


def quintic(d0, v0, a0, dg, T):
    A = np.array([[T ** 3, T ** 4, T ** 5], [3 * T ** 2, 4 * T ** 3, 5 * T ** 4], [6 * T, 12 * T ** 2, 20 * T ** 3]])
    b = np.array([dg - d0 - v0 * T - a0 / 2 * T ** 2, -v0 - a0 * T, -a0])
    return np.polynomial.Polynomial([d0, v0, a0 / 2] + list(np.linalg.solve(A, b)))


def quartic(v0, vT, T):
    b4 = (v0 - vT) / (2 * T ** 3)
    return np.polynomial.Polynomial([0, v0, 0, -2 * b4 * T, b4])


LON = {'decel': quartic(5, 3, 4), 'accel': quartic(5, 7, 4)}
LAT = {dT: quintic(0, 0, 0, dT, 4) for dT in (-2.0, 0.0, 2.0)}


# ------------------------------------------------------------------ 1. overview (hand SVG)
def fig_overview():
    W, H = 780, 250
    o = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d" font-family="Segoe UI">' % (W, H, W, H)]
    o.append('<defs>')
    for nm, col in (('m', C['muted']), ('t', C['teal']), ('o', C['orange']), ('g', C['green'])):
        o.append('<marker id="a%s" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto">'
                 '<path d="M0 0L10 5L0 10z" fill="%s"/></marker>' % (nm, col))
    o.append('</defs>')

    def box(x, y, w, h, title, sub, col, fill=C['node']):
        o.append('<rect x="%d" y="%d" width="%d" height="%d" rx="9" fill="%s" stroke="%s" stroke-width="1.6"/>' % (x, y, w, h, fill, col))
        o.append('<text x="%d" y="%d" text-anchor="middle" style="fill:%s;font-size:13.5px;font-weight:600">%s</text>' % (x + w / 2, y + 22, col, title))
        for k, line in enumerate(sub):
            o.append('<text x="%d" y="%d" text-anchor="middle" style="fill:%s;font-size:11px">%s</text>' % (x + w / 2, y + 40 + 14 * k, C['muted'], line))

    def line(pts, col, mk):
        d = 'M' + ' L'.join('%d %d' % p for p in pts)
        o.append('<path d="%s" fill="none" stroke="%s" stroke-width="1.7" marker-end="url(#a%s)"/>' % (d, col, mk))

    def label(x, y, s, col=C['muted'], size=11, anchor='middle', weight=400, italic=False):
        st = 'font-style:italic;' if italic else ''
        o.append('<text x="%d" y="%d" text-anchor="%s" style="fill:%s;font-size:%spx;font-weight:%s;%s">%s</text>' % (x, y, anchor, col, size, weight, st, s))

    # plan block
    o.append('<rect x="118" y="14" width="430" height="122" rx="12" fill="none" stroke="%s" stroke-width="1.2" stroke-dasharray="5 4"/>' % C['faint'])
    label(130, 31, 'Plan(c, g, π)  —  this lecture', C['teal'], 11.5, 'start', 600)
    box(132, 44, 124, 80, 'Generate', ['candidates 𝒯', 'polynomials, curves,', 'rollouts, E2E, optim.'], C['blue'])
    box(272, 44, 124, 80, 'Evaluate', ['feasible? safe?', 'collision, limits', 'costs J'], C['amber'])
    box(412, 44, 124, 80, 'Select', ['best valid τ*', 'by preference π', 'argmin J'], C['green'])
    line([(256, 84), (270, 84)], C['muted'], 'm')
    line([(396, 84), (410, 84)], C['muted'], 'm')
    # situation
    box(8, 44, 96, 80, 'Situation', ['c: ego, objects,', 'road; goal g'], C['orange'])
    line([(104, 84), (130, 84)], C['orange'], 'o')
    # controller and vehicle
    box(580, 44, 90, 80, 'Controller', ['tracks τ*', '(next lecture)'], C['rose'])
    box(686, 44, 86, 80, 'Vehicle', ['executes', 'only Δt'], C['text'])
    line([(536, 84), (578, 84)], C['teal'], 't')
    label(557, 76, 'τ*', C['teal'], 12, 'middle', 600, True)
    line([(670, 84), (684, 84)], C['muted'], 'm')
    # feedback
    box(560, 170, 212, 56, 'Observation · state estimation', ['new c after Δt'], C['violet'])
    line([(729, 124), (729, 168)], C['muted'], 'm')
    line([(560, 198), (56, 198), (56, 126)], C['green'], 'g')
    label(300, 216, 'repeat every Δt: receding horizon — plan T seconds ahead, execute only the first Δt', C['green'], 11.5, 'middle', 600)
    o.append('</svg>')
    (FIG / 'l9_overview.svg').write_text(''.join(o), encoding='utf-8')
    print('  fig l9_overview')


# ------------------------------------------------------------------ 2. Frenet frame on a curved path
def fig_frenet():
    R = 20.0
    fig, ax = plt.subplots(figsize=(6.2, 4.4))
    s = np.linspace(0, 22, 300)
    for d in (-3, -2, -1, 1, 2, 3):
        r, t, n = circle_path(R, s)
        p = r + d * n
        ax.plot(p[:, 0], p[:, 1], color=C['faint'], lw=0.7, ls=(0, (3, 3)), zorder=1)
    for sk in range(0, 21, 5):
        r, t, n = circle_path(R, sk)
        a, b = r - 3 * n, r + 3 * n
        ax.plot([a[0], b[0]], [a[1], b[1]], color=C['faint'], lw=0.7, zorder=1)
        lab = r - 3.9 * n
        ax.text(lab[0], lab[1], 's = %d' % sk, color=C['gray'], fontsize=7.4, ha='center', va='center')
    r, t, n = circle_path(R, s)
    ax.plot(r[:, 0], r[:, 1], color=C['muted'], lw=2.2, zorder=2)
    ax.text(r[-1, 0] + 0.5, r[-1, 1] - 0.4, 'reference\npath r(s)', color=C['muted'], fontsize=8.6, ha='left', va='top')
    s0 = 10 * math.pi / 3
    r0, t0, n0 = circle_path(R, s0)
    p = r0 + 1.5 * n0
    arrow(ax, tuple(r0), tuple(r0 + 3.6 * t0), C['blue'], 1.8)
    arrow(ax, tuple(r0), tuple(r0 + 3.6 * n0), C['green'], 1.8)
    arrow(ax, tuple(r0), tuple(p), C['orange'], 2.2, z=6)
    ax.plot(*r0, 'o', color=C['text'], ms=4.5, zorder=7)
    ax.plot(*p, 'o', color=C['orange'], ms=6, zorder=7)
    ax.text(*(r0 + 3.7 * t0 + np.array([0.25, -0.35])), r'$\mathbf{t}(s)$', color=C['blue'], fontsize=11.5)
    ax.text(*(r0 + 3.7 * n0 + np.array([-0.4, 0.35])), r'$\mathbf{n}(s)$', color=C['green'], fontsize=11.5)
    ax.text(*(p + np.array([-5.4, -0.2])), r'$\mathbf{p}=\mathbf{r}(s)+d\,\mathbf{n}(s)$', color=C['orange'], fontsize=10.5)
    ax.text(*(r0 + np.array([0.7, -1.1])), r'$\mathbf{r}(s)$', color=C['text'], fontsize=10.5)
    ax.text(10.6, -1.9, 'Frenet grid: solid = constant s,\ndashed = constant d (every 1 m)\nd > 0 left of the path, d < 0 right',
            color=C['gray'], fontsize=7.8, va='top')
    ax.plot(0, 0, 'o', color=C['text'], ms=3.5)
    ax.set_aspect('equal')
    ax.set_xlim(-1, 21)
    ax.set_ylim(-5, 12)
    ax.set_xlabel('x [m]')
    ax.set_ylabel('y [m]')
    ax.set_title('Frenet frame on a left curve (R = 20 m): s = 10.47 m, d = 1.5 m', loc='left')
    save(fig, 'l9_frenet')


# ------------------------------------------------------------------ 3. projection
def fig_projection():
    fig, axs = plt.subplots(1, 2, figsize=(6.8, 3.2), gridspec_kw=dict(wspace=0.28))
    ax = axs[0]
    t = np.array([math.cos(math.pi / 6), math.sin(math.pi / 6)])
    n = np.array([-t[1], t[0]])
    ax.plot([-1 * t[0], 13 * t[0]], [-1 * t[1], 13 * t[1]], color=C['muted'], lw=2)
    p = np.array([8.0, 6.0])
    s = p @ t
    f = s * t
    ax.plot([f[0], p[0]], [f[1], p[1]], color=C['orange'], lw=1.5, ls='--')
    ax.plot(*p, 'o', color=C['orange'], ms=6)
    ax.plot(*f, 'o', color=C['text'], ms=4.5)
    ax.plot(0, 0, 'o', color=C['text'], ms=3.5)
    sq = 0.45
    corner = [f + sq * t, f + sq * t + sq * n, f + sq * n]
    ax.plot([c[0] for c in corner], [c[1] for c in corner], color=C['gray'], lw=0.8)
    ax.text(*(p + np.array([-3.4, 0.55])), 'p = (8, 6)', color=C['orange'], fontsize=8.6)
    ax.text(*(f + np.array([0.45, -0.9])), r'$\mathbf{r}(s^*)$', color=C['text'], fontsize=10)
    ax.text(3.0, 0.4, r'$s^* = \mathbf{p}^T\mathbf{t} = 9.93$', color=C['blue'], fontsize=9.5, rotation=30)
    ax.text(8.2, 7.25, r'$d = \mathbf{p}^T\mathbf{n} = 1.20$', color=C['orange'], fontsize=9.5, ha='center')
    ax.set_aspect('equal')
    ax.set_xlim(-1.5, 12.5)
    ax.set_ylim(-1.5, 8.5)
    ax.set_title('(a) straight path at 30°', loc='left')
    ax = axs[1]
    R = 20.0
    s_ = np.linspace(-2, 34, 300)
    r, _, _ = circle_path(R, s_)
    ax.plot(r[:, 0], r[:, 1], color=C['muted'], lw=2)
    cc = np.array([0.0, R])
    p = np.array([12.0, 6.0])
    u = (p - cc) / np.linalg.norm(p - cc)
    rs = cc + R * u
    ax.plot([cc[0], rs[0]], [cc[1], rs[1]], color=C['faint'], lw=0.9, ls=':')
    ax.plot([p[0], rs[0]], [p[1], rs[1]], color=C['orange'], lw=1.6, ls='--')
    ax.plot(*p, 'o', color=C['orange'], ms=6)
    ax.plot(*rs, 'o', color=C['text'], ms=4.5)
    ax.plot(*cc, 'o', color=C['rose'], ms=5)
    ax.text(p[0] - 7.4, p[1] + 0.9, 'p = (12, 6)', color=C['orange'], fontsize=8.6)
    ax.text(14.6, 1.4, r'$s^* = 14.17$' + '\n' + r'$d = 1.56$', color=C['text'], fontsize=9)
    ax.text(cc[0] + 0.8, cc[1] - 0.6, 'centre of curvature:\nevery path point is\nequally near → s* undefined',
            color=C['rose'], fontsize=7.8, va='top')
    ax.set_aspect('equal')
    ax.set_xlim(-2, 22)
    ax.set_ylim(-1.5, 22)
    ax.set_title('(b) circle R = 20 m: project along the radius', loc='left')
    save(fig, 'l9_projection')


# ------------------------------------------------------------------ 4. quintic profiles
def fig_quintic():
    a = quintic(0, 0, 0, 2, 4)
    b = quintic(0.5, 0.4, -0.2, 0.0, 3.0)
    fig, axs = plt.subplots(3, 1, figsize=(6.6, 4.25), sharex=True, gridspec_kw=dict(hspace=0.22))
    ta, tb = np.linspace(0, 4, 300), np.linspace(0, 3, 300)
    names = [r'$d$ [m]', r'$\dot d$ [m/s]', r'$\ddot d$ [m/s²]']
    for k, ax in enumerate(axs):
        pa, pb = a.deriv(k) if k else a, b.deriv(k) if k else b
        ax.plot(ta, pa(ta), color=C['teal'], lw=2, label=r'$d_0=\dot d_0=\ddot d_0=0,\ d_{goal}=2,\ T=4$')
        ax.plot(tb, pb(tb), color=C['orange'], lw=1.8, ls='--',
                label=r'$d_0=0.5,\ \dot d_0=0.4,\ \ddot d_0=-0.2,\ d_{goal}=0,\ T=3$')
        for (pp, T_) in ((pa, 4.0), (pb, 3.0)):
            ax.plot([0, T_], [pp(0), pp(T_)], 'o', color=C['text'], ms=3.6, zorder=5)
        ax.set_ylabel(names[k])
        ax.axhline(0, color=C['spine'], lw=0.8)
    axs[0].legend(loc='upper left', fontsize=7.6)
    axs[1].annotate('peak 0.94 m/s at T/2', xy=(2, 0.9375), xytext=(2.62, 0.22), color=C['teal'], fontsize=7.8,
                    arrowprops=dict(arrowstyle='-', color=C['teal'], lw=0.7))
    axs[2].annotate('peak 0.72 m/s² at t = 0.85 s', xy=(0.845, 0.7217), xytext=(4.12, 0.56), color=C['teal'], fontsize=7.8, ha='right',
                    arrowprops=dict(arrowstyle='-', color=C['teal'], lw=0.7))
    axs[2].set_xlabel('t [s]')
    axs[0].set_title('Quintic lateral plans: the 6 boundary conditions are the dots (value, slope, curvature at both ends)', loc='left')
    save(fig, 'l9_quintic')


# ------------------------------------------------------------------ 5. candidates (slide 10 rebuilt)
def fig_candidates():
    fig = plt.figure(figsize=(6.9, 3.5))
    gs = fig.add_gridspec(2, 2, width_ratios=[1, 1.55], hspace=0.55, wspace=0.25)
    t = np.linspace(0, 4, 200)
    tk = np.arange(0, 5)
    ax = fig.add_subplot(gs[0, 0])
    for name, ls in (('decel', '--'), ('accel', '-')):
        ax.plot(t, LON[name](t), color=C['blue'], ls=ls, lw=1.6, label='%s (v: 5 → %d m/s)' % (name, 3 if name == 'decel' else 7))
        ax.plot(tk, LON[name](tk), 'o' if name == 'decel' else 's', color=C['blue'], ms=3)
    ax.set_title('2 longitudinal plans s(t)', loc='left')
    ax.set_ylabel('s [m]')
    ax.legend(fontsize=7, loc='upper left')
    ax = fig.add_subplot(gs[1, 0])
    for dT, pl in LAT.items():
        ax.plot(t, pl(t), color=LAT_COL[dT], lw=1.6, label=LAT_NAME[dT])
    ax.set_title('3 lateral plans d(t)', loc='left')
    ax.set_ylabel('d [m]')
    ax.set_xlabel('t [s]')
    ax.legend(fontsize=7, loc='lower left', ncol=1)
    ax = fig.add_subplot(gs[:, 1])
    for name, ls, mk in (('decel', '--', 'o'), ('accel', '-', 's')):
        for dT, pl in LAT.items():
            ax.plot(LON[name](t), pl(t), color=LAT_COL[dT], ls=ls, lw=1.7 if name == 'accel' else 1.3)
            ax.plot(LON[name](tk), pl(tk), mk, color=LAT_COL[dT], ms=3.4, mfc='none' if name == 'decel' else LAT_COL[dT])
    ax.plot(0, 0, 'o', color=C['text'], ms=4)
    ax.text(15.6, 2.38, 'decel ends at s = 16', color=C['gray'], fontsize=7.4, ha='right')
    ax.text(24.6, 2.38, 'accel: s = 24', color=C['gray'], fontsize=7.4, ha='right')
    ax.set_ylim(-2.6, 2.7)
    ax.set_xlabel('s [m]   (markers every 1 s)')
    ax.set_ylabel('d [m]')
    ax.set_title('6 candidates (s_i(t), d_j(t)) in the Frenet plane', loc='left')
    save(fig, 'l9_candidates')


# ------------------------------------------------------------------ 6. candidates on a curved road + obstacle
def fig_cartesian():
    R = 40.0
    obs_s, obs_d = 13.0, 1.0
    ro, to, no = circle_path(R, obs_s)
    obs = ro + obs_d * no
    fig, ax = plt.subplots(figsize=(6.8, 3.3))
    s = np.linspace(-2, 27, 300)
    r, tt_, n = circle_path(R, s)
    for d, ls, col, lw in ((3.5, '-', C['spine'], 1.4), (-3.5, '-', C['spine'], 1.4), (0, '-', C['muted'], 1.6)):
        p = r + d * n
        ax.plot(p[:, 0], p[:, 1], color=col, lw=lw, ls=ls, zorder=1)
    t = np.linspace(0, 4, 200)
    passed = {(-2.0, 'decel'), (-2.0, 'accel')}
    for name, ls in (('decel', '--'), ('accel', '-')):
        for dT, pl in LAT.items():
            ss, dd = LON[name](t), pl(t)
            rr, _, nn = circle_path(R, ss)
            p = rr + dd[:, None] * nn
            ok = (dT, name) in passed
            ax.plot(p[:, 0], p[:, 1], color=LAT_COL[dT] if ok else C['rose'], ls=ls, lw=1.8 if ok else 1.1,
                    alpha=1 if ok else 0.55, zorder=3 if ok else 2)
    ax.add_patch(Circle(tuple(obs), 0.5, color=C['text'], zorder=5))
    ax.add_patch(Circle(tuple(obs), 1.8715, fill=False, ec=C['rose'], lw=0.9, ls=':', zorder=4))
    ax.annotate('obstacle, r = 0.5 m\n(dotted: check radius 1.87 m)', xy=(obs[0] - 0.4, obs[1] + 0.3), xytext=(3.5, 7.6),
                color=C['rose'], fontsize=7.6, ha='center', arrowprops=dict(arrowstyle='-', color=C['rose'], lw=0.7))
    ax.plot(0, 0, 'o', color=C['text'], ms=4, zorder=6)
    ax.text(0.3, -1.4, 'ego', color=C['text'], fontsize=8)
    ax.set_aspect('equal')
    ax.set_xlim(-1.5, 25)
    ax.set_ylim(-4.5, 10.5)
    ax.set_xlabel('x [m]')
    ax.set_ylabel('y [m]')
    ax.set_title('The same 6 candidates mapped to x–y along a left curve (R = 40 m): 4 collide, 2 pass', loc='left')
    save(fig, 'l9_cartesian')


# ------------------------------------------------------------------ 7. inner / outer arcs
def fig_inner_outer():
    R = 20.0
    fig, ax = plt.subplots(figsize=(4.6, 3.1))
    s = np.linspace(0, 10, 100)
    for d, col, lab in ((1.5, C['teal'], 'd = +1.5 (inside): 9.25 m'), (0, C['muted'], 'reference: Δs = 10 m'),
                        (-1.5, C['orange'], 'd = −1.5 (outside): 10.75 m')):
        r, t, n = circle_path(R, s)
        p = r + d * n
        ax.plot(p[:, 0], p[:, 1], color=col, lw=2.2, label=lab)
    for sk in (0, 10):
        r, t, n = circle_path(R, sk)
        a, b = r - 2.2 * n, r + 2.2 * n
        ax.plot([a[0], b[0]], [a[1], b[1]], color=C['faint'], lw=0.9)
    ax.legend(fontsize=7.8, loc='upper left')
    ax.set_aspect('equal')
    ax.set_xlim(-1, 12)
    ax.set_ylim(-2.5, 6.5)
    ax.set_title('Same Δs, different distance travelled: (1 − κd)Δs', loc='left')
    save(fig, 'l9_inner_outer')


# ------------------------------------------------------------------ 8. limits
def fig_limits():
    amax, kmax = 3.0, 0.2
    vs = math.sqrt(amax / kmax)
    v = np.linspace(0.01, 12, 400)
    lim = np.minimum(kmax, amax / v ** 2)
    fig, ax = plt.subplots(figsize=(5.4, 3.0))
    ax.fill_between(v, 0, lim, color=C['blue'], alpha=0.14, lw=0)
    ax.plot(v, lim, color=C['blue'], lw=2)
    ax.axvline(vs, color=C['faint'], ls='--', lw=0.9)
    ax.text(vs + 0.15, 0.205, r'$v^* = \sqrt{a_{\perp,max}/\kappa_{max}} = 3.87$ m/s', color=C['muted'], fontsize=8.2)
    ax.text(1.0, 0.1, 'allowed', color=C['blue'], fontsize=9)
    ax.text(0.3, 0.178, r'$\kappa_{max} = 0.2$ (steering limit)', color=C['muted'], fontsize=7.8)
    ax.text(6.4, 0.105, r'$|\kappa| \leq a_{\perp,max}/v^2$  ($a_{\perp,max}$ = 3 m/s²)', color=C['muted'], fontsize=7.8)
    ax.plot(9.2635, 0.05157, 'x', color=C['rose'], ms=8, mew=2)
    ax.text(8.6, 0.066, 'example candidate\nv = 9.26, κ = 0.052 → rejected', color=C['rose'], fontsize=7.6)
    ax.plot(7.627, 0.05157, 'o', color=C['green'], ms=4.5)
    ax.text(6.9, 0.028, 'feasible up to 7.63 m/s', color=C['green'], fontsize=7.6, ha='center')
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 0.235)
    ax.set_xlabel('speed v [m/s]')
    ax.set_ylabel(r'curvature $|\kappa_p|$ [1/m]')
    save(fig, 'l9_limits')


# ------------------------------------------------------------------ 9. circles
def fig_circles():
    L, Wd = 4.5, 1.8
    rk = math.hypot(L / 6, Wd / 2)
    fig, axs = plt.subplots(1, 2, figsize=(6.9, 2.7), gridspec_kw=dict(width_ratios=[1, 1.25], wspace=0.15))
    ax = axs[0]
    ax.add_patch(Rectangle((-L / 2, -Wd / 2), L, Wd, fill=True, fc='#22314a', ec=C['blue'], lw=1.6))
    for off in (-1.5, 0, 1.5):
        ax.add_patch(Circle((off, 0), rk, fill=False, ec=C['teal'], lw=1.3))
        ax.plot(off, 0, 'o', color=C['teal'], ms=3)
        ax.plot([off - 0.75, off - 0.75], [-Wd / 2, Wd / 2], color=C['faint'], lw=0.6, ls=':')
    ax.plot([1.5, 2.25], [0, 0.9], color=C['amber'], lw=1.4)
    ax.plot([1.5, 2.25], [0, 0], color=C['amber'], lw=0.9, ls='--')
    ax.plot([2.25, 2.25], [0, 0.9], color=C['amber'], lw=0.9, ls='--')
    ax.text(1.95, -0.3, '0.75', color=C['amber'], fontsize=7.6, ha='center')
    ax.text(2.4, 0.38, '0.9', color=C['amber'], fontsize=7.6)
    ax.text(0.0, 1.45, r'$r_k=\sqrt{0.75^2+0.9^2}=1.17$ m', color=C['amber'], fontsize=8.6, ha='center')
    ax.text(0, -1.55, '4.5 × 1.8 m body, centres at −1.5, 0, +1.5 m', color=C['gray'], fontsize=7.6, ha='center')
    ax.set_aspect('equal')
    ax.set_xlim(-3.6, 3.6)
    ax.set_ylim(-1.9, 1.85)
    ax.axis('off')
    ax = axs[1]
    cc, hd = np.array([10.0, 0.5]), math.radians(10)
    u = np.array([math.cos(hd), math.sin(hd)])
    v_ = np.array([-u[1], u[0]])
    corners = [cc + a * u * L / 2 + b * v_ * Wd / 2 for a, b in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    ax.add_patch(Polygon(corners, closed=True, fc='#22314a', ec=C['blue'], lw=1.4))
    o = np.array([12.5, 1.6])
    ax.add_patch(Circle(tuple(o), 0.5, color=C['text']))
    ax.add_patch(Circle(tuple(o), rk + 0.5 + 0.2, fill=False, ec=C['rose'], lw=1, ls=':'))
    for off, dist in ((-1.5, 4.20), (0, 2.73), (1.5, 1.32)):
        ck = cc + off * u
        bad = dist <= 1.8715
        ax.add_patch(Circle(tuple(ck), rk, fill=False, ec=C['rose'] if bad else C['teal'], lw=1.2))
        ax.plot([ck[0], o[0]], [ck[1], o[1]], color=C['rose'] if bad else C['faint'], lw=0.9, ls='--')
        ax.text(ck[0] - 0.05, ck[1] - 0.42, '%.2f' % dist, color=C['rose'] if bad else C['gray'], fontsize=7.6, ha='center')
    ax.text(o[0] + 0.7, o[1] + 0.8, 'obstacle', color=C['text'], fontsize=7.8)
    ax.text(10.0, -1.75, 'front circle: 1.32 ≤ 1.17 + 0.5 + 0.2 = 1.87 → collision', color=C['rose'], fontsize=7.8, ha='center')
    ax.set_aspect('equal')
    ax.set_xlim(7.0, 14.8)
    ax.set_ylim(-2.2, 3.7)
    ax.axis('off')
    save(fig, 'l9_circles')


# ------------------------------------------------------------------ 10. tunnelling
def fig_tunnel():
    fig, axs = plt.subplots(2, 1, figsize=(6.4, 2.6), sharex=True, gridspec_kw=dict(hspace=0.35))
    o, zone, e = np.array([10.0, 1.0]), 1.8715, 0.0
    for ax, dt, ttl in ((axs[0], 0.5, 'checks every 0.5 s at 8 m/s: 4 m apart — the collision falls between two checks'),
                        (axs[1], 0.1, 'checks every 0.1 s: 0.8 m apart — caught')):
        ax.add_patch(Circle(tuple(o), zone, fc=C['rose'], alpha=0.13, ec=C['rose'], lw=0.9, ls=':'))
        ax.add_patch(Circle(tuple(o), 0.5, color=C['text']))
        ax.plot([0, 20], [1.0, 1.0], color=C['faint'], lw=1, ls='--')
        xs = np.arange(0, 16.01, 8 * dt) + 3.9
        for x in xs:
            hit = abs(x - o[0]) <= zone
            ax.plot(x, 1.0, 'o', color=C['rose'] if hit else C['teal'], ms=4.5 if hit else 3.6, zorder=5)
        ax.set_aspect('equal')
        ax.set_ylim(-1.2, 3.2)
        ax.set_xlim(0, 20)
        ax.set_yticks([])
        ax.set_title(ttl, loc='left', fontsize=8.6)
    axs[1].set_xlabel('x [m]  (dots: sampled positions of a circle centre)')
    save(fig, 'l9_tunnel')


# ------------------------------------------------------------------ 11. costs
def fig_costs():
    data = [('decel', -2, 3.5625, 1.7227, 1.0), ('decel', 0, 0.75, 1.7943, 0.0), ('decel', 2, 3.5625, 1.7227, 1.0),
            ('accel', -2, 3.5625, 0.1942, 1.0), ('accel', 0, 0.75, 0.1943, 0.0), ('accel', 2, 3.5625, 0.1942, 1.0)]
    fig, ax = plt.subplots(figsize=(6.4, 2.9))
    x = np.arange(len(data))
    labels = []
    for i, (lk, dT, jj, jv, jd) in enumerate(data):
        ok = dT == -2
        al = 1 if ok else 0.35
        ax.bar(i, jj, color=C['violet'], alpha=al, width=0.62, label='jerk  J_j/S_j' if i == 0 else None)
        ax.bar(i, jv, bottom=jj, color=C['amber'], alpha=al, width=0.62, label='speed  J_v/S_v' if i == 0 else None)
        ax.bar(i, jd, bottom=jj + jv, color=C['cyan'], alpha=al, width=0.62, label='lateral  J_d/S_d' if i == 0 else None)
        tot = jj + jv + jd
        ax.text(i, tot + 0.12, '%.2f' % tot, ha='center', color=C['text'] if ok else C['faint'], fontsize=8, fontweight=600)
        if not ok:
            ax.text(i, tot + 0.62, 'collision', ha='center', color=C['rose'], fontsize=7.4)
        labels.append('%s\n%s' % (lk, {-2: 'right 2 m', 0: 'keep', 2: 'left 2 m'}[dT]))
    ax.annotate('selected τ*', xy=(3, 4.85), xytext=(3.75, 6.1), color=C['green'], fontsize=8.4, fontweight=600,
                arrowprops=dict(arrowstyle='-|>', color=C['green'], lw=1))
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=7.6)
    ax.set_ylim(0, 7.3)
    ax.set_ylabel('normalized cost')
    ax.legend(fontsize=7.4, loc='lower center', bbox_to_anchor=(0.5, 1.0), ncol=3)
    ax.grid(axis='x', visible=False)
    save(fig, 'l9_costs')


# ------------------------------------------------------------------ 12. curves
def bspline(P, k=3, num=400):
    """Uniform clamped cubic B-spline by de Boor."""
    P = np.asarray(P, float)
    n = len(P) - 1
    knots = np.concatenate([np.zeros(k), np.linspace(0, 1, n - k + 2), np.ones(k)])
    us = np.linspace(0, 1 - 1e-9, num)
    out = []
    for u in us:
        j = np.searchsorted(knots, u, side='right') - 1
        j = min(max(j, k), n)
        d = [P[i].copy() for i in range(j - k, j + 1)]
        for r in range(1, k + 1):
            for i in range(k, r - 1, -1):
                a = (u - knots[i + j - k]) / (knots[i + 1 + j - r] - knots[i + j - k])
                d[i] = (1 - a) * d[i - 1] + a * d[i]
        out.append(d[k])
    return np.array(out), knots


def fig_curves():
    fig, axs = plt.subplots(1, 2, figsize=(6.9, 2.7), gridspec_kw=dict(wspace=0.18))
    ax = axs[0]
    P = np.array([[0, 0], [4, 0], [8, 2], [12, 2]], float)
    u = np.linspace(0, 1, 200)[:, None]
    S = (1 - u) ** 3 * P[0] + 3 * u * (1 - u) ** 2 * P[1] + 3 * u ** 2 * (1 - u) * P[2] + u ** 3 * P[3]
    ax.plot(P[:, 0], P[:, 1], color=C['orange'], lw=0.9, ls='--', marker='o', ms=4.5)
    ax.plot(S[:, 0], S[:, 1], color=C['teal'], lw=2.2)
    for uu in (0.25, 0.5, 0.75):
        q = (1 - uu) ** 3 * P[0] + 3 * uu * (1 - uu) ** 2 * P[1] + 3 * uu ** 2 * (1 - uu) * P[2] + uu ** 3 * P[3]
        ax.plot(*q, 'o', color=C['text'], ms=3.4)
    ax.text(5.6, 1.35, 'S(0.5) = (6, 1)', color=C['text'], fontsize=7.6, ha='right')
    for i, (pnt, dy) in enumerate(zip(P, (0.3, -0.75, 0.3, 0.3))):
        ax.text(pnt[0], pnt[1] + dy, r'$\mathbf{P}_%d$' % i, color=C['orange'], fontsize=9.5, ha='center')
    ax.set_title('Cubic Bézier: passes through P0, P3 only', loc='left')
    ax.set_aspect('equal')
    ax.set_ylim(-1, 3.2)
    ax.set_xlim(-0.8, 13)
    ax = axs[1]
    Q = np.array([[0, 0], [2, 0], [4, 0.2], [6, 1.6], [8, 2], [10, 2], [12, 2]], float)
    Sb, knots = bspline(Q)
    Q2 = Q.copy()
    Q2[5] = [10, 3.2]
    Sb2, _ = bspline(Q2)
    ax.plot(Q[:, 0], Q[:, 1], color=C['orange'], lw=0.8, ls='--', marker='o', ms=4)
    ax.plot(Sb[:, 0], Sb[:, 1], color=C['teal'], lw=2.2, label='B-spline')
    ax.plot(Sb2[:, 0], Sb2[:, 1], color=C['amber'], lw=1.5, ls='-.', label='after moving P5')
    ax.plot(*Q2[5], 'o', color=C['amber'], ms=5)
    joints = knots[3:-3]
    for kv in joints[1:-1]:
        idx = int(kv * (len(Sb) - 1))
        ax.plot(*Sb[idx], 'D', color=C['green'], ms=4)
    ax.text(12.6, -0.85, 'green diamonds: segment joints\nmoving P5 changes only the nearby part', color=C['gray'], fontsize=7.2,
            ha='right', va='bottom')
    ax.legend(fontsize=7.4, loc='upper left')
    ax.set_title('Cubic B-spline: many cubic pieces, local control', loc='left')
    ax.set_aspect('equal')
    ax.set_ylim(-1, 3.9)
    ax.set_xlim(-0.8, 13)
    save(fig, 'l9_curves')


# ------------------------------------------------------------------ 13. closed-loop rollout
def fig_rollout():
    fig, axs = plt.subplots(1, 2, figsize=(6.8, 2.6), gridspec_kw=dict(wspace=0.28))
    ax = axs[0]
    k = np.arange(0, 7)
    for r in (-2, 0, 2):
        y = [0.0]
        for _ in k[1:]:
            y.append(y[-1] + 0.5 * 1.0 * (r - y[-1]))
        ax.plot(k * 0.5, y, '-o', color=LAT_COL[float(r)], ms=3.6, lw=1.6, label='target r = %+d m' % r)
        ax.axhline(r, color=LAT_COL[float(r)], lw=0.6, ls=':')
    ax.set_xlabel('t [s]  (Δt = 0.5 s)')
    ax.set_ylabel('lateral offset y [m]')
    ax.set_title(r'Rollouts: $u_k = K(r - y_k)$, K = 1/s', loc='left')
    ax.legend(fontsize=7.2, loc='lower right', bbox_to_anchor=(1.0, 0.16))
    ax = axs[1]
    for K, col, lab in ((0.8, C['teal'], 'KΔt = 0.4: smooth'), (3.0, C['amber'], 'KΔt = 1.5: overshoots'),
                        (4.5, C['rose'], 'KΔt = 2.25: unstable')):
        y = [0.0]
        nk = 4 if K > 4 else 6
        for _ in range(nk):
            y.append(y[-1] + 0.5 * K * (3 - y[-1]))
        ax.plot(np.arange(nk + 1) * 0.5, y, '-o', color=col, ms=3.4, lw=1.5, label=lab)
    ax.axhline(3, color=C['muted'], lw=0.7, ls=':')
    ax.set_ylim(-6, 10)
    ax.set_xlabel('t [s]')
    ax.set_title('Target r = 3: the gain decides the shape', loc='left')
    ax.legend(fontsize=7.2, loc='upper right')
    save(fig, 'l9_rollout')


# ------------------------------------------------------------------ 14. penalty optimisation
def fig_penalty():
    fig, axs = plt.subplots(1, 2, figsize=(6.8, 2.6), gridspec_kw=dict(wspace=0.3))
    ax = axs[0]
    y = np.linspace(-0.5, 3, 400)
    J = y ** 2 + 10 * np.maximum(0, 2 - y) ** 2
    ax.plot(y, J, color=C['blue'], lw=2)
    ax.axvspan(2, 3, color=C['green'], alpha=0.08, lw=0)
    ax.text(2.06, 34, 'safe: y ≥ 2', color=C['green'], fontsize=7.8)
    it = [0.0, 1.6, 1.792, 1.815, 1.8178]
    for k_, yy in enumerate(it):
        ax.plot(yy, yy ** 2 + 10 * max(0, 2 - yy) ** 2, 'o', color=C['amber'], ms=4)
        if k_ < 3:
            ax.text(yy + 0.04, yy ** 2 + 10 * max(0, 2 - yy) ** 2 + 2.0, 'y%d' % k_, color=C['amber'], fontsize=7.6)
    ax.annotate('y* = 1.818', xy=(1.818, 3.636), xytext=(0.6, 14), color=C['text'], fontsize=8,
                arrowprops=dict(arrowstyle='-', color=C['muted'], lw=0.7))
    ax.set_xlabel('waypoint offset y [m]')
    ax.set_ylabel('J(y)')
    ax.set_ylim(0, 45)
    ax.set_title(r'$J = y^2 + 10\,\max(0, 2-y)^2$, gradient steps', loc='left')
    ax = axs[1]
    mu = np.logspace(0, 3, 100)
    ax.semilogx(mu, 2 * mu / (1 + mu), color=C['teal'], lw=2)
    ax.axhline(2, color=C['green'], lw=0.8, ls='--')
    for m_ in (1, 10, 100, 1000):
        ax.plot(m_, 2 * m_ / (1 + m_), 'o', color=C['text'], ms=3.6)
        ax.text(m_ * 1.15, 2 * m_ / (1 + m_) - 0.12, '%.3f' % (2 * m_ / (1 + m_)), color=C['gray'], fontsize=7.4)
    ax.set_xlabel('penalty weight μ')
    ax.set_ylabel('optimal y*')
    ax.set_ylim(0.9, 2.15)
    ax.set_title('Constraint met only as μ → ∞', loc='left')
    save(fig, 'l9_penalty')


# ------------------------------------------------------------------ 15. receding horizon
def fig_receding():
    fig, ax = plt.subplots(figsize=(6.6, 2.5))
    T, dt = 4.0, 0.5
    for k in range(5):
        t0 = k * dt
        y = 4 - k
        ax.add_patch(Rectangle((t0, y - 0.28), T, 0.56, fc=C['blue'], alpha=0.16, ec=C['blue'], lw=0.8))
        ax.add_patch(Rectangle((t0, y - 0.28), dt, 0.56, fc=C['green'], alpha=0.85, ec='none'))
        ax.text(t0 - 0.08, y, 'plan %d' % (k + 1), ha='right', va='center', color=C['muted'], fontsize=7.8)
    ax.text(2.6, 4.48, 'planned horizon T = 4 s (mostly thrown away)', color=C['blue'], fontsize=7.8)
    ax.text(0.05, -0.75, 'green: the only part executed (Δt) before the next plan starts from the new state',
            color=C['green'], fontsize=7.8)
    ax.set_xlim(-0.9, 6.7)
    ax.set_ylim(-1.1, 4.8)
    ax.set_yticks([])
    ax.set_xlabel('time [s]')
    ax.grid(axis='y', visible=False)
    save(fig, 'l9_receding')


ALL = [fig_overview, fig_frenet, fig_projection, fig_quintic, fig_candidates, fig_cartesian, fig_inner_outer,
       fig_limits, fig_circles, fig_tunnel, fig_costs, fig_curves, fig_rollout, fig_penalty, fig_receding]

if __name__ == '__main__':
    want = sys.argv[1:]
    for f in ALL:
        if not want or f.__name__[4:] in want:
            f()
