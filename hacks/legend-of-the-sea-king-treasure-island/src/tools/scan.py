"""Find u16 glyph strings (FFFF-terminated) in the exe data area."""
import sys, struct, collections
sys.path.insert(0, 'tools')
from dec import *
d = open(EXE, 'rb').read()
def scan(lo=0x800, hi=None, minlen=2):
    hi = hi or len(d)
    res = []; i = lo
    while i < hi - 1:
        j = i; n = 0; kana = 0
        while j < hi - 1:
            w = struct.unpack_from('<H', d, j)[0]
            if w == 0xffff: break
            if w < 1068 or 0xff00 <= w: n += 1; kana += (32 <= w < 1068); j += 2
            else: break
        if j < hi - 1 and struct.unpack_from('<H', d, j)[0] == 0xffff and n >= minlen and kana * 2 >= n:
            res.append((i, j + 2)); i = j + 2
        else:
            i += 2
    return res
if __name__ == '__main__':
    r = scan()
    cc = collections.Counter()
    for a, b in r:
        for k in range(a, b - 2, 2):
            w = struct.unpack_from('<H', d, k)[0]
            if w >= 0xff00: cc[w] += 1
    print(len(r), sum(b - a for a, b in r))
    print(sorted((hex(k), v) for k, v in cc.items()))
    # region summary
    prev = None
    for a, b in r:
        if prev is None or a - prev > 64: print('region start', hex(a), hex(a - 0x800 + 0x80010000))
        prev = b
