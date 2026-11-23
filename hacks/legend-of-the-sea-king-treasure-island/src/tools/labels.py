"""Fishing Note map labels: the game draws each caught fish's name from a pre-rendered atlas in COMM.TIM image 0
(4bpp, rows 48-151 hold 97 katakana labels, 8 px per kana) using (u, v, w) bytes at fish_table + i*52 + 48.
We redraw the atlas with hand-pixelled English names (tiny mixed-case font below, navy on the label blue with a
soft shade column, like the bold katakana) and pack them into the old atlas rows plus clear gaps elsewhere."""
import sys, struct; sys.path.insert(0, 'tools')
import numpy as np
import tim

FISH_TABLE, STRIDE, NFISH, FIRST_ID = 0x800e4cf8, 52, 97, 740
BG, INK, SHADE = 1, 13, 6
# rows 0-7 of the 8 px label; '#' ink. Caps sit on rows 1-6, x-height rows 3-6, descenders row 7.
F = {}
def g(ch, *rows):
    F[ch] = [r for r in rows]
def caps(ch, *r6): g(ch, '.' * len(r6[0]), *r6, '.' * len(r6[0]))
def low(ch, asc, *r4, desc=None):
    w = len(r4[0]); g(ch, '.' * w, *(asc or ['.' * w, '.' * w]), *r4, desc or '.' * w)
caps('A', '.#.', '#.#', '#.#', '###', '#.#', '#.#')
caps('B', '##.', '#.#', '##.', '#.#', '#.#', '##.')
caps('C', '.##', '#..', '#..', '#..', '#..', '.##')
caps('D', '##.', '#.#', '#.#', '#.#', '#.#', '##.')
caps('E', '###', '#..', '##.', '#..', '#..', '###')
caps('F', '###', '#..', '##.', '#..', '#..', '#..')
caps('G', '.##', '#..', '#..', '#.#', '#.#', '.##')
caps('H', '#.#', '#.#', '###', '#.#', '#.#', '#.#')
caps('I', '#', '#', '#', '#', '#', '#')
caps('J', '..#', '..#', '..#', '..#', '#.#', '.#.')
caps('K', '#.#', '#.#', '##.', '#.#', '#.#', '#.#')
caps('L', '#..', '#..', '#..', '#..', '#..', '###')
caps('M', '#...#', '##.##', '#.#.#', '#...#', '#...#', '#...#')
caps('N', '#..#', '##.#', '##.#', '#.##', '#.##', '#..#')
caps('O', '.#.', '#.#', '#.#', '#.#', '#.#', '.#.')
caps('P', '##.', '#.#', '#.#', '##.', '#..', '#..')
caps('R', '##.', '#.#', '#.#', '##.', '#.#', '#.#')
caps('S', '.##', '#..', '.#.', '..#', '..#', '##.')
caps('T', '###', '.#.', '.#.', '.#.', '.#.', '.#.')
caps('W', '#...#', '#...#', '#...#', '#.#.#', '##.##', '#...#')
caps('Y', '#.#', '#.#', '.#.', '.#.', '.#.', '.#.')
low('a', None, '.##', '#.#', '#.#', '.##')
low('b', ['#..', '#..'], '##.', '#.#', '#.#', '##.')
low('c', None, '.##', '#..', '#..', '.##')
low('d', ['..#', '..#'], '.##', '#.#', '#.#', '.##')
low('e', None, '.#.', '###', '#..', '.##')
low('f', ['.#', '#.'], '##', '#.', '#.', '#.')
low('g', None, '.##', '#.#', '.##', '..#', desc='##.')
low('h', ['#..', '#..'], '##.', '#.#', '#.#', '#.#')
low('i', ['#', '.'], '#', '#', '#', '#')
low('j', ['.#', '..'], '.#', '.#', '.#', '.#', desc='#.')
low('k', ['#..', '#..'], '#.#', '##.', '#.#', '#.#')
low('l', ['#', '#'], '#', '#', '#', '#')
low('m', None, '####.', '#.#.#', '#.#.#', '#.#.#')
low('n', None, '##.', '#.#', '#.#', '#.#')
low('o', None, '.#.', '#.#', '#.#', '.#.')
low('p', None, '##.', '#.#', '##.', '#..', desc='#..')
low('q', None, '.##', '#.#', '.##', '..#', desc='..#')
low('r', None, '#.#', '##.', '#..', '#..')
low('s', None, '.##', '#..', '..#', '##.')
low('t', ['..', '#.'], '##', '#.', '#.', '.#')
low('u', None, '#.#', '#.#', '#.#', '.##')
low('v', None, '#.#', '#.#', '#.#', '.#.')
low('w', None, '#...#', '#...#', '#.#.#', '.#.#.')
low('x', None, '#.#', '.#.', '.#.', '#.#')
low('y', None, '#.#', '#.#', '.##', '..#', desc='##.')
low('z', None, '###', '..#', '.#.', '###')
g('-', '..', '..', '..', '..', '##', '..', '..', '..')
g('.', '.', '.', '.', '.', '.', '.', '#', '.')
g(' ', '.', '.', '.', '.', '.', '.', '.', '.')
for k, v in F.items(): assert len(v) == 8 and len(set(map(len, v))) == 1, k

