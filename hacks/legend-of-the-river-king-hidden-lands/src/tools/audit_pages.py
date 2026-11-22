"""Dump how every message is laid out: one line per box line, boxes separated."""
import sys
sys.path.insert(0, 'tools')
import insert as I
S = I.load_script(); en = I.load_en()
toks, warns = I.prepare(en, S)
NAMES = {0xfffa: '<A>', 0xfffb: '<B>', 0xfff7: '<NAME>'}
def show(t):
    out = ''
    for k, v in t:
        if k == 't': out += v
        elif k == 'nl': out += '\n   '
        elif k == 'pg': out += '\n --\n   ' if v == [0xfffd] else '\n ==9==\n   '
        elif k == 'tab': out += '[>%d]' % v
        elif k == 'w': out += NAMES.get(v[0][0], '') 
    return out
ids = [int(a) for a in sys.argv[1:]] if len(sys.argv) > 1 else sorted(toks)
W = dict(warns.__iter__()) if False else {}
for i, w in warns: W.setdefault(i, []).append(w)
for i in ids:
    if i in toks:
        print('#%d %s' % (i, ' '.join(W.get(i, []))))
        print('   ' + show(toks[i]))
