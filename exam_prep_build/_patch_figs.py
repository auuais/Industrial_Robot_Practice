# -*- coding: utf-8 -*-
import io
p = 'figures.py'
s = io.open(p, encoding='utf-8').read()
rep = [
 ("ax.set_xlim(-0.5, 17); ax.set_ylim(-0.5, 13)", "ax.set_xlim(-0.5, 19.5); ax.set_ylim(-0.5, 13)"),
 ("ax.annotate('Euler: 1.62 m off after 4 s', xy=(15.0, 10.6), xytext=(8.5, 11.6),",
  "ax.annotate('Euler: 1.62 m off after 4 s', xy=(15.05, 10.6), xytext=(15.6, 6.2),"),
 ("ax.annotate('RK4 sits on the\\nanalytic curve (6 µm)', xy=(13.99, 11.92), xytext=(14.8, 7.0),",
  "ax.annotate('RK4 sits on the analytic\\ncurve (error 6 µm)', xy=(13.9, 11.95), xytext=(5.2, 11.1),"),
 ("label='%s  (slope ≈ %d)' % (m, p))", "label='%s: slope %d — halve h, error ×1/%d' % (m, p, 2 ** p))"),
 ("    ax.text(0.27, 3e-1, 'halve h → error ×½', color=C['rose'], fontsize=8)\n", ""),
 ("    ax.text(0.27, 6e-3, 'halve h → error ×¼', color=C['cyan'], fontsize=8)\n", ""),
 ("    ax.text(0.27, 1.5e-6, 'halve h → error ×1/16', color=C['green'], fontsize=8)\n", ""),
 ("xy=(8, 0.4805), xytext=(1.2, 0.47),", "xy=(8, 0.4805), xytext=(0.6, 0.43),"),
 ("ax.text(0.012, 0.86, 'trust the\\nobservation', color=C['orange'], fontsize=8)",
  "ax.text(2.2, 0.62, 'P⁻ ≫ R: trust the\\nobservation (K → 1)', color=C['orange'], fontsize=7.8)"),
 ("ax.text(0.012, 0.08, 'trust the prediction', color=C['blue'], fontsize=8)",
  "ax.text(0.011, 0.2, 'P⁻ ≪ R: trust the\\nprediction (K → 0)', color=C['blue'], fontsize=7.8)"),
 ("ax.text(1.55, 0.55, 'p ~ N(1, 0.5)', color=C['violet'], fontsize=7.6)",
  "ax.text(1.75, 0.62, 'p ~ N(1, 0.5)', color=C['violet'], fontsize=7.6)"),
 ("    sv, sw = 0.05, 0.03\n", "    sv, sw = 0.06, 0.03\n"),
 ("        um = u + rng.normal(0, [sv, sw])\n", "        um = u + rng.normal(0, [sv, sw]) + np.array([0.0, 0.025])\n"),
 ("    ax.legend(loc='center', fontsize=6.6)\n", "    ax.legend(loc='upper center', fontsize=6.6, ncol=2, bbox_to_anchor=(0.5, -0.2))\n"),
 ("            sens = (Rt.T @ (wall - X1[i, :2]).T).T\n",
  "            sens = (Rt.T @ (wall - X1[i, :2]).T).T + np.random.default_rng(i).normal(0, 0.015, wall.shape)\n"),
 ("    p0 = np.array([0.5, 0.3])\n", "    p0 = np.array([1.0, -3.0])\n"),
 ("ax.set_title('Same start (a, b) = (0.5, 0.3)', loc='left')", "ax.set_title('Same start (a, b) = (1, −3)', loc='left')"),
]
bad = 0
for a, b in rep:
    if a not in s:
        bad += 1
        print('MISSING:', a[:60].encode('ascii', 'replace'))
    s = s.replace(a, b)
io.open(p, 'w', encoding='utf-8').write(s)
print('done, missing', bad)
