# ROM notes

Hacking knowledge for this game. Record anything a future session would otherwise rediscover.

## Versions (researched 2026-11-09, no images yet)
- Target: 7 Blades / セブンブレイズ, Japan, SLPM-65008, 2000-12-21, DVD-5. Reissue: Konami the Best SLPM-65057 (check which one the project lead has).
- Reference: PAL SLES-50109, 2001-09-28, DVD-5, menus/text in English, French, German, voices kept in Japanese. 50 Hz only (no 60 Hz option) — the main reason an English NTSC-J patch is worth making: full speed 60 Hz with English text.
- No US release; no existing English patch for the JP disc found (web search 2026-11-09).
- Dev: KCE Japan East + Paradise Pictures; director supervisor Kaizo Hayashi (film *Zipang*). Setting: Dejima, mid-17th c., Tokugawa era.
- JP debug menu (TCRF): hold Start+Select at power-on; stage select, movie viewer, character select; L1/R1 pages, R2 confirm. Handy for reaching cutscenes in testing.
- Sources: psxdatacenter SLPM-65008 / SLES-50109, tcrf.net/7_Blades, en.wikipedia.org/wiki/7_Blades.

## Plan
1. Diff JP vs PAL file trees (`rhtk ps2 ls`), find where the text lives (ELF vs data files) and its encoding in each.
2. Dump JP script, dump PAL English script, align line-by-line (ids, order, cutscene subtitles).
3. Port PAL English into the JP layout; replace JP font/texture text with PAL equivalents where formats match.
4. Edit pass: compare PAL English against the Japanese, fix mistranslations per STYLE_GUIDE; record changes.
5. Build, PCSX2 playtest (debug menu for cutscenes), xdelta release like conveni3-ps2.

## Disc images (2026-11-09)
- JP: the project lead's own image (plain 2048-byte ISO), 4596269056 B, CRC32 CC8D415A, SHA-1 faa45d3f...24c4. Copied whole to `rom/7 Blades (Japan) SLPM-65008.iso`. Size = PVD block count, so complete. Redump not checked (site blocks fetches).
- PAL: the project lead's own image, 4628742144 B, CRC32 1E348FC5, SHA-1 1919d692...7d56. Only small files copied to `rom/pal/` (ELF, EFF, STAGE1/STAGE0, IOP, 2 sample movies).
- Copying a 4.6 GB ISO from the lead's PC: split into 390 MB parts on the device (python), stage one per call (500 MB/call limit), check SHA-1, cat. ~20 min total.

## Disc layout (both regions)
- ~95% of the disc is FMV: MOVIE/G0-G3 (Gokurakumaru route), Y0-Y3 (Oyuri route), M0/M1, END. PSS MPEG-2. JP 640x320 30 fps; PAL re-encoded 512x320 25 fps, same durations. No burned-in subtitles in either.
- ELF (SLPM_650.08 / SLES_501.09), load vaddr 0x200000 at file 0x1000.
- EFF/PEACE.NCB: UI textures (system.r, title2.rh2, fonts.rh2, item.r, save.r, load.r ...). PAL adds item_e.r, save_e.r, load_e.r.
- STAGE1/CHARA.NCB, STAGE0.NCB; JP-only STAGE1/REPLAY.NCB (10 KB).
- PAL-only EFF/SUBTITLE.NCB: cutscene subtitles. The JP ELF has no subtitle code at all (no SUBTITLE.NCB string).

