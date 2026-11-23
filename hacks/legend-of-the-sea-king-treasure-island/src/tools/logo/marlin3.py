"""The original marlin, reconstructed. Every pixel of the fish the Japanese logo shows is kept exactly where it was:
tail, belly stripe and fins, sail, head, bill. Only what 海の covered is painted in: the body between tail and head,
the foot of the sail and the stretch of the upper tail lobe behind 海's shadow."""
import numpy as np, cv2
from PIL import Image
from scipy import ndimage as ndi
from scipy.interpolate import PchipInterpolator
from eng import W, H, SS, Canvas, show

ORIG = np.array(Image.open('title_logo_only_original.png').convert('RGBA'))

# back and belly lines of the hidden body (band coords). The belly follows the white stripe that shows under 海の,
# the back joins the top of the head where the sail stands.
TOP = [(26, 52.0), (30, 46.5), (35, 40.0), (41, 33.5), (48, 28.0), (56, 23.5), (64, 20.2), (72, 18.2), (80, 17.4), (90, 19.5)]
BOT = [(26, 57.6), (32, 56.0), (40, 54.0), (50, 51.5), (58, 49.5), (68, 47.0), (78, 44.2), (86, 40.5), (90, 36.0)]


def kanji_mask():
    """where 海の and its black 3D side sit"""
    yy, xx = np.mgrid[0:H, 0:W]
    c = ORIG[..., :3].astype(int); R, G, B = c[..., 0], c[..., 1], c[..., 2]
    no = (((xx - 59.0) / 18.5) ** 2 + ((yy - 30.5) / 18.5) ** 2 <= 1) | (((xx - 62.0) / 18.5) ** 2 + ((yy - 33.5) / 18.5) ** 2 <= 1)
    umi = (xx >= 5) & (xx <= 45) & (yy >= 11) & (yy <= 52)
    zone = no | umi
    dark = (c.max(-1) < 80) & (B <= R + 24)                       # black / brown side faces
    grey = (np.abs(R - G) < 24) & (np.abs(G - B) < 28) & (c.max(-1) < 170) & (c.max(-1) >= 80)
    cyan = (B >= 190) & (G >= 150) & (B >= R) & ~((yy >= 44) & (R > 225))    # the white belly stripe is the fish's
    side = (xx >= 72) & (xx <= 85) & (yy >= 18) & (yy <= 50) & (R >= G) & (R - B >= 8) & (c.max(-1) < 170)   # lit side face of の
    teal = (G > R + 30) & (G >= B - 40) & (B < 200)                # the teal fringe pixels round the kanji
    m = (zone & ((yy < 44) | dark | grey | cyan | teal)) | side
    m &= ~((yy <= 16) & (xx >= 62))                               # the sail stands clear of の up here
    return m


def original_fish():
    """bool mask of the original fish pixels to keep"""
    a = ORIG; c = a[..., :3].astype(int); R, G, B = c[..., 0], c[..., 1], c[..., 2]
    yy, xx = np.mgrid[0:H, 0:W]
    keep = (a[..., 3] > 0) & (xx <= 126) & (yy <= 86)
    warm = (R > 150) & (B < 150) & (R > B + 50)                   # ぬ and し
    keep &= ~warm
    keep &= ~ndi.binary_dilation(warm, iterations=2) | (B > R + 30) | ((c.min(-1) > 150) & (yy < 60))
    keep &= ~kanji_mask()
    keep &= ~((yy > 36) & (xx > 60) & (G > R + 30) & (G > B - 30))    # stray teal fringe below the head
    keep &= ~((yy > 58) & (xx > 36))                              # shadow pixels of ぬ
    keep &= ~((yy > 50) & (xx > 62))                              # glints of ぬ and し
    keep &= ~((c.max(-1) < 60) & (B <= R + 24))                    # leftover black of the 3D sides
    keep &= ~((yy > 40) & (R > B + 50))                           # red fringe of ぬ
    keep &= ~((yy >= 43) & (yy <= 46) & (xx >= 36) & (xx <= 58))     # specks of 海's shadow above the belly stripe
    lab, n = ndi.label(keep, np.ones((3, 3), int))
    sizes = ndi.sum(keep, lab, range(1, n + 1))
    return np.isin(lab, [i + 1 for i, s in enumerate(sizes) if s >= 4])


