# -*- coding: utf-8 -*-
"""Recompute every number quoted in the notes (slides' examples + new questions)."""
import numpy as np
from numpy import sin, cos, tan, arctan, arctan2, sqrt, pi, deg2rad, rad2deg

np.set_printoptions(precision=6, suppress=True)
d = deg2rad


def Rz(a):
    return np.array([[cos(a), -sin(a)], [sin(a), cos(a)]])


def T2(a, x, y):
    return np.array([[cos(a), -sin(a), x], [sin(a), cos(a), y], [0, 0, 1.0]])


def hdr(s):
    print('\n=== ' + s)


# ---------------------------------------------------------------- Lecture 2
hdr('L2 spherical')
rho, az, pol = 2, d(30), d(60)
print(rho * sin(pol) * cos(az), rho * sin(pol) * sin(az), rho * cos(pol))

hdr('L2 tool frame / world composition (3D)')
R90 = np.array([[0, -1, 0], [1, 0, 0], [0, 0, 1.0]])
print('p_B', R90 @ [0.1, 0, 0.05] + [0.4, 0.2, 0.3], 'dp_B', R90 @ [0.1, 0, 0])
print('t_GE', R90 @ [0.4, 0.2, 0.3] + [1, 2, 0])

hdr('L2 2-link FK')
L1, L2 = 0.4, 0.3


def fk(q1, q2, l1=L1, l2=L2):
    return np.array([l1 * cos(q1) + l2 * cos(q1 + q2), l1 * sin(q1) + l2 * sin(q1 + q2)])


print('p_E', fk(d(30), d(60)))
TBE = T2(d(90), *fk(d(30), d(60)))
TGB = T2(d(90), 1, 2)
print('T_GE\n', TGB @ TBE)
TES1 = T2(0, 0.1, 0)
TBS2 = T2(0, 0.1, 0.2)
TBS1 = TBE @ TES1
TS2S1 = np.linalg.inv(TBS2) @ TBS1
print('T_BS1\n', TBS1, '\nT_S2S1\n', TS2S1, '\np_S2', TS2S1 @ [0.2, 0, 1])
pa = fk(d(30), d(60), 0.4, 0.6)
pb = fk(d(29.5), d(59), 0.4, 0.6)
print('timestamp: p(tk)', pa, 'p(earlier)', pb, 'dp', pb - pa, 'norm mm', 1000 * np.linalg.norm(pb - pa))

# new question: inverse transform example
hdr('L2 Q: inverse of T_AB with Rz(30), t=(2,1)')
TAB = T2(d(30), 2, 1)
print(np.linalg.inv(TAB))
R = Rz(d(30))
print('-R^T t', -R.T @ [2, 1])

hdr('L2 Q: IK of 2-link for target (0.3464,0.5)')
x, y = 0.34641016, 0.5
c2 = (x * x + y * y - L1 ** 2 - L2 ** 2) / (2 * L1 * L2)
q2 = np.arccos(c2)
q1 = arctan2(y, x) - arctan2(L2 * sin(q2), L1 + L2 * cos(q2))
print('c2', c2, 'q2 deg', rad2deg(q2), 'q1 deg', rad2deg(q1), 'elbow-other q2', -rad2deg(q2),
      'q1', rad2deg(arctan2(y, x) - arctan2(L2 * sin(-q2), L1 + L2 * cos(-q2))))

hdr('L2 Q: Jacobian at q=(30,60) and joint error 0.5 deg each')
q1, q2 = d(30), d(60)
J = np.array([[-L1 * sin(q1) - L2 * sin(q1 + q2), -L2 * sin(q1 + q2)],
              [L1 * cos(q1) + L2 * cos(q1 + q2), L2 * cos(q1 + q2)]])
print('J\n', J, '\nJ dq (0.5deg,0.5deg) mm', 1000 * J @ [d(0.5), d(0.5)], 'det', np.linalg.det(J))
print('workspace radii', L1 - L2, L1 + L2)

