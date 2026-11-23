import numpy as np, sys
sys.path.insert(0, 'tools')
from table import T
from PIL import Image, ImageDraw, ImageFont
g = np.load('view/glyphs.npy')
F = ImageFont.truetype('/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf', 40)
a, b, out = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
cols = 10; S = 3; cw = 16 * S + 48 + 8; ch = 16 * S + 14
n = b - a; rows = (n + cols - 1) // cols
im = Image.new('RGB', (cols * cw, rows * ch), 'white'); dr = ImageDraw.Draw(im)
for k in range(n):
    i = a + k; x = (k % cols) * cw; y = (k // cols) * ch
    arr = np.where(g[i] >= 5, 0, np.where(g[i] > 0, 200, 255)).astype(np.uint8)
    im.paste(Image.fromarray(arr).resize((16 * S, 16 * S), Image.NEAREST), (x, y + 12))
    dr.text((x, y), str(i), fill='red')
    t = T.get(i, '?')
    dr.text((x + 16 * S + 2, y + 12), t[:1], font=F, fill=(0, 0, 200))
im.save(out)
