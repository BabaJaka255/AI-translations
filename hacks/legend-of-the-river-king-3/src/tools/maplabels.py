"""Fishing Note area maps: the place name is drawn on a scroll baked into each map's BG tiles.

Each map is a 240x160 picture (tiles 32 per row, all unique) with a per-tile choice of 13 palettes. We render it to
RGB, paint a new scroll (wider where the English name needs it) with the name in the dialogue font, then pick the
best palette for every touched tile and re-encode. Tiles and tilemaps are stored raw and repointed."""
import struct
import numpy as np

TILES, MAPS, PALS = 0x14AB8C, 0x14ABA8, 0x14ABC4   # 7 pointers each; entries 0 and 1 are the same map
NAMES = ['Nushikiri Village', 'Oven Kingdom', 'Cold Park', 'Coconut Village', 'Fairy Town', 'Mysterious Forest']
# old scroll extent (x0, x1 inclusive, rolls included) and which way it may grow
OLD = [(5, 93, 'L'), (5, 104, 'L'), (126, 235, 'R'), (148, 235, 'R'), (5, 125, 'L'), (76, 163, 'C')]
Y0, Y1 = 4, 32          # rows replaced by the scroll strip (scroll is rows 6-31 on every map)
SRC = 1                 # map whose scroll supplies the pieces (Oven Kingdom: both ends visible, clean)
LEFT = (2, 18)          # [a, b) columns of SRC: background margin + left roll + a little body
RIGHT = (91, 109)       # body + right roll + margin
TEXT = (128, 112, 72)
PAD = 4                 # space between the rolls and the text

def u32(d, o): return struct.unpack_from('<I', d, o)[0]

def text_mask(d, text):
    """Dialogue font, proportional: each glyph trimmed to its ink plus 1 px; a space is 3 px."""
    from logo import FONT, WIDE
    cols = []
    for ch in text:
        if ch == ' ': cols += [np.zeros(10, bool)] * 3; continue
        c = ord('0' if ch == 'O' else ch); a = FONT + 20 * (c - 1 if c > 0x4F else c)
        g = np.zeros((10, 6), bool)
        for y in range(10):
            if ch in WIDE: g[y, :5] = [c == '#' for c in WIDE[ch][y]]
            else:
                v = struct.unpack_from('<H', d, a + 2 * y)[0]; g[y] = [bool(v >> (8 + x) & 1) for x in range(6)]
        ink = np.nonzero(g.any(0))[0]
        cols += list(g[:, ink.min():ink.max() + 1].T) + [np.zeros(10, bool)]
    m = np.array(cols[:-1]).T
    return m

class Map:
    def __init__(self, r, i):
        d = r.d
        self.tiles = bytearray(r.decompress(u32(d, TILES + 4 * i)))
        self.map = bytearray(r.decompress(u32(d, MAPS + 4 * i)))
        p = r.decompress(u32(d, PALS + 4 * i))
        self.npal = len(p) // 32
        self.pal = np.array([[((c & 31) * 8, (c >> 5 & 31) * 8, (c >> 10 & 31) * 8)
                              for c in struct.unpack_from('<16H', p, 32 * k)] for k in range(self.npal)], int)
    def entry(self, tx, ty): return struct.unpack_from('<H', self.map, 2 * (ty * 32 + tx))[0]
    def rgb(self):
        im = np.zeros((160, 240, 3), int)
        for ty in range(20):
            for tx in range(30):
                e = self.entry(tx, ty); n = e & 1023
                t = np.frombuffer(bytes(self.tiles[32 * n:32 * n + 32]), np.uint8)
                px = np.stack([t & 15, t >> 4], 1).reshape(8, 8)
                if e >> 10 & 1: px = px[:, ::-1]
                if e >> 11 & 1: px = px[::-1]
                im[ty * 8:ty * 8 + 8, tx * 8:tx * 8 + 8] = self.pal[e >> 12][px]
        return im
    def encode(self, im, tx0, tx1, ty0, ty1):
        """Re-encode tiles in the given tile range from RGB, each with its best palette (colour 0 not used)."""
        for ty in range(ty0, ty1):
            for tx in range(tx0, tx1):
                blk = im[ty * 8:ty * 8 + 8, tx * 8:tx * 8 + 8].reshape(64, 1, 3)
                best = None
                for k in range(self.npal):
                    dist = ((blk - self.pal[k][None, 1:]) ** 2).sum(2)
                    idx = dist.argmin(1); err = dist.min(1).sum()
                    if best is None or err < best[0]: best = (err, k, idx + 1)
                _, k, idx = best
                e = self.entry(tx, ty); n = e & 1023
                assert not e & 0xC00
                px = idx.reshape(8, 8).astype(np.uint8)
                self.tiles[32 * n:32 * n + 32] = (px[:, 0::2] | px[:, 1::2] << 4).tobytes()
                struct.pack_into('<H', self.map, 2 * (ty * 32 + tx), n | k << 12)

def body_slice(src):
    """4-px wide, phase-aligned body strip of the source scroll, picked row by row from text-free windows."""
    out = np.zeros((Y1 - Y0, 4, 3), int)
    for y in range(Y0, Y1):
        for x in range(20, 88, 4):
            w = src[y, x:x + 4]
            if not (np.abs(w - TEXT).sum(1) < 60).any() and not (w.sum(1) < 400).any():
                out[y - Y0] = w; break
        else: raise ValueError('no clean window on row %d' % y)
    return out

def scroll(src, d, name, minw):
    txt = text_mask(d, name)
    left, right = src[Y0:Y1, LEFT[0]:LEFT[1]], src[Y0:Y1, RIGHT[0]:RIGHT[1]]
    body = body_slice(src)
    inner = max(txt.shape[1] + 2 * PAD - 6, minw - left.shape[1] - right.shape[1])
    inner += (-inner) % 4
    mid = np.tile(body, (1, inner // 4, 1))
    s = np.concatenate([left, mid, right], 1)
    tx = left.shape[1] - 2 + (inner + 6 - txt.shape[1]) // 2
    ty = 18 - Y0 - (txt.shape[0] + 1) // 2 - 1
    s[ty:ty + txt.shape[0], tx:tx + txt.shape[1]][txt] = TEXT
    return s

def build(r):
    """Returns {map index: (tiles, tilemap)} with English labels."""
    src = Map(r, SRC + 1).rgb()
    out = {}
    for i, name in enumerate(NAMES):
        m = Map(r, i + 1); im = m.rgb()
        x0, x1, grow = OLD[i]
        minw = x1 - x0 + 1 + (LEFT[0] < 5) * 3 + 4
        s = scroll(src, r.d, name, minw)
        w = s.shape[1]
        left = {'L': x0 - 3, 'R': x1 + 4 - w, 'C': (x0 + x1 - w) // 2}[grow]
        left = max(0, min(240 - w, left))
        im[Y0:Y1, left:left + w] = s
        m.encode(im, left // 8, (left + w + 7) // 8, Y0 // 8, (Y1 + 7) // 8)
        out[i] = (bytes(m.tiles), bytes(m.map), im)
    return out
