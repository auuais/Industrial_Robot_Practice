# -*- coding: utf-8 -*-
"""Generate the data plots for the notes as dark-theme SVGs in fig/."""
import pathlib
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse, FancyArrowPatch, Polygon

FIG = pathlib.Path(__file__).parent / 'fig'
FIG.mkdir(exist_ok=True)

C = dict(cyan='#22d3ee', violet='#a78bfa', amber='#fbbf24', rose='#fb7185', green='#4ade80',
         blue='#60a5fa', orange='#fb923c', teal='#2dd4bf', gray='#8a94a7', text='#dfe4ec',
         muted='#a3acbd', faint='#5d6880', grid='#263044', spine='#3a4560', panel='#161b24')

plt.rcParams.update({
    'font.family': 'Segoe UI', 'font.size': 8.6, 'mathtext.fontset': 'stix',
    'text.color': C['text'], 'axes.labelcolor': C['muted'], 'axes.edgecolor': C['spine'],
    'xtick.color': C['gray'], 'ytick.color': C['gray'], 'axes.facecolor': 'none',
    'figure.facecolor': 'none', 'savefig.facecolor': 'none', 'savefig.transparent': True,
    'axes.grid': True, 'grid.color': C['grid'], 'grid.linewidth': 0.6, 'axes.linewidth': 0.8,
    'axes.titlesize': 9.2, 'axes.titlecolor': C['text'], 'axes.titleweight': 'semibold',
    'axes.titlepad': 7, 'legend.frameon': False, 'legend.fontsize': 8, 'lines.linewidth': 1.7,
    'svg.fonttype': 'path', 'axes.axisbelow': True, 'xtick.major.size': 3, 'ytick.major.size': 3,
    'axes.spines.top': False, 'axes.spines.right': False,
})


def save(fig, name):
    fig.savefig(FIG / (name + '.svg'), bbox_inches='tight', pad_inches=0.04)
    plt.close(fig)
    print('  fig', name)


def wrap(a):
    return (a + np.pi) % (2 * np.pi) - np.pi


# =========================================================== Lecture 2
def l2_figs():
    v, L, dl = 5.0, 2.5, np.deg2rad(10)
    w = v / L * np.tan(dl)

    def fc(x):
        return np.array([x[3] * np.cos(x[2]), x[3] * np.sin(x[2]), x[3] / L * np.tan(dl), 0.0])

    def step(x, h, m):
        if m == 'Euler':
            return x + h * fc(x)
        if m == 'Midpoint':
            return x + h * fc(x + h / 2 * fc(x))
        k1 = fc(x); k2 = fc(x + h / 2 * k1); k3 = fc(x + h / 2 * k2); k4 = fc(x + h * k3)
        return x + h / 6 * (k1 + 2 * k2 + 2 * k3 + k4)

    def run(h, m, T=4.0):
        x = np.array([0, 0, 0, v])
        out = [x]
        for _ in range(int(round(T / h))):
            x = step(x, h, m)
            out.append(x)
        return np.array(out)

    # trajectories, h = 0.5
    fig, ax = plt.subplots(figsize=(6.6, 2.9))
    t = np.linspace(0, 4, 300)
    ax.plot(v / w * np.sin(w * t), v / w * (1 - np.cos(w * t)), color=C['text'], lw=1.2, ls='--', label='Analytic')
    for m, col, mk in (('Euler', C['rose'], 'o'), ('Midpoint', C['cyan'], 's'), ('RK4', C['green'], '^')):
        tr = run(0.5, m)
        ax.plot(tr[:, 0], tr[:, 1], color=col, marker=mk, ms=3.6, lw=1.3, label=m)
    ax.set_xlabel('X [m]'); ax.set_ylabel('Y [m]'); ax.set_aspect('equal')
    ax.set_xlim(-0.5, 19.5); ax.set_ylim(-0.5, 13)
    ax.legend(loc='upper left')
    ax.annotate('Euler: 1.62 m off after 4 s', xy=(15.05, 10.6), xytext=(15.6, 6.2), color=C['rose'], fontsize=8,
                arrowprops=dict(arrowstyle='->', color=C['rose'], lw=0.8))
    ax.annotate('RK4 sits on the analytic\ncurve (error 6 µm)', xy=(13.9, 11.95), xytext=(5.2, 11.1), color=C['green'], fontsize=8,
                arrowprops=dict(arrowstyle='->', color=C['green'], lw=0.8))
    ax.set_title('Same model, same inputs, h = 0.5 s (8 steps): only the integrator differs', loc='left')
    save(fig, 'l2_traj')

    # convergence (log-log)
    hs = np.array([0.5, 0.25, 0.2, 0.1, 0.05, 0.025])
    ex = np.array([v / w * np.sin(w * 4), v / w * (1 - np.cos(w * 4))])
    fig, ax = plt.subplots(figsize=(6.6, 2.9))
    for m, col, mk, p in (('Euler', C['rose'], 'o', 1), ('Midpoint', C['cyan'], 's', 2), ('RK4', C['green'], '^', 4)):
        e = np.array([np.linalg.norm(run(h, m)[-1, :2] - ex) for h in hs])
        ax.loglog(hs, e, color=col, marker=mk, ms=4, label='%s: slope %d — halve h, error ×1/%d' % (m, p, 2 ** p))
        ax.loglog(hs, e[0] * (hs / hs[0]) ** p, color=col, lw=0.7, ls=':', alpha=0.9)
    ax.set_xlabel('step size h [s]'); ax.set_ylabel('position error after 4 s [m]')
    ax.invert_xaxis()
    ax.legend(loc='lower left')
    ax.set_title('Order of convergence: E(h) ≈ C·hᵖ is a straight line of slope p on log–log axes', loc='left')
    save(fig, 'l2_conv')

    # steering lag + Euler stability
    tau, cmd = 0.4, 10.0
    fig, axs = plt.subplots(1, 2, figsize=(6.8, 2.55), gridspec_kw=dict(wspace=0.28))
    ax = axs[0]
    t = np.linspace(0, 2.5, 400)
    act = np.where(t < 0.5, 0, cmd * (1 - np.exp(-(t - 0.5) / tau)))
    ax.plot(t, np.where(t < 0.5, 0, cmd), color=C['blue'], lw=1.3, label='command δcmd')
    ax.plot(t, act, color=C['amber'], label='actual δ (τ = 0.4 s)')
    ax.axvline(0.9, color=C['faint'], lw=0.8, ls='--')
    ax.plot([0.9], [cmd * (1 - np.exp(-1))], 'o', color=C['amber'], ms=4)
    ax.annotate('63.2 % after one τ\nδ(0.9 s) ≈ 6.32°', xy=(0.9, 6.32), xytext=(1.25, 3.2), fontsize=8, color=C['amber'],
                arrowprops=dict(arrowstyle='->', color=C['amber'], lw=0.8))
    ax.set_xlabel('t [s]'); ax.set_ylabel('steering angle [°]'); ax.set_ylim(-0.8, 12)
    ax.legend(loc='lower right', fontsize=7.6)
    ax.set_title('First-order steering actuator', loc='left')
    ax = axs[1]
    ta = np.linspace(0, 4, 300)
    ax.plot(ta, cmd * (1 - np.exp(-ta / tau)), color=C['text'], lw=1.1, ls='--', label='analytic')
    for h, col in ((0.2, C['green']), (0.6, C['cyan']), (1.0, C['rose'])):
        n = int(round(4 / h))
        e = [-cmd]
        for _ in range(n):
            e.append((1 - h / tau) * e[-1])
        ax.plot(np.arange(n + 1) * h, np.array(e) + cmd, color=col, marker='o', ms=3,
                label='Euler h = %.1f s  (1−h/τ = %+.1f)' % (h, 1 - h / tau))
    ax.set_xlabel('t [s]'); ax.set_ylim(-45, 50)
    ax.legend(loc='lower left', fontsize=7.2)
    ax.set_title('Euler stability needs |1 − h/τ| < 1, i.e. h < 0.8 s', loc='left')
    save(fig, 'l2_stab')


