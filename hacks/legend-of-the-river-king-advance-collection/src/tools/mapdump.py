import sys, struct, ocr
from lzscan import lz77
rom = open('../rom/k34.gba', 'rb').read()
def dump(block, m, rows=20, game='g3', w=32, base=0, extra=None):
    k = ocr.read_block(block, game)
    k = {t + base: c for t, c in k.items()}
    if extra: k.update({t + extra[1]: c for t, c in ocr.read_block(extra[0], game).items()})
    d, _ = lz77(rom, m, limit=0x10000); hw = struct.unpack('<%dH' % (len(d) // 2), d)
    for r in range(min(rows, len(hw) // w)):
        print('%2d' % r, ' '.join('%03x%s' % (v & 0x3ff, k.get(v & 0x3ff, '.')) for v in hw[r * w:r * w + 20]))
if __name__ == '__main__':
    a = [int(x, 16) for x in sys.argv[1:]]
    dump(a[0], a[1], extra=(a[2], a[3]) if len(a) > 2 else None)
