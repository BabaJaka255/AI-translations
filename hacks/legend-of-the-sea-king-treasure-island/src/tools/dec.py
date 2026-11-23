import sys, struct
sys.path.insert(0, 'tools')
from table import T
EXE = 'files/SLPS_021.72'
def off(a): return a - 0x80010000 + 0x800
def ch(w):
    if w >= 0xff00: return '{%X}' % (w & 0xff)
    return T.get(w, '[%x]' % w)
PARAM = {0xfffc, 0xfff7, 0xfff8}
def words_to_text(ws):
    out = []; i = 0
    while i < len(ws):
        w = ws[i]
        if w in PARAM and i + 1 < len(ws): out.append('{%X:%d}' % (w & 0xf, ws[i + 1])); i += 2; continue
        if w >= 0xfff0: out.append('{%X}' % (w & 0xf))
        else: out.append(T.get(w, '[%x]' % w))
        i += 1
    return ''.join(out)
def dec_at(d, a, maxw=4000):
    o = off(a); s = []
    for k in range(maxw):
        w = struct.unpack_from('<H', d, o + 2 * k)[0]
        if w == 0xffff: return ''.join(s), k + 1
        s.append(ch(w))
    return ''.join(s), maxw
def syms():
    out = []
    for line in open('sym.txt'):
        p = line.split()
        if len(p) >= 3 and p[1] == 'sym2': out.append((int(p[0], 16), p[2]))
    return sorted(set(out))
