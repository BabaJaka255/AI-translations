"""Fune Tarou (SFC) helpers: addresses, text codec, font."""
import os, zlib

GAME = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROM_PATH = os.environ.get('FT_ROM', os.path.join(GAME, 'rom', 'Fune Tarou (Japan).sfc'))
ORIG_CRC = 0x5D6BA598
TEXT_BANK_OLD = 0xC1      # original string bank (ROM 0x10000-0x1FFFF)
TEXT_BANK_NEW = 0xE1      # English string bank (ROM 0x210000-0x21FFFF), a copy of C1 at first
NEW_TEXT = 0x210000       # ROM offset of bank E1

# control characters in strings (single bytes)
END, NL, MARK, SKIP = 0x2F, 0x5D, 0x5E, 0x7E   # '/', ']', '^', '~'
SLASH = 0x7F                                   # our code for a printed '/'
# extra glyphs in data/font_en.txt
SPECIAL = {'ō': 0x60, 'Ō': 0x7B, 'ū': 0x7C, '\u00a0': 0x5F}   # no-break space = blank that does not end a label


def hirom(off):
    """ROM offset -> SNES address in banks C0-FF."""
    return 0xC00000 | off


def load_rom():
    d = open(ROM_PATH, 'rb').read()
    assert zlib.crc32(d) == ORIG_CRC, 'wrong ROM: need Fune Tarou (Japan).sfc, CRC32 5D6BA598'
    return d


def decode_jp(b):
    """Original string bytes -> readable text. ']' becomes a newline; other controls stay as is."""
    out = []
    i = 0
    while i < len(b):
        c = b[i]
        if (0x81 <= c <= 0x9F or 0xE0 <= c <= 0xFC) and i + 1 < len(b):
            out.append(b[i:i + 2].decode('cp932', 'replace')); i += 2; continue
        if c == NL:
            out.append('\n')
        elif 0x20 <= c < 0x7F or 0xA1 <= c <= 0xDF:
            out.append(bytes([c]).decode('cp932'))
        else:
            out.append('{%02X}' % c)
        i += 1
    return ''.join(out)


def encode_en(s):
    """English text -> bytes. Newline -> ']', '/' -> 0x7F. '^', '~', '<', '>' pass through as controls."""
    out = bytearray()
    i = 0
    while i < len(s):
        ch = s[i]
        if ch == '{' and s[i + 3:i + 4] == '}':
            out.append(int(s[i + 1:i + 3], 16)); i += 4; continue
        if ch in SPECIAL:
            out.append(SPECIAL[ch])
        elif ch == '\n':
            out.append(NL)
        elif ch == '/':
            out.append(SLASH)
        elif ch in '<>':
            out.append(ord(ch))             # font switch: '>' compact, '<' tall (zero width)
        elif ch in '[\\]' or ord(ch) >= 0x7F:
            raise ValueError('cannot encode %r in %r' % (ch, s))
        else:
            out.append(ord(ch))
        i += 1
    return bytes(out)


def cols(s):
    """On-screen width of an English string in 8 px columns (longest line)."""
    best = 0
    for line in s.split('\n'):
        best = max(best, len(line.replace('^', '').replace('~', '').replace('<', '').replace('>', '')))
    return best


def load_font(path=None):
    """data/font_en.txt -> {code: 16 rows of 8-bit ints}."""
    path = path or os.path.join(GAME, 'data', 'font_en.txt')
    glyphs = {}
    lines = open(path, encoding='utf-8').read().split('\n')
    i = 0
    while i < len(lines):
        ln = lines[i]
        if ln and not ln.startswith('#') and len(ln) >= 2 and all(c in '0123456789ABCDEF' for c in ln[:2]) and (len(ln) == 2 or ln[2] == ' '):
            code = int(ln[:2], 16)
            rows = []
            for y in range(16):
                r = lines[i + 1 + y]
                assert len(r) == 8 and set(r) <= set('#.'), 'bad font row for %02X: %r' % (code, r)
                rows.append(int(r.replace('#', '1').replace('.', '0'), 2))
            glyphs[code] = rows
            i += 17
        else:
            i += 1
    return glyphs


def snes_checksum(rom):
    rom = bytearray(rom)
    rom[0xFFDC:0xFFE0] = b'\xff\xff\x00\x00'
    s = sum(rom) & 0xFFFF
    rom[0xFFDE] = s & 0xFF; rom[0xFFDF] = s >> 8
    c = s ^ 0xFFFF
    rom[0xFFDC] = c & 0xFF; rom[0xFFDD] = c >> 8
    return bytes(rom)
