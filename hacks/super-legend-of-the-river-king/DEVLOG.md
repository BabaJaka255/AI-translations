# Development log: Super Legend of the River King

This log covers how the English translation of *Kawa no Nushi Tsuri 2* (Super Famicom, 1995) was made, written from the chat in which it was built (October–November 2026).

Two people did the work:
- **Claude (Anthropic):** the analysis, code and first-draft translation, working in a cloud sandbox with Python and no emulator.
- **"The tester":** a human working in the Mesen-S emulator, who ran every build, sent screenshots and memory dumps, made the naming and art calls, drew the title logo and edited the script.

Version numbers are the test patches sent during the chat (v0.1 → v1.3).

---

## 0. Starting point

The tester asked how to start a Japanese→English SNES translation, then asked how much of it could be automated if they handed over a legally dumped ROM of *Kawa no Nushi Tsuri 2* (the Super Famicom game, not the Game Boy one).

Claude set out the division of labour at the start:
- **Claude:** analysis, tools and the first-draft translation.
- **The tester:** running builds, screenshots, graphics judgement and playtesting. Claude cannot run or watch the game.

**Prior work.** Claude suggested checking romhacking.net and Data Crystal for an existing translation or documentation. Neither of us reported finding one, and no outside documentation was used. Everything below was worked out from the ROM, the code and the tester's dumps.

---

## 1. Finding the text (no patch yet)

- **ROM check.** Claude's first header scan read the wrong offsets and found no valid header. A second scan found it at `0x7FC0`: LoROM, 12 Mbit, valid checksum when mirrored to 16 Mbit, no copier header.
- **Search for plain text.** There was no Shift-JIS or ASCII text. A *relative search* for 14 common kana words returned only one hit, which turned out to be a false positive in compressed data.
- **The text gave way once the tester sent a dump.** They sent a Mesen-S WRAM/VRAM/CGRAM dump of the first dialogue box, a screenshot, and an OCR of its first line (山奥のせせらぎから…).
  - Claude matched the on-screen glyphs against VRAM, then VRAM against the ROM. That located the 16×16 1bpp font at ROM `0x30000`, the glyph blitter at `$82:8956`, and the three text-drawing loops.
  - Claude read the single-byte table (kana, digits, punctuation) by eye from a rendered font sheet.
- **Kanji table.** Claude matched the font's glyphs against Noto Sans CJK.
  - A naive match got 1 of 7 known kanji right. Normalising both sides to their bounding boxes got 6 of 7.
  - The ~276 low-confidence glyphs were read by eye in batches, with script context, then checked again on verification sheets. That pass corrected 7 more. All 523 kanji used by the script have a reading.
  - Some misreads survived anyway (for example 昆虫 read as 貝虫); they were found later while making the glossary.
- **Script.** Searching for the first string's address (`05:C169`) found a 537-entry pointer table at ROM `0x2BAD5`. It covers 526 unique strings with control codes `CC`–`DF`.
  - Claude wrote a dumper (`script.json`) and a reinserter that rebuilt the text region **byte-identical** to the original. That became the first regression check.
- **Setback.** The sandbox was reset between sessions and the first disassembler was lost, so Claude rewrote a compact 65816 disassembler (`tools/dis65816.py`).

## 2. First English text (v0.1–v0.4)

- **v0.1.** Claude wrote a small 65816 interpreter (`tools/cpu65816.py`) that runs the game's own dialogue routine and renders the result. That way patches could be checked before the tester saw them.
  - The first patch expanded the ROM to 2 MB and added an 8×16 English font (X11 `koi8x16`), one letter per 8-pixel column, 23 columns per line.
  - It hooked the main dialogue loop and translated the opening scene.
  - **Tester:** "It works! The text fits the box fine, letters aren't garbled, scrolling works."
