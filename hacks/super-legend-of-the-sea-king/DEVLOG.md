# Development log: Super Legend of the Sea King

How the English patch for *Umi no Nushi Tsuri* (Super Famicom, 1996) was made, in order. All dates are 2026. "The tester" is the human who started the project, made the naming and art calls, and playtested; "Claude" is the AI that did the hacking and translation. Addresses are in [docs/ENGINE_NOTES.md](docs/ENGINE_NOTES.md).

## Starting point (26 Oct)
The tester had an English patch for *Kawa no Nushi Tsuri 2* made in an earlier chat ([Super Legend of the River King](../super-legend-of-the-river-king/README.md)) and handed over its toolkit, saying Umi "seemingly" used "a similar if not the same engine", in the hope that "much of the work can be streamlined and possibly reused". Base: the Rev 1 ROM (16 Mbit, CRC32 `C985F568`). No earlier translation was known.

## Phase 1: engine comparison
Claude ran the River King tools against Umi. The LZSS compression, text encoding and kanji font layout were unchanged: the old `lzss.py` round-tripped every Umi block byte for byte, and byte `DF` was still free as the switch into English. Moved: the script (`$86:9B25`, 703 pointers) and the three text loops (`$82:843B`, `8956`, `B19E`), which read the string through different RAM variables. New: about 130 kanji Kawa 2 never used, and a different fish-record layout. Since the ROM was full, Claude proposed expanding it to 32 Mbit and the tester agreed.

## Phase 2: script tools and first English
- **Dump and reinsert:** the round trip came back byte for byte. One surprise: Umi's pointer table also points at 67 small data records between the strings, so the tools detect those and keep them out of the script.
- **Kanji table:** all 954 glyphs were checked by eye. That covered the 130 new ones, and caught 43 of Kawa 2's unconfirmed guesses that were wrong.
- **First build:** a 32 Mbit expansion, a checksum fix, and an English hook in all three text loops.
- **Testing:** unlike the Kawa 2 project, this one had a headless emulator (snes9x through stable-retro). The opening narration was confirmed in English there.

## Phase 3: translation
Claude translated 541 of the 636 strings in one pass, using Kawa 2's terms. 海のぬし became "the Sea King" to match "River King". Testing caught a layout bug: the page-end arrow sits on column 23, so dialogue was capped at 22 characters and 59 strings were re-wrapped. The tester tried the WIP in their own emulator and reported it worked.

## Phase 4: menus, names and graphics
- **Menus:** the command menu and window titles were redrawn in place, and about 290 item names were translated.
- **Fish data:** 111 fish got English names, alternative names and cooking notes.
- **Other screens:** the Fishing Note contents page, the character select panels, an English name-entry keyboard (8 letters) and the letters were done.
- **Default name:** Dad stays "Katsu", the tester's choice, because "Katsuhiro" doesn't fit.
- **Bug, reported by the tester:** "much of the UI has broken borders now". Cause: Claude had moved two window font blocks into the expanded ROM, but their loader can only read the first 2 MB. They were moved back into an unused bank, and the frames, ages and HP/Cash labels returned.
- **Title logo:** the tester picked "Legend of the Sea King" on a decision card. Later they supplied their own mock-up, "Super Legend of the Sea King" ("I imagine it would have jumped on the bandwagon of adding 'Super' to the beginning of every title"). Claude scaled it to 176 px wide in one 15-colour sprite palette, which turned the fade into bands.
- **Map captions:** shortened to fit 6 letters (Jetty, Ocean, Isle).

## Phase 5: playtest rounds
The tester sent screenshots, a save file (.srm) so Claude could open the Fishing Note, and a link to reference screenshots of the original. Fixes by round:
- **Round 1:**
  - The cut-off board title is now "Family Board".
  - The family board keyboard has English letters.
  - The fish name on the Fishing Note page vanished whenever the name had an odd number of letters. It's centred and fixed now.
  - The page's side labels are translated.
  - The map fish labels follow the Kawa 2 style: outlined, with a transparent background.
  - Town plaques are pictures: INN, a hook and a fish.
