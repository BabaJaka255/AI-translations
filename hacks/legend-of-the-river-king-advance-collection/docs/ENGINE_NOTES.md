# Kawa no Nushi Tsuri 3 & 4 (GBA): translation notes

## Build
- `tools/make_release.py ORIGINAL.gba VERSION [OUTDIR]`: runs `insert.build_all`, writes IPS and xdelta
  (`xdelta3 -e -9 -S djw`) and prints hashes. `tools/insert.py` alone writes `k34_en.gba`.
- Translations: `tr_g4_a/b/c.py` (game 4, ~1,035 strings), `tr_g3_a/b.py` (game 3, ~404 strings), keyed by ROM offset
  of the Japanese string (`g3_jp.json`, `g4_jp.json`). `allrefs.pkl` = every pointer to every string/block.
- Screenshots: `tools/shots_release.py PATCHED.gba OUTDIR` (needs the emulator states from the work dir; states
  made before a build show stale VRAM, so boot from `t3` / `t4` for menus).
- Emulator: `gba.py` (unicorn, HLE BIOS); `drive.py` has load/loadrom/save/sheet; `g.press(keys, hold, after)`.

## Text engine
- One 8-bit encoding for both games (0-9, A-Z at 0A-23, kana from 24, F0-FF control codes). Fonts: g4 0xD2220,
  g3 0x1B51DC. VWF hook on the glyph blit (g4 0x8045C5C, g3 0x8094FD4); 0xEE pads to next tile.
- `{c8}` and similar codes in dialogue are the original emote glyphs (e.g. ♂ shown as a sweat drop); kept.
- wrap() removes spaces before {c8}/{c9}/{b0}/{c5}.

## Game 4 graphics/menus
- Menu tile streams are 16-bit (F1 next row, F0 end). Main menu 0x1FE5E6; brother stream 0x1FE5B2 (repointed).
- Title blocks 0xE3D34 / 0xE4E04: Start 42-45, Erase Data 46-4B (66-6B highlighted), Little Bro C0-C5, Big Bro
  C6-CB. VRAM tiles CE+ get overwritten by 0xD3CF4, so only C0-CD are free.
- File select block 0xE5C54: File on 1A-1D, EXP on 38,39,3E,3F written into label list 0x1FE738 (F0-separated,
  walked sequentially: keep lengths). "No save data." had to be one line (F1 ends the panel string).
- Kanji labels 体力/お金/命令/はい/いいえ are LZ77 graphics (gfx.py).

## Game 3 graphics/menus
- Window strings: 16-bit tile ids, FF end, FE newline, FD blank. Pointer tables in 0x1FE000-0x202400; some strings
  are referenced directly by code, so repoint all refs.
- Title block 0x1BD5B0 (6x2-tile labels); file panel block 0x1BE5A4, strings via 0x2013C4.
- Status panel: LZ77 32-wide maps decompressed to 0x200D8E8. Shared set 0x1B6A04 at D0 (BG and OBJ 0x6011A00);
  tile FE is the cursor. Place-name sets at DA (table 0x1FE944, strings 0x1FE9B0). Bait/Lure/Fly word at E0
  (table 0x1FE958). Per-panel C0 sets: tackle 0x1B6E30, creel 0x1B6F74, battle 0x1EEAF4. The field status panel
  got its own C0 set (loader literal pool 0x84734). First command cell is written by code (movs r3 at 0x84946 ...).
- Sub-windows load a 128-tile block at 0 + map at 0xD800: Food 0x1B8E80/0x1B92C8, Bait 0x1B7124/0x1B7644
  (+0x1B7E08), Items 0x1B9370/0x1B9AEC, Gear 0x1B86D4/0x1B8D0C, Creel 0x1BA27C/0x1BA684 (g3win.py). Gear has only
  3 free tiles left.
- Not yet converted: tables 0x1FF0C8, 0x1FF2A4, 0x1FFAF8; 2048-cell maps 0x1B77A0 / 0x1B7F64 sharing the bait
  block (probably shops); Fishing Memo; Uocchi screens. Icon grid tables 0x1FF010, 0x1FF188, 0x1FF364, 0x1FF5E4,
  0x1FF844, 0x1FF928, 0x1FFA94.

## Fixes and screens added in v0.6
- g4 bait-word print happens twice (0x395BC and 0x3E322, the second when a window redraws the field panel); both
  now print at EB with W=3 (menus.py CODE). Missing this made the panel garble after the Gear window.
- g4 string 0x12068 (Canoe Master) was missed by the first extraction (table 0x11868); added to g4_jp.json.
  A ROM-wide pointer scan found no other missed strings in either game.
- g4win.py: Food/Bait/Items share map 0xDAFD8 (title tiles 0A-0C per set 0xDC6B4/0xDA9C4/0xDCB10); Level window
  set 0xDDA94 / map 0xDDE90; Cooler/Bug Cage/Flowers titles are mini tile streams 0x1F8AA8/AB2/ABA (set 0xDE650).
