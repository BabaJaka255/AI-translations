"""Edit ripped art sheets (gfx/orig/art) and write them to gfx/edit/art.

A sheet is an indexed PNG: pixel index = sub_palette * 4 + value. The build
stores only the value (0-3), so painting keeps each tile's sub-palette and
changes the value.
"""
import os
from PIL import Image
from PIL.PngImagePlugin import PngInfo

G = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
ORIG = os.path.join(G, 'gfx/orig/art')
EDIT = os.path.join(G, 'gfx/edit/art')

class Sheet:
    def __init__(self, name):
        self.name = name
        self.img = Image.open(os.path.join(ORIG, name + '.png'))
        self.img.load()
        self.tiles = self.img.info.get('rhtk_tiles')
        self.w, self.h = self.img.size
        self.order = 'linear'
        try:
            import json
            for g in json.load(open(os.path.join(G, 'project.json')))['gfx']:
                if g['name'] == name: self.order = g.get('order', 'linear')
        except Exception:
            pass

    def get(self, x, y):
        return self.img.getpixel((x, y)) % 4

    def sub(self, x, y):
        return self.img.getpixel((x, y)) // 4

    def put(self, x, y, v, sub=None):
        if 0 <= x < self.w and 0 <= y < self.h:
            s = self.sub(x, y) if sub is None else sub
            self.img.putpixel((x, y), s * 4 + v)

    def fill(self, x0, y0, x1, y1, v):
        """Fill the box [x0,x1) x [y0,y1) with value v."""
        for y in range(y0, y1):
            for x in range(x0, x1):
                self.put(x, y, v)

    def replace(self, x0, y0, x1, y1, old, new):
        for y in range(y0, y1):
            for x in range(x0, x1):
                if self.get(x, y) in old:
                    self.put(x, y, new)

    def paint(self, mask, x0, y0, v, clip=None):
        """Paint mask (rows of 0/1) at (x0, y0) with value v (an int, or a
        function (x, y) -> value). clip(x, y) -> bool limits where ink goes."""
        for j, row in enumerate(mask):
            for i, m in enumerate(row):
                if m:
                    x, y = x0 + i, y0 + j
                    if clip and not clip(x, y):
                        continue
                    self.put(x, y, v(x, y) if callable(v) else v)

    def save(self):
        os.makedirs(EDIT, exist_ok=True)
        info = PngInfo()
        if self.tiles:
            info.add_text('rhtk_tiles', str(self.tiles))
        self.img.save(os.path.join(EDIT, self.name + '.png'), pnginfo=info)

def shift(mask, dx, dy):
    h, w = len(mask), len(mask[0])
    out = [[0] * (w + abs(dx)) for _ in range(h + abs(dy))]
    for j in range(h):
        for i in range(w):
            if mask[j][i]:
                out[j + max(dy, 0)][i + max(dx, 0)] = 1
    return out

def styled(sheet, mask, x0, y0, fill, shadow=None, outline=None, sdx=1, sdy=1, clip=None):
    """Paint a word with an optional outline (1px all round) and drop shadow,
    then the fill on top. Values are ints or functions (x, y) -> value."""
    import letter
    if outline is not None:
        sheet.paint(letter.dilate(mask, 1), x0 - 1, y0 - 1, outline, clip)
    if shadow is not None:
        base = letter.dilate(mask, 1) if outline is not None else mask
        ox = x0 - 1 if outline is not None else x0
        oy = y0 - 1 if outline is not None else y0
        sheet.paint(base, ox + sdx, oy + sdy, shadow, clip)
        if outline is not None:
            sheet.paint(letter.dilate(mask, 1), x0 - 1, y0 - 1, outline, clip)
    sheet.paint(mask, x0, y0, fill, clip)
