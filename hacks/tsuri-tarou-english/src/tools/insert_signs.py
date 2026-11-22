"""Insert the English spot sign text (text/signs_en.txt) into an expanded ROM.
The sign reader $01:E099 has one LDA $01:xxxx,X per spot (operands at $01:E0E8 + 6*n); those are repointed to bank $20.
Each of the 5 lines is drawn from col 7 of rows 14,16,...,22 on a text-only BG layer, so a line can run onto the row
below by padding to 32 tiles with blank FF: the VRAM address wraps to col 7 of the next row."""
import os, sys, textwrap
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from build_font import ENC
SIGN_BASE = 0x100000          # ROM offset = $20:8000
WIDTH, ROWS = 21, 2
def load(path=os.path.join(HERE, '..', 'text', 'signs_en.txt')):
    spots = []
    for l in open(path, encoding='utf-8'):
        l = l.rstrip('\n')
        if l.startswith('## '): spots.append([])
        elif l and not l.startswith('#'): spots[-1].append(l)
    assert len(spots) == 15 and all(len(s) == 5 for s in spots), [len(s) for s in spots]
    return spots
def encode_line(t):
    rows = textwrap.wrap(t, WIDTH)
    if len(rows) > ROWS: raise ValueError('too long for %d rows of %d: %r' % (ROWS, WIDTH, t))
    out = b''
    for i, row in enumerate(rows):
        b = bytes(ENC[c] for c in row)
        out += b + (b'\xff' * (32 - len(b)) if i < len(rows) - 1 else b'')
    return out + b'\xf0'
def patch_signs(r, spots=None):
    spots = spots or load(); o = SIGN_BASE
    from insert_menus import sign_name_prefix
    for n, lines in enumerate(spots):
        blob = sign_name_prefix(n) + b''.join(encode_line(t) for t in lines)
        r[o:o + len(blob)] = blob
        bank, addr = 0x20 + (o - 0x100000) // 0x8000, 0x8000 | (o & 0x7FFF)
        assert (o & 0x7FFF) + len(blob) <= 0x8000, 'sign block crosses a bank'
        p = 0xE0E7 + 6 * n
        assert r[p] == 0xBF and r[p + 3] in (0x01, 0x20)
        r[p + 1:p + 4] = bytes([addr & 0xFF, addr >> 8, bank])
        o += len(blob)
    return o
if __name__ == '__main__':
    for n, lines in enumerate(load()):
        for t in lines:
            rows = textwrap.wrap(t, WIDTH); print('%2d %-23s | %s' % (n + 1, rows[0], rows[1] if len(rows) > 1 else ''))
