"""Show how the builder lays out English strings: / = new line, // = new page."""
import sys, json
sys.path.insert(0, 'tools')
import insert as I
S = I.load_script()
en = I.load_en(); toks, w = I.prepare(en, S)
NAMES = {'fffa': '<A>', 'fffb': '<B>', 'fff7': '<N>'}
def show(t):
    out = ''
    for k, v in t:
        if k == 't': out += v
        elif k == 'nl': out += ' / '
        elif k == 'pg': out += ' // ' if v == [0xfffd] else ' //9 '
        elif k == 'tab': out += '[>%d]' % v
        elif k == 'w': out += NAMES.get('%04x' % v[0][0], '<%x>' % v[0][0]) if v[0][0] not in (0xfff8,) else ''
    return out
ids = [int(a) for a in sys.argv[1:]] if len(sys.argv) > 1 else sorted(toks)
for i in ids:
    if i in toks: print(i, show(toks[i]))
