"""Script dumping and reinsertion driven by a block definition.

Block definition (one entry of "blocks" in project.json):
{
  "name": "dialogue",
  "mode": "pointers",              # or "range"
  "table": "tables/main.tbl",       # optional, else the project's table
  "ptr_table": "0x10000",           # pointers mode: file offset of the table
  "count": 256,                     # number of pointers
  "ptr_size": 2, "ptr_stride": 2,   # bytes per pointer, bytes between pointers
  "endian": "little",
  "ptr_or": "0x8C0000",             # bits implied by the code (e.g. SNES bank), optional
  "mapping": {"type": "snes-lorom"},
  "range": ["0x20000", "0x24000"],  # range mode: strings back to back, no pointers
  "free_space": [["0x1F8000", "0x1FFFFF"]],  # extra room for longer text
  "reuse_original": true,           # recycle the space the old strings used
  "fill": "0xFF",                   # byte written over freed space
  "length_prefix": 1,               # pointers mode: strings start with a 1-byte length
                                    # instead of ending with an end code
  "box": {"max_chars": 18, "max_lines": 3}   # used by QA. Optional keys:
      # line_tokens / page_tokens / free_tokens: which codes break lines, pages, or neither
      # token_widths: {"<name 00>": 8} on-screen width of variable tokens
      # spaces_ok: true for column-aligned menus (no double-space warning)
}

"mode": "fixed" is for fixed-width fields (menus, item and name tables) that the
code reads with a hard-coded length:
  "fields": [["0x92C8", 10, 6], ["0x9387", 8]]   # [offset, width, count=1]
  "pad": "0xA3"                                 # byte that fills unused width
Each field is one entry; "count" repeats fields of the same width back to back.
Translations must fit the width; QA checks it (the entry's "length").

"mode": "plugin" hands the block to a game-specific module, for scripts that are
bytecode rather than plain pointer tables:
  {"name": "events", "mode": "plugin", "module": "tools/events.py", ...}
The module (path relative to the game folder) defines
  dump(rom, block, table) -> script dict
  insert(rom, block, script, table, log) -> stats dict (keys as insert_block returns)
and may read any other keys it wants from the block.

Script files are JSON so they are easy for both people and agents to edit:
{"block": "...", "entries": [{"id", "offset", "length", "pointers", "jp", "en", "notes"}]}
Only "en" (and "notes") should be edited by translators.
"""
from __future__ import annotations

import importlib.util
import json
import os

from .address import Mapper, read_ptr, write_ptr
from .table import Table


def _int(v) -> int:
    return int(v, 0) if isinstance(v, str) else int(v)


def _ptr_offsets(block: dict) -> list[int]:
    base = _int(block["ptr_table"])
    stride = _int(block.get("ptr_stride", block.get("ptr_size", 2)))
    return [base + i * stride for i in range(_int(block["count"]))]


