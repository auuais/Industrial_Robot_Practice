# -*- coding: utf-8 -*-
"""Recompute every number used in the Lecture 10 notes (tracking control)."""
import math

import numpy as np

D = math.radians
G = 9.81


def hdr(s):
    print('\n==== ' + s)


def wrap(a):
    """(-pi, pi]"""
    a = (a + math.pi) % (2 * math.pi) - math.pi
    return math.pi if a == -math.pi else a


# ---------------------------------------------------------------- bicycle model
hdr('E1 bicycle model L=2.7, v=10, delta=5 deg')
L, v, dl = 2.7, 10.0, D(5)
psidot = v / L * math.tan(dl)
R = L / math.tan(dl)
print('psidot=%.4f rad/s (%.2f deg/s)  R=%.3f m  kappa=%.5f' % (psidot, math.degrees(psidot), R, 1 / R))
x = y = p = 0.0
for k in range(2):
    x, y, p = x + 0.1 * v * math.cos(p), y + 0.1 * v * math.sin(p), p + 0.1 * psidot
    print('  Euler step %d (dt=0.1): x=%.4f y=%.4f psi=%.4f' % (k + 1, x, y, p))
t = 1.0
ps = psidot * t
print('exact after 1 s: psi=%.4f rad x=%.4f y=%.4f' % (ps, R * math.sin(ps), R * (1 - math.cos(ps))))
print('time for 90 deg: %.3f s' % (math.pi / 2 / psidot))

# ---------------------------------------------------------------- path errors
hdr('E2 path errors: straight path along x, p=(5,0.8), psi=10 deg')
print('s*=5, e_y=0.8, e_psi=%.4f rad' % D(10))
print('wrap(179-(-179)) = %.2f deg' % math.degrees(wrap(D(179) - D(-179))))

# ---------------------------------------------------------------- pure pursuit
hdr('E3/E4 pure pursuit: car (2,1,30deg), goal (6,6), L=2.7')
xc, yc, ps = 2.0, 1.0, D(30)
Xg, Yg = 6.0, 6.0
dX, dY = Xg - xc, Yg - yc
xg = dX * math.cos(ps) + dY * math.sin(ps)
yg = -dX * math.sin(ps) + dY * math.cos(ps)
Ld = math.hypot(xg, yg)
al = math.atan2(yg, xg)
kap = 2 * yg / Ld ** 2
dlt = math.atan(2 * L * yg / Ld ** 2)
print('dX=%.1f dY=%.1f xg=%.4f yg=%.4f Ld=%.4f (sqrt41=%.4f) alpha=%.4f rad (%.3f deg)' % (
    dX, dY, xg, yg, Ld, math.sqrt(41), al, math.degrees(al)))
print('kappa=%.5f (check 2 sin a/Ld=%.5f) R=%.2f m delta=%.4f rad (%.3f deg)' % (
    kap, 2 * math.sin(al) / Ld, 1 / kap, dlt, math.degrees(dlt)))

hdr('E5 lookahead: v=10')
for Ldx in (5.0, 10.0, 20.0):
    wn = math.sqrt(2) * 10 / Ldx
    print('Ld=%4.1f wn=%.4f zeta=%.4f ts(2%%)=%.2f s  gains: e_y %.4f rad/m, e_psi %.4f' % (
        Ldx, wn, 1 / math.sqrt(2), 4 / (wn / math.sqrt(2)), 2 * L / Ldx ** 2, 2 * L / Ldx))
print('first undershoot for zeta=1/sqrt2: %.4f' % -math.exp(-math.pi))
print('delta for e_y=0.5, Ld=10: %.4f rad (%.3f deg)' % (-2 * L / 100 * 0.5, math.degrees(-2 * L / 100 * 0.5)))

# ---------------------------------------------------------------- stanley
hdr('E6 Stanley: rear axle (0,0.3) psi=5deg, v=5, k=1')
xr, yr, ps, v, k = 0.0, 0.3, D(5), 5.0, 1.0
xf, yf = xr + L * math.cos(ps), yr + L * math.sin(ps)
ef, epf = yf, ps
beta = math.atan(k * ef / v)
dcmd = -epf - beta
efd = -k * ef / (math.cos(dcmd) * math.sqrt(1 + (k * ef / v) ** 2))
efd2 = v / math.cos(dcmd) * math.sin(epf + dcmd)
print('front=(%.4f, %.4f) e_f=%.4f e_psi_f=%.4f beta=%.4f delta_cmd=%.4f rad (%.3f deg)' % (
    xf, yf, ef, epf, beta, dcmd, math.degrees(dcmd)))
