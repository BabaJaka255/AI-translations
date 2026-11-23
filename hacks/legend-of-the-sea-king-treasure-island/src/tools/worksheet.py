"""Worksheet for translating: JP line + exact TM hit + best fuzzy TM match.  python3 tools/worksheet.py lo hi"""
import sys, json, re, difflib
sys.path.insert(0, 'tools')
from tm import load, norm
tm = load(); keys = list(tm)
S = json.load(open('out/script_jp.json'))
hits = {int(k): v for k, v in json.load(open('out/tm_hits.json')).items()}
lo, hi = int(sys.argv[1]), int(sys.argv[2])
for o in S[lo:hi + 1]:
    i = o['id']; jp = o['jp']
    line = '%d|%s%s' % (i, 'U ' if o['unref'] else '', jp)
    print(line)
    if i in hits: print('   = ' + hits[i]); continue
    k = norm(re.sub(r'\{[0-9A-F]:\d+\}', '', jp))
    if len(k) >= 6:
        m = difflib.get_close_matches(k, keys, 1, 0.55)
        if m: print('   ~ %s => %s' % (m[0][:60], tm[m[0]][0][0][:200]))
