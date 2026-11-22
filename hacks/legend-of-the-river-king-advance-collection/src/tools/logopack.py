# Cut an RGBA logo into GBA OBJ pieces, pack them into a 2D-mapped char area (32 tiles wide) and build
# 4bpp tiles, 15-colour palettes and metasprite templates for the title sprite engine (8-byte OAM templates,
# list ended by a0 = 0xC000; offsets relative to the metasprite centre).
import numpy as np
from PIL import Image

SHAPES = {(8, 8): (0, 0), (16, 16): (0, 1), (32, 32): (0, 2), (64, 64): (0, 3),
          (16, 8): (1, 0), (32, 8): (1, 1), (32, 16): (1, 2), (64, 32): (1, 3),
          (8, 16): (2, 0), (8, 32): (2, 1), (16, 32): (2, 2), (32, 64): (2, 3)}
WIDTHS = {8: [32, 16, 8], 16: [32, 16, 8], 32: [64, 32, 16, 8], 64: [64, 32]}
PIECE_COST = 6      # in tiles: trades piece count against wasted tiles

def load(path, w, thresh=110):
    im = Image.open(path).convert('RGBA'); im = im.crop(im.getbbox())
    h = round(im.height * w / im.width)
    a = np.asarray(im).astype(float); a[..., :3] *= a[..., 3:4] / 255
    r = np.asarray(Image.fromarray(a.astype(np.uint8)).resize((w, h), Image.LANCZOS)).astype(float)
    al = r[..., 3]
    rgb = np.where(al[..., None] > 0, r[..., :3] * 255 / np.maximum(al[..., None], 1), 0)
    return np.clip(rgb, 0, 255).astype(np.uint8), al > thresh

