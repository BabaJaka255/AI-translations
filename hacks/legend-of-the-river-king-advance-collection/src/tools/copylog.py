# Log every LZ77 / CpuSet / DMA copy (any source) from a given frame on.
import gba
L = []
START = [0]
for name, get in [('swi_0b', lambda s, r, pc: (r[0], r[1], r[2])), ('swi_0c', lambda s, r, pc: (r[0], r[1], r[2])),
                  ('swi_11', lambda s, r, pc: (r[0], r[1], 0)), ('swi_12', lambda s, r, pc: (r[0], r[1], 0)),
                  ('_run_dma', lambda s, n: tuple(s.dma_int[n]))]:
    o = getattr(gba.GBA, name)
    def f(self, *a, o=o, get=get, name=name):
        s = get(self, *a)
        if self.frame >= START[0]: L.append((self.frame, name, s[0], s[1], s[2]))
        return o(self, *a)
    setattr(gba.GBA, name, f)
def show(rom_only=False):
    seen = set(); out = []
    for fr, n, a, b, c in L:
        if (n, a, b) in seen or (rom_only and not 0x8000000 <= a < 0xa000000): continue
        if 0x3001b00 <= a < 0x3002000 or 0x3007e00 <= a or b in (0x7000000, 0x30029b0): continue
        seen.add((n, a, b)); out.append('f%d %s %x->%x %x' % (fr, n, a, b, c))
    return '\n'.join(out)
