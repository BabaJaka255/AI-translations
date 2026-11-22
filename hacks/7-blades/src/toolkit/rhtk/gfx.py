"""Tile graphics: decode ROM bytes to indexed PNG sheets and encode them back.

Formats (8x8 tiles):
    1bpp        1 byte per row
    2bpp_gb     GB/GBC and SNES 2bpp: per row, plane0 byte then plane1 byte
    2bpp_nes    NES: 8 bytes plane0, then 8 bytes plane1
    4bpp_snes   SNES/PCE: planes 0+1 as 2bpp_gb (16 bytes), then planes 2+3 (16 bytes)
    4bpp_gba    GBA/NDS: linear, 2 pixels per byte, low nibble = left pixel
    4bpp_md     Mega Drive: linear, 2 pixels per byte, high nibble = left pixel
    8bpp        GBA/NDS 8bpp: 1 byte per pixel

Sheets are saved as palette-indexed PNGs so the pixel values are the exact
colour indices. Edit them in an editor that preserves indexed mode (Aseprite,
GraphicsGale, YY-CHR, GIMP with indexed mode), then reinsert.
"""
from __future__ import annotations

from PIL import Image

BPP = {"1bpp": 1, "2bpp_gb": 2, "2bpp_nes": 2, "4bpp_snes": 4, "4bpp_gba": 4,
       "4bpp_md": 4, "8bpp": 8}


def tile_bytes(fmt: str) -> int:
    return 8 * BPP[fmt]


def _planar_rows(data: bytes, planes_at) -> list[list[int]]:
    rows = []
    for y in range(8):
        row = []
        for x in range(8):
            bit = 7 - x
            v = 0
            for p, idx in enumerate(planes_at(y)):
                v |= ((data[idx] >> bit) & 1) << p
            row.append(v)
        rows.append(row)
    return rows


def decode_tile(data: bytes, fmt: str) -> list[list[int]]:
    if fmt == "1bpp":
        return _planar_rows(data, lambda y: [y])
    if fmt == "2bpp_gb":
        return _planar_rows(data, lambda y: [2 * y, 2 * y + 1])
    if fmt == "2bpp_nes":
        return _planar_rows(data, lambda y: [y, y + 8])
    if fmt == "4bpp_snes":
        return _planar_rows(data, lambda y: [2 * y, 2 * y + 1, 16 + 2 * y, 17 + 2 * y])
    if fmt in ("4bpp_gba", "4bpp_md"):
        rows = []
        for y in range(8):
            row = []
            for b in data[4 * y:4 * y + 4]:
                lo, hi = b & 0xF, b >> 4
                row += [lo, hi] if fmt == "4bpp_gba" else [hi, lo]
            rows.append(row)
        return rows
    if fmt == "8bpp":
        return [list(data[8 * y:8 * y + 8]) for y in range(8)]
    raise ValueError(f"unknown tile format {fmt!r}; choose from {', '.join(BPP)}")


