"""eu_font (rh2, PSMT4 256x256 stored as CT32 64x128 transfer data) <-> 256x256 index image.
Adds PlayStation button glyphs (circle, cross, triangle, square) to the empty cells 0x9c-0x9f that PAL's
in-game renderer maps 0x819b/0x817e/0x81a2/0x81a0 to (they are blank in PAL's eu_font)."""
import numpy as np
CHUNKS = (0x230, 0x2290, 0x42f0, 0x6350)
BT32 = [[0, 1, 4, 5, 16, 17, 20, 21], [2, 3, 6, 7, 18, 19, 22, 23], [8, 9, 12, 13, 24, 25, 28, 29], [10, 11, 14, 15, 26, 27, 30, 31]]
CT32 = [[0, 1, 4, 5, 8, 9, 12, 13], [2, 3, 6, 7, 10, 11, 14, 15]]
BT4 = [[0, 2, 8, 10], [1, 3, 9, 11], [4, 6, 12, 14], [5, 7, 13, 15], [16, 18, 24, 26], [17, 19, 25, 27], [20, 22, 28, 30], [21, 23, 29, 31]]
C4 = [[0, 8, 32, 40, 64, 72, 96, 104, 2, 10, 34, 42, 66, 74, 98, 106, 4, 12, 36, 44, 68, 76, 100, 108, 6, 14, 38, 46, 70, 78, 102, 110],
      [16, 24, 48, 56, 80, 88, 112, 120, 18, 26, 50, 58, 82, 90, 114, 122, 20, 28, 52, 60, 84, 92, 116, 124, 22, 30, 54, 62, 86, 94, 118, 126],
      [65, 73, 97, 105, 1, 9, 33, 41, 67, 75, 99, 107, 3, 11, 35, 43, 69, 77, 101, 109, 5, 13, 37, 45, 71, 79, 103, 111, 7, 15, 39, 47],
      [81, 89, 113, 121, 17, 25, 49, 57, 83, 91, 115, 123, 19, 27, 51, 59, 85, 93, 117, 125, 21, 29, 53, 61, 87, 95, 119, 127, 23, 31, 55, 63],
      [192, 200, 224, 232, 128, 136, 160, 168, 194, 202, 226, 234, 130, 138, 162, 170, 196, 204, 228, 236, 132, 140, 164, 172, 198, 206, 230, 238, 134, 142, 166, 174],
      [208, 216, 240, 248, 144, 152, 176, 184, 210, 218, 242, 250, 146, 154, 178, 186, 212, 220, 244, 252, 148, 156, 180, 188, 214, 222, 246, 254, 150, 158, 182, 190],
      [129, 137, 161, 169, 193, 201, 225, 233, 131, 139, 163, 171, 195, 203, 227, 235, 133, 141, 165, 173, 197, 205, 229, 237, 135, 143, 167, 175, 199, 207, 231, 239],
      [145, 153, 177, 185, 209, 217, 241, 249, 147, 155, 179, 187, 211, 219, 243, 251, 149, 157, 181, 189, 213, 221, 245, 253, 151, 159, 183, 191, 215, 223, 247, 255]]
C4 = C4 + [[v + 256 for v in r] for r in C4]


def _a32(x, y):   # byte address of CT32 pixel (x, y), buffer width 64, base 0
    page = (y // 32) + (x // 64); blk = BT32[(y % 32) // 8][(x % 64) // 8]
    return ((page * 32 + blk) * 64 + ((y % 8) // 2) * 16 + CT32[y % 2][x % 8]) * 4


def _n4(x, y):    # nibble address of PSMT4 pixel (x, y), buffer width 256, base 0
    page = (y // 128) * 2 + (x // 128); blk = BT4[(y % 128) // 16][(x % 128) // 32]
    return (page * 32 + blk) * 512 + C4[y % 16][x % 32]


_A32 = np.array([[_a32(x, y) for x in range(64)] for y in range(128)]).ravel()
_N4 = np.array([[_n4(x, y) for x in range(256)] for y in range(256)])


def decode(rh2):
    data = np.frombuffer(b''.join(rh2[a:a + 0x2000] for a in CHUNKS), np.uint8)
    vram = np.zeros(0x8000, np.uint8)
    for k in range(4): vram[_A32 + k] = data[k::4]
    nib = np.stack([vram & 15, vram >> 4], 1).ravel()
    return nib[_N4]


def encode(rh2, img):
    nib = np.zeros(0x10000, np.uint8); nib[_N4] = img
    vram = (nib[0::2] | (nib[1::2] << 4)).astype(np.uint8)
    data = np.zeros(0x8000, np.uint8)
    for k in range(4): data[k::4] = vram[_A32 + k]
    out = bytearray(rh2); data = data.tobytes()
    for i, a in enumerate(CHUNKS): out[a:a + 0x2000] = data[i * 0x2000:(i + 1) * 0x2000]
    return bytes(out)


def button_glyphs():
    """16x16 index images: white (0) antialiased shape on transparent (15), like the letters (the
    renderer's shadow pass gives the dark edge)."""
    from PIL import Image, ImageDraw
    S = 8; out = []
    for kind in ('circle', 'cross', 'triangle', 'square'):
        im = Image.new('L', (16 * S, 16 * S), 0); d = ImageDraw.Draw(im); w = int(2.2 * S)
        if kind == 'circle': d.ellipse((3 * S, 3 * S, 13 * S, 13 * S), outline=255, width=w)
        elif kind == 'cross':
            d.line((3.5 * S, 3.5 * S, 12.5 * S, 12.5 * S), fill=255, width=w); d.line((12.5 * S, 3.5 * S, 3.5 * S, 12.5 * S), fill=255, width=w)
        elif kind == 'triangle': d.polygon((8 * S, 2.5 * S, 13.5 * S, 12.5 * S, 2.5 * S, 12.5 * S), outline=255, width=w)
        else: d.rectangle((3.5 * S, 3.5 * S, 12.5 * S, 12.5 * S), outline=255, width=w)
        fill = np.asarray(im.resize((16, 16), Image.BOX), float) / 255
        g = np.full((16, 16), 15, np.uint8)
        g[fill > 0.25] = np.clip(np.round(13 - fill[fill > 0.25] * 13), 0, 12).astype(np.uint8)
        out.append(g)
    return out


def with_buttons(rh2):
    img = decode(rh2).copy()
    for i, g in enumerate(button_glyphs()):   # cells 0x9c circle, 0x9d cross, 0x9e triangle, 0x9f square
        c = 0x9c + i; x, y = (c & 15) * 16, (c >> 4) * 16
        assert (img[y:y + 16, x:x + 16] == 15).all(), hex(c)
        img[y:y + 16, x:x + 16] = g
    return encode(rh2, img)
