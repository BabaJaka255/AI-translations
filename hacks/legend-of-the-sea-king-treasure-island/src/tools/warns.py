"""List layout warnings with JP and EN text: python3 tools/warns.py [lo hi]"""
import sys, json; sys.path.insert(0, 'tools')
from insert import layout, Metrics
from textfmt import load_en
S = {o['id']: o for o in json.load(open('out/script_jp.json'))}
en = load_en(); M = Metrics()
lo, hi = (int(sys.argv[1]), int(sys.argv[2])) if len(sys.argv) > 2 else (0, 99999)
n = 0
for i in sorted(en):
    if not lo <= i < hi: continue
    o = S[i]
    if not o['jp'] and not o['words']: continue
    _, w = layout(en[i], o['words'], M)
    if w:
        n += 1
        print('%d  %s\n   JP %s\n   EN %s' % (i, '; '.join(sorted(set(w))), o['jp'], en[i]))
print(n, 'strings')
