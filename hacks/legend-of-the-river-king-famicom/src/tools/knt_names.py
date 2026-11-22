"""Fish and creature names for Kawa no Nushi Tsuri (FC), from the series glossary
(notes/glossary.md).  Dialogue form: lower case except proper names."""

# fish number = area*12 + kind, in ROM order (bank 10 $AF6E-$B0BF)
FISH = [
    # area 1 (Stream)
    ("イワナ", "char", "a"), ("ヤマメ", "Masu trout", "a"), ("カジカ", "sculpin", "a"),
    ("ニジマス", "rainbow trout", "a"), ("アマゴ", "redspot trout", "a"), ("イモリ", "newt", "a"),
    ("ヒメマス", "kokanee", "a"), ("ブラウントラウト", "brown trout", "a"), ("カワマス", "brook trout", "a"),
    ("ワカサギ", "pond smelt", "a"), ("ブラックバス", "black bass", "a"), ("ウグイ", "dace", "a"),
    # area 2 (Upstream)
    ("カエル", "frog", "a"), ("コイ", "carp", "a"), ("ドンコ", "dark sleeper", "a"),
    ("オイカワ", "pale chub", "a"), ("モツゴ", "stone moroko", "a"), ("モロコ", "gudgeon", "a"),
    ("ギギ", "bagrid catfish", "a"), ("サクラマス", "Masu salmon", "a"), ("コクレン", "bighead carp", "a"),
    ("ハクレン", "silver carp", "a"), ("ムギツク", "mugitsuku", "a"), ("ホンモロコ", "Biwa gudgeon", "a"),
    # area 3 (Midstream)
    ("ヤマノカミ", "rough sculpin", "a"), ("ドジョウ", "loach", "a"), ("タモロコ", "tamoroko", "a"),
    ("カワムツ", "dark chub", "a"), ("カナヘビ", "grass lizard", "a"), ("キンブナ", "gold crucian", "a"),
    ("フナ", "crucian carp", "a"), ("アカザ", "torrent catfish", "a"), ("メダカ", "ricefish", "a"),
    ("ブルーギル", "bluegill", "a"), ("オヤニラミ", "Aucha perch", "an"), ("ハリヨ", "stickleback", "a"),
    # area 4 (Plains)
    ("カメ", "turtle", "a"), ("トミヨ", "ninespine", "a"), ("タイワンドジョウ", "Taiwan snakehead", "a"),
    ("ヘラブナ", "white crucian", "a"), ("ナマズ", "catfish", "a"), ("テナガエビ", "river prawn", "a"),
    ("サヨリ", "halfbeak", "a"), ("ハス", "three-lips", "a"), ("ワタカ", "wataka", "a"),
    ("カマツカ", "pike gudgeon", "a"), ("ツチフキ", "false gudgeon", "a"), ("シマドジョウ", "spined loach", "a"),
    # area 5 (Coast)
    ("カムルチー", "Amur snakehead", "an"), ("ヒガイ", "higai", "a"), ("ソウギョ", "grass carp", "a"),
    ("ニゴイ", "barbel steed", "a"), ("メゴチ", "flathead", "a"), ("マルタ", "Pacific redfin", "a"),
    ("ハゼ", "goby", "a"), ("ボラ", "mullet", "a"), ("スズキ", "sea bass", "a"),
    ("ヘビ", "snake", "a"), ("カワノヌシ", "River King", "the"),
]
assert len(FISH) == 59


def catch_lines(name, art):
    """Candidates for $074A = D1 (got away), D2 (landed), D3 (let go); the
    builder takes the first one that fits the two 18-tile rows."""
    return [[f"The {name} got away.", f"The {name} escaped."],
            [f"You landed {art} {name}!", f"Landed {art} {name}!"],
            [f"You let the {name} go.", f"You released the {name}."]]


# battle creatures, order of the offset table at $F4D8 (index $0756)
CREATURES = [
    ("あかねずみ", "Field Mouse"), ("のうさぎ", "Hare"), ("もぐら", "Mole"), ("やまこうもり", "Mt. Bat"),
    ("ふくろう", "Owl"), ("てん", "Marten"), ("カラス", "Crow"), ("きつね", "Fox"),
    ("ももんが", "Flying Squirrel"), ("たぬき", "Tanuki"), ("いたち", "Weasel"), ("わし", "Eagle"),
    ("あおだいしょう", "Rat Snake"), ("しまへび", "Snake"), ("かもしか", "Serow"), ("まむし", "Viper"),
    ("おおじか", "Deer"), ("やまざる", "Macaque"), ("やまねこ", "Wildcat"), ("あなぐま", "Badger"),
    ("いのしし", "Boar"), ("つきのわぐま", "Moon Bear"),
]
assert len(CREATURES) == 22
B1_WIDTH = max(len(e) for _, e in CREATURES)
