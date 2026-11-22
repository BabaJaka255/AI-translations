"""Dump every string of the main executable to out/script.json (id, offset, slot words, refs, text)."""
import sys, json, struct, collections
sys.path.insert(0, 'tools')
from strings import *
from decode import ch
from refs import refs
d = open(EXE, 'rb').read()
st = starts(d)
R = refs(d)
byt = collections.defaultdict(list)
for r in R: byt[r[4]].append(r)
out = []
for k, s in enumerate(st):
    e = s
    while struct.unpack_from('<H', d, e)[0] != 0xffff: e += 2
    nxt = st[k + 1] if k + 1 < len(st) and st[k + 1] > s else None
    reg_end = [b for a, b in REGIONS if a <= s < b][0]
    slot_end = nxt if nxt and nxt <= reg_end else ((e + 2 + 3) & ~3)
    words = [struct.unpack_from('<H', d, i)[0] for i in range(s, e, 2)]
    rs = byt.get(BASE + s, [])
    out.append(dict(id=k, off=s, addr=BASE + s, n=len(words), slot=(slot_end - s) // 2,
                    refs=[(r[0], r[1] + (BASE if r[0] == 'code' else 0)) for r in rs],
                    jp=''.join(ch(w) for w in words)))
json.dump(out, open(sys.argv[1], 'w'), ensure_ascii=False, indent=0)
print(len(out), sum(o['n'] for o in out), 'words; unreferenced', sum(1 for o in out if not o['refs']))
