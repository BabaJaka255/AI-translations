"""Screen-space view of BG art, for redrawing lettering that spans many tiles.

From a PyBoy save state, map every visible BG cell to (sheet, tile, flips,
palette) for the sheets loaded into VRAM, so a word can be drawn on a 160x144
canvas and written back into the tiles. Cells whose tile is also used outside
the edited region are reported, because changing them would change the other
place too.
"""
import os, collections
from pyboy import PyBoy

BUILD = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../build/hamster-club-gbc-en.gbc')

def col(c):
    return tuple(((c >> s) & 31) * 255 // 31 for s in (0, 5, 10))

class Screen:
    def __init__(self, state, sheets, rom=BUILD, ticks=1):
        """sheets: {name: (Sheet, vram_addr, vram_bank)}"""
        pb = PyBoy(rom, window='null', sound_emulated=False)
        pb.load_state(open(state, 'rb'))
        pb.tick(ticks, True)
        M = pb.memory
        self.lcdc = M[0xFF40]; self.scx = M[0xFF43]; self.scy = M[0xFF42]
        base = 0x9C00 if self.lcdc & 8 else 0x9800
        self.map = [M[0, a] for a in range(base, base + 0x400)]
        self.attr = [M[1, a] for a in range(base, base + 0x400)]
        self.pal = [col(M[a] | M[a + 1] << 8) for a in range(0xC0A0, 0xC0E0, 2)]
        self.image = pb.screen.image.convert('RGB')
        pb.stop(save=False)
        self.sheets = sheets
        self.cells = {}
        for r in range(32):
            for c in range(32):
                t = self.map[r * 32 + c]; a = self.attr[r * 32 + c]
                addr = 0x8000 + t * 16 if self.lcdc & 0x10 else 0x9000 + ((t ^ 0x80) - 0x80) * 16
                bank = (a >> 3) & 1
                for name, (sh, va, vb) in sheets.items():
                    n = int(sh.tiles or (sh.w // 8) * (sh.h // 8))
                    if vb == bank and va <= addr < va + n * 16:
                        self.cells[(r, c)] = (name, (addr - va) // 16, bool(a & 0x20), bool(a & 0x40), a & 7)

    def visible(self, r, c):
        """BG map cell under screen cell (r, c) (scroll must be a multiple of 8)."""
        return ((r + self.scy // 8) % 32, (c + self.scx // 8) % 32)

    def tile_xy(self, name, t):
        sh = self.sheets[name][0]
        W = sh.w // 8
        return (t % W) * 8, (t // W) * 8

    def users(self):
        u = collections.defaultdict(list)
        for (r, c), (name, t, fx, fy, p) in self.cells.items():
            u[(name, t)].append((r, c))
        return u

    def read(self, r, c):
        """8x8 values of screen cell (r, c), flips applied."""
        name, t, fx, fy, p = self.cells[self.visible(r, c)]
        sh = self.sheets[name][0]; x0, y0 = self.tile_xy(name, t)
        out = [[0] * 8 for _ in range(8)]
        for j in range(8):
            for i in range(8):
                sx = 7 - i if fx else i; sy = 7 - j if fy else j
                out[j][i] = sh.get(x0 + sx, y0 + sy)
        return out

    def canvas(self, r0, c0, r1, c1):
        """Values of screen cells [r0,r1) x [c0,c1) as a pixel grid, plus palettes."""
        g = [[0] * ((c1 - c0) * 8) for _ in range((r1 - r0) * 8)]
        pals = {}
        for r in range(r0, r1):
            for c in range(c0, c1):
                if self.visible(r, c) not in self.cells: continue
                v = self.read(r, c)
                pals[(r, c)] = self.cells[self.visible(r, c)][4]
                for j in range(8):
                    for i in range(8):
                        g[(r - r0) * 8 + j][(c - c0) * 8 + i] = v[j][i]
        return g, pals

    def write(self, g, r0, c0, r1, c1, allow_shared=False):
        """Write a pixel grid back into the tiles under cells [r0,r1) x [c0,c1).
        Returns the list of conflicts (tile used outside the region, or used
        twice inside it with different content)."""
        u = self.users()
        region = {self.visible(r, c) for r in range(r0, r1) for c in range(c0, c1)}
        done = {}; conflicts = []
        for r in range(r0, r1):
            for c in range(c0, c1):
                key = self.visible(r, c)
                if key not in self.cells: continue
                name, t, fx, fy, p = self.cells[key]
                block = tuple(tuple(g[(r - r0) * 8 + j][(c - c0) * 8 + i] for i in range(8)) for j in range(8))
                if fx: block = tuple(tuple(reversed(row)) for row in block)
                if fy: block = tuple(reversed(block))
                outside = [x for x in u[(name, t)] if x not in region]
                if outside and not allow_shared:
                    if block != tuple(tuple(row) for row in self._tile(name, t)):
                        conflicts.append(((r, c), name, t, 'shared with ' + str(outside[:3])))
                    continue
                if (name, t) in done and done[(name, t)] != block:
                    conflicts.append(((r, c), name, t, 'used twice in region'))
                    continue
                done[(name, t)] = block
                sh = self.sheets[name][0]; x0, y0 = self.tile_xy(name, t)
                for j in range(8):
                    for i in range(8):
                        sh.put(x0 + i, y0 + j, block[j][i])
        return conflicts

    def _tile(self, name, t):
        sh = self.sheets[name][0]; x0, y0 = self.tile_xy(name, t)
        return [[sh.get(x0 + i, y0 + j) for i in range(8)] for j in range(8)]

    def render(self, sheets_override=None):
        """Recompose the 160x144 BG from the sheets (to preview edits)."""
        from PIL import Image
        im = Image.new('RGB', (160, 144))
        for r in range(18):
            for c in range(20):
                key = self.visible(r, c)
                if key not in self.cells:
                    im.paste(self.image.crop((c * 8, r * 8, c * 8 + 8, r * 8 + 8)), (c * 8, r * 8)); continue
                v = self.read(r, c); p = self.cells[key][4]
                for j in range(8):
                    for i in range(8):
                        im.putpixel((c * 8 + i, r * 8 + j), self.pal[p * 4 + v[j][i]])
        return im
