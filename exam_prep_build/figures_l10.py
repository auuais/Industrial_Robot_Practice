# -*- coding: utf-8 -*-
"""Figures for the Lecture 10 notes (tracking control). Dark theme, SVG.
    python figures_l10.py            # all
    python figures_l10.py pp_response kanayama ...   (function names without the fig_ prefix)"""
import math
import pathlib
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Arc, FancyArrowPatch, Polygon

FIG = pathlib.Path(__file__).parent / 'fig'
FIG.mkdir(exist_ok=True)
C = dict(text='#dfe4ec', muted='#a3acbd', gray='#8a94a7', faint='#5d6880', grid='#263044', spine='#3a4560',
         teal='#2dd4bf', blue='#60a5fa', orange='#fb923c', rose='#fb7185', green='#4ade80', amber='#fbbf24',
         violet='#a78bfa', cyan='#22d3ee', node='#1c2230')
plt.rcParams.update({'font.family': 'Segoe UI', 'font.size': 8.6, 'text.color': C['text'], 'axes.labelcolor': C['muted'],
                     'axes.edgecolor': C['spine'], 'xtick.color': C['gray'], 'ytick.color': C['gray'],
                     'axes.facecolor': 'none', 'figure.facecolor': 'none', 'savefig.transparent': True,
                     'axes.grid': True, 'grid.color': C['grid'], 'grid.linewidth': 0.6, 'svg.fonttype': 'path',
                     'axes.spines.top': False, 'axes.spines.right': False, 'legend.frameon': False,
                     'mathtext.fontset': 'cm', 'axes.titlesize': 9.2, 'axes.titleweight': 600})
L = 2.7
DMAX = math.radians(35)


def save(fig, name):
    fig.savefig(FIG / (name + '.svg'), bbox_inches='tight', pad_inches=0.04)
    plt.close(fig)
    print('  fig', name)


def arrow(ax, p, q, color, lw=1.6, ms=9, z=5):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle='-|>', mutation_scale=ms, color=color, lw=lw, zorder=z,
                                 shrinkA=0, shrinkB=0))


def car(ax, x, y, psi, color, length=2.7, width=1.2, alpha=0.9):
    """Rectangle for a car whose rear-axle centre is (x, y)."""
    c, s = math.cos(psi), math.sin(psi)
    pts = [(-0.6, -width / 2), (length + 0.9, -width / 2), (length + 0.9, width / 2), (-0.6, width / 2)]
    poly = [(x + c * px - s * py, y + s * px + c * py) for px, py in pts]
    ax.add_patch(Polygon(poly, closed=True, fc=color, ec=color, alpha=alpha * 0.35, lw=1.2, zorder=4))
    ax.plot(x, y, 'o', color=color, ms=4, zorder=6)


def pose(ax, x, y, psi, color, size=0.42, z=6):
    """Small arrowhead for a pose (rear-axle point + heading); not to scale."""
    c, s = math.cos(psi), math.sin(psi)
    pts = [(size * 1.9, 0), (-size * 0.5, size * 0.8), (0, 0), (-size * 0.5, -size * 0.8)]
    poly = [(x + c * px - s * py, y + s * px + c * py) for px, py in pts]
    ax.add_patch(Polygon(poly, closed=True, fc=color, ec=color, alpha=0.95, lw=1, zorder=z))
    ax.plot(x, y, 'o', color=color, ms=4.5, zorder=z + 1)


