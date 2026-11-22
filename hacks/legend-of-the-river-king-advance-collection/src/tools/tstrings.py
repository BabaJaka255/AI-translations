import struct, pickle
import ocr
rom = ocr.rom
refs = pickle.load(open('allrefs.pkl', 'rb'))

def read_str(o):
    out = []
    while True:
        v = struct.unpack_from('<H', rom, o)[0]; o += 2
        if v == 0xff: return out
        out.append(v)
        if len(out) > 40: return out

def tables(lo=0x1fe000, hi=0x202400):
    res = []
    for o in range(lo, hi, 4):
        v = struct.unpack_from('<I', rom, o)[0]
        if 0x08000000 + lo <= v < 0x08000000 + hi: res.append((o, v - 0x08000000))
    groups, cur = [], []
    for o, v in res:
        if cur and o == cur[-1][0] + 4: cur.append((o, v))
        else:
            if cur: groups.append(cur)
            cur = [(o, v)]
    groups.append(cur)
    return groups

def decode(s, kana, base=0):
    o = ''
    for v in s:
        t = (v & 0x3ff) - base
        if v == 0xfe: o += '/'
        elif v == 0xfd: o += '_'
        else: o += kana.get(t, '[%x]' % v)
    return o
