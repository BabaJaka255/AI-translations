"""Build the translation script for Tsuri Tarou.
build_script.py ROM OUTDIR  ->  OUTDIR/script.json and OUTDIR/script.xlsx

Every entry has: id, group, kind, rom (hex offset), jp, en (blank), limit, notes.
'limit' is the on-screen space in 8x8 columns (and lines, where it matters)."""
import sys, os, json, unicodedata
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ttlib import decode, TS, mark

rom = open(sys.argv[1], 'rb').read()
outdir = sys.argv[2]
E = []
def add(id, group, kind, rom_off, jp, limit, notes='', **kw):
    d = dict(id=id, group=group, kind=kind, rom='%06X' % rom_off if rom_off is not None else '',
             jp=jp, en='', limit=limit, notes=notes)
    d.update(kw); E.append(d)

# Known decode slips where two glyphs share one tile (ロ/口, シ/し).
FIX = {'ロに入れた': '口に入れた', 'ジゅうぶん': 'じゅうぶん'}
def fix(s):
    for a, b in FIX.items(): s = s.replace(a, b)
    return s

# ---- 1. Spot info signs: 15 spots x 5 lines, F0-terminated, $01:E141-E751
SPOT_FISH = ['イワナ', 'ヤマメ', 'ニジマス', 'ヘラブナ', 'ブラックバス', 'ウグイ', 'オイカワ', 'マブナ',
             'ナマズ', 'コイ', 'テナガエビ', 'ウナギ', 'タナゴ', 'モツゴ', '川のヌシ']
o, end = 0x0E141, 0x0E751
p = o
for i, s in enumerate(rom[o:end].split(b'\xf0')):
    if p >= end: break
    spot, ln = i // 5 + 1, i % 5 + 1
    tiles = len(s) - s.count(0x1A) - s.count(0x2A)
    add('spot%02d_l%d' % (spot, ln), 'Spot signs', 'F0 string (8x8 font)', p, fix(decode(s)),
        '22 cols', 'Spot %d (%s), line %d of 5. JP uses %d cols, %d bytes. Drawn at col 7; bullet at col 5 (line 5 has none).'
        % (spot, SPOT_FISH[spot - 1], ln, tiles, len(s)), bytes=len(s))
    p += len(s) + 1

# ---- 2. Story pages: 32x32 column-major tilemaps, text tiles 0x100+code, dakuten on the row above
PAGES = [(0x40000, 'Opening'), (0x0A0800, 'Next morning (start of a new day)'),
         (0x037800, 'Came home early without the Nushi'), (0x087800, 'Day ended without the Nushi'),
         (0x040800, 'Ending')]
for m, title in PAGES:
    w = [rom[m + 2 * i] | rom[m + 2 * i + 1] << 8 for i in range(1024)]
    def ch(r, c):
        t = w[c * 32 + r] & 0x3FF
        if t in (0, 0x100): return ' '
        return TS.get(t & 0xFF, '?') if 0x100 <= t < 0x200 else '#'
    n = 0
    for r in range(32):
        row = []
        for c in range(32):
            k = ch(r, c); above = ch(r - 1, c) if r else ' '
            if k in ('゛', '゜'): k = ' '
            elif above in ('゛', '゜') and k.strip(): k = mark(k, above)
            row.append(k)
        line = ''.join(row)
        if not line.strip(' #'): continue
        c0 = len(line) - len(line.lstrip()); c1 = len(line.rstrip()) - 1
        n += 1
        add('story_%06X_r%02d' % (m, r), 'Story pages', 'Tilemap row (story font)', m + 2 * r,
            fix(line.strip()), '30 cols', '%s, line %d (row %d, cols %d-%d). Kana marks sit on the row above, so '
            'English can use every row: up to about 26 rows x 30 cols per page.' % (title, n, r, c0, c1))

# ---- 3. Menu screens: tilemap labels drawn with the 0x3A000 glyph sheet (BG1, 16x16 kanji/kana art)
MENUS = [
    ('name', 0x0A0000, 'Name entry', [('名前を入れて下さい', '18 cols x 2 rows', 'Title box, 16x16 glyphs')]),
    ('date', 0x0C4000, 'Date entry', [('日付を入れて下さい', '18 cols x 2 rows', 'Title box, 16x16 glyphs'),
                                       ('年', '1 col', 'Year label (8x8)'), ('月', '1 col', 'Month label'),
                                       ('日', '1 col', 'Day label')]),
    ('file', 0x03C000, 'File select', [('はじめる', '8 cols x 2 rows', 'Start'), ('データを消す', '12 cols x 2 rows', 'Erase data'),
                                         ('名　前', '6 cols x 2 rows', 'Column header: name'),
                                         ('釣りの力', '8 cols x 2 rows', 'Column header: fishing power'),
                                         ('歩く力', '6 cols x 2 rows', 'Column header: walking power')]),
    ('records', 0x03D000, 'Records (best catches / totals)', [
        ('釣り人', '6 cols x 2 rows', 'Header: angler (top table)'), ('体長', '4 cols x 2 rows', 'Header: length'),
        ('釣った日', '8 cols x 2 rows', 'Header: date caught'), ('Cm', '2 cols', 'Unit after length'),
        ('年', '1 col', 'Year'), ('月', '1 col', 'Month'), ('日', '1 col', 'Day'),
        ('釣り人', '6 cols x 2 rows', 'Header: angler (bottom table)'), ('釣果', '4 cols x 2 rows', 'Header: catch count'),
        ('成功率', '6 cols x 2 rows', 'Header: success rate'), ('匹', '1 col', 'Counter for fish'), ('%', '1 col', 'Percent')]),
    ('confirm', 0x03C800, 'Erase confirm', [('本当に　いいですか？', '19 cols x 2 rows', 'Are you sure?'),
                                            ('はい', '6 cols', 'Yes'), ('いいえ', '6 cols', 'No')]),
    ('title', 0x080800, 'Title screen', [('はじめる', '8 cols', 'Press start / begin (glyphs not in 0x3A000 sheet)'),
                                         ('© 1994 PACK-IN-VIDEO', '22 cols', 'Copyright line, likely keep as is')]),
    ('kbd', 0x081000, 'Name keyboard', [('あ～ん + が～ぽ, を ー っ ゃ ゅ ょ', '9x5 + 7x5 grid', 'Hiragana keyboard; decide on Latin letters'),
                                        ('おわり', '6 cols', 'Done button')]),
]
for key, m, title, labels in MENUS:
    for j, (jp, lim, note) in enumerate(labels):
        add('menu_%s_%02d' % (key, j + 1), 'Menus', 'Tilemap graphic label', m, jp, lim,
            '%s screen. %s.' % (title, note))