def label(text):
    """-> 8 x w index array: 1 px lead, glyphs with 1 px spacing (the spacing column carries the shade)."""
    cols = [np.full(8, BG)]
    for c in text:
        gl = F[c]; w = len(gl[0])
        for x in range(w): cols.append(np.array([INK if gl[y][x] == '#' else BG for y in range(8)]))
        cols.append(np.full(8, BG))
    a = np.stack(cols, 1)
    ink = a == INK
    sh = np.zeros_like(ink); sh[1:, 1:] = ink[:-1, :-1]          # soft shade down-right, as the kana have
    a[sh & ~ink] = SHADE
    return a

def free_segments(idx):
    """8-row bands to pack into: the old atlas rows, then transparent gaps with a 2 px clearance elsewhere."""
    from scipy import ndimage
    op = idx != 0; op[48:152] = False
    occ = ndimage.binary_dilation(op, iterations=3)
    segs = [(48 + 8 * k, 0, 256) for k in range(13)]
    for y0 in list(range(152, 256, 8)) + list(range(0, 48, 8)):
        col = ~occ[y0:y0 + 8].any(0); x = 0
        while x < 256:
            if col[x]:
                s = x
                while x < 256 and col[x]: x += 1
                if x - s >= 12: segs.append((y0, s, x - s))
            else: x += 1
    return segs

def fish_names(en):
    """English name of each fish table entry, from the entry's own name pointer (word 7). The string ids are NOT
    FIRST_ID + i: entry 32 points at an empty string and later ids drift, so map by address."""
    import json
    S = json.load(open('out/script_jp.json'))
    by_addr = {int(o['addr'], 16): o['id'] for o in S}
    exe = open('files/SLPS_021.72', 'rb').read()
    out = {}
    for i in range(NFISH):
        p = struct.unpack_from('<I', exe, FISH_TABLE + i * STRIDE + 28 - 0x80010000 + 0x800)[0]
        sid = by_addr.get(p)
        if sid is not None and en.get(sid): out[i] = en[sid]
    return out

def apply(comm, en):
    comm = bytearray(comm)
    t = tim.parse(bytes(comm), 0); idx = tim.indices(t).copy()
    names = fish_names(en)                                  # entries with a blank name get no label
    labs = {i: label(n) for i, n in names.items()}
    idx[48:152] = 0
    segs = [list(s) for s in free_segments(idx)]
    order = sorted(labs, key=lambda i: -labs[i].shape[1])
    place = {}
    for i in order:
        w = labs[i].shape[1]
        for s in segs:
            if s[2] >= w:
                place[i] = (s[1], s[0], w); idx[s[0]:s[0] + 8, s[1]:s[1] + w] = labs[i]; s[1] += w; s[2] -= w; break
        else: raise SystemExit('label atlas full at %r' % names[i])
    img = t['img']; w, h = img['w'], img['h']
    words = (idx[:, 0::4] | (idx[:, 1::4] << 4) | (idx[:, 2::4] << 8) | (idx[:, 3::4] << 12)).astype('<u2')
    comm[img['off']:img['off'] + 2 * w * h] = words.tobytes()
    return bytes(comm), place, idx

def patch_exe(exe, place):
    exe = bytearray(exe)
    for i, (u, v, w) in place.items():
        o = FISH_TABLE + i * STRIDE + 48 - 0x80010000 + 0x800
        assert w < 256
        exe[o:o + 3] = bytes([u, v, w])
    return bytes(exe)

if __name__ == '__main__':
    from textfmt import load_en
    from PIL import Image
    comm, place, idx = apply(open('files/TIM/COMM.TIM', 'rb').read(), load_en())
    t = tim.parse(comm, 0); pal = [tim.c15(int(v))[:3] for v in t['clut']['data'][0]]
    rgb = np.array(pal, np.uint8)[idx]; rgb[idx == 0] = (255, 0, 255)
    Image.fromarray(rgb).resize((768, 768), Image.NEAREST).save('view/labels_atlas.png')
    print(len(place), 'placed; rows used:', sorted(set(v for u, v, w in place.values())))
