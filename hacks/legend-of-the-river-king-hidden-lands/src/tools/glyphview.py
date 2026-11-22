import sys
sys.path.insert(0, 'tools')
from PIL import Image, ImageDraw
pages = [Image.open(f'png/COMM.TIM_{p}.png').convert('RGB') for p in range(1, 6)]
def glyph(i):
    p, r = divmod(i, 256); y, x = divmod(r, 16)
    return pages[p].crop((x * 16, y * 16, x * 16 + 16, y * 16 + 16))
if __name__ == '__main__':
    ids = list(range(int(sys.argv[2]), int(sys.argv[3])))
    cols = 10; sc = 5
    s = Image.new('RGB', (cols * 90, ((len(ids) + cols - 1) // cols) * 100), (255, 255, 255))
    d = ImageDraw.Draw(s)
    for k, i in enumerate(ids):
        x, y = (k % cols) * 90, (k // cols) * 100
        s.paste(glyph(i).resize((16 * sc, 16 * sc), Image.NEAREST), (x + 5, y + 18))
        d.text((x + 5, y + 2), str(i), fill=(0, 0, 0))
    s.save(sys.argv[1])
