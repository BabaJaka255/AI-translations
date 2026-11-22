"""One-time generator for script/*.json (Japanese from the ROM, first English draft).
After this, script/*.json is the source of truth: edit "en" (and "notes") there, not here.
Run with --force to regenerate (overwrites translations!)."""
import json, os, sys
from ftlib import *

FISH = [  # index order of the game's fish tables
    ('イサキ', 'Grunt'), ('イシガキダイ', 'Spot Beakfish'), ('イシダイ', 'Beakfish'), ('イスズミ', 'Rudderfish'),
    ('イナダ', 'Jr. Yellowtail'), ('カサゴ', 'Scorpionfish'), ('カツオ', 'Bonito'), ('カッポレ', 'Black Trevally'),
    ('カンパチ', 'Amberjack'), ('クエ', 'Kelp Grouper'), ('シイラ', 'Mahi-mahi'), ('シマアジ', 'Striped Jack'),
    ('ツムブリ', 'Rainbow Runner'), ('ヒラマサ', 'Kingfish'), ('フエフキダイ', 'Emperor'), ('ブダイ', 'Parrotfish'),
    ('マハタ', 'Grouper'), ('メジナ', 'Opaleye'), ('メジマグロ', 'Young Bluefin'), ('ワラサ', 'Big Yellowtail'),
    ('アイゴ', 'Rabbitfish'), ('アイナメ', 'Greenling'), ('アオブダイ', 'Blue Parrotfish'), ('アジ', 'Jack Mackerel'),
    ('イシガキフグ', 'Burrfish'), ('ウツボ', 'Moray Eel'), ('ウマヅラハギ', 'Horse Filefish'), ('エイ', 'Stingray'),
    ('オニオコゼ', 'Devil Stinger'), ('オニカサゴ', 'Stingfish'), ('カイワリ', 'Trevally'), ('カゴカキダイ', 'Stripey'),
    ('カマス', 'Barracuda'), ('カワハギ', 'Filefish'), ('キス', 'Whiting'), ('クロダイ', 'Black Porgy'),
    ('サヨリ', 'Halfbeak'), ('サワラ', 'Seerfish'), ('タカノハダイ', 'Morwong'), ('タカベ', 'Butterfish'),
    ('タチウオ', 'Cutlassfish'), ('ダツ', 'Needlefish'), ('ニザダイ', 'Surgeonfish'), ('ヒラスズキ', 'Blackfin Bass'),
    ('ヒラメ', 'Flounder'), ('フグ', 'Puffer'), ('ベラ', 'Wrasse'), ('ホウボウ', 'Gurnard'),
    ('ボラ', 'Mullet'), ('マサバ', 'Mackerel'), ('マダイ', 'Red Sea Bream'), ('ムロアジ', 'Round Scad'),
    ('ヌシ', 'Sea King'),
]
FISH_EN = dict(FISH)
FISH_NOTES = {
    'クエ': 'Same species as Umi no Nushi Tsuri\'s モロコ (Kanto name), which that patch calls Kelp Grouper.',
    'オニカサゴ': 'Scorpaenopsis cirrosa, weedy stingfish. Not in Umi no Nushi Tsuri.',
    'イシガキフグ': 'Chilomycterus reticulatus, spotfin burrfish.',
    'カゴカキダイ': 'Microcanthus strigatus, stripey.',
    'タカノハダイ': 'Goniistius zonatus, spottedtail morwong.',
    'ニザダイ': 'Prionurus scalprum, sawtail surgeonfish.',
    'ヒラスズキ': 'Lateolabrax latus, blackfin sea bass.',
    'フエフキダイ': 'Lethrinus haematopterus, emperor.',
    'ヌシ': 'ぬし: Sea King, as in Super Legend of the Sea King (海のぬし).',
}
MODES = ['Lure Fishing', 'Live Bait', 'Drop Fishing', 'Chum Fishing', 'Bottom Fishing']
MODE_NOTES = ['ルアー釣り篇', '生きエサ釣り篇', 'タラシ釣り篇: tarashi, bait hung straight down', 'コマセ釣り篇: komase, fishing over chum', 'ブッ込み釣り篇: bukkomi, heavy bottom rig']
BAITS = ['Metal Jig', 'Spoon', 'Floating Minnow', 'Deep Diver', 'Sinking Minnow',
         'Sardine', 'Small Scad', 'Round Scad',
         'Lugworm', 'Ragworm', 'Krill', 'Squid Strip', 'Sardine', 'Hanpen',
         'Krill (L)', 'Krill (M)', 'Krill (S)',
         'Turban Shell', 'Abalone', 'Crab', 'Habanori',
         'Sardine', 'Ark Shell', 'Sea Urchin', 'Hermit Crab']
