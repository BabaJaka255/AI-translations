"""Pointer references (code lui pairs + data words) into the exe, and string candidates."""
import struct, sys, collections
sys.path.insert(0, 'tools')
from dec import EXE, off, ch
d = open(EXE, 'rb').read()
BASE = 0x80010000 - 0x800
CODE_LO, CODE_HI = 0x80013554, 0x800c0000   # .text (approx from SYM; data after)
END = BASE + len(d)
def valid_string(a, maxw=2000):
    o = a - BASE
    if o < 0x800 or o + 2 > len(d): return None
    n = 0; good = 0
    while n < maxw:
        if o + 2 * n + 2 > len(d): return None
        w = struct.unpack_from('<H', d, o + 2 * n)[0]
        if w == 0xffff: break
        if w >= 0xff00: pass
        elif w < 1068: good += 1
        else: return None
        n += 1
    else: return None
    return n if n >= 1 else None
def refs():
    out = []
    lui = {}
    for o in range(CODE_LO - BASE, CODE_HI - BASE, 4):
        ins = struct.unpack_from('<I', d, o)[0]
        op = ins >> 26; rs = (ins >> 21) & 31; rt = (ins >> 16) & 31; imm = ins & 0xffff
        if op == 0x0f: lui[rt] = (imm << 16, o); continue
        if op in (0x09, 0x0d, 0x23, 0x21, 0x25, 0x2b, 0x29, 0x28, 0x20, 0x24) and rs in lui and o - lui[rs][1] < 0x100:
            s = imm - 0x10000 if (imm & 0x8000 and op != 0x0d) else imm
            v = (lui[rs][0] + s) & 0xffffffff
            if 0x800b0000 <= v < END: out.append(('code', lui[rs][1] + BASE, o + BASE, op, v))
        # kill registers written by this instruction
        if op == 0:
            lui.pop((ins >> 11) & 31, None)
        elif op in (0x08, 0x09, 0x0a, 0x0b, 0x0c, 0x0d, 0x0e, 0x20, 0x21, 0x23, 0x24, 0x25):
            lui.pop(rt, None)
        elif op == 3:
            lui.pop(31, None)
    for o in range(0xa0000, len(d) - 3, 4):
        v = struct.unpack_from('<I', d, o)[0]
        if 0x800b0000 <= v < END: out.append(('data', o + BASE, None, None, v))
    for o in range(0x800, CODE_LO - BASE, 4):   # rdata before text
        v = struct.unpack_from('<I', d, o)[0]
        if 0x800b0000 <= v < END: out.append(('rdata', o + BASE, None, None, v))
    return out
if __name__ == '__main__':
    R = refs()
    tg = collections.defaultdict(list)
    for r in R: tg[r[4]].append(r)
    strs = {a: valid_string(a) for a in tg}
    strs = {a: n for a, n in strs.items() if n}
    print('refs', len(R), 'targets', len(tg), 'string targets', len(strs))
    import json
    json.dump({hex(a): n for a, n in sorted(strs.items())}, open('view/strtargets.json', 'w'))
