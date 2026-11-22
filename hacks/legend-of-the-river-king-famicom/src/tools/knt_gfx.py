"""Graphics edits for Kawa no Nushi Tsuri (FC): town plaques and the tea banner.

Series convention (Umi no Nushi / Shizen-ha / GBA patches): building plaques
become pictures, 宿 = INN, 釣 (tackle shop) = a hook, 魚 (fish shop) = a fish.
The teahouse banner おちゃ becomes TEA.
"""
CHR_TOWN = 0x8000          # CHR offset of the town tile page (JP file 0x28010)


def _tile_get(rom, o):
    px = [[0] * 8 for _ in range(8)]
    for y in range(8):
        a, b = rom[o + y], rom[o + y + 8]
        for x in range(8):
            px[y][x] = ((a >> (7 - x)) & 1) | (((b >> (7 - x)) & 1) << 1)
    return px


def _tile_put(rom, o, px):
    for y in range(8):
        a = b = 0
        for x in range(8):
            a |= (px[y][x] & 1) << (7 - x)
            b |= ((px[y][x] >> 1) & 1) << (7 - x)
        rom[o + y], rom[o + y + 8] = a, b


def _sign(rom, base, tiles, art):
    """tiles: (tl, tr, bl, br) tile numbers of a 16x16 plaque.  art: up to 12
    rows of up to 12 chars ('#' ink) drawn centred in the plaque's inside
    (rows 2-13, cols 2-14), ink colour 0 on colour 3."""
    T = [_tile_get(rom, base + t * 16) for t in tiles]
    g = [[(T[0] if y < 8 else T[2])[y % 8][x] if x < 8 else (T[1] if y < 8 else T[3])[y % 8][x - 8]
          for x in range(16)] for y in range(16)]
    for y in range(2, 14):
        for x in range(2, 15):
            g[y][x] = 3
    h = len(art); w = max(len(r) for r in art)
    oy = 2 + (12 - h) // 2; ox = 2 + (13 - w + 1) // 2
    for y, r in enumerate(art):
        for x, c in enumerate(r):
            if c == "#":
                g[oy + y][ox + x] = 0
    for i, t in enumerate(tiles):
        _tile_put(rom, base + t * 16, [[g[(i // 2) * 8 + y][(i % 2) * 8 + x] for x in range(8)] for y in range(8)])


INN = [
    "###.#..#.#..#",
    ".#..##.#.##.#",
    ".#..##.#.##.#",
    ".#..#.##.#.##",
    ".#..#.##.#.##",
    ".#..#..#.#..#",
    ".#..#..#.#..#",
    "###.#..#.#..#",
]
HOOK = [
    ".......###",
    ".......#.#",
    ".......###",
    "........#.",
    "........#.",
    "........#.",
    "........#.",
    "..#.....#.",
    ".##.....#.",
    "#.#.....#.",
    "..#....#..",
    "...####...",
]
FISH = [
    "..#####....",
    ".#.....#..#",
    "#.#.....##.",
    "#........#.",
    "#.......##.",
    ".#.....#..#",
    "..#####....",
]
TEA = [  # 6 wide, 6 rows each, two blank rows between letters
    "######", "..##..", "..##..", "..##..", "..##..", "..##..",
    "......", "......",
    "######", "##....", "#####.", "##....", "##....", "######",
    "......", "......",
    "..##..", ".####.", "##..##", "######", "##..##", "##..##",
]
BANNER = (0x52, 0x53, 0x62, 0x63, 0x00, 0x01, 0x10, 0x58)   # 2 tiles wide, 4 tall


def _banner(rom, base):
    """Tea-stall banner おちゃ -> TEA.  Lettering area: cols 5-12, rows 1-24 of
    the 16x32 banner; ink colour 3 on the red colour 2, as the original kana."""
    T = [_tile_get(rom, base + t * 16) for t in BANNER]
    g = [[T[(y // 8) * 2 + (x // 8)][y % 8][x % 8] for x in range(16)] for y in range(32)]
    for y in range(1, 25):
        for x in range(5, 13):
            g[y][x] = 2
    for y, r in enumerate(TEA):
        for x, c in enumerate(r):
            if c == "#":
                g[2 + y][6 + x] = 3
    for i, t in enumerate(BANNER):
        _tile_put(rom, base + t * 16, [[g[(i // 2) * 8 + y][(i % 2) * 8 + x] for x in range(8)] for y in range(8)])


def apply(rom, chr_start):
    base = chr_start + CHR_TOWN
    _sign(rom, base, (2, 3, 18, 19), INN)
    _sign(rom, base, (4, 5, 20, 21), FISH)
    _sign(rom, base, (6, 7, 22, 23), HOOK)
    _banner(rom, base)
