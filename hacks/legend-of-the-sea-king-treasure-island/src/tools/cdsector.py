"""Mode 2 Form 1 CD sector EDC/ECC (ECMA-130) and file patching for the PS1 disc image."""
EDC = [0] * 256
for i in range(256):
    e = i
    for _ in range(8): e = (e >> 1) ^ (0xD8018001 if e & 1 else 0)
    EDC[i] = e
F = [0] * 256; B = [0] * 256
for i in range(256):
    j = (i << 1) ^ (0x11D if i & 0x80 else 0); F[i] = j & 0xff; B[i ^ j & 0xff] = i
def edc(data):
    e = 0
    for b in data: e = (e >> 8) ^ EDC[(e ^ b) & 0xff]
    return e
def _ecc(sec, major, minor, mmul, minc, dest):
    size = major * minor
    for m in range(major):
        idx = (m >> 1) * mmul + (m & 1); a = b = 0
        for n in range(minor):
            t = sec[12 + idx]; idx += minc
            if idx >= size: idx -= size
            a ^= t; b ^= t; a = F[a]
        a = B[F[a] ^ b]
        sec[12 + dest + m] = a; sec[12 + dest + m + major] = a ^ b
def form1(sector):
    s = bytearray(sector)
    s[0x818:0x81c] = edc(s[0x10:0x818]).to_bytes(4, 'little')
    hdr = s[12:16]; s[12:16] = bytes(4)
    _ecc(s, 86, 24, 2, 86, 0x81C - 12)
    _ecc(s, 52, 43, 86, 88, 0x8C8 - 12)
    s[12:16] = hdr
    return bytes(s)
def write_file(img, lba, data):
    """Overwrite a file's user data in place (bytearray img), sector by sector."""
    for i in range(0, len(data), 2048):
        o = (lba + i // 2048) * 2352
        chunk = data[i:i + 2048]
        s = bytearray(img[o:o + 2352])
        s[24:24 + len(chunk)] = chunk
        img[o:o + 2352] = form1(s)
if __name__ == '__main__':
    import sys
    d = open(sys.argv[1], 'rb').read(); bad = 0
    for i in range(int(sys.argv[2]), int(sys.argv[3])):
        s = d[i * 2352:(i + 1) * 2352]
        if s[18] & 0x20: continue
        if form1(s) != s: bad += 1
    print('mismatch', bad)