- **v0.2.** Claude translated about 440 strings. A width checker refuses any line over 23 columns.
- **v0.3.**
  - **Name lists.** Claude found the fish, bait, hook, float, lure, rod, fly, food, item and creature name lists in bank 5, and hooked the second text loop so inserted names (`{D8}` fish, `{D9}` creature) come out in English.
  - **Relocation.** English strings went to new banks through a sorted *old pointer → new pointer* table that the hooks look up (`xl`). The tester had pointed out the RPG-style creature battles, and those names were in the same lists.
- **v0.4.**
  - Translated the fish descriptions, hooking the third loop, which word-wraps.
  - Translated the area names and NPC names.
  - **Tester reported:** the descriptions didn't wrap correctly, rod names in the shop were still Japanese, and the squirrel was missing.

## 3. Shops, copies and the English marker (v0.5–v0.7)

- **v0.5.**
  - **Wrapping fix.** Claude's guessed line width was wrong. The real one (22 columns on the first line, after the 生活: label, then 27) fixed the descriptions.
  - **Squirrel.** It was missing from the creature list.
  - **Copied strings.** Some code copies a string into a buffer before drawing it, which skipped the lookup. Every English string now starts with an unused byte (`DF`) that switches the renderer to English, and the copy sites were hooked too (`cp1`, `cp3`).
- **The tester sent shop and battle dumps:**
  - rods and hooks were still Japanese;
  - the fly-shop price line was garbled.
- **v0.6.**
  - **Rods and hooks.** Nine more copy sites were found and hooked.
  - **Garbled price.** The English flag leaked into the price digits (bytes below `0x20`). Those bytes now always draw from the Japanese font.
  - **Tester:** "Items in the shops are now translated", apart from two stragglers.