# ---- 4. Fish names: 16x16 katakana (sheet at 0xB8000 for sprites, VRAM tile 0x180+ on the fish list)
KANA = {}
for l in open(os.path.join(os.path.dirname(__file__), '..', 'data', 'tt_sprite_kana.tbl'), encoding='utf-8'):
    l = l.strip()
    if l and not l.startswith('#'):
        k, _, v = l.partition('='); KANA[int(k, 16)] = v
def kname(codes):
    return ''.join(KANA.get(c, '[%02X]' % c) for c in codes)
for setname, base, where in (('sign', 0x3E9F4, 'Spot sign header, centred at y=0x38'),
                             ('catch', 0x3EBD4, 'Second header set at (0x18,0x18), probably the catch screen')):
    for n in range(15):
        o = base + n * 0x20
        recs = [rom[o + 4 * i:o + 4 * i + 4] for i in range(8)]
        recs = [r for r in recs if r[3]]
        inner = [r[2] for r in recs[1:-1]]  # first/last are the ( ) brackets
        nm = kname(inner) if n < 14 else '川のヌシ'
        add('fishhdr_%s_%02d' % (setname, n + 1), 'Fish names', 'Sprite list (16x16 kana)', o, nm,
            '8 sprites incl. brackets',
            '%s. %d sprites; tiles %s.%s' % (where, len(recs), ' '.join('%02X' % t for t in inner),
            ' Tiles are outside the kana sheet; name assumed from the fish list, not yet seen on screen.' if n == 14 else ''))
m = 0x03D800
w = [rom[m + 2 * i] | rom[m + 2 * i + 1] << 8 for i in range(1024)]
for r in range(3, 25, 3):
    for side, cols in (('L', range(4, 16, 2)), ('R', range(19, 30, 2))):
        codes = []
        for c in cols:
            t = w[c * 32 + r] & 0x3FF
            if 0x180 <= t < 0x200: codes.append(t - 0x180)
        if codes:
            add('fishlist_r%02d%s' % (r, side), 'Fish names', 'Tilemap (16x16 kana)', m + 2 * r, kname(codes),
                '%d cols' % (12 if side == 'L' else 10), 'SELECT fish list, row %d %s column.' % (r, 'left' if side == 'L' else 'right'))
add('fishlist_nushi', 'Fish names', 'Tilemap graphic', m, '川のヌシ', '8 cols', 'SELECT fish list, last entry (0x3A000 sheet tiles 002-025).')

# ---- 5. Sprite text
add('spr_backup', 'Sprite text', 'Sprite list (8x8 font, tile-0x80)', 0x3E90C,
    '＊バックアップデータがこわれています。＊ / スタートボタンをおしてください。 / はじめからゲームをはじめます。',
    '3 lines, 58 sprites', 'Shown when SRAM is bad. One sprite per character.')
add('spr_hud_power', 'Sprite text', 'Sprite graphic (0x36800)', 0x36800, 'つりの力', '4 sprites', 'HUD label: fishing power.')
add('spr_hud_walk', 'Sprite text', 'Sprite graphic (0x36800)', 0x36800, '歩く力', '3 sprites', 'HUD label: walking power.')
add('logo', 'Graphics', 'Compressed? / raw tiles', None, 'つり太郎', 'logo', 'Title logo art. English logo is an open question.')

for i, e in enumerate(E): e['n'] = i + 1
os.makedirs(outdir, exist_ok=True)
json.dump(E, open(os.path.join(outdir, 'script.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill
wb = Workbook(); ws = wb.active; ws.title = 'Script'
cols = ['n', 'id', 'group', 'kind', 'rom', 'jp', 'en', 'limit', 'notes']
ws.append(cols)
for c in ws[1]: c.font = Font(bold=True); c.fill = PatternFill('solid', fgColor='DDDDDD')
for e in E: ws.append([e[k] for k in cols])
for k, wd in zip('ABCDEFGHI', (5, 22, 12, 24, 9, 48, 48, 18, 60)): ws.column_dimensions[k].width = wd
for row in ws.iter_rows(min_row=2):
    for c in row: c.alignment = Alignment(wrap_text=True, vertical='top')
ws.freeze_panes = 'F2'
wb.save(os.path.join(outdir, 'script.xlsx'))
from collections import Counter
print(len(E), Counter(e['group'] for e in E))
