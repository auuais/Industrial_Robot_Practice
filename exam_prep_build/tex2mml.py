# -*- coding: utf-8 -*-
"""Minimal TeX -> MathML Core converter for the exam notes.

Covers the subset used in the notes: fractions, roots, scripts, accents,
font styles (via Unicode math alphanumerics), stretchy fences, matrices,
cases/aligned, large operators with limits, function names and spacing.
Chromium renders the result natively with Cambria Math.
"""
import re
from html import escape

GREEK_LOWER = {
    'alpha': 'α', 'beta': 'β', 'gamma': 'γ', 'delta': 'δ', 'epsilon': 'ϵ',
    'varepsilon': 'ε', 'zeta': 'ζ', 'eta': 'η', 'theta': 'θ', 'vartheta': 'ϑ',
    'iota': 'ι', 'kappa': 'κ', 'lambda': 'λ', 'mu': 'μ', 'nu': 'ν', 'xi': 'ξ',
    'pi': 'π', 'rho': 'ρ', 'varrho': 'ϱ', 'sigma': 'σ', 'tau': 'τ',
    'upsilon': 'υ', 'phi': 'ϕ', 'varphi': 'φ', 'chi': 'χ', 'psi': 'ψ',
    'omega': 'ω',
}
GREEK_UPPER = {
    'Gamma': 'Γ', 'Delta': 'Δ', 'Theta': 'Θ', 'Lambda': 'Λ', 'Xi': 'Ξ',
    'Pi': 'Π', 'Sigma': 'Σ', 'Upsilon': 'Υ', 'Phi': 'Φ', 'Psi': 'Ψ',
    'Omega': 'Ω',
}
ORD_SYMBOLS = {
    'nabla': '∇', 'partial': '∂', 'infty': '∞', 'ell': 'ℓ', 'emptyset': '∅',
    'top': '⊤', 'prime': '′', 'dagger': '†', 'angle': '∠', 'checkmark': '✓',
    'R': 'ℝ', 'hbar': 'ℏ', 'star': '⋆',
}
OPS = {
    'cdot': '⋅', 'times': '×', 'pm': '±', 'mp': '∓', 'approx': '≈',
    'simeq': '≃', 'sim': '∼', 'neq': '≠', 'ne': '≠', 'leq': '≤', 'le': '≤',
    'geq': '≥', 'ge': '≥', 'll': '≪', 'gg': '≫', 'equiv': '≡', 'propto': '∝',
    'to': '→', 'rightarrow': '→', 'leftarrow': '←', 'Rightarrow': '⇒',
    'Leftarrow': '⇐', 'Leftrightarrow': '⇔', 'iff': '⟺', 'implies': '⟹',
    'mapsto': '↦', 'Longleftrightarrow': '⟺', 'Longrightarrow': '⟹', 'in': '∈', 'notin': '∉', 'subset': '⊂', 'subseteq': '⊆',
    'cup': '∪', 'cap': '∩', 'circ': '∘', 'ast': '∗', 'succ': '≻',
    'succeq': '⪰', 'prec': '≺', 'preceq': '⪯', 'perp': '⊥', 'parallel': '∥',
    'otimes': '⊗', 'oplus': '⊕', 'vee': '∨', 'wedge': '∧', 'ldots': '…',
    'dots': '…', 'cdots': '⋯', 'vdots': '⋮', 'ddots': '⋱', 'forall': '∀',
    'exists': '∃', 'mid': '∣', 'setminus': '∖', 'longrightarrow': '⟶',
    'uparrow': '↑', 'downarrow': '↓', 'leftrightarrow': '↔', 'colon': ':',
    'lt': '<', 'gt': '>', 'triangleq': '≜', 'coloneqq': '≔', 'neg': '¬',
    'bullet': '∙', 'searrow': '↘', 'nearrow': '↗', 'longmapsto': '⟼',
}
DELIMS = {
    '(': '(', ')': ')', '[': '[', ']': ']', '|': '|', '.': '',
    '\\{': '{', '\\}': '}', '\\|': '‖', '\\langle': '⟨', '\\rangle': '⟩',
    '\\lVert': '‖', '\\rVert': '‖', '\\lvert': '|', '\\rvert': '|',
    '\\vert': '|', '\\Vert': '‖', '\\lfloor': '⌊', '\\rfloor': '⌋',
    '\\lceil': '⌈', '\\rceil': '⌉', '\\lbrace': '{', '\\rbrace': '}',
}
FUNCS = ['sin', 'cos', 'tan', 'cot', 'sec', 'csc', 'arcsin', 'arccos',
         'arctan', 'sinh', 'cosh', 'tanh', 'exp', 'log', 'ln', 'det', 'dim',
         'ker', 'deg', 'Pr', 'tr', 'diag', 'rank', 'sign', 'wrap', 'atan',
         'var', 'cov', 'Var', 'Cov', 'proj']