# ------------------------------------------------------------------ 1. overview (hand SVG)
def fig_overview():
    W, H = 780, 230
    o = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d" font-family="Segoe UI">' % (W, H, W, H),
         '<defs>']
    for nm, col in (('m', C['muted']), ('t', C['teal']), ('o', C['orange']), ('g', C['green']), ('b', C['blue'])):
        o.append('<marker id="a%s" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto">'
                 '<path d="M0 0L10 5L0 10z" fill="%s"/></marker>' % (nm, col))
    o.append('</defs>')

    def box(x, y, w, h, title, sub, col):
        o.append('<rect x="%d" y="%d" width="%d" height="%d" rx="9" fill="%s" stroke="%s" stroke-width="1.6"/>' % (x, y, w, h, C['node'], col))
        o.append('<text x="%d" y="%d" text-anchor="middle" style="fill:%s;font-size:13px;font-weight:600">%s</text>' % (x + w / 2, y + 21, col, title))
        for k, line in enumerate(sub):
            o.append('<text x="%d" y="%d" text-anchor="middle" style="fill:%s;font-size:10.8px">%s</text>' % (x + w / 2, y + 38 + 14 * k, C['muted'], line))

    def line(pts, col, mk):
        o.append('<path d="M%s" fill="none" stroke="%s" stroke-width="1.7" marker-end="url(#a%s)"/>' % (
            ' L'.join('%d %d' % p for p in pts), col, mk))

    def label(x, y, s, col=C['muted'], size=11, anchor='middle', weight=400):
        o.append('<text x="%d" y="%d" text-anchor="%s" style="fill:%s;font-size:%spx;font-weight:%s">%s</text>' % (x, y, anchor, col, size, weight, s))

    box(8, 70, 118, 70, 'Reference', ['path p_r(s) or', 'trajectory q_r(t)', 'from the planner'], C['orange'])
    box(176, 10, 196, 74, 'Lateral control', ['Pure Pursuit · Stanley', '(path) · Kanayama', '(trajectory)'], C['blue'])
    box(176, 126, 196, 74, 'Longitudinal control', ['PI on speed → a_des, limits,', 'actuator map / adaptive', 'inverse model → u'], C['teal'])
    box(430, 66, 118, 78, 'Vehicle', ['bicycle model', 'm v̇ = F − F_res'], C['text'])
    box(604, 66, 168, 78, 'State estimation', ['(x, y, ψ, v) for', 'the errors e_y, e_ψ,', 'e_v, e_x …'], C['violet'])
    line([(126, 96), (150, 96), (150, 47), (174, 47)], C['orange'], 'o')
    line([(150, 112), (150, 163), (174, 163)], C['orange'], 'o')
    line([(372, 47), (400, 47), (400, 92), (428, 92)], C['blue'], 'b')
    line([(372, 163), (400, 163), (400, 118), (428, 118)], C['teal'], 't')
    label(386, 38, 'steering δ', C['blue'], 11, 'middle', 600)
    label(386, 184, 'throttle / brake u', C['teal'], 11, 'middle', 600)
    line([(548, 105), (602, 105)], C['muted'], 'm')
    line([(688, 144), (688, 220), (274, 220), (274, 202)], C['green'], 'g')
    line([(688, 66), (688, 4), (274, 4), (274, 8)], C['green'], 'g')
    label(480, 214, 'errors relative to the reference, recomputed every control cycle', C['green'], 11, 'middle', 600)
    o.append('</svg>')
    (FIG / 'l10_overview.svg').write_text(''.join(o), encoding='utf-8')
    print('  fig l10_overview')


# ------------------------------------------------------------------ 2. bicycle model
def fig_bicycle():
    fig, ax = plt.subplots(figsize=(6.0, 3.4))
    v, T, dt = 10.0, 4.0, 0.01
    for deg, col in ((5, C['teal']), (10, C['blue']), (20, C['orange'])):
        d = math.radians(deg)
        x = y = p = 0.0
        xs, ys = [x], [y]
        for _ in range(int(T / dt)):
            x, y, p = x + dt * v * math.cos(p), y + dt * v * math.sin(p), p + dt * v / L * math.tan(d)
            xs.append(x)
            ys.append(y)
        R = L / math.tan(d)
        ax.plot(xs, ys, color=col, lw=2, label='δ = %d°: R = L / tan δ = %.1f m' % (deg, R))
        ax.plot(0, R, '+', color=col, ms=7)
    ax.plot(0, 0, 'o', color=C['text'], ms=4)
    ax.text(0.6, -1.6, 'start, heading +x', color=C['gray'], fontsize=7.8)
    ax.set_aspect('equal')
    ax.set_xlim(-16, 33)
    ax.set_ylim(-3, 32)
    ax.legend(fontsize=7.8, loc='upper right')
    ax.set_xlabel('x [m]')
    ax.set_ylabel('y [m]')
    ax.set_title('Rear-axle paths for 4 s at v = 10 m/s, L = 2.7 m (+ marks the turn centre)', loc='left')
    save(fig, 'l10_bicycle')


