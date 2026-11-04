# -*- coding: utf-8 -*-
"""Recompute every number used in the Lecture 9 notes (slide examples, extra examples, practice)."""
import math

import numpy as np

D2R = math.pi / 180


def hdr(s):
    print('\n==== ' + s)


# ---------------------------------------------------------------- reference circle (left turn)
def circle(R, s):
    th = s / R
    r = np.array([R * math.sin(th), R - R * math.cos(th)])
    t = np.array([math.cos(th), math.sin(th)])
    n = np.array([-math.sin(th), math.cos(th)])
    return r, t, n, th


hdr('E1 circle R=20, s=10*pi/3 (theta=30 deg)')
R = 20.0
s = 10 * math.pi / 3
r, t, n, th = circle(R, s)
print('s=%.4f theta=%.2f deg r=%s t=%s n=%s |t|=%.3f t.n=%.1e' % (s, th / D2R, r.round(4), t.round(4), n.round(4),
                                                                  np.linalg.norm(t), t @ n))
hdr('chord / arc on the R=20 circle')
for ds in (10, 5, 2, 0.5):
    chord = 2 * R * math.sin(ds / (2 * R))
    print('ds=%4.1f chord=%.4f ratio=%.6f angle(chord,tangent)=%.2f deg' % (ds, chord, chord / ds, ds / (2 * R) / D2R))

hdr('E2 Frenet -> Cartesian: (s,d)=(10pi/3, 1.5)')
p = r + 1.5 * n
print('p =', p.round(4), ' |p-c| =', round(np.linalg.norm(p - np.array([0, R])), 4), '= R - d =', R - 1.5)

hdr('E3a straight path at 30 deg, p=(8,6)')
t30 = np.array([math.cos(30 * D2R), math.sin(30 * D2R)])
n30 = np.array([-t30[1], t30[0]])
pp = np.array([8.0, 6.0])
print('s* = %.4f  d = %.4f' % (pp @ t30, pp @ n30))

hdr('E3b circle R=20, p=(12,6)')
c = np.array([0.0, R])
pp = np.array([12.0, 6.0])
u = (pp - c) / np.linalg.norm(pp - c)
rs = c + R * u
th = math.atan2(rs[0], R - rs[1])
_, ts, ns, _ = circle(R, R * th)
print('|p-c|=%.4f r*=%s theta=%.3f deg s*=%.4f d=%.4f (R-|p-c|=%.4f)' % (
    np.linalg.norm(pp - c), rs.round(4), th / D2R, R * th, (pp - rs) @ ns, R - np.linalg.norm(pp - c)))

# ---------------------------------------------------------------- quintic
def quintic(d0, v0, a0, dg, T):
    a = [d0, v0, a0 / 2]
    A = np.array([[T ** 3, T ** 4, T ** 5], [3 * T ** 2, 4 * T ** 3, 5 * T ** 4], [6 * T, 12 * T ** 2, 20 * T ** 3]])
    b = np.array([dg - a[0] - a[1] * T - a[2] * T ** 2, -a[1] - 2 * a[2] * T, -2 * a[2]])
    return np.array(a + list(np.linalg.solve(A, b))), A, b


def pev(c, t, k=0):
    p = np.polynomial.polynomial.Polynomial(c)
    for _ in range(k):
        p = p.deriv()
    return p(t)


hdr('E4 quintic d0=v0=a0=0, dg=2, T=4')
cq, A, b = quintic(0, 0, 0, 2, 4)
print('coeffs a0..a5 =', cq.round(8))
print('closed form a3,a4,a5 =', 10 * 2 / 4 ** 3, -15 * 2 / 4 ** 4, 6 * 2 / 4 ** 5)
ts_ = np.linspace(0, 4, 40001)
vel = pev(cq, ts_, 1)
acc = pev(cq, ts_, 2)
jer = pev(cq, ts_, 3)
print('max ddot=%.4f at t=%.3f   max |dddot|=%.4f at t=%.3f   jerk(0)=%.4f' % (
    vel.max(), ts_[vel.argmax()], np.abs(acc).max(), ts_[np.abs(acc).argmax()], jer[0]))
print('int jerk^2 = %.4f  (720 D^2/T^5 = %.4f)' % (np.trapz(jer ** 2, ts_), 720 * 4 / 4 ** 5))
for tt in (1, 2, 3):
    print('  d(%d)=%.4f' % (tt, pev(cq, tt)))

