# Hamster Club art pack: lettering to redraw

> **Status (v0.12, 2026-11-02):** every sheet here has an English version in
> `gfx/edit/art/`, drawn by `tools/make_art.py` (one function per sheet; run
> `python3 tools/make_art.py trick04` to redraw one). To change a word, edit
> that function and rerun it, or paint over the file in `gfx/edit/art/` by
> hand. Tricks 19 and 57 have no words (only sweat and pain marks) and were
> left as they are.

Every graphic in this folder has Japanese lettering baked into the pixels. Each
`.png` sheet is the exact set of tiles the game loads, ripped straight from the
ROM. Redraw the lettering in English, and the build puts your version back in.

## How to hand them back

1. Copy the sheet into `gfx/edit/art/` under **the same file name**.
2. Edit it there. Leave the rest of the image alone where you can.
3. Run `rhtk build` (or send the files to me and I'll build and test them).
   The build only reinserts the sheets it finds in `gfx/edit/art/`, so you can
   send them one at a time.

## Rules for editing a sheet

- **Keep the image size and indexed-color mode.** Don't convert to RGB.
- **Each 8x8 tile has 4 colors.** The palette has 16 rows of 4 colors, and each
  tile is shown in the row the game uses for it. Only a color's position within
  its row (0-3) is stored, so pick colors from the same row as the tile you
  are painting, or the tile will change color in the game.
- **In sprite sheets (`obj8x16`), color 0 of each row is transparent.**
  Sprite sheets are laid out as 8x16 cells, the way the game draws them.
- **You can't add tiles.** The lettering has to fit inside the tiles that are
  already there. Blank or unused tiles in a sheet are fair game.
- **Some tiles are drawn in more than one place.** A blank tile, or a letter
  that repeats in a strip (for example the じたばた border in trick 33), is one
  tile used many times. If you change it, it changes everywhere.
- The `*_screens.png` files are screenshots, for reference only. They show
  where each piece of lettering appears. They are not reinserted.

If a sheet is awkward to work in, send me a drawing of the whole screen (at
160x144, or 2x) and I'll cut it into tiles myself.

## The list

### Title and boot screens

| Sheet | What it is | Japanese | Suggested English |
|---|---|---|---|
| `title_logo_bg8800.png`, `title_logo_bg9000.png` | Title screen logo (see `title_screen.png`) | ハムスター倶楽部 | HAMSTER CLUB |
| `boot_logos_bg9000.png` | Copyright line and the Jorudan logo (see `boot_screen_credit.png`, `boot_screen_logos.png`) | ©めで鯛 / あおば出版, ジョルダン | © Medetai / Aoba Shuppan, JORUDAN |
| `boot_logos_bg8800.png` | Nekogumi (the developer) logo lettering | ねこぐみ | NEKOGUMI |

"PUSH START" on the title screen is already in English.

### Weekly report events

| Sheet | What it is | Japanese | Suggested English |
|---|---|---|---|
| `accident_banner.png` (sprites) | Banner that slides in before bad news (see `accident_screens.png`) | アクシデント | ACCIDENT! (or "UH-OH!") |
| `event_labels.png` (sprites) | Two-kanji labels that slide in from both sides, one 32x16 row each | 出産, 死亡, 事故, 病気, 逃亡 | BIRTH, DEATH, ACCIDENT, SICK, ESCAPE |
| `illness_picture.png` | Picture shown when a hamster gets sick (see `illness_screen.png`) | red ケン marks, written top to bottom (ケンケン is a dry, hacking cough) | KOFF (a demo redraw is in `gfx/demo/`) |

About `event_labels.png`: each label is two 16x16 halves. The left half slides
in from the left and the right half from the right, and they stop well apart
(see `accident_screens.png`). So an English label has to be split across two
16x16 squares with a gap in the middle, for example "SI" + "CK", or one short
word per half, for example "RAN" + "OFF".

### Trick animations

These play when a hamster performs a trick, mostly during the judged contests.
The trick number is the one in the file name; the name column is the trick's
name in the game's trick list. Readings marked "possibly" are guesses from the
tiles, because that lettering only shows up in frames I didn't catch on screen.
Where I couldn't read it at all, the English is your call.

| # | Trick | Sheet | Japanese lettering | Suggested English |
|---|---|---|---|---|
| 1 | オラオラ (Jab-jab) | `trick01_0F9450.png` (17 tiles, linear) | オラ / オラオラ (a punching cry) | POW / POW POW |
| 2 | むっしむっし (Fidget) | `trick02_0F9570.png` (126 tiles, linear) | strip along the top and bottom edges; looks like むし (from むっしむっし) but hard to read | SCOOT SCOOT |
| 3 | もしゃもしゃ (Ruffle) | `trick03_0F9D70.png` (128 tiles, linear) | もしゃもしゃ, repeated (rustling) | rustle rustle |
| 4 | だきつき (Hug) | `trick04_0FAD20.png` (68 tiles, obj8x16) | ぎゅ〜っ with a heart (squeeze); only in the sheet, not in the frames I caught | squeeze~ ♥ |
| 5 | こうちょく (Freeze) | `trick05_0FB8D0.png` (72 tiles, obj8x16) | カッチン (going stiff); only in the sheet | FROZEN |
| 6 | ずるずる (Slide) | `trick06_0EC000.png` (87 tiles, linear) | strip along the edges: ずるっ (sliding) | SLIDE |
| 8 | ちょーだい (Gimme) | `trick08_0ED7C0.png` (40 tiles, obj8x16) | ちょ… ちょーだい ("gimme") | Gim… gimme |
| 9 | ちょーだい (Gimme) | `trick09_14BD20.png` (28 tiles, obj8x16) | ちょ〜… だいっ (a drawn-out "gimme") | Gim~… me! |
| 10 | こうちょく (Freeze) | `trick10_147B60.png` (26 tiles, linear) | カッチーン (frozen stiff) | FROZEN! |
| 11 | すなあび (Sandbath) | `trick11_16DDA0.png` (234 tiles, obj8x16) | ばっ ばっ ばっ (kicking sand) | fwsh fwsh fwsh |
| 15 | ぷりぷり (Wiggle) | `trick15_150740.png` (101 tiles, obj8x16) | ぽてっ (plop) and プッ | plop / pfft |
| 16 | おろろろろ〜 (Fluster) | `trick16_150000.png` (116 tiles, obj8x16) | おろろろろ〜 (flustered wail) | uh-uh-uh-uh~ |
| 17 | むしゃむしゃ (Munch) | `trick17_154820.png` (128 tiles, linear) | むしゃ むしゃ | munch munch |
| 18 | よじよじ (Climb) | `trick18_157840.png` (120 tiles, obj8x16) | よじ (clambering) | climb |
| 19 | ちょーだい (Gimme) | `trick19_16C000.png` (128 tiles, linear) | no lettering in the frames I caught; check the sheet | your call |
| 20 | さかさね (Belly-up) | `trick20_13E7F0.png` (86 tiles, linear) | ぐ〜っ (snoring) | snore~ |
| 21 | ゆびあくしゅ (Shake) | `trick21_15F220.png` (124 tiles, obj8x16) | ぎゅっ in a speech bubble (squeeze) | squeeze |
| 23 | けづくろい (Groom) | `trick23_15D7F0.png` (230 tiles, obj8x16) | くる (rubbing in circles) | rub |
| | | `trick23_16FA70.png` (69 tiles, linear) | (same trick, second sheet) | |
| 24 | かえるとび (Leapfrog) | `trick24_15CFF0.png` (128 tiles, obj8x16) | pink lettering in the sheet, possibly ぴょん (hop); not in the frames I caught | boing |
| 28 | びたっ (Splat) | `trick28_173C00.png` (58 tiles, obj8x16) | びたっ (splat) | SPLAT |
| 29 | ころがる (Roll) | `trick29_162B50.png` (151 tiles, obj8x16) | コロン (rolling over) | roll |
| 30 | ねる (Sleep) | `trick30_1625A0.png` (91 tiles, obj8x16) | ぐぅ (sleeping) | zzz |
| 33 | じたばた (Flail) | `trick33_160000.png` (128 tiles, linear) | strips along the sides: じたばた (flailing) | flail flail |
| 36 | ぐうぐう2 (Snooze2) | `trick36_1584C0.png` (101 tiles, obj8x16) | ぐぅ (sleeping) | zzz |
| 37 | ばしっ！ (Whack!) | `trick37_158000.png` (76 tiles, obj8x16) | ばしっ (whack) | whack! |
| 39 | おらおら2 (Jab-jab2) | `trick39_16BA10.png` (94 tiles, linear) | strips along the edges: オラオラ (punching cry) | POW POW |
| 42 | のびキャッチ (Catch) | `trick42_16C8C0.png` (128 tiles, linear) | びょ〜ん (stretching out) | stre-e-etch |
| 43 | ぼてぼて (Waddle) | `trick43_183E10.png` (27 tiles, linear) | ぼて ぼて (waddling) | waddle waddle |
| 44 | あわあわ (Panic) | `trick44_140000.png` (128 tiles, linear) | すぽっ in a speech bubble (popping into the cup) | pop! |
| | | `trick44_13DCF0.png` (55 tiles, obj8x16) | (same trick, second sheet) | |
| 45 | かえるとび (Leapfrog) | `trick45_1722F0.png` (122 tiles, obj8x16) | びょ〜ん (springing up) | boing~ |
| | | `trick45_177AD0.png` (75 tiles, linear) | (same trick, second sheet) | |
| 46 | ひじかけ (Lounge) | `trick46_17D070.png` (128 tiles, linear) | もぐもぐ (chewing) | munch munch |
| 47 | よじよじつつ〜 (Climb~) | `trick47_176D20.png` (219 tiles, obj8x16) | よじ よじ (clambering) | climb climb |
| 48 | ぐりぐり (Nuzzle) | `trick48_176640.png` (110 tiles, obj8x16) | ぐり (rubbing) | rub |
| 49 | ばしばし (Smack) | `trick49_174F90.png` (123 tiles, obj8x16) | ばしっ (smack) | smack! |
| 51 | ゴンッじわー (Bonk) | `trick51_139DF0.png` (128 tiles, linear) | じわ〜 (pain welling up) | owww~ |
| 52 | かえるとび？ (Hop?) | `trick52_1839F0.png` (11 tiles, obj8x16) | small lettering in the sheet I can't read with confidence | your call |
| 53 | コロン (Tumble) | `trick53_17A980.png` (120 tiles, obj8x16) | すぽっ and コロン… in the sheet (pop, then roll) | pop / roll… |
| 54 | ぬぼ〜っ (Daze~) | `trick54_17F220.png` (118 tiles, obj8x16) | ぬぼっ (blank, dazed look) | duh |
| 55 | つめこみ (Cram) | `trick55_153210.png` (174 tiles, obj8x16) | ぱっ in a bubble, then もぐもぐ | ! / munch munch |
| 57 | びっくりかみつき (Bite!) | `trick57_17C000.png` (142 tiles, obj8x16) | small lettering in the sheet I can't read with confidence | your call |
| 58 | うなぎ (Eel) | `trick58_138F30.png` (236 tiles, obj8x16) | small lettering in the sheet I can't read with confidence | your call |
| 59 | ちょうだっしゅ (Dash) | `trick59_186D30.png` (127 tiles, obj8x16) | lettering in the sheet I can't read with confidence | your call |
| 61 | ちまちまぐい (Nibble) | `trick61_187BF0.png` (28 tiles, obj8x16) | ちま ちま, then もぐ (nibbling) | nibble nibble |
| 62 | くつろぎ (Relax) | `trick62_13E060.png` (121 tiles, obj8x16) | small lettering in the sheet (possibly はっ) | your call |
| 63 | ひくひく (Sniff) | `trick63_1427A0.png` (128 tiles, obj8x16) | lettering in both sheets (possibly はっ); not in the frames I caught | your call |
| | | `trick63_181650.png` (128 tiles, linear) | (same trick, second sheet) | |
| 64 | けづくろい (Groom) | `trick64_167CF0.png` (30 tiles, obj8x16) | ぽり (scratching) | scratch |
| 65 | どこどこ？ (Where?) | `trick65_147D00.png` (35 tiles, obj8x16) | なで (petting), handwritten; only in the sheet | pat pat |
| 67 | うふっ♡ (Tee-hee♡) | `trick67_143D90.png` (26 tiles, obj8x16) | ぬぼ〜 (dazed) | duh~ |
| 68 | ピコピコ (Earflick) | `trick68_16FEC0.png` (20 tiles, obj8x16) | ぴこ (ear twitch) | flick |
| 69 | ぢぢぢぢぢ (Chitter) | `trick69_13CA70.png` (192 tiles, obj8x16) | ぢ, ぢぢ (chittering) | chi chi |
| 70 | ゆらゆら (Sway) | `trick70_17DE30.png` (117 tiles, obj8x16) | ゆら〜っ (swaying) | sway~ |
| 73 | おおあばれ (Rampage) | `trick73_167ED0.png` (16 tiles, obj8x16) | ぢ ぢ (chittering) | chi chi |
| 75 | プリプリあばれ (Tantrum) | `trick75_148EF0.png` (128 tiles, linear) | strips along the edges: プリプリ (in a huff), plus ぢ | HUFF HUFF / chi |
| | | `trick75_163F00.png` (16 tiles, obj8x16) | (same trick, second sheet) | |
| 76 | うなぎ (Eel) | `trick76_14B3F0.png` (118 tiles, linear) | pattern along the edges, possibly repeated lettering | your call |
| 77 | あくび (Yawn) | `trick77_14FA60.png` (82 tiles, obj8x16) | ふぁ〜ん (yawn) | yaaawn |
| 80 | あとずさり (Back up) | `trick80_145EF0.png` (84 tiles, obj8x16) | white lettering in the sheet, possibly ずりずり (shuffling back) | shuffle |
| 81 | くさいくさい (Stinky) | `trick81_146430.png` (96 tiles, obj8x16) | lettering in the sheet, possibly くさ… and しゅ〜っ (stinky, pssh) | stinky / pssh |
| 82 | ハミガキオラオラ (Brush!) | `trick82_146A30.png` (71 tiles, obj8x16) | lettering in the sheet, possibly ゴシ (scrubbing) | scrub |
| 84 | ピコピコ (Earflick) | `trick84_153F00.png` (12 tiles, obj8x16) | purple and orange lettering in the sheet | your call |
| 85 | ぶらぶら (Dangle) | `trick85_149EB0.png` (99 tiles, linear) | lettering in the sheet (possibly がっ) | your call |
| 86 | とろーん (Drowsy) | `trick86_14A4E0.png` (128 tiles, linear) | ぽか (bonk), plus a dizzy squiggle | bonk |
| | | `trick86_187FD0.png` (2 tiles, obj8x16) | (same trick, second sheet) | |
| 87 | ぐわーん (Dizzy) | `trick87_13B7F0.png` (95 tiles, obj8x16) | ぐわ〜ん, written top to bottom (dizzy) | woozy~ |

Tricks with no lettering at all are not included. Trick 56 has a small ぴくっ
(twitch) that I couldn't pin to one tile set, so it's left out for now.

## Where each sheet goes in the ROM

The offsets, tile counts and layouts are in `project.json` under `gfx`. Each
sheet also stores its tile count in the PNG (`rhtk_tiles`), so the build
writes back exactly the bytes it ripped.