SPOTS = ['Off Rokusōne', 'Off Cape Izu', 'Off Yunohama', 'Off Sanshichiyama', 'Off Cape Satadō',
         'Off Miikehama', 'Off Kuramane', 'Off Cape Tsurune', 'Off Shinbana', 'Off Shinmyōike',
         'Off Usuki', 'Off Mabana', 'Off Tomiga Shrine', 'Off Ako', 'Off Sabigahama',
         'Off Ōne East', 'Off Ōne South', 'Off Bunzōne East', 'Off Bunzōne South', 'Off Bunzōne West',
         'Off Makadone South', 'Off Makadone West', 'Off Makadone North', 'Off Kasagone', 'Off Ebine',
         'Off Nokogirine', 'Off Koyasujima', 'Off Tokkurine', 'Off Mikurajima NE', 'Off Subaru Rock',
         'Off Mikurajima SE', 'Off Motone NE', 'Off Motone East', 'Off Motone South', 'Off Motone West',
         'Off Kawaguchi Falls', 'Off Yokozukane', 'Off Koikene North', 'Off Koikene NW', 'Off Koikene SW',
         'Off Koikene South', 'Off Yokosene North', 'Off Yokosene East', 'Off Yokosene South', 'Off Yokosene SW',
         'Off Ichinone SE', 'Off Ichinone North', 'Off Nakane', 'Off Shitatatebana', 'Off Nagasaki',
         'Off Jinta', 'Off Niura', 'Off Eigagata', 'Off Nazumado', 'Off Kaminato Port',
         'Off Mishōtaine West', 'Off Mishōtaine East', 'Off Ōne', 'Off Ōgane', 'Off Ishizumigahana',
         'Off Harabuto', 'Off Tatamine', 'Off Yokozuka', 'Off Yokomagaura', 'Off Inanba']
SPOT_UNSURE = {0, 6, 8, 11, 26, 31, 32, 33, 34, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 48, 51, 52, 55, 56, 58, 60}
ISLANDS = ['Miyakejima', 'Sanbondake', 'Mikurajima', 'Hachijō-kojima', 'Hachijōjima', 'Inanbajima']

INTRO = """Well, hello there!
Fish don't bite like they
used to these days.
Still, next to fishing from
the rocks or the shore,
you'll catch plenty from a
boat. That's what makes it
so much fun!
There are lots of kinds of
fish, and each one is a
thrill in its own way.
From a boat you can reach
fish far offshore, out of
casting range from land.
Moving to a new spot is
easy, too.
And once a fish is hooked,
it's less likely to snag
your line on the rocks.
When you fish the rocks of
a far-off island, even a
small swell can keep you
from landing on them. It's
a real letdown, but you
won't have that worry on a
boat!

Now, all aboard!
Let's go fishing!
Catch all kinds of fish.
And at the very end, the
Sea King of Inanba is
waiting for you.
Good luck out there!
So long!

                Fune Taro"""

STRINGS = [
    # id, offset, refs (ROM offsets of 16-bit operands -> string start), en, notes
    ('save_lost', 0x14200, [], None, 'Two entry points ($4200 from $C0:6B6A, $4210 from $C0:6994), so it stays in place: text from $4211 to the end code at $4225 (20 bytes).'),
    ('sound_test', 0x14226, [0x6BA5], "\n\n\n\n      Sound Test\n\n\n\n        ^Music\n\n\n        ^Sound FX\n\n\n        ^PCM", 'Hidden sound test.'),
    ('catch_list', 0x1426D, [0x705A], None, 'Y on the sea map: catch by species. Two boxed columns about 9 columns wide.'),
    ('name_entry', 0x14D43, [0x7495, 0x769C], None, 'Keyboard: each ^ is a key, the byte after it is the letter typed. The END key is ^~.'),
    ('new_record', 0x14EB2, [0x7D84], 'New Record!', ''),
    ('game_over', 0x14EB9, [0x8037], 'GAME OVER', ''),
    ('title_menu', 0x15BA8, [0x74F1], None, '^ = menu cursor and angler-name slots.'),
    ('records', 0x15C16, [0x7105], None, 'Per-fish records: longest catch and most caught, 4 anglers each. Numbers are drawn by the game after the ^ name slots.'),
    ('intro', 0x15CEA, [0xC596], INTRO, 'Opening speech after a new name. Two-line window from column 4; keep lines within 28 columns.'),
]