# ------------------------------------------------------------------ 3. pure pursuit geometry (worked example)
def fig_pp_geometry():
    fig, ax = plt.subplots(figsize=(5.4, 4.0))
    x0, y0, ps = 2.0, 1.0, math.radians(30)
    G = np.array([6.0, 6.0])
    dX, dY = G[0] - x0, G[1] - y0
    xg = dX * math.cos(ps) + dY * math.sin(ps)
    yg = -dX * math.sin(ps) + dY * math.cos(ps)
    Ld2 = xg ** 2 + yg ** 2
    R = Ld2 / (2 * yg)
    al = math.atan2(yg, xg)
    u = np.array([math.cos(ps), math.sin(ps)])
    n = np.array([-u[1], u[0]])
    o = np.array([x0, y0])
    c = o + R * n
    a0 = math.atan2(o[1] - c[1], o[0] - c[0])
    a1 = math.atan2(G[1] - c[1], G[0] - c[0])
    th = np.linspace(a0, a1, 120)
    ax.plot(c[0] + R * np.cos(th), c[1] + R * np.sin(th), color=C['teal'], lw=2.4, zorder=3)
    arrow(ax, tuple(o), tuple(o + 7.4 * u), C['gray'], 1.0)
    arrow(ax, tuple(o), tuple(o + 3.0 * n), C['gray'], 1.0)
    ax.text(*(o + 7.6 * u + np.array([0.05, -0.2])), r'$x_b$', color=C['gray'], fontsize=11)
    ax.text(*(o + 3.15 * n + np.array([-0.45, 0.0])), r'$y_b$', color=C['gray'], fontsize=11)
    q = o + xg * u
    ax.plot([o[0], q[0]], [o[1], q[1]], color=C['orange'], lw=2.6, zorder=4)
    ax.plot([q[0], G[0]], [q[1], G[1]], color=C['rose'], lw=2.6, zorder=4)
    ax.plot([o[0], G[0]], [o[1], G[1]], color=C['amber'], lw=1.3, ls='--', zorder=4)
    s = 0.28
    sq = [q - s * u, q - s * u + s * n, q + s * n]
    ax.plot([p[0] for p in sq], [p[1] for p in sq], color=C['gray'], lw=0.8)
    ax.plot(*G, 'o', color=C['amber'], ms=6.5, zorder=7)
    ax.text(G[0] + 0.18, G[1] + 0.12, 'G', color=C['amber'], fontsize=11, fontweight=600)
    ax.text(*(o + 3.0 * u - 0.5 * n), r'$x_g$', color=C['orange'], fontsize=11, rotation=30, ha='center', va='center')
    ax.text(*(0.5 * (q + G) + 0.32 * u), r'$y_g$', color=C['rose'], fontsize=11, ha='left', va='center')
    nc = np.array([-dY, dX]) / math.hypot(dX, dY)
    ax.text(*(0.5 * (o + G) + 0.42 * nc), r'$L_d$', color=C['amber'], fontsize=11, rotation=51.3,
            ha='center', va='center')
    ax.add_patch(Arc(tuple(o), 3.0, 3.0, theta1=30, theta2=30 + math.degrees(al), color=C['violet'], lw=1.4))
    ax.text(*(o + 1.85 * np.array([math.cos(math.radians(44)), math.sin(math.radians(44))])), r'$\alpha$',
            color=C['violet'], fontsize=11, ha='center', va='center')
    ax.text(c[0] + 0.0, 0, '', color=C['gray'])
    pose(ax, x0, y0, ps, C['blue'], size=0.2)
    ax.text(x0 + 0.25, y0 - 0.55, 'car (2, 1), ψ = 30°', color=C['blue'], fontsize=8.2)
    info = ('goal G = (6, 6):  ΔX = 4,  ΔY = 5\n'
            'x_g = 5.96 m,   y_g = 2.33 m\n'
            'L_d = √41 = 6.40 m,   α = 21.3°\n'
            'κ = 2y_g / L_d² = 0.114 1/m   (R = 8.80 m)\n'
            'δ = arctan(Lκ) = 17.1°   (L = 2.7 m)')
    ax.text(0.15, 7.75, info, color=C['text'], fontsize=7.9, va='top', linespacing=1.45)
    pa = (c[0] + R * math.cos(th[70]), c[1] + R * math.sin(th[70]))
    ax.annotate('arc of radius R,\ntangent to $x_b$', xy=pa, xytext=(6.3, 1.75), color=C['teal'], fontsize=7.8,
                ha='left', va='top', arrowprops=dict(arrowstyle='-', color=C['teal'], lw=0.7))
    ax.set_aspect('equal')
    ax.set_xlim(0, 9.8)
    ax.set_ylim(0, 7.9)
    ax.set_title('Pure Pursuit worked example', loc='left')
    save(fig, 'l10_pp_geometry')


def pp_sim(Ld, v=10.0, y0=1.0, T=12.0, dt=0.005):
    x, y, p = 0.0, y0, 0.0
    ts, ys, ds = [], [], []
    for k in range(int(T / dt)):
        if abs(y) >= Ld:
            break
        Xg = x + math.sqrt(Ld ** 2 - y ** 2)
        dX, dY = Xg - x, -y
        yg = -dX * math.sin(p) + dY * math.cos(p)
        d = max(-DMAX, min(DMAX, math.atan(2 * L * yg / Ld ** 2)))
        ts.append(k * dt)
        ys.append(y)
        ds.append(d)
        x, y, p = x + dt * v * math.cos(p), y + dt * v * math.sin(p), p + dt * v / L * math.tan(d)
    return np.array(ts), np.array(ys), np.array(ds)


