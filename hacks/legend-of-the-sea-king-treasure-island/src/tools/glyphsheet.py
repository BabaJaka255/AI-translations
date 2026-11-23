import numpy as np, sys
from PIL import Image, ImageDraw
glyphs = np.load('view/glyphs.npy')
def sheet(start, n, path, cols=16, S=3):
    W = cols * (16 * S + 4); rows = (n + cols - 1) // cols
    im = Image.new('RGB', (W, rows * (16 * S + 14)), (255, 255, 255)); dr = ImageDraw.Draw(im)
    for k in range(n):
        g = glyphs[start + k]; a = np.where(g >= 5, 0, np.where(g > 0, 170, 255)).astype(np.uint8)
        gi = Image.fromarray(a).resize((16 * S, 16 * S), Image.NEAREST)
        x = (k % cols) * (16 * S + 4); y = (k // cols) * (16 * S + 14)
        im.paste(gi, (x, y + 12)); dr.text((x, y), str(start + k), fill=(255, 0, 0))
    im.save(path)
sheet(int(sys.argv[1]), int(sys.argv[2]), sys.argv[3])
