"""Hamster Club (GBC) event-script parser.

The interpreter lives in bank 0 at 0x32A3. Scene table: 51 entries of
(bank, addr16) at ROM 0xE650. Each scene starts with one setup byte, then
bytecode. Bytes < 0xE8 are glyphs (0x00 is a space,
0x7E/0x7D dakuten go on the row above,
0xA3 returns from an F2 string). Bytes 0xE8-0xF9 are commands; see notes/rom.md.

Usage: python3 tools/hcscript.py rom/original.gbc  -> prints a summary
"""
from __future__ import annotations

import sys

SCENE_TABLE, SCENE_COUNT = 0xE650, 51

# fixed parameter byte counts; None = special-cased below
PARAMS = {0xE8: 0, 0xE9: 1, 0xEA: 1, 0xEB: None, 0xEC: 2, 0xED: None, 0xEE: 0, 0xEF: 0,
          0xF0: 0, 0xF1: 1, 0xF2: 1, 0xF3: 2, 0xF4: 2, 0xF5: 2, 0xF6: 1, 0xF7: None,
          0xF8: 1, 0xF9: None}
EB_EXTRA = {7: 1, 13: 1, 17: 2}
F7_EXTRA = {0: 2, 1: 2, 2: 0, 3: 0, 4: 0, 5: 0, 6: 2, 7: 1, 8: 0, 9: 2, 10: 0}
TEXT_CMDS = {0xEE, 0xEF, 0xF0}  # clear box, new line, wait for button: part of a message
NAME_CMD = 0xF2                 # insert a name (string ends with 0xA3): part of a message
ENDS = {0xE8, 0xEC, 0xED, 0xF9}  # no fall-through


def file_off(bank: int, addr: int) -> int:
    return bank * 0x4000 + (addr - 0x4000 if bank else addr)


def scenes(rom: bytes):
    for i in range(SCENE_COUNT):
        o = SCENE_TABLE + 3 * i
        yield i, rom[o], rom[o + 1] | rom[o + 2] << 8


class Op:
    __slots__ = ("off", "size", "cmd", "targets")

    def __init__(self, off, size, cmd, targets=()):
        self.off, self.size, self.cmd, self.targets = off, size, cmd, list(targets)


def decode_op(rom: bytes, off: int, bank: int) -> Op:
    b = rom[off]
    if b < 0xE8:
        return Op(off, 1, None)
    if b not in PARAMS:
        raise ValueError(f"unknown command {b:02X} at 0x{off:X}")
    n = PARAMS[b]
    w = lambda o: file_off(bank, rom[o] | rom[o + 1] << 8)
    if b == 0xEB:
        return Op(off, 2 + EB_EXTRA.get(rom[off + 1], 0), b)
    if b == 0xF7:
        sub = rom[off + 1]
        if sub not in F7_EXTRA:
            raise ValueError(f"unknown F7 subcommand {sub:02X} at 0x{off:X}")
        p = off + 2 + F7_EXTRA[sub]
        return Op(off, p + 2 - off, b, [w(p)])
    if b == 0xED:
        cnt = rom[off + 1]
        # n options: n targets plus a B-button target (0000 = no cancel).
        # 5 and 6 are the cage pickers: one "picked" target and one cancel target.
        k = cnt + 1 if cnt < 5 else 2
        # k words of option targets; unused slots (the last one, at least) are 0000
        raw = [rom[off + 2 + 2 * i] | rom[off + 3 + 2 * i] << 8 for i in range(k)]
        return Op(off, 2 + 2 * k, b, [file_off(bank, a) for a in raw if a])
    if b == 0xF9:  # switch on a hamster stat band: 4 targets
        return Op(off, 10, b, [w(off + 2 + 2 * i) for i in range(4)])
    if b == 0xEC:
        return Op(off, 3, b, [w(off + 1)])
    return Op(off, 1 + n, b)


def walk(rom: bytes, extra=()):
    """Recursive-descent over all scenes. Returns {offset: Op}, scene entries
    [(index, bank, file offset)] and {offset: scene index} (first scene to reach it).
    `extra` adds scenes the table doesn't list, as (bank, file offset)."""
    ops: dict[int, Op] = {}
    owner: dict[int, int] = {}
    entries = [(i, bank, file_off(bank, addr)) for i, bank, addr in scenes(rom)]
    entries += [(SCENE_COUNT + k, b, o) for k, (b, o) in enumerate(extra)]
    for i, bank, start in entries:
        todo = [(bank, start + 1)]  # skip the setup byte
        while todo:
            bk, off = todo.pop()
            while off not in ops:
                op = decode_op(rom, off, bk)
                ops[off] = op
                owner[off] = i
                for t in op.targets:
                    todo.append((bk, t))
                if op.cmd in ENDS:
                    break
                off += op.size
    return ops, entries, owner