def encode_tile(rows: list[list[int]], fmt: str) -> bytes:
    bpp = BPP[fmt]
    out = bytearray(tile_bytes(fmt))
    for y, row in enumerate(rows):
        for x, v in enumerate(row):
            if v >= 1 << bpp:
                raise ValueError(f"pixel value {v} too large for {fmt}")
            bit = 7 - x
            if fmt == "1bpp":
                out[y] |= (v & 1) << bit
            elif fmt == "2bpp_gb":
                out[2 * y] |= (v & 1) << bit
                out[2 * y + 1] |= ((v >> 1) & 1) << bit
            elif fmt == "2bpp_nes":
                out[y] |= (v & 1) << bit
                out[y + 8] |= ((v >> 1) & 1) << bit
            elif fmt == "4bpp_snes":
                for p, idx in enumerate((2 * y, 2 * y + 1, 16 + 2 * y, 17 + 2 * y)):
                    out[idx] |= ((v >> p) & 1) << bit
            elif fmt in ("4bpp_gba", "4bpp_md"):
                left_low = fmt == "4bpp_gba"
                shift = (0 if x % 2 == 0 else 4) if left_low else (4 if x % 2 == 0 else 0)
                out[4 * y + x // 2] |= v << shift
            elif fmt == "8bpp":
                out[8 * y + x] = v
    return bytes(out)


def grayscale_palette(bpp: int) -> list[tuple[int, int, int]]:
    n = 1 << bpp
    return [(255 - i * 255 // (n - 1),) * 3 for i in range(n)]


def read_palette_bgr555(data: bytes, offset: int, count: int) -> list[tuple[int, int, int]]:
    """SNES/GBA/NDS 15-bit colour, little endian."""
    pal = []
    for i in range(count):
        c = int.from_bytes(data[offset + 2 * i:offset + 2 * i + 2], "little")
        pal.append(tuple(((c >> s) & 0x1F) * 255 // 31 for s in (0, 5, 10)))
    return pal


ORDERS = ("linear", "obj8x16")


def tile_pos(t: int, width_tiles: int, order: str = "linear") -> tuple[int, int]:
    """Pixel position of tile t on a sheet.

    linear   tiles left to right, then down.
    obj8x16  GB/GBC 8x16 sprites: tile pairs (2k, 2k+1) stacked as one 8x16
             cell, cells left to right, so 16x16 sprite art stays whole.
    """
    if order == "linear":
        return (t % width_tiles) * 8, (t // width_tiles) * 8
    if order == "obj8x16":
        cell = t // 2
        return (cell % width_tiles) * 8, (cell // width_tiles) * 16 + (t % 2) * 8
    raise ValueError(f"unknown sheet order {order!r}; choose from {', '.join(ORDERS)}")


def sheet_size(count: int, width_tiles: int, order: str = "linear") -> tuple[int, int]:
    if order == "obj8x16":
        return width_tiles * 8, -(-count // (2 * width_tiles)) * 16
    return width_tiles * 8, -(-count // width_tiles) * 8


def rip(data: bytes, offset: int, count: int, fmt: str, width_tiles: int = 16,
        palette: list[tuple[int, int, int]] | None = None, order: str = "linear",
        tile_palettes: list[int] | None = None) -> Image.Image:
    """Tiles -> indexed sheet.

    `palette` may hold several sub-palettes back to back (e.g. 8 x 4 colours
    for GBC). `tile_palettes[t]` picks the sub-palette for tile t, and the
    pixel index becomes sub * colours + value, so each tile shows in its real
    colours. `pack` keeps only the low bits, so the sub-palette is cosmetic.
    """
    tb = tile_bytes(fmt)
    ncol = 1 << BPP[fmt]
    count = min(count, (len(data) - offset) // tb)
    img = Image.new("P", sheet_size(count, width_tiles, order), 0)
    pal = palette or grayscale_palette(BPP[fmt])
    flat = [c for rgb in pal[:256] for c in rgb]
    img.putpalette(flat + [0] * (768 - len(flat)))
    px = img.load()
    for t in range(count):
        tile = decode_tile(data[offset + t * tb:offset + (t + 1) * tb], fmt)
        base = (tile_palettes[t] if tile_palettes and t < len(tile_palettes) else 0) * ncol
        ox, oy = tile_pos(t, width_tiles, order)
        for y in range(8):
            for x in range(8):
                px[ox + x, oy + y] = base + tile[y][x]
    return img


def pack(img: Image.Image, fmt: str, count: int | None = None, order: str = "linear") -> bytes:
    """Indexed sheet -> tiles. Pixel values are taken modulo the format's colour
    count, so a sheet using several sub-palettes (see `rip`) packs correctly."""
    if img.mode != "P":
        raise ValueError("sheet must be a palette-indexed PNG so pixel values are colour indices; "
                         "re-export it in indexed mode")
    w, h = img.size
    wt = w // 8
    if count is None:
        count = int(img.info.get("rhtk_tiles", 0)) or (wt * (h // 8))
    mask = (1 << BPP[fmt]) - 1
    px = img.load()
    out = bytearray()
    for t in range(count):
        ox, oy = tile_pos(t, wt, order)
        out += encode_tile([[px[ox + x, oy + y] & mask for x in range(8)] for y in range(8)], fmt)
    return bytes(out)