print('e_f dot exact=%.4f (from kinematics %.4f), approx -k e_f=%.4f, v_f=%.4f' % (efd, efd2, -k * ef, v / math.cos(dcmd)))

# ---------------------------------------------------------------- longitudinal
hdr('E7 forces m=1500, v=20, rho=1.2, CD=0.3, A=2.2, Crr=0.012, theta=3deg')
m, v, rho, CD, A, Crr, th = 1500, 20.0, 1.2, 0.3, 2.2, 0.012, D(3)
Fa = 0.5 * rho * CD * A * v ** 2
Fr = Crr * m * G * math.cos(th)
Fg = m * G * math.sin(th)
Fres = Fa + Fr + Fg
print('F_aero=%.1f F_roll=%.1f F_grade=%.1f F_res=%.1f N power=%.2f kW  vdot(F=2000)=%.4f' % (
    Fa, Fr, Fg, Fres, Fres * v / 1000, (2000 - Fres) / m))
for vv in (10, 30):
    print('  at v=%d: F_aero=%.1f' % (vv, 0.5 * rho * CD * A * vv ** 2))

hdr('E8 PI kp=1, ki=0.25; d_a=-0.3')
kp, ki = 1.0, 0.25
wn = math.sqrt(ki)
print('wn=%.3f zeta=%.3f a_des(e=3,z=0)=%.2f  z_ss=-d_a/ki=%.3f  P-only e_ss=-d_a/kp=%.3f' % (
    wn, kp / (2 * wn), kp * 3, 0.3 / ki, 0.3 / kp))

hdr('E9 actuator map')
u = np.array([0.0, 0.2, 0.4])
a1 = np.array([-0.3, 0.8, 1.9])   # v1 = 10
a2 = np.array([-0.5, 0.5, 1.4])   # v2 = 20
lam = (14 - 10) / (20 - 10)
af = (1 - lam) * a1 + lam * a2
amap = 0.5 + G * math.sin(D(2))
j = int(np.searchsorted(af, amap)) - 1
ucmd = u[j] + (amap - af[j]) / (af[j + 1] - af[j]) * (u[j + 1] - u[j])
print('lambda=%.2f f(v)=%s a_map=%.4f bracket j=%d u_cmd=%.4f' % (lam, np.round(af, 3), amap, j, ucmd))

# ---------------------------------------------------------------- online estimation
hdr('E10 online estimation b=2, d=0.4, start (1.5, 0.2), Ts=0.05, Gamma=diag(2,2)')
b, d = 2.0, 0.4
th = np.array([1.5, 0.2])
Ts, Gm = 0.05, np.diag([2.0, 2.0])
alim = 1.0
print('u needed=%.3f, u with initial estimate=%.3f -> a=%.3f' % ((alim + d) / b, (alim + th[1]) / th[0],
                                                                   b * (alim + th[1]) / th[0] - d))
uu, eps = 0.5, None
phi = np.array([uu, -1.0])
am = b * uu - d
ah = phi @ th
eps = am - ah
step = Ts * Gm @ phi * eps
print('one step at u=0.5: a_meas=%.3f a_hat=%.3f eps=%.3f update=%s -> %s' % (am, ah, eps, np.round(step, 5),
                                                                             np.round(th + step, 5)))
def estimate(inp, gain, T=40.0):
    th = np.array([1.5, 0.2])
    hist = []
    for kk in range(int(T / Ts) + 1):
        tt = kk * Ts
        uu = inp(tt)
        phi = np.array([uu, -1.0])
        eps = (b * uu - d) - phi @ th
        if kk % int(10 / Ts) == 0:
            hist.append((round(tt), round(th[0], 3), round(th[1], 3)))
        th = th + Ts * gain * phi * eps
        th[0] = max(th[0], 0.5)
        th[1] = min(max(th[1], -1.0), 2.0)
    return hist


print('stepping input 0.2/0.8 every 1 s, Gamma=4I (t, b_hat, d_hat):',
      estimate(lambda tt: 0.8 if int(tt) % 2 == 0 else 0.2, 4.0))
print('slow sine 0.5+0.4 sin(0.8t), Gamma=10I:', estimate(lambda tt: 0.5 + 0.4 * math.sin(0.8 * tt), 10.0))
print('first step with Gamma=4I at u=0.8: eps=%.3f' % ((b * 0.8 - d) - (1.5 * 0.8 - 0.2)))

