import sys
def lz77(r, o, limit=0x20000):
    if r[o] != 0x10: return None
    size = r[o+1] | r[o+2] << 8 | r[o+3] << 16
    if size == 0 or size > limit or size % 32: return None
    out = bytearray(); i = o + 4
    try:
        while len(out) < size:
            flags = r[i]; i += 1
            for b in range(8):
                if len(out) >= size: break
                if flags & 0x80:
                    a, c = r[i], r[i+1]; i += 2
                    n = (a >> 4) + 3; d = ((a & 15) << 8 | c) + 1
                    if d > len(out): return None
                    for _ in range(n): out.append(out[-d])
                else:
                    out.append(r[i]); i += 1
                flags <<= 1
    except IndexError:
        return None
    return bytes(out[:size]), i - o
