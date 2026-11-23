"""Common console compression formats.

GBA/NDS BIOS-style formats start with a 4-byte header: type byte, then the
24-bit little-endian decompressed size.
    0x10  LZ77 (LZ10)   decompress + compress
    0x11  LZ11 (NDS)    decompress
    0x30  RLE           decompress + compress
Many games use their own schemes. When `rhtk scan-lz` finds nothing, find
the decompression routine in a debugger (see docs/WORKFLOW.md) and add a
codec here.
"""
from __future__ import annotations


def _header(data: bytes, off: int) -> tuple[int, int]:
    return data[off], int.from_bytes(data[off + 1:off + 4], "little")


def lz10_decompress(data: bytes, off: int = 0) -> tuple[bytes, int]:
    """Returns (output, compressed_size)."""
    kind, size = _header(data, off)
    if kind != 0x10:
        raise ValueError(f"not LZ10 data at 0x{off:X} (type 0x{kind:02X})")
    out = bytearray()
    i = off + 4
    while len(out) < size:
        flags = data[i]
        i += 1
        for bit in range(7, -1, -1):
            if len(out) >= size:
                break
            if flags >> bit & 1:
                b1, b2 = data[i], data[i + 1]
                i += 2
                length = (b1 >> 4) + 3
                disp = ((b1 & 0xF) << 8 | b2) + 1
                if disp > len(out):
                    raise ValueError("LZ10 back-reference before start of output")
                for _ in range(length):
                    out.append(out[-disp])
            else:
                out.append(data[i])
                i += 1
    return bytes(out[:size]), i - off


def lz11_decompress(data: bytes, off: int = 0) -> tuple[bytes, int]:
    kind, size = _header(data, off)
    if kind != 0x11:
        raise ValueError(f"not LZ11 data at 0x{off:X}")
    i = off + 4
    if size == 0:
        size = int.from_bytes(data[i:i + 4], "little")
        i += 4
    out = bytearray()
    while len(out) < size:
        flags = data[i]
        i += 1
        for bit in range(7, -1, -1):
            if len(out) >= size:
                break
            if flags >> bit & 1:
                b = data[i]
                ind = b >> 4
                if ind == 0:
                    length = (((b & 0xF) << 4) | (data[i + 1] >> 4)) + 0x11
                    disp = (((data[i + 1] & 0xF) << 8) | data[i + 2]) + 1
                    i += 3
                elif ind == 1:
                    length = (((b & 0xF) << 12) | (data[i + 1] << 4) | (data[i + 2] >> 4)) + 0x111
                    disp = (((data[i + 2] & 0xF) << 8) | data[i + 3]) + 1
                    i += 4
                else:
                    length = ind + 1
                    disp = (((b & 0xF) << 8) | data[i + 1]) + 1
                    i += 2
                for _ in range(length):
                    out.append(out[-disp])
            else:
                out.append(data[i])
                i += 1
    return bytes(out[:size]), i - off


def lz10_compress(src: bytes, vram_safe: bool = True) -> bytes:
    """Greedy LZ10. vram_safe avoids displacement 1, which breaks VRAM decompression."""
    out = bytearray([0x10]) + len(src).to_bytes(3, "little")
    min_disp = 2 if vram_safe else 1
    i = 0
    while i < len(src):
        flag_pos = len(out)
        out.append(0)
        flags = 0
        for bit in range(7, -1, -1):
            if i >= len(src):
                break
            best_len, best_disp = 0, 0
            for disp in range(min_disp, min(i, 0x1000) + 1):
                n = 0
                while n < 18 and i + n < len(src) and src[i + n] == src[i - disp + n]:
                    n += 1
                if n > best_len:
                    best_len, best_disp = n, disp
                    if n == 18:
                        break
            if best_len >= 3:
                flags |= 1 << bit
                d = best_disp - 1
                out += bytes([((best_len - 3) << 4) | (d >> 8), d & 0xFF])
                i += best_len
            else:
                out.append(src[i])
                i += 1
        out[flag_pos] = flags
    while len(out) % 4:
        out.append(0)
    return bytes(out)


def rle_decompress(data: bytes, off: int = 0) -> tuple[bytes, int]:
    kind, size = _header(data, off)
    if kind != 0x30:
        raise ValueError(f"not RLE data at 0x{off:X}")
    out = bytearray()
    i = off + 4
    while len(out) < size:
        f = data[i]
        i += 1
        if f & 0x80:
            out += bytes([data[i]]) * ((f & 0x7F) + 3)
            i += 1
        else:
            n = (f & 0x7F) + 1
            out += data[i:i + n]
            i += n
    return bytes(out[:size]), i - off


def rle_compress(src: bytes) -> bytes:
    out = bytearray([0x30]) + len(src).to_bytes(3, "little")
    i, lit = 0, bytearray()

    def flush():
        while lit:
            chunk = lit[:128]
            out.append(len(chunk) - 1)
            out.extend(chunk)
            del lit[:128]

    while i < len(src):
        n = 1
        while i + n < len(src) and n < 130 and src[i + n] == src[i]:
            n += 1
        if n >= 3:
            flush()
            out += bytes([0x80 | (n - 3), src[i]])
            i += n
        else:
            lit.append(src[i])
            i += 1
    flush()
    while len(out) % 4:
        out.append(0)
    return bytes(out)


def scan_lz10(data: bytes, min_size: int = 0x20, max_size: int = 0x40000, align: int = 4):
    """Yield (offset, decompressed_size, compressed_size) for plausible LZ10 blobs."""
    for off in range(0, len(data) - 4, align):
        if data[off] != 0x10:
            continue
        size = int.from_bytes(data[off + 1:off + 4], "little")
        if not min_size <= size <= max_size:
            continue
        try:
            out, used = lz10_decompress(data, off)
        except (ValueError, IndexError):
            continue
        yield off, len(out), used
