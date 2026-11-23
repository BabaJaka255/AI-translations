"""Dump all strings in the exe text area -> out/script_jp.json
Each: id, addr, n (words), slot (bytes available up to next string start / region), refs, jp, unref flag."""
import sys, json, struct, collections, bisect
sys.path.insert(0, 'tools')
from refs import refs, valid_string
from scan import scan
from dec import ch, EXE, words_to_text
d = open(EXE, 'rb').read(); BASE = 0x80010000 - 0x800
LO, HI = 0x800ce000, 0x800e5000
R = refs(); tg = collections.defaultdict(list)
for r in R:
    if LO <= r[4] < HI: tg[r[4]].append(r)
starts = {a for a in tg if valid_string(a)}
S = [(a + BASE, b + BASE) for a, b in scan(minlen=1) if LO <= a + BASE < HI]
st = sorted(starts)
ext = sorted((a, a + 2 * valid_string(a) + 2) for a in starts)
def inside(x):
    i = bisect.bisect_right(ext, (x, 1 << 40)) - 1
    while i >= 0 and ext[i][0] > x - 4000:
        if ext[i][0] <= x < ext[i][1]: return True
        i -= 1
    return False
unref = set()
for a, b in S:
    i = bisect.bisect_left(st, a)
    if not (i < len(st) and st[i] < b) and not inside(a): unref.add(a)
allst = sorted(starts | unref)
out = []
for k, a in enumerate(allst):
    n = valid_string(a)
    ws = [struct.unpack_from('<H', d, a - BASE + 2 * i)[0] for i in range(n)]
    end = a + 2 * n + 2
    nxt = allst[k + 1] if k + 1 < len(allst) else end
    # slot: through padding zeros up to next start (strings overlap if next start < end: tail sharing)
    slot = max(end, min(nxt, (end + 3) & ~3)) - a if nxt >= end else end - a
    rr = [dict(kind=r[0], at=hex(r[1]), at2=hex(r[2]) if r[2] else None, op=r[3]) for r in tg.get(a, [])]
    out.append(dict(id=k, addr=hex(a), n=n, slot=slot, overlap=nxt < end, refs=rr, unref=a in unref,
                    jp=words_to_text(ws), words=ws))
json.dump(out, open('out/script_jp.json', 'w'), ensure_ascii=False, indent=0)
print(len(out), 'strings,', sum(o['n'] for o in out), 'words;', sum(o['unref'] for o in out), 'unreferenced;',
      sum(o['overlap'] for o in out), 'overlapping')
