# Log LZ77 decompressions (source -> dest) while driving the emulator.
import gba
LOG = []
_o12, _o11 = gba.GBA.swi_12, gba.GBA.swi_11
gba.GBA.swi_12 = lambda self, r, pc: (LOG.append((r[0] - 0x08000000, r[1])), _o12(self, r, pc))
gba.GBA.swi_11 = lambda self, r, pc: (LOG.append((r[0] - 0x08000000, r[1])), _o11(self, r, pc))
def show():
    return ' '.join('%x->%x' % (a, b) for a, b in LOG if b >= 0x6000000)
