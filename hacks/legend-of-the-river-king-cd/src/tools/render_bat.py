"""Render the BG layer from a savestate. usage: render_bat.py state out.png [x0 y0 w h] (tiles)"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from mdfnstate import parse
from PIL import Image
def tile_pixels(v, t):
    o = t * 32; px = []
    for y in range(8):
        p0, p1 = v[o + y * 2], v[o + y * 2 + 1]; p2, p3 = v[o + 16 + y * 2], v[o + 16 + y * 2 + 1]
        px.append([((p0 >> (7 - x)) & 1) | ((p1 >> (7 - x)) & 1) << 1 | ((p2 >> (7 - x)) & 1) << 2 | ((p3 >> (7 - x)) & 1) << 3 for x in range(8)])
    return px
def render(st, x0=0, y0=0, w=32, h=30, mark=False):
    s = parse(st); v = s['VDC0']['VRAM'][1]; ct = s['VCE']['color_table'][1]
    mwr = int.from_bytes(s['VDC0']['MWR'][1], 'little'); W = (32, 64, 128, 128)[(mwr >> 4) & 3]
    def col(i):
        c = ct[i * 2] | ct[i * 2 + 1] << 8
        return (((c >> 3) & 7) * 36, ((c >> 6) & 7) * 36, (c & 7) * 36)
    im = Image.new('RGB', (w * 8, h * 8)); px = im.load()
    for ty in range(h):
        for tx in range(w):
            e = v[((y0 + ty) * W + x0 + tx) * 2] | v[((y0 + ty) * W + x0 + tx) * 2 + 1] << 8
            t = e & 0x7FF; pal = e >> 12; tp = tile_pixels(v, t)
            for y in range(8):
                for x in range(8):
                    c = tp[y][x]; px[tx * 8 + x, ty * 8 + y] = col(pal * 16 + c if c else 0)
    return im
if __name__ == '__main__':
    a = [int(x) for x in sys.argv[3:7]] if len(sys.argv) > 6 else [0, 0, 32, 30]
    im = render(open(sys.argv[1], 'rb').read(), *a); im.resize((im.width * 3, im.height * 3), Image.NEAREST).save(sys.argv[2])