def fig_pp_response():
    fig, axs = plt.subplots(1, 2, figsize=(6.9, 2.7), gridspec_kw=dict(wspace=0.28))
    v = 10.0
    for Ld, col in ((5, C['teal']), (10, C['blue']), (20, C['orange'])):
        wn, z = math.sqrt(2) * v / Ld, 1 / math.sqrt(2)
        wd = wn * math.sqrt(1 - z * z)
        t = np.linspace(0, 12, 600)
        lin = np.exp(-z * wn * t) * (np.cos(wd * t) + z / math.sqrt(1 - z * z) * np.sin(wd * t))
        axs[0].plot(t, lin, color=col, lw=1.8, label='$L_d$ = %d m ($\\omega_n$ = %.2f)' % (Ld, wn))
        ts, ys, ds = pp_sim(Ld)
        axs[0].plot(ts[::40], ys[::40], 'o', color=col, ms=2.6)
        axs[1].plot(ts, np.degrees(ds), color=col, lw=1.6)
    axs[0].axhline(0, color=C['spine'], lw=0.8)
    axs[0].set_xlabel('t [s]   (lines: linear model, dots: full simulation)')
    axs[0].set_ylabel(r'$e_y(t)\,/\,e_y(0)$')
    axs[0].set_title('Lateral error from a 1 m offset, v = 10 m/s', loc='left')
    axs[0].legend(fontsize=7.4, loc='upper right')
    axs[1].set_xlabel('t [s]')
    axs[1].set_ylabel('steering δ [deg]')
    axs[1].set_title('Steering effort', loc='left')
    axs[1].set_xlim(0, 6)
    save(fig, 'l10_pp_response')


# ------------------------------------------------------------------ 5. stanley
def stanley_sim(k, v=5.0, e0=1.0, T=6.0, dt=0.002):
    x, y, p = -L, e0, 0.0          # front axle starts at (0, e0)
    ts, es, ds = [], [], []
    for i in range(int(T / dt)):
        yf = y + L * math.sin(p)
        d = max(-DMAX, min(DMAX, -p - math.atan(k * yf / v)))
        ts.append(i * dt)
        es.append(yf)
        ds.append(d)
        x, y, p = x + dt * v * math.cos(p), y + dt * v * math.sin(p), p + dt * v / L * math.tan(d)
    return np.array(ts), np.array(es), np.array(ds)


def fig_stanley():
    fig, axs = plt.subplots(1, 2, figsize=(6.9, 2.7), gridspec_kw=dict(wspace=0.28))
    for k, col in ((0.5, C['orange']), (1.0, C['blue']), (2.0, C['teal'])):
        ts, es, ds = stanley_sim(k)
        axs[0].plot(ts, es, color=col, lw=1.9, label='k = %.1f 1/s' % k)
        axs[0].plot(ts, np.exp(-k * ts), color=col, lw=0.9, ls='--')
        axs[1].plot(ts, np.degrees(ds), color=col, lw=1.6)
    axs[1].axhline(-35, color=C['rose'], lw=0.8, ls=':')
    axs[1].text(3.2, -33, 'steering limit −35°', color=C['rose'], fontsize=7.6)
    axs[0].set_xlabel('t [s]   (dashed: $e^{-kt}$)')
    axs[0].set_ylabel(r'front-axle error $e_f$ [m]')
    axs[0].set_title('Stanley from a 1 m offset, v = 5 m/s', loc='left')
    axs[0].legend(fontsize=7.6)
    axs[1].set_xlabel('t [s]')
    axs[1].set_ylabel('δ [deg]')
    axs[1].set_title('Steering command', loc='left')
    axs[1].set_xlim(0, 4)
    save(fig, 'l10_stanley')


# ------------------------------------------------------------------ 6. longitudinal forces
def fig_forces():
    m, rho, CD, A, Crr, th = 1500, 1.2, 0.3, 2.2, 0.012, math.radians(3)
    v = np.linspace(0, 40, 200)
    Fa = 0.5 * rho * CD * A * v ** 2
    Fr = np.full_like(v, Crr * m * 9.81 * math.cos(th))
    Fg = np.full_like(v, m * 9.81 * math.sin(th))
    fig, ax = plt.subplots(figsize=(5.6, 2.9))
    ax.stackplot(v, Fg, Fr, Fa, colors=[C['violet'], C['amber'], C['teal']], alpha=0.55,
                 labels=['grade  m g sin θ (θ = 3°)', 'rolling  C_rr m g cos θ', 'aero  ½ρC_D A v²'])
    ax.plot(20, 1104.9, 'o', color=C['text'], ms=5)
    ax.annotate('v = 20 m/s: 770 + 176 + 158 = 1105 N', xy=(20, 1104.9), xytext=(1.0, 1500), color=C['text'], fontsize=8,
                arrowprops=dict(arrowstyle='-', color=C['muted'], lw=0.7))
    ax.set_xlabel('speed v [m/s]')
    ax.set_ylabel('resistance force [N]')
    ax.set_xlim(0, 40)
    ax.set_ylim(0, 1700)
    ax.legend(fontsize=7.6, loc='upper left', bbox_to_anchor=(0.0, 0.83))
    ax.set_title('Resistance of the example car (m = 1500 kg, C_D A = 0.66 m², C_rr = 0.012)', loc='left')
    save(fig, 'l10_forces')