SAVE_LOST_EN = 'Records were erased.'

CATCH_LIST = None   # built below
NAME_ROWS = ['ABCDEFGHI', 'JKLMNOPQR', 'STUVWXYZ.', 'abcdefghi', 'jklmnopqr', 'stuvwxy', "z-'!?&", '012345', '6789()', ',:;"+*']


def name_entry_en():
    s = '\n\n\n\n  Enter your name\n\n\n\n'
    rows = []
    for i, r in enumerate(NAME_ROWS):
        line = '      ' + ' '.join('^' + c for c in r)
        if i == len(NAME_ROWS) - 1:
            line += '          ^~End'
        rows.append(line)
    return s + '\n\n'.join(rows) + '\n'


TITLE_MENU_EN = ('\n\n\n\n       ^Depart     ^New Angler\n\n\n\n\n     Angler          Score\n\n\n\n'
                 '      ^\n\n\n\n      ^\n\n\n\n      ^\n\n\n\n      ^')
RECORDS_EN = ('\n' * 15 + '      Longest         Most Caught\n\n\n'
              '  Angler   Size   Angler  Count\n\n'
              '  1 ^            cm  1 ^\n\n'
              '  2 ^            cm  2 ^\n\n'
              '  3 ^            cm  3 ^\n\n'
              '  4 ^            cm  4 ^')


def main():
    os.makedirs(os.path.join(GAME, 'script'), exist_ok=True)
    out1 = os.path.join(GAME, 'script', 'strings.json')
    if os.path.exists(out1) and '--force' not in sys.argv:
        print('script/ exists; use --force to overwrite'); return
    rom = load_rom()
    ents = []
    for sid, off, refs, en, notes in STRINGS:
        end = rom.index(bytes([END]), off)
        jp = decode_jp(rom[off:end])
        if sid == 'save_lost':
            en = '\n' * 11 + '     ' + SAVE_LOST_EN
        elif sid == 'name_entry':
            en = name_entry_en()
        elif sid == 'title_menu':
            en = TITLE_MENU_EN
        elif sid == 'records':
            en = RECORDS_EN
        elif sid == 'catch_list':
            en = None
        ents.append({'id': sid, 'offset': '0x%05X' % off, 'length': end - off + 1,
                     'refs': ['0x%05X' % r for r in refs], 'jp': jp, 'en': en or '', 'notes': notes})
    json.dump({'block': 'strings', 'entries': ents}, open(out1, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

    lists = {}
    def mk(name, base, stride, count, en_list, notes_list=None, jp_fn=None):
        ents = []
        for i in range(count):
            raw = rom[base + i * stride: base + (i + 1) * stride]
            jp = decode_jp(raw).strip(' 　~').replace(' ', '') if jp_fn is None else jp_fn(raw)
            ents.append({'id': '%s_%02d' % (name, i), 'jp': jp, 'en': en_list[i] if en_list else '',
                         'notes': (notes_list[i] if notes_list else '')})
        lists[name] = {'base': '0x%05X' % base, 'stride': stride, 'count': count, 'entries': ents}
    fish_en = [FISH[i][1] for i in range(53)]
    fish_notes = [FISH_NOTES.get(FISH[i][0], '') for i in range(53)]
    mk('fish_title', 0x14588, 17, 53, fish_en, fish_notes)
    mk('fish_name', 0x1510B, 12, 53, fish_en, fish_notes)
    mk('mode', 0x14ECC, 15, 5, MODES, MODE_NOTES)
    mk('bait', 0x14F17, 20, 25, BAITS)
    chap_jp = []
    mk('chapter', 0x15387, 19, 65, None)
    for e in lists['chapter']['entries']:
        fish = e['jp'].replace('の巻き', '')
        e['en'] = FISH_EN[fish] + ' Chapter'
    mk('spot', 0x1585A, 12, 65, SPOTS, ['UNSURE: reading of the place name' if i in SPOT_UNSURE else '' for i in range(65)])
    mk('island', 0x15B66, 11, 6, ISLANDS)
    json.dump(lists, open(os.path.join(GAME, 'script', 'lists.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('wrote script/strings.json and script/lists.json')


if __name__ == '__main__':
    main()