# =========================================================== Lecture 3
def l3_figs():
    # radial distortion
    fig, axs = plt.subplots(1, 2, figsize=(6.6, 3.0), gridspec_kw=dict(wspace=0.12))
    g = np.linspace(-0.6, 0.6, 9)
    s = np.linspace(-0.6, 0.6, 120)
    for ax, k1, name in ((axs[0], -0.35, 'Barrel  (k₁ < 0)'), (axs[1], 0.35, 'Pincushion  (k₁ > 0)')):
        for c in g:
            for xs, ys in ((np.full_like(s, c), s), (s, np.full_like(s, c))):
                ax.plot(xs, ys, color=C['faint'], lw=0.6)
                r2 = xs ** 2 + ys ** 2
                f = 1 + k1 * r2
                ax.plot(xs * f, ys * f, color=C['violet'], lw=1.1)
        ax.set_aspect('equal'); ax.set_xlim(-0.82, 0.82); ax.set_ylim(-0.82, 0.82)
        ax.set_xticks([]); ax.set_yticks([]); ax.grid(False)
        for sp in ax.spines.values():
            sp.set_visible(False)
        ax.set_title(name, color=C['text'])
    fig.text(0.5, 0.01, 'gray: ideal grid in normalized coordinates · violet: after  x_d = x(1 + k₁r²)', ha='center',
             color=C['muted'], fontsize=8)
    save(fig, 'l3_distortion')

    # stereo depth error
    fig, ax = plt.subplots(figsize=(6.6, 2.6))
    Z = np.linspace(0.5, 10, 300)
    f, sd = 800, 0.5
    for B, col in ((0.12, C['violet']), (0.24, C['cyan'])):
        ax.plot(Z, Z ** 2 / (f * B) * sd, color=col, label='B = %.2f m' % B)
    for z, s_ in ((2, 0.0208), (8, 0.333)):
        ax.plot([z], [s_], 'o', color=C['amber'], ms=5)
    ax.annotate('d = 48 px → Z = 2 m, σZ = 2.1 cm', xy=(2, 0.0208), xytext=(2.4, 0.28), color=C['amber'], fontsize=8,
                arrowprops=dict(arrowstyle='->', color=C['amber'], lw=0.8))
    ax.annotate('d = 12 px → Z = 8 m, σZ = 33 cm', xy=(8, 0.333), xytext=(4.2, 0.5), color=C['amber'], fontsize=8,
                arrowprops=dict(arrowstyle='->', color=C['amber'], lw=0.8))
    ax.set_xlabel('depth Z [m]'); ax.set_ylabel('σZ [m]')
    ax.legend(loc='upper left')
    ax.set_title('σZ ≈ Z²·σd /(f B): 4× the distance → 16× the depth error (f = 800 px, σd = 0.5 px)', loc='left')
    save(fig, 'l3_depth')

    # observability: time offset vs position offset
    fig, axs = plt.subplots(1, 2, figsize=(6.6, 2.4), gridspec_kw=dict(wspace=0.3))
    tt = np.linspace(0, 1, 100)
    ax = axs[0]
    ax.plot(tt, 10 * (tt + 0.05), color=C['violet'], lw=2.6, label='Δt = 0.05 s, b = 0')
    ax.plot(tt, 10 * tt + 0.5, color=C['amber'], lw=1.2, ls='--', label='Δt = 0, b = 0.5 m')
    ax.set_xlabel('τ [s]'); ax.set_ylabel('y(τ) [m]'); ax.legend(loc='upper left', fontsize=7.6)
    ax.set_title('Constant velocity: identical predictions', loc='left')
    ax = axs[1]
    w_ = 2 * np.pi * 1.2

    def pos(t):  # velocity 10 + 6 sin(w t)
        return 10 * t - 6 / w_ * (np.cos(w_ * t) - 1)
    ax.axhline(0, color=C['violet'], lw=1.4, label='constant velocity: difference 0')
    ax.plot(tt, (pos(tt + 0.05) - pos(tt)) - 0.5, color=C['amber'], lw=1.6,
            label='velocity 10 + 6 sin(ωτ) m/s')
    ax.set_xlabel('τ [s]'); ax.set_ylabel('difference [m]'); ax.set_ylim(-0.42, 0.42)
    ax.legend(loc='lower left', fontsize=7.2)
    ax.set_title('Prediction gap between the two hypotheses', loc='left')
    save(fig, 'l3_observ')


