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