def load_plugin(block: dict, root: str = "."):
    path = os.path.join(root, block["module"])
    spec = importlib.util.spec_from_file_location(f"rhtk_plugin_{block['name']}", path)
    if spec is None:
        raise ValueError(f"{block['name']}: cannot load plugin module {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def dump_block(rom: bytes, block: dict, table: Table, root: str = ".") -> dict:
    entries: list[dict] = []
    name = block["name"]
    if block.get("mode") == "plugin":
        return load_plugin(block, root).dump(rom, block, table)
    if block.get("mode") == "fixed":
        pad = _int(block.get("pad", 0x00))
        for f in block["fields"]:
            off, width, count = _int(f[0]), _int(f[1]), _int(f[2]) if len(f) > 2 else 1
            for k in range(count):
                o = off + k * width
                raw = bytes(rom[o:o + width])
                text, _ = table.decode(raw.rstrip(bytes([pad])), stop_at_end=False)
                entries.append({"id": f"{name}_{len(entries):04d}", "offset": f"0x{o:X}",
                                "length": width, "pointers": [], "jp": text, "en": "", "notes": ""})
        return {"block": name, "entries": entries}
    if block.get("mode", "pointers") == "range":
        start, end = (_int(x) for x in block["range"])
        off = start
        while off < end:
            text, n = table.decode(rom, off, limit=end - off)
            entries.append({"id": f"{name}_{len(entries):04d}", "offset": f"0x{off:X}",
                            "length": n, "pointers": [], "jp": text, "en": "", "notes": ""})
            off += n
    else:
        mapper = Mapper(block.get("mapping", {}))
        size = _int(block.get("ptr_size", 2))
        endian = block.get("endian", "little")
        ptr_or = _int(block.get("ptr_or", 0))
        by_off: dict[int, dict] = {}
        for p in _ptr_offsets(block):
            target = mapper.to_file(read_ptr(rom, p, size, endian) | ptr_or)
            if target in by_off:  # several pointers can share one string
                by_off[target]["pointers"].append(f"0x{p:X}")
                continue
            if not 0 <= target < len(rom):
                raise ValueError(f"{name}: pointer at 0x{p:X} points outside the ROM (0x{target:X}); "
                                 f"check ptr_size/mapping/ptr_or")
            if block.get("length_prefix"):
                n = 1 + rom[target]
                text, _ = table.decode(bytes(rom[target + 1:target + n]), stop_at_end=False)
            else:
                text, n = table.decode(rom, target)
            e = {"id": f"{name}_{len(by_off):04d}", "offset": f"0x{target:X}", "length": n,
                 "pointers": [f"0x{p:X}"], "jp": text, "en": "", "notes": ""}
            by_off[target] = e
            entries.append(e)
    return {"block": name, "entries": entries}


class FreeSpace:
    """First-fit allocator over [start, end) ranges."""

    def __init__(self):
        self.ranges: list[list[int]] = []

    def add(self, start: int, end: int) -> None:
        self.ranges.append([start, end])
        self.ranges.sort()
        merged: list[list[int]] = []
        for r in self.ranges:
            if merged and r[0] <= merged[-1][1]:
                merged[-1][1] = max(merged[-1][1], r[1])
            else:
                merged.append(r)
        self.ranges = merged

    def alloc(self, size: int, ok=lambda off, size: True) -> int | None:
        for r in self.ranges:
            if r[1] - r[0] >= size and ok(r[0], size):
                off = r[0]
                r[0] += size
                return off
        return None

    def total(self) -> int:
        return sum(e - s for s, e in self.ranges)


def insert_block(rom: bytearray, block: dict, script: dict, table: Table,
                 log=print, root: str = ".") -> dict:
    """Write translated entries back into rom (in place). Returns stats."""
    if block.get("mode") == "plugin":
        return load_plugin(block, root).insert(rom, block, script, table, log)
    name = block["name"]
    fill = _int(block.get("fill", 0xFF))
    entries = script["entries"]
    stats = {"block": name, "strings": len(entries), "translated": 0, "moved": 0}

    # untranslated strings keep their original bytes: the insert table usually
    # cannot encode Japanese once the font has been replaced
    original = {e["id"]: bytes(rom[_int(e["offset"]):_int(e["offset"]) + e["length"]])
                for e in entries}

    def encode(e):
        if e.get("en", "").strip():
            stats["translated"] += 1
            data = table.encode(e["en"])
            if block.get("length_prefix"):
                if len(data) > 0xFF:
                    raise ValueError(f"{e['id']}: {len(data)} bytes, a length prefix holds 255")
                data = bytes([len(data)]) + data
            return data
        return original[e["id"]]

    if block.get("mode") == "fixed":
        fill = _int(block.get("pad", 0x00))
    if block.get("mode", "pointers") in ("range", "fixed"):
        for e in entries:
            data = encode(e)
            off, length = _int(e["offset"]), e["length"]
            if len(data) > length:
                raise ValueError(f"{e['id']}: {len(data)} bytes but only {length} available "
                                 f"({block.get('mode')} blocks have no pointers; shorten it or repoint in ASM)")
            rom[off:off + length] = data + bytes([fill]) * (length - len(data))
        return stats

    mapper = Mapper(block.get("mapping", {}))
    size = _int(block.get("ptr_size", 2))
    endian = block.get("endian", "little")
    ptr_or = _int(block.get("ptr_or", 0))
    mask = (1 << (8 * size)) - 1

    def reachable(off: int, n: int) -> bool:
        # the pointer must round-trip, and the string must not cross a bank edge
        try:
            first, last = mapper.to_ptr(off), mapper.to_ptr(off + max(n, 1) - 1)
        except ValueError:
            return False
        return mapper.to_file((first & mask) | ptr_or) == off and last - first == max(n, 1) - 1

    free = FreeSpace()
    if block.get("reuse_original", True):
        for e in entries:
            off = _int(e["offset"])
            free.add(off, off + e["length"])
    for s, t in block.get("free_space", []):
        free.add(_int(s), _int(t) + 1)  # free_space ranges are inclusive
    for s, t in free.ranges:
        rom[s:t] = bytes([fill]) * (t - s)

    encoded = [(e, encode(e)) for e in entries]
    # place biggest strings first: fewer allocation failures
    for e, data in sorted(encoded, key=lambda x: -len(x[1])):
        off = free.alloc(len(data), reachable)
        if off is None:
            raise ValueError(f"{name}: no reachable free space for {e['id']} ({len(data)} bytes, "
                             f"{free.total()} bytes free in total). Add free_space ranges.")
        rom[off:off + len(data)] = data
        if off != _int(e["offset"]):
            stats["moved"] += 1
        stored = mapper.to_ptr(off) & mask
        for p in e["pointers"]:
            write_ptr(rom, _int(p), stored, size, endian)
    stats["free_left"] = free.total()
    return stats


def load_script(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save_script(path: str, script: dict) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(script, f, ensure_ascii=False, indent=1)
        f.write("\n")
