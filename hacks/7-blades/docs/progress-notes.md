# Progress

| Phase | Status | Notes |
|---|---|---|
| ROM identified, notes/rom.md started | done 2026-11-09 | JP ISO copied (CRC CC8D415A), PAL key files in rom/pal |
| Table (jp.tbl) complete | | |
| Pointer tables mapped, script dumped | partial 2026-11-09 | cutscene subs: script/subs_pal.json (PAL En/Fr/De); ELF text not yet |
| Glossary + character sheet drafted | | |
| Translation pass 1 | | |
| Edit pass (voice, consistency) | | |
| Movie subtitles (PAL engine ported into JP code) | done 2026-11-09 | src/subtitle, tools/b7_build_jp.py; tested on G0010 in PCSX2 |
| Tutorial text (PAL English into JP message records) | done 2026-11-09 | tested Gokurakumaru tutorial in PCSX2 |
| In-game text (names, items, weapons, hints, item screen) | done 2026-11-09 | tools/b7_strings.py; PAL eu_font + proportional renderer replaces kanji1 |
| Font / VWF / gfx | partial 2026-11-09 | font, menus, item/save/load/game over images, status captions, kill counter, save/load layouts done; options screens done 2026-11-10 (my_optspr) |
| Build + qa clean | test build 2026-11-10 | build/release/7blades-en-test.xdelta (rebuilt 2026-11-10 late with options screens + ○/✕ prompts; 36.4 MB, md5 c1d537c2..., verified) + README.txt; build: tools/build_iso.sh <jp.iso> <out.iso> |
| Playtest | | |

## 2026-11-10 (the project lead's feedback round)
- In-game font was "ballooned": pal_text now scales glyphs, advance and PAL's per-side padding by txt_sx/txt_sy = 12/16 (variables in sub.c); line pitch and positions stay JP's, glyphs centred in the JP line. Shadow 2 px as PAL. Screens: build/screens/font_before_after.png, item_screen_small.png.
- the project lead saw fully garbled movie subtitles (no letters) in the Nagasaki movie G0070 on a real PS2 (Neutrino, UDPFS streaming, compat mode 7); fine in PCSX2 (viewer and Stage2A flow). Font texture was read from a fixed TBP_BASE+0x280; my_send/build now read kanji1's live TEX0 from the game's slot table (0x434180 handles, 0x4341c8 TEX0, slot 33) every frame, plus CLAMP_1. Waiting on the project lead's retest.
- Our own English for PAL-untranslated items (b7_strings.py EXTRA): 七支砲 Seven-Branch Cannon (+3 lines), 金丹 Elixir, 扇子 Folding fan. '-' must be ー (0x815b) and ' must be ’ for eu_font.
- Debug menu (TCRF): see rom.md "Debug menu".
- Seen in the debug Stage2A item screen: "@ knocked out." (a texture, partner status while Oyuri is out). Not checked whether PAL shows the same.
- Later 2026-11-10: "@ knocked out." top left = 4th row of the JP message box layout (0x474f48: x/y[3] = 0,0) drawing the shared blank string 0x4f0ac0, which b7_strings.free_ranges had merged into a free range (now never merges across pointed-to addresses). Ported PAL's English layouts (b7_build_jp.py 'font'): box structs 0x474f48/0x474d20/0x4749e8/0x474308/0x474658 from PAL 0x4987fc/0x498244/0x4976a4/0x495e98/0x496c4c (16 px, 4-5 rows), set_size 32->16 enemy name (0x229150), 24->16 item label (0x36ffc8) and command labels (0x3790f8) with PAL x/y, "Item" label via my_cmd_label (0x37911c). Glyph scale back to 16/16 (PAL numbers 1:1; same screen coordinates in both programs). Tutorial stays 24 like PAL.
- the project lead noticed PAL (their 60 Hz conversion) plays faster and has more sword effects. Not investigated; offered.

## 2026-11-10 sword effects + pressure attacks (the project lead chose the full PAL port)
- Effect 77 (weapon trail for entity types 21/22/4/41) and effect 10 (Gokuu's trail; PAL's level glow + sparks) ported as C in src/subtitle/fx.c.
- PAL pressure-sensitive attacks ported as C in src/subtitle/pressure.c, hooked by b7_build_jp.py 'press' (addresses in rom.md "Pressure attacks"). PCSX2: keyboard press = 255 -> level 5, tutorial combo shows the blue glow + sparks (build/screens not saved; scratch rec_a_grid.png).
- Yuri's copy also ported (lvl_y, PAL gp-17128/-17127): her action fn entry clear + start on actions 243/229/233 (JP 0x2cb078, 0x2cb4b4, jump table 0x4dc7e0), shot speed (0x2d14bc), swing (0x2d1c98), shot record damage (0x244cfc), and PAL's own hit routine 0x2c9c80 as my_yuri_hit (entity +108, set at JP 0x2c7308/38 and 0x315cc0/d0). Tested: my_yuri_hit runs every frame, sampling starts (forced via action 170 in a test build); her 243/229/233 moves not reached by hand in PCSX2.
- Not ported: PAL's init zeroing (0x253560, 0x2bec34), harmless. Unrelated PAL balance changes seen and left alone: 0x25cb48 (action 501 damage 32767), 0x240be0 (shot record 8 -> 64), 0x2c91a0 (5 -> 3).

## 2026-11-10 late: ○/✕ prompts + options screens (the project lead: "options menu still untranslated and glyphs swapped")
- Button prompts: PAL images use cross = confirm. b7_peace.BUTTON_SWAP swaps the icons in mapft3_u (map "Decision/Return", load.r and save.r mapfont3), load2_u (Start/Return) and puts a circle into chk_u ("press the ○ button"; its CLUT had no red, a duplicate white entry gives up its slot). Pixel editing via tools/b7_rh2edit.py (get/put index images for any rh2 upload layout, round-trip exact). In-game text was already swapped (b7_strings FIX).
- Options screens (title and in-game, Equip screen L1/R1): tools/b7_optfix.py -> src/subtitle/optfix.h, my_optspr / my_optload_* / my_optfix_* in sub.c, hooks 'opt' in b7_build_jp.py. Details in rom.md "Options screens". PEACE: load.r/item.r font1/font2 <- PAL FONT1_u/FONT2_u, new member font3.rh2 <- FONT3_u (stage-data copies of item.r follow automatically).
- Tested in PCSX2: title options (main, Stereo/Monaural, Volume, Control incl. "?" while assigning) and in-game options (main, Volume, Control, "Return to title? No/Yes"). Map/load prompts checked only as images (no memory card save in PCSX2 here); built archives verified to carry them.
- Test loop: /tmp dbgiso.sh now also patches PEACE.NCB and the stage-data movies into b7dbg.iso (stages read item.r from the movie copies). In-game options: debug Stage1A, Return (Equip), q (L1).
