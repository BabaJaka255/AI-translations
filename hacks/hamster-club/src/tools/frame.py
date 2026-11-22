"""Screen-space editing of BG and sprite tiles, frame by frame.

Frame(state, sheets) maps every screen pixel to the tile pixels that cover it:
sprites (8x16 or 8x8, flips, CGB VRAM bank) and the BG/window. Lettering is then
erased and redrawn on screen coordinates and written back into the tiles.

sheets: {name: (Sheet, vram_addr, vram_bank, kind)} with kind 'obj' or 'bg'.
"""
import os, collections
from pyboy import PyBoy

BUILD = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../build/hamster-club-gbc-en.gbc')

def col(c):
    return tuple(((c >> s) & 31) * 255 // 31 for s in (0, 5, 10))

class Frame:
    def __init__(self, state, sheets, rom=BUILD, pb=None):
        own = pb is None
        if own:
            pb = PyBoy(rom, window='null', sound_emulated=False)
            pb.load_state(open(state, 'rb') if isinstance(state, str) else state)
            pb.tick(1, True)
        M = pb.memory
        self.lcdc = M[0xFF40]; scy, scx = M[0xFF42], M[0xFF43]; wy, wx = M[0xFF4A], M[0xFF4B]
        self.image = pb.screen.image.convert('RGB')
        bgbase = 0x9C00 if self.lcdc & 8 else 0x9800
        wbase = 0x9C00 if self.lcdc & 0x40 else 0x9800
        vmap = lambda base: ([M[0, a] for a in range(base, base + 0x400)], [M[1, a] for a in range(base, base + 0x400)])
        bgm, bga = vmap(bgbase); wm, wa = vmap(wbase)
        oam = [M[0xFE00 + i] for i in range(160)]
        if own: pb.stop(save=False)
        self.sheets = sheets
        tall = bool(self.lcdc & 4)
        def find(addr, bank, kind):
            for name, (sh, va, vb, k) in sheets.items():
                n = int(sh.tiles or (sh.w // 8) * (sh.h // 8))
                if vb == bank and va <= addr < va + n * 16 and (k == kind or k == 'any'):
                    return name, (addr - va) // 16
            return None
        # per pixel: list of sources (name, tile, tx, ty, kind, visible_value_now)
        self.src = [[[] for _ in range(160)] for _ in range(144)]
        win_on = self.lcdc & 0x20 and wx <= 166 and wy <= 143
        for y in range(144):
            for x in range(160):
                if win_on and x >= wx - 7 and y >= wy:
                    mx, my = x - (wx - 7), y - wy; m, a = wm, wa
                else:
                    mx, my = (x + scx) & 255, (y + scy) & 255; m, a = bgm, bga
                i = (my // 8) * 32 + mx // 8
                t, at = m[i], a[i]
                addr = 0x8000 + t * 16 if self.lcdc & 0x10 else 0x9000 + ((t ^ 0x80) - 0x80) * 16
                f = find(addr, (at >> 3) & 1, 'bg')
                if f:
                    tx, ty = mx % 8, my % 8
                    if at & 0x20: tx = 7 - tx
                    if at & 0x40: ty = 7 - ty
                    self.src[y][x].append((f[0], f[1], tx, ty, 'bg'))
        for s in range(39, -1, -1):
            oy, ox, t, at = oam[4 * s:4 * s + 4]
            sy, sx = oy - 16, ox - 8
            h = 16 if tall else 8
            if not (-h < sy < 144 and -8 < sx < 160): continue
            for j in range(h):
                for i in range(8):
                    x, y = sx + i, sy + j
                    if not (0 <= x < 160 and 0 <= y < 144): continue
                    tx = 7 - i if at & 0x20 else i
                    ty = (h - 1 - j) if at & 0x40 else j
                    tile = (t & 0xFE if tall else t) + ty // 8
                    f = find(0x8000 + tile * 16, (at >> 3) & 1, 'obj')
                    if f:
                        # sprites drawn later in this loop have priority: put first
                        self.src[y][x].insert(0, (f[0], f[1], tx, ty % 8, 'obj'))

    def xy(self, name, t):
        sh = self.sheets[name][0]
        if self.sheets[name][3] == 'obj' and getattr(sh, 'order', 'linear') == 'obj8x16':
            W = sh.w // 8; cell = t // 2
            return (cell % W) * 8, (cell // W) * 16 + (t % 2) * 8
        W = sh.w // 8
        return (t % W) * 8, (t // W) * 8

    def value(self, s):
        name, t, tx, ty, k = s
        x0, y0 = self.xy(name, t)
        return self.sheets[name][0].get(x0 + tx, y0 + ty)

    def set(self, s, v):
        name, t, tx, ty, k = s
        x0, y0 = self.xy(name, t)
        self.sheets[name][0].put(x0 + tx, y0 + ty, v)

    def top(self, x, y, targets=None):
        """The visible source at (x, y): first sprite with a non-zero pixel, else BG."""
        for s in self.src[y][x]:
            if s[4] == 'obj' and self.value(s) == 0: continue
            return s
        return None

    def edit(self, rect, targets, erase, erase_to, ink=None, ink_at=None, keep=None, shared_ok=False):
        """In rect (x0,y0,x1,y1): pixels from tiles in `targets` (set of (name,
        tile) or names) whose value passes erase(v) become erase_to(src) (or the
        int). Then ink: list of (x, y, value) drawn into the first target source
        at that pixel (sprites first, even transparent ones). Returns conflicts."""
        def ok(s):
            return (s[0], s[1]) in targets or s[0] in targets
        writes = {}; conflicts = 0
        x0, y0, x1, y1 = rect
        for y in range(max(0, y0), min(144, y1)):
            for x in range(max(0, x0), min(160, x1)):
                if keep and keep(x, y): continue
                for s in self.src[y][x]:
                    if ok(s) and erase(self.value(s)):
                        writes[s] = erase_to(s) if callable(erase_to) else erase_to
        for s, v in writes.items(): self.set(s, v)
        # BG tiles that also show outside rect (blank fill, repeated scenery) take no ink
        shared = set()
        if not shared_ok:
            for yy in range(144):
                for xx in range(160):
                    for s in self.src[yy][xx]:
                        if s[4] == 'bg' and s[2] in (0, 7) and s[3] in (0, 7):
                            if not (x0 - 8 < xx < x1 + 8 and y0 - 8 < yy < y1 + 8): shared.add(s[:2])
        done = {}
        for (x, y, v) in (ink or []):
            if not (0 <= x < 160 and 0 <= y < 144): continue
            cand = [s for s in self.src[y][x] if ok(s) and s[:2] not in shared]
            if not cand: conflicts += 1; continue
            s = cand[0]
            key = s[:4]
            if key in done and done[key] != v: conflicts += 1; continue
            done[key] = v; self.set(s, v)
        return conflicts

def mask_ink(mask, x0, y0, v):
    return [(x0 + i, y0 + j, v(x0 + i, y0 + j) if callable(v) else v)
            for j, r in enumerate(mask) for i, m in enumerate(r) if m]

def styled_ink(mask, x0, y0, fill, outline=None, shadow=None, sdx=1, sdy=1, ring=None):
    """Ink list: ring (2px outer border), shadow, then outline, then fill (later entries win)."""
    import letter
    out = []
    if ring is not None:
        out += mask_ink(letter.dilate(letter.dilate(mask, 1), 1), x0 - 2, y0 - 2, ring)
    if shadow is not None:
        base = letter.dilate(mask, 1) if outline is not None else mask
        o = 1 if outline is not None else 0
        out += mask_ink(base, x0 - o + sdx, y0 - o + sdy, shadow)
    if outline is not None:
        out += mask_ink(letter.dilate(mask, 1), x0 - 1, y0 - 1, outline)
    out += mask_ink(mask, x0, y0, fill)
    # keep the last value per pixel
    d = {}
    for x, y, v in out: d[(x, y)] = v
    return [(x, y, v) for (x, y), v in d.items()]
