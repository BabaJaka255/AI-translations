"""Minimal two-pass HuC6280 assembler for small patches.
asm(src, org, symbols) -> bytes.  Syntax: 'label:' lines, 'op operand', '.db a,b', '.dw a', ';' comments.
Operands: #expr, expr, expr,x, expr,y, (expr), (expr),y, (expr,x). Expressions are Python with labels/symbols.
zp mode is used when the operand is < $100 and the opcode has a zp form (force abs with '!' prefix)."""
import re, sys, os
sys.path.insert(0, os.path.dirname(__file__))
from dis6280 import T
OPS = {}
for c, (n, m) in T.items(): OPS.setdefault(n, {})[m] = c
def asm(src, org, syms=None):
    syms = dict(syms or {})
    lines = []
    for raw in src.splitlines():
        l = raw.split(';')[0].strip()
        while True:
            m = re.match(r'^([A-Za-z_]\w*):\s*(.*)$', l)
            if not m: break
            lines.append(('label', m.group(1))); l = m.group(2).strip()
        if l: lines.append(('ins', l))
    def ev(e, final):
        e = e.replace('$', '0x')
        try: return eval(e, {}, syms)
        except NameError:
            if final: raise
            return 0
    out = b''
    for final in (False, True):
        pc = org; out = bytearray()
        for kind, l in lines:
            if kind == 'label': syms[l] = pc; continue
            op, _, arg = l.partition(' '); op = op.lower(); arg = arg.strip()
            if op in ('.db', '.dw'):
                for a in [x for x in re.split(r',(?![^(]*\))', arg) if x.strip()]:
                    a=a.strip()
                    if a.startswith('"'): out += a.strip('"').encode(); pc += len(a.strip('"')); continue
                    v = ev(a, final)
                    out += bytes([v & 255]) if op == '.db' else bytes([v & 255, (v >> 8) & 255]); pc += 1 if op == '.db' else 2
                continue
            modes = OPS[op]; force = '!' in arg; arg = arg.replace('!', '')
            if not arg: mode = 'acc' if 'acc' in modes else 'imp'; b = []
            elif arg.startswith('#'): mode = 'imm'; b = [ev(arg[1:], final) & 255]
            elif re.match(r'^\(.*\),y$', arg, re.I): mode = 'izy'; b = [ev(arg[1:-3], final)]
            elif re.match(r'^\(.*,x\)$', arg, re.I):
                v = ev(arg[1:-3], final); mode = 'izx' if 'izx' in modes and v < 256 and not force else 'iax'; b = [v & 255] if mode == 'izx' else [v & 255, v >> 8]
            elif arg.startswith('(') and arg.endswith(')'):
                v = ev(arg[1:-1], final); mode = 'izp' if 'izp' in modes and v < 256 else 'ind'; b = [v] if mode == 'izp' else [v & 255, v >> 8]
            else:
                parts = [p.strip() for p in arg.split(',')]
                if 'zrel' in modes:
                    z = ev(parts[0], final); t = ev(parts[1], final); r = t - (pc + 3)
                    if final and not -128 <= r < 128: raise ValueError('branch range ' + l)
                    mode = 'zrel'; b = [z, r & 255]
                elif 'rel' in modes:
                    t = ev(arg, final); r = t - (pc + 2)
                    if final and not -128 <= r < 128: raise ValueError('branch range ' + l)
                    mode = 'rel'; b = [r & 255]
                else:
                    v = ev(parts[0], final); idx = parts[1].lower() if len(parts) > 1 else ''
                    zm, am = {'': ('zp', 'abs'), 'x': ('zpx', 'abx'), 'y': ('zpy', 'aby')}[idx]
                    if v < 256 and zm in modes and not force: mode = zm; b = [v]
                    else: mode = am; b = [v & 255, (v >> 8) & 255]
            if mode not in modes: raise ValueError('bad mode %s for %s' % (mode, l))
            out += bytes([modes[mode]] + [x & 255 for x in b]); pc += 1 + len(b)
    asm.syms = syms
    return bytes(out)