NAMED_FUNCS = {'atantwo': 'atan2'}
LIMIT_FUNCS = {'min': 'min', 'max': 'max', 'argmin': 'arg min',
               'argmax': 'arg max', 'lim': 'lim', 'sup': 'sup', 'inf': 'inf'}
BIG_OPS = {'sum': '∑', 'prod': '∏', 'int': '∫', 'oint': '∮',
           'bigcup': '⋃', 'bigcap': '⋂'}
ACCENTS = {  # name: (char, stretchy)
    'hat': ('^', False), 'widehat': ('^', True), 'bar': ('¯', False),
    'overline': ('‾', True), 'tilde': ('~', False), 'widetilde': ('~', True),
    'dot': ('˙', False), 'ddot': ('¨', False), 'check': ('ˇ', False),
    'breve': ('˘', False), 'vec': ('→', False),
}
SPACES = {',': '0.1667em', ':': '0.2222em', ';': '0.2778em', ' ': '0.25em',
          'quad': '1em', 'qquad': '2em', 'enspace': '0.5em'}
STYLE_CMDS = {'mathbf': 'bf', 'boldsymbol': 'bi', 'bm': 'bi',
              'mathrm': 'rm', 'mathit': 'it', 'mathcal': 'cal',
              'mathbb': 'bb', 'mathsf': 'sf', 'mathtt': 'tt'}

# ---- Unicode mathematical alphanumerics ---------------------------------
_LATIN_BASE = {'bf': 0x1D400, 'it': 0x1D434, 'bi': 0x1D468, 'cal': 0x1D49C,
               'bb': 0x1D538, 'sf': 0x1D5A0, 'tt': 0x1D670}
_LATIN_EXC = {
    'it': {'h': 'ℎ'},
    'cal': {'B': 'ℬ', 'E': 'ℰ', 'F': 'ℱ', 'H': 'ℋ', 'I': 'ℐ', 'L': 'ℒ',
            'M': 'ℳ', 'R': 'ℛ', 'e': 'ℯ', 'g': 'ℊ', 'o': 'ℴ'},
    'bb': {'C': 'ℂ', 'H': 'ℍ', 'N': 'ℕ', 'P': 'ℙ', 'Q': 'ℚ', 'R': 'ℝ',
           'Z': 'ℤ'},
}
_DIGIT_BASE = {'bf': 0x1D7CE, 'bb': 0x1D7D8, 'sf': 0x1D7E2, 'tt': 0x1D7F6}
_GREEK_BASE = {'bf': 0x1D6A8, 'it': 0x1D6E2, 'bi': 0x1D71C}
_GREEK_SPECIAL = {'∇': 25, '∂': 51, 'ϵ': 52, 'ϑ': 53, 'ϰ': 54, 'ϕ': 55,
                  'ϱ': 56, 'ϖ': 57}


def styled(ch, style):
    """Map one character to the requested math alphanumeric style."""
    if style in (None, 'rm'):
        return ch
    if 'A' <= ch <= 'Z' or 'a' <= ch <= 'z':
        exc = _LATIN_EXC.get(style, {})
        if ch in exc:
            return exc[ch]
        base = _LATIN_BASE.get(style)
        if base is None:
            return ch
        off = ord(ch) - 65 if ch <= 'Z' else 26 + ord(ch) - 97
        return chr(base + off)
    if '0' <= ch <= '9':
        base = _DIGIT_BASE.get(style)
        return chr(base + ord(ch) - 48) if base else ch
    gb = _GREEK_BASE.get(style)
    if gb is None:
        return ch
    if ch in _GREEK_SPECIAL:
        return chr(gb + _GREEK_SPECIAL[ch])
    o = ord(ch)
    if 0x391 <= o <= 0x3A9:
        return chr(gb + o - 0x391)
    if 0x3B1 <= o <= 0x3C9:
        return chr(gb + 26 + o - 0x3B1)
    return ch