hdr('L2 bicycle')
v, L, delta, lr = 5.0, 2.5, d(10), 1.25
w = v / L * tan(delta)
beta = arctan(lr / L * tan(delta))
print('omega', w, 'R_R', L / tan(delta), 'kappa', tan(delta) / L, 'beta deg', rad2deg(beta), 'vC', v / cos(beta))
print('Q: delta=5deg v=10 L=2.7 -> R', 2.7 / tan(d(5)), 'yawrate', 10 * tan(d(5)) / 2.7,
      'deg/s', rad2deg(10 * tan(d(5)) / 2.7))


def fc(x, u=(d(10), 0.0), L=2.5):
    X, Y, psi, vv = x
    dl, a = u
    return np.array([vv * cos(psi), vv * sin(psi), vv / L * tan(dl), a])


def step(x, h, method):
    if method == 'euler':
        return x + h * fc(x)
    if method == 'mid':
        k1 = fc(x)
        return x + h * fc(x + h / 2 * k1)
    k1 = fc(x)
    k2 = fc(x + h / 2 * k1)
    k3 = fc(x + h / 2 * k2)
    k4 = fc(x + h * k3)
    return x + h / 6 * (k1 + 2 * k2 + 2 * k3 + k4)


x0 = np.array([0, 0, 0, 5.0])
hdr('L2 one step h=0.1')
for m in ('euler', 'mid', 'rk4'):
    print(m, step(x0, 0.1, m))
k1 = fc(x0)
print('k2 mid', fc(x0 + 0.05 * k1))
print('exact Y(0.1)', v / w * (1 - cos(w * 0.1)), 'X(0.1)', v / w * sin(w * 0.1))


def err(h, m, T=4.0):
    x = x0.copy()
    n = int(round(T / h))
    for _ in range(n):
        x = step(x, h, m)
    ex = np.array([v / w * sin(w * T), v / w * (1 - cos(w * T))])
    return np.linalg.norm(x[:2] - ex)


hdr('L2 errors at 4 s')
for h in (0.5, 0.2, 0.1, 0.05):
    print(h, err(h, 'euler'), err(h, 'mid'), err(h, 'rk4'))
print('exact pos at 4 s', v / w * sin(w * 4), v / w * (1 - cos(w * 4)))

hdr('L2 normal accel / validity')
print(5 ** 2 / 20, 15 ** 2 / 20, 'vmax mu=1 R=20', sqrt(0.5 * 9.81 * 20), 'mu=0.3', sqrt(0.5 * 0.3 * 9.81 * 20))
hdr('L2 steering lag')
print('delta(0.9)', 10 * (1 - np.exp(-(0.9 - 0.5) / 0.4)), 'h<', 2 * 0.4)
print('amp h=0.2', 1 - 0.2 / 0.4, 'h=1.0', 1 - 1.0 / 0.4, 'h=0.6', 1 - 0.6 / 0.4)
print('Q: tau=0.25 -> h<', 0.5, ' Euler e after 3 steps h=0.3 e0=-10:', -10 * (1 - 0.3 / 0.25) ** 3)
print('Q order: ratio 0.08->0.02 p=', np.log2(0.08 / 0.02), ' 0.08->0.01', np.log2(8))

# ---------------------------------------------------------------- Lecture 3
hdr('L3 projection')
pL = np.array([1.2, 0.4, 5.0])
tLC = np.array([0.2, -0.1, 0])
pC = pL - tLC
print('pC', pC, 'uv', 800 * pC[0] / pC[2] + 640, 800 * pC[1] / pC[2] + 360)
hdr('L3 reprojection RMS example')
e = np.array([[-2, 1], [1, 1], [0, -2]], float)
print('per-point RMS', sqrt(np.mean(np.sum(e ** 2, 1))), 'per-coord RMS', sqrt(np.mean(e ** 2)))
hdr('L3 stereo depth')
f, B, sd = 800, 0.12, 0.5
for dd in (48, 12, 96, 24):
    Z = f * B / dd
    print(dd, Z, Z ** 2 / (f * B) * sd)
