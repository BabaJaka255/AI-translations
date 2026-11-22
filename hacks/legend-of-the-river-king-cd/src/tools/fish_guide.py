"""Fish guide (図鑑) overlay: sector 82, bank $80 at $8000.

Every string is reached through a 7-byte stub `ldx #hi / ldy #lo / jmp $8d75` (202 stubs at
$87EF-$8D74), so the whole string pool ($8D80-$95EF) is rebuilt and the stubs re-pointed.
Overflow goes to the unused tail of the bank ($9D4E-$9FFF).
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import kslib

SECTOR = 82
STUBS = 0x87EF
POOL = [(0x8D80, 0x95F0), (0x9D4E, 0xA000)]
W = 18                      # detail window: 9 cells

# Area headers use the same area names as the menus
AREAS = {'渓流': 'Glen', '上流': 'High', '中流': 'Mid', '下流': 'Low', '河口': 'Bay'}
# Fish names follow the Super Legend of the River King glossary (v1.3), in Title Case. メゴチ is Flathead as there.
FISH = {
    'イワナ': 'Char', 'ヤマメ': 'Masu Trout', 'カジカ': 'Sculpin', 'ニジマス': 'Rainbow Trout',
    'アマゴ': 'Redspot Trout', 'ヒメマス': 'Kokanee', 'ブラウントラウト': 'Brown Trout',
    'カワマス': 'Brook Trout', 'ワカサギ': 'Pond Smelt', 'ブラックバス': 'Black Bass', 'ウグイ': 'Dace',
    'コイ': 'Carp', 'ドンコ': 'Dark Sleeper', 'オイカワ': 'Pale Chub', 'モツゴ': 'Stone Moroko',
    'イトモロコ': 'Itomoroko', 'ギギ': 'Bagrid Catfish', 'サクラマス': 'Masu Salmon',
    'コクレン': 'Bighead Carp', 'ハクレン': 'Silver Carp', 'ムギツク': 'Mugitsuku',
    'ホンモロコ': 'Biwa Gudgeon', 'ヤマノカミ': 'Rough Sculpin', 'ドジョウ': 'Loach',
    'タモロコ': 'Tamoroko', 'カワムツ': 'Dark Chub', 'キンブナ': 'Gold Crucian',
    'フナ': 'Crucian Carp', 'アカザ': 'Torrent Catfish', 'メダカ': 'Ricefish', 'ブルーギル': 'Bluegill',
    'オヤニラミ': 'Aucha Perch', 'ハリヨ': 'Stickleback', 'トミヨ': 'Ninespine',
    'タイワンドジョウ': 'Taiwan Snakehead', 'ヘラブナ': 'White Crucian', 'ナマズ': 'Catfish',
    'サヨリ': 'Halfbeak', 'ハス': 'Three-lips', 'ワタカ': 'Wataka', 'カマツカ': 'Pike Gudgeon',
    'ツチフキ': 'False Gudgeon', 'シマドジョウ': 'Spined Loach', 'カムルチー': 'Amur Snakehead',
    'ヒガイ': 'Higai', 'ソウギョ': 'Grass Carp', 'ニゴイ': 'Barbel Steed', 'メゴチ': 'Flathead',
    'マルタ': 'Pacific Redfin', 'ハゼ': 'Goby', 'ボラ': 'Mullet', 'スズキ': 'Sea Bass',
}
# "Use" column: 5 cells = 10 characters; dish names follow the River King glossary (Arai, Kabayaki...)
USES = {
    '塩焼き': 'Salt-grill', '美味': 'Tasty', '鑑賞用': 'Ornamental', 'みそ汁絶品': 'Great soup',
    'まずい': 'Tastes bad', '刺身': 'Sashimi', 'バター焼き': 'Butter fry', 'フライ': 'Fried',
    'スポーツ用': 'For sport', '味噌田楽': 'Dengaku', 'コイこく': 'Carp soup', '甘煮つけ': 'Sweet stew',
    '白焼き': 'Grilled', 'つくだに': 'Tsukudani', '煮つけ': 'Simmered', 'つけやき': 'Tsukeyaki',
    'みそ汁': 'Miso soup', 'からあげ': 'Fried', '煮びたし': 'Nibitashi', '食べない': 'Not eaten',
    'あらい': 'Arai', '蒲焼き': 'Kabayaki', '吸物': 'Soup', 'なれずし': 'Narezushi',
    '産卵期美味': 'Spawn-good', '天ぷら': 'Tempura', 'カラスミ': 'Bottarga', '夏のあらい': 'Arai',
    '極めて美味': 'Delicious!', 'くんせい': 'Smoked', 'すし': 'Sushi', '甘露煮': 'Candied',
    '酢のもの': 'Vinegared',
}
LABELS = {
    '長　さ　　　　Ｃｍ': 'Length' + ' ' * 8 + 'cm',   # number in cells 5-6
    '釣　果　　　　　匹': 'Got'.ljust(W),      # count in cell 7
    '利　用': 'Use', '戻る': 'Back', '続く': 'Next', '終り': 'End',
}

def translate(jp):
    """Japanese pool string -> English text, or None to keep the original bytes."""
    if jp in LABELS: return LABELS[jp]
    if jp in USES: assert len(USES[jp]) <= 10, jp; return USES[jp]
    if jp in FISH: return FISH[jp]
    if jp.startswith('（') and jp[1:3] in AREAS:          # （渓流の魚１）
        return '(%s fish %s)' % (AREAS[jp[1:3]], chr(ord(jp[5]) - 0xFEE0))
    name = jp.replace('　', '')
    if name in FISH:                                       # spaced title on the detail page
        en = FISH[name]; assert len(en) <= W, en
        return (' ' * ((W - len(en)) // 2) + en).rstrip()
    return None                                            # full-width numbers, variables

def enc(text):
    b = text.encode('ascii')
    if len(b) % 2: b += b' '
    return b + b'\0\0'

def rebuild(t):
    """t: build_patch.Track. Returns bytes used per pool region."""
    bank = bytearray(b''.join(t.read(SECTOR + i) for i in range(4)))
    def at(a): return a - 0x8000
    stubs = []; p = STUBS
    while bank[at(p)] == 0xA2 and bank[at(p) + 2] == 0xA0 and bank[at(p) + 4:at(p) + 7] == b'\x4c\x75\x8d':
        stubs.append((p, bank[at(p) + 1] << 8 | bank[at(p) + 3])); p += 7
    assert len(stubs) == 202, len(stubs)
    blobs = {}
    for _, a in stubs:
        jp, n = kslib.parse(bytes(bank), at(a))
        en = translate(jp)
        blobs[a] = enc(en) if en is not None else bytes(bank[at(a):at(a) + n])
    for lo, hi in POOL: bank[at(lo):at(hi)] = bytes(hi - lo)
    placed = {}; regions = [list(r) for r in POOL]
    for p, a in stubs:
        b = blobs[a]
        if b not in placed:
            for r in regions:
                if r[0] + len(b) <= r[1]: placed[b] = r[0]; bank[at(r[0]):at(r[0]) + len(b)] = b; r[0] += len(b); break
            else: raise ValueError('fish guide strings do not fit')
        q = placed[b]; bank[at(p) + 1] = q >> 8; bank[at(p) + 3] = q & 0xFF
    t.write(SECTOR, 0, bytes(bank))
    return [r[0] - lo for r, (lo, hi) in zip(regions, POOL)], [hi - lo for lo, hi in POOL]
