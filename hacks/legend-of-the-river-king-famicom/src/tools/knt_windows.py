"""English menu windows for Kawa no Nushi Tsuri (FC).

Window templates are tile maps copied to RAM $0100 and drawn by the game.
Borders: 60 72.. 62 / 70 .. 71 / 61 73.. 63.  Text uses the English font
(one row per line; the Japanese dakuten rows are left blank or reused).

In a template string: ' ' = blank (FE), '=' = top border (72), '_' = 73,
'Y' prefix is not used; '¥' = 75 (the game's own yen tile).
"""
import knt_font
from knt_common import HEADER

BANK = 0x2000

def off(bank, addr):
    """File offset in the expanded ROM. Banks 0-13 are unchanged; the
    original fixed banks 14/15 now live in 30/31."""
    if bank == 15:
        return HEADER + 31 * BANK + (addr - 0xE000)
    if bank == 14:
        return HEADER + 30 * BANK + (addr - 0xC000)
    return HEADER + bank * BANK + (addr - 0xA000)


CODES = dict(knt_font.CODES)
CODES.update({str(i): i for i in range(10)})
CODES.update({" ": 0xFE, "=": 0x72, "_": 0x73, "¥": 0x75})


def enc(s):
    try:
        return bytes(CODES[c] for c in s)
    except KeyError as e:
        raise KeyError(f"no tile for {e} in {s!r}")


def window(w, h, title, rows):
    """title: string of w-2 chars ('=' border). rows: dict row->text (1-based
    interior rows), text placed from interior col 1 and padded."""
    iw = w - 2
    assert len(title) <= iw, title
    title = title.ljust(iw, "=")
    out = bytearray([0x60]) + enc(title) + bytes([0x62])
    for r in range(1, h - 1):
        t = rows.get(r, "")
        assert len(t) <= iw, (t, len(t), iw)
        out += bytes([0x70]) + enc(t.ljust(iw)) + bytes([0x71])
    out += bytes([0x61]) + bytes([0x73]) * iw + bytes([0x63])
    assert len(out) == w * h
    return bytes(out)


def center(s, n=10, fill="="):
    left = (n - len(s)) // 2
    return (fill * left + s).ljust(n, fill)


def right(s, n=10):
    return s.rjust(n)


# ---- names -----------------------------------------------------------------
BAIT = ["Caddis", "Paste", "Midge", "Maggot", "Worms"]          # カワムシ ねりえ アカムシ サシ ミミズ
FOOD = ["Bread", "Meat Bun", "Udon", "Sw.Potato", "Rice Ball"]  # パン にくまん うどん やきいも おにぎり
ITEMS = ["Glasses", "Key", "Map", "Compass", "Washtub", "Fireworks", "Hammer", "Apple"]
RODS = ["Bamboo Rod", "Glass Rod", "Carbon Rod", "King Rod"]
FLOATS = ["Ball", "Stick", "Chili"]                              # たまうき ぼううき とうがらしうき
AREAS = ["Stream", "Upstream", "Midstream", "Plains", "Coast"]   # 渓流 上流 中流 下流 河口
SHOPS = [  # area 1-5: (name, price)
    [("Hooks", 10), ("Chum", 20), ("Creel 10", 200), ("Key", 400), ("Bread", 20)],
    [("Hooks", 10), ("Chum", 20), ("Creel 20", 250), ("Compass", 500), ("Meat Bun", 40)],
    [("Hooks", 10), ("Chum", 20), ("Creel 30", 300), ("Fireworks", 350), ("Udon", 50)],
    [("Hooks", 10), ("Chum", 20), ("Creel 60", 600), ("Hammer", 700), ("Sw.Potato", 70)],
    [("Hooks", 10), ("Chum", 20), ("King Hook", 50), ("King Rod", 990), ("Rice Ball", 100)],
]