# ---------------------------------------------------------------- MRAC
hdr('E11 MRAC: vdot = b u - d, b=0.5, d=0.3, k=1, Gamma=0.5 I')
b, d, k = 0.5, 0.3, 1.0
Gm = 0.5 * np.eye(3)
ths = np.array([1 / b, k / b, d / b])
th = np.array([1.0, 1.0, 0.0])
dt, T = 0.001, 60.0
vv = 8.0
rows = []
for kk in range(int(T / dt) + 1):
    tt = kk * dt
    vr, vrd = 10 + 2 * math.sin(0.3 * tt), 0.6 * math.cos(0.3 * tt)
    e = vr - vv
    phi = np.array([vrd, e, 1.0])
    uin = th @ phi
    tl = th - ths
    V = 0.5 * e ** 2 + 0.5 * b * tl @ np.linalg.inv(Gm) @ tl
    if kk % int(10 / dt) == 0:
        rows.append((round(tt), round(e, 4), round(V, 4), np.round(th, 3).tolist()))
    vv += dt * (b * uin - d)
    th = th + dt * Gm @ phi * e
print('theta*=', np.round(ths, 3))
for r in rows:
    print('  t=%3d e=%8.4f V=%8.4f theta=%s' % r)

# ---------------------------------------------------------------- limits
hdr('E12 limits: hill hold and anti-windup')
m, gr = 1500, 0.10
th = math.atan(gr)
print('10%% grade: theta=%.3f deg, m g sin=%.1f N' % (math.degrees(th), m * G * math.sin(th)))
print('anti-windup zdot: e=4, a_des=3.5, a_lim=2, kaw=0.5 -> %.2f (no aw: 4)' % (4 + 0.5 * (2 - 3.5)))
print('jerk-limited ramp 0->2 m/s2 at jmax=2: %.1f s' % (2 / 2))

# ---------------------------------------------------------------- trajectory errors
hdr('E13/E14 trajectory errors: ref (10,3,30), actual (8,2,20)')
xr, yr, pr = 10.0, 3.0, D(30)
x, y, p = 8.0, 2.0, D(20)
dx, dy = xr - x, yr - y
ex = dx * math.cos(p) + dy * math.sin(p)
ey = -dx * math.sin(p) + dy * math.cos(p)
ep = pr - p
print('ex=%.4f ey=%.4f epsi=%.4f' % (ex, ey, ep))
vr, wr, v, w = 10.0, 0.1, 9.0, 0.12
print('exdot=%.4f eydot=%.4f epsidot=%.4f' % (vr * math.cos(ep) - v + w * ey, vr * math.sin(ep) - w * ex, wr - w))

hdr('E15 Kanayama kx=1, ky=0.1, kpsi=0.6, vr=10, wr=0.1')
kx, ky, kps = 1.0, 0.1, 0.6
vc = vr * math.cos(ep) + kx * ex
wc = wr + vr * (ky * ey + kps * math.sin(ep))
kc = wc / vc
dc = math.atan(L * kc)
kmax = math.tan(D(35)) / L
V = 0.5 * (ex ** 2 + ey ** 2) + (1 - math.cos(ep)) / ky
Vd = -kx * ex ** 2 - vr * kps / ky * math.sin(ep) ** 2
print('vc=%.4f wc=%.4f kappa_c=%.4f delta_c=%.3f deg  kappa_max(35deg)=%.4f  V=%.4f Vdot=%.4f' % (
    vc, wc, kc, math.degrees(dc), kmax, V, Vd))
hdr('E16 Kanayama start (0,-4,-30deg), straight ref x_r = 4t, kx=0.8, ky=0.1, kpsi=0.6')
p0 = D(-30)
ex0 = 0 * math.cos(p0) + 4 * math.sin(p0)
ey0 = -0 * math.sin(p0) + 4 * math.cos(p0)
ep0 = -p0
vc0 = 4 * math.cos(ep0) + 0.8 * ex0
wc0 = 4 * (0.1 * ey0 + 0.6 * math.sin(ep0))
print('ex=%.4f ey=%.4f epsi=%.1f deg V0=%.4f vc=%.4f wc=%.4f kappa_c=%.4f (R=%.3f) kappa_max=%.4f omega_max=%.4f' % (
    ex0, ey0, math.degrees(ep0), 0.5 * (ex0 ** 2 + ey0 ** 2) + (1 - math.cos(ep0)) / 0.1, vc0, wc0, wc0 / vc0,
    vc0 / wc0, kmax, vc0 * kmax))