print('Q: f=700 B=0.5 d=35 ->', 700 * 0.5 / 35, 'sigma(0.25px)', (700 * 0.5 / 35) ** 2 / (700 * 0.5) * 0.25)
print('Q: Z=20 m f=700 B=0.5 -> d', 700 * 0.5 / 20, 'sigmaZ for 0.25px', 400 / 350 * 0.25)
hdr('L3 distortion example')
x, y, k1, k2 = 0.3, 0.2, -0.25, 0.05
r2 = x * x + y * y
g = 1 + k1 * r2 + k2 * r2 * r2
print('r2', r2, 'g', g, 'xd', x * g, 'yd', y * g, 'pixels', 800 * x * g + 640, 800 * y * g + 360,
      'undistorted', 800 * x + 640, 800 * y + 360)
hdr('L3 time offset')
print(10 * 0.05, 20 * 0.05, 'Q: 2 m/s 30 ms', 2 * 0.03, '90deg/s 30ms', 90 * 0.03)
print('Q rolling shutter: 1080 rows t_read 30ms, row 810 vs centre:', (810 / 1080 - 0.5) * 30, 'ms')
hdr('L3 SVD rotation (Kabsch) check with det fix')
rng = np.random.default_rng(3)
Rtrue = np.array([[cos(0.3), -sin(0.3), 0], [sin(0.3), cos(0.3), 0], [0, 0, 1]])
nC = rng.normal(size=(5, 3))
nC /= np.linalg.norm(nC, axis=1, keepdims=True)
nL = (Rtrue @ nC.T).T
Hn = sum(np.outer(a, b) for a, b in zip(nC, nL))
U, S, Vt = np.linalg.svd(Hn)
V = Vt.T
Rhat = V @ np.diag([1, 1, np.linalg.det(V @ U.T)]) @ U.T
print('R err', np.abs(Rhat - Rtrue).max())
hdr('L3 translation LS: N = I, b')
print('t', np.linalg.lstsq(np.eye(3), [0.2, -0.1, 0.3], rcond=None)[0])
Nd = np.array([[0, 0, 1], [0, 0, 1], [0, 0, 1.0]])
print('rank all-parallel', np.linalg.matrix_rank(Nd))

# ---------------------------------------------------------------- Lecture 4
hdr('L4 encoder / diff drive')
r, N, b = 0.05, 1000, 0.30
sL = r * 2 * pi * 100 / N
sR = r * 2 * pi * 200 / N
ds, dth = (sR + sL) / 2, (sR - sL) / b
print('sL', sL, 'sR', sR, 'ds', ds, 'dth', dth, rad2deg(dth), 'dx', ds * cos(dth / 2), 'dy', ds * sin(dth / 2))
print('exact arc dx', ds / dth * sin(dth), 'dy', ds / dth * (1 - cos(dth)))
print('quat 6deg', sin(d(3)), cos(d(3)))
print('Q: L=+300 R=+100 counts:',
      [(r * 2 * pi * 100 / N + r * 2 * pi * 300 / N) / 2, (r * 2 * pi * 100 / N - r * 2 * pi * 300 / N) / b])
sl3, sr3 = r * 2 * pi * 300 / N, r * 2 * pi * 100 / N
ds3, dt3 = (sr3 + sl3) / 2, (sr3 - sl3) / b
print('   ds', ds3, 'dth', dt3, rad2deg(dt3), 'dx', ds3 * cos(dt3 / 2), 'dy', ds3 * sin(dt3 / 2))
print('Q quat 120deg', sin(d(60)), cos(d(60)), ' -90deg', sin(d(-45)), cos(d(-45)))
print('yaw from q z=0.2588,w=0.9659 ->', rad2deg(2 * arctan2(0.2588, 0.9659)))

hdr('L4 square drift')
pos = np.zeros(2)
hd = 0.0
pts = [pos.copy()]
for i in range(4):
    pos = pos + 2.04 * np.array([cos(hd), sin(hd)])
    pts.append(pos.copy())
    hd += d(95)
