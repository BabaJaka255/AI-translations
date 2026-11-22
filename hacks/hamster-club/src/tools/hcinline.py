"""rhtk plugin for short strings drawn straight from code.

Most UI text outside the event script is a fixed-length string that a routine
draws with `ld hl, string` ... `ld a, length` ... `call` one of the draw
routines (0x0C90, 0x0C77, or a bank wrapper like 0x643B / 0x6E82). 0xA3 is
padding and draws nothing, so a shorter translation just pads with 0xA3.

A translation longer than its slot moves to free space in the same bank: the
`ld hl` immediates are repointed and the `ld a` length bytes are raised.

Block config:
    {"name": "inline01", "mode": "plugin", "module": "tools/hcinline.py",
     "free": [["0x7DC0", "0x8000"]],          # free ROM ranges, any banks
     "strings": [
        # at, length, max columns on screen, `ld hl` sites, `ld a` sites
        {"at": "0x528A", "len": 16, "max": 18, "hl": ["0x5246"], "a": ["0x524F"]},
        ...]}
The `hl`/`a` sites are the ROM offsets of the 0x21 / 0x3E opcodes. A string
without sites can't move, so it must fit its slot.
"""
from __future__ import annotations

PAD = 0xA3


def _int(v):
    return int(v, 0) if isinstance(v, str) else v


def _cpu(off: int) -> int:
    return 0x4000 + off % 0x4000 if off >= 0x4000 else off


def dump(rom: bytes, block: dict, table) -> dict:
    """rhtk plugin entry point: one entry per configured string."""
    out = []
    for n, s in enumerate(block["strings"]):
        at, ln = _int(s["at"]), s["len"]
        raw = rom[at:at + ln].rstrip(bytes([PAD]))
        text, _ = table.decode(raw, 0, stop_at_end=False)
        out.append({"id": f"{block['name']}_{n:04d}", "offset": f"0x{at:X}", "length": ln,
                    "pointers": [], "jp": text, "en": "", "notes": "",
                    # a string that can't move must also fit its slot
                    "max_chars": s.get("max", ln) if s.get("hl") else min(s.get("max", ln), ln)})
    return {"block": block["name"], "entries": out}


class _Free:
    def __init__(self, ranges):
        self.ranges = [[_int(a), _int(b)] for a, b in ranges]

    def alloc(self, bank: int, n: int) -> int:
        for r in self.ranges:
            if r[0] // 0x4000 == bank and r[1] - r[0] >= n:
                off = r[0]
                r[0] += n
                return off
        raise ValueError(f"no free space left in bank 0x{bank:X} for {n} bytes")


def insert(rom: bytearray, block: dict, script: dict, table, log=print) -> dict:
    """rhtk plugin entry point."""
    free = _Free(block.get("free", []))
    by_at = {_int(s["at"]): s for s in block["strings"]}
    stats = {"block": block["name"], "strings": len(script["entries"]), "translated": 0, "moved": 0}
    for e in script["entries"]:
        en = e.get("en", "")
        if not en:  # a translation may be just spaces, to blank a label
            continue
        stats["translated"] += 1
        at = int(e["offset"], 0)
        cfg = by_at[at]
        ln = cfg["len"]
        data = table.encode(en)
        if len(data) > cfg.get("max", ln):
            raise ValueError(f"{e['id']}: {len(data)} characters, the screen has room for {cfg.get('max', ln)}")
        if len(data) <= ln:
            rom[at:at + ln] = data.ljust(ln, bytes([PAD]))
            continue
        hl, a = [_int(x) for x in cfg.get("hl", [])], [_int(x) for x in cfg.get("a", [])]
        if not hl or not a:
            raise ValueError(f"{e['id']}: {len(data)} bytes in a {ln}-byte slot, and no hl/a sites to move it")
        bank = at // 0x4000
        dest = free.alloc(bank, len(data))
        if any(b not in (0, 0xFF) for b in rom[dest:dest + len(data)]):
            raise ValueError(f"{e['id']}: free space at 0x{dest:X} is not empty")
        rom[dest:dest + len(data)] = data
        for site in hl:
            if rom[site] != 0x21 or rom[site + 1] | rom[site + 2] << 8 != _cpu(at):
                raise ValueError(f"{e['id']}: no `ld hl, ${_cpu(at):04X}` at 0x{site:X}")
            rom[site + 1:site + 3] = bytes([_cpu(dest) & 0xFF, _cpu(dest) >> 8])
        for site in a:
            if rom[site] != 0x3E or rom[site + 1] != ln:
                raise ValueError(f"{e['id']}: no `ld a, ${ln:02X}` at 0x{site:X}")
            rom[site + 1] = len(data)
        rom[at:at + ln] = bytes([PAD]) * ln
        stats["moved"] += 1
    return stats
