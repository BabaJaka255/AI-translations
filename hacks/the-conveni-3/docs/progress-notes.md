# Progress

| Phase | Status | Notes |
|---|---|---|
| ROM identified, notes/rom.md started | done 2026-11-02 | SLPM-62322, CD image converted to ISO |
| Containers (PAC, LZS) | done 2026-11-02 | tools/c3pac.py |
| Emulator | done 2026-11-02 | PCSX2 headless, save state at first map |
| Table (jp.tbl) complete | n/a | plain Shift-JIS |
| Pointer tables mapped, script dumped | done 2026-11-02 | script/elf.json 1822 strings (re-dump added 849 kanji-only labels the first pass missed; ids stay stable), script/cn3.json 1083 |
| Glossary + character sheet drafted | approved 2026-11-02 | notes/glossary.md decisions section |
| Translation pass 1 | nearly done 2026-11-02 | ELF 1551/1602 (left: money formats waiting on the yen code change, name-entry rows, memory card title); CN3 1079/1079 |
| Edit pass (voice, consistency) | | |
| Font / VWF / gfx | pairs proof done | English renders (full-width SJIS); menu font letters added by tools/font_proof.py; checksum fix required; space 6 px; letter-pair glyphs (tools/c3_glyphs.py) give ~1 byte/char; texture labels redrawn by tools/c3_gfx.py (menus, headers, buttons, cards); title logo open |
| Build + qa clean | done 2026-11-02 | build 22: ELF 1566 and CN3 1079 written, 0 too long, 0 without glyphs |
| Playtest | partial 2026-11-02 | boot, title, tutorial, menus, setup flow, map, Store Status, ticker verified; random event popups not all seen |
| Release | v0.9.6 beta 2026-11-06 (build 44, CRC A3BAF439: career lines reordered, no 〃); v0.9.5 beta 2026-11-06 (build 43, CRC E14E4FFE: clerk age "22, M", career "Joined your Main"); v0.9.4 beta 2026-11-03 (build 42, CRC B7EF0E67: fixture panel word wrap, fixture names, /G prices, stamp, goals, encyclopedia, tips wait); v0.9.3 beta (build 30: tutorial margin 75, tabs, #N store names, marker "1"); v0.9.2 (build 28); v0.9.1 (build 27, after the project lead's playtest notes); v0.9 earlier | release/v0.9-beta: xdelta for the Redump bin and for the ISO, README with hashes |