print('end', pos, 'err', np.linalg.norm(pos), 'heading after 4 turns', rad2deg(hd))
gam = -d(20)
Rg = Rz(gam)
t_mo = -Rg @ pos
print('map->odom t', t_mo)

hdr('L4 KF 1D')


def kf1(x, P, u, Q, z, R):
    xm, Pm = x + u, P + Q
    K = Pm / (Pm + R)
    return xm, Pm, K, xm + K * (z - xm), (1 - K) * Pm


print(kf1(8, 3, 2, 1, 12, 1))
print('R=9', kf1(8, 3, 2, 1, 12, 9), 'Q=13', kf1(8, 3, 2, 13, 12, 1))
a = (0.09 + sqrt(0.09 ** 2 + 4 * 0.09 * 1)) / 2
print('steady P-', a, 'P+', a / (a + 1), 'sigma+', sqrt(a / (a + 1)))
print('Q: x=5,P=2,u=1,Q=0.5,z=6.5,R=0.5', kf1(5, 2, 1, 0.5, 6.5, 0.5))

hdr('L4 pos-vel KF')
F = np.array([[1, 1], [0, 1.0]])
G = np.array([[0.5], [1.0]])
Qm = 0.1 * G @ G.T
P0 = np.eye(2)
xm = F @ [0, 1.0]
Pm = F @ P0 @ F.T + Qm
H = np.array([[1, 0.0]])
S = (H @ Pm @ H.T)[0, 0] + 0.25
K = (Pm @ H.T / S).ravel()
nu = 1.5 - xm[0]
print('Q', Qm, '\nPm', Pm, '\nS', S, 'K', K, 'x+', xm + K * nu, '\nP+', Pm - np.outer(K, H @ Pm))
hdr('L4 bias')
P, x = 4.0, 10.0
for n in range(1, 41):
    Kb = P / (P + 0.04)
    x = x + Kb * (12 - x)
    P = (1 - Kb) * P
    if n in (1, 40):
        print(n, x, P, sqrt(P))

# ---------------------------------------------------------------- Lecture 6
hdr('L6 EKF update example')
xm = np.array([1, 1, 0.2])
lm = np.array([4, 5.0])
dx, dy = lm - xm[:2]
q = dx * dx + dy * dy
rho = sqrt(q)
hpred = np.array([rho, arctan2(dy, dx) - xm[2]])
Hk = np.array([[-dx / rho, -dy / rho, 0], [dy / q, -dx / q, -1]])
Pm = np.diag([0.16, 0.16, 0.04])
Rm = np.diag([0.04, 0.01])
Sk = Hk @ Pm @ Hk.T + Rm
Kk = Pm @ Hk.T @ np.linalg.inv(Sk)
z = np.array([4.8, 0.8])
nu = z - hpred
xp = xm + Kk @ nu
IKH = np.eye(3) - Kk @ Hk
Pp = IKH @ Pm @ IKH.T + Kk @ Rm @ Kk.T
print('h', hpred, '\nH', Hk, '\nS', Sk, '\nK', Kk, '\nnu', nu, '\nx+', xp, '\nP+', Pp,
      '\nP+ standard', IKH @ Pm)
hdr('L6 EKF motion Jacobian example (Q)')
vv, wv, dt, th = 1.0, 0.5, 0.2, d(30)
Fj = np.array([[1, 0, -vv * dt * sin(th)], [0, 1, vv * dt * cos(th)], [0, 0, 1]])
print(Fj)
P0 = np.diag([0.01, 0.01, 0.04])
print('F P F^T', Fj @ P0 @ Fj.T)

hdr('L6 UKF 1D example')
p, Pv, Rr = 1.0, 0.5, 0.04
chi = np.array([0, 1, 2.0])
W = np.array([0.25, 0.5, 0.25])
hz = sqrt(chi ** 2 + 1)
zhat = W @ hz
dz = hz - zhat
S = W @ dz ** 2 + Rr
Cpz = W @ ((chi - p) * dz)
Kk = Cpz / S
zz = 1.6
print('h', hz, 'zhat', zhat, 'd', dz, 'S terms', W * dz ** 2, 'S', S, 'Cpz', Cpz, 'K', Kk,
      'p+', p + Kk * (zz - zhat), 'P+', Pv - Kk * S * Kk, 'nu', zz - zhat)
