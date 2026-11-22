"""Dump all text from the data track (copy 1).  usage: dump_script.py data.iso out_dir
Writes script.json (one entry per string slot) and script_dump.txt."""
import sys, os, re, json
sys.path.insert(0, os.path.dirname(__file__))
from kslib import parse, sjis_ok, CTRL
COPY2 = 1478
d = open(sys.argv[1], 'rb').read()[:COPY2 * 2048]
out = sys.argv[2]
# immediate references: ldx #hi / ldy #lo
refs = {}
for m in re.finditer(rb'\xa2(.)\xa0(.)', d, re.S): refs.setdefault(m.group(1)[0] << 8 | m.group(2)[0], []).append(m.start())
def valid(p):
    lo, hi = d[p], d[p + 1]
    return (hi in CTRL) or sjis_ok(hi, lo)
found = {}
for par in (0, 1):
    p = par
    while p + 1 < len(d):
        if not valid(p): p += 2; continue
        s = p
        while p + 1 < len(d) and valid(p): p += 2
        if d[p:p + 2] == b'\0\0':
            r = parse(d, s)
            if r:
                txt, n = r
                kana = sum(1 for ch in txt if '぀' <= ch <= 'ヿ' or ch in '。、！？　')
                prev0 = s >= 2 and d[s - 2:s] == b'\0\0'
                if (len(txt) >= 3 and kana >= max(1, len(txt) // 4)) or (prev0 and kana >= 1 and len(txt) >= 2):
                    found[s] = (txt, n)
        p += 2
# also strings that start right after another string's terminator (chains of short items)
changed = True
while changed:
    changed = False
    for s, (t, n) in list(found.items()):
        q = s + n
        if q not in found:
            r = parse(d, q)
            if r and r[0] and any('぀' <= ch <= 'ヿ' or '一' <= ch <= '鿿' for ch in r[0]):
                found[q] = r; changed = True
# drop entries contained in another entry
ents = sorted(found.items())
keep = []
for s, (t, n) in ents:
    if keep and s < keep[-1][0] + keep[-1][1][1]: continue
    keep.append((s, (t, n)))
items = []
for i, (s, (t, n)) in enumerate(keep):
    sec = s // 2048
    items.append(dict(id=i, off=s, sector=sec, size=n, jp=t, refs=len([1 for A, ps in refs.items() for q in ps
                                                                        if (A & 0x1FFF) == ((s - (sec // 4 * 4 * 2048 if 0 else 0)) & 0x1FFF) and False])))
json.dump(items, open(os.path.join(out, 'script.json'), 'w'), ensure_ascii=False, indent=0)
with open(os.path.join(out, 'script_dump.txt'), 'w') as f:
    for it in items: f.write('%04d %06X s%03d %3dB  %s\n' % (it['id'], it['off'], it['sector'], it['size'], it['jp']))
print(len(items), 'strings,', sum(len(it['jp']) for it in items), 'chars,', len(set(it['jp'] for it in items)), 'unique')
