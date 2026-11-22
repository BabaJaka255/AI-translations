"""Strings in the gaps between the main text regions (2-byte aligned, reached through pointer
tables or code). Written to out/script_extra.json with ids from 2491 on."""
import sys, json, struct
sys.path.insert(0, 'tools')
import strings
from decode import ch
GAPS = [(0xc02a6, 0xc0306), (0xc0620, 0xc0662), (0xc0da0, 0xc0f6e)]
strings.REGIONS[:] = GAPS
import refs
refs.REGIONS = GAPS
from refs import refs as find_refs
d = open(strings.EXE, 'rb').read()
B = strings.BASE
R = find_refs(d)
reffed = {r[4] - B for r in R}
out = []; k = 2491
for a, b in GAPS:
    i = a; st = []
    cur = a
    while cur < b:
        e = cur
        while e < b and struct.unpack_from('<H', d, e)[0] != 0xffff: e += 2
        # referenced addresses inside this run start strings themselves
        inner = sorted(x for x in reffed if cur < x < e)
        st.append(cur)
        cur = e + 2
    # build records
    for j, s in enumerate(st):
        e = s
        while struct.unpack_from('<H', d, e)[0] != 0xffff: e += 2
        nxt = st[j + 1] if j + 1 < len(st) else b
        rs = [r for r in R if s <= r[4] - B <= e]
        if rs: s = min(r[4] - B for r in rs)          # the pointer skips leading padding
        words = struct.unpack_from('<%dH' % ((e - s) // 2), d, s)
        out.append(dict(id=k, off=s, addr=B + s, n=len(words), slot=(nxt - s) // 2,
                        refs=[(r[0], r[1] + (B if r[0] == 'code' else 0), r[4]) for r in rs],
                        jp=''.join(ch(w) for w in words)))
        k += 1
json.dump(out, open('out/script_extra.json', 'w'), ensure_ascii=False, indent=0)
for o in out: print(o['id'], hex(o['off']), o['slot'], [(r[0], hex(r[1]), hex(r[2])) for r in o['refs']], o['jp'])