Hd = 1 / sqrt(2)
Se = Hd * Pv * Hd + Rr
Ke = Pv * Hd / Se
print('EKF same: zhat', sqrt(2), 'S', Se, 'K', Ke, 'p+', p + Ke * (zz - sqrt(2)), 'P+', (1 - Ke * Hd) * Pv)
mc = np.random.default_rng(0).normal(p, sqrt(Pv), 2_000_000)
print('Monte Carlo E[h]', np.mean(sqrt(mc ** 2 + 1)), 'var', np.var(sqrt(mc ** 2 + 1)))
print('Q: h=p^2 with mean 2 var 0.25: EKF', 4, 'true', 4 + 0.25)
s = sqrt(2 * 0.25)
ch = np.array([2 - s, 2, 2 + s])
print('   UKF (kappa: n+l=2)', W @ ch ** 2)

hdr('L6 pose graph')


def wrap(a):
    return (a + pi) % (2 * pi) - pi


def hrel(xa, xb):
    c, s_ = cos(xa[2]), sin(xa[2])
    dp = xb[:2] - xa[:2]
    return np.array([c * dp[0] + s_ * dp[1], -s_ * dp[0] + c * dp[1], wrap(xb[2] - xa[2])])


Z = {(0, 1): [2.2, 0, 1.6581], (1, 2): [2.1, 0, 2.4435], (2, 3): [2.9, 0, 2.3562], (0, 3): [0, 0, 0]}
SIG = {e: ([0.05, 0.05, 0.03491] if e == (0, 3) else [0.15, 0.15, 0.08727]) for e in Z}


def compose(xa, z):
    c, s_ = cos(xa[2]), sin(xa[2])
    return np.array([xa[0] + c * z[0] - s_ * z[1], xa[1] + s_ * z[0] + c * z[1], wrap(xa[2] + z[2])])


x0p = np.zeros(3)
X = [x0p]
for e in [(0, 1), (1, 2), (2, 3)]:
    X.append(compose(X[-1], Z[e]))
X = np.array(X)
print('initial poses\n', X)


def residuals(Xf):
    Xa = np.vstack([x0p, Xf.reshape(3, 3)])
    out = []
    for (a, bb), z in Z.items():
        rr = np.array(z) - hrel(Xa[a], Xa[bb])
        rr[2] = wrap(rr[2])
        out.append(rr / np.array(SIG[(a, bb)]))
    return np.concatenate(out)


def jac(Xf, eps=1e-7):
    r0 = residuals(Xf)
    Jn = np.zeros((len(r0), len(Xf)))
    for j in range(len(Xf)):
        Xp = Xf.copy()
        Xp[j] += eps
        Jn[:, j] = (residuals(Xp) - r0) / eps
    return Jn


Xf = X[1:].ravel().copy()
r0 = residuals(Xf)
print('r03 raw', np.array(Z[(0, 3)]) - hrel(x0p, X[3]), 'scaled', r0[9:], 'cost0', 0.5 * r0 @ r0)
for it in range(6):
    Jn = jac(Xf)
    rr = residuals(Xf)
    delta = np.linalg.solve(Jn.T @ Jn, -Jn.T @ rr)
    Xf = Xf + delta
    Xf[2::3] = wrap(Xf[2::3])
    rr = residuals(Xf)
    print('iter', it + 1, 'cost', 0.5 * rr @ rr, ('delta ' + str(delta.reshape(3, 3).round(4).tolist())) if it == 0 else '')