# ------------------------------------------------------------------ 7. PI speed control
def fig_pi():
    dt, T = 0.01, 25.0
    fig, ax = plt.subplots(figsize=(5.8, 2.8))
    for kp, ki, col, lab in ((1.0, 0.0, C['orange'], 'P only ($k_p$ = 1): stays 0.3 m/s low'),
                             (1.0, 0.25, C['teal'], 'PI ($k_p$ = 1, $k_i$ = 0.25): error → 0')):
        v, z = 10.0, 0.0
        ts, vs = [], []
        for i in range(int(T / dt)):
            t = i * dt
            vref = 10.0 if t < 3 else 15.0
            e = vref - v
            a = kp * e + ki * z - 0.3
            ts.append(t)
            vs.append(v)
            v += dt * a
            z += dt * e
        ax.plot(ts, vs, color=col, lw=2, label=lab)
    ax.plot([0, 3, 3, 25], [10, 10, 15, 15], color=C['muted'], lw=1, ls='--', label='$v_{ref}$')
    ax.set_xlabel('t [s]   (constant disturbance $d_a$ = −0.3 m/s² from t = 0)')
    ax.set_ylabel('speed v [m/s]')
    ax.set_ylim(9.2, 15.8)
    ax.legend(fontsize=7.6, loc='lower right')
    ax.set_title('Why the integral term: speed step 10 → 15 m/s', loc='left')
    save(fig, 'l10_pi')


# ------------------------------------------------------------------ 8. actuator map
def fig_map():
    u = np.array([0.0, 0.2, 0.4, 0.6, 0.8])
    a1 = np.array([-0.3, 0.8, 1.9, 2.8, 3.5])
    a2 = np.array([-0.5, 0.5, 1.4, 2.2, 2.8])
    af = 0.6 * a1 + 0.4 * a2
    fig, ax = plt.subplots(figsize=(5.4, 3.0))
    ax.plot(u, a1, '-o', color=C['blue'], ms=3.5, lw=1.4, label='map at $v_1$ = 10 m/s')
    ax.plot(u, a2, '-o', color=C['green'], ms=3.5, lw=1.4, label='map at $v_2$ = 20 m/s')
    ax.plot(u, af, '-o', color=C['teal'], ms=4, lw=2.2, label='interpolated, v = 14 m/s (λ = 0.4)')
    amap, ucmd = 0.8424, 0.2318
    ax.plot([0, ucmd], [amap, amap], color=C['orange'], lw=1.2, ls='--')
    ax.plot([ucmd, ucmd], [amap, -0.9], color=C['orange'], lw=1.2, ls='--')
    ax.plot(ucmd, amap, 'o', color=C['orange'], ms=6, zorder=6)
    ax.annotate('$a_{map}$ = 0.5 + g sin 2° = 0.84', xy=(ucmd, amap), xytext=(0.29, 0.25), color=C['orange'],
                fontsize=8, arrowprops=dict(arrowstyle='-', color=C['orange'], lw=0.7))
    ax.text(ucmd + 0.015, -0.8, '$u_{cmd}$ = 0.232', color=C['orange'], fontsize=8)
    ax.set_xlabel('throttle input u')
    ax.set_ylabel('acceleration a [m/s²]')
    ax.set_ylim(-0.9, 3.8)
    ax.legend(fontsize=7.6, loc='upper left')
    ax.set_title('Actuator map: interpolate in speed, then invert in u', loc='left')
    save(fig, 'l10_map')


# ------------------------------------------------------------------ 9. online estimation
def estimate(inp, gain, T=40.0, Ts=0.05, b=2.0, d=0.4):
    th = np.array([1.5, 0.2])
    ts, bs, dsr, es = [], [], [], []
    for k in range(int(T / Ts) + 1):
        t = k * Ts
        u = inp(t)
        phi = np.array([u, -1.0])
        eps = (b * u - d) - phi @ th
        ts.append(t)
        bs.append(th[0])
        dsr.append(th[1])
        es.append(eps)
        th = th + Ts * gain * phi * eps
        th[0] = max(th[0], 0.5)
        th[1] = min(max(th[1], -1.0), 2.0)
    return np.array(ts), np.array(bs), np.array(dsr), np.array(es)


