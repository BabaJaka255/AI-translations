# Log every ROM -> VRAM/palette copy (LZ77, CpuSet, CpuFastSet, DMA) while driving the emulator.
import gba, struct
LOG = []
def _wrap(name, getter):
    orig = getattr(gba.GBA, name)
    def f(self, *a):
        try:
            s = getter(self, *a)
            if s and 0x8000000 <= s[0] < 0xa000000 and s[1] >= 0x5000000:
                LOG.append((self.frame, name, s[0] - 0x8000000, s[1], s[2] if len(s) > 2 else 0))
        except Exception: pass
        return orig(self, *a)
    setattr(gba.GBA, name, f)
_wrap('swi_11', lambda self, r, pc: (r[0], r[1]))
_wrap('swi_12', lambda self, r, pc: (r[0], r[1]))
_wrap('swi_0b', lambda self, r, pc: (r[0], r[1], r[2]))
_wrap('swi_0c', lambda self, r, pc: (r[0], r[1], r[2]))
_wrap('_run_dma', lambda self, n: tuple(self.dma_int[n]))
def show(since=0):
    return '\n'.join('f%d %s %x->%x n=%x' % l for l in LOG if l[0] >= since)
