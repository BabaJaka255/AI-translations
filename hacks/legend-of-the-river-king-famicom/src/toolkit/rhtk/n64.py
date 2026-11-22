"""Nintendo 64 cartridge tools: byte order, header, CIC/CRC, MIO0/Yay0/Yaz0, MIPS refs.

See docs/N64.md. Everything works on bytes; nothing writes the original ROM.
"""
from __future__ import annotations

import re
import struct
import zlib

# ------------------------------------------------------------------ byte order

MAGIC_Z64 = b"\x80\x37\x12\x40"  # big endian (native), .z64
MAGIC_V64 = b"\x37\x80\x40\x12"  # 16-bit byteswapped (Doctor V64), .v64
MAGIC_N64 = b"\x40\x12\x37\x80"  # 32-bit little endian, .n64


def byte_order(data: bytes) -> str:
    m = bytes(data[:4])
    if m == MAGIC_Z64:
        return "z64"
    if m == MAGIC_V64:
        return "v64"
    if m == MAGIC_N64:
        return "n64"
    return "unknown"


def _swap16(b: bytes) -> bytes:
    a = bytearray(b)
    a[0::2], a[1::2] = b[1::2], b[0::2]
    return bytes(a)


def _swap32(b: bytes) -> bytes:
    a = bytearray(b)
    a[0::4], a[1::4], a[2::4], a[3::4] = b[3::4], b[2::4], b[1::4], b[0::4]
    return bytes(a)


def to_z64(data: bytes) -> bytes:
    """Return the ROM in big-endian (.z64) order, whatever order it came in."""
    order = byte_order(data)
    if order == "z64":
        return bytes(data)
    if order == "v64":
        return _swap16(data)
    if order == "n64":
        return _swap32(data)
    raise ValueError("not an N64 ROM (unknown first word %s)" % data[:4].hex())


def from_z64(data: bytes, order: str) -> bytes:
    if order == "z64":
        return bytes(data)
    if order == "v64":
        return _swap16(data)
    if order == "n64":
        return _swap32(data)
    raise ValueError(order)


# ------------------------------------------------------------------ CIC and CRC

CIC_SEEDS = {6101: 0xF8CA4DDC, 6102: 0xF8CA4DDC, 6103: 0xA3886759, 6105: 0xDF26F436, 6106: 0x1FEA617A}
# CRC32 of the IPL3 boot code (ROM 0x40-0x1000) for the retail CICs. Used as a hint;
# detect_cic() also confirms by recomputing the header CRC with each seed.
IPL3_CRC32 = {0x6170A4A1: 6101, 0x90BB6CB5: 6102, 0x0B050EE0: 6103, 0x98BC2C86: 6105,
              0xACC8580A: 6106, 0x009E9EA3: 7102}
M = 0xFFFFFFFF


def calc_crc(data: bytes, cic: int) -> tuple[int, int]:
    """The two header checksums (ROM 0x10 and 0x14) the boot code verifies.

    `data` must be big endian. Covers ROM 0x1000-0x101000 only, so data past
    1 MiB + 4 KiB never needs a CRC update (but updating is harmless)."""
    seed = CIC_SEEDS[6102 if cic in (6101, 7102) else cic]
    buf = bytes(data[:0x101000])
    if len(buf) < 0x101000:
        buf = buf + bytes(0x101000 - len(buf))
    words = struct.unpack_from(">262144I", buf, 0x1000)
    t1 = t2 = t3 = t4 = t5 = t6 = seed
    boot = struct.unpack_from(">64I", buf, 0x750) if cic == 6105 else None
    for n, d in enumerate(words):
        s = (t6 + d) & M
        if s < t6:
            t4 = (t4 + 1) & M
        t6 = s
        t3 ^= d
        sh = d & 0x1F
        r = ((d << sh) | (d >> (32 - sh))) & M if sh else d
        t5 = (t5 + r) & M
        if t2 > d:
            t2 ^= r
        else:
            t2 ^= t6 ^ d
        if boot is not None:
            t1 = (t1 + (boot[n & 0x3F] ^ d)) & M
        else:
            t1 = (t1 + (t5 ^ d)) & M
    if cic == 6103:
        return ((t6 ^ t4) + t3) & M, ((t5 ^ t2) + t1) & M
    if cic == 6106:
        return ((t6 * t4) + t3) & M, ((t5 * t2) + t1) & M
    return t6 ^ t4 ^ t3, t5 ^ t2 ^ t1