def fig_estimation():
    fig, axs = plt.subplots(1, 2, figsize=(6.9, 2.7), sharey=True, gridspec_kw=dict(wspace=0.08))
    cases = ((axs[0], lambda t: 0.8 if int(t) % 2 == 0 else 0.2, 4.0, 'input steps 0.2 ↔ 0.8 every second, Γ = 4I'),
             (axs[1], lambda t: 0.5 + 0.4 * math.sin(0.8 * t), 10.0, r'slow sine input, Γ = 10I: $\hat a$ fits $a$, but $\hat b$, $\hat d_{eq}$ wander'))
    for ax, inp, gain, ttl in cases:
        ts, bs, dsr, es = estimate(inp, gain)
        ax.plot(ts, bs, color=C['blue'], lw=1.8, label=r'$\hat b$')
        ax.plot(ts, dsr, color=C['orange'], lw=1.8, label=r'$\hat d_{eq}$')
        ax.axhline(2.0, color=C['blue'], lw=0.8, ls='--')
        ax.axhline(0.4, color=C['orange'], lw=0.8, ls='--')
        ax.set_title(ttl, loc='left', fontsize=8.4)
        ax.set_xlabel('t [s]')
    axs[0].text(30, 2.06, 'true b = 2.0', color=C['blue'], fontsize=7.6)
    axs[0].text(30, 0.46, 'true $d_{eq}$ = 0.4', color=C['orange'], fontsize=7.6)
    axs[0].legend(fontsize=7.6, loc='center right')
    axs[0].set_ylabel('estimate')
    save(fig, 'l10_estimation')


# ------------------------------------------------------------------ 10. MRAC
def fig_mrac():
    b, d, k = 0.5, 0.3, 1.0
    Gm = 0.5
    ths = np.array([1 / b, k / b, d / b])
    th = np.array([1.0, 1.0, 0.0])
    dt, T = 0.002, 60.0
    v = 8.0
    ts, es, Vs, TH = [], [], [], []
    for i in range(int(T / dt) + 1):
        t = i * dt
        vr, vrd = 10 + 2 * math.sin(0.3 * t), 0.6 * math.cos(0.3 * t)
        e = vr - v
        phi = np.array([vrd, e, 1.0])
        tl = th - ths
        if i % 25 == 0:
            ts.append(t)
            es.append(e)
            Vs.append(0.5 * e * e + 0.5 * b * tl @ tl / Gm)
            TH.append(th.copy())
        v += dt * (b * (th @ phi) - d)
        th = th + dt * Gm * phi * e
    TH = np.array(TH)
    fig, axs = plt.subplots(1, 2, figsize=(6.9, 2.7), gridspec_kw=dict(wspace=0.3))
    ax = axs[0]
    ax.plot(ts, es, color=C['teal'], lw=1.6, label='$e_v = v_{ref} - v$ [m/s]')
    ax.plot(ts, Vs, color=C['amber'], lw=1.6, label='V (never increases)')
    ax.axhline(0, color=C['spine'], lw=0.8)
    ax.set_xlabel('t [s]')
    ax.set_xlim(0, 30)
    ax.legend(fontsize=7.6)
    ax.set_title('Tracking error and Lyapunov function', loc='left')
    ax = axs[1]
    for j, (col, lab) in enumerate(((C['blue'], r'$\hat\theta_1$ (→ 1/b = 2)'), (C['violet'], r'$\hat\theta_2$ (k/b = 2)'),
                                    (C['orange'], r'$\hat\theta_3$ (d/b = 0.6)'))):
        ax.plot(ts, TH[:, j], color=col, lw=1.6, label=lab)
        ax.axhline(ths[j], color=col, lw=0.8, ls='--')
    ax.set_xlabel('t [s]')
    ax.legend(fontsize=7.4, loc='center right', bbox_to_anchor=(1.0, 0.42))
    ax.set_title(r'Parameters: $\hat\theta_2$ settles at 2.52, not 2', loc='left')
    save(fig, 'l10_mrac')