- g3yn.py: the FF Yes/No handler DMAs font glyphs は/い/え to tiles 300-302 (literals 0x94F28/34/3C, count 0x94F30);
  now copies 5 English tiles and the map writes get distinct numbers.
- g3 window table 0x1FE9C4: blocks[10] then maps[10] (0x1FE9EC) then palettes (0x1FEA14, 224-byte entries are
  palettes, not maps). Entries 8/9 are the lure (0x1B77A0/0x1B7E08, names 0x1FF0C8) and fly (0x1B7F64/0x1B8570,
  names 0x1FF2A4) lists. The Uocchi feeding window uses the bait set with map 0x1F7B44.
- g3uo.py + tlabels.py (generic label rewriter for LZ77 maps): tank settings 0x1F6A7C/0x1F6E98 (title tiles 02-0C
  are placed by code), command menu 0x1F6FF4/0x1F7424, fish status 0x1F7584/0x1F7A28, tank view 0x1F5A9C (tiles
  B0-B5 'hours'), Fishing Memo 0x1BAEE8 (labels in colour 10 on 14).
- "esEat" in the g4 Fish slot was the いどう (move) cells F6 E2 E3; fixed in v0.7.

## Fixes and screens added in v0.7
- g3 shops: table at 0x1FEA3C = 7 sets, 0x1FEA58 = 7 maps, 0x1FEA74 = 7 palettes (rod 1B86D4/1B8DE0,
  lure 1B77A0/1B7E08, hook 1B86D4/1B8DE0, bait 1B7124/1B7644, fly 1B7F64/1B8570, items 1B9BE0/1BA1D4, fish shop
  price board 1BA770/1BABA4). The shop code draws the item icons straight into the map, so g3win now protects
  gear 30-76 and lure/fly 10-4F ('keep'); 7F (3E in the items set, 24 on the price board) is 円, drawn as ¥.
  Items counter names: table 0x1FFAF8. Rod/hook title: code wrote 2 cells (strh at 0x86968 / 0x869B8); patched to
  ldr/ldmia/stmia so 4 cells (row 1, cols 8-11) come from a 4-halfword string ('Rods', 'Hooks').
  Gear names now share pieces ('Lure|Rod| S'); gear set has 3 tiles left.
- g3 Uocchi help strings 0x1B5F1-0x1B75B are wrapped at 136 px (insert.py UOCCHI_PX).
- g3 Fishing Memo stamps are OBJ tiles 40-47 (大物, 'Big One') and 48-4F (育成, 'Raised') in set 0x1BAEE8,
  ink colour 4. Not seen in our save (needs a raised fish).
- g4 'Go': いどう cells patched to EA (custom one-tile glyph Ⓖ, code 0x81; Ⓛ 0x80 = 'Lv').
- g4 shops: sets 0x1F82A0 (byte 0x3000020+2F1 == 2) / 0x1F82E0, maps 0x1F8320, 16 entries (8-15 = Catalog,
  つうはん, set 0xDFC20 / map 0xE0254). Index = [0x28E]*3+[0x28F], kept at [0x294]. Titles are tiles 0A-0D of
  each set (g4win SHOP_TITLES); rod/hook shop prints strings B3E/B3F (0x11346/0x11349) with print 0x8039B50,
  now at tile 78 W=4 (0x3EA32/0x3EB2A, 0x3EA4C/0x3EB44) and cells 0x309A6-0x309B8 = 78-7B.
  Price board set 0xDDF88 / map 0xDE3EC. 0xDF40C (キジバリ) is the fly counter in the other brother's table.
- tools/g4force.py draws a g4 shop window by calling 0x80376D0 from a field state (no shop save needed).
- Screens: screens/v0.7/ and v0.7_contact_sheet.png (g4 shop shots are drawn that way, without icons).

## Signs (v0.8, gbasigns.py)
- Building plaques are 2x2 BG tiles in the field tilesets (LZ77; game 4 0x104DC4..0x11F6F8, 13 sets; game 3
  0x1C1DF8, 0x1C46E4, 0x1C7174, 0x1CA0F4). In game 4 set 0x104DC4: 万 A8/A9+0C/0D, 宿 AA/AB+10/11, 魚 AC/AD+14/15,
  釣 AE/AF+18/19 (game 3 sets hold 魚 A4/A5+48/49 and 釣 A6/A7+4C/4D). Face colour C, ink 6, 12x12 face at (2,2).
  Every copy is replaced by content (244 tiles). Art: Umi's hook / fish / INN, plus a shopping bag for 万.

