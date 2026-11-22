"""Build patches/hacks.ips: small code changes for English text layout.

Each entry is (ROM offset, original bytes, new bytes, why). The original bytes
are checked so a wrong offset fails loudly instead of corrupting code.

Usage (game folder): python3 tools/make_hacks.py
"""
from __future__ import annotations

import os
import sys

TK = os.environ.get("RHTK", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "toolkit"))
sys.path.insert(0, TK)
from rhtk import patch  # noqa: E402

HACKS = [
    # Status window (bank 02, 0x8DE7-0x8E2B): the mood and condition values are
    # drawn one column right (tile buffer +0x10, dakuten row +1), so they start
    # after "Mood:"/"Cond:" instead of under the colon. 5 columns remain.
    (0x8DE7, "01 a3 d5 11 80 d1", "01 a4 d5 11 90 d1", "mood value column 4 -> 5"),
    (0x8E15, "01 e3 d5 11 20 d2", "01 e4 d5 11 30 d2", "condition value column 4 -> 5"),
    # Item grid (bank 0F, 0x3EAF9-0x3EBAF): six lines of two items, each name
    # right-aligned before its count. The Japanese lines start at different
    # columns; all start at column 1 now so the English can be laid out freely.
    (0x3EB0A, "01 a3 d0 11 c4 d0", "01 a0 d0 11 c1 d0", "item grid line 1 -> column 1"),
    (0x3EB52, "01 22 d1 11 43 d1", "01 20 d1 11 41 d1", "item grid line 3 -> column 1"),
    (0x3EB60, "01 61 d1 11 82 d1", "01 60 d1 11 81 d1", "item grid line 4 -> column 1"),
    (0x3EB99, "01 a2 d1 11 c3 d1", "01 a0 d1 11 c1 d1", "item grid line 5 -> column 1"),
    (0x3EBA7, "01 e2 d1 11 03 d2", "01 e0 d1 11 01 d2", "item grid line 6 -> column 1"),
    # Treat list (bank 0F, 0x3EBE7-0x3EC9E): beans on the left start at column 1
    # and end at column 8, their counts move from column 9 to 10; the two
    # items on the right start at column 12 and end at column 18.
    (0x3EBEA, "01 a2 d0 11 c3 d0", "01 a0 d0 11 c1 d0", "treat line 1 -> column 1"),
    (0x3EBF8, "01 e1 d0 11 02 d1", "01 e0 d0 11 01 d1", "treat line 2 -> column 1"),
    (0x3EC14, "01 61 d1 11 82 d1", "01 60 d1 11 81 d1", "treat line 4 -> column 1"),
    (0x3EC22, "01 a1 d1 11 c2 d1", "01 a0 d1 11 c1 d1", "treat line 5 -> column 1"),
    (0x3EC30, "01 e1 d1 11 02 d2", "01 e0 d1 11 01 d2", "treat line 6 -> column 1"),
    (0x3EC3E, "01 4c d1 11 6d d1", "01 4b d1 11 6c d1", "treat line 7 -> column 12"),
    (0x3EC4C, "01 cf d1 11 f0 d1", "01 cb d1 11 ec d1", "treat line 8 -> column 12"),
    (0x3EC5C, "21 c9 d0", "21 ca d0", "treat count 1 -> column 10"),
    (0x3EC65, "21 09 d1", "21 0a d1", "treat count 2 -> column 10"),
    (0x3EC6E, "21 49 d1", "21 4a d1", "treat count 3 -> column 10"),
    (0x3EC77, "21 89 d1", "21 8a d1", "treat count 4 -> column 10"),
    (0x3EC80, "21 c9 d1", "21 ca d1", "treat count 5 -> column 10"),
    (0x3EC89, "21 09 d2", "21 0a d2", "treat count 6 -> column 10"),
    # home screen window, age line (see make_homemenu.py)
    (0xA1EC, "21 66 9c", "21 65 9c", "age digits columns 6-7 -> 5-6"),
    # schedule header "<M>がつ <W>しゅうめ" (month M, week W) -> "<M>mo <W>wk"
    (0x3C7C7, "3e 06 22 3e 12 22", "3e 0d 22 3e 0f 22", "schedule: がつ -> mo"),
    (0x3C7D4, "3e 0c 22 3e 35 22 3e 03 22 3e 22 22", "3e 17 22 3e 0b 22 3e 00 22 3e 00 22",
     "schedule: しゅうめ -> wk"),
    (0x3C7EA, "3e 7e 77", "3e 00 77", "schedule: no dakuten over がつ"),
    # cage status window, food line: "<food>／のこり<amount>" -> "<food>: <amount>"
    (0x3E8E4, "3e 9b 12", "3e 9f 12", "cage status: separator after the food name / -> :"),
    # food screen: "のこり：<amount>" -> "Left <amount>": the amount starts one tile later
    (0x3CF1F, "11 10 d1 01 44 d2", "11 20 d1 01 45 d2", "food screen: amount one tile right"),
    # Weekly report event labels (Birth/Death/Accident/Sick/Escape, code at bank 00
    # 0x3D21): the two 16x16 halves slide in from both sides by a shared x-delta
    # table at 0x3D73 (left adds, right subtracts) and stopped 32px apart. The
    # English labels are one word across both halves, so the first 8 steps move
    # 6px instead of 4: the halves end 16px further in each, side by side at
    # screen x 64 and 80.
    (0x3D73, "04 04 04 04 04 04 04 04", "06 06 06 06 06 06 06 06", "event labels: halves meet in the middle"),
]


def main():
    rom = open("rom/original.gbc", "rb").read()
    out = bytearray(rom)
    for off, old, new, why in HACKS:
        old, new = bytes.fromhex(old), bytes.fromhex(new)
        if rom[off:off + len(old)] != old:
            sys.exit(f"0x{off:X} ({why}): expected {old.hex(' ')}, found {rom[off:off + len(old)].hex(' ')}")
        out[off:off + len(new)] = new
    os.makedirs("patches", exist_ok=True)
    with open("patches/hacks.ips", "wb") as f:
        f.write(patch.ips_create(rom, bytes(out)))
    print(f"wrote patches/hacks.ips ({len(HACKS)} hacks)")


if __name__ == "__main__":
    main()