# ------------------------------------------------------------------ 11. limits
def fig_limits():
    fig, axs = plt.subplots(1, 2, figsize=(6.9, 2.7), gridspec_kw=dict(wspace=0.28))
    dt, T = 0.001, 4.0
    jmax, amax, tau, Td = 2.0, 2.0, 0.3, 0.1
    alim, a = 0.0, 0.0
    hist = []
    ts, ad, al, aa = [], [], [], []
    for i in range(int(T / dt)):
        t = i * dt
        ades = 2.5 if t >= 0.5 else 0.0
        target = min(max(ades, -3.0), amax)
        alim += max(-jmax * dt, min(jmax * dt, target - alim))
        hist.append(alim)
        delayed = hist[i - int(Td / dt)] if i >= int(Td / dt) else 0.0
        a += dt * (delayed - a) / tau
        ts.append(t)
        ad.append(ades)
        al.append(alim)
        aa.append(a)
    ax = axs[0]
    ax.plot(ts, ad, color=C['muted'], lw=1.2, ls='--', label='$a_{des}$ (asks 2.5)')
    ax.plot(ts, al, color=C['amber'], lw=1.8, label='$a_{lim}$: jerk ≤ 2, a ≤ 2')
    ax.plot(ts, aa, color=C['teal'], lw=1.8, label='actual a: delay 0.1 s, lag 0.3 s')
    ax.set_xlabel('t [s]')
    ax.set_ylabel('acceleration [m/s²]')
    ax.legend(fontsize=7.2, loc='lower right')
    ax.set_title('Limited command and actual response', loc='left')
    ax = axs[1]
    for kaw, col, lab in ((0.0, C['rose'], 'no anti-windup'), (1.0, C['teal'], 'anti-windup, $k_{aw}$ = 1 s')):
        v, z = 10.0, 0.0
        ts, vs = [], []
        for i in range(int(25 / 0.01)):
            e = 25.0 - v
            ades = 1.0 * e + 0.25 * z
            al_ = min(max(ades, -3.0), 2.0)
            ts.append(i * 0.01)
            vs.append(v)
            v += 0.01 * al_
            z += 0.01 * (e + kaw * (al_ - ades))
        ax.plot(ts, vs, color=col, lw=1.9, label=lab)
    ax.axhline(25, color=C['muted'], lw=0.9, ls='--')
    ax.set_xlabel('t [s]   ($a_{max}$ = 2 m/s², PI $k_p$ = 1, $k_i$ = 0.25)')
    ax.set_ylabel('speed [m/s]')
    ax.legend(fontsize=7.4, loc='lower right')
    ax.set_title('Speed step 10 → 25 m/s with saturation', loc='left')
    save(fig, 'l10_limits')


# ------------------------------------------------------------------ 12. trajectory error geometry
def fig_traj_error():
    fig, ax = plt.subplots(figsize=(5.4, 3.5))
    xr, yr, pr = 10.0, 3.0, math.radians(30)
    x, y, p = 8.0, 2.0, math.radians(20)
    u = np.array([math.cos(p), math.sin(p)])
    n = np.array([-u[1], u[0]])
    o = np.array([x, y])
    ex, ey = 2.2214, 0.2557
    arrow(ax, tuple(o), tuple(o + 3.7 * u), C['gray'], 1.0)
    arrow(ax, tuple(o), tuple(o + 1.7 * n), C['gray'], 1.0)
    ax.text(*(o + 3.85 * u + np.array([0, -0.12])), r'$x_b$', color=C['gray'], fontsize=11)
    ax.text(*(o + 1.85 * n + np.array([-0.3, 0])), r'$y_b$', color=C['gray'], fontsize=11)
    q = o + ex * u
    ax.plot([x, q[0]], [y, q[1]], color=C['orange'], lw=2.8, zorder=4)
    ax.plot([q[0], xr], [q[1], yr], color=C['rose'], lw=2.8, zorder=4)
    ax.plot([x, xr], [y, yr], color=C['faint'], lw=1.0, ls=':', zorder=3)
    s = 0.12
    sq = [q - s * u, q - s * u + s * n, q + s * n]
    ax.plot([pp[0] for pp in sq], [pp[1] for pp in sq], color=C['gray'], lw=0.8)
    ax.text(*(o + 0.5 * ex * u - 0.27 * n), r'$e_x = 2.22$', color=C['orange'], fontsize=10.5, rotation=20,
            ha='center', va='center')
    ax.text(q[0] + 0.2, q[1] - 0.06, r'$e_y = 0.26$', color=C['rose'], fontsize=10.5, ha='left', va='center')
    pose(ax, x, y, p, C['blue'], size=0.14)
    pose(ax, xr, yr, pr, C['green'], size=0.14)
    ax.text(x - 0.15, y - 0.45, 'actual (8, 2), ψ = 20°', color=C['blue'], fontsize=8.4, ha='left')
    ax.text(xr - 0.25, yr + 0.42, 'reference (10, 3), ψ_r = 30°', color=C['green'], fontsize=8.4, ha='center')
    ax.text(6.95, 4.35, r'$e_\psi = \psi_r - \psi$' + ' = 10°', color=C['text'], fontsize=10.5)
    ax.set_aspect('equal')
    ax.set_xlim(6.8, 12.4)
    ax.set_ylim(1.2, 4.7)
    ax.set_title('Trajectory error: reference − actual, in the vehicle frame', loc='left')
    save(fig, 'l10_traj_error')