def l3_epipolar():
    """Two verging cameras, a 3-D point, the epipolar plane and line (oblique projection)."""
    def roty(a):
        c, s = np.cos(a), np.sin(a)
        return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])
    P = lambda p: np.array([p[0] + 0.30 * p[2], p[1] + 0.34 * p[2]])
    C1, C2 = np.array([-1.3, 0, 0.0]), np.array([1.3, 0, 0.0])
    R1, R2 = roty(np.deg2rad(18)), roty(np.deg2rad(-18))
    f, w, h = 1.5, 0.62, 0.46
    X = np.array([0.1, 0.55, 5.2])

    def plane(C, R):
        x, y, z = R[:, 0], R[:, 1], R[:, 2]
        c = C + f * z
        return np.array([c - w * x - h * y, c + w * x - h * y, c + w * x + h * y, c - w * x + h * y])

    def proj(C, R, Q):
        z = R[:, 2]
        d = Q - C
        return C + f * d / (d @ z)
    fig, ax = plt.subplots(figsize=(6.6, 3.0))
    pl1, pl2 = plane(C1, R1), plane(C2, R2)
    # epipolar plane (triangle C1, C2, X extended a little)
    tri = np.array([P(C1), P(C2), P(X)])
    ax.fill(tri[:, 0], tri[:, 1], color=C['violet'], alpha=0.10, lw=0)
    for pl, col in ((pl1, C['cyan']), (pl2, C['cyan'])):
        q = np.array([P(p) for p in pl])
        ax.fill(q[:, 0], q[:, 1], color='#1c2230', alpha=0.95, lw=0)
        ax.plot(np.append(q[:, 0], q[0, 0]), np.append(q[:, 1], q[0, 1]), color=col, lw=1.2)
    # baseline
    b = np.array([P(C1), P(C2)])
    ax.plot(b[:, 0], b[:, 1], color=C['gray'], lw=1.2, ls='--')
    ax.text(*(P((C1 + C2) / 2) + [0, -0.2]), 'baseline', color=C['muted'], fontsize=8, ha='center')
    # rays and alternative depths
    for s, mk in ((0.62, 'o'), (1.0, 'o'), (1.35, 'o')):
        Q = C1 + s * (X - C1)
        ax.plot(*P(Q), mk, color=C['amber'] if s == 1.0 else C['faint'], ms=6 if s == 1.0 else 4.5, zorder=5)
        ax.plot(*np.array([P(C2), P(Q)]).T, color=C['faint'], lw=0.8, ls=':')
        x2 = proj(C2, R2, Q)
        ax.plot(*P(x2), 'o', color=C['amber'] if s == 1.0 else C['faint'], ms=4.5 if s == 1.0 else 3.5, zorder=6)
    Qfar = C1 + 1.5 * (X - C1)
    ax.plot(*np.array([P(C1), P(Qfar)]).T, color=C['amber'], lw=1.4)
    ax.plot(*np.array([P(C2), P(X)]).T, color=C['amber'], lw=1.2)
    # epipolar line in image 2 = images of the ray points
    ss = np.linspace(0.25, 6, 200)
    line = np.array([P(proj(C2, R2, C1 + s * (X - C1))) for s in ss])
    q2 = np.array([P(p) for p in pl2])
    from matplotlib.path import Path as MPath
    inside = MPath(q2).contains_points(line)
    ax.plot(line[inside, 0], line[inside, 1], color=C['rose'], lw=2.2)
    x1 = proj(C1, R1, X)
    ax.plot(*P(x1), 'o', color=C['amber'], ms=4.5, zorder=6)
    for Cc, lab in ((C1, 'O₁'), (C2, 'O₂')):
        ax.plot(*P(Cc), 's', color=C['text'], ms=5)
        ax.text(*(P(Cc) + [-0.05, -0.22]), lab, color=C['text'], fontsize=9, ha='center')
    ax.text(*(P(X) + [0.08, 0.06]), 'X', color=C['amber'], fontsize=10)
    ax.text(*(P(x1) + [-0.42, 0.05]), 'x₁', color=C['amber'], fontsize=9)
    mid = line[inside][len(line[inside]) // 2]
    ax.text(mid[0] - 0.55, mid[1] - 0.42, 'epipolar line ℓ₂', color=C['rose'], fontsize=8.5)
    ax.text(*(P((C1 + C2 + X) / 3) + [-0.25, -0.05]), 'epipolar\nplane', color=C['violet'], fontsize=8.5)
    ax.text(*(P(C1 + 1.35 * (X - C1)) + [0.1, 0.0]), 'same x₁, other depths', color=C['muted'], fontsize=7.6)
    ax.set_aspect('equal'); ax.axis('off')
    save(fig, 'l3_epipolar')


# =========================================================== Lecture 4
def l4_figs():
    # square path drift and map->odom correction
    est = [np.zeros(2)]
    hd = 0.0
    for i in range(4):
        est.append(est[-1] + 2.04 * np.array([np.cos(hd), np.sin(hd)]))
        hd += np.deg2rad(95)
    true = np.array([[0, 0], [2, 0], [2, 2], [0, 2], [0, 0.0]])
    est = np.array(est)

    def dense(P, n=40):
        out = []
        for a, b in zip(P[:-1], P[1:]):
            for s in np.linspace(0, 1, n, endpoint=False):
                out.append(a + s * (b - a))
        out.append(P[-1])
        return np.array(out)
    T, E = dense(true), dense(est)
    fig, axs = plt.subplots(1, 3, figsize=(7.0, 2.55), gridspec_kw=dict(wspace=0.38, width_ratios=[1, 1.15, 1]))
    ax = axs[0]
    for i in range(0, len(T), 10):
        ax.plot([T[i, 0], E[i, 0]], [T[i, 1], E[i, 1]], color=C['faint'], lw=0.6)
    ax.plot(T[:, 0], T[:, 1], color=C['text'], lw=1.4, label='true (map)')
    ax.plot(E[:, 0], E[:, 1], color=C['orange'], lw=1.4, label='odometry (odom)')
    ax.plot([0], [0], 'o', color=C['text'], ms=3.5)
    ax.set_aspect('equal'); ax.set_xlim(-0.8, 2.8); ax.set_ylim(-0.8, 2.8)
    ax.set_xlabel('x [m]'); ax.set_ylabel('y [m]')
    ax.set_title('+2 % distance, 95° turns', loc='left')
    ax.legend(loc='upper center', fontsize=6.8, bbox_to_anchor=(0.5, -0.28), ncol=1)
    ax = axs[1]
    dist = np.linspace(0, 8, len(T))
    ax.plot(dist, np.linalg.norm(E - T, axis=1), color=C['orange'])
    ax.set_xlabel('distance driven [m]'); ax.set_ylabel('position error [m]')
    ax.annotate('0.48 m at the start point', xy=(8, 0.4805), xytext=(0.6, 0.43), color=C['orange'], fontsize=7.6,
                arrowprops=dict(arrowstyle='->', color=C['orange'], lw=0.8))
    ax.set_title('Error grows with distance', loc='left')
    ax = axs[2]
    g = np.deg2rad(-20)
    R = np.array([[np.cos(g), -np.sin(g)], [np.sin(g), np.cos(g)]])
    t = -R @ est[-1]
    Ec = (R @ E.T).T + t
    ax.plot(T[:, 0], T[:, 1], color=C['text'], lw=1.4)
    ax.plot(E[:, 0], E[:, 1], color=C['orange'], lw=1.0, alpha=0.7)
    ax.plot(Ec[:, 0], Ec[:, 1], color=C['green'], lw=1.4, label='after map→odom')
    ax.set_aspect('equal'); ax.set_xlim(-0.8, 2.8); ax.set_ylim(-0.8, 2.8)
    ax.set_xlabel('x [m]')
    ax.set_title('Correct the current pose', loc='left')
    ax.text(-0.7, 2.45, 'rot −20°, t = (−0.26, 0.41) m', color=C['green'], fontsize=7.2)
    ax.legend(loc='upper center', fontsize=6.8, bbox_to_anchor=(0.5, -0.28))
    save(fig, 'l4_drift')

    # Gaussian fusion
    def gauss(x, m, var):
        return np.exp(-(x - m) ** 2 / (2 * var)) / np.sqrt(2 * np.pi * var)
    x = np.linspace(4, 16, 600)
    fig, ax = plt.subplots(figsize=(6.6, 2.5))
    for m, var, col, lab in ((8, 3, C['faint'], 'previous  8 m, P⁺ = 3'),
                             (10, 4, C['blue'], 'prediction  10 m, P⁻ = 4'),
                             (12, 1, C['orange'], 'observation  12 m, R = 1'),
                             (11.6, 0.8, C['green'], 'corrected  11.6 m, P⁺ = 0.8')):
        ax.plot(x, gauss(x, m, var), color=col, lw=1.8 if col != C['faint'] else 1.0, label=lab)
        ax.fill_between(x, gauss(x, m, var), color=col, alpha=0.08)
    ax.annotate('', xy=(10, 0.214), xytext=(8, 0.24), arrowprops=dict(arrowstyle='->', color=C['blue'], lw=1))
    ax.text(8.2, 0.255, 'predict: +u, +Q', color=C['blue'], fontsize=8)
    ax.text(12.4, 0.40, 'update: K = 4/(4+1) = 0.8', color=C['green'], fontsize=8)
    ax.set_xlabel('position [m]'); ax.set_ylabel('density'); ax.set_ylim(0, 0.5)
    ax.legend(loc='upper left', fontsize=7.6)
    ax.set_title('One Kalman cycle: prediction widens the bell, the update narrows it', loc='left')
    save(fig, 'l4_fusion')

    # P+(K) parabola and gain vs ratio
    fig, axs = plt.subplots(1, 2, figsize=(6.7, 2.45), gridspec_kw=dict(wspace=0.3))
    ax = axs[0]
    K = np.linspace(0, 1, 200)
    ax.plot(K, (1 - K) ** 2 * 4 + K ** 2 * 1, color=C['amber'])
    ax.plot(K, (1 - K) ** 2 * 4, color=C['blue'], lw=1, ls='--', label='(1−K)²P⁻')
    ax.plot(K, K ** 2 * 1, color=C['orange'], lw=1, ls='--', label='K²R')
    ax.plot([0.8], [0.8], 'o', color=C['green'], ms=5)
    ax.annotate('K* = 0.8, P⁺ = 0.8', xy=(0.8, 0.8), xytext=(0.32, 2.4), color=C['green'], fontsize=8,
                arrowprops=dict(arrowstyle='->', color=C['green'], lw=0.8))
    ax.set_xlabel('gain K'); ax.set_ylabel('P⁺(K) [m²]'); ax.legend(loc='upper center', fontsize=7.4)
    ax.set_title('P⁻ = 4, R = 1', loc='left')
    ax = axs[1]
    r = np.logspace(-2, 2, 200)
    ax.semilogx(r, r / (r + 1), color=C['amber'])
    ax.set_xlabel('P⁻ / R'); ax.set_ylabel('K* = P⁻/(P⁻+R)')
    ax.text(3.0, 0.42, r'$P^{-}\gg R$: trust the' + '\nobservation (K → 1)', color=C['orange'], fontsize=7.8)
    ax.text(0.011, 0.42, r'$P^{-}\ll R$: trust the' + '\nprediction (K → 0)', color=C['blue'], fontsize=7.8)
    ax.set_title('Gain depends only on the variance ratio', loc='left')
    save(fig, 'l4_gain')

    # 1D KF with observation gap
    rng = np.random.default_rng(7)
    dt, n = 1.0, 21
    Q, Rv = 0.09, 1.0
    xt = [5.0]
    u = 1.0
    for k in range(1, n):
        xt.append(xt[-1] + u + rng.normal(0, np.sqrt(Q)))
    xt = np.array(xt)
    z = xt + rng.normal(0, 1.0, n)
    xe, P = [5.0], [0.25]
    for k in range(1, n):
        xm, Pm = xe[-1] + u, P[-1] + Q
        if 8 <= k <= 11:
            xe.append(xm); P.append(Pm)
        else:
            Kk = Pm / (Pm + Rv)
            xe.append(xm + Kk * (z[k] - xm)); P.append((1 - Kk) * Pm)
    xe, P = np.array(xe), np.array(P)
    tt = np.arange(n) * dt
    fig, axs = plt.subplots(2, 1, figsize=(6.6, 3.3), sharex=True, gridspec_kw=dict(hspace=0.12, height_ratios=[1.6, 1]))
    ax = axs[0]
    ax.axvspan(7.5, 11.5, color=C['faint'], alpha=0.18, lw=0)
    ax.fill_between(tt, xe - np.sqrt(P), xe + np.sqrt(P), color=C['green'], alpha=0.18, lw=0)
    ax.plot(tt, xt, color=C['text'], lw=1.2, label='true')
    m = np.ones(n, bool); m[8:12] = False
    ax.plot(tt[m], z[m], 'o', color=C['orange'], ms=3.5, label='observed')
    ax.plot(tt, xe, color=C['green'], label='estimate ±1σ')
    ax.set_ylabel('position [m]'); ax.legend(loc='upper left', ncol=3, fontsize=7.6)
    ax.text(8.0, 7.5, 'no observations', color=C['muted'], fontsize=8)
    ax = axs[1]
    ax.axvspan(7.5, 11.5, color=C['faint'], alpha=0.18, lw=0)
    ax.plot(tt, np.sqrt(P), color=C['green'], marker='o', ms=3)
    ax.axhline(0.508, color=C['faint'], lw=0.8, ls='--')
    ax.text(14.2, 0.56, 'steady state σ ≈ 0.51 m', color=C['muted'], fontsize=7.6)
    ax.set_ylabel('σ [m]'); ax.set_xlabel('time [s]'); ax.set_ylim(0, 0.95)
    axs[0].set_title('Q = 0.09 m², R = 1 m²: σ grows during the gap and drops at the first new observation', loc='left')
    save(fig, 'l4_gap')

    # covariance ellipses pos-vel example
    def ell(ax, P, col, lab, ls='-'):
        vals, vecs = np.linalg.eigh(P)
        ang = np.degrees(np.arctan2(vecs[1, 1], vecs[0, 1]))
        e = Ellipse((0, 0), 2 * np.sqrt(vals[1]), 2 * np.sqrt(vals[0]), angle=ang, fill=False, ec=col, lw=1.8, ls=ls, label=lab)
        ax.add_patch(e)
    fig, ax = plt.subplots(figsize=(3.4, 2.9))
    rng = np.random.default_rng(1)
    Pm = np.array([[2.025, 1.05], [1.05, 1.1]])
    s = rng.multivariate_normal([0, 0], Pm, 250)
    ax.scatter(s[:, 0], s[:, 1], s=4, color=C['blue'], alpha=0.35, lw=0)
    ell(ax, np.eye(2), C['faint'], 'P₀⁺ = I', '--')
    ell(ax, Pm, C['blue'], 'P⁻ (after predict)')
    ell(ax, np.array([[0.2225, 0.1154], [0.1154, 0.6154]]), C['green'], 'P⁺ (after z = 1.5 m)')
    ax.set_xlim(-3.6, 3.6); ax.set_ylim(-3.2, 3.2); ax.set_aspect('equal')
    ax.set_xlabel('position error [m]'); ax.set_ylabel('velocity error [m/s]')
    ax.legend(loc='upper left', fontsize=7)
    ax.set_title('1σ ellipses: the tilt is the cross-covariance', loc='left', fontsize=8.6)
    save(fig, 'l4_ellipse')

    # bias: confident but wrong
    fig, ax = plt.subplots(figsize=(3.3, 2.9))
    P, x = 4.0, 10.0
    xs, ss = [x], [2.0]
    for k in range(40):
        Kk = P / (P + 0.04)
        x = x + Kk * (12 - x); P = (1 - Kk) * P
        xs.append(x); ss.append(np.sqrt(P))
    xs, ss = np.array(xs), np.array(ss)
    kk = np.arange(41)
    ax.fill_between(kk, xs - ss, xs + ss, color=C['green'], alpha=0.2, lw=0)
    ax.plot(kk, xs, color=C['green'], label='estimate ± σ')
    ax.axhline(10, color=C['text'], lw=1.2, label='true position')
    ax.axhline(12, color=C['orange'], lw=1, ls='--', label='every observation')
    ax.set_xlabel('number of observations'); ax.set_ylabel('position [m]')
    ax.set_ylim(7.6, 12.8); ax.legend(loc='lower right', fontsize=7)
    ax.set_title('σ → 0.03 m, error stays 2 m', loc='left', fontsize=8.6)
    save(fig, 'l4_bias')

    # identifiability of position and bias
    fig, ax = plt.subplots(figsize=(3.3, 2.9))
    pp = np.linspace(8, 12, 50)
    ax.plot(pp, 12 - pp, color=C['blue'], label='z = p + b = 12 m')
    ax.axvline(10, color=C['green'], lw=1.6, label='extra sensor: p = 10 m')
    ax.plot([10], [2], 'o', color=C['amber'], ms=6)
    ax.plot([11], [1], 'o', color=C['faint'], ms=6)
    ax.text(10.12, 2.15, 'A (10, 2)', color=C['amber'], fontsize=8)
    ax.text(11.1, 1.15, 'B (11, 1)', color=C['muted'], fontsize=8)
    ax.set_xlabel('position p [m]'); ax.set_ylabel('bias b [m]'); ax.set_ylim(0, 4.2)
    ax.legend(loc='upper right', fontsize=7)
    ax.set_title('Every point on the line fits z', loc='left', fontsize=8.6)
    save(fig, 'l4_ident')


# =========================================================== Lecture 6
def l6_figs():
    h = lambda p: np.sqrt(p ** 2 + 1)
    fig, axs = plt.subplots(1, 2, figsize=(6.8, 2.75), gridspec_kw=dict(wspace=0.28, width_ratios=[1.1, 1]))
    ax = axs[0]
    p = np.linspace(-1.0, 3.0, 300)
    ax.plot(p, h(p), color=C['blue'], label='h(p) = √(p² + 1)')
    ax.plot(p, np.sqrt(2) + (p - 1) / np.sqrt(2), color=C['orange'], lw=1.1, ls='--', label='EKF tangent at p̂ = 1')
    chi = np.array([0, 1, 2.0])
    ax.plot(chi, h(chi), 'o', color=C['green'], ms=6, label='sigma points χ = 0, 1, 2')
    for c_ in chi:
        ax.plot([c_, c_], [0.4, h(c_)], color=C['green'], lw=0.6, ls=':')
    pg = np.linspace(-1, 3, 200)
    ax.fill_between(pg, 0.4, 0.4 + 0.9 * np.exp(-(pg - 1) ** 2 / 1.0) / np.sqrt(np.pi), color=C['violet'], alpha=0.35, lw=0)
    ax.text(1.75, 0.62, 'p ~ N(1, 0.5)', color=C['violet'], fontsize=7.6)
    ax.set_xlim(-1, 3); ax.set_ylim(0.4, 3.2)
    ax.set_xlabel('robot position p [m]'); ax.set_ylabel('predicted range ρ [m]')
    ax.legend(loc='upper left', fontsize=7.2)
    ax.set_title('Nonlinear observation of an uncertain state', loc='left')
    ax = axs[1]
    rng = np.random.default_rng(0)
    smp = h(rng.normal(1, np.sqrt(0.5), 300000))
    ax.hist(smp, bins=120, range=(0.9, 3.4), density=True, color=C['faint'], alpha=0.55, label='Monte Carlo (truth)')
    r = np.linspace(0.6, 3.4, 400)
    for m, var, col, lab in ((np.sqrt(2), 0.25, C['orange'], 'EKF  mean 1.414, var 0.250'),
                             (1.5161, 0.2014, C['green'], 'UKF  mean 1.516, var 0.201')):
        ax.plot(r, np.exp(-(r - m) ** 2 / (2 * var)) / np.sqrt(2 * np.pi * var), color=col, lw=1.6, label=lab)
    ax.axvline(1.5169, color=C['text'], lw=0.8, ls=':')
    ax.set_xlabel('predicted range ρ [m]'); ax.set_yticks([]); ax.set_ylim(0, 1.75)
    ax.legend(loc='upper right', fontsize=6.9)
    ax.set_title('E[h(p)] = 1.517 ≠ h(E[p]) = 1.414', loc='left')
    save(fig, 'l6_ekf_ukf')

    # EKF tracking simulation
    rng = np.random.default_rng(4)
    dt, n = 0.2, 150
    L = np.array([[-1.5, -1.5], [7.5, -1.5], [7.5, 9.0], [-1.5, 9.0]])
    sr, sp = 0.15, 0.04
    sv, sw = 0.06, 0.03

    def f(x, u):
        return np.array([x[0] + u[0] * dt * np.cos(x[2]), x[1] + u[0] * dt * np.sin(x[2]), wrap(x[2] + u[1] * dt)])
    xt = np.array([3.0, 0.2, 0.0])
    xe = xt + np.array([0.15, -0.1, 0.05])
    xd = xe.copy()
    P = np.diag([0.04, 0.04, 0.01])
    Qm = np.diag([(sv * dt) ** 2, (sv * dt) ** 2, (sw * dt) ** 2]) * 2
    Rm = np.diag([sr ** 2, sp ** 2])
    T, E_, D, S = [xt.copy()], [xe.copy()], [xd.copy()], [P.copy()]
    for k in range(n):
        t_ = k * dt
        u = np.array([1.0, 0.28 + 0.12 * np.sin(0.15 * t_)])
        xt = f(xt, u)
        um = u + rng.normal(0, [sv, sw]) + np.array([0.0, 0.025])
        xd = f(xd, um)
        th = xe[2]
        F = np.array([[1, 0, -um[0] * dt * np.sin(th)], [0, 1, um[0] * dt * np.cos(th)], [0, 0, 1]])
        xe = f(xe, um)
        P = F @ P @ F.T + Qm
        for l in L:
            dx, dy = l - xt[:2]
            z = np.array([np.hypot(dx, dy) + rng.normal(0, sr), wrap(np.arctan2(dy, dx) - xt[2] + rng.normal(0, sp))])
            dx, dy = l - xe[:2]
            q = dx * dx + dy * dy
            rho = np.sqrt(q)
            zh = np.array([rho, wrap(np.arctan2(dy, dx) - xe[2])])
            H = np.array([[-dx / rho, -dy / rho, 0], [dy / q, -dx / q, -1]])
            Sm = H @ P @ H.T + Rm
            K = P @ H.T @ np.linalg.inv(Sm)
            nu = z - zh
            nu[1] = wrap(nu[1])
            xe = xe + K @ nu
            xe[2] = wrap(xe[2])
            IKH = np.eye(3) - K @ H
            P = IKH @ P @ IKH.T + K @ Rm @ K.T
        T.append(xt.copy()); E_.append(xe.copy()); D.append(xd.copy()); S.append(P.copy())
    T, E_, D, S = map(np.array, (T, E_, D, S))
    fig, axs = plt.subplots(1, 2, figsize=(6.9, 2.9), gridspec_kw=dict(wspace=0.3, width_ratios=[1, 1.25]))
    ax = axs[0]
    ax.plot(T[:, 0], T[:, 1], color=C['text'], lw=2.4, alpha=0.6, label='truth')
    ax.plot(D[:, 0], D[:, 1], color=C['faint'], lw=1.1, ls='--', label='prediction only')
    ax.plot(E_[:, 0], E_[:, 1], color=C['rose'], lw=1.2, label='EKF')
    ax.plot(L[:, 0], L[:, 1], '*', color=C['amber'], ms=8, label='landmarks')
    ax.set_aspect('equal'); ax.set_xlabel('x [m]'); ax.set_ylabel('y [m]')
    ax.legend(loc='upper center', fontsize=6.6, ncol=2, bbox_to_anchor=(0.5, -0.2))
    ax.set_title('Range–bearing EKF, Δt = 0.2 s', loc='left')
    ax = axs[1]
    tt = np.arange(n + 1) * dt
    sig = np.sqrt(S[:, 0, 0])
    ax.fill_between(tt, -2 * sig, 2 * sig, color=C['faint'], alpha=0.3, lw=0, label='±2σ from P')
    ax.plot(tt, E_[:, 0] - T[:, 0], color=C['rose'], lw=1.1, label='x error (EKF)')
    ax.set_xlabel('time [s]'); ax.set_ylabel('error [m]'); ax.set_ylim(-0.3, 0.3)
    ax.legend(loc='lower right', fontsize=7)
    ax.set_title('A consistent filter: the error stays in the band', loc='left')
    save(fig, 'l6_track')

    # pose graph before / after
    def compose(xa, z):
        c, s_ = np.cos(xa[2]), np.sin(xa[2])
        return np.array([xa[0] + c * z[0] - s_ * z[1], xa[1] + s_ * z[0] + c * z[1], wrap(xa[2] + z[2])])

    def hrel(xa, xb):
        c, s_ = np.cos(xa[2]), np.sin(xa[2])
        dp = xb[:2] - xa[:2]
        return np.array([c * dp[0] + s_ * dp[1], -s_ * dp[0] + c * dp[1], wrap(xb[2] - xa[2])])
    Z = {(0, 1): [2.2, 0, 1.6581], (1, 2): [2.1, 0, 2.4435], (2, 3): [2.9, 0, 2.3562], (0, 3): [0, 0, 0]}
    SIG = {e: np.array([0.05, 0.05, 0.03491] if e == (0, 3) else [0.15, 0.15, 0.08727]) for e in Z}
    X0 = [np.zeros(3)]
    for e in [(0, 1), (1, 2), (2, 3)]:
        X0.append(compose(X0[-1], Z[e]))
    X0 = np.array(X0)

    def res(Xf):
        Xa = np.vstack([np.zeros(3), Xf.reshape(3, 3)])
        out = []
        for (a, b), z in Z.items():
            r = np.array(z) - hrel(Xa[a], Xa[b]); r[2] = wrap(r[2]); out.append(r / SIG[(a, b)])
        return np.concatenate(out)
    Xf = X0[1:].ravel().copy()
    costs = [0.5 * res(Xf) @ res(Xf)]
    for it in range(4):
        J = np.zeros((12, 9)); r0 = res(Xf)
        for j in range(9):
            Xp = Xf.copy(); Xp[j] += 1e-7; J[:, j] = (res(Xp) - r0) / 1e-7
        Xf = Xf + np.linalg.solve(J.T @ J, -J.T @ r0)
        costs.append(0.5 * res(Xf) @ res(Xf))
    X1 = np.vstack([np.zeros(3), Xf.reshape(3, 3)])
    fig, axs = plt.subplots(1, 3, figsize=(7.0, 2.5), gridspec_kw=dict(wspace=0.42, width_ratios=[1.2, 0.9, 0.9]))
    ax = axs[0]
    for X, col, lab, lw in ((X0, C['faint'], 'initial (odometry chain)', 1.2), (X1, C['rose'], 'optimized', 1.8)):
        ax.plot(X[:, 0], X[:, 1], '-o', color=col, lw=lw, ms=4, label=lab)
        for i, x in enumerate(X):
            ax.plot([x[0], x[0] + 0.32 * np.cos(x[2])], [x[1], x[1] + 0.32 * np.sin(x[2])], color=col, lw=1)
    ax.plot([X0[3, 0], 0], [X0[3, 1], 0], color=C['amber'], lw=1, ls=':')
    for i, x in enumerate(X1):
        ax.text(x[0] + 0.09, x[1] + 0.12, str(i), color=C['text'], fontsize=8)
    ax.text(0.45, -0.62, 'loop closure 0–3 pulls\npose 3 back to the start', color=C['amber'], fontsize=7.2)
    ax.set_aspect('equal'); ax.set_xlabel('x [m]'); ax.set_ylabel('y [m]')
    ax.set_xlim(-0.6, 2.8); ax.set_ylim(-0.9, 2.5)
    ax.legend(loc='upper left', fontsize=6.6)
    ax.set_title('Trajectory', loc='left')
    ax = axs[1]
    ax.semilogy(range(len(costs)), costs, '-o', color=C['rose'], ms=4)
    ax.set_xlabel('Gauss–Newton iteration'); ax.set_ylabel('cost Φ')
    ax.text(0.6, 20, '53.6 → 0.91 → 0.90', color=C['muted'], fontsize=7.4)
    ax.set_title('Cost', loc='left')
    ax = axs[2]
    rr = res(Xf)
    contrib = [0.5 * rr[3 * i:3 * i + 3] @ rr[3 * i:3 * i + 3] for i in range(4)]
    ax.bar(['01', '12', '23', '03'], contrib, color=[C['blue'], C['blue'], C['blue'], C['amber']], width=0.6)
    ax.set_xlabel('edge'); ax.set_ylabel('cost after optimization')
    ax.set_title('Error is spread out', loc='left')
    save(fig, 'l6_pgo')

    # map before / after (illustrative wall)
    wall = np.vstack([np.column_stack([np.linspace(-0.5, 3.2, 26), np.full(26, 3.0)]),
                      np.column_stack([np.full(24, 3.2), np.linspace(2.85, -0.6, 24)])])
    fig, axs = plt.subplots(1, 2, figsize=(6.6, 2.7), gridspec_kw=dict(wspace=0.18))
    cols = [C['blue'], C['green'], C['amber'], C['rose']]
    for ax, X, ttl in ((axs[0], X0, 'Map from the initial poses'), (axs[1], X1, 'Map from the optimized poses')):
        ax.plot(wall[:26, 0], wall[:26, 1], color=C['faint'], lw=3, alpha=0.5)
        ax.plot(wall[26:, 0], wall[26:, 1], color=C['faint'], lw=3, alpha=0.5)
        for i in range(4):
            c, s_ = np.cos(X1[i, 2]), np.sin(X1[i, 2])
            Rt = np.array([[c, -s_], [s_, c]])
            sens = (Rt.T @ (wall - X1[i, :2]).T).T + np.random.default_rng(i).normal(0, 0.015, wall.shape)
            c, s_ = np.cos(X[i, 2]), np.sin(X[i, 2])
            Rm_ = np.array([[c, -s_], [s_, c]])
            m = (Rm_ @ sens.T).T + X[i, :2]
            ax.plot(m[::2, 0], m[::2, 1], '.', color=cols[i], ms=3.2, label='from pose %d' % i)
        ax.set_aspect('equal'); ax.set_xlim(-0.9, 4.1); ax.set_ylim(-1.0, 3.6)
        ax.set_title(ttl, loc='left'); ax.set_xlabel('x [m]')
    axs[0].set_ylabel('y [m]')
    axs[1].legend(loc='lower left', fontsize=6.6, ncol=2)
    save(fig, 'l6_map')

    # sparsity
    fig, axs = plt.subplots(1, 2, figsize=(5.4, 2.5), gridspec_kw=dict(wspace=0.35, width_ratios=[0.8, 1]))
    J = np.zeros((12, 9))
    J[0:3, 0:3] = 1; J[3:6, 0:6] = 1; J[6:9, 3:9] = 1; J[9:12, 6:9] = 1
    for ax, M, ttl in ((axs[0], J, 'J  (12 × 9)'), (axs[1], (J.T @ J) > 0, 'JᵀJ  (9 × 9)')):
        ax.imshow(np.where(M > 0, 1.0, 0.0), cmap=matplotlib.colors.ListedColormap(['#1c2230', C['rose']]), aspect='equal')
        ax.set_xticks(np.arange(-0.5, M.shape[1], 3)); ax.set_yticks(np.arange(-0.5, M.shape[0], 3))
        ax.set_xticklabels([]); ax.set_yticklabels([])
        ax.grid(True, color=C['spine'], lw=1)
        ax.set_title(ttl, loc='left')
    axs[0].set_ylabel('edges 01 · 12 · 23 · 03', fontsize=7.6)
    axs[0].set_xlabel('pose 1 · 2 · 3', fontsize=7.6)
    axs[1].set_xlabel('pose 1 · 2 · 3', fontsize=7.6)
    save(fig, 'l6_sparsity')


# =========================================================== Lecture 7
def l7_figs():
    # GD (exact line search) vs Newton on an ill-conditioned quadratic
    Hq = np.diag([2.0, 20.0])
    xs = np.array([1.0, 2.0])
    f = lambda X, Y: (X - 1) ** 2 + 10 * (Y - 2) ** 2
    x = np.array([-3.0, 0.6])
    path = [x.copy()]
    for _ in range(14):
        g = Hq @ (x - xs)
        a = g @ g / (g @ Hq @ g)
        x = x - a * g
        path.append(x.copy())
    path = np.array(path)
    fig, ax = plt.subplots(figsize=(6.6, 2.7))
    X, Y = np.meshgrid(np.linspace(-3.6, 2.6, 300), np.linspace(0.2, 3.4, 200))
    ax.contour(X, Y, f(X, Y), levels=[0.3, 1, 2.5, 5, 9, 14, 20, 28], colors=C['faint'], linewidths=0.7)
    ax.plot(path[:, 0], path[:, 1], '-o', color=C['rose'], ms=3, lw=1.2, label='gradient descent (exact line search)')
    ax.plot([-3, 1], [0.6, 2], '-', color=C['green'], lw=2, label='Newton: one step')
    ax.plot([1], [2], '*', color=C['amber'], ms=11, label='minimum (1, 2)')
    ax.set_aspect('equal'); ax.set_xlabel('x₁'); ax.set_ylabel('x₂')
    ax.legend(loc='lower right', fontsize=7.4)
    ax.set_title('f = (x₁−1)² + 10(x₂−2)²: curvature differs 10× by direction → zigzag', loc='left')
    save(fig, 'l7_gd_newton')

    # Armijo backtracking illustration
    al = np.linspace(0, 1.3, 400)
    phi = lambda a: 1 - 2 * a + 2.4 * a ** 2 - 0.25 * a ** 3
    dphi0 = -2.0
    c1 = 0.3
    fig, ax = plt.subplots(figsize=(6.6, 2.6))
    ok = phi(al) <= phi(0) + c1 * al * dphi0
    ax.fill_between(al, -0.1, 1.35, where=ok, color=C['green'], alpha=0.13, lw=0)
    ax.plot(al, phi(al), color=C['blue'], label='φ(α) = f(xₖ + α dₖ)')
    ax.plot(al, phi(0) + al * dphi0, color=C['faint'], ls=':', lw=1, label=r'tangent  $f+\alpha\,\nabla f^{T}d$')
    ax.plot(al, phi(0) + c1 * al * dphi0, color=C['amber'], ls='--', lw=1.2, label=r'Armijo line  $f+c_1\alpha\,\nabla f^{T}d$')
    for a, lab in ((1.0, 'α = 1 rejected'), (0.5, 'α = 0.5 accepted')):
        col = C['rose'] if a == 1.0 else C['green']
        ax.plot([a], [phi(a)], 'o', color=col, ms=5)
        ax.annotate(lab, xy=(a, phi(a)), xytext=(a + 0.06, phi(a) - 0.32), color=col, fontsize=8,
                    arrowprops=dict(arrowstyle='->', color=col, lw=0.8))
    ax.set_xlim(0, 1.3); ax.set_ylim(-0.1, 1.35)
    ax.set_xlabel('step size α'); ax.set_ylabel('objective')
    ax.legend(loc='upper center', fontsize=7.4, ncol=3, bbox_to_anchor=(0.5, 1.12))
    ax.text(0.02, 0.0, 'green band: α that pass the Armijo test (c₁ = 0.3)', color=C['green'], fontsize=7.6)
    save(fig, 'l7_armijo')

    # curvature: PD vs saddle
    fig, axs = plt.subplots(1, 2, figsize=(6.4, 2.6), gridspec_kw=dict(wspace=0.2))
    X, Y = np.meshgrid(np.linspace(-2, 2, 200), np.linspace(-2, 2, 200))
    for ax, F, ttl, lv in ((axs[0], X ** 2 + 2 * Y ** 2, r'$H = \mathrm{diag}(2,4) \succ 0$ : minimum', np.linspace(0.25, 8, 9)),
                           (axs[1], X ** 2 - Y ** 2, 'H = diag(2, −2) indefinite : saddle', np.linspace(-3.5, 3.5, 15))):
        cs = ax.contour(X, Y, F, levels=lv, cmap=matplotlib.colors.LinearSegmentedColormap.from_list('m', [C['violet'], C['cyan'], C['amber']]), linewidths=0.9)
        ax.plot([0], [0], 'o', color=C['text'], ms=4)
        ax.set_aspect('equal'); ax.set_xticks([]); ax.set_yticks([])
        ax.set_title(ttl, loc='left')
    axs[1].annotate('', xy=(0, 1.6), xytext=(0, 0.15), arrowprops=dict(arrowstyle='->', color=C['rose'], lw=1.2))
    axs[1].text(0.12, 1.3, 'f decreases', color=C['rose'], fontsize=7.6)
    axs[1].annotate('', xy=(1.6, 0), xytext=(0.15, 0), arrowprops=dict(arrowstyle='->', color=C['green'], lw=1.2))
    axs[1].text(0.9, 0.15, 'f increases', color=C['green'], fontsize=7.6)
    save(fig, 'l7_curvature')

    # GD vs GN vs LM on exponential fit
    rng = np.random.default_rng(2)
    t = np.linspace(0, 4, 20)
    y = 2.0 * np.exp(-0.8 * t) + rng.normal(0, 0.02, t.size)

    def r(p):
        return p[0] * np.exp(p[1] * t) - y

    def J(p):
        e = np.exp(p[1] * t)
        return np.column_stack([e, p[0] * t * e])
    p0 = np.array([1.0, -3.0])
    hist = {}
    # gradient descent with backtracking
    p = p0.copy(); h = []
    for _ in range(60):
        rr = r(p); f0 = 0.5 * rr @ rr; h.append(f0)
        g = J(p).T @ rr; a = 1.0
        while 0.5 * r(p - a * g) @ r(p - a * g) > f0 - 1e-4 * a * g @ g:
            a *= 0.5
        p = p - a * g
    hist['Gradient descent + backtracking'] = h
    p = p0.copy(); h = []
    with np.errstate(all='ignore'):
        for _ in range(40):
            rr = r(p); h.append(0.5 * rr @ rr)
            Jk = J(p)
            try:
                p = p + np.linalg.solve(Jk.T @ Jk, -Jk.T @ rr)
            except np.linalg.LinAlgError:
                break
            if not np.all(np.isfinite(p)):
                break
    hist['Gauss–Newton (full steps)'] = h
    gn_hist = np.array(h)
    p = p0.copy(); h = []; eta = 1.0
    for _ in range(60):
        rr = r(p); f0 = 0.5 * rr @ rr; h.append(f0)
        Jk = J(p)
        if np.linalg.norm(Jk.T @ rr) < 1e-10:
            break
        for _try in range(40):
            d = np.linalg.solve(Jk.T @ Jk + eta * np.eye(2), -Jk.T @ rr)
            pred = f0 - 0.5 * (rr + Jk @ d) @ (rr + Jk @ d)
            act = f0 - 0.5 * r(p + d) @ r(p + d)
            if pred > 0 and act / pred > 0.25:
                p = p + d; eta = max(eta / 3, 1e-9); break
            eta *= 4
        else:
            break
    hist['Levenberg–Marquardt'] = h
    fig, axs = plt.subplots(1, 2, figsize=(6.8, 2.55), gridspec_kw=dict(wspace=0.3, width_ratios=[1, 1.2]))
    ax = axs[0]
    ax.plot(t, y, 'o', color=C['text'], ms=3, label='data')
    tt = np.linspace(0, 4, 100)
    ax.plot(tt, p[0] * np.exp(p[1] * tt), color=C['green'], label='fit  %.2f·e^(%.2f t)' % (p[0], p[1]))
    ax.plot(tt, p0[0] * np.exp(p0[1] * tt), color=C['faint'], ls='--', label='initial guess')
    ax.set_xlabel('t'); ax.set_ylabel('y'); ax.legend(loc='upper right', fontsize=7.2); ax.set_ylim(-0.1, 2.6)
    ax.set_title('Fit y = a·e^(b t)', loc='left')
    ax = axs[1]
    top = 3e3
    for (lab, hh), col in zip(hist.items(), (C['amber'], C['rose'], C['green'])):
        hh = np.minimum(np.maximum(hh, 1e-6), top)
        ax.semilogy(range(len(hh)), hh, '-o', ms=2.4, color=col, lw=1.2, label=lab)
    ax.set_xlabel('iteration'); ax.set_ylabel('cost ½‖r‖²'); ax.set_xlim(-1, 32); ax.set_ylim(1e-3, 2e4)
    ax.legend(loc='upper right', fontsize=6.8)
    ax.annotate('GN overshoots: cost %.0e' % gn_hist[1], xy=(1, top), xytext=(4, 2.5e2), color=C['rose'], fontsize=7.4,
                arrowprops=dict(arrowstyle='->', color=C['rose'], lw=0.8))
    ax.text(14, 12, 'GN stalls at a wrong fit (cost %.1f)' % gn_hist[-1], color=C['rose'], fontsize=7.4)
    ax.set_title('Same start (a, b) = (1, −3)', loc='left')
    save(fig, 'l7_lm')
    print('    LM final', p, 'GN len', len(gn_hist), 'GN first/last', gn_hist[:3], gn_hist[-2:])

    # Lagrange / KKT geometry
    fig, axs = plt.subplots(1, 2, figsize=(6.6, 2.85), gridspec_kw=dict(wspace=0.15))
    X, Y = np.meshgrid(np.linspace(-1.6, 2.6, 300), np.linspace(-1.5, 2.0, 260))
    th = np.linspace(0, 2 * np.pi, 300)
    for ax, ctr, ttl in ((axs[0], (2, 1), 'Active: minimum on the boundary, μ > 0'),
                         (axs[1], (0.3, 0.2), 'Inactive: interior minimum, μ = 0')):
        F = (X - ctr[0]) ** 2 + (Y - ctr[1]) ** 2
        ax.contour(X, Y, F, levels=[0.05, 0.3, 0.8, 1.5, 2.5, 3.8, 5.5], colors=C['faint'], linewidths=0.7)
        ax.fill(np.cos(th), np.sin(th), color=C['green'], alpha=0.10)
        ax.plot(np.cos(th), np.sin(th), color=C['green'], lw=1.4)
        ax.plot([ctr[0]], [ctr[1]], 'x', color=C['muted'], ms=5)
        ax.set_aspect('equal'); ax.set_xticks([]); ax.set_yticks([]); ax.grid(False)
        ax.set_xlim(-1.6, 2.6); ax.set_ylim(-1.5, 2.0)
        ax.set_title(ttl, loc='left')
        ax.text(-1.45, -1.35, 'g(x) = ‖x‖² − 1 ≤ 0', color=C['green'], fontsize=7.6)
    xo = np.array([2, 1]) / np.sqrt(5)
    ax = axs[0]
    ax.plot(*xo, 'o', color=C['amber'], ms=5)
    gf = 2 * (xo - np.array([2, 1]))
    gg = 2 * xo
    ax.add_patch(FancyArrowPatch(xo, xo + 0.42 * gg, arrowstyle='->', mutation_scale=10, color=C['green'], lw=1.4))
    ax.add_patch(FancyArrowPatch(xo, xo + 0.30 * gf, arrowstyle='->', mutation_scale=10, color=C['rose'], lw=1.4))
    ax.text(xo[0] + 0.62, xo[1] + 0.30, r'$\nabla g$', color=C['green'], fontsize=9.5)
    ax.text(xo[0] - 0.95, xo[1] - 0.62, r'$\nabla f$', color=C['rose'], fontsize=9.5)
    ax.text(0.15, 1.62, r'$\nabla f + \mu\,\nabla g = 0,\ \ \mu = 1.24$', color=C['text'], fontsize=9)
    ax.text(xo[0] + 0.08, xo[1] - 0.22, r'$x^{*}$', color=C['amber'], fontsize=9.5)
    ax = axs[1]
    ax.plot([0.3], [0.2], 'o', color=C['amber'], ms=5)
    ax.text(0.38, 0.28, r'$x^{*}:\ \nabla f = 0$', color=C['amber'], fontsize=9.5)
    save(fig, 'l7_kkt')

    # convexity
    fig, axs = plt.subplots(1, 2, figsize=(6.2, 2.25), gridspec_kw=dict(wspace=0.25))
    xx = np.linspace(-1.6, 2.2, 200)
    fx = lambda x: 0.5 * x ** 2 + 0.3
    ax = axs[0]
    ax.plot(xx, fx(xx), color=C['blue'])
    a, b = -1.2, 1.8
    ax.plot([a, b], [fx(a), fx(b)], color=C['amber'], lw=1.3)
    tm = 0.35
    xm = (1 - tm) * a + tm * b
    ax.plot([xm, xm], [fx(xm), (1 - tm) * fx(a) + tm * fx(b)], color=C['faint'], ls=':')
    ax.plot([a, b], [fx(a), fx(b)], 'o', color=C['amber'], ms=4)
    ax.text(0.15, 1.75, 'chord above the graph', color=C['amber'], fontsize=8)
    ax.set_xticks([]); ax.set_yticks([]); ax.set_title('f((1−t)x + t y) ≤ (1−t)f(x) + t f(y)', loc='left', fontsize=8.4)
    ax = axs[1]
    ax.plot(xx, fx(xx), color=C['blue'])
    x0 = 0.9
    ax.plot(xx, fx(x0) + x0 * (xx - x0), color=C['green'], lw=1.2)
    ax.plot([x0], [fx(x0)], 'o', color=C['green'], ms=4)
    ax.text(-1.5, 1.6, 'tangent below the graph', color=C['green'], fontsize=8)
    ax.set_xticks([]); ax.set_yticks([]); ax.set_title(r'$f(y) \geq f(x) + \nabla f(x)^{T}(y-x)$', loc='left', fontsize=9.4)
    save(fig, 'l7_convex')


# =========================================================== cover art
def cover_figs():
    """Decorative SVG: drifting odometry vs estimated path, growing/shrinking uncertainty."""
    W, H = 680, 360
    s = np.linspace(0, 1, 400)
    x = 50 + 590 * s
    y = 300 - 230 * (3 * s ** 2 - 2 * s ** 3) - 28 * np.sin(2 * np.pi * 1.4 * s) * s * (1 - s) * 4
    dx, dy = np.gradient(x), np.gradient(y)
    out = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d">' % (W, H, W, H)]
    out.append('<defs><linearGradient id="pg" x1="0" x2="1"><stop offset="0" stop-color="#60a5fa" stop-opacity=".25"/>'
               '<stop offset=".5" stop-color="#22d3ee"/><stop offset="1" stop-color="#a78bfa"/></linearGradient>'
               '<radialGradient id="glow"><stop offset="0" stop-color="#fbbf24" stop-opacity=".55"/>'
               '<stop offset="1" stop-color="#fbbf24" stop-opacity="0"/></radialGradient></defs>')
    for gx in range(20, W, 34):
        for gy in range(16, H, 34):
            out.append('<circle cx="%d" cy="%d" r="1" fill="#3a4560" opacity=".55"/>' % (gx, gy))
    # drifting odometry (dashed)
    drift = np.column_stack([x, y]) + np.column_stack([-40 * s ** 2, 70 * s ** 2])
    out.append('<path d="M%s" fill="none" stroke="#fb923c" stroke-width="1.6" stroke-dasharray="5 5" opacity=".55"/>'
               % ' L'.join('%.1f %.1f' % tuple(p) for p in drift[::4]))
    out.append('<path d="M%s" fill="none" stroke="url(#pg)" stroke-width="3" stroke-linecap="round"/>'
               % ' L'.join('%.1f %.1f' % p for p in zip(x[::2], y[::2])))
    lms = [(300, 70), (560, 230)]
    obs = {0.47: lms[0], 0.80: lms[1]}
    for (lx, ly) in lms:
        out.append('<circle cx="%d" cy="%d" r="22" fill="url(#glow)"/>' % (lx, ly))
        pts = []
        for k in range(10):
            r_ = 9 if k % 2 == 0 else 4
            a = -np.pi / 2 + k * np.pi / 5
            pts.append('%.1f,%.1f' % (lx + r_ * np.cos(a), ly + r_ * np.sin(a)))
        out.append('<polygon points="%s" fill="#fbbf24"/>' % ' '.join(pts))
    sig = 5.0
    for sv in np.arange(0.06, 0.99, 0.09):
        i = int(sv * 399)
        ang = np.degrees(np.arctan2(dy[i], dx[i]))
        for so, lm in obs.items():
            if abs(sv - so) < 0.046:
                out.append('<line x1="%.1f" y1="%.1f" x2="%d" y2="%d" stroke="#fbbf24" stroke-width="1.2" '
                           'stroke-dasharray="3 4" opacity=".8"/>' % (x[i], y[i], lm[0], lm[1]))
                sig = 6.0
        out.append('<ellipse cx="%.1f" cy="%.1f" rx="%.1f" ry="%.1f" transform="rotate(%.1f %.1f %.1f)" '
                   'fill="#a78bfa" fill-opacity=".10" stroke="#a78bfa" stroke-opacity=".75" stroke-width="1.2"/>'
                   % (x[i], y[i], sig * 1.0, sig * 1.7, ang, x[i], y[i]))
        tri = np.array([[9, 0], [-6, 5.5], [-6, -5.5]])
        c, s_ = np.cos(np.radians(ang)), np.sin(np.radians(ang))
        tp = tri @ np.array([[c, s_], [-s_, c]]) + [x[i], y[i]]
        out.append('<polygon points="%s" fill="#e5e9f0"/>' % ' '.join('%.1f,%.1f' % tuple(p) for p in tp))
        sig += 3.2
    # frame at start
    out.append('<line x1="50" y1="300" x2="105" y2="300" stroke="#fb7185" stroke-width="2.2"/>'
               '<polygon points="110,300 101,295 101,305" fill="#fb7185"/>'
               '<line x1="50" y1="300" x2="50" y2="245" stroke="#4ade80" stroke-width="2.2"/>'
               '<polygon points="50,240 45,249 55,249" fill="#4ade80"/>'
               '<text x="58" y="322" fill="#8a94a7" font-family="Segoe UI" font-size="12">map</text>')
    out.append('</svg>')
    (FIG / 'cover_art.svg').write_text(''.join(out), encoding='utf-8')
    print('  fig cover_art')


if __name__ == '__main__':
    import sys
    which = sys.argv[1:] or ['l2', 'l3', 'l3_epipolar_', 'l4', 'l6', 'l7', 'cover']
    for w in which:
        (globals()[w[:-1]] if w.endswith('_') else globals()[w + '_figs'])()