hdr('E4b general quintic d0=0.5, v0=0.4, a0=-0.2, dg=0, T=3')
cg, A, b = quintic(0.5, 0.4, -0.2, 0.0, 3.0)
print('A =\n', A, '\n b =', b)
print('coeffs =', cg.round(6))
print('check: d(T)=%.2e  v(T)=%.2e  a(T)=%.2e  d(0)=%.3f v(0)=%.3f a(0)=%.3f' % (
    pev(cg, 3), pev(cg, 3, 1), pev(cg, 3, 2), pev(cg, 0), pev(cg, 0, 1), pev(cg, 0, 2)))
tt = np.linspace(0, 3, 30001)
dd = pev(cg, tt)
print('min d=%.4f at t=%.3f (overshoot below 0?)  max |a|=%.4f' % (dd.min(), tt[dd.argmin()], np.abs(pev(cg, tt, 2)).max()))

# ---------------------------------------------------------------- longitudinal quartics (slide 10)
def quartic(v0, vT, T):
    b4 = (v0 - vT) / (2 * T ** 3)
    b3 = -2 * b4 * T
    return np.array([0, v0, 0, b3, b4])


hdr('E5 longitudinal velocity-keeping quartics v0=5, vT in {3,7}, T=4')
LON = {'decel': quartic(5, 3, 4), 'accel': quartic(5, 7, 4)}
for k, cl in LON.items():
    print(k, 'coeffs', cl, ' s(t)=', [round(pev(cl, x), 3) for x in (1, 2, 3, 4)],
          ' v(T)=%.3f a(T)=%.3e' % (pev(cl, 4, 1), pev(cl, 4, 2)))
LAT = {dT: quintic(0, 0, 0, dT, 4)[0] for dT in (-2.0, 0.0, 2.0)}
for dT, cl in LAT.items():
    print('lateral dT=%+.0f d(t)=%s' % (dT, [round(pev(cl, x), 4) for x in (1, 2, 3, 4)]))

# ---------------------------------------------------------------- Frenet kinematics example
hdr('E6-E8 kinematics: R=20 (kappa=0.05), theta_r=30, d=1.5, sd=10, dd=0.5, sdd=0.4, ddd=-0.2, kappa\'=0')
k, d, sd, ddot, sdd, dddot, kp = 0.05, 1.5, 10.0, 0.5, 0.4, -0.2, 0.0
vT, vN = (1 - k * d) * sd, ddot
aT = (1 - k * d) * sdd - kp * d * sd ** 2 - 2 * k * sd * ddot
aN = dddot + k * (1 - k * d) * sd ** 2
print('vT=%.4f vN=%.4f aT=%.4f aN=%.4f   check aN-ddd = vT^2/(R-d) = %.4f' % (vT, vN, aT, aN, vT ** 2 / (R - d)))
thr = 30 * D2R
xd = vT * math.cos(thr) - vN * math.sin(thr)
yd = vT * math.sin(thr) + vN * math.cos(thr)
xdd = aT * math.cos(thr) - aN * math.sin(thr)
ydd = aT * math.sin(thr) + aN * math.cos(thr)
v = math.hypot(vT, vN)
print('xdot=%.4f ydot=%.4f xddot=%.4f yddot=%.4f v=%.4f theta_p=%.4f deg (=30+%.4f)' % (
    xd, yd, xdd, ydd, v, math.degrees(math.atan2(yd, xd)), math.degrees(math.atan2(vN, vT))))
kap1 = (vT * aN - vN * aT) / (vT ** 2 + vN ** 2) ** 1.5
kap2 = (xd * ydd - yd * xdd) / (xd ** 2 + yd ** 2) ** 1.5
apar = (vT * aT + vN * aN) / v
aperp = v ** 2 * kap1
print('kappa_p=%.5f (cart %.5f) radius=%.3f  a_par=%.4f a_perp=%.4f  |a|=%.4f vs %.4f' % (
    kap1, kap2, 1 / kap1, apar, aperp, math.hypot(aT, aN), math.hypot(apar, aperp)))
print('v^3 = %.3f' % v ** 3)

hdr('E11 limits a_perp_max=3, kappa_max=0.2')
amax, kmax = 3.0, 0.2
print('v* = %.4f   allowed kappa at v=%.4f: %.5f   candidate a_perp=%.3f -> %s   max speed for its kappa: %.3f' % (
    math.sqrt(amax / kmax), v, amax / v ** 2, aperp, 'REJECT' if aperp > amax else 'ok', math.sqrt(amax / kap1)))

# ---------------------------------------------------------------- collision circles
def circles(L, W, n=3):
    seg = L / n
    r = math.hypot(seg / 2, W / 2)
    offs = [-L / 2 + seg * (i + 0.5) for i in range(n)]
    return r, offs