# ---------------------------------------------------------------- practice
hdr('P1 L=2.5, v=8, delta=8deg')
pd = 8 / 2.5 * math.tan(D(8))
print('psidot=%.4f rad/s R=%.3f t90=%.3f s' % (pd, 2.5 / math.tan(D(8)), math.pi / 2 / pd))
hdr('P2 path heading 45 at (3,3), p=(2.5,4), psi=60')
nr = np.array([-math.sin(D(45)), math.cos(D(45))])
print('n_r=%s e_y=%.4f e_psi=15deg' % (np.round(nr, 4), nr @ np.array([2.5 - 3, 4 - 3])))
hdr('P3 wrap(-170-175)')
print('%.1f deg' % math.degrees(wrap(D(-170) - D(175))))
hdr('P4 PP car (0,0,90), goal (3,8)')
dX, dY, ps = 3.0, 8.0, D(90)
xg = dX * math.cos(ps) + dY * math.sin(ps)
yg = -dX * math.sin(ps) + dY * math.cos(ps)
Ld2 = xg ** 2 + yg ** 2
print('xg=%.4f yg=%.4f Ld=%.4f alpha=%.3f deg kappa=%.5f R=%.3f delta=%.3f deg' % (
    xg, yg, math.sqrt(Ld2), math.degrees(math.atan2(yg, xg)), 2 * yg / Ld2, Ld2 / (2 * yg),
    math.degrees(math.atan(2 * L * yg / Ld2))))
hdr('P5 lookahead v=15, wn=1')
print('Ld=%.3f m ts=%.3f s' % (math.sqrt(2) * 15 / 1.0, 4 / (1.0 / math.sqrt(2))))
hdr('P6 Stanley e_f=-0.4, e_psi_f=-3deg, v=8, k=1.5')
dlt = D(3) - math.atan(1.5 * -0.4 / 8)
print('delta=%.4f rad (%.3f deg) e_f dot approx=%.3f' % (dlt, math.degrees(dlt), -1.5 * -0.4))
hdr('P7 Stanley low speed v=0.5, e_f=0.4, k=1.5')
print('arctan term=%.2f deg' % math.degrees(math.atan(1.5 * 0.4 / 0.5)))
hdr('P8 forces m=1800, CDA=0.75, rho=1.2, Crr=0.01, v=25, theta=-2')
m, th = 1800, D(-2)
Fa = 0.5 * 1.2 * 0.75 * 625
Fr = 0.01 * m * G * math.cos(th)
Fg = m * G * math.sin(th)
print('F_aero=%.2f F_roll=%.2f F_grade=%.2f F_res=%.2f' % (Fa, Fr, Fg, Fa + Fr + Fg))
hdr('P9 PI wn=0.8 zeta=0.9')
print('ki=%.3f kp=%.3f' % (0.8 ** 2, 2 * 0.9 * 0.8))
hdr('P10 inverse lookup')
ut = np.array([0.0, 0.25, 0.5])
at = np.array([-0.4, 0.9, 2.1])
amap = 1.2 + G * math.sin(D(-3))
j = int(np.searchsorted(at, amap)) - 1
print('a_map=%.4f j=%d u=%.4f' % (amap, j, ut[j] + (amap - at[j]) / (at[j + 1] - at[j]) * (ut[j + 1] - ut[j])))
print('lambda for v=17 between 15 and 25: %.2f' % ((17 - 15) / 10))
hdr('P11 estimation step: b_hat=1.8, d_hat=0.5, u=0.6, a_meas=0.9, Ts=0.1, Gamma=diag(1,1)')
th = np.array([1.8, 0.5])
phi = np.array([0.6, -1.0])
ah = phi @ th
eps = 0.9 - ah
print('a_hat=%.3f eps=%.3f new=%s' % (ah, eps, np.round(th + 0.1 * phi * eps, 4)))
print('u_cmd for a_lim=1.0 with new estimate: %.4f' % ((1.0 + (th + 0.1 * phi * eps)[1]) / (th + 0.1 * phi * eps)[0]))
hdr('P14 hill hold m=2000, 15%')
th = math.atan(0.15)
print('theta=%.3f deg F=%.1f N' % (math.degrees(th), 2000 * G * math.sin(th)))
hdr('P15 traj error ref (5,5,90), actual (4,3,80)')
dx, dy, p = 1.0, 2.0, D(80)
print('ex=%.4f ey=%.4f' % (dx * math.cos(p) + dy * math.sin(p), -dx * math.sin(p) + dy * math.cos(p)))
hdr('P16 Kanayama kx=0.5 ky=0.2 kpsi=1 vr=6 wr=0.2, ex=1, ey=-0.5, epsi=-10deg, L=2.7, dmax=30')
ex, ey, ep = 1.0, -0.5, D(-10)
vc = 6 * math.cos(ep) + 0.5 * ex
wc = 0.2 + 6 * (0.2 * ey + 1.0 * math.sin(ep))
kc = wc / vc
print('vc=%.4f wc=%.4f kappa=%.4f delta=%.3f deg kmax=%.4f' % (vc, wc, kc, math.degrees(math.atan(L * kc)),
                                                              math.tan(D(30)) / L))
