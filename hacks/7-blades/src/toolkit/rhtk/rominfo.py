"""Identify a ROM, report its header, and fix header checksums after editing."""
from __future__ import annotations

import hashlib
import zlib


def hashes(data: bytes) -> dict:
    return {"size": len(data), "crc32": f"{zlib.crc32(data):08X}",
            "md5": hashlib.md5(data).hexdigest(), "sha1": hashlib.sha1(data).hexdigest()}


def _ascii(b: bytes) -> str:
    return b.split(b"\0")[0].decode("ascii", "replace").strip()


def detect(data: bytes, name: str = "") -> dict:
    """Best-effort platform detection from headers and file extension."""
    ext = name.lower().rsplit(".", 1)[-1] if "." in name else ""
    info: dict = {"platform": "unknown"}
    if data[:4] == b"NES\x1a":
        info.update(platform="nes", prg_banks_16k=data[4], chr_banks_8k=data[5],
                    mapper=(data[6] >> 4) | (data[7] & 0xF0), header=16)
    elif len(data) >= 0xC0 and data[0x04:0x08] == bytes.fromhex("24FFAE51") and data[0xB2] == 0x96:
        info.update(platform="gba", title=_ascii(data[0xA0:0xAC]), code=_ascii(data[0xAC:0xB0]))
    elif len(data) >= 0x150 and data[0x104:0x108] == bytes.fromhex("CEED6666"):
        info.update(platform="gbc" if data[0x143] & 0x80 else "gb",
                    title=_ascii(data[0x134:0x143]), cart_type=f"0x{data[0x147]:02X}")
    elif len(data) >= 0x200 and data[0x100:0x104] in (b"SEGA", b" SEG"):
        info.update(platform="megadrive", title=_ascii(data[0x150:0x180]))
    elif len(data) >= 0x200 and data[0xC0:0xC4] == bytes.fromhex("24FFAE51"):
        info.update(platform="nds", title=_ascii(data[0:12]), code=_ascii(data[12:16]))
    elif ext in ("sfc", "smc") or len(data) % 0x8000 in (0, 0x200):
        copier = 0x200 if len(data) % 0x8000 == 0x200 else 0
        for kind, base in (("lorom", 0x7FC0), ("hirom", 0xFFC0)):
            h = copier + base
            if h + 0x20 > len(data):
                continue
            chk = int.from_bytes(data[h + 0x1E:h + 0x20], "little")
            comp = int.from_bytes(data[h + 0x1C:h + 0x1E], "little")
            if chk ^ comp == 0xFFFF:
                info.update(platform="snes", mapping=kind, title=_ascii(data[h:h + 21]),
                            copier_header=copier)
                break
    if data[:4] == b"\x7fELF" or ext in ("iso", "bin", "cue", "chd", "cso", "nsp", "xci", "3ds", "cia"):
        info.setdefault("note", "disc/archive image: extract the filesystem first (see docs/PLATFORMS.md)")
    return info


def set_rom_size(buf: bytearray, platform: str) -> str | None:
    """Update the header's ROM size field after expanding. Returns a note or None."""
    if platform in ("gb", "gbc"):
        code = (len(buf) // 0x8000).bit_length() - 1  # 32 KiB << code
        if 0x8000 << code != len(buf):
            raise ValueError(f"GB ROM size must be a power of two, got 0x{len(buf):X}")
        buf[0x148] = code
        return f"header ROM size 0x{code:02X}"
    return None


CHECKSUM_PLATFORMS = ("gb", "gbc", "gba", "snes", "megadrive")


def fix_checksum(buf: bytearray, platform: str, mapping: str = "lorom") -> str:
    """Fix the header checksum in place. Returns a description of what changed."""
    if platform in ("gb", "gbc"):
        x = 0
        for b in buf[0x134:0x14D]:
            x = (x - b - 1) & 0xFF
        buf[0x14D] = x
        g = (sum(buf) - buf[0x14E] - buf[0x14F]) & 0xFFFF
        buf[0x14E:0x150] = g.to_bytes(2, "big")
        return f"header 0x{x:02X}, global 0x{g:04X}"
    if platform == "gba":
        c = (-(sum(buf[0xA0:0xBD]) + 0x19)) & 0xFF
        buf[0xBD] = c
        return f"complement 0x{c:02X}"
    if platform == "snes":
        h = 0x7FC0 if mapping == "lorom" else 0xFFC0
        buf[h + 0x1C:h + 0x20] = bytes([0xFF, 0xFF, 0, 0])
        size = len(buf)
        # mirror up to a power of two the way the hardware sees it
        p = 1 << (size.bit_length() - 1)
        s = sum(buf[:p])
        if size > p:
            rest = buf[p:]
            s += sum(rest) * (p // len(rest))
        s &= 0xFFFF
        buf[h + 0x1C:h + 0x20] = (s ^ 0xFFFF).to_bytes(2, "little") + s.to_bytes(2, "little")
        return f"checksum 0x{s:04X}"
    if platform == "megadrive":
        s = 0
        for i in range(0x200, len(buf) - 1, 2):
            s = (s + (buf[i] << 8 | buf[i + 1])) & 0xFFFF
        buf[0x18E:0x190] = s.to_bytes(2, "big")
        return f"checksum 0x{s:04X}"
    return "no checksum for this platform"