hdr('E9 circles 4.5 x 1.8, 3 circles')
rk, offs = circles(4.5, 1.8)
print('r_k=%.4f offsets=%s  lateral bulge=%.4f' % (rk, offs, rk - 0.9))
robs, m = 0.5, 0.2
thrd = rk + robs + m
cc, hd = np.array([10.0, 0.5]), 10 * D2R
o = np.array([12.5, 1.6])
for off in offs:
    ck = cc + off * np.array([math.cos(hd), math.sin(hd)])
    dist = np.linalg.norm(ck - o)
    print('  c=%s dist=%.4f threshold=%.4f -> %s' % (ck.round(4), dist, thrd, 'COLLISION' if dist <= thrd else 'clear'))
print('area: rectangle %.3f, 3 circles union approx (MC):' % (4.5 * 1.8), end=' ')
rng = np.random.default_rng(1)
P = rng.uniform([-4, -2], [4, 2], size=(400000, 2))
inside = np.zeros(len(P), bool)
for off in offs:
    inside |= np.hypot(P[:, 0] - off, P[:, 1]) <= rk
print('%.3f' % (inside.mean() * 32))

hdr('E10 tunnelling')
for vv, dtc in ((20, 0.01), (20, 0.5), (15, 0.2)):
    print('v=%g dt=%g -> step %.2f m' % (vv, dtc, vv * dtc))
print('collision zone width through the centre = 2*thr = %.3f' % (2 * thrd))

# ---------------------------------------------------------------- costs for the 6 slide-10 candidates
hdr('E12 costs (straight reference, v_ref=6, d_pref=0)')
T = 4.0
tt = np.linspace(0, T, 40001)
vref, dpref = 6.0, 0.0
S = dict(j=1.0, v=10.0, d=4.0)
W = dict(j=1.0, v=1.0, d=1.0)
rows = []
for lk, cl in LON.items():
    for dT, cd in LAT.items():
        sd_ = pev(cl, tt, 1)
        dd_ = pev(cd, tt, 1)
        js = pev(cl, tt, 3)
        jd = pev(cd, tt, 3)
        Jj = np.trapz(js ** 2 + jd ** 2, tt)
        vv = np.hypot(sd_, dd_)
        Jv = np.trapz((vv - vref) ** 2, tt)
        Jd = (pev(cd, T) - dpref) ** 2
        J = W['j'] * Jj / S['j'] + W['v'] * Jv / S['v'] + W['d'] * Jd / S['d']
        rows.append((lk, dT, Jj, Jv, Jd, J))
        print('%-5s dT=%+.0f  Jj=%.4f (lon %.4f lat %.4f)  Jv=%.4f  Jd=%.2f  J=%.4f' % (
            lk, dT, Jj, np.trapz(js ** 2, tt), np.trapz(jd ** 2, tt), Jv, Jd, J))
print('lon jerk^2 integral closed form: b3,b4 ->', [np.trapz(pev(cl, tt, 3) ** 2, tt) for cl in LON.values()])
surv = [r_ for r_ in rows if r_[1] == -2.0]
best = min(surv, key=lambda r_: r_[5])
print('survivors (dT=-2):', [(r_[0], round(r_[5], 4)) for r_ in surv], '-> select', best[0])
best_all = min(rows, key=lambda r_: r_[5])
print('cheapest overall (before checks):', best_all[0], best_all[1], round(best_all[5], 4))
for wv in (0.2, 3.0):
    Jw = [(r_[0], r_[2] / S['j'] + wv * r_[3] / S['v'] + r_[4] / S['d']) for r_ in surv]
    print('  w_v=%.1f ->' % wv, [(a, round(b_, 4)) for a, b_ in Jw])
for vr in (4.0, 5.0):
    out = []
    for lk, cl in LON.items():
        sd_ = pev(cl, tt, 1)
        dd_ = pev(LAT[-2.0], tt, 1)
        Jv = np.trapz((np.hypot(sd_, dd_) - vr) ** 2, tt)
        out.append((lk, round(Jv, 4), round(2.8125 + 0.75 + Jv / S['v'] + 1.0, 4)))
    print('  v_ref=%.0f survivors (Jv, J):' % vr, out)