def kanayama_sim(limit, T=12.0, dt=0.0005, kx=0.8, ky=0.1, kp=0.6, vr=4.0, start=(0.0, -4.0, math.radians(-30))):
    """Straight reference along x at speed vr (x_r = vr t); returns rows
    (t, x, y, ex, ey, epsi, V, xr, yr, saturated)."""
    x, y, p = start
    out = []
    for i in range(int(T / dt)):
        t = i * dt
        xr, yr, pr = vr * t, 0.0, 0.0
        dx, dy = xr - x, yr - y
        ex = dx * math.cos(p) + dy * math.sin(p)
        ey = -dx * math.sin(p) + dy * math.cos(p)
        ep = (pr - p + math.pi) % (2 * math.pi) - math.pi
        vc = vr * math.cos(ep) + kx * ex
        wc = vr * (ky * ey + kp * math.sin(ep))
        sat = 0.0
        if limit:
            wm = abs(vc) * math.tan(DMAX) / L
            if abs(wc) > wm:
                sat = 1.0
                wc = max(-wm, min(wm, wc))
        V = 0.5 * (ex * ex + ey * ey) + (1 - math.cos(ep)) / ky
        out.append((t, x, y, ex, ey, ep, V, xr, yr, sat))
        x, y, p = x + dt * vc * math.cos(p), y + dt * vc * math.sin(p), p + dt * wc
    return np.array(out)


def fig_kanayama():
    ideal = kanayama_sim(False)
    lim = kanayama_sim(True)
    dt = 0.0005
    dV = np.diff(lim[:, 6])
    print('    limited: saturated for %.2f s, V rises over %.2f s (max V %.2f vs start %.2f); ideal V monotone: %s'
          % (lim[:, 9].sum() * dt, (dV > 1e-9).sum() * dt, lim[:, 6].max(), lim[0, 6],
             bool((np.diff(ideal[:, 6]) <= 1e-9).all())))
    fig = plt.figure(figsize=(6.9, 4.7))
    gs = fig.add_gridspec(2, 1, height_ratios=[1.0, 1.25], hspace=0.42)
    ax = fig.add_subplot(gs[0])
    ax.plot([-2, 50], [0, 0], color=C['muted'], lw=1.2, ls='--', label='reference: $x_r = 4t$, $y_r = 0$')
    ax.plot(ideal[:, 1], ideal[:, 2], color=C['teal'], lw=2.0, label='ideal: $v = v_c$, $\omega = \omega_c$')
    ax.plot(lim[:, 1], lim[:, 2], color=C['orange'], lw=1.6, ls='-.', label='car with |δ| ≤ 35°')
    for tk in (0, 1, 2, 3):
        i = int(round(tk / dt))
        ax.plot(ideal[i, 7], 0, 'o', color=C['muted'], ms=4, zorder=6)
        ax.plot(ideal[i, 1], ideal[i, 2], 'o', color=C['teal'], ms=4, zorder=6)
        ax.plot([ideal[i, 7], ideal[i, 1]], [0, ideal[i, 2]], color=C['faint'], lw=0.7, ls=':')
        ax.text(ideal[i, 7], 0.5, 't = %d s' % tk, color=C['gray'], fontsize=7.4, ha='center')
    ax.text(2.2, -5.35, 'start (0, −4), ψ = −30°', color=C['gray'], fontsize=7.6)
    ax.set_aspect('equal')
    ax.set_xlim(-1.5, 36)
    ax.set_ylim(-5.6, 2.6)
    ax.legend(fontsize=7.4, loc='lower right')
    ax.set_title('Paths (dotted: reference and car at the same instant)', loc='left')
    ax = fig.add_subplot(gs[1])
    ax.plot(ideal[:, 0], ideal[:, 3], color=C['blue'], lw=1.5, label='$e_x$ [m]')
    ax.plot(ideal[:, 0], ideal[:, 4], color=C['rose'], lw=1.5, label='$e_y$ [m]')
    ax.plot(ideal[:, 0], np.degrees(ideal[:, 5]) / 10, color=C['violet'], lw=1.5, label=r'$e_\psi$ [10°]')
    ax.plot(ideal[:, 0], ideal[:, 6] / 5, color=C['amber'], lw=1.8, label='V / 5, ideal')
    ax.plot(lim[:, 0], lim[:, 6] / 5, color=C['amber'], lw=1.3, ls='--', label='V / 5, steering-limited (rises!)')
    ax.axhline(0, color=C['spine'], lw=0.8)
    ax.set_xlabel(r't [s]   ($k_x$ = 0.8 1/s, $k_y$ = 0.1 1/m², $k_\psi$ = 0.6 1/m, $v_r$ = 4 m/s; errors of the ideal case)')
    ax.set_xlim(0, 10)
    ax.legend(fontsize=7.3, loc='upper right', ncol=2)
    ax.set_title('Errors and the Lyapunov function V', loc='left')
    save(fig, 'l10_kanayama')


ALL = [fig_overview, fig_bicycle, fig_pp_geometry, fig_pp_response, fig_stanley, fig_forces, fig_pi, fig_map,
       fig_estimation, fig_mrac, fig_limits, fig_traj_error, fig_kanayama]

if __name__ == '__main__':
    want = sys.argv[1:]
    for f in ALL:
        if not want or f.__name__[4:] in want:
            f()
