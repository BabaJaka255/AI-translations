"""Minimal GS local-memory model (swizzled CT32/CT16/PSMT8/PSMT4 writes and reads), after PCSX2 GSTables.
Used to view rh2 textures whichever way they are uploaded (native or the CT32 trick)."""
import numpy as np

BT32 = [[0, 1, 4, 5, 16, 17, 20, 21], [2, 3, 6, 7, 18, 19, 22, 23], [8, 9, 12, 13, 24, 25, 28, 29], [10, 11, 14, 15, 26, 27, 30, 31]]
CT32 = [[0, 1, 4, 5, 8, 9, 12, 13], [2, 3, 6, 7, 10, 11, 14, 15]]
BT16 = [[0, 2, 8, 10], [1, 3, 9, 11], [4, 6, 12, 14], [5, 7, 13, 15], [16, 18, 24, 26], [17, 19, 25, 27], [20, 22, 28, 30], [21, 23, 29, 31]]
CT16 = [[0, 2, 8, 10, 16, 18, 24, 26, 1, 3, 9, 11, 17, 19, 25, 27], [4, 6, 12, 14, 20, 22, 28, 30, 5, 7, 13, 15, 21, 23, 29, 31]]
BT8 = BT32
_c8 = [[0, 4, 16, 20, 32, 36, 48, 52, 2, 6, 18, 22, 34, 38, 50, 54], [8, 12, 24, 28, 40, 44, 56, 60, 10, 14, 26, 30, 42, 46, 58, 62],
       [33, 37, 49, 53, 1, 5, 17, 21, 35, 39, 51, 55, 3, 7, 19, 23], [41, 45, 57, 61, 9, 13, 25, 29, 43, 47, 59, 63, 11, 15, 27, 31],
       [96, 100, 112, 116, 64, 68, 80, 84, 98, 102, 114, 118, 66, 70, 82, 86], [104, 108, 120, 124, 72, 76, 88, 92, 106, 110, 122, 126, 74, 78, 90, 94],
       [65, 69, 81, 85, 97, 101, 113, 117, 67, 71, 83, 87, 99, 103, 115, 119], [73, 77, 89, 93, 105, 109, 121, 125, 75, 79, 91, 95, 107, 111, 123, 127]]
CT8 = _c8 + [[v + 128 for v in r] for r in _c8]
BT4 = [[0, 2, 8, 10], [1, 3, 9, 11], [4, 6, 12, 14], [5, 7, 13, 15], [16, 18, 24, 26], [17, 19, 25, 27], [20, 22, 28, 30], [21, 23, 29, 31]]
_c4 = [[0, 8, 32, 40, 64, 72, 96, 104, 2, 10, 34, 42, 66, 74, 98, 106, 4, 12, 36, 44, 68, 76, 100, 108, 6, 14, 38, 46, 70, 78, 102, 110],
       [16, 24, 48, 56, 80, 88, 112, 120, 18, 26, 50, 58, 82, 90, 114, 122, 20, 28, 52, 60, 84, 92, 116, 124, 22, 30, 54, 62, 86, 94, 118, 126],
       [65, 73, 97, 105, 1, 9, 33, 41, 67, 75, 99, 107, 3, 11, 35, 43, 69, 77, 101, 109, 5, 13, 37, 45, 71, 79, 103, 111, 7, 15, 39, 47],
       [81, 89, 113, 121, 17, 25, 49, 57, 83, 91, 115, 123, 19, 27, 51, 59, 85, 93, 117, 125, 21, 29, 53, 61, 87, 95, 119, 127, 23, 31, 55, 63],
       [192, 200, 224, 232, 128, 136, 160, 168, 194, 202, 226, 234, 130, 138, 162, 170, 196, 204, 228, 236, 132, 140, 164, 172, 198, 206, 230, 238, 134, 142, 166, 174],
       [208, 216, 240, 248, 144, 152, 176, 184, 210, 218, 242, 250, 146, 154, 178, 186, 212, 220, 244, 252, 148, 156, 180, 188, 214, 222, 246, 254, 150, 158, 182, 190],
       [129, 137, 161, 169, 193, 201, 225, 233, 131, 139, 163, 171, 195, 203, 227, 235, 133, 141, 165, 173, 197, 205, 229, 237, 135, 143, 167, 175, 199, 207, 231, 239],
       [145, 153, 177, 185, 209, 217, 241, 249, 147, 155, 179, 187, 211, 219, 243, 251, 149, 157, 181, 189, 213, 221, 245, 253, 151, 159, 183, 191, 215, 223, 247, 255]]