def templates():
    T = {}
    # status (bank 9): area name is written over the top border by AREATITLE
    T[(9, 0xBEC3, 12, 8)] = window(12, 8, "", {2: "HP", 4: "Yen", 6: "EXP"})
    # bait
    T[(13, 0xAEF9, 12, 12)] = window(12, 12, center("Bait"),
                                     {2 * i + 2: " " + n for i, n in enumerate(BAIT)})
    # gear: rod name in the top border (RODTITLE), float name on row 10 col 2
    T[(13, 0xAF89, 12, 12)] = window(12, 12, "", {2: " Hooks", 4: " Chum", 6: " K.Hook", 8: " K.Bait",
                                                 9: " Float:"})
    # food / items (items blank cols 3-8 of the title)
    T[(13, 0xB019, 12, 12)] = window(12, 12, center("Food"), {})
    # creel: capacity digits are written at title cols 8-9
    T[(13, 0xB0A9, 12, 12)] = window(12, 12, "=Creel ===", {2: " 0-10cm", 4: "11-20cm", 6: "21-30cm",
                                                           8: "31-50cm", 10: "51cm+"})
    # shops: name on the upper row, price below it
    for k, (addr, goods) in enumerate(zip([0xB139, 0xB1C9, 0xB259, 0xB2E9, 0xB379], SHOPS)):
        rows = {}
        for i, (n, p) in enumerate(goods):
            rows[2 * i + 1] = " " + n
            rows[2 * i + 2] = right(f"¥{p}")
        T[(13, addr, 12, 12)] = window(12, 12, center("Shop"), rows)
    # fish buyer: price per size class
    fish = [("≤10cm", 10), ("≤20cm", 20), ("≤30cm", 30), ("≤50cm", 40), ("51cm+", 50)]
    T[(13, 0xB409, 12, 12)] = window(12, 12, center("Fish"),
                                     {2 * i + 2: s.ljust(7) + f"¥{p}" for i, (s, p) in enumerate(fish)})
    # bank 15 (now 31)
    T[(15, 0xEEB5, 12, 8)] = window(12, 8, center("Command"),
                                    {2: " Bait Eat", 4: " Gear Bag", 6: " Talk Item"})
    T[(15, 0xEF15, 12, 8)] = window(12, 8, "", {1: "Dist     m", 2: "_" * 10, 4: "    Reel", 6: "    Let Go"})
    T[(15, 0xEF75, 12, 8)] = window(12, 8, "", {2: "   Fight", 4: "   Eat", 6: "   Run"})
    T[(15, 0xEFD5, 6, 6)] = window(6, 6, "", {2: " Yes", 4: " No"})
    return T


def patch(rom, bank, addr, expect, new):
    o = off(bank, addr)
    if expect is not None:
        got = bytes(rom[o:o + len(expect)])
        assert got == bytes(expect), f"bank {bank} ${addr:04X}: expected {bytes(expect).hex()} got {got.hex()}"
    rom[o:o + len(new)] = bytes(new)


def lohi(a):
    return [a & 0xFF, a >> 8]