# ---- tokenizer -------------------------------------------------------------
TOKEN_RE = re.compile(r"""
    (?P<cmd>\\[A-Za-z]+) |
    (?P<cmdsym>\\[^A-Za-z]) |
    (?P<num>[0-9]+(?:\.[0-9]+)?) |
    (?P<letter>[A-Za-z]) |
    (?P<ws>\s+) |
    (?P<ch>.)
""", re.X | re.S)


def tokenize(src):
    # whitespace tokens are kept so \text{...} can reproduce its spaces;
    # the parser skips them everywhere else
    return [(m.lastgroup, m.group()) for m in TOKEN_RE.finditer(src)]


class Node:
    __slots__ = ('mml', 'limits', 'op', 'closing', 'func')

    def __init__(self, mml, limits=False, op=False, closing=False, func=False):
        self.mml = mml
        self.func = func          # function name: append ApplyFunction
        self.limits = limits      # takes under/over scripts in display mode
        self.op = op              # an operator (so a following -/+ is unary)
        self.closing = closing    # a closing fence (so -/+ after it is binary)


def row(nodes):
    if len(nodes) == 1:
        return nodes[0].mml
    return '<mrow>' + ''.join(n.mml for n in nodes) + '</mrow>'


def mo(ch, **attrs):
    a = ''.join(' %s="%s"' % (k.replace('_', ''), v) for k, v in attrs.items())
    return '<mo%s>%s</mo>' % (a, escape(ch, quote=False))


class TexError(Exception):
    pass