hdr('E12b collision filter on a left curve R=40 (obstacle at s=13, d=+1.0, r_obs=0.5, m=0.2)')
R40 = 40.0
obs_s, obs_d = 13.0, 1.0
ro, _, no, _ = circle(R40, obs_s)
obs = ro + obs_d * no
thr40 = rk + 0.5 + 0.2
tt2 = np.arange(0, T + 1e-9, 0.01)
for lk, cl in LON.items():
    for dT, cd in LAT.items():
        ss, dd = pev(cl, tt2), pev(cd, tt2)
        P = np.array([circle(R40, a)[0] + b_ * circle(R40, a)[2] for a, b_ in zip(ss, dd)])
        V = np.gradient(P, axis=0)
        H = np.arctan2(V[:, 1], V[:, 0])
        dmin, tmin = 1e9, None
        for k_, (pt, hh) in enumerate(zip(P, H)):
            for off in offs:
                ck = pt + off * np.array([math.cos(hh), math.sin(hh)])
                dist = np.linalg.norm(ck - obs)
                if dist < dmin:
                    dmin, tmin = dist, tt2[k_]
        print('%-5s dT=%+.0f  min circle-obstacle distance %.3f at t=%.2f -> %s' % (
            lk, dT, dmin, tmin, 'REJECT' if dmin <= thr40 else 'pass'))
print('obstacle xy =', obs.round(3), 'threshold', round(thr40, 4))

# ---------------------------------------------------------------- Bezier
hdr('E13 Bezier P0=(0,0) P1=(4,0) P2=(8,2) P3=(12,2)')
Pb = np.array([[0, 0], [4, 0], [8, 2], [12, 2]], float)


def bez(P, u):
    return (1 - u) ** 3 * P[0] + 3 * u * (1 - u) ** 2 * P[1] + 3 * u ** 2 * (1 - u) * P[2] + u ** 3 * P[3]


for uu in (0.25, 0.5, 0.75):
    print('S(%.2f)=%s' % (uu, bez(Pb, uu)))
print("S'(0)=%s S'(1)=%s" % (3 * (Pb[1] - Pb[0]), 3 * (Pb[3] - Pb[2])))

# ---------------------------------------------------------------- closed-loop rollout
hdr('E14 rollout y+=dt*K*(r-y), K=1, dt=0.5')
for rr in (-2, 0, 2):
    y, seq = 0.0, []
    for _ in range(5):
        y = y + 0.5 * 1.0 * (rr - y)
        seq.append(round(y, 4))
    print('r=%+d' % rr, seq)

# ---------------------------------------------------------------- penalty optimisation
hdr('E15 J(y)=y^2+mu*max(0,2-y)^2, gradient descent alpha=0.04, mu=10')
mu, alpha, y = 10.0, 0.04, 0.0
for it in range(1, 7):
    g = 2 * y - 2 * mu * max(0.0, 2 - y)
    y = y - alpha * g
    print('it %d y=%.4f' % (it, y))
for mu in (1, 10, 100, 1000):
    print('mu=%g y*=%.4f violation=%.4f' % (mu, 2 * mu / (1 + mu), 2 - 2 * mu / (1 + mu)))

# ---------------------------------------------------------------- practice problems
hdr('P1 straight path at 60 deg, p=(2,5)')
t60 = np.array([0.5, math.sqrt(3) / 2])
n60 = np.array([-t60[1], t60[0]])
print('s=%.4f d=%.4f' % (np.array([2, 5]) @ t60, np.array([2, 5]) @ n60))

hdr('P2 circle R=25, (s,d)=(25pi/4, -2)')
r2, t2, n2, th2 = circle(25, 25 * math.pi / 4)
p2 = r2 - 2 * n2
print('r=%s n=%s p=%s |p-c|=%.4f' % (r2.round(4), n2.round(4), p2.round(4), np.linalg.norm(p2 - np.array([0, 25]))))

hdr('P3 circle R=25, p=(10,-3)')
c25 = np.array([0.0, 25.0])
p3 = np.array([10.0, -3.0])
u3 = (p3 - c25) / np.linalg.norm(p3 - c25)
r3 = c25 + 25 * u3
th3 = math.atan2(r3[0], 25 - r3[1])
_, t3, n3, _ = circle(25, 25 * th3)
print('|p-c|=%.4f r*=%s theta=%.3f deg s*=%.4f d=%.4f' % (np.linalg.norm(p3 - c25), r3.round(4), th3 / D2R, 25 * th3,
                                                          (p3 - r3) @ n3))

hdr('P4 lane change dg=-3.5, T=5')
c4 = quintic(0, 0, 0, -3.5, 5)[0]
tt = np.linspace(0, 5, 50001)
print('coeffs', c4.round(6), 'peak |v|=%.4f peak |a|=%.4f' % (np.abs(pev(c4, tt, 1)).max(), np.abs(pev(c4, tt, 2)).max()))
print('T for peak a <= 1 with D=3.5: %.4f s' % math.sqrt(10 / math.sqrt(3) * 3.5 / 1.0))
print('scaling: halve T -> a x4, jerk x8, Jj x32')

