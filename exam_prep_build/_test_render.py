# -*- coding: utf-8 -*-
"""Render a test page to check dark @page, margin boxes and MathML."""
import pathlib, fitz
from playwright.sync_api import sync_playwright
from tex2mml import convert_html

BASE = pathlib.Path(__file__).parent
eqs = r"""
<p>Inline: $\mathbf{p}_\mathrm{G} = R_\mathrm{GB}\,\mathbf{p}_\mathrm{B} + \mathbf{t}_\mathrm{GB}$, and
$\dot\psi = \frac{v_\mathrm{R}}{L}\tan\delta$, angle $30^\circ$, $x \le -1$, $\hat{x}^{-}_{k} = \hat{x}^{+}_{k-1} + u_{k-1}$.</p>
$$T_\mathrm{BA} = T_\mathrm{AB}^{-1} = \begin{bmatrix} R_\mathrm{AB}^\T & -R_\mathrm{AB}^\T\mathbf{t}_\mathrm{AB} \\ \mathbf{0}_{1\times3} & 1 \end{bmatrix}$$
$$K^{*} = \frac{P^{-}}{P^{-}+R}, \qquad P^{+} = (1-K^{*})P^{-}$$
$$\hat{\boldsymbol\theta} = \argmin_{\boldsymbol\theta} \sum_{n} \mathbf{e}_n^\T \Sigma_n^{-1}\mathbf{e}_n$$
$$h(x) = \begin{bmatrix} \sqrt{d_x^2 + d_y^2} \\ \wrap\!\left(\atantwo(d_y, d_x) - \theta\right) \end{bmatrix}, \quad \left\| \mathbf{r}_k + J_k \mathbf{d} \right\|_2^2$$
$$\begin{aligned} \mathbf{k}_1 &= f_c(\mathbf{x}_k, \mathbf{u}_k) \\ \mathbf{x}_{k+1} &= \mathbf{x}_k + \frac{h}{6}\left(\mathbf{k}_1 + 2\mathbf{k}_2 + 2\mathbf{k}_3 + \mathbf{k}_4\right) \end{aligned}$$
$$\mu_i g_i(x) = 0, \quad \nabla_x \mathcal{L} = \nabla f + J_h^\T \lambda + J_g^\T \mu = 0, \quad \mathbb{R}^{12\times 9}$$
$$\left|1 - \frac{h}{\tau}\right| < 1 \;\Rightarrow\; 0 < h < 2\tau, \qquad \sigma_Z \simeq \frac{Z^2}{fB}\sigma_{d}$$
$$\boldsymbol{\omega}_C(t) = R_{CB}\,\boldsymbol\omega_B(t),\quad \tilde{\mathbf{a}}_B = R_{BG}(\ddot{\mathbf{p}}_{GB} - \mathbf{g}_G) + \mathbf{b}_a + \mathbf{n}_a$$
"""
html = """<!doctype html><html><head><meta charset="utf-8"><style>
@page { size: A4; margin: 18mm 16mm 16mm 16mm; background: #0f131a;
  @bottom-center { content: counter(page) " / " counter(pages); color: #8b95a7; font: 9pt 'Segoe UI'; }
  @top-left { content: "Intelligent Robot Practice"; color: #6b7588; font: 8.5pt 'Segoe UI'; }
}
@page l2 { @top-right { content: "Lecture 2 · System modeling"; color: #22d3ee; font: 600 8.5pt 'Segoe UI'; } }
html, body { background: #0f131a; color: #e6e9f0; margin: 0; }
body { font: 10.5pt/1.55 'Segoe UI', sans-serif; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
h1 { font-family: Bahnschrift; font-weight: 600; font-size: 28pt; color: #22d3ee; }
.l2 { page: l2; }
math { font-family: 'Cambria Math'; font-size: 1.08em; }
.eq { display: block; text-align: center; margin: 0.55em 0; break-inside: avoid; }
mtd.al-r { text-align: right; padding: 0.15em 0 0.15em 0.3em; }
mtd.al-l { text-align: left; padding: 0.15em 0.3em 0.15em 0; }
mtd.al-c { padding: 0.15em 0.5em; }
.box { background: #161b26; border: 1px solid #2a3242; border-left: 4px solid #22d3ee; border-radius: 8px; padding: 10px 14px; }
</style></head><body>
<section class="l2"><h1>Test page — dark theme</h1>
<div class="box">%s</div>
<p style="break-before: page">Second page text; check the margins stay dark. 한국어 텍스트: 칼만 이득, 좌표계.</p>
</section></body></html>""" % convert_html(eqs)

tmp = BASE / '_test.html'
tmp.write_text(html, encoding='utf-8')
out = BASE / '_test.pdf'
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page()
    pg.goto(tmp.resolve().as_uri())
    pg.pdf(path=str(out), prefer_css_page_size=True, print_background=True,
           outline=True, tagged=True)
    b.close()
d = fitz.open(str(out))
print('pages', d.page_count, d[0].rect)
for i in range(d.page_count):
    d[i].get_pixmap(dpi=110).save(str(BASE / ('_test_p%d.png' % (i + 1))))