class Parser:
    def __init__(self, src, display):
        self.toks = tokenize(src)
        self.i = 0
        self.display = display
        self.style = None
        self.src = src

    # -- token helpers (whitespace tokens are skipped) --
    def peek(self, k=0):
        j, n = self.i, -1
        while j < len(self.toks):
            if self.toks[j][0] != 'ws':
                n += 1
                if n == k:
                    return self.toks[j]
            j += 1
        return (None, None)

    def take(self):
        while self.i < len(self.toks) and self.toks[self.i][0] == 'ws':
            self.i += 1
        t = self.toks[self.i] if self.i < len(self.toks) else (None, None)
        self.i += 1
        return t

    def expect(self, val):
        t = self.take()
        if t[1] != val:
            raise TexError('expected %r got %r in %r' % (val, t[1], self.src))

    def raw_group(self):
        """Read a {...} group verbatim (for \\text, \\begin, \\operatorname)."""
        self.expect('{')
        depth, parts = 1, []
        while True:
            if self.i >= len(self.toks):
                raise TexError('unclosed group in %r' % self.src)
            t = self.toks[self.i]
            self.i += 1
            if t[0] == 'ws':
                parts.append(' ')
                continue
            if t[1] == '{':
                depth += 1
            elif t[1] == '}':
                depth -= 1
                if depth == 0:
                    break
            parts.append(t[1])
        return parts

    # -- grammar --
    def parse_list(self, enders=()):
        nodes = []
        while True:
            kind, val = self.peek()
            if kind is None or val in enders:
                return nodes
            if val == '}':
                return nodes
            node = self.parse_scripted(nodes)
            if node is not None:
                nodes.append(node)

    def parse_arg(self):
        """One argument: a {group} or a single token atom."""
        kind, val = self.peek()
        if kind == 'num' and len(val) > 1 and val[1].isdigit():
            # TeX shorthand such as \frac12: an unbraced argument is one digit
            j = self.i
            while self.toks[j][0] == 'ws':
                j += 1
            self.toks[j] = ('num', val[1:])
            return Node('<mn>%s</mn>' % val[0])
        if val == '{':
            self.take()
            nodes = self.parse_list()
            self.expect('}')
            return Node(row(nodes) if nodes else '<mrow></mrow>')
        node = self.parse_atom([])
        return node if node is not None else Node('<mrow></mrow>')

    def parse_scripted(self, prev):
        base = self.parse_atom(prev)
        if base is None:
            return None
        sub = sup = None
        primes = 0
        while True:
            kind, val = self.peek()
            if val == '^' and sup is None:
                self.take()
                sup = self.parse_arg()
            elif val == '_' and sub is None:
                self.take()
                sub = self.parse_arg()
            elif val == "'":
                self.take()
                primes += 1
            else:
                break
        if primes:
            pm = mo('′' * primes)
            sup = Node(pm if sup is None else '<mrow>%s%s</mrow>' % (pm, sup.mml))
        if sub is None and sup is None:
            return self.apply_func(base) if base.func else base
        under = base.limits and self.display
        if sub is not None and sup is not None:
            tag = 'munderover' if under else 'msubsup'
            mml = '<%s>%s%s%s</%s>' % (tag, base.mml, sub.mml, sup.mml, tag)
        elif sub is not None:
            tag = 'munder' if under else 'msub'
            mml = '<%s>%s%s</%s>' % (tag, base.mml, sub.mml, tag)
        else:
            tag = 'mover' if under else 'msup'
            mml = '<%s>%s%s</%s>' % (tag, base.mml, sup.mml, tag)
        node = Node(mml, op=base.op and base.limits, func=base.func)
        return self.apply_func(node) if base.func else node

    def apply_func(self, node):
        """Function name followed by ApplyFunction; thin space unless '(' follows."""
        nxt = self.peek()[1]
        tight = nxt in (None, '(', '[', r'\left', r'\big', r'\Big', r'\bigl',
                        r'\Bigl', '}', '&', '\\\\', r'\end', r'\right', ',', ')')
        space = '0' if tight else '0.1667em'
        return Node('<mrow>%s<mo lspace="0" rspace="%s">&#x2061;</mo></mrow>'
                    % (node.mml, space))

    def ident(self, ch, upright=False):
        s = self.style
        if s in ('bf', 'bi', 'cal', 'bb', 'sf', 'tt', 'it'):
            return Node('<mi>%s</mi>' % styled(ch, s))
        if upright or s == 'rm':
            return Node('<mi mathvariant="normal">%s</mi>' % escape(ch))
        return Node('<mi>%s</mi>' % escape(ch))

    def parse_atom(self, prev):
        kind, val = self.take()
        if kind is None:
            return None
        if kind == 'letter':
            return self.ident(val)
        if kind == 'num':
            if self.style in ('bf', 'bb', 'sf', 'tt'):
                return Node('<mn>%s</mn>' % ''.join(styled(c, self.style) for c in val))
            return Node('<mn>%s</mn>' % val)
        if kind == 'ch':
            return self.parse_char(val, prev)
        if kind == 'cmdsym':
            return self.parse_cmdsym(val[1], prev)
        return self.parse_cmd(val[1:], prev)

    def unary(self, sym, prev):
        """Treat +/- as a prefix operator when nothing binary precedes it."""
        last = prev[-1] if prev else None
        nxt = self.peek()[1]
        if nxt is None or nxt in ('}', '&', '\\\\', '\\end', '\\right', ']',
                                  ')', '^', '_', ',', '='):
            return Node(mo(sym), op=True)
        if last is None or (last.op and not last.closing):
            operand = self.parse_scripted([])
            inner = mo(sym) + (operand.mml if operand is not None else '')
            return Node('<mrow>%s</mrow>' % inner)
        return Node(mo(sym), op=True)

    def parse_char(self, c, prev):
        if c == '{':
            nodes = self.parse_list()
            self.expect('}')
            return Node(row(nodes) if nodes else '<mrow></mrow>')
        if c == '-':
            return self.unary('−', prev)
        if c == '+':
            return self.unary('+', prev)
        if c in '([':
            return Node(mo(c, stretchy='false'), op=True)
        if c in ')]':
            return Node(mo(c, stretchy='false'), op=True, closing=True)
        if c == '|':
            closing = bool(prev) and not (prev[-1].op and not prev[-1].closing)
            return Node(mo('|', stretchy='false'), op=True, closing=closing)
        if c == '~':
            return Node('<mspace width="0.333em"></mspace>')
        if c == '*':
            return Node(mo('∗'), op=True)
        if c == '/':
            return Node(mo('/', stretchy='false'), op=True)
        if c == '&':
            raise TexError('stray & in %r' % self.src)
        if c == '}':
            raise TexError('unexpected } in %r' % self.src)
        if c in '=<>,;:!?.':
            return Node(mo(c), op=c not in '.!')
        if c == "'":
            return Node(mo('′'))
        return Node(mo(c), op=True)

    def parse_cmdsym(self, c, prev):
        if c in SPACES:
            return Node('<mspace width="%s"></mspace>' % SPACES[c])
        if c == '!':
            return None
        if c == '|':
            closing = bool(prev) and not (prev[-1].op and not prev[-1].closing)
            return Node(mo('‖', stretchy='false'), op=True, closing=closing)
        if c in '{}':
            return Node(mo(c, stretchy='false'), op=True, closing=(c == '}'))
        if c == '\\':
            return None  # line break outside a table: ignore
        if c in '%&#_$':
            return Node('<mi mathvariant="normal">%s</mi>' % escape(c))
        raise TexError('unknown control symbol \\%s in %r' % (c, self.src))

    def read_delim(self):
        kind, val = self.take()
        if kind == 'cmd' or kind == 'cmdsym':
            key = val
        else:
            key = val
        if key not in DELIMS:
            raise TexError('bad delimiter %r in %r' % (key, self.src))
        return DELIMS[key]

    def parse_cmd(self, name, prev):
        if name in GREEK_LOWER:
            return self.ident(GREEK_LOWER[name])
        if name in GREEK_UPPER:
            if self.style in ('bf', 'bi', 'it'):
                return Node('<mi>%s</mi>' % styled(GREEK_UPPER[name], self.style))
            return Node('<mi mathvariant="normal">%s</mi>' % GREEK_UPPER[name])
        if name in ORD_SYMBOLS:
            ch = ORD_SYMBOLS[name]
            if self.style in ('bf', 'bi') and ch in _GREEK_SPECIAL:
                return Node('<mi>%s</mi>' % styled(ch, self.style))
            return Node('<mi mathvariant="normal">%s</mi>' % ch)
        if name == 'T':  # transpose, upright T
            return Node('<mi mathvariant="normal">T</mi>')
        if name in OPS:
            ch = OPS[name]
            return Node(mo(ch), op=ch not in '…⋯⋮⋱')
        if name in SPACES:
            return Node('<mspace width="%s"></mspace>' % SPACES[name])
        if name in STYLE_CMDS:
            saved = self.style
            self.style = STYLE_CMDS[name]
            arg = self.parse_arg()
            self.style = saved
            return arg
        if name in ('text', 'textrm', 'mbox', 'textbf', 'textit'):
            txt = ''.join(self.raw_group())
            txt = txt.replace('\\%', '%').replace('\\&', '&').replace('\\,', ' ')
            st = ''
            if name == 'textbf':
                st = ' style="font-weight:bold"'
            elif name == 'textit':
                st = ' style="font-style:italic"'
            # Chromium trims leading/trailing spaces inside <mtext>: emit them as mspace
            pad = '<mspace width="0.3em"></mspace>'
            core = txt.strip(' ')
            mml = '<mtext%s>%s</mtext>' % (st, escape(core, quote=False))
            if txt[:1] == ' ':
                mml = pad + mml
            if txt[-1:] == ' ':
                mml = mml + pad
            return Node('<mrow>%s</mrow>' % mml if mml.count('<') > 2 else mml)
        if name == 'operatorname':
            txt = ''.join(self.raw_group()).replace('\\,', ' ')
            return Node('<mi>%s</mi><mo>&#x2061;</mo>' % escape(txt))
        if name in ('frac', 'dfrac', 'tfrac', 'cfrac'):
            num = self.parse_arg()
            den = self.parse_arg()
            mml = '<mfrac>%s%s</mfrac>' % (num.mml, den.mml)
            if name == 'dfrac':
                mml = '<mstyle displaystyle="true">%s</mstyle>' % mml
            elif name == 'tfrac':
                mml = '<mstyle displaystyle="false">%s</mstyle>' % mml
            return Node(mml)
        if name == 'binom':
            a = self.parse_arg()
            b = self.parse_arg()
            return Node('<mrow>%s<mfrac linethickness="0">%s%s</mfrac>%s</mrow>'
                        % (mo('('), a.mml, b.mml, mo(')')))
        if name == 'sqrt':
            if self.peek()[1] == '[':
                self.take()
                idx = self.parse_list(enders=(']',))
                self.expect(']')
                arg = self.parse_arg()
                return Node('<mroot>%s%s</mroot>' % (arg.mml, row(idx)))
            arg = self.parse_arg()
            return Node('<msqrt>%s</msqrt>' % arg.mml)
        if name in ACCENTS:
            ch, stretch = ACCENTS[name]
            arg = self.parse_arg()
            return Node('<mover accent="true">%s%s</mover>'
                        % (arg.mml, mo(ch, stretchy='true' if stretch else 'false')))
        if name == 'underline':
            arg = self.parse_arg()
            return Node('<munder accentunder="true">%s%s</munder>' % (arg.mml, mo('_', stretchy='true')))
        if name in ('underbrace', 'overbrace'):
            arg = self.parse_arg()
            if name == 'underbrace':
                mml = '<munder accentunder="true">%s%s</munder>' % (arg.mml, mo('⏟', stretchy='true'))
            else:
                mml = '<mover accent="true">%s%s</mover>' % (arg.mml, mo('⏞', stretchy='true'))
            return Node(mml, limits=True)
        if name in ('xrightarrow', 'xleftarrow'):
            arg = self.parse_arg()
            arrow = '→' if name == 'xrightarrow' else '←'
            return Node('<mover><mo stretchy="true" minsize="2em">%s</mo><mpadded lspace="0.3em" width="+0.6em">%s</mpadded></mover>'
                        % (arrow, arg.mml), op=True)
        if name in ('overset', 'stackrel'):
            top = self.parse_arg()
            base = self.parse_arg()
            return Node('<mover>%s%s</mover>' % (base.mml, top.mml), op=True)
        if name == 'underset':
            bot = self.parse_arg()
            base = self.parse_arg()
            return Node('<munder>%s%s</munder>' % (base.mml, bot.mml))
        if name in FUNCS or name in NAMED_FUNCS:
            label = NAMED_FUNCS.get(name, name)
            if len(label) == 1:
                return Node('<mi mathvariant="normal">%s</mi>' % label, func=True)
            return Node('<mi>%s</mi>' % label, func=True)
        if name in LIMIT_FUNCS:
            label = LIMIT_FUNCS[name]
            return Node('<mi>%s</mi>' % label, limits=True, op=True)
        if name in BIG_OPS:
            ch = BIG_OPS[name]
            lim = name not in ('int', 'oint')
            attrs = ' largeop="true"' if self.display else ''
            return Node('<mo%s movablelimits="false">%s</mo>' % (attrs, ch),
                        limits=lim, op=True)
        if name == 'left':
            left = self.read_delim()
            nodes = self.parse_list(enders=('\\right',))
            self.expect('\\right')
            right = self.read_delim()
            inner = ''.join(n.mml for n in nodes)
            l = mo(left, stretchy='true', symmetric='true') if left else ''
            r = mo(right, stretchy='true', symmetric='true') if right else ''
            return Node('<mrow>%s<mrow>%s</mrow>%s</mrow>' % (l, inner, r))
        if name in ('big', 'Big', 'bigg', 'Bigg', 'bigl', 'bigr', 'Bigl',
                    'Bigr', 'biggl', 'biggr', 'Biggl', 'Biggr'):
            size = {'big': '1.2em', 'Big': '1.6em', 'bigg': '2.05em',
                    'Bigg': '2.5em'}[name.rstrip('lr')]
            d = self.read_delim()
            return Node(mo(d, stretchy='true', symmetric='true', minsize=size,
                           maxsize=size), op=True, closing=name.endswith('r'))
        if name == 'begin':
            env = ''.join(self.raw_group())
            return self.parse_env(env)
        if name == 'textcolor' or name == 'hl':
            cls = ''.join(self.raw_group())
            arg = self.parse_arg()
            return Node('<mrow class="mc-%s">%s</mrow>' % (cls, arg.mml))
        if name == 'boxed':
            arg = self.parse_arg()
            return Node('<mrow class="mboxed">%s</mrow>' % arg.mml)
        if name == 'phantom':
            arg = self.parse_arg()
            return Node('<mpadded style="visibility:hidden">%s</mpadded>' % arg.mml)
        if name in ('displaystyle',):
            return None
        if name == 'not':
            nxt = self.parse_atom(prev)
            return nxt
        raise TexError('unknown command \\%s in %r' % (name, self.src))

    def parse_env(self, env):
        rows, cur = [], []
        while True:
            cells_nodes = self.parse_list(enders=('&', '\\\\', '\\end'))
            cur.append(row(cells_nodes) if cells_nodes else '')
            kind, val = self.take()
            if val == '&':
                continue
            if val == '\\\\':
                rows.append(cur)
                cur = []
                continue
            if val == '\\end':
                name = ''.join(self.raw_group())
                if name != env:
                    raise TexError('mismatched \\end{%s} for %s' % (name, env))
                if any(c for c in cur):
                    rows.append(cur)
                break
            raise TexError('unterminated environment %s in %r' % (env, self.src))
        ncol = max(len(r) for r in rows) if rows else 0
        trs = []
        for r in rows:
            tds = []
            for j in range(ncol):
                cell = r[j] if j < len(r) else ''
                if env in ('aligned', 'align', 'align*', 'alignedat'):
                    cls = 'al-r' if j % 2 == 0 else 'al-l'
                elif env == 'cases':
                    cls = 'al-l'
                else:
                    cls = 'al-c'
                tds.append('<mtd class="%s">%s</mtd>' % (cls, cell))
            trs.append('<mtr>%s</mtr>' % ''.join(tds))
        kind = 'mt-aligned' if env.startswith('align') else (
            'mt-cases' if env == 'cases' else 'mt-matrix')
        table = '<mtable class="%s">%s</mtable>' % (kind, ''.join(trs))
        fences = {'bmatrix': ('[', ']'), 'pmatrix': ('(', ')'),
                  'vmatrix': ('|', '|'), 'Vmatrix': ('‖', '‖'),
                  'cases': ('{', ''), 'matrix': ('', ''),
                  'aligned': ('', ''), 'align': ('', ''), 'align*': ('', ''),
                  'smallmatrix': ('', ''), 'array': ('', '')}
        if env not in fences:
            raise TexError('unknown environment %s' % env)
        l, r = fences[env]
        out = ''
        if l:
            out += mo(l, stretchy='true', symmetric='true')
        out += table
        if r:
            out += mo(r, stretchy='true', symmetric='true')
        return Node('<mrow>%s</mrow>' % out)


