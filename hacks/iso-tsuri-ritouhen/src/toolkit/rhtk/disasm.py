"""Disassembly and pointer cross-references.

`disasm` wraps Capstone (pip install capstone), which covers 6502/65816,
ARM/Thumb (GBA, NDS, 3DS), MIPS (PS1, PS2, PSP, N64), M68K (Mega Drive),
SH (Saturn) and x86. Game Boy / Color (SM83) uses the built-in table
disassembler in sm83.py (`--arch sm83`). Z80 is not covered: use an emulator
debugger for it. For whole-program work, import
the ROM into Ghidra (Java is installed in cloud sessions) with the right
loader extension.
"""
from __future__ import annotations

from .address import Mapper

ARCHS = {
    # name: (arch const, mode const) resolved lazily from capstone
    "6502": ("CS_ARCH_MOS65XX", "CS_MODE_MOS65XX_6502"),
    "65816": ("CS_ARCH_MOS65XX", "CS_MODE_MOS65XX_65816_LONG_MX"),
    "arm": ("CS_ARCH_ARM", "CS_MODE_ARM"),
    "thumb": ("CS_ARCH_ARM", "CS_MODE_THUMB"),
    "mips": ("CS_ARCH_MIPS", "CS_MODE_MIPS32"),
    "mips64": ("CS_ARCH_MIPS", "CS_MODE_MIPS64"),  # PS2 EE (R5900); MMI opcodes show as data
    "n64": ("CS_ARCH_MIPS", "CS_MODE_MIPS64"),  # N64 R4300i, big endian
    "m68k": ("CS_ARCH_M68K", "CS_MODE_M68K_000"),
    "sh2": ("CS_ARCH_SH", "CS_MODE_SH2"),
    "x86": ("CS_ARCH_X86", "CS_MODE_32"),
    "sm83": None,  # Game Boy / Color: rhtk.sm83, no Capstone needed
}
BIG_ENDIAN = {"m68k", "sh2", "n64"}


def disassemble(data: bytes, offset: int, length: int, arch: str, address: int | None = None):
    if arch == "sm83":
        from . import sm83
        yield from sm83.disassemble(data, offset, length, address)
        return
    try:
        import capstone
    except ImportError as e:
        raise SystemExit("disasm needs Capstone: pip install capstone") from e
    a, m = ARCHS[arch]
    mode = getattr(capstone, m)
    if arch in BIG_ENDIAN:
        mode |= capstone.CS_MODE_BIG_ENDIAN
    md = capstone.Cs(getattr(capstone, a), mode)
    md.skipdata = True  # keep going past opcodes Capstone doesn't know
    addr = offset if address is None else address
    for ins in md.disasm(data[offset:offset + length], addr):
        yield ins.address, ins.bytes.hex(" "), ins.mnemonic, ins.op_str


def xrefs(data: bytes, target: int, mapping: dict, sizes=(2, 3, 4), endian: str = "little",
          ptr_or: int = 0):
    """Find stored pointers that resolve to file offset `target`.

    The usual way to find a pointer table: locate one string by search,
    then look for its pointer. Consecutive hits spaced evenly are a table."""
    m = Mapper(mapping)
    value = m.to_ptr(target)
    for size in sizes:
        needle = (value & ((1 << 8 * size) - 1)).to_bytes(size, endian)
        if m.to_file(int.from_bytes(needle, endian) | ptr_or) != target:
            continue
        i = data.find(needle)
        while i != -1:
            yield i, size
            i = data.find(needle, i + 1)
