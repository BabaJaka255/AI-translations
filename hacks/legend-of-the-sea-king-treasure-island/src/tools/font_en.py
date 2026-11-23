"""Build the English VWF font: 94 glyphs (0x21-0x7E) as 16x16 4bpp cells in the game's gray palette.
Fill uses palette index 15 (white), anti-alias 10/12, drop shadow index 2 at (+1,+1)."""
import numpy as np
from PIL import Image, ImageDraw, ImageFont
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
SIZE = 11
BASELINE = 12        # pixel row of the baseline inside the 16px cell
SPACE_W = 4
def render(ch, font):
    im = Image.new('L', (24, 20)); d = ImageDraw.Draw(im)
    d.text((2, BASELINE), ch, font=font, fill=255, anchor='ls')
    return np.array(im)
def shadow(cell):
    sh = np.zeros_like(cell)
    sh[1:, 1:] = (cell[:-1, :-1] > 0) * 2
    return np.where(cell > 0, cell, sh)
_masks = None
def masks():
    """{code: (mask 16xW without shadow, advance)}"""
    global _masks
    if _masks is None:
        font = ImageFont.truetype(FONT, SIZE); _masks = {}
        for c in range(0x21, 0x7f):
            a = render(chr(c), font).astype(int)
            m = np.where(a >= 150, 15, np.where(a >= 90, 11, 0))
            cols = np.nonzero(m.max(0))[0]
            if len(cols) == 0: cols = np.array([2])
            g = m[:16, cols.min():cols.max() + 1]
            _masks[c] = (g, g.shape[1] + 1)
    return _masks
def advance(s):
    M = masks()
    return sum(SPACE_W if ch == ' ' else M[ord(ch)][1] for ch in s)
def compose(s):
    """16x16 cell holding the text s drawn with VWF spacing (advance(s) must be <= 16)"""
    M = masks(); cell = np.zeros((16, 24), int); x = 0
    for ch in s:
        if ch == ' ': x += SPACE_W; continue
        g, w = M[ord(ch)]
        cell[:g.shape[0], x:x + g.shape[1]] = np.maximum(cell[:g.shape[0], x:x + g.shape[1]], g); x += w
    return shadow(cell)[:, :16]
def build():
    font = ImageFont.truetype(FONT, SIZE)
    cells, widths = {}, {}
    for c in range(0x21, 0x7f):
        a = render(chr(c), font).astype(int)
        m = np.where(a >= 150, 15, np.where(a >= 90, 11, 0))
        cols = np.nonzero(m.max(0))[0]
        if len(cols) == 0: cols = np.array([2])
        x0, x1 = cols.min(), cols.max()
        g = m[:, x0:x1 + 1][:16]
        w = g.shape[1]
        cell = np.zeros((16, 16), int)
        cell[:g.shape[0], :w] = g
        sh = np.zeros_like(cell)
        sh[1:, 1:] = (cell[:-1, :-1] > 0) * 2
        cell = np.where(cell > 0, cell, sh)
        cells[c] = cell
        widths[c] = w + 1          # 1px gap (shadow column)
    return cells, widths
if __name__ == '__main__':
    cells, widths = build()
    lut = np.array([[i * 17] * 3 for i in range(16)], np.uint8); lut[0] = (40, 60, 120)
    s = 'The River King: A Quest for the Secret Waters! 0123 "quick" fox, jumps; (lazy) dog?'
    img = np.zeros((20, 8 + sum(widths.get(ord(c), SPACE_W) for c in s) + 16), int)
    x = 4
    for c in s:
        if c == ' ': x += SPACE_W; continue
        img[2:18, x:x + 16] = np.maximum(img[2:18, x:x + 16], cells[ord(c)]); x += widths[ord(c)]
    Image.fromarray(lut[img]).resize((img.shape[1] * 4, 80), Image.NEAREST).save('png/font_sample.png')
    print(widths)

# ---- tiny 3x5 caps for cramped labels: text '‹SINK|ER›' becomes one cell with two 5 px rows
TINY_FONT = dict(zip('ABCDEFGHIJKLMNOPQRSTUVWXYZ/&+-.', [
 '010101111101101', '110101110101110', '011100100100011', '110101101101110', '111100110100111',
 '111100110100100', '011100101101011', '101101111101101', '111010010010111', '001001001101010',
 '101101110101101', '100100100100111', '101111111101101', '110101101101101', '010101101101010',
 '110101110100100', '010101101111011', '110101110101101', '011100010001110', '111010010010010',
 '101101101101111', '101101101101010', '101101111111101', '101101010101101', '101101010010010',
 '111001010100111', '001001010100100', '010101010101011', '000010111010000', '000000111000000',
 '000000000000010']))
TINY = {}          # PUA char -> 'SINK|ER'
def tiny_char(spec):
    for k, v in TINY.items():
        if v == spec: return k
    k = chr(0xE000 + len(TINY)); TINY[k] = spec; return k
def tiny_cell(spec):
    cell = np.zeros((16, 16), int)
    for r, line in enumerate(spec.split('|')[:2]):
        y = 2 + 7 * r; x = 0
        for ch in line:
            if ch == ' ': x += 2; continue
            bits = TINY_FONT[ch]
            for yy in range(5):
                for xx in range(3):
                    if bits[yy * 3 + xx] == '1' and x + xx < 16: cell[y + yy, x + xx] = 15
            x += 4
    return shadow(cell)
_adv, _comp = advance, compose
def advance(s):
    return sum(16 if ch in TINY else _adv(ch) for ch in s)
def compose(s):
    if len(s) == 1 and s in TINY: return tiny_cell(TINY[s])
    return _comp(s)