- **v0.6.1 / v0.6.2.** Two name ranges started a few bytes too late. That missed the first topwater lure and the earthworm bait (ミミズ; Claude's first guess at it was wrong).
- **Localization choice.** The tester asked for "a sensible localization". Claude asked whether fish without everyday English names should get English names, Japanese names, or a mix, and the choice was English names.
- **v0.7.** English common names throughout, for example:
  - Masu Trout / Masu Salmon
  - Redspot Trout / Salmon
  - Char, Sweetfish, White Crucian

  Japanese names were kept only where there's no English one (Itomoroko, Mugitsuku, Tamoroko, Wataka, Higai). Lines that insert a long fish name were reflowed.

## 4. Menus and pictures of text (v0.8–v0.9.2)

- **v0.8.**
  - **Pre-drawn labels.** Most menu labels turned out to be pictures in ROM bank 7, copied to VRAM, not text. Claude redrew them in the dialogue font with touch-aware kerning (`build/labels.py`) and previewed every label as an image.
  - **Shortened labels.** "Terrestr.", "Tackle" and "Spin Rod" were shortened to fit.
  - **Tester:** "The new menus look great… It'd be great to see all the incidental Japanese replaced."
- **v0.9.**
  - Translated the yen/fish counters, the title menu, the postcard prompts and the ranking header.
  - **Status labels.** The status-window labels (体力/お金/経験 → HP/Yen/EXP) and the battle title (命令 → Cmd) were painted over by an extra DMA each time the window opened.
- **Tester reported:**
  - "Cmd" wiped the window's top border;
  - creel fish names were still Japanese;
  - map titles were cut off at 6 letters.
- **v0.9.1.** Areas renamed to fit 6 letters (Alpine, Plains, Coast) and the border restored.
  - **Tester:** "Cmd" had regressed to Japanese. The game reloads its window graphics on some screen changes, which undid the overlay. **Dead end.**
  - The tester then sent dumps of the title, character select, Fishing Note contents and creel screens.
- **v0.9.2.**
  - **LZSS.** Claude disassembled the decompressor at `$00:E5C2` and wrote a decoder (`build/lzss.py`).
  - **Window font.** The window UI font was unpacked, edited (HP/Yen/EXP, Cmd, ¥, blank 尾) and stored in expanded ROM, with all five loaders repointed. The DMA overlay was dropped (`ui_hooks.py` is kept for reference only).
  - **Creel names.** They now go through the lookup.
  - **Contents page.** Its tilemap was rebuilt so the English labels have room.
  - **Tester:** "Everything looks great!"

## 5. Keyboards (v0.10–v0.11.1)

- **v0.10. English name entry.**
  - Pre-rendered A–Z / a–z / digits / symbols keyboard blocks replace the kana and kanji palettes.
  - The selection tables were replaced and names raised from 4 to 8 letters.
  - The dakuten keys were disabled.
  - Stored names are always drawn in English.
  - Default names are Taro, Kyoko, Yuzo and Noriko.
  - Claude tested key selection and name drawing in the simulator before sending it.
  - **Tester:** "works without a hitch", and an 8-letter test name fit.
- **Tester found next:**
  - long fish names cut off in the fishery window;
  - the postcard keyboard, with ?! squeezed into one cell;
  - the postcard keyboard's three-way mode switch. They suggested turning its modes into English keyboards.
- **v0.11.**
  - **Postcards.** UPPER/lower/symbol modes, 28 letters per line, and "Line" instead of "Enter", which was too wide.
  - **Fishery window.** Widened to 13 letters, with eight short names.
  - **Character select.** The relation labels 兄/妹/父/母 were removed, which Claude proposed and the tester agreed to.
- **v0.11.1.** Fixed a palette gap the tester spotted next to names on character select.

## 6. Title logo and naming (v0.12–v0.14, v0.17)

- **Title.** The tester suggested a "Super River King" graphic and asked for "River Master" to become "River King", following the existing Western releases.
- **v0.12.** Claude generated a "SUPER RIVER KING" logo from DejaVu Sans in the original logo's palette, and replaced "River Master" in about 20 strings.
- **The name.** The tester sent the US Game Boy Color logo and proposed the title *Super Legend of the River King*.
  - Claude agreed and recommended dropping the "2", since *Legend of the River King 2* is a different Western game.
  - The tester also noticed the father's letter ended at "Sincerely,". The Japanese has no signature either, so Claude added "The villagers".
- **v0.13.** A Game Boy-style logo built from Poppins. The sandbox couldn't download display fonts (network blocked), so local fonts were used.
- **Logo kit.** The tester asked whether they could draw the logo themselves. Claude made a kit (blank 192×48 canvas, current logo, screen layout) and a PNG importer that reduces to 15 SNES colours.
- **v0.14.** The tester's logo went in; it had about 3,400 colours, reduced automatically to 15.
- **v0.17.** The tester's revised logo, with a white border and a reworked "Super".

## 7. Signs, maps, banner and icons (v0.15–v0.18)

- **Graphics survey.** Claude scanned the ROM for every LZSS loader, rendered each block, and wrote a matcher that compares screenshot tiles with ROM tiles regardless of palette.
- **v0.15.**
  - **Town plaques.** From the tester's Stream and Alpine screenshots, Claude found the three plaques (宿 inn, 魚 fish shop, 釣 tackle). Frame-edge signatures then located them in all six area tilesets.
    - The first colour-mapping approach produced false matches and was replaced.
    - Each plaque has a 12×12 space: "INN" fits, so the other two became a fish and a hook picture.
    - The tilesets are recompressed with a new greedy LZSS compressor, round-trip tested.
  - **Map labels.** The tester noticed the Fishing Note map draws small fish-name labels on the fly. Those use a tiny katakana font, now replaced with an 8×8 English one (X11 `koi5x8`).
- **Tester feedback:** the labels were too long. They suggested dithering the dark background, and noted that the red banner in Stream and Alpine is one object and doesn't animate.
- **v0.16.**
  - **Map labels.** Up to 9 letters, with map-only short forms. Instead of dithering, Claude gave the letters an outline on a fully transparent background.
  - **Banner.** An automatic screenshot search was too slow and was stopped.
- **v0.17.**
  - **Banner found.** The tester sent a dump next to the banner. It's on a second background layer within the town tileset, which is why the first search missed it.
  - **Banner redrawn.** Claude redrew だんご as a dango skewer in four area tilesets.
  - **Warp code.** The tester found a warp code online and swept every area. They found nothing left except the Stereo/Mono item icon.
- **v0.18.**
  - **Icon location.** The item icons are stored *uncompressed*, so the LZSS-based searches had never looked at them. A plane-mask scan of the raw ROM found the sheet at `0x56000`.
  - **New icons.** Claude redrew the records with STEREO/MONO in a 3×5 pixel font.
  - **Tester:** "It all looks right!"

## 8. Script pass and 1.0

- **v0.19.** Claude read the whole script against the Japanese; there's no spellchecker in the sandbox. About 35 lines changed:
  - **Leftover romaji:** amago, akame, big eel, Uodome and others now use the glossary names.
  - **Name clash:** a pig called the golden carp "the river's king", which clashed with the River King; it now says "champion of the river".
  - **Small fixes:** punctuation and capitalisation in the descriptions.
- **v1.0.** Claude applied the patch to an untouched ROM and confirmed it matched the build byte for byte, then wrote the README with checksums.

## 9. After release (v1.1–v1.3)

- **v1.1. Script workbook.** The tester asked to edit the script themselves. Claude built `script_io.py`:
  - **Export:** an `.xlsx` with Japanese and English, per-line limits, and a live "longest line" check.
  - **Import:** validates the workbook and writes `user_edits.py`.

  The tester made **43 edits**, including fuller early scenes and speaker names. While adding the import checks, Claude found that four end-of-game letters overflowed the 5-line postcard frame. One of them was Claude's own v1.0 text. All four were reflowed, and the limit is now checked at build and import time.
- **v1.2.**
  - **Farmer's line.** The tester found the NPC and suggested the wording "Most farmhands take to fishing this time of year".
  - **Secret name.** The tester learned online that naming the brother つり太郎 unlocks a stocked tackle box. Claude found the 8-byte name compare at `$81:B077` and proposed **FishTaro** for the English keyboard. The tester confirmed it works.
- **v1.3. Empty gear slots.** The tester found Japanese placeholder text (サオ, ウキ, オモリ, ハリ, 無し) in empty gear slots, reached by pressing Select in the gear window.
  - Claude found the raw sprite cells by plane-mask scanning and redrew them as ROD, FLOAT, SINKER, HOOK and NONE in a 5×5 pixel font. SINKER uses a 5×4 variant so it fits.
  - Checked in the graphics data only; **not confirmed in the emulator** before release.
- **Afterwards.** A toolkit (tools, fonts, engine notes) and a 393-entry name glossary (`docs/glossary.*`) were made for future fishing-game translations. Then this folder was published.

---

## Testing

**Setup.** All testing was done by the tester in **Mesen-S** on a PC. Nothing was tested on real hardware or a flash cart.

**How the testing worked.**
- The tester applied each build to a clean ROM and played the affected screens.
- They sent screenshots and, when asked, VRAM/CGRAM/WRAM dumps. Those dumps are in `src/data/dumps/`, and the screenshots in `docs/images/screenshots/`.
- Late in the project they used the game's area-warp code to sweep every area for leftover Japanese.
- The game was **not** played through start to finish in one run.

**Bugs the tester reported, and their fixes:**

| Reported | Cause | Fixed in |
|---|---|---|
| Fish descriptions wrap wrongly | Guessed line width was wrong | v0.5 |
| Rods, hooks untranslated in shops; squirrel untranslated | Copy routines bypassed the lookup; name missing | v0.5 / v0.6 |
| Garbled fly-shop price | English flag leaked into digit bytes | v0.6 |
| One lure and one bait untranslated | Name ranges started too late | v0.6.1 / v0.6.2 |
| "Cmd" erased the window border | Overlay overwrote the top row | v0.9.1 |
| Creel fish names Japanese | Creel copies the name itself | v0.9.2 |
| Map titles cut at 6 letters | Fixed-width title | v0.9.1 |
| "Cmd" back to Japanese | Window graphics reloaded; overlay approach abandoned | v0.9.2 |
| Long fish names cut off at the fishery | 12-tile field | v0.11 |
| ?! in one key; postcard keyboard Japanese | Postcard keyboard not yet replaced | v0.11 |
| Unhighlighted tiles on character select | Wrong palette on blank tiles | v0.11.1 |
| Letter ends at "Sincerely," | Original has no signature | v0.13 |
| Map labels too long, dark box | 8 px per letter, opaque font | v0.16 |
| Japanese on the shop banner, Stereo/Mono icon, gear-slot placeholders | Graphics not yet found | v0.17, v0.18, v1.3 |

**How Claude checked its own work:**
- **Simulator:** a 65816 interpreter running the game's real text routines, used to render boxes and test keyboards, name drawing and helpers.
- **Width checks** on every line at build time.
- **Regression:** every string rendered with the previous patch and the new one, and the two compared.
- **Round trips:** the original script reinserted byte for byte, and the LZSS compressor checked against the decoder.
- **Original-byte checks** before every hook.
- **Final check:** re-applying each release IPS to a clean ROM and comparing it with the build.

**What Claude couldn't do:** run or watch the game, judge timing and animation, see how sprites overlap on the real screen, or playtest. Every preview image Claude sent was a mock-up built from dumps, and the tester's screenshots were the only real confirmation.

---

## Decisions and who made them

| Decision | Made by |
|---|---|
| English common names for fish; Japanese only where none exists | Chosen when Claude asked (English names) |
| "River King" (not "River Master"); Western Game Boy naming | Tester |
| Title *Super Legend of the River King* | Tester proposed; Claude agreed and suggested dropping "2" |
| Title logo art (both versions) | Tester (drawn by hand); Claude converted it |
| Asking for gear-slot, banner, sign, icon and map fixes; finding the warp code and secret name | Tester |
| Rewording of one farmer's line; 43 script edits | Tester |
| Draft translation of all text | Claude |
| Area names cut to 6 letters (Alpine, Plains, Coast) | Claude, forced by the map title width |
| Removing 兄/妹/父/母 labels | Claude proposed; tester agreed |
| Sign and banner pictures (fish, hook, dango) instead of words | Claude (12×12 / narrow space) |
| Transparent, outlined map labels; map-only short names | Tester asked for less background; Claude chose outline + transparency |
| "The villagers" signature on the father's letter | Claude |
| Secret name "FishTaro" | Claude proposed; tester approved |
| Default names Taro, Kyoko, Yuzo, Noriko | Claude (romanised originals) |
| Yen shown as "yen"/¥, fish counter 尾 dropped | Claude |
| Short forms "W.Crucian", "Terrestr.", "Spin Rod" | Claude (space limits) |

---

## Known gaps and ideas

- **Not hardware-tested.** It should be tried on a real SNES with a flash cart. The patch expands the ROM to 16 Mbit LoROM.
- **No full playthrough.** Late-game scenes and endings were checked in the simulator, not seen in play.
- **v1.3 gear labels** weren't confirmed in the emulator.
- **Uncertain text:**
  - the シビ hook is still "Shibi" (meaning unclear);
  - one cooking note (つけやき・煉白) has kanji that couldn't be confirmed;
  - the 〒 postal mark is kept on postcards.
- **Old saves** from the Japanese game show stored names as garbled letters.
- **IPS size.** The IPS is large because it includes the whole expanded region; a BPS would be smaller and checksummed.
- **Map labels** still use 8 px per letter. A variable-width renderer would let more names appear in full.
- **For related games** (other Nushi Tsuri titles), start with `docs/ENGINE_NOTES.md` section 5 and the porting tools in `src/tools/`. The LZSS format, text encoding and hook patterns are likely to carry over, but every address has to be found again.
