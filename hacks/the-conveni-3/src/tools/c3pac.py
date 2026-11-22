"""The Conveni 3 (PS2) containers: PAC archives and LZS compression.

PAC:  "PAC\\0", u32 header_size, u32 count, then count x (u32 offset, u32 size); data 0x800-aligned.
LZS:  "LZS\\0", u32 unpacked_size, then Okumura-style LZSS: flag byte read LSB first,
      1 = literal byte, 0 = 2-byte reference (pos = b0 | (b1 & 0xF0) << 4, len = (b1 & 0x0F) + 3)
      into a 4096-byte ring that starts zero-filled at 0xFEE.
"""
import struct
import sys


def pac_read(data):
    assert data[:4] == b"PAC\0", "not a PAC"
    _hs, n = struct.unpack_from("<II", data, 4)
    return [data[o:o + s] for o, s in (struct.unpack_from("<II", data, 12 + i * 8) for i in range(n))]


def pac_build(files, align=0x800, first=None, header=None):
    """header: the original PAC's bytes up to its first file; keeps the name table that follows the offsets."""
    n = len(files)
    hs = 12 + n * 8
    pos = first or -(-hs // align) * align
    out = bytearray(pos)
    if header:
        out[:len(header)] = header[:pos]
    out[:12] = b"PAC\0" + struct.pack("<II", hs, n)
    for i, d in enumerate(files):
        struct.pack_into("<II", out, 12 + i * 8, len(out), len(d))
        out += d
        out += b"\0" * (-len(out) % align)
    return bytes(out)


def lzs_decompress(data, fill=0):
    assert data[:4] == b"LZS\0", "not LZS"
    size, = struct.unpack_from("<I", data, 4)
    ring = bytearray([fill]) * 4096
    r = 0xFEE
    out = bytearray()
    i, flags = 8, 0
    while len(out) < size and i < len(data):
        flags >>= 1
        if not flags & 0x100:
            flags = data[i] | 0xFF00
            i += 1
        if flags & 1:
            c = data[i]; i += 1
            out.append(c); ring[r] = c; r = (r + 1) & 0xFFF
        else:
            if i + 1 >= len(data):
                break
            b0, b1 = data[i], data[i + 1]; i += 2
            pos = b0 | (b1 & 0xF0) << 4
            for k in range((b1 & 0x0F) + 3):
                c = ring[(pos + k) & 0xFFF]
                out.append(c); ring[r] = c; r = (r + 1) & 0xFFF
    return bytes(out[:size])


def lzs_compress(raw, chain=512):
    """LZSS with optimal parsing (literal = 9 bits, match = 17 bits); decompresses with lzs_decompress.
    Usually a little smaller than the game's own packer, so repacked files fit their old slots."""
    N, F = 4096, 18
    n = len(raw)
    best_len = [0] * n
    best_src = [0] * n
    heads = {}
    for i in range(n):
        if i + 2 < n:
            key = raw[i:i + 3]
            lst = heads.get(key)
            if lst:
                bl, bj = 0, 0
                for j in reversed(lst[-chain:]):
                    if i - j >= N - F:
                        break
                    L = 3
                    while L < F and i + L < n and raw[j + L] == raw[i + L]:
                        L += 1
                    if L > bl:
                        bl, bj = L, j
                        if L == F:
                            break
                best_len[i], best_src[i] = bl, bj
                lst.append(i)
            else:
                heads[key] = [i]
    # cost[i] = bits to encode raw[i:]
    cost = [0] * (n + 1)
    choice = [0] * n
    for i in range(n - 1, -1, -1):
        c, ch = cost[i + 1] + 9, 1
        for L in range(3, best_len[i] + 1):
            v = cost[i + L] + 17
            if v < c:
                c, ch = v, L
        cost[i], choice[i] = c, ch
    out = bytearray(b"LZS\0" + struct.pack("<I", n))
    i = 0
    while i < n:
        flag_pos = len(out); out.append(0); flag = 0
        for bit in range(8):
            if i >= n:
                break
            L = choice[i]
            if L == 1:
                flag |= 1 << bit
                out.append(raw[i])
                i += 1
            else:
                pos = (0xFEE + best_src[i]) & 0xFFF
                out += bytes((pos & 0xFF, (pos >> 4) & 0xF0 | (L - 3)))
                i += L
        out[flag_pos] = flag
    return bytes(out)


if __name__ == "__main__":
    import os
    cmd, src, dest = sys.argv[1:4]
    if cmd == "unpack":  # unpack a PAC, decompressing LZS members
        os.makedirs(dest, exist_ok=True)
        for k, d in enumerate(pac_read(open(src, "rb").read())):
            if d[:4] == b"LZS\0":
                d = lzs_decompress(d)
                tag = d[:4].rstrip(b"\0").decode("ascii", "replace")
                name = f"{k:03d}.lzs." + (tag.lower() if tag.isalnum() else "bin")
            else:
                name = f"{k:03d}.raw"
            open(os.path.join(dest, name), "wb").write(d)


# ---- file checksums: the ELF keeps (name ptr, size, sum, xor) for 126 files at vaddr 0x283930 and checks them
SUM_TABLE, SUM_COUNT = 0x283930, 126


def _foff(v):
    return v - 0x205700 + 0xF6700


def file_sums(data):
    n = len(data) // 4
    words = struct.unpack_from(f"<{n}I", data)
    s, x = 0, 0
    for w in words:
        s = (s + w) & 0xFFFFFFFF
        x ^= w
    return len(data), s, x


def fix_sum(elf: bytearray, old, new):
    """Replace the (size, sum, xor) record of file data `old` with that of `new`, everywhere in the ELF.
    The game keeps at least two tables of these (vaddr 0x283930 and 0x283EA0) and hangs at boot on a mismatch."""
    a, b = struct.pack("<III", *file_sums(old)), struct.pack("<III", *file_sums(new))
    n = elf.count(a)
    if not n:
        raise KeyError("no checksum record for this file")
    elf[:] = elf.replace(a, b)
    return n