## Formats
- NCB archive (corrected 2026-11-09): u32 count, then 32-byte entries name[24], u32 offset, u32 size; data 0x800-aligned. Header 0x800 in PEACE.NCB, 0x1800 in the movie data streams. tools/b7_peace.py ncb_list/ncb_build.
- .r archive (inside PEACE.NCB and the movie streams): "1.\." LZ around an inner directory of name[0x18], u32 raw size, u32 offset; count = first offset / 32; an empty terminator entry has offset = total. Members are '1\0\0\0' + BE size + LZ tokens, back to back, no alignment. tools/b7_peace.py r_unpack/r_pack.
- Every LZ stream ends with a 0x00 token; the game's member decoder needs it (leaving it off = black screen at boot). b7_lz.compress adds it; b7_lz.c is an optimal-parse compressor.
- rh2 texture: "RH2\0", size +8, first GIF packet offset +0x10, TEX0 +0x30, psm u16 +0x50, w/h u16 +0x54/+0x56; body = CLUT upload then pixel chunks, one GS page each. tools/b7_rh2.py renders (b7_gs.py = GS memory model).
- "1.\." LZ: magic, BE u32 raw size, tokens: b<0x80 = b literals; b>=0x80 = BE u16 v, copy ((~v>>8)&0x7f)+3 from distance (v&0xff)+1. tools/b7_lz.py (decompress + compress, round-trips all 216 subtitle files).
- Subtitle script (.GSC en / .GSF fr / .GSG de, one per movie, 72 movies): LZ'd; records (start, end, text_off) LE u32, end (0,0,-1); NUL strings, TAB = line break. Times are 1/30 s (checked against JP movie lengths), so they fit the JP movies unchanged. tools/b7_sub.py -> script/subs_pal.json (1217 English lines, ~6100 words).
- PAL ELF: "eff/SUBTITLE.NCB" at file 0x308898 (ref 0xF11F4, func ~0x2f01d8 loads it), "subtitle packet size over." at 0x3089a8 (ref 0xF4EAC).

## Text
- ELF: JP has ~295 SJIS strings (tutorial, Togizo lines, enemy/boss names, menus); PAL ELF has the same in En/Fr/De. Glyph order string at JP file 0x234b90 (ー・！？、。...), so the font is a custom-ordered SJIS subset.
- Encoding / table status:
- Pointer tables found (offset, count, format):
- Control codes (byte, meaning, params):
- Text box size (chars per line, lines per box), fixed or variable width font:

## Graphics
- PAL keeps its English images as extra members <jp>_u.rh2 (or _e) in the same .r or in <name>_e.r. b7_peace.py swaps every one whose rh2 header (first 0x30 bytes) matches the JP member, plus RENAME (girisuji -> giri_u, mapfont1-3 -> load_e.r mapft1-3_u) and ADD (status captions kai_e... appended to effect.r).
- Not swapped: effect.r status images (dimensions differ; captions drawn by my_status_draw instead), save EYE1L/R (PAL per-character backgrounds, no text).
- PAL-identical, so left alone: HUD weapon names and the quick-slot 無 (item.r g_iten/y_iten), Gover hi/ka, the small English already on JP kei/zoku/hi/ka/title menu.
- Stage data: 66 movies carry effect.r, Geffect.r, Gover.r, Gparam.r, item.r (byte-identical to PEACE); stages use these copies. tools/b7_stagedata.py patches them in place (movies must not grow; tighten() recompresses members to make room).

## Free space
- Ranges confirmed unused (how verified):