def messages(rom: bytes, ops: dict[int, Op]):
    """Group glyphs + EE/EF/F0/F2 into messages. Yields (start, end) file offsets.
    A jump target always starts a new message, so every message has one entry point."""
    offs = sorted(ops)
    targets = {t for op in ops.values() for t in op.targets}
    start = None
    prev_end = None
    for o in offs:
        op = ops[o]
        is_text = op.cmd is None or op.cmd in TEXT_CMDS or op.cmd == NAME_CMD
        if start is not None and (not is_text or o != prev_end or o in targets):
            yield start, prev_end
            start = None
        if is_text and start is None:
            start = o
        prev_end = o + op.size
    if start is not None:
        yield start, prev_end


def _extra(block):
    return [(int(b, 0), int(o, 0)) for b, o in block.get("extra_scenes", [])]


def dump(rom: bytes, block: dict, table) -> dict:
    """rhtk plugin entry point: one entry per message."""
    ops, entries, owner = walk(rom, _extra(block))
    setup = {i: rom[o] for i, _, o in entries}
    # the portrait shown is the scene's setup byte until an F6 changes it
    portrait_at, face, entries_out = {}, {}, []
    for o in sorted(ops):
        op = ops[o]
        if op.cmd == 0xF6:
            face[owner[o]] = rom[o + 1]
        portrait_at[o] = face.get(owner[o], setup[owner[o]])
    for n, (s, e) in enumerate(messages(rom, ops)):
        text, _ = table.decode(rom[:e], s, stop_at_end=False)
        sc = owner[s]
        entries_out.append({"id": f"{block['name']}_{n:04d}", "offset": f"0x{s:X}", "length": e - s,
                            "pointers": [], "jp": text, "en": "",
                            "notes": "", "scene": sc, "face": f"{portrait_at[s]:02X}"})
    return {"block": block["name"], "entries": entries_out}


if __name__ == "__main__":
    rom = open(sys.argv[1], "rb").read()
    ops, entries, _ = walk(rom)
    msgs = list(messages(rom, ops))
    print(f"{len(ops)} ops, {len(msgs)} messages, {sum(e - s for s, e in msgs)} text bytes")


# ------------------------------------------------------------------ insertion
#
# Translations that fit go back in place. Longer ones move to free banks: the
# message start becomes `FA bank lo hi` (far goto, added by the hook below) and
# the moved text ends with `FA` back to where the original message ended.
# Leftover bytes of a message that shrank are skipped with FA or filled with
# FB (no-op), so the interpreter never runs stale Japanese.

FAR, NOP = 0xFA, 0xFB
HOOK_SITE = 0x32BC  # `cp $E8 / jr c, $32E9` in the interpreter loop
# EF (<br>) moves the cursor to line 2 if it's before column 18, else past the
# box. Text auto-wraps at 18, so a full 18-character line followed by <br>
# skipped a line and drew over other tiles. `cp $12` -> `cp $13` makes <br>
# after a full first line a no-op.
BR_FIX = (0x3446, 0x12, 0x13)
# F2 02 (the honorific) copies 3 bytes from one of three strings at 0x38D4
# into the D8AF buffer. The immediates below are moved to a table of 6-byte
# strings so the English suffixes fit: (hl immediate, original target).
HONORIFIC_PTRS = ((0x38A5, 0x38D4), (0x38AC, 0x38D7), (0x38B1, 0x38DA))
HONORIFIC_LEN = 0x38B7  # `ld bc, $0003`


def hook_code(at: int) -> bytes:
    """SM83 for the FA/FB commands, placed at CPU address `at` in bank 0.
    Entered from HOOK_SITE with a = command byte, hl = its address."""
    dispatch = bytes([0xFE, FAR, 0x28, 0x0C,         # cp FA / jr z, far   (+12)
                      0xFE, NOP, 0x28, 0x17,         # cp FB / jr z, nop   (+23)
                      0xFE, 0xE8, 0xDA, 0xE9, 0x32,  # cp E8 / jp c, $32E9 (a glyph)
                      0xC3, 0xC0, 0x32])             # jp $32C0 (the game's command table)
    far = bytes([0x23,                               # inc hl
                 0x2A, 0xEA, 0xAC, 0xD8,             # ld a,[hl+] / ld [$D8AC],a   bank
                 0x2A, 0xEA, 0xA8, 0xD8,             # ld a,[hl+] / ld [$D8A8],a   pointer lo
                 0x7E, 0xEA, 0xA9, 0xD8,             # ld a,[hl]  / ld [$D8A9],a   pointer hi
                 0x18, 0x09])                        # jr next     (+9)
    nop = bytes([0x23,                               # inc hl
                 0x7D, 0xEA, 0xA8, 0xD8,             # ld a,l / ld [$D8A8],a
                 0x7C, 0xEA, 0xA9, 0xD8])            # ld a,h / ld [$D8A9],a
    nxt = bytes([0xC3, 0xA3, 0x32])                  # jp $32A3 (interpreter: next byte)
    return dispatch + far + nop + nxt


