"""Fune Tarou LZSS ($C0:D6C9). stream: byte 0 (unused), u16 length, then groups of flag byte + 8 items.
flag bit (LSB first) 1 = literal; 0 = 2 bytes b0,b1: offset = (b0 | (b1&15)<<8) + 1, n = b1>>4;
length = n + 2 if n else next byte + 18."""
def decompress(rom, o, maxlen=0x10000):
    L = rom[o+1] | rom[o+2] << 8
    if L == 0 or L > maxlen: return None, 0
    out = bytearray(); y = o + 3
    groups = [8] * (L >> 3) + ([L & 7] if L & 7 else [])
    for cnt in groups:
        flag = rom[y]; y += 1
        for _ in range(cnt):
            if flag & 1:
                out.append(rom[y]); y += 1
            else:
                b0, b1 = rom[y], rom[y+1]; y += 2
                off = (b0 | (b1 & 15) << 8) + 1; n = b1 >> 4
                if n: ln = n + 2
                else: ln = rom[y] + 18; y += 1
                s = len(out) - off
                if s < 0: return None, 0
                for k in range(ln): out.append(out[s + k])
            flag >>= 1
    return bytes(out), y - o

def compress(data):
    """Greedy LZSS for the format above. Item count in the header = number of items."""
    items = []; i = 0; n = len(data)
    while i < n:
        best = (0, 0)
        for off in range(1, min(i, 4096) + 1):
            s = i - off; ln = 0
            while i + ln < n and ln < 273 and data[s + ln] == data[i + ln]: ln += 1
            if ln > best[0]: best = (ln, off)
        if best[0] >= 3:
            ln, off = best; o = off - 1
            if ln <= 17: items.append(bytes([o & 0xFF, (o >> 8) | (ln - 2) << 4]))
            else: items.append(bytes([o & 0xFF, o >> 8, ln - 18]))
            i += ln
        else:
            items.append(data[i:i+1]); i += 1
    out = bytearray([0, len(items) & 0xFF, len(items) >> 8])
    for g in range(0, len(items), 8):
        grp = items[g:g+8]; flag = 0
        for k, it in enumerate(grp):
            if len(it) == 1: flag |= 1 << k
        out.append(flag)
        for it in grp: out += it
    return bytes(out)
