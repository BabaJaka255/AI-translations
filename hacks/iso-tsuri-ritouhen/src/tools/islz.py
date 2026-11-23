"""LZ format of Iso Tsuri (decompressor $80:EF1C).

byte 0: unused ($FE), word 1-2: number of tokens. Then groups of 8 tokens, each led by a flag byte (LSB first):
1 = literal byte; 0 = back reference: b0 b1 [b2]
  distance = ((b1 & 0x0F) << 8 | b0) + 1
  length   = (b1 >> 4) + 2            if b1 >> 4 != 0
           = b2 + 18                  otherwise
The copy is a forward MVN, so overlapping references repeat bytes.
"""

def decompress(d, off=0):
    n = d[off + 1] | d[off + 2] << 8
    i = off + 3; out = bytearray(); t = 0
    while t < n:
        flags = d[i]; i += 1
        for b in range(8):
            if t >= n: break
            if flags >> b & 1:
                out.append(d[i]); i += 1
            else:
                b0, b1 = d[i], d[i + 1]; i += 2
                dist = ((b1 & 0x0F) << 8 | b0) + 1
                if b1 >> 4: ln = (b1 >> 4) + 2
                else: ln = d[i] + 18; i += 1
                s = len(out) - dist
                for k in range(ln): out.append(out[s + k])
            t += 1
    return bytes(out), i - off

def compress(src):
    toks = []; i = 0; n = len(src)
    while i < n:
        best_len, best_d = 0, 0
        lo = max(0, i - 4096)
        maxl = min(273, n - i)
        if maxl >= 3:
            # simple search
            for s in range(i - 1, lo - 1, -1):
                l = 0
                while l < maxl and src[s + l] == src[i + l]: l += 1
                if l > best_len:
                    best_len, best_d = l, i - s
                    if l == maxl: break
        if best_len >= 3:
            toks.append((best_d, best_len)); i += best_len
        else:
            toks.append(src[i]); i += 1
    out = bytearray([0xFE, len(toks) & 0xff, len(toks) >> 8])
    for g in range(0, len(toks), 8):
        grp = toks[g:g + 8]; flags = 0; body = bytearray()
        for b, t in enumerate(grp):
            if isinstance(t, int):
                flags |= 1 << b; body.append(t)
            else:
                d, l = t; d -= 1
                if l <= 17: body += bytes([d & 0xff, (d >> 8) | (l - 2) << 4])
                else: body += bytes([d & 0xff, d >> 8, l - 18])
        out.append(flags); out += body
    return bytes(out)
