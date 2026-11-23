"""IPS and BPS patch creation and application.

Distribute patches, never ROMs. Prefer BPS: it records CRC32s of the source
and target, so players get a clear error when they patch the wrong dump.
"""
from __future__ import annotations

import zlib

# ---------------------------------------------------------------- IPS -----

def ips_create(src: bytes, dst: bytes) -> bytes:
    if len(dst) > 0x1000000:
        raise ValueError("IPS cannot address past 16 MiB; use BPS")
    out = bytearray(b"PATCH")
    i, n = 0, len(dst)
    while i < n:
        if i < len(src) and src[i] == dst[i]:
            i += 1
            continue
        start = i
        while i < n and i - start < 0xFFFF and (i >= len(src) or src[i] != dst[i]):
            i += 1
        if start == 0x454F46:  # offset would read as "EOF"; back up one byte
            start -= 1
        chunk = dst[start:i]
        out += start.to_bytes(3, "big") + len(chunk).to_bytes(2, "big") + chunk
    out += b"EOF"
    if len(dst) < len(src):
        out += len(dst).to_bytes(3, "big")  # truncation extension
    return bytes(out)


def ips_apply(src: bytes, patch: bytes) -> bytes:
    if patch[:5] != b"PATCH":
        raise ValueError("not an IPS patch")
    out = bytearray(src)
    i = 5
    while patch[i:i + 3] != b"EOF":
        off = int.from_bytes(patch[i:i + 3], "big")
        size = int.from_bytes(patch[i + 3:i + 5], "big")
        i += 5
        if size == 0:  # RLE record
            run = int.from_bytes(patch[i:i + 2], "big")
            data = bytes([patch[i + 2]]) * run
            i += 3
        else:
            data = patch[i:i + size]
            i += size
        if len(out) < off + len(data):
            out.extend(b"\0" * (off + len(data) - len(out)))
        out[off:off + len(data)] = data
    i += 3
    if len(patch) - i == 3:
        del out[int.from_bytes(patch[i:i + 3], "big"):]
    return bytes(out)

# ---------------------------------------------------------------- BPS -----

def _vlq(n: int) -> bytes:
    out = bytearray()
    while True:
        x = n & 0x7F
        n >>= 7
        if n == 0:
            out.append(0x80 | x)
            return bytes(out)
        out.append(x)
        n -= 1


def _read_vlq(data: bytes, i: int) -> tuple[int, int]:
    n, shift = 0, 1
    while True:
        x = data[i]
        i += 1
        n += (x & 0x7F) * shift
        if x & 0x80:
            return n, i
        shift <<= 7
        n += shift


RUN = 32  # runs of one byte at least this long become TargetCopy (e.g. expanded ROM padding)


def _run_len(data: bytes, i: int) -> int:
    j = i
    while j < len(data) and data[j] == data[i]:
        j += 1
    return j - i


MIRROR = 16  # past the end of the source, runs this long that repeat the source become SourceCopy


def _mirror_len(src: bytes, dst: bytes, i: int) -> int:
    """Length of dst[i:] matching src at i mod len(src) (only past the end of src)."""
    L = len(src)
    if i < L or not L:
        return 0
    j = i
    while j < len(dst) and dst[j] == src[j % L]:
        j += 1
    return j - i


def bps_create(src: bytes, dst: bytes, metadata: str = "") -> bytes:
    """Linear BPS: SourceRead where bytes match in place, TargetRead otherwise,
    TargetCopy for long runs of one byte, and SourceCopy where an expanded ROM's
    new space repeats the source (mirror copies). Good for translations, where
    most data stays put, and for expanded ROMs."""
    meta = metadata.encode()
    out = bytearray(b"BPS1") + _vlq(len(src)) + _vlq(len(dst)) + _vlq(len(meta)) + meta
    i, n = 0, len(dst)
    dst_rel = src_rel = 0
    while i < n:
        start = i
        m = _mirror_len(src, dst, i)
        if m >= MIRROR:
            sp = i % len(src)
            d = sp - src_rel
            out += _vlq(((m - 1) << 2) | 2) + _vlq((abs(d) << 1) | (d < 0))  # SourceCopy
            src_rel = sp + m
            i += m
            continue
        if i < len(src) and src[i] == dst[i]:
            while i < n and i < len(src) and src[i] == dst[i]:
                i += 1
            out += _vlq(((i - start - 1) << 2) | 0)  # SourceRead
        else:
            # keep short matches (<4 bytes) inside the literal run; stop at a long run
            run = 0
            while i < n:
                if i < len(src) and src[i:i + 4] == dst[i:i + 4] and i + 4 <= min(n, len(src)):
                    break
                if i >= len(src) and _mirror_len(src, dst, i) >= MIRROR:
                    break
                run = _run_len(dst, i)
                if run >= RUN and not (i < len(src) and src[i] == dst[i]):
                    i += 1  # the run's first byte goes out literally, the rest copies it
                    break
                run = 0
                i += 1
            out += _vlq(((i - start - 1) << 2) | 1) + dst[start:i]  # TargetRead
            if run:
                d = (i - 1) - dst_rel
                out += _vlq(((run - 2) << 2) | 3) + _vlq((abs(d) << 1) | (d < 0))  # TargetCopy
                dst_rel = i - 1 + run - 1
                i += run - 1
    out += zlib.crc32(src).to_bytes(4, "little") + zlib.crc32(dst).to_bytes(4, "little")
    out += zlib.crc32(out).to_bytes(4, "little")
    return bytes(out)


def bps_apply(src: bytes, patch: bytes, check: bool = True) -> bytes:
    if patch[:4] != b"BPS1":
        raise ValueError("not a BPS patch")
    if zlib.crc32(patch[:-4]) != int.from_bytes(patch[-4:], "little"):
        raise ValueError("BPS patch is corrupt (patch CRC mismatch)")
    src_crc = int.from_bytes(patch[-12:-8], "little")
    dst_crc = int.from_bytes(patch[-8:-4], "little")
    if check and zlib.crc32(src) != src_crc:
        raise ValueError(f"wrong source ROM: CRC32 {zlib.crc32(src):08X}, patch expects {src_crc:08X}")
    i = 4
    src_size, i = _read_vlq(patch, i)
    dst_size, i = _read_vlq(patch, i)
    meta_size, i = _read_vlq(patch, i)
    i += meta_size
    out = bytearray()
    src_rel = dst_rel = 0
    end = len(patch) - 12
    while i < end:
        cmd, i = _read_vlq(patch, i)
        action, length = cmd & 3, (cmd >> 2) + 1
        if action == 0:
            out += src[len(out):len(out) + length]
        elif action == 1:
            out += patch[i:i + length]
            i += length
        else:
            d, i = _read_vlq(patch, i)
            d = -(d >> 1) if d & 1 else d >> 1
            if action == 2:
                src_rel += d
                out += src[src_rel:src_rel + length]
                src_rel += length
            else:
                dst_rel += d
                for _ in range(length):
                    out.append(out[dst_rel])
                    dst_rel += 1
    if check and zlib.crc32(out) != dst_crc:
        raise ValueError("patched output CRC mismatch")
    return bytes(out)


def apply_any(src: bytes, patch: bytes) -> bytes:
    if patch[:4] == b"BPS1":
        return bps_apply(src, patch)
    if patch[:5] == b"PATCH":
        return ips_apply(src, patch)
    raise ValueError("unknown patch format")
