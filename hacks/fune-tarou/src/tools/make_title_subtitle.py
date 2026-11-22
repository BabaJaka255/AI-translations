"""Draws gfx/edit/title-subtitle.png, the hand-drawn "Fune Tarō" lettering under the title logo.
The letter shapes below are drawn by hand (15 rows, caps 0-14, x-height 5-14) to match the brush strokes of the
ふね太郎 logo: forward lean, a red-to-orange face gradient per letter, a yellow right edge, an olive underside and a
dark purple shadow, all in the logo's own colors. The PNG is the source the build reads: edit it directly if
you like, and only rerun this script to start over from these shapes.
python3 tools/make_title_subtitle.py"""
import os
L = {}
L['F'] = """
.##########
###########
####.....##
####.......
####.......
####.......
#########..
########...
####.......
####.......
####.......
####.......
####.......
###........
.#........."""
L['u'] = """
####..###.
####..###.
###...###.
###...###.
###...###.
###...###.
###..####.
####.####.
.#########
..###..##."""
L['n'] = """
###.####..
#########.
#####.####
####...###
###....###
###....###
###....###
###....###
###....###
##.....##."""
L['e'] = """
...####...
..######..
.###..###.
###....###
##########
#########.
###.......
###....##.
.#######..
..#####..."""
L['T'] = """
..###########
#############
###..####..##
.....####....
.....####....
.....####....
.....####....
.....####....
.....####....
.....####....
.....####....
.....####....
.....####....
.....###.....
......#......"""
L['a'] = """
..######..
.###..###.
......###.
..#######.
.###..###.
###...###.
###...###.
###..####.
.#####.###
..###...#."""
L['r'] = """
###.####
########
#####..#
####....
###.....
###.....
###.....
###.....
###.....
.#......"""
L['ō'] = """
.########.
.########.
..........
...####...
.###..###.
###....###
###....###
###....###
###....###
###....###
###....###
.###..###.
...####..."""
H = 15
def rows(ch):
    r=[l for l in L[ch].strip('\n').split('\n')]
    return H-len(r), r


C = {'r1': (0xa4, 0x20, 0x10), 'r2': (0xc5, 0x39, 0x20), 'r3': (0xe6, 0x5a, 0x41), 'o1': (0xff, 0x8b, 0x52),
     'o2': (0xff, 0xac, 0x5a), 'y': (0xe6, 0xe6, 0x52), 'ol': (0xac, 0xa4, 0x41), 'sh': (0x7b, 0x41, 0x5a)}
BANDS = ['r1', 'r2', 'r3', 'o1', 'o2']


def compose(text, gap=2, space=6):
    face, x = {}, 0
    for ch in text:
        if ch == ' ':
            x += space
            continue
        top, r = rows(ch)
        b0 = 3 if ch == 'ō' else 0            # the macron takes the top band
        n = len(r) - b0
        for yy, l in enumerate(r):
            for xx, c in enumerate(l):
                if c == '#':
                    y = top + yy
                    face[(x + xx + (14 - y) // 5, y)] = BANDS[min(4, max(0, (yy - b0) * 5 // n))]
        x += len(r[0]) + gap
    pix, S = {}, set(face)
    for p in {(a + 1, b + 1) for a, b in S} - S:
        pix[p] = 'ol'
    for p in {(a + 1, b) for a, b in S} - S:
        pix[p] = 'y'
    allp = S | set(pix)
    for p in {(a + 1, b) for a, b in allp} - allp:
        pix[p] = 'sh'
    pix.update(face)
    return pix


if __name__ == '__main__':
    from PIL import Image
    pix = compose('Fune Tarō')
    im = Image.new('RGBA', (max(p[0] for p in pix) + 1, 16), (0, 0, 0, 0))
    for (x, y), c in pix.items():
        im.putpixel((x, y), C[c] + (255,))
    out = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'gfx', 'edit', 'title-subtitle.png')
    im.save(out)
    print(out, im.size)