print('x* \n', Xf.reshape(3, 3))
rr = residuals(Xf)
contrib = [0.5 * rr[3 * i:3 * i + 3] @ rr[3 * i:3 * i + 3] for i in range(4)]
print('per-edge cost', np.round(contrib, 4), 'raw r03*', rr[9:] * np.array(SIG[(0, 3)]))
Xs = np.vstack([x0p, Xf.reshape(3, 3)])
s2 = np.array([0.0, 1.4142])
print('map pt 2 before', Rz(X[2][2]) @ s2 + X[2][:2], 'after', Rz(Xs[2][2]) @ s2 + Xs[2][:2])
print('dr12y/dtheta1 ~ hx =', hrel(X[1], X[2])[0], ' nonlinear dr for 0.05:',
      -(hrel(X[1] + [0, 0, 0.05], X[2])[1] - hrel(X[1], X[2])[1]))

# ---------------------------------------------------------------- Lecture 7
hdr('L7 Armijo example f=x^2 x0=1')
f1 = lambda x: x * x
x0_, g0 = 1.0, 2.0
dd = -g0
for al in (1, 0.5, 0.25):
    print(al, f1(x0_ + al * dd), f1(x0_) + 0.5 * al * g0 * dd)
hdr('L7 GD vs Newton on f=(x-1)^2+10(y-2)^2')
Hq = np.diag([2, 20.0])
gq = lambda z: np.array([2 * (z[0] - 1), 20 * (z[1] - 2)])
z0 = np.array([0, 0.0])
print('newton step', z0 - np.linalg.solve(Hq, gq(z0)), 'kappa', 10, 'rate', ((10 - 1) / (10 + 1)) ** 2)
g = gq(z0)
al = (g @ g) / (g @ Hq @ g)
print('GD exact step alpha', al, 'x1', z0 - al * g)
hdr('L7 Gauss-Newton sqrt2')
xx = 1.0
for i in range(3):
    xx = xx - (xx * xx - 2) / (2 * xx)
    print(i + 1, xx)
hdr('L7 equality QP')
Kkt = np.array([[1, 0, 1], [0, 1, 1], [1, 1, 0.0]])
print(np.linalg.solve(Kkt, [0, 0, 1]))
Kkt2 = np.array([[2, 0, 1], [0, 4, 1], [1, 1, 0.0]])
print('Q2 (Q=diag(2,4), q=(-2,-4)? ) ->', np.linalg.solve(Kkt2, [2, 4, 1]))
hdr('L7 LM gain ratio example')
fx, fnew, pred = 10.0, 7.0, 4.0
print('gamma', (fx - fnew) / pred)
hdr('L7 Newton 1D on f=x^4/4 - x example?')
fx4 = lambda x: x ** 4 - 2 * x ** 2
for x_ in (2.0, 0.5):
    gq1 = 4 * x_ ** 3 - 4 * x_
    hq1 = 12 * x_ ** 2 - 4
    print('x', x_, 'grad', gq1, 'hess', hq1, 'newton dir', -gq1 / hq1)

hdr('L2 extra question numbers')
print('Q4 lidar', 10 * cos(d(10)) * cos(d(45)), 10 * cos(d(10)) * sin(d(45)), 10 * sin(d(10)))
print('Q5 fk 90,-90', fk(d(90), d(-90)))
print('Q7 S1 (0,0.1) -> B', TBS1 @ [0, 0.1, 1], ' -> S2', TS2S1 @ [0, 0.1, 1])
print('Q8 r w dt', 0.8 * d(30) * 0.05)
bq = arctan(1.2 / 2.7 * tan(d(5)))
print('Q10 beta deg', rad2deg(bq), 'vC', 10 / cos(bq), 'yaw', 10 / 2.7 * tan(d(5)))
x0q = np.array([0, 0, 0, 10.0])
fq = lambda x: fc(x, (d(5), 0.0), 2.7)
print('Q11 euler', x0q + 0.2 * fq(x0q), 'mid', x0q + 0.2 * fq(x0q + 0.1 * fq(x0q)))
print('Q15 vmax', sqrt(0.5 * 0.8 * 9.81 * 50))
print('RK4 h=0.4 err', err(0.4, 'rk4'), 'euler h=0.1', err(0.1, 'euler'), 'mid h=0.2', err(0.2, 'mid'))

