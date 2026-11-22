# Kawa no Nushi Tsuri: Shizen-ha (PC Engine CD-ROM², 1992, Pack-In-Video): notes

Remake of the Famicom Kawa no Nushi Tsuri. Needs a System Card (testing with 3.0, `syscard3.pce`).

## Disc
| | |
|---|---|
| Tracks | 30. Track 1 audio warning, track 2 MODE1/2352 data, 3-30 audio |
| Track 2 file | 7,832,160 bytes (3330 raw sectors), SHA-1 `660c5950bf93a35a095b53116379b760875d07f3`, CRC32 `269CFEAF` |
| Layout | file sectors 0-73 zero, 74-223 mode-1 pregap, index 01 at file sector 224 (MSF 00:49:65, LBA 3590). File sector 0 = LBA 3366 |
| Data | 3106 user sectors (`~/ks/data.iso` = 2048-byte extraction from file sector 224). "Sector N" below = sector in that file |
| **Two copies** | the data is stored twice, second copy at +$5C6 (1478) sectors. The loader retries from the second copy on a read error. Sectors 0-1477 match 1478-2955 exactly except sector 2 (boot loader). **Patch both copies** |

## Boot
* Sector 1 IPL: load 1 sector from sector 2 to $4000, jump $4000, MPR2-6 = 00 01 02 03 04.
* $4000: MPR5/6 = bank([$FFF5])+6/+7, CD_READ ($E009) 8 sectors from sector $3A to $A000 (dh=1), jump $A000.
* $A000: jump table of ~100 entries.

## Text
* Shift-JIS, **stored as little-endian words** (`82 A0` あ is stored `A0 82`), each string ends with `00 00`.
  Window lines are 12 full-width characters, padded with `　` (8140); no line-break codes seen yet.
* Drawn with the System Card font: `JSR $E060` (EX_GETFNT, dh=0 = 16x16) at sector 5 +$AE8 and sector 61 +$BF0 (two overlays).
  So the English font has to live on the disc and be drawn by a hook in place of EX_GETFNT.
* `tools/scan_text.py data.iso` lists candidate strings (`out/scan_raw.txt`). First copy: ~521 terminated strings,
  ~385 unique, ~6,100 characters, in sectors 4-34 (dialogue, items, shops, battle), 60-65 (intro, animals), 83-84
  (fish list, fish names, cooking notes), plus a few elsewhere. Strings of 1-2 characters (コイ, フナ, ...) are missed by the scan.
* No plain pointer tables to these strings found (tried LE words, split lo/hi, immediates). Probably found by index
  by skipping terminators, or offsets relative to an overlay base. Needs a trace in the emulator.

## Tools (`tools/`)
* `dis6280.py file offset addr count`: HuC6280 disassembler.
* `make_disc.py track02.bin outdir`: test disc with the real data track and silent audio (track 1 padded to 3366 sectors so LBAs match).
* `emu.py`: headless libretro driver (Beetle PCE Fast, `apt install libretro-beetle-pce-fast`), needs `syscard3.pce` in the system dir.

## Memory map at runtime (field)
MPR: FF F8 80 81 82/84 86 87 00. Main program = banks $86/$87 at $A000-$DFFF (sectors 58-65).
Overlays: sectors 10-25 -> banks $82-$85 (8 KB each, mapped at $8000 when used); text chunks of 4 sectors
start at sectors 10, 14, 18, 22, 26, 30, 34; fish guide chunk at sector 82 ($8000). Super CD RAM ($68-$7F) unused by the game.

## Text engine (main program)
* `$C14E` (jump table `$A039`) prints the string at [$12] into the dialogue window: 12 cells per line, 2 lines,
  waits for a button, auto-wraps. Word = 2 bytes, read as $1A (first byte) / $1B (second byte).
  Control words by second byte: F0 number, D0 name/sub-string, C0-C6 print a variable, A0, B0, B2, B3 numbers,
  B1 = animal name from the table at $C886 (offsets) / $C89F (names, end = first byte 00).
* Callers: `LDX #hi / LDY #lo` then `STX $13 / STY $12 / JSR $A039` (405 of 521 strings found this way).
* `$BB87` draws one 16x16 cell: EX_GETFNT to $C12E (32 bytes, rows of 2 bytes), then `$BCA7` writes 4 tiles.
* Digits come from the SJIS table at `$C83E` (０-９), followed by the "...got away" string.

## English text engine (tools/build_patch.py)
* A word whose second byte is < $80 is two ASCII letters: `$BBE4` calls the new `glyph` routine, which maps
  bank $68 at MPR2 (with SEI) and copies two 8x16 glyphs from the font into $C12E. Kanji words still go to EX_GETFNT.
* The unrolled tile writer at `$BCA7-$BFBB` (788 bytes) is replaced by a loop; the hook lives in the freed space.
* Boot (sector 2, both copies) also CD_READs the font (sector 38) into bank $68. Needs the Super System Card.
* Strings are translated in place (`tools/tr_main.py`, `tools/encode.py`): 24 letters per line; lines are
  space-padded to 24 except the last. `tools/check_tr.py` reports strings that don't fit.

## Menus
* Menu labels are 16x16 glyphs from a 64-entry dictionary at sector 34 +$403 ($8403 in that overlay), loaded by
  $837E to VRAM $7000 (tile $700 + 4*index + quadrant). Window contents are BAT-word templates:
  status window at $DEB7 (12x9 words), area names at $DF8F (16 bytes per area), command menu copied by $ACF7 from [$04].
  Templates go to RAM $2F00 then VRAM via $AE1D. Button I opens the menu (RUN does not).