def detect_cic(data: bytes) -> int | None:
    """Which CIC this ROM boots with: the seed whose CRC matches the header."""
    hdr = struct.unpack_from(">II", data, 0x10)
    hint = IPL3_CRC32.get(zlib.crc32(data[0x40:0x1000]))
    order = [hint] if hint else []
    order += [c for c in (6102, 6101, 6103, 6105, 6106, 7102) if c != hint]
    for c in order:
        if c is not None and calc_crc(data, c) == hdr:
            return c
    return hint


def fix_crc(data: bytes, cic: int | None = None) -> tuple[bytes, int, tuple[int, int]]:
    """Return (rom with recomputed header CRC, cic used, (crc1, crc2))."""
    cic = cic or IPL3_CRC32.get(zlib.crc32(data[0x40:0x1000])) or 6102
    c1, c2 = calc_crc(data, cic)
    out = bytearray(data)
    struct.pack_into(">II", out, 0x10, c1, c2)
    return bytes(out), cic, (c1, c2)


# ------------------------------------------------------------------ header

REGIONS = {"J": "Japan", "E": "USA", "P": "Europe", "D": "Germany", "F": "France", "I": "Italy",
           "S": "Spain", "U": "Australia", "A": "All", "N": "Canada", "X": "Europe", "Y": "Europe"}