def cover(op, piece_cost=None):
    """op: opaque mask (H, W) -> list of pieces (x, y, w, h) in pixels."""
    pc = PIECE_COST if piece_cost is None else piece_cost
    H, W = op.shape
    th, tw = -(-H // 8), -(-W // 8)
    cell = np.zeros((th, tw), bool)
    for ty in range(th):
        for tx in range(tw):
            cell[ty, tx] = op[ty * 8:ty * 8 + 8, tx * 8:tx * 8 + 8].any()
    def band(r0, bh):
        cols = cell[r0:r0 + bh // 8].any(0) if r0 < th else np.zeros(tw, bool)
        # DP over columns: cover every opaque column with runs of allowed widths
        INF = 10 ** 9; best = [INF] * (tw + 1); how = [None] * (tw + 1); best[tw] = 0
        for c in range(tw - 1, -1, -1):
            if not cols[c]:
                best[c] = best[c + 1]; how[c] = None; continue
            for w in WIDTHS[bh]:
                n = w // 8
                cost = pc + n * bh // 8 + best[min(tw, c + n)]
                if cost < best[c]: best[c], how[c] = cost, w
        out, c = [], 0
        while c < tw:
            if how[c] is None: c += 1; continue
            out.append((c * 8, r0 * 8, how[c], bh)); c += how[c] // 8
        return best[0], out
    INF = 10 ** 9; f = [INF] * (th + 1); g = [None] * (th + 1); f[th] = 0
    for r in range(th - 1, -1, -1):
        if not cell[r].any(): f[r] = f[r + 1]; g[r] = None; continue
        for bh in (8, 16, 32, 64):
            cst, ps = band(r, bh)
            cst += f[min(th, r + bh // 8)]
            if cst < f[r]: f[r], g[r] = cst, (bh, ps)
    pieces, r = [], 0
    while r < th:
        if g[r] is None: r += 1; continue
        pieces += g[r][1]; r += g[r][0] // 8
    return pieces

def pack(pieces, free):
    """free: bool grid (rows, 32) of usable tiles. Returns tile index (row*32+col) per piece, or None."""
    free = free.copy(); place = [None] * len(pieces)
    order = sorted(range(len(pieces)), key=lambda i: (-pieces[i][3], -pieces[i][2]))
    R, C = free.shape
    for i in order:
        w, h = pieces[i][2] // 8, pieces[i][3] // 8
        for r in range(R - h + 1):
            for c in range(C - w + 1):
                if free[r:r + h, c:c + w].all():
                    free[r:r + h, c:c + w] = False; place[i] = r * 32 + c; break
            if place[i] is not None: break
        if place[i] is None: return None
    return place

def to15(rgb):
    return (rgb.astype(int) * 31 + 127) // 255

def kmeans(px, k, iters=25):
    """px: (N,3) 5-bit colours -> (k,3) centres."""
    u, cnt = np.unique(px, axis=0, return_counts=True)
    if len(u) <= k: return u
    rng = np.random.default_rng(1)
    c = u[rng.choice(len(u), k, replace=False, p=cnt / cnt.sum())].astype(float)
    for _ in range(iters):
        d = ((u[:, None, :] - c[None]) ** 2).sum(-1); a = d.argmin(1)
        for j in range(k):
            m = a == j
            if m.any(): c[j] = (u[m] * cnt[m, None]).sum(0) / cnt[m].sum()
    return np.clip(np.rint(c), 0, 31).astype(int)

def qerr(px, k=15):
    c = kmeans(px, k, 8)
    return ((px[:, None, :] - c[None]) ** 2).sum(-1).min(1).sum()

def group(rgb15, op, pieces, npal):
    """Merge pieces into at most npal palette groups, greedily keeping the quantisation error low."""
    pxs = [rgb15[y:y + h, x:x + w][op[y:y + h, x:x + w]] for x, y, w, h in pieces]
    groups = [[i] for i in range(len(pieces)) if len(pxs[i])]
    empty = [i for i in range(len(pieces)) if not len(pxs[i])]
    gp = lambda g: np.concatenate([pxs[i] for i in g])
    err = {tuple(g): qerr(gp(g)) for g in groups}
    while len(groups) > npal:
        best = None
        for a in range(len(groups)):
            for b in range(a + 1, len(groups)):
                m = groups[a] + groups[b]
                e = qerr(gp(m)) - err[tuple(groups[a])] - err[tuple(groups[b])]
                if best is None or e < best[0]: best = (e, a, b, m)
        e, a, b, m = best
        groups = [g for k, g in enumerate(groups) if k not in (a, b)] + [m]
        err[tuple(m)] = qerr(gp(m))
    if empty: groups[0] += empty
    return groups

def tiles_of(idx, x, y, w, h):
    out = []
    for ty in range(h // 8):
        for tx in range(w // 8):
            b = idx[y + ty * 8:y + ty * 8 + 8, x + tx * 8:x + tx * 8 + 8]
            out.append(bytes(int(b[r, c]) | int(b[r, c + 1]) << 4 for r in range(8) for c in range(0, 8, 2)))
    return out

def build(path, width, free, max_pieces, pal_ids, centre):
    """Returns dict(charmap={tile: 32 bytes}, pals={pal: [16 colours 15-bit]}, frame=bytes, pieces, size)."""
    rgb, op = load(path, width)
    H, W = op.shape
    pad = np.zeros((-(-H // 8) * 8 + 64, -(-W // 8) * 8 + 64), bool); pad[:H, :W] = op
    prgb = np.zeros(pad.shape + (3,), np.uint8); prgb[:H, :W] = rgb
    # fewer pieces first; fall back to tighter (more, smaller) pieces until they fit the char area
    for pc in (8, 6, 4, 3, 2, 1, 0.5):
        pieces = cover(pad, pc)
        if len(pieces) > max_pieces: continue
        place = pack(pieces, free)
        if place is not None: break
    else:
        return None
    rgb15 = to15(prgb)
    groups = group(rgb15, pad, pieces, len(pal_ids))
    idx = np.zeros(pad.shape, np.uint8); pals = {}; piece_pal = {}
    for gi, g in enumerate(groups):
        px = np.concatenate([rgb15[y:y + h, x:x + w][pad[y:y + h, x:x + w]] for x, y, w, h in (pieces[i] for i in g)])
        cen = kmeans(px, 15)
        pid = pal_ids[gi]
        pals[pid] = [0x7c1f] + [int(r | g_ << 5 | b << 10) for r, g_, b in cen] + [0] * (15 - len(cen))
        for i in g:
            x, y, w, h = pieces[i]; piece_pal[i] = pid
            sub = rgb15[y:y + h, x:x + w]; d = ((sub[..., None, :] - cen[None, None]) ** 2).sum(-1)
            q = (d.argmin(-1) + 1).astype(np.uint8); q[~pad[y:y + h, x:x + w]] = 0
            idx[y:y + h, x:x + w] = q
    charmap = {}; frame = b''
    ox, oy = centre[0] - W // 2, centre[1] - H // 2      # logo top-left relative to the metasprite centre
    import struct
    for i, (x, y, w, h) in enumerate(pieces):
        t0 = place[i]
        for k, tile in enumerate(tiles_of(idx, x, y, w, h)):
            ty, tx = divmod(k, w // 8)
            charmap[t0 + ty * 32 + tx] = tile
        shape, size = SHAPES[(w, h)]
        rx, ry = ox + x, oy + y
        a0 = (ry & 0xff) | shape << 14
        a1 = (rx & 0x1ff) | size << 14
        a2 = t0 | piece_pal[i] << 12
        frame += struct.pack('<4H', a0, a1, a2, 0)
    frame += struct.pack('<4H', 0xc000, 0, 0, 0)
    return dict(charmap=charmap, pals=pals, frame=frame, pieces=pieces, size=(W, H), idx=idx, place=place)