CT4 = _c4 + [[v + 256 for v in r] for r in _c4]
_BT32, _CT32, _BT16, _CT16, _BT8, _CT8, _BT4, _CT4 = map(np.array, (BT32, CT32, BT16, CT16, BT8, CT8, BT4, CT4))
MEM = 4 << 20


def addr(psm, bp, bw, x, y):
    """element address in units of the format (word/halfword/byte/nibble). bp in 256-byte blocks, bw in 64 px."""
    x = np.asarray(x); y = np.asarray(y)
    if psm == 0:
        page = (y // 32) * bw + x // 64; blk = _BT32[(y % 32) // 8, (x % 64) // 8]
        return ((bp + page * 32 + blk) * 64 + ((y % 8) // 2) * 16 + _CT32[y % 2, x % 8]) % (MEM // 4)
    if psm == 2:
        page = (y // 64) * bw + x // 64; blk = _BT16[(y % 64) // 8, (x % 64) // 16]
        return ((bp + page * 32 + blk) * 128 + ((y % 8) // 2) * 32 + _CT16[y % 2, x % 16]) % (MEM // 2)
    if psm == 0x13:
        page = (y // 64) * (bw // 2) + x // 128; blk = _BT8[(y % 64) // 16, (x % 128) // 16]
        return ((bp + page * 32 + blk) * 256 + _CT8[y % 16, x % 16]) % MEM
    if psm == 0x14:
        page = (y // 128) * (bw // 2) + x // 128; blk = _BT4[(y % 128) // 16, (x % 128) // 32]
        return ((bp + page * 32 + blk) * 512 + _CT4[y % 16, x % 32]) % (MEM * 2)
    raise ValueError('psm %x' % psm)


class GS:
    def __init__(self): self.m = np.zeros(MEM, np.uint8)

    def write(self, psm, bp, bw, x0, y0, w, h, data):
        yy, xx = np.mgrid[y0:y0 + h, x0:x0 + w]; a = addr(psm, bp, bw, xx, yy).ravel()
        if psm == 0:
            v = self.m.view(np.uint32); v[a] = np.frombuffer(data, np.uint32)[:w * h]
        elif psm == 2:
            v = self.m.view(np.uint16); v[a] = np.frombuffer(data, np.uint16)[:w * h]
        elif psm == 0x13:
            self.m[a] = np.frombuffer(data, np.uint8)[:w * h]
        elif psm == 0x14:
            b = np.frombuffer(data, np.uint8)[:w * h // 2]; n = np.stack([b & 15, b >> 4], 1).ravel()
            for h in (0, 1):   # one pass per nibble so no byte is written twice in one assignment
                sel = (a & 1) == h; byte = a[sel] >> 1; v = n[sel]
                self.m[byte] = (self.m[byte] & 15) | (v << 4) if h else (self.m[byte] & 0xf0) | v

    def read(self, psm, bp, bw, w, h):
        yy, xx = np.mgrid[0:h, 0:w]; a = addr(psm, bp, bw, xx, yy)
        if psm == 0: return self.m.view(np.uint32)[a]
        if psm == 2: return self.m.view(np.uint16)[a]
        if psm == 0x13: return self.m[a]
        if psm == 0x14: return (self.m[a >> 1] >> ((a & 1) * 4)) & 15

    def clut(self, cpsm, cbp, n):
        """CSM1 palette as 32-bit RGBA (alpha 0-128)."""
        if n == 256:
            c = self.read(cpsm, cbp, 1, 16, 16).ravel().copy().reshape(-1, 32)
            c[:, 8:16], c[:, 16:24] = c[:, 16:24].copy(), c[:, 8:16].copy(); c = c.ravel()
        else:
            c = self.read(cpsm, cbp, 1, 8, 2).ravel()
        c = c.astype(np.uint32)
        if cpsm == 2:
            a = np.where((c >> 15) | (c & 0x7fff) > 0, 0x80, 0).astype(np.uint32)   # TEXA as AEM=1, TA0=TA1=0x80
            c = ((c & 31) << 3) | (((c >> 5) & 31) << 11) | (((c >> 10) & 31) << 19) | (a << 24)
        return c