def apply(rom, m13, s9, fixed):
    """m13 / s9 / fixed: (code bytes, labels) of menu13.s, status9.s and the fixed-bank hook."""
    # templates
    for (bank, addr, w, h), data in templates().items():
        o = off(bank, addr)
        assert rom[o] == 0x60 and rom[o + w * h - 1] == 0x63, f"template {bank}:{addr:04X}"
        rom[o:o + w * h] = data

    code, L = m13
    o = off(13, 0xB985); rom[o:o + len(code)] = code
    names = b"".join(enc(n.ljust(9)) for n in FOOD + ITEMS)
    assert len(names) == 13 * 9
    o = off(13, L["NAMES"]); rom[o:o + len(names)] = names
    rods = b"".join(enc(center(r)) for r in RODS)
    o = off(13, L["RODS"]); rom[o:o + len(rods)] = rods
    o = off(13, L["ITEMTITLE"]); rom[o:o + 6] = enc(center("Items")[2:8])
    patch(rom, 13, 0xAC5B, [0xA2, 0x03, 0xA0, 0x06, 0xA9, 0x72, 0x9D, 0x00, 0x01, 0xE8, 0x88, 0xD0, 0xF9],
          [0xA2, 0x00, 0xBD, *lohi(L["ITEMTITLE"]), 0x9D, 0x03, 0x01, 0xE8, 0xE0, 0x06, 0xD0, 0xF5])
    slots = L["LISTSLOT"]
    S = [0x0E, 0x1A, 0x26, 0x32, 0x3E, 0x4A, 0x56, 0x62, 0x6E, 0x7A]

    # cursor: left/right check, up, down
    patch(rom, 13, 0xA5ED, [0xAD, 0x9E, 0x07, 0xC9, 0x0A, 0xB0, 0x05, 0xAD, 0x57, 0x07, 0xF0, 0x11],
          [0x20, *lohi(L["LRCHK"]), 0xB0, 0x07, 0x60] + [0xEA] * 6)
    patch(rom, 13, 0xA60B, [0xAD, 0x28, 0x02, 0x38, 0xE9, 0x10, 0xC9, 0x30, 0x90, 0x24],
          [0x20, *lohi(L["UPCALC"]), 0xB0, 0x29] + [0xEA] * 5)
    patch(rom, 13, 0xA63A, [0xAD, 0x57, 0x07, 0xD0, 0x0C, 0xAD, 0x9E, 0x07],
          [0x20, *lohi(L["DNCALC"]), 0xB0, 0x4C, 0x4C, 0x67, 0xA6])
    # eating: the slot of the chosen row, then the food's first letter
    patch(rom, 13, 0xA6FB, [0xBC, 0x68, 0xA7], [0xBC, *lohi(slots)])
    for a, old, ch in [(0xA701, 0x15, "B"), (0xA70F, 0x24, "M"), (0xA71D, 0x30, "U"), (0xA72B, 0x17, "S")]:
        patch(rom, 13, a, [0xC9, old], [0xC9, CODES[ch]])
    # name drawing: one row of 9 letters per entry
    patch(rom, 13, 0xADE3, [0xA9, 0x04, 0x85], [0x4C, *lohi(L["NAMEDRAW"])])
    for k in range(10):
        for base in (0xAD62, 0xAE09):
            a = base + 5 * k
            o = off(13, a)
            assert rom[o] == 0xA0, hex(a)
            rom[o + 1] = S[k]
    # counts one column further right (names get 6 letters plus a gap)
    for a in (0xB558, 0xB55F, 0xB566, 0xB56D, 0xB574, 0xB5B3, 0xB5BA, 0xB5C2, 0xB5C9):
        o = off(13, a); assert rom[o] == 0xA2, hex(a); rom[o + 1] += 1
    # rod name across the top border; float name table; no dakuten over the float row
    patch(rom, 13, 0xB598, [0xAD, 0xEA, 0x07, 0x0A, 0x85, 0x0C],
          [0x20, *lohi(L["RODTITLE"]), 0x4C, 0xB1, 0xB5])
    floats = b"".join(enc((" " + f).ljust(8)) for f in FLOATS)
    patch(rom, 13, 0xB653, [0xFE, 0xFE, 0x13, 0x16], floats)
    patch(rom, 13, 0xB5E3, [0xAD, 0xD7, 0x07], [0x60])

    # bank 10: item use and the map check look at the first letter of the chosen row
    patch(rom, 10, 0xB182, [0x1A, 0x32, 0x4A, 0x62, 0x7A, 0x1F, 0x37, 0x4F, 0x67, 0x7F], S)
    for a, old, ch in [(0xA1BE, 0x46, "G"), (0xA1C8, 0x11, "K"), (0xA1D2, 0x23, "M"), (0xA1DC, 0x74, "C"),
                       (0xA1E6, 0x3B, "W"), (0xA1F0, 0x15, "F"), (0xA1FA, 0x5B, "H"), (0xA204, 0x28, "A")]:
        patch(rom, 10, a, [0xC9, old], [0xC9, CODES[ch]])
    patch(rom, 10, 0xB4FA, [0xE0, 0x23], [0xE0, CODES["M"]])

    # bank 9: area name, 10 tiles
    code, L9 = s9
    o = off(9, 0xBFAB); rom[o:o + len(code)] = code
    areas = b"".join(enc(center(a)) for a in AREAS)
    o = off(9, L9["AREAS"]); rom[o:o + len(areas)] = areas
    patch(rom, 9, 0xBE6E, [0xA6, 0x7B, 0xCA, 0x8A, 0x0A, 0x85],
          [0x20, *lohi(L9["AREATITLE"]), 0x4C, 0x88, 0xBE])

    # fixed bank: cursor start row
    _, LF = fixed
    patch(rom, 15, 0xE4DC, [0xA9, 0x00, 0x8D, 0x9F, 0x07, 0xA9, 0x30],
          [0x20, *lohi(LF["INITY"]), 0xEA, 0xEA, 0xEA, 0xEA])