def _cpu(off: int) -> int:
    return 0x4000 + off % 0x4000 if off >= 0x4000 else off


class _Banks:
    """Sequential allocator over whole free banks."""

    def __init__(self, banks):
        self.banks = list(banks)
        self.cur = self.banks.pop(0)
        self.pos = 0

    def alloc(self, n: int) -> int:
        if n > 0x4000:
            raise ValueError("message longer than a bank")
        if self.pos + n > 0x4000:
            if not self.banks:
                raise ValueError("out of text banks: add more to text_banks")
            self.cur, self.pos = self.banks.pop(0), 0
        off = self.cur * 0x4000 + self.pos
        self.pos += n
        return off


def _far(off: int) -> bytes:
    a = _cpu(off)
    return bytes([FAR, off // 0x4000, a & 0xFF, a >> 8])


def _fill(rom: bytearray, start: int, end: int) -> None:
    """Make [start, end) skip itself: a far goto when it fits, else no-ops."""
    if end - start >= 4:
        rom[start:start + 4] = _far(end)
        start += 4
        rom[start:end] = bytes([NOP]) * (end - start)  # never run, but tidy
    else:
        rom[start:end] = bytes([NOP]) * (end - start)


def _honorifics(rom: bytearray, block: dict, table) -> None:
    """block["honorifics"]: English for さん, ちゃん, クン (the C303 = 1, 2, 3 order),
    written at block["honorifics_at"] in bank 0 as 6-byte, A3-terminated strings."""
    at = int(block.get("honorifics_at", "0x3FD0"), 0)
    if rom[HONORIFIC_LEN] != 3:
        raise ValueError("honorific copy length already patched")
    for i, ((imm, old), text) in enumerate(zip(HONORIFIC_PTRS, block["honorifics"])):
        if rom[imm] | rom[imm + 1] << 8 != old:
            raise ValueError(f"unexpected honorific pointer at 0x{imm:X}")
        data = table.encode(text) + b"\xA3"
        if len(data) > 6:
            raise ValueError(f"honorific {text!r} is longer than 5 characters")
        dest = at + 6 * i
        if any(rom[dest:dest + 6]):
            raise ValueError(f"honorific space at 0x{dest:X} is not empty")
        rom[dest:dest + 6] = data.ljust(6, b"\xA3")
        rom[imm:imm + 2] = bytes([dest & 0xFF, dest >> 8])
    rom[HONORIFIC_LEN] = 6


def insert(rom: bytearray, block: dict, script: dict, table, log=print) -> dict:
    """rhtk plugin entry point."""
    ops, _, _ = walk(bytes(rom), _extra(block))
    targets = {t for op in ops.values() for t in op.targets}
    hook_at = int(block.get("hook_at", "0x3FA0"), 0)
    code = hook_code(hook_at)
    if any(rom[hook_at:hook_at + len(code)]):
        raise ValueError(f"hook space at 0x{hook_at:X} is not empty")
    rom[hook_at:hook_at + len(code)] = code
    rom[HOOK_SITE:HOOK_SITE + 4] = bytes([0xC3, hook_at & 0xFF, hook_at >> 8, NOP])  # jp hook
    at, old, new = BR_FIX
    if rom[at] != old:
        raise ValueError(f"unexpected byte at 0x{at:X}: not the original ROM?")
    rom[at] = new
    if "honorifics" in block:
        _honorifics(rom, block, table)
    banks = _Banks(int(b, 0) if isinstance(b, str) else b for b in block["text_banks"])
    entries = script["entries"]
    stats = {"block": block["name"], "strings": len(entries), "translated": 0, "moved": 0}
    for e in entries:
        if not e.get("en", "").strip():
            continue
        stats["translated"] += 1
        data = table.encode(e["en"])
        s = int(e["offset"], 0)
        end = s + e["length"]
        if len(data) <= end - s:
            rom[s:s + len(data)] = data
            _fill(rom, s + len(data), end)
            continue
        # need 4 bytes for the far goto: take following simple commands along
        tail = end
        while tail - s < 4:
            op = ops.get(tail)
            if op is None or tail in targets or op.cmd in ENDS or op.targets:
                raise ValueError(f"{e['id']}: message is {end - s} bytes and can't grow to fit a far jump")
            tail += op.size
        chunk = data + bytes(rom[end:tail])
        dest = banks.alloc(len(chunk) + 4)
        rom[dest:dest + len(chunk)] = chunk
        rom[dest + len(chunk):dest + len(chunk) + 4] = _far(tail)
        rom[s:s + 4] = _far(dest)
        rom[s + 4:tail] = bytes([NOP]) * (tail - s - 4)
        stats["moved"] += 1
    stats["free_left"] = 0x4000 - banks.pos + 0x4000 * len(banks.banks)
    return stats