def tex_to_mathml(src, display=False):
    p = Parser(src, display)
    nodes = p.parse_list()
    if p.peek()[0] is not None:
        raise TexError('unbalanced braces in %r' % src)
    body = ''.join(n.mml for n in nodes)
    if display:
        # Chromium pushes <math display="block"> onto its own page when
        # printing, so display equations are inline math in a block span.
        return ('<span class="eq"><math displaystyle="true"><mrow>%s</mrow>'
                '</math></span>' % body)
    return '<math><mrow>%s</mrow></math>' % body


_DISPLAY_RE = re.compile(r'\$\$(.+?)\$\$', re.S)
_INLINE_RE = re.compile(r'(?<![\\$])\$(?!\$)(.+?)(?<!\\)\$', re.S)


def convert_html(text):
    """Replace $$...$$ and $...$ in an HTML fragment by MathML."""
    from html import unescape
    text = _DISPLAY_RE.sub(lambda m: tex_to_mathml(unescape(m.group(1)), True), text)
    text = _INLINE_RE.sub(lambda m: tex_to_mathml(unescape(m.group(1)), False), text)
    return text.replace('\\$', '$')


if __name__ == '__main__':
    import sys
    print(tex_to_mathml(sys.argv[1], display=len(sys.argv) > 2))