* `tools/cpu6280.py` interprets HuC6280 code from a savestate (stub VDC, pad, vsync IRQ) for tracing;
  `tools/bat_tmpl.py` shows templates as glyphs.

## Title menu (sprites)
- SAT buffer in RAM $2800 (DMA'd to VRAM SAT). Title menu = entries 14/15, 31/46, 63/54 (16x16, 4bpp planar,
  128 bytes each, raw on disc at data.iso 0x45700/0x45780, 0x45F80/0x46700, 0x46F80/0x46B00).
- Positions are set by straight-line code in the sector-34 overlay: `lda #$88 / sta $287a|$2972|$29b2` at
  0x11E94/0x11E9E/0x11EA8 (right column x). Patched to $80 so each row is a contiguous 32x16 strip.
- tools/title_sprites.py draws "Start / Resume / Guide" with a small hand-made proportional font.

## Fish guide (sector 82 → bank $80 at $8000)
- 202 stubs `ldx #hi / ldy #lo / jmp $8d75` at $87EF-$8D74 point at every string; pool $8D80-$95EF.
  Free tail $9D4E-$9FFF (690 bytes, zero at runtime). tools/fish_guide.py rebuilds the pool and re-points stubs.
- Detail window is 9 cells (18 chars). Numbers stay full-width kanji digits (one per cell).
- Note: Track.read() reads within one sector only (raw sectors are 2352 bytes); read multi-sector data sector by sector.

## Backup messages
- Sector 34 strings at 0x11271-0x11319: 22-char fixed lines, translated via DIALOGUE (padded to 22).

## Release
- release/: xdelta + IPS for Track 02, README_v0.9.txt (hashes, System Card 3.0 requirement).
- Patched Track 02: CRC32 077DEF71, SHA-1 6260c70357e2884c9500136f090bc3a2b19cf809.
- Title-menu cursor input in the emulator: HOLD=12 single step; HOLD=30 moves twice (auto-repeat).

## v0.9.1 findings
- Battle menu: second 命令 template (s065 0x20C93.., old copy s009) uses glyph slots 56-63, which the battle
  code reloads ($99A0 in the sector-10 overlay, 8 glyphs 戦う弁当する逃げ from $9E24 to VRAM $7E00).
  Labels: Fight / Eat / Run (tr_menus.py). They had been blanked as "placeholders" in v0.9.
- Catch message names: sector 990 chunk (lives in ADPCM RAM, copied to $8000). $8254: base by area $27E5 +
  offset byte $871E[fish]; names end with D0D0 (continue with sub-string by $26D0). tools/catch_names.py
  repacks them; overflow goes to the zero tail $9D6E-$9FFF.
- Using Specs from Items only opens an empty message window (no print call); same code as the Japanese game.
- Signs/banner: uncompressed BG tiles in several tilesets (first at data.iso 0x6D000 = tile $600);
  tools/signs.py redraws them and replaces every copy by content. Tiles are cached in RAM: test from a fresh boot.
- encode() strips leading spaces when reflowing; build uses reflow=False for strings starting with a space.

## Title logo (v0.9.3)
- 44 logo sprites (SAT entries, 8x6 grid at x24,y8, holes at row0 cols 0/3/7 and row3 col6); patterns at data.iso 0x45000 + entry*128.
- Title sprite palette 0 at data.iso 0x14DE80; colour 1 blinks (cursor), 3/15 shared. tools/logo.py.

## v0.9.4 title logo (the tester's design)
- tools/logo.py resamples art/logo_mockup.png to 200x60, 13 colours (palette 0 at 0x14DE80, colours 2,4-14), and covers it with 43 freely placed 16x16 sprites from the 44 original logo SAT entries; positions are patched in the sector-34 overlay immediates (lda #imm / sta $28xx). Screen pos x28,y6. `python3 logo.py out.png` writes a preview.
- Release v0.9.4: patched Track 02 CRC32 89D386DB.

## v0.9.5
- the tester prefers English names over romanised Japanese. Fish renamed in fish_guide.FISH (also feeds catch_names): Cherry trout, Red-spot trout, Topmouth gudgeon, Slender/Biwa/Paddy gudgeon, Bagrid catfish, Striped minnow, Ricefish, Amur stickleback, White crucian, Three-lips, Weed chub, Lake gudgeon, Redfin dace; モロコ Gudgeon; タヌキ Raccoon.
- signs.py uses Umi's plaque art (INN, hook, fish) and draws a 3-ball dango skewer on the banner (white/tan/green, banner palette: 0 black,1 red,2 brown,4 tan,6 green,c dark,f white).
- Village tiles are cached: test signs from a fresh boot (run_intro -> nb -> nb2 -> nb3 -> vil).

## v0.9.6: River King glossary (2026-10-27)
- fish_guide.FISH, catch_names, tr_main ANIMALS/dialogue, tr_menus follow glossary/series_glossary.md (Title Case
  River King names; Tanuki; Arai/Kabayaki/Bottarga...; ねりえ = Paste). Exceptions for slot width are listed there.
- Rebuilding the v0.9.5 sources gave CRC32 191B87A3 again, so the build is reproducible. v0.9.6 patched Track 02:
  CRC32 FF28D7BD. Patches: IPS via tsuri-tarou/tools/make_ips.py (generic), xdelta3 -S lzma.
- Emulator in a fresh container: apt install libretro-beetle-pce-fast; syscard3.pce is upload bd30a578 in
  uploads/hearth. Title menu appears ~frame 980 after tapping RUN at frame 300; DOWN x2 + I = Guide.
