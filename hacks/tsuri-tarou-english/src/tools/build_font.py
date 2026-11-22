"""English 8x8 font for Tsuri Tarou.
build_font.py IN.sfc OUT.sfc   writes data/en_font.txt glyphs into the main font (ROM 0xAE000) and the story font (0x1B000),
and writes data/en.tbl. Importable: load_glyphs(), patch_fonts(rom), ENC (char -> code)."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
MAIN, STORY = 0xAE000, 0x1B000
def load_glyphs(path=os.path.join(HERE, '..', 'data', 'en_font.txt')):
    G = {}; cur = None
    for l in open(path, encoding='utf-8'):
        l = l.rstrip('\n')
        if l.startswith('# ') or not l: continue
        if l.startswith('= '):
            code, ch = l[2:4], l[5:]
            cur = (int(code, 16), ch); G[cur] = []
        else: G[cur].append(l)
    return G
def enc4(rows):
    """8 rows of '#'/'.' -> 32-byte 4bpp tile in colour 15."""
    b = bytearray(32)
    for y, r in enumerate(rows):
        v = sum(1 << (7 - x) for x, c in enumerate(r) if c == '#')
        b[y*2] = b[y*2+1] = b[16+y*2] = b[16+y*2+1] = v
    return bytes(b)
G = load_glyphs()
ENC = {ch: code for (code, ch) in G}
ENC.update({str(d): d for d in range(10)}); ENC[' '] = 0xFF
def patch_fonts(r):
    for (code, ch), rows in G.items():
        assert len(rows) == 8 and code not in (0x1A, 0x2A, 0xF0, 0xFF) and code < 0x74, (code, ch)
        t = enc4(rows)
        r[MAIN + code*32:MAIN + code*32 + 32] = t
        r[STORY + code*32:STORY + code*32 + 32] = t
    for d in range(1, 10):   # story font has no digits; code 00 stays blank because story maps use it as space
        r[STORY + d*32:STORY + d*32 + 32] = r[MAIN + d*32:MAIN + d*32 + 32]
def write_tbl(path=os.path.join(HERE, '..', 'data', 'en.tbl')):
    with open(path, 'w', encoding='utf-8') as f:
        f.write('# English table for Tsuri Tarou (both 8x8 fonts). Story pages: no 0 digit (code 00 is blank there); use O.\n')
        for ch, code in sorted(ENC.items(), key=lambda x: x[1]): f.write('%02X=%s\n' % (code, ch))
        f.write('F0=<end>\n')
if __name__ == '__main__':
    r = bytearray(open(sys.argv[1], 'rb').read()); patch_fonts(r); write_tbl()
    sys.path.insert(0, HERE); from expand import fix_checksum; fix_checksum(r)
    open(sys.argv[2], 'wb').write(r); print('font patched,', len(G), 'glyphs')
