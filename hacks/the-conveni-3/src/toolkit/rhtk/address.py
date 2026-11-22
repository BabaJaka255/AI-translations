"""Map between pointer values stored in a ROM and file offsets.

A mapping is described in project.json as a dict, e.g.
    {"type": "linear", "base": "0x0"}            file = ptr - base
    {"type": "gba"}                               file = ptr - 0x08000000
    {"type": "snes-lorom"}                        24-bit SNES CPU address, LoROM
    {"type": "snes-hirom"}                        24-bit SNES CPU address, HiROM
    {"type": "bank", "bank_size": "0x4000", "window": "0x4000", "bank": 3}
        16-bit pointer into a switchable bank window (GB, many NES mappers).
        file = bank*bank_size + (ptr - window), plus "header" bytes (NES: 16).
    {"type": "elf", "segments": [[vaddr, file_offset, size], ...]}
        Virtual address in a loaded ELF (PS2/PSP/PS1 executables). `rhtk xref
        --mapping elf` fills the segments from the file's program headers.
"""
from __future__ import annotations


def _int(v) -> int:
    return int(v, 0) if isinstance(v, str) else int(v)


class Mapper:
    def __init__(self, spec: dict):
        self.spec = spec
        self.type = spec.get("type", "linear")
        if self.type not in ("linear", "gba", "snes-lorom", "snes-hirom", "bank", "elf"):
            raise ValueError(f"unknown address mapping {self.type!r}")
        self.base = _int(spec.get("base", 0))
        self.header = _int(spec.get("header", 0))
        self.bank_size = _int(spec.get("bank_size", 0x4000))
        self.window = _int(spec.get("window", 0x4000))
        self.bank = _int(spec.get("bank", 0))
        self.segments = [tuple(_int(x) for x in seg) for seg in spec.get("segments", [])]

    def to_file(self, ptr: int) -> int:
        t = self.type
        if t == "elf":
            for vaddr, foff, size in self.segments:
                if vaddr <= ptr < vaddr + size:
                    return foff + ptr - vaddr
            raise ValueError(f"address 0x{ptr:X} is not in a loaded ELF segment")
        if t == "linear":
            off = ptr - self.base
        elif t == "gba":
            off = (ptr & 0x01FFFFFF)
        elif t == "snes-lorom":
            off = ((ptr & 0x7F0000) >> 1) | (ptr & 0x7FFF)
        elif t == "snes-hirom":
            off = ptr & 0x3FFFFF
        else:  # bank
            off = self.bank * self.bank_size + (ptr - self.window)
        return off + self.header

    def to_ptr(self, off: int) -> int:
        off -= self.header
        t = self.type
        if t == "elf":
            for vaddr, foff, size in self.segments:
                if foff <= off + self.header < foff + size:
                    return vaddr + off + self.header - foff
            raise ValueError(f"file offset 0x{off:X} is not in a loaded ELF segment")
        if t == "linear":
            return off + self.base
        if t == "gba":
            return off + 0x08000000
        if t == "snes-lorom":
            return (((off << 1) & 0x7F0000) | (off & 0x7FFF) | 0x8000) | 0x800000 * bool(self.spec.get("fastrom"))
        if t == "snes-hirom":
            return off | 0xC00000
        rel = off - self.bank * self.bank_size
        if not 0 <= rel < self.bank_size:
            raise ValueError(f"offset 0x{off:X} is outside bank {self.bank}; "
                             f"a 16-bit banked pointer cannot reach it")
        return rel + self.window


def read_ptr(data: bytes, off: int, size: int, endian: str = "little") -> int:
    return int.from_bytes(data[off:off + size], endian)


def write_ptr(buf: bytearray, off: int, value: int, size: int, endian: str = "little") -> None:
    mask = (1 << (8 * size)) - 1
    if value & ~mask:
        raise ValueError(f"pointer value 0x{value:X} does not fit in {size} bytes")
    buf[off:off + size] = value.to_bytes(size, endian)
