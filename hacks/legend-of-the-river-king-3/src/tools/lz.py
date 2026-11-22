"""GBA BIOS LZ77 (type 0x10) decompress / compress (VRAM-safe)."""

def decompress(d, off=0, maxout=None):
    assert d[off] == 0x10
    size = d[off+1] | d[off+2] << 8 | d[off+3] << 16
    if maxout and size > maxout: raise ValueError('too big')
    out = bytearray(); p = off + 4
    while len(out) < size:
        flags = d[p]; p += 1
        for bit in range(8):
            if len(out) >= size: break
            if flags & (0x80 >> bit):
                b1, b2 = d[p], d[p+1]; p += 2
                n = (b1 >> 4) + 3; disp = ((b1 & 15) << 8 | b2) + 1
                if disp > len(out): raise ValueError('bad disp')
                for _ in range(n): out.append(out[-disp])
            else:
                out.append(d[p]); p += 1
    return bytes(out[:size]), p - off

def compress(data, vram_safe=True):
    n = len(data); out = bytearray([0x10, n & 255, n >> 8 & 255, n >> 16 & 255])
    i = 0
    # index of 3-byte sequences for speed
    from collections import defaultdict
    table = defaultdict(list)
    while i < n:
        flagpos = len(out); out.append(0); flags = 0
        for bit in range(8):
            if i >= n: break
            best_len, best_disp = 0, 0
            if i + 2 < n:
                key = data[i:i+3]
                cands = table.get(key, [])
                for j in reversed(cands):
                    disp = i - j
                    if disp > 4096: break
                    if vram_safe and disp < 2: continue
                    l = 3
                    while l < 18 and i + l < n and data[j+l] == data[i+l]: l += 1
                    if l > best_len: best_len, best_disp = l, disp
                    if l == 18: break
            if best_len >= 3:
                flags |= 0x80 >> bit
                d = best_disp - 1
                out += bytes([((best_len - 3) << 4) | (d >> 8), d & 255])
                for k in range(i, i + best_len):
                    if k + 2 < n: table[data[k:k+3]].append(k)
                i += best_len
            else:
                if i + 2 < n: table[data[i:i+3]].append(i)
                out.append(data[i]); i += 1
        out[flagpos] = flags
    while len(out) % 4: out.append(0)
    return bytes(out)