## Fish shop and memo books (v0.9)
- Sell prompt (g3 0x1B42B, string 27 at 0x1AB50; g4 0x0FBD7) is one line plus a second line with はい at cells 9-10
  and いいえ at 12-14; the cursor sits in cells 8 and 11. English: question on line 1, then
  "<rest>     |Yes |No" (PAD lands Yes on cell 9 and No on cell 12). The box auto-wrap clips glyphs, so always {f1}.
  Test: tools selltest2.py (pokes a fish into the g3 creel, 0x3000FCD = species, size pairs).
- Game 4 memo books (g4memo.py): Fish Memo set 0xE0368 / map 0xE090C, labels 3x2 tiles 50-52+60-62 etc. (ink 10),
  尾 = 1D; 大物 stamp = OBJ set 0xE12F8 tiles 00-03 + 10-13 (red = 1). Shell / Bug / Flower share set 0xE0AE8 /
  map 0xE1150: 価値 50.., 総数 53.., ランク 40-42 after the rank letter, counters 個 1B-1E, 匹 17-1A, 本 1F/48/56/57
  (2x2, written by code), note すいそうに、おくことができる！ = stream 0x1FE540 (tiles 66-6F, 4D-4F, 5D-5E).
  RAM for tests: fish records 0x30007DC (4 bytes/species), shells from 0x30009DD (count). tools memoshots.py,
  memofill.py. 基本 is "Size" (the species' standard length), not "Avg." as 平均 in the game 3 memo.

## Title logos (v0.95, gbalogos.py + logopack.py)
- Start screen (3&4): mode 4 sky bitmap 0x21EF90 / palette 0x223F24; logo = sprites, tiles 0xC1A70 -> 0x6014000
  (rows 0-7 logo, rows 8-9 cols 0-23 copyright, 10-11 free), OBJ palettes 0xC2BCC (pal 0 + 1; extended to 16,
  pal 2-9 are reloaded by 0xC4534 = PUSH START), frame list = first pointer of table 0x202130.
- Game select: game 3 logo tiles 0xC2C08 -> 0x6014000, pal 0xC3648, table 0x2021B0; game 4 tiles 0xC3670 ->
  0x6016000, pal 0xC4174 (pal 1), table 0x20222C. The unselected logo is dimmed by fading its one palette, so
  each select logo has a single 15-colour palette.
- Metasprite engine 0x80BB8xx: 8-byte OAM templates relative to the sprite centre, list ended by a0 = 0xC000;
  tile and palette are added to the caller's base. Every OBJ is affine with its own matrix (counter 0x3002DB4) but
  only 3 bits of the index were stored (wrapped at 8); patched 0xBBA3E / 0xBBA48 to keep 5 bits.
- Game titles: mode 4 bitmaps game 3 0x2240F4 / pal 0x227768, game 4 0x2278D0 / pal 0x22D458. New pictures are
  tools/logos/t3_title.png, t4_title.png (256-colour PNGs made by titlecomp.py: colour mask of the old logo,
  smooth fill (game 3) or patch fill from rocks/water/grass (game 4), the tester's logo pasted, requantized).
- the tester's art: tools/logos/collection.png, kawa3.png ("GBC"), kawa4.png ("2").

## Name entry (namekbd.py)
- Both games collapsed to one English page (other page pointers copied from the first). Conversion tables
  g4 0x1FB490 (0x200), g3 0x200530 (0x140) rewritten for allocated tiles. g3 hint bar blanked.

## Releases
- v1.0 (2026-10-28): script pass (both games read in full; fixes in tools/tr_*.py), item names aligned
  (g4 Pole S/L, Worms, Rubber Worm, ギジバリ = Fly), smart page cuts in insert.wrap_page (split_page: cut long
  pages at sentence/clause ends; 32 lines shortened where no cut fit). Patched CRC32 24573A7E.
- v0.95 (2026-10-28): English title logos. Patched CRC32 F7A51662.
- v0.9 (2026-10-28): third playtest fixes (sell prompt, game 4 memos). Patched CRC32 04D9EE8C.
- v0.8 (2026-10-28): building signboards. Patched CRC32 43B99C8F.
- v0.7 (2026-10-28): second playtest fixes. Patched CRC32 E3670EE2.
- v0.5 (2026-10-27): first test release. Patched CRC32 F53A6E6D. Logos still Japanese (the tester is sending mock-ups:
  3&4 menu logo, Kawa 3 title, Kawa 4 title, about 190x70 px each).

## To do
- Other painted signs, if the tester finds any (ミンカ2 text sits at the end of game 4 tilesets, probably unused);
  g4 price board ランク/かち tiles (check whether the price board still shows them).
- Done in v1.0: g3 tackle/creel/battle panels checked (tools/fakepanel2.py points the field panel literals
  0x83310 / 0x84734 at a variant); g4 file panel checked with a real save (call the save routine 0x80BCC2C(slot)
  from a field state; SRAM written by 0x80BD800); rumble tiles are never referenced (left as is).
- g4 Jizo statues: not found yet on Home / farm / Plains Lake screens (the pots there are flower pots).