def _title(raw: bytes) -> str:
    raw = raw.rstrip(b"\x00 ")
    for enc in ("ascii", "shift_jis", "cp932"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            pass
    return raw.decode("latin-1")


def header(data: bytes) -> dict:
    """Parse the 0x40-byte header of a big-endian ROM."""
    clock, entry, libultra, crc1, crc2 = struct.unpack_from(">IIIII", data, 0x04)
    code = data[0x3B:0x3F].decode("latin-1")
    cic = detect_cic(data)
    ok = cic is not None and calc_crc(data, cic) == (crc1, crc2)
    return {
        "title": _title(data[0x20:0x34]),
        "game_code": code,
        "region": REGIONS.get(code[3:4], "?"),
        "version": data[0x3F],
        "entry_point": f"0x{entry:08X}",
        "clock_rate": f"0x{clock:08X}",
        "libultra": f"0x{libultra:08X}",
        "crc1": f"0x{crc1:08X}", "crc2": f"0x{crc2:08X}",
        "cic": cic, "crc_ok": ok,
        "size": len(data), "size_mbit": len(data) * 8 // (1 << 20),
    }


def info(raw: bytes) -> dict:
    order = byte_order(raw)
    data = to_z64(raw)
    h = header(data)
    h.update({"byte_order": order, "crc32_as_given": f"{zlib.crc32(raw):08X}",
              "crc32_z64": f"{zlib.crc32(data):08X}"})
    return h


def boot_segment(data: bytes, length: int | None = None) -> tuple[int, int, int]:
    """(vaddr, rom_offset, size) of the code the boot loader copies: ROM 0x1000 -> entry point.

    libultra boot always copies 1 MiB; the real code segment is usually shorter
    and the game DMAs other segments itself (find them with dma_refs / lui pairs)."""
    entry, = struct.unpack_from(">I", data, 0x08)
    size = length or min(0x100000, len(data) - 0x1000)
    return entry, 0x1000, size


# ------------------------------------------------------------------ MIPS pointer search (big endian)

def mips_hilo_refs(data: bytes, segments, target: int, window: int = 64):
    """Find `lui rX, hi` + `addiu/ori/lw/...  rY, lo(rX)` that build `target`.

    N64 games almost never store string pointers in code as plain words; they
    load them with a lui/addiu pair. `segments` is [(vaddr, rom_off, size)].
    Yields (rom_offset_of_lui, rom_offset_of_low, mnemonic)."""
    hi_signed = ((target + 0x8000) >> 16) & 0xFFFF
    hi_plain = (target >> 16) & 0xFFFF
    lo = target & 0xFFFF
    low_ops = {0x09: "addiu", 0x0D: "ori", 0x20: "lb", 0x21: "lh", 0x23: "lw", 0x24: "lbu",
               0x25: "lhu", 0x28: "sb", 0x29: "sh", 0x2B: "sw", 0x31: "lwc1", 0x39: "swc1", 0x37: "ld"}
    for _vaddr, foff, size in segments:
        end = min(len(data), foff + size)
        end -= (end - foff) % 4
        words = struct.unpack_from(f">{(end - foff) // 4}I", data, foff)
        for i, w in enumerate(words):
            if w >> 26 != 0x0F:
                continue
            imm, rt = w & 0xFFFF, (w >> 16) & 31
            if imm not in (hi_signed, hi_plain):
                continue
            for j in range(i + 1, min(len(words), i + 1 + window // 4)):
                v = words[j]
                op, rs = v >> 26, (v >> 21) & 31
                if rs == rt and op in low_ops and (v & 0xFFFF) == lo:
                    if imm == (hi_plain if op == 0x0D else hi_signed):
                        yield foff + i * 4, foff + j * 4, low_ops[op]
                        break
                if op == 0x0F and (v >> 16) & 31 == rt:
                    break


def word_refs(data: bytes, value: int, align: int = 4):
    """ROM offsets of 32-bit big-endian words equal to `value` (RAM pointers or ROM offsets in tables)."""
    pat = struct.pack(">I", value)
    i = data.find(pat)
    while i != -1:
        if i % align == 0:
            yield i
        i = data.find(pat, i + 1)


# ------------------------------------------------------------------ compression

def mio0_decompress(data: bytes, off: int = 0) -> bytes:
    """Nintendo MIO0 (used by SM64, many first- and third-party games)."""
    if data[off:off + 4] != b"MIO0":
        raise ValueError("no MIO0 header")
    size, comp, raw = struct.unpack_from(">III", data, off + 4)
    out = bytearray()
    bits = off + 0x10
    comp += off
    raw += off
    bit = 0
    cur = 0
    while len(out) < size:
        if bit == 0:
            cur, = struct.unpack_from(">I", data, bits)
            bits += 4
            bit = 32
        bit -= 1
        if cur & (1 << bit):
            out.append(data[raw])
            raw += 1
        else:
            v, = struct.unpack_from(">H", data, comp)
            comp += 2
            n, d = (v >> 12) + 3, (v & 0xFFF) + 1
            for _ in range(n):
                out.append(out[-d])
    return bytes(out[:size])


def yay0_decompress(data: bytes, off: int = 0) -> bytes:
    """Nintendo Yay0 (MIO0 layout, Yaz0-style long counts)."""
    if data[off:off + 4] != b"Yay0":
        raise ValueError("no Yay0 header")
    size, link, chunk = struct.unpack_from(">III", data, off + 4)
    out = bytearray()
    bits = off + 0x10
    link += off
    chunk += off
    bit = 0
    cur = 0
    while len(out) < size:
        if bit == 0:
            cur, = struct.unpack_from(">I", data, bits)
            bits += 4
            bit = 32
        bit -= 1
        if cur & (1 << bit):
            out.append(data[chunk])
            chunk += 1
        else:
            v, = struct.unpack_from(">H", data, link)
            link += 2
            d = (v & 0xFFF) + 1
            n = v >> 12
            if n == 0:
                n = data[chunk] + 0x12
                chunk += 1
            else:
                n += 2
            for _ in range(n):
                out.append(out[-d])
    return bytes(out[:size])


def yaz0_decompress(data: bytes, off: int = 0) -> bytes:
    """Nintendo Yaz0 (Zelda OoT/MM, many later games)."""
    if data[off:off + 4] != b"Yaz0":
        raise ValueError("no Yaz0 header")
    size, = struct.unpack_from(">I", data, off + 4)
    src = off + 0x10
    out = bytearray()
    while len(out) < size:
        code = data[src]
        src += 1
        for bit in range(7, -1, -1):
            if len(out) >= size:
                break
            if code & (1 << bit):
                out.append(data[src])
                src += 1
            else:
                b1, b2 = data[src], data[src + 1]
                src += 2
                d = ((b1 & 0xF) << 8 | b2) + 1
                if b1 >> 4:
                    n = (b1 >> 4) + 2
                else:
                    n = data[src] + 0x12
                    src += 1
                for _ in range(n):
                    out.append(out[-d])
    return bytes(out)


def _matches(data: bytes, max_len: int, min_len: int = 3, window: int = 0x1000):
    """Greedy LZ parse: yields ('lit', byte) or ('ref', dist, length). Hash-chain search."""
    n = len(data)
    head: dict[bytes, list[int]] = {}
    i = 0
    while i < n:
        best_len, best_d = 0, 0
        if i + min_len <= n:
            key = data[i:i + 3]
            cands = head.get(key, ())
            lim = min(max_len, n - i)
            for j in reversed(cands[-64:]):
                d = i - j
                if d > window:
                    break
                k = 3
                while k < lim and data[j + k] == data[i + k]:
                    k += 1
                if k > best_len:
                    best_len, best_d = k, d
                    if k == lim:
                        break
        if best_len >= min_len:
            for p in range(i, i + best_len):
                head.setdefault(data[p:p + 3], []).append(p)
            yield ("ref", best_d, best_len)
            i += best_len
        else:
            head.setdefault(data[i:i + 3], []).append(i)
            yield ("lit", data[i])
            i += 1


def mio0_compress(data: bytes) -> bytes:
    flags: list[int] = []
    comp = bytearray()
    raw = bytearray()
    for t in _matches(data, 18):
        if t[0] == "lit":
            flags.append(1)
            raw.append(t[1])
        else:
            flags.append(0)
            comp += struct.pack(">H", ((t[2] - 3) << 12) | (t[1] - 1))
    while len(flags) % 32:
        flags.append(0)
    bits = bytearray()
    for k in range(0, len(flags), 32):
        w = 0
        for f in flags[k:k + 32]:
            w = (w << 1) | f
        bits += struct.pack(">I", w)
    comp_off = 0x10 + len(bits)
    if len(comp) % 4:
        comp += bytes(4 - len(comp) % 4)
    raw_off = comp_off + len(comp)
    return b"MIO0" + struct.pack(">III", len(data), comp_off, raw_off) + bytes(bits) + bytes(comp) + bytes(raw)


def yaz0_compress(data: bytes) -> bytes:
    out = bytearray(b"Yaz0" + struct.pack(">I", len(data)) + bytes(8))
    group: list = []

    def flush():
        code = 0
        body = bytearray()
        for k, t in enumerate(group):
            if t[0] == "lit":
                code |= 0x80 >> k
                body.append(t[1])
            else:
                d, n = t[1] - 1, t[2]
                if n >= 0x12:
                    body += bytes([d >> 8, d & 0xFF, n - 0x12])
                else:
                    body += bytes([((n - 2) << 4) | (d >> 8), d & 0xFF])
        out.append(code)
        out.extend(body)
        group.clear()

    for t in _matches(data, 0xFF + 0x12):
        group.append(t)
        if len(group) == 8:
            flush()
    if group:
        flush()
    return bytes(out)


CODECS = {"MIO0": mio0_decompress, "Yay0": yay0_decompress, "Yaz0": yaz0_decompress}


def scan_compressed(data: bytes, align: int = 4, verify: bool = True):
    """Find MIO0/Yay0/Yaz0 blocks. Yields dict(offset, kind, size, packed_size or None, ok)."""
    for kind, fn in CODECS.items():
        for m in re.finditer(re.escape(kind.encode()), data):
            o = m.start()
            if o % align:
                continue
            size, = struct.unpack_from(">I", data, o + 4)
            if not 0 < size < 0x2000000:
                continue
            rec = {"offset": o, "kind": kind, "size": size, "ok": None}
            if verify:
                try:
                    fn(data, o)
                    rec["ok"] = True
                except Exception:  # noqa: BLE001 - corrupt or false positive
                    rec["ok"] = False
            yield rec


# ------------------------------------------------------------------ text scanning helpers

SJIS_RUN = re.compile(rb"(?:[\x81-\x9F\xE0-\xEF][\x40-\x7E\x80-\xFC]|[\x20-\x7E]){3,}")
EUC_RUN = re.compile(rb"(?:[\xA1-\xFE][\xA1-\xFE]){4,}")


def text_runs(data: bytes, encoding: str = "sjis", min_kana: int = 2):
    """Yield (offset, decoded) for Shift-JIS or EUC-JP runs that contain Japanese kana."""
    rx, codec = (SJIS_RUN, "cp932") if encoding == "sjis" else (EUC_RUN, "euc_jp")
    for m in rx.finditer(data):
        raw = m.group()
        try:
            s = raw.decode(codec)
        except UnicodeDecodeError:
            continue
        kana = sum(1 for ch in s if "ぁ" <= ch <= "ヿ")
        if kana >= min_kana:
            yield m.start(), s
