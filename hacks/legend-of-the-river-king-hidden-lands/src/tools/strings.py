"""Text regions and string starts in SLPS_015.36."""
import struct
EXE = 'files/SLPS_015.36'
BASE = 0x80010000 - 0x800
REGIONS = [(0xbfb04, 0xc02a6),
           (0xc0306, 0xc0620), (0xc0662, 0xc0da0), (0xc0f6e, 0xdc612)]
def starts(d):
    out = []
    for a, b in REGIONS:
        out.append(a)
        for i in range(a, b - 2, 2):
            if struct.unpack_from('<H', d, i)[0] == 0xffff:
                j = (i + 2 + 3) & ~3          # each string is a 4-aligned u16 array
                if j < b: out.append(j)
    return out
