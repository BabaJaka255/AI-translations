# Glossary: Kawa no Nushi Tsuri (Famicom, 1990)

Settled 2026-11-22 against the ROM (names checked in the ROM tables; ソ/ン read as ン where the ROM tile is shared).
Follows the series glossary used by the River King patches in this repo (master: the SFC
"Super Legend of the River King" glossary in `hacks/super-legend-of-the-river-king/docs/`). Window widths: command 4 letters, bait/gear rows 6,
food/item rows 9, shop rows 9, status/rod titles 10. Short forms follow the Shizen-ha and GBA precedents
(Caddis, Midge, Paste, Bag) where a series name does not fit; dialogue uses the same words as the menus.
The code-level source of every window string is `src/tools/knt_windows.py`; fish and creatures are in `src/tools/knt_names.py`.

Rules carried over: same Japanese = same English as the series; Title Case in menus/lists, lower case in dialogue;
ぬし = River King; money in yen; counters dropped; honorifics: none needed (no named characters speak with them).

## Terms
| Japanese | Reading | English | Kind | Notes |
|---|---|---|---|---|
| 川のぬし釣り | Kawa no Nushi Tsuri | Legend of the River King | title | series western name; new logo "Legend of The River King" (src/gfx/title_logo.png, drawn by the project lead) |
| ぬし | nushi | River King | term | series |
| 体力 | tairyoku | HP | stat | series |
| お金 / 円 | okane / en | Yen | stat | series |
| 経験値 | keikenchi | EXP | stat | series |
| びく | biku | Bag (command) / Creel | item | command slot is 4 letters, as GBA "Bag"; creel window title, shop items and dialogue say "creel" |
| めいれい | meirei | Command | window title | |
| エサ / たべる / つりぐ / びく / はなす / どうぐ | | Bait / Eat / Gear / Bag / Talk / Item | commands | 4-letter slots |
| きょり / ひきよせる / にがす | | Dist / Reel / Let Go | fishing window | 6-letter slots; distance in m |
| たたかう / たべる / にげる | | Fight / Eat / Run | battle window | |
| はい / いいえ | | Yes / No | | |
| しょくりょう | | Food | window title | the item window has the title "Items" |
| ようりょう | | Creel (capacity) | window title | "Creel 10" etc.; rows 0-10cm, 11-20cm, 21-30cm, 31-50cm, 51cm+ |
| つりようひん | | Shop | window title | name on one row, price below it |
| さかな (fish buyer) | | Fish | window title | ≤10cm ¥10 … 51cm+ ¥50 |
| 宿 / 釣 / 魚 plaques | | INN / hook picture / fish picture | town graphics | series convention; おちゃ banner = TEA |

## Areas (status window title, up to 10 letters)
| Japanese | Reading | English | Notes |
|---|---|---|---|
| 渓流 | keiryū | Stream | series |
| 上流 | jōryū | Upstream | new in FC |
| 中流 | chūryū | Midstream | as Nushi Tsuri 64 |
| 下流 | karyū | Plains | series (KnT2 下流 = Plains) |
| 河口 | kakō | Coast | series |

## Bait and tackle
| Japanese | English | Notes |
|---|---|---|
| カワムシ | Caddis | menu and dialogue ("caddis"), as Shizen-ha (6-letter bait slot) |
| ねりえ | Paste | menu; "paste bait" in dialogue |
| アカムシ | Midge | menu; "midges" in dialogue, as Shizen-ha |
| サシ | Maggot | menu (6 letters); "maggots" in dialogue |
| ミミズ | Worms | |
| はり | Hooks | gear row; "hook" in dialogue |
| よせえ | Chum | 寄せ餌, scattered to draw fish (the FAQ's "fishing line" was a guess) |
| ぬしばり | K.Hook / King Hook | K.Hook in the 6-letter gear row; King Hook in shops and dialogue |
| ぬしえさ | K.Bait / King Bait | same rule |
| びく10/20/30/60 | Creel 10 / 20 / 30 / 60 | shop names |
| たけざお | Bamboo Rod | |
| グラスざお | Glass Rod | |
| カーボンざお | Carbon Rod | |
| ぬしざお | King Rod | |
| たまうき | Ball Float | gear window shows "Float:" then "Ball" |
| ぼううき | Stick Float | "Stick" |
| とうがらしうき | Chili Float | "Chili" |

## Food
| Japanese | English | Notes |
|---|---|---|
| パン | Bread | |
| にくまん | Meat Bun | nikuman |
| うどん | Udon | keep the dish name |
| やきいも | Sweet Potato | "Sw.Potato" in the 9-letter food and shop rows |
| おにぎり | Rice Ball | series |

## Tools
| Japanese | English | Notes |
|---|---|---|
| かぎ | Key | series |
| めがね | Glasses | given by the man by the tackle shop; used to look around |
| じしゃく | Compass | series (磁石 = Compass); it points to the hidden switch |
| ちず | Map | |
| タライ | Washtub | series |
| はなび | Fireworks | series |
| ハンマー | Hammer | |
| りんご | Apple | |

## Creatures (battle enemies, as series; Title Case, they open battle lines: "Mt. Bat appeared!")
あかねずみ Field Mouse · のうさぎ Hare · やまこうもり Mt. Bat · もぐら Mole · ふくろう Owl · てん Marten · カラス Crow ·
たぬき Tanuki · きつね Fox · ももんが Flying Squirrel · いたち Weasel · しまへび Snake · わし Eagle ·
あおだいしょう Rat Snake · かもしか Serow · まむし Viper · やまねこ Wildcat · おおじか Deer · やまざる Macaque ·
あなぐま Badger · つきのわぐま Moon Bear · いのしし Boar

## Fish and other catches (as series; lower case inside the catch lines, e.g. "You landed a Masu trout!")
カジカ Sculpin · イワナ Char · ヤマメ Masu Trout · アマゴ Redspot Trout · ニジマス Rainbow Trout · ブラウントラウト Brown Trout ·
ワカサギ Pond Smelt · ウグイ Dace · ヒメマス Kokanee · カワマス Brook Trout · ブラックバス Black Bass · ギギ Bagrid Catfish ·
オイカワ Pale Chub · サクラマス Masu Salmon · コクレン Bighead Carp · ハクレン Silver Carp · モロコ Gudgeon · モツゴ Stone Moroko ·
ホンモロコ Biwa Gudgeon · ドンコ Dark Sleeper · コイ Carp · ムギツク Mugitsuku · ヤマノカミ Rough Sculpin (ROM: ヤマノカミ) ·
カワムツ Dark Chub · アカザ Torrent Catfish · オヤニラミ Aucha Perch · ハリヨ Stickleback · キンブナ Gold Crucian · タモロコ Tamoroko ·
メダカ Ricefish · ドジョウ Loach · フナ Crucian Carp · ブルーギル Bluegill · ヘラブナ White Crucian · トミヨ Ninespine ·
サヨリ Halfbeak · ナマズ Catfish · テナガエビ River Prawn · タイワンドジョウ Taiwan Snakehead · ハス Three-lips · カマツカ Pike Gudgeon ·
ワタカ Wataka · ツチフキ False Gudgeon · シマドジョウ Spined Loach · メゴチ Flathead · ハゼ Goby · マルタ Pacific Redfin · ヒガイ Higai ·
カムルチー Amur Snakehead · ソウギョ Grass Carp · ニゴイ Barbel Steed · ボラ Mullet · スズキ Sea Bass ·
イモリ Newt · カエル Frog · カナヘビ Grass Lizard · カメ Turtle · ヘビ Snake · ぬし River King