def body():
    """RGBA float layer of the painted body, drawn at 8x and averaged down"""
    hh, ww = H * SS, W * SS
    yy, xx = np.mgrid[0:hh, 0:ww].astype(np.float32)
    x = xx / SS; y = yy / SS
    top = PchipInterpolator([p[0] for p in TOP], [p[1] for p in TOP]); bot = PchipInterpolator([p[0] for p in BOT], [p[1] for p in BOT])
    xc = np.clip(x, 26, 90)
    T = top(xc).astype(np.float32); B = bot(xc).astype(np.float32)
    inside = (x >= 26) & (x <= 90) & (y >= T) & (y <= B)
    u = np.clip((y - T) / np.maximum(B - T, 0.5), 0, 1)
    rng = np.random.default_rng(4)
    u = np.clip(u + np.kron(rng.normal(0, 0.022, (H, W)), np.ones((SS, SS))).astype(np.float32), 0, 1)
    tailward = np.clip((70 - x) / 44, 0, 1)                         # 0 at the head, 1 at the tail
    stops = [(0.00, (48, 40, 104)), (0.05, (64, 48, 112)), (0.12, (96, 56, 128)), (0.27, (104, 64, 136)), (0.33, (152, 88, 144)),
             (0.38, (200, 184, 192)), (0.43, (248, 248, 248)), (0.50, (248, 248, 248)), (0.535, (176, 160, 176)), (0.56, (104, 88, 112)),
             (0.585, (200, 184, 192)), (0.63, (248, 248, 248)), (0.71, (248, 248, 248)), (0.745, (176, 160, 176)), (0.77, (96, 56, 128)),
             (0.80, (200, 184, 192)), (0.85, (248, 248, 248)), (0.95, (248, 248, 248)), (1.0, (200, 184, 192))]
    xs = [s[0] for s in stops]
    col = np.zeros((hh, ww, 3), np.float32)
    for k in range(3): col[..., k] = np.interp(u, xs, [s[1][k] for s in stops])
    navy = np.array((24, 24, 96), np.float32)
    w = (tailward * 0.75 * (u < 0.36))[..., None]                   # the purple back deepens to navy toward the tail
    col = col * (1 - w) + navy * w
    # the streak lines break up and fade toward the tail, as they do on the head
    fade = (np.clip((tailward - 0.35) / 0.5, 0, 1) * ((u > 0.5) & (u < 0.8)))[..., None]
    col = col * (1 - fade) + np.array((244, 244, 248), np.float32) * fade
    pre = np.dstack([col * inside[..., None], inside.astype(np.float32)])
    small = pre.reshape(H, SS, W, SS, 4).mean((1, 3))
    al = small[..., 3]
    out = np.zeros((H, W, 4)); out[..., :3] = small[..., :3] / np.maximum(al[..., None], 1e-4); out[..., 3] = np.where(al >= 0.5, 255, 0)
    return out


def extras(lay):
    """the bits of fin that 海の hid: foot of the sail, upper tail lobe"""
    def put(pts, col):
        m = np.zeros((H * SS, W * SS), np.uint8)
        cv2.fillPoly(m, [np.round(np.array(pts, float) * SS).astype(np.int32)], 255)
        cov = m.reshape(H, SS, W, SS).mean((1, 3)) / 255
        sel = cov >= 0.5
        lay[sel, :3] = col; lay[sel, 3] = 255
    # sail: its rear edge runs straight down at x = 64..65; carry the rays down to the back
    put([(64.2, 15.5), (72, 15.5), (78, 18.5), (64.2, 21.5)], (104, 88, 112))
    for x0, col in ((65.2, (152, 152, 160)), (67.2, (200, 248, 248)), (69.4, (96, 56, 128)), (71.4, (192, 208, 216)), (73.6, (152, 88, 144))):
        put([(x0, 15.5), (x0 + 1.1, 15.5), (x0 + 3.4, 20.5), (x0 + 2.3, 20.5)], col)
    # upper tail lobe from where it shows at the far left to the tail root
    put([(8, 46.2), (14, 47.6), (20, 49.6), (25, 51.6), (24, 54.0), (18, 52.0), (12, 49.6), (8, 48.2)], (0, 0, 72))
    put([(12, 48.0), (18, 50.0), (23, 52.0), (18, 51.0)], (0, 24, 96))


def marlin(dx=0, dy=0):
    """RGBA float layer in band coords"""
    lay = body()
    extras(lay)
    keep = original_fish()
    lay[keep] = ORIG[keep].astype(float)
    out = np.zeros_like(lay)
    h, w = lay.shape[:2]
    out[max(0, dy):min(h, h + dy), max(0, dx):min(w, w + dx)] = lay[max(0, -dy):h - max(0, dy), max(0, -dx):w - max(0, dx)]
    return out


if __name__ == '__main__':
    from marlin import paste_layer
    cv = Canvas(); paste_layer(cv, marlin())
    show(cv, 'v_marlin3.png', 8, box=(0, 0, 130, 88), bg=(40, 90, 90))
    cv = Canvas(); k = original_fish(); cv.put(k, ORIG[..., :3].astype(float))
    show(cv, 'v_marlin3_orig.png', 8, box=(0, 0, 130, 88), bg=(40, 90, 90))