## Code hacks
### English movie subtitles in the JP program (working 2026-11-09)
- Source: `src/subtitle/` (sub.c, gen_data.py, link.ld). Build: `python3 tools/b7_build_jp.py [out]` -> build/SLPM_650.08 (needs gcc-mips64el-linux-gnuabi64). B7_HOOKS=play,pic,send picks hooks for bisecting.
- C port of the PAL engine, compiled to a new PT_LOAD segment at 0x6d3200 (second program header in the JP ELF; ~100 KB). Embeds the 72 English .GSC scripts (decompressed, from PAL SUBTITLE.NCB), PAL's kerning table (PAL 0x43e410) and eu_font (LZ, see In-game font). No new disc files; JP FILES.TXT untouched.
- Hooks: 0x385db0 jal 0x385e10 -> my_play (movie name in a0, e.g. "g1/g0010_1a" -> key G0010); 0x387b9c jal GetPicture 0x3c5738 -> my_getpic (frame = mpeg[2], builds the GS packet, timing 1:1 since JP movies are 30 fps); 0x385b10/0x385b60 jal sceDmaSend -> my_send (sends the subtitle packet on the GIF channel after each field's movie packet, sceGsSyncPath 0x3bc2c8 between).
- Font: eu_font sits permanently in kanji1's VRAM slot (TBP *0x4f14d8+0x280 = 0x3f00, CBP *0x4f1514+0x40 = 0x3ec0), see In-game font; the movie code only builds TEX0 for it. (Earlier builds uploaded it per movie and re-queued kanji1 with 0x2f8b40 afterwards.)
- Layout: PAL x math (512 units, center 0x100) scaled 5/4 to the 640 field; glyph 12x14 field lines; one line at field y 200, two at 191/205 (bar under the movie is lines 192-224). XYZ origin 0x6c00/0x7900.
- Memory gotchas: (1) newlib sbrk's start pointer is a data word at 0x4ba66c (= &end 0x6d3200), separate from SetupHeap in crt0 (0x20006c-0x200078); both are moved past the segment, heap now 0x6ef300-0x700000 (PAL leaves less). (2) crt0's bss-clear loop overshoots and zeroes 0x6d3200-0x6d320f, so the segment starts with 16 bytes of padding. Game guards compare end-of-static against 0x6effff/0x6fffff, so keep the segment end below 0x6f0000.
- Tested in PCSX2: G0010 (first Gokurakumaru movie) shows timed, centered English lines; HUD/kanji fine afterwards. Screens: build/screens/subs_g0010.png.
- Toolchain gotcha: compile with -mabi=n32 (link -m elf32ltsmipn32), not EABI. EABI frames are only 8-byte aligned and Sony's libraries (libmpeg etc.) use sq/lq on the stack, so a hook with a 56-byte frame hung the game in GetPicture. n32 gives 16-byte frames and the same a0-a3/t0-t3 argument registers.
- Testing gotcha: always `pkill -f AppRun` before relaunching PCSX2; a leftover instance made good builds look hung.
### Tutorial text (working 2026-11-09)
- JP builds all tutorial messages up front in 0x22fb40: records at 0x3fbb80 + i*0x15c (id +0x47c, line count +0x480, line widths +0x484, five 64-byte lines from +0x498), one switch case per record (jump tables 0x4bf4c0 Gokurakumaru 84 cases, 0x4bf610 Yuri 77). Button names (10 x 0x20 bytes) at 0x3fbebc.
- PAL keeps the same ids but stores whole messages in tables (id, en, fr, de) at 0x402878 (81) / 0x402d88 (68), '$/' = new line, '$0'-'$9' = button name. Every JP id exists in PAL (Yuri case 21 has no id and is never shown).
- Hack: the jump-table dispatch (0x22fc4c / 0x231264) calls tut_fill_goku/tut_fill_yuri (src/subtitle/sub.c), which writes PAL's English for that record's id, then continues at 0x2311a8 / 0x232618 (the original width pass). PAL's one 6-line message (Quick items, id 78/56) is re-wrapped to 5 lines by gen_data.py.
- Draw 0x232940 now goes through pal_text (proportional eu_font, 24-px cell as in PAL). Centring: 0x232ea0 (counted 2-byte chars) jumps to tut_width (half the proportional width) and the factor at 0x232bc0 is 1, like PAL's 0x2ef498 width call. Button names: inline 0x20-byte strings at 0x3fadf0.. are copied to 0x3fbebc at run time; セレクト/スタート (0x3faeb0/0x3faed0) become ＳＥＬＥＣＴ/ＳＴＡＲＴ as in PAL.
- Screens: build/screens/tutorial_en.png.
- Route to G0010 in PCSX2: title, Start, Start, Circle (Start game), Right+Circle (no tutorial), Circle (Gokurakumaru).

### In-game font: PAL's eu_font + proportional renderer (working 2026-11-09)
- PAL loads eu_font.rh2 where JP loads kanji1.rh2 (same rh2 header: PSMT4 256x256, CT16 16-colour CLUT, same VRAM slot) and its renderer 0x2ee4f8 has no kanji at all. Same approach here: 0x2f346c jal install -> my_install, which lets the JP installer load kanji1 into its 0x6000 buffer (0x4f9c60, LZ '1' + BE size, same LZ as b7_lz) and then overwrites everything after the 4-byte tag with eu_font LZ (~14 KB); the normal upload queue then puts eu_font in VRAM.
- 0x2f3600 (JP SJIS renderer, called via 0x2f35e0/0x2f35f0 by 14 functions) starts with `j pal_text`: port of PAL 0x2ee4f8 with JP's GS helpers (0x2f7868/7848/7f78 setup, 0x2f6c90 + 0x2f6ee0 per sprite, shadow +3 px). SJIS 0x82 digits/A-Z/a-z -> eu_font cells, 0x81xx via PAL's table at 0x43e611 (PAL 0x2ef078), ASCII also accepted, kerning PAL 0x43e210 scaled by cell width, full-width space = half a cell. Kana/kanji draw nothing (as in PAL).
- PAL maps ○×△□ (0x819b/817e/81a2/81a0) to cells 0x9c-0x9f, which are blank in PAL's eu_font. tools/b7_font.py (PSMT4<->CT32 swizzle, checked against PCSX2's GSTables) paints button glyphs into those cells before packing.
- Item screen: the 胴乱 label becomes "Quick" (PAL splits Quick/Item), label x moved 0xe0->0xc0 at 0x3790b4 so it clears the square icon.
### In-game text tables (working 2026-11-09)
- tools/b7_strings.py: JP table ranges, matching PAL Japanese block and PAL English offset (hints 0x300, food names 0x2c8, food comments 0x14c, weapons 0x29c, quick items 0x94, keys 0x20, item-screen messages 0x154) plus the 82-entry name table. Item command menu mapped by meaning (PAL's English block is ordered Drop/Use/Remove/Quick/Item). PAL's "× Yes / ○ No" is swapped back to ○ Yes / × No (JP confirms with circle).
- Strings go into freed JP string space (old Japanese text and the JP ELF's unused dev-English text, never referenced by code), ~17 KB in 56 ranges; overflow would go to the segment. The JP dev-English blocks sit at different offsets from PAL's English blocks for food names (0x248) and food comments (0x108).
- Still Japanese in PAL too: 七支砲 (weapon slot 0x4748e4), quick items 金丹 (0x474ca0) and 扇子 (0x474cb0); since 2026-11-10 our own English via EXTRA (the project lead okayed). Keys 極かぎ２/３ and 百合かぎ２/３ look like unused duplicates, left as is.
- HUD weapon name (bottom right, e.g. 麒麟) and the 無 quick-slot boxes are textures, not text: graphics task.

### Status popups (working 2026-11-09)
- 11 status images load through jal 0x2f81f8 at 0x2e7c0c..0x2e81fc -> my_status_load also loads the PAL caption <name>_e.rh2; draw 0x2e7678 -> my_status_draw (JP image + PAL caption strip). Caption handles verified in RAM; not yet seen on screen.

### Kill counter (working 2026-11-09, seen in PCSX2)
- effect.r girisuji.rh2 -> giri_u.rh2 (same header; white art, label "Defeated" 64x16 texels instead of 48). Draw 0x3ba270: tint 0x808080 -> PAL's 0x808008 (cyan, at 0x3ba47c/4cc/510), centring count 3 -> 4, label width 3 -> 4 digit widths, uv u1 48 -> 64, 6 px gap. Visible only ~14 frames per kill; test builds held the timer (0x3ba3f0 nop, 0x3ba3f4 li v0,7000).

### Save and load screens (2026-11-09)
- Sprite tables (stride 0x2c: +0xc handle, +0x18 u0 v0 u1 v1, +0x20 x0 y0 x1 y1): save JP 0x46da48 (62, setup 0x35f860, draw range 0x363fc0), load JP 0x46a030 (52, setup 0x35bf80, draw 0x35f378). PAL 0x48e588 / 0x47eb60, setups 0x3612c0 / 0x35d358, language var 0x4990a8 (0 = English).
- tools/b7_savefix.py emulates both setups (unicorn; R5900 mult/mult1 in hooks), diffs, writes src/subtitle/savefix.h; my_save_fix / my_load_fix run as the setups' tails (jr ra -> j). Verified: the built JP setups produce PAL's English tables exactly.
- PAL draws extra sprites: save 29 "SAVE FAILED." header in states 0x3f0/0x3f1/0x3f5/0x1c5 and range 0x14-0x19, 59/60 second lines in 0x3f0/0x3f1, 50 in 0x3f8 when overwrite flag 0x46f34a==1 (my_save_draw at 0x3621b0); load 4 "LOAD FAILED." header for ranges (8,11) (12,13) (13,13) (17,18) (16,16) (5,7) (my_load_draw at 0x35d0fc). PAL's own quirk kept: in state 0x3f8 "at the last save location," sits between lines 2 and 3.
- Map location labels: table JP 0x46ac80 (2 chars x 0x400, entries 0x20: x, y, u, v, w, h, sheet). PAL has blocks at 0x47f7c0 + n*0x800 (0 = JP copy, English = (lang+2) = 0x1000); build copies the English block (horizontal mapft*_u labels).
- Seen in PCSX2: load prompt and "LOAD FAILED." card error. Save screen only checked offline (composited from the sprite tables).

## English already inside the JP ELF (found 2026-11-09)
- The JP ELF carries full-width SJIS English tables next to the Japanese ones: item names (Stew, Rice porridge...), Togizo's item comments ("I feel weaker."), weapon descriptions, enemy names (Saberman, Wind God...). Example: JP food names table at va 0x4740c8, English at 0x474308; Togizo comment tables at 0x474550 (JP) / 0x474658 (EN).
- Only the JP tables have direct code refs found so far (lui+addiu at file 0xBE4B0 etc.); the English ones may be reached by base+offset or be dead data. No language-select strings found. Worth checking in PCSX2 whether a flag switches them on.
- PAL ELF English is ALSO full-width SJIS (French/German are Latin-1 ASCII). So the JP font already draws English; no font work needed for ELF text beyond fit.
- Clean string lists: tools/b7_elfstr.py (JP 673 real strings, PAL 711).

## PAL subtitle engine (decompiled 2026-11-09, Ghidra headless; see tools/ghidra/, tools/b7_r5900_sanitize.py)
Ghidra setup: sanitize EE-only opcodes (MMI/LQ/SQ -> nop, analysis copy only), import with `-processor MIPS:LE:64:64-32addr`, preScript SetGP (JP gp 0x4f4df0, PAL gp 0x520b70), postScript ExportDecomp. Exact-match function map PAL->JP by normalized decompile: 2301/3259 match.
PAL functions (JP has none of these unless noted):
- 0x2f01d8 init: loads eff/PEACE.NCB and eff/SUBTITLE.NCB handles.
- 0x2f3958: alloc 0x10000 subtitle GS packet buffer (DAT_0051dd08).
- 0x2f3980 per-movie loader: movie name "g0010_1a.pss" -> "g0010.gs"+lang char (c/f/g) -> entry from SUBTITLE.NCB (FUN_003a4118, JP 0x3a2370) -> DAT_0051d9cc record ptr. Called from movie play func 0x38cb10 (JP 0x385c20 lacks it).
- 0x2f3b28 per-frame: compares frame*0.8333 (25/30, float at 0x51a6d0/d4) with start/end, splits at TAB into two lines (0x53d120/0x53d1a0), centers at x=0x100 using width fn 0x2ef3d0, draws at y=0xe0 (one line) or 0xe8/0xf0 (two lines) with 0x2ef0e0. Char size set by 0x2ee400(0xc,0x10).
- 0x2f3db8 packet wrapper: sceVif1Pk-style lib calls (0x3c1f88/98, 3c2000, 3c21a0, 3c2260 AddGsAD x5 regs 0x3f,0x3b,0x14,0x47,0x06, 3c21b8, 3c1fa8, 3c2110), sets DAT_0051d9d4 = packet, calls 0x2f3b28. Called from the MPEG decode loop 0x38ea18 right after sceMpegGetPicture with DAT_0051d358 = frame (param_1[2]). JP decode loop = 0x387b40 (identical minus these two lines; hook candidate: its jal 0x3c5738 GetPicture).
- vsync handler 0x38c8a0 DMAs the packet (DAT_0051dd04) after the movie frame (extra FUN_003bfd78 call).
- 0x2ef0e0 ASCII proportional text draw, 0x2ef3d0 width; font eu_font.rh2 (texture handle DAT_0051d9b0) with kerning byte pairs at 0x43e410 (ELF data, 0x60 chars). Sprite append 0x2f3d48 into DAT_0051d9d4.
- Fonts: JP loads kanji1 (0x6000, VRAM slot +0x280), kanji2 (0x8400, temp), kanji3 (0x4c00, slot +0x300) in 0x2f3428. PAL loads eu_font (slot +0x280), emov_font (+0x300), kanji3 (temp) in 0x2ee2d8. PAL system.r (in PEACE.NCB) = JP system.r + eu_font, mov_font, us_font, emov_font.
- JP's own SJIS renderer 0x2f3600 writes into the main display list (DAT_004f14c0) which is not flushed during movies, so it can't be used for subtitles.
## Memory
- JP: ELF memsz ends 0x6d3200; heap 0x700000-0x1700000 (0x3a11b8); guards check end-of-bss <= 0x6fffff. 0x6d3200-0x6fffff is free headroom (PAL's bigger bss ends 0x6f2f20). New code/data segment goes there.
- Toolchain: apt gcc-mips64el-linux-gnuabi64 (+binutils), -march=r5900; game uses EABI-style arg regs (5th arg in t0).

## Debug menu (TCRF, 2026-11-10)
- Codes for SLPM-65008: D05326C2 0000FFF6 203B2198 03E00008 / D05326C2 0000FFFF 203B2198 080EC868. Test builds just patch ELF va 0x3b2198 (0x080ec868 -> 0x03e00008, jr ra).
- L1/R1 pages, R2 confirms (PCSX2 key '3'). Menu: Release, MovieCheck, CharacterTest, Tutorial Goku, Stage1A G, 1B, 1D, 1E, Stage2A (8 Downs). Stage2A plays G0070 while streaming the stage. MovieCheck: 10 Downs to G0070.
## Texture slots (2026-11-10)
- 0x434180 short handle[36], 0x4341c8 u64 TEX0[36]: 32 dynamic slots at TBP_BASE + i*0x10 (FUN_002f87b0), fixed slots 32-35 (kanji1 = 33, tbp 0x3f00 cbp 0x3ec0). TBP_BASE is 0x3c80 or 0x3880 (FUN_002f7cd0 param). kanji1/eu_font uploaded once (FUN_002f3428, guard 0x4f04d0) via the fixed-upload queue FUN_002f8b40.

## Pressure attacks (PAL only; ported 2026-11-10, src/subtitle/pressure.c)
- PAL samples pad pressures (pad data +8, 12 bytes; 5 = circle, 4 = triangle) for 5 frames after an attack action starts, then 0x25c380 turns max pressure into level: >=210 -> 5 (dmg x1.5, record type 2/5->4, <2 ->+1), >=55 -> 4, else 3 (dmg x0.5). Level byte PAL gp-17748 (JP: atk_level[0] in fx.c), copies gp-17747 (hitbox/swing) and gp-17746 (thrown blade).
- PAL -> JP: pad read 0x38a8c8 -> 0x384568 (callers 0x3b4e40, 0x3baa6c); pad mask check 0x3c1c08 -> 0x3bf318; demo flag gp-13920 -> JP gp-16496; button config 0x49c4c0 -> 0x478830; player gp-13836 -> gp-16412.
- Action fn PAL 0x254de0 / JP 0x258d58 (jump table 0x4ef300 / 0x4c5c00, same action ids): entry hook 0x258d88 (s3 = action), tail hook 0x259f04 (s1 ent, s4 motion, s3 final). Start-sampling and keep-level action sets are in hk_act_tail.
- Hitbox setup PAL 0x278070 / JP 0x27de00 (level at 0x27df5c; reach 50/100 -> 75/150 at 0x27e038/0x27e044), swing test 0x278968 / 0x27e688 (reach 0x27ea4c/0x27ea80, sectors 0x27e950, back limit 0x27f018, knockback floor 0x27f198), special hit records 0x2798e0 / 0x27f630 (0x27f744, 0x27f7a0), hit handler 0x25c578 / 0x260170 (0x260608: s0<179 -> triangle table), light-press path 0x2623c8 / 0x265c90 (0x265cc4), level clear 0x2642c8 / 0x269448 (0x2694a4), thrown blade 0x2ba550 / 0x2c2cf8 (speed 4 -> 6 at 0x2c2d78).
- Yuri (PAL gp-17128 level, -17127 copy; table 0x437da0): action fn 0x2c2850 / JP 0x2cb078 (cases 243 / 229 / 233 start sampling; JP table 0x4dc7e0, 254 entries), level at shot spawn 0x2c89a0 / 0x2d1070 (+0x44c, speed 1.5 -> 3), swing 0x2c9608 / 0x2d1c98, shot records 0x240aa0 / 0x244b80 (damage 3 -> 10 / 1), hit routine 0x2c9c80 = copy of generic 0x3a7e78 (JP 0x3a6188) with the level on the record and motion 243 damage 15/5/1; JP has no copy, so my_yuri_hit replaces 0x3a6188 at Yuri's two setups.

## Options screens (2026-11-10, src/subtitle/sub.c my_optspr, tools/b7_optfix.py)
- One sprite table for both option screens: 80 records x 0x2c at JP 0x478f3c / PAL 0x49cbcc (+0xc texture handle, +0x18 u0 v0 u1 v1, +0x20 x0 y0 x1 y1), records 88-90 = in-game "Return to title?" + No/Yes. Sheet handles at JP 0x47a3f8/0x47a3fc (PAL 0x49e088/8c/90, three sheets). Cursor-bar table (shorts) right after record 90: JP 0x479ee0 (row x0 [0..7], y0 [8..15], x1 [30..37], volume screen [60..85], control column x0 [104..109]).
- Code: title loader 0x368cf0 (FONT1/Font2 from taku_save/load_data = load.r) -> setup 0x368e08 (calls in-game setup 0x37bd10 first) -> main 0x36a708; in-game loader 0x382380 (taku_data = item.r), setup 0x37bd10 (ends calling 0x37ded0 = control-screen values from pad config 0x478830). PAL: 0x36c918 / 0x36da50 / 0x36f7f0, 0x3816e0.. / 0x381780 / 0x383e18 (all three load_e FONT*_u).
- Every option sprite is built by 0x37b538(pkt, rec, xoff, yoff); 16 call sites (title 0x36bfd4.., in-game 0x380218.., list in b7_build_jp 'opt') go to my_optspr, which builds a translated copy: JP (sheet, src rect) -> PAL (sheet, rect) from opt_map, x0 += opt_dx[slot], x1 = x0 + English width; hidden = zero width. JP rows stay (PAL adds Language/Text rows). Cursor bars: PAL extents (my_optfix_title/game at the setups' jr ra 0x36a6fc / 0x37dec8). FONT3 loaded beside Font2 (jal at 0x368d9c / 0x3823a8 -> my_optload_title/game, handle opt_h3).
- b7_optfix.py runs both programs' setups in unicorn (movz/movn emulated) and pairs slot by slot; MANUAL covers run-time values (Monaural, Reverse, ?, Return to title?).