hdr('L3 extra question numbers')
p = np.array([0.5, -0.2, 4.0])
print('Q proj', 800 * p[0] / p[2] + 640, 800 * p[1] / p[2] + 360)
print('Q lateral at 10 m for 2.7 deg', 10 * tan(d(2.7)))
pL2 = np.array([2.2, 0.9, 10.0])
pC2 = pL2 - tLC
print('Q lidar far point', pC2, 800 * pC2[0] / pC2[2] + 640, 800 * pC2[1] / pC2[2] + 360)
E = np.array([[0, 0, 0], [0, 0, -1], [0, 1, 0.0]])
x1 = np.array([0.2, 0.1, 1.0])
l2 = E @ x1
x2 = np.array([0.05, 0.13, 1.0])
print('Q epipolar line', l2, 'dist', abs(x2 @ l2) / np.hypot(l2[0], l2[1]))
print('Q scale 25/24', 25 / 24)

hdr('L4 extra question numbers')
print('Q enc', 0.08 * 2 * pi * 1024 / 4096)
print('Q Q-matrix dt=0.5 sa2=0.2', 0.2 * np.array([[0.5 ** 4 / 4, 0.5 ** 3 / 2], [0.5 ** 3 / 2, 0.5 ** 2]]))
a_ = (0.09 + sqrt(0.09 ** 2 + 4 * 0.09)) / 2
print('Q steady K', a_ / (a_ + 1))

hdr('L6 extra question numbers')
xq = np.array([2, -1, pi / 2]); lq = np.array([6, 2.0])
dxq, dyq = lq - xq[:2]; qq = dxq ** 2 + dyq ** 2; rq = sqrt(qq)
print('Q h', rq, arctan2(dyq, dxq) - xq[2], 'H', [[-dxq / rq, -dyq / rq, 0], [dyq / qq, -dxq / qq, -1]])
print('Q wrap', wrap(-3.10 - 3.10))
s = sqrt(2 * 0.25)
chi = np.array([2 - s, 2, 2 + s])
print('Q sigma pts', chi, chi ** 2, W @ chi ** 2)
print('Q h12', hrel(X[1], X[2]))
r03 = np.array([-0.3536, 0.2835, -0.1745]) / np.array([0.05, 0.05, 0.03491])
print('Q whiten', r03, 0.5 * r03 @ r03)

hdr('L7 extra question numbers')
x_ = 0.4
for i in range(5):
    g_ = 4 * x_ ** 3 - 4 * x_
    h_ = 12 * x_ ** 2 - 4
    print('newton iter', i, 'x', round(x_, 5), 'f', round(x_ ** 4 - 2 * x_ ** 2, 5), 'grad', round(g_, 4), 'hess', round(h_, 4))
    x_ = x_ - g_ / h_
print('stationary pts of x^3-3x+y^2: H at (1,0)', [6, 2], 'at (-1,0)', [-6, 2])
print('Lagrange min x^2+y^2 s.t. x+y=1:', np.linalg.solve(np.array([[2, 0, 1], [0, 2, 1], [1, 1, 0.0]]), [0, 0, 1]))
print('GD contraction for kappa=10', ((10 - 1) / (10 + 1)) ** 2, 'f ratio check', end=' ')
z = np.array([0, 0.0]); fq_ = lambda z: (z[0] - 1) ** 2 + 10 * (z[1] - 2) ** 2
g = gq(z); al = (g @ g) / (g @ Hq @ g); z1 = z - al * g
print(fq_(z), fq_(z1), fq_(z1) / fq_(z))
print('gamma reject', (10 - 10.5) / 4)

hdr('Synthesis question numbers')
for Zs in (8.0, 2.0):
    sz = Zs ** 2 / (800 * 0.12) * 0.5
    Rz = sz ** 2
    print('Z', Zs, 'sigmaZ', sz, 'R', Rz, 'K with P-=0.04', 0.04 / (0.04 + Rz))
hq_ = 0.1
print('bicycle F entries', hq_ * 5, hq_ * tan(d(10)) / 2.5)