- **Round 2:**
  - The tackle shop item window is translated.
  - The board's "Line"/"Done" key label is translated.
  - The tester found a secret name in their own research (ふね太郎). It became **BoatTaro**, and Claude confirmed it in the emulator: 1000 yen and a full tackle box, while a control name got 100 yen and an empty box.
  - The paper's つり新聞 logo was redrawn as FISH NEWS, and about 20 of its tips that broke words at the right edge were re-wrapped.
- **Script pass 1** (asked for by the tester: "a sensible translation, that uses English names for the fish"):
  - Japanese fish names were replaced with English ones.
  - The marlin became a blue marlin, from the game's own ブルーマーリン.
  - Every inserted name was checked against its slot at the longest length. That forced a 14-letter cap from the paper headline and some renames. The tester chose "Jr. yellowtail" over "Yellowtail jr.".
  - Details: [docs/script_pass_1.md](docs/script_pass_1.md).
- **Sweep for leftover Japanese:**
  - The tester remembered Kawa 2's Japanese placeholder for empty gear slots. Umi leaves those slots blank in the original too.
  - The cup ranking board and the five letter envelopes were translated. Three rivals were shortened to 8 letters: Ginsuke, Kichiro and Haruki.
- **Round 3:**
  - The fishmonger's daily special cut off long names, which the tester found with screenshots. Each name over 12 letters got a short form for that window only (`build/market.py`).
  - The tester spotted an untranslated sea louse. It exposed a bug: Claude's name lookup skipped the first entry of each table, which had also left the first bait in Japanese.
- **Script pass 2:**
  - The tester asked for the save message ("I've memorized it.") to read naturally, and for a similar pass over the rest.
  - Claude read all 613 lines against the Japanese and changed 25: [docs/script_pass_2.md](docs/script_pass_2.md).

## Phase 6: warp test build and v1.0 (26-27 Oct)
The tester asked about a zone-warp cheat like Kawa 2's. Claude checked all 210 controller reads in the code and tried combos in the emulator, and found none. At the tester's suggestion it added a shoulder-button warp to a **separate test build** (`build/warp_test.py`, not part of the release): R goes to the next of the 7 zones and L to the previous one. The tester used it to visit every zone: "there really doesn't seem to be anything more to translate. I think the patch is done!" v1.0 was packaged the same day.

## Phase 7: series glossary (v1.1, 27 Oct)
The tester asked that every patch follow their *Super Legend of the River King* v1.3 glossary. The changes:
- Title Case names, matching fish names where the games share a fish.
- Yen, New Game / Erase Data.
- Arai, Bottarga and Kabayaki in the cooking notes.
- Sea Louse is now Sea Slater, and the Olive Sinker is the Date Sinker.
- Where a glossary name would clash or not fit, Umi keeps its own (for example Dragonet, because Umi also has a Flathead). The list is in [docs/series_glossary.md](docs/series_glossary.md).

v1.1 was rebuilt from source and matched. **v1.1 has not been playtested as a whole.**

## Phase 8: publishing (21-22 Nov)
Published here; then the source, docs and this log were added. The published IPS was rebuilt from this folder and matched byte for byte.

## How Claude worked
- **Reused** the Kawa 2 toolkit: the 65816 disassembler and simulator, LZSS, kanji matching and the IPS writer.
- **Wrote new tools:** an emulator driver, a RAM poker, a pointer-table finder, a graphics loader scanner and a kanji check sheet. The build also measures every inserted name against its slot.
- **Checked its work:** byte-identical round trips, screenshots from the emulator, and rebuilding the patch from source.
- **What it couldn't do:** land fish quickly enough to reach every screen, judge the art, or tell whether the English felt natural in play. The tester covered those with screenshots and the warp build.

## Known gaps and ideas
- Fishing fights, tournaments and the endings were reached by the tester, not by Claude.
- The two dead ゛゜ keys on the board and name keyboards are blank.
- There is one unused label (名前を入れてください) that no code seems to use.