hdr('P5 general quintic d0=1, v0=-0.5, a0=0, dg=0, T=4')
c5, A5, b5 = quintic(1, -0.5, 0, 0, 4)
print('A=\n', A5, '\n b =', b5, '\n coeffs', c5.round(6))
tt = np.linspace(0, 4, 40001)
d5 = pev(c5, tt)
print('min d=%.4f at t=%.3f   d(2)=%.4f' % (d5.min(), tt[d5.argmin()], pev(c5, 2)))

hdr('P7 candidate count / checks')
print(3 * 7 * 2, 'candidates;', int(4 / 0.01), 'samples;', int(4 / 0.01) * 3 * 5, 'distance checks each;',
      3 * 7 * 2 * int(4 / 0.01) * 3 * 5, 'total')

hdr('P8 R=40 left, d=-1.5 / +1.5, sd=12')
for dd8 in (-1.5, 1.5):
    print('d=%+.1f vT=%.4f' % (dd8, (1 - dd8 / 40) * 12))

hdr('P10 xd=6 yd=8 xdd=-2 ydd=1.5')
xd, yd, xdd, ydd = 6.0, 8.0, -2.0, 1.5
v10 = math.hypot(xd, yd)
k10 = (xd * ydd - yd * xdd) / v10 ** 3
print('v=%.3f theta=%.3f deg kappa=%.5f R=%.3f a_par=%.4f a_perp=%.4f' % (
    v10, math.degrees(math.atan2(yd, xd)), k10, 1 / k10, (xd * xdd + yd * ydd) / v10, v10 ** 2 * k10))

hdr('P11 limits a_perp_max=2.5, kappa_max=0.25')
print('v*=%.4f kappa_allowed(15)=%.5f Rmin=%.2f a_perp(15,R60)=%.3f vmax(R60)=%.3f' % (
    math.sqrt(2.5 / 0.25), 2.5 / 225, 225 / 2.5, 225 / 60, math.sqrt(2.5 * 60)))

hdr('P12 circles 4.8 x 2.0, r_obs=0.4, m=0.3, obstacle (2.4,1.5)')
rk12, offs12 = circles(4.8, 2.0)
thr12 = rk12 + 0.4 + 0.3
print('r_k=%.4f offsets=%s threshold=%.4f' % (rk12, offs12, thr12))
for off in offs12:
    dist = math.hypot(2.4 - off, 1.5)
    print('  c=(%.1f,0) dist=%.4f -> %s' % (off, dist, 'COLLISION' if dist <= thr12 else 'clear'))

hdr('P13 tunnelling v=15, dt=0.2, threshold 1.9806')
print('step=%.2f  zone width at centre=%.3f  chord at offset 1.5=%.3f' % (
    15 * 0.2, 2 * thr12, 2 * math.sqrt(thr12 ** 2 - 1.5 ** 2)))

hdr('P14 normalised selection')
cands = {'A': (2.0, 30.0, 0.0), 'B': (0.5, 50.0, 1.0), 'C': (1.2, 20.0, 4.0)}
S14 = (1.0, 25.0, 4.0)
for w in ((1, 1, 1), (1, 3, 1)):
    tot = {k_: w[0] * a / S14[0] + w[1] * b_ / S14[1] + w[2] * c_ / S14[2] for k_, (a, b_, c_) in cands.items()}
    print('w=%s' % (w,), {k_: round(v_, 3) for k_, v_ in tot.items()}, '-> pick', min(tot, key=tot.get))

hdr('P15 Bezier P0=(0,0) P1=(3,0) P2=(6,3) P3=(10,3)')
Pq = np.array([[0, 0], [3, 0], [6, 3], [10, 3]], float)
print('S(0.5)=%s  S(0.25)=%s  S\'(0)=%s S\'(1)=%s' % (bez(Pq, 0.5), bez(Pq, 0.25), 3 * (Pq[1] - Pq[0]), 3 * (Pq[3] - Pq[2])))

hdr('P16 rollout K=0.8 dt=0.5 r=3')
y, seq = 0.0, []
for _ in range(4):
    y = y + 0.5 * 0.8 * (3 - y)
    seq.append(round(y, 4))
print(seq, ' closed form', [round(3 * (1 - 0.6 ** kk), 4) for kk in range(1, 5)])
for K in (3.0, 4.5):
    y, seq = 0.0, []
    for _ in range(4):
        y = y + 0.5 * K * (3 - y)
        seq.append(round(y, 3))
    print('K=%.1f (K dt=%.2f)' % (K, K * 0.5), seq)
