"""Table-driven disassembler for the Game Boy / Game Boy Color CPU (SM83).

Capstone has no SM83 backend, so `rhtk disasm --arch sm83` uses this instead.
Operands: d8/d16 immediates, a16 absolute addresses, r8 relative jumps
(shown as the absolute target), a8 for LDH ($FF00+n).
"""
from __future__ import annotations

_R = ["b", "c", "d", "e", "h", "l", "[hl]", "a"]
_RP = ["bc", "de", "hl", "sp"]
_RP2 = ["bc", "de", "hl", "af"]
_CC = ["nz", "z", "nc", "c"]
_ALU = ["add a,", "adc a,", "sub", "sbc a,", "and", "xor", "or", "cp"]
_ROT = ["rlc", "rrc", "rl", "rr", "sla", "sra", "swap", "srl"]


def _build() -> dict[int, tuple[str, str]]:
    """opcode -> (mnemonic, operand template). Templates use d8, d16, a16, a8, r8, e8."""
    t: dict[int, tuple[str, str]] = {}
    for op in range(0x40, 0x80):
        if op != 0x76:
            t[op] = ("ld", f"{_R[(op >> 3) & 7]}, {_R[op & 7]}")
    t[0x76] = ("halt", "")
    for op in range(0x80, 0xC0):
        m = _ALU[(op >> 3) & 7]
        t[op] = (m.split()[0], (m.split()[1] + " " if " " in m else "") + _R[op & 7])
    for i in range(8):
        t[0x06 + 8 * i] = ("ld", f"{_R[i]}, d8")
        t[0x04 + 8 * i] = ("inc", _R[i])
        t[0x05 + 8 * i] = ("dec", _R[i])
        m = _ALU[i]
        t[0xC6 + 8 * i] = (m.split()[0], (m.split()[1] + " " if " " in m else "") + "d8")
        t[0xC7 + 8 * i] = ("rst", f"${8 * i:02X}")
    for i in range(4):
        t[0x01 + 16 * i] = ("ld", f"{_RP[i]}, d16")
        t[0x03 + 16 * i] = ("inc", _RP[i])
        t[0x0B + 16 * i] = ("dec", _RP[i])
        t[0x09 + 16 * i] = ("add", f"hl, {_RP[i]}")
        t[0xC1 + 16 * i] = ("pop", _RP2[i])
        t[0xC5 + 16 * i] = ("push", _RP2[i])
        t[0x20 + 8 * i] = ("jr", f"{_CC[i]}, r8")
        t[0xC0 + 8 * i] = ("ret", _CC[i])
        t[0xC2 + 8 * i] = ("jp", f"{_CC[i]}, a16")
        t[0xC4 + 8 * i] = ("call", f"{_CC[i]}, a16")
    t.update({
        0x00: ("nop", ""), 0x02: ("ld", "[bc], a"), 0x12: ("ld", "[de], a"),
        0x22: ("ld", "[hl+], a"), 0x32: ("ld", "[hl-], a"), 0x0A: ("ld", "a, [bc]"),
        0x1A: ("ld", "a, [de]"), 0x2A: ("ld", "a, [hl+]"), 0x3A: ("ld", "a, [hl-]"),
        0x07: ("rlca", ""), 0x0F: ("rrca", ""), 0x17: ("rla", ""), 0x1F: ("rra", ""),
        0x27: ("daa", ""), 0x2F: ("cpl", ""), 0x37: ("scf", ""), 0x3F: ("ccf", ""),
        0x08: ("ld", "[a16], sp"), 0x10: ("stop", ""), 0x18: ("jr", "r8"),
        0xC3: ("jp", "a16"), 0xCD: ("call", "a16"), 0xC9: ("ret", ""), 0xD9: ("reti", ""),
        0xE9: ("jp", "hl"), 0xF9: ("ld", "sp, hl"), 0xE8: ("add", "sp, e8"),
        0xF8: ("ld", "hl, sp+e8"), 0xE0: ("ldh", "[a8], a"), 0xF0: ("ldh", "a, [a8]"),
        0xE2: ("ld", "[$FF00+c], a"), 0xF2: ("ld", "a, [$FF00+c]"),
        0xEA: ("ld", "[a16], a"), 0xFA: ("ld", "a, [a16]"), 0xF3: ("di", ""), 0xFB: ("ei", ""),
    })
    return t


OPS = _build()
_SIZE = {"d8": 1, "a8": 1, "r8": 1, "e8": 1, "d16": 2, "a16": 2}


def disassemble(data: bytes, offset: int, length: int, address: int | None = None):
    """Yield (address, hex bytes, mnemonic, operands), like disasm.disassemble."""
    addr = offset if address is None else address
    i, end = offset, min(len(data), offset + length)
    while i < end:
        op = data[i]
        if op == 0xCB and i + 1 < len(data):
            cb = data[i + 1]
            reg = _R[cb & 7]
            group = cb >> 6
            if group == 0:
                mn, ops = _ROT[(cb >> 3) & 7], reg
            else:
                mn, ops = ("bit", "res", "set")[group - 1], f"{(cb >> 3) & 7}, {reg}"
            yield addr, data[i:i + 2].hex(" "), mn, ops
            i, addr = i + 2, addr + 2
            continue
        if op not in OPS:
            yield addr, f"{op:02x}", "db", f"${op:02X}"
            i, addr = i + 1, addr + 1
            continue
        mn, tmpl = OPS[op]
        kind = next((k for k in _SIZE if k in tmpl), None)
        n = 1 + (_SIZE[kind] if kind else 0)
        raw = data[i:i + n]
        if len(raw) < n:
            yield addr, raw.hex(" "), "db", ", ".join(f"${b:02X}" for b in raw)
            return
        ops = tmpl
        if kind in ("d16", "a16"):
            ops = tmpl.replace(kind, f"${raw[1] | raw[2] << 8:04X}")
        elif kind == "d8":
            ops = tmpl.replace(kind, f"${raw[1]:02X}")
        elif kind == "a8":
            ops = tmpl.replace(kind, f"$FF{raw[1]:02X}")
        elif kind == "r8":
            rel = raw[1] - 256 if raw[1] > 127 else raw[1]
            ops = tmpl.replace(kind, f"${(addr + 2 + rel) & 0xFFFF:04X}")
        elif kind == "e8":
            rel = raw[1] - 256 if raw[1] > 127 else raw[1]
            ops = tmpl.replace(kind, f"{rel:+d}")
        yield addr, raw.hex(" "), mn, ops
        i, addr = i + n, addr + n
