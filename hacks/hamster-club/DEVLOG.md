# Hamster Club: development log

How the English patch was made, in order. "The lead" is the human who ran the project; "Claude" is the AI
(Anthropic's Claude, working in a cloud sandbox with a Python toolkit and a headless emulator).

## Starting point (2026-10-30)
- The lead picked *Hamster Club* (ハムスター倶楽部, Jorudan, 1999), a Game Boy Color hamster-raising sim, and
  supplied their own cartridge dump. No earlier fan translation or technical documentation was found.
- The work used a small general toolkit (`rhtk`, in `src/toolkit/`) set up earlier the same day for this project.
  Several gaps in it surfaced on this ROM and were fixed along the way: a Game Boy (SM83) disassembler,
  "plugin" script blocks for custom formats, GB ROM expansion, fixed-width table blocks, 8x16 sprite tile order,
  palette support and BPS size handling.

## Phase 1: text engine and script dump (2026-10-30)
- **Font and encoding:** the font was found at ROM 0xFE250 by viewing the ROM as 2bpp tiles. It holds kana and
  A-Z; dakuten are separate bytes. `tables/jp.tbl` was generated from the font order (`tools/make_jp_tbl.py`).
- **Event script:** Claude disassembled the text routines and found the script is bytecode, not plain text:
  51 scenes with commands 0xE8-0xF9 (line, page, wait, name insert, menus, portraits). `tools/hcscript.py`
  decodes and re-encodes it. 465 messages were dumped to `script/events.json`.
- **Box size:** 18 characters x 2 lines, menu options 8 characters at most.
- **Glossary and voices:** Claude drafted `docs/glossary.md` and `docs/characters.md` with open questions
  (honorifics, the rival's っち nickname as "-chi", short breed names like "Djungar."). The lead approved all of it:
  "Everything looks good!"

## Phase 2: English engine (2026-10-30)
- **Font:** English lowercase drawn over unused hiragana tiles (`tools/make_font.py`), later a "+" for "Pellets+".
- **Space:** a far-jump hook at 0x3FA0 lets text live in new banks (the ROM was expanded from 2 to 4 MiB), so
  English longer than the Japanese can be relocated.
- **Bug found in testing:** a full line followed by a line break drew over the date box. That is a quirk of the
  original routine, which never had full lines; it was patched.
- **Honorifics:** the -san/-kun/-chan suffixes the player picks were still Japanese; they were moved to 0x3FD0
  where the English fits.

## Phase 3: translation (2026-10-30)
- Claude translated the event script (462 of 465 messages; three one-glyph entries are probably misparsed bytes
  and were left alone). QA: 0 errors.
- About 150 lines were rewritten so no box ends in a single stray word. Testing showed the blinking "next" icon
  covers column 18 of line 2, so only punctuation goes there (the Japanese script does the same).
  `tools/hc_tr.py` enforces this and word-wraps `script/events_en.txt` into `events.json`.
- Spot checks in PyBoy: intro, name and honorific choice, starter pick, shop tutorial.

## Phase 4: everything outside the story (2026-10-30 to 2026-10-31)
- **Name entry:** the kana page could already type English (the letters had replaced the kana) but in scrambled
  order. `tools/make_keyboard.py` reorders it a-z, adds punctuation and English titles ("Your name?", "Cage name?").
- **Home menu:** it is a picture, not text, so its labels were redrawn as tiles (`tools/make_homemenu.py`).
- **Tables:** 91 personality traits, 88 trick names, mood/health/cleanliness, food, body type, training progress,
  care results, item lists, cups, schedule, save and title menus, game-over lines (fixed-width blocks; a new toolkit
  mode moves strings that don't fit).
- **Contests:** announcers (Charm Awards, Leapfrog, Pretty Cup), 34 rival hamster names, home-screen age line
  ("🎂06mo"). Names are capped at 8 letters: ビビッチ is "Bibi", ジョセフィーヌ "Josefine".

## Phase 5: fresh-game playtest and v0.9 (2026-10-31)
- Claude played a new game through week 3 in PyBoy and fixed about 15 screens that only broke in real play
  (overflowing cage text, Japanese schedule and icon captions, weekly report labels).
- The 8 contest title banners were redrawn in English (`tools/make_banners.py`).
- **v0.9** test build. Claude could not get a contest to start in the emulator, so said so.

## Phase 6: contest fixes, v0.10 (2026-10-31)
- **Reported by the lead** after playing in their emulator: "a lot of the text there is still untranslated or
  otherwise glitchy."
- Claude found RAM values that force each of the 8 events (recipe in `docs/ENGINE_NOTES.md`, "Contest screens")
  and played them all. Broken parts traced to text the code builds with immediate stores (not in any table),
  graphics scoreboards and a missed Pretty Cup line. Fixed in `tools/make_contest.py` and the `racetitles` block.

## Phase 7: audit, v0.11 (2026-11-01 to 2026-11-02)
- The lead asked for a full review for mistakes and leftover strings, and asked for the baked-in art to be sent
  to them for redrawing.
- A ROM-wide scan (`tools/textscan.py`) and a scan for immediate-store strings found one missed line (the popup
  for vacuuming up a hamster in the "Outside" cage). A reread fixed the contest result box ("Prize 75G won!"),
  event-name mismatches (Snack, Bars, Seeds, Wheel), "100m", "WHEEL RACE!", ellipses and one trait.
- Claude played all 88 trick animations and ripped every graphic with Japanese lettering (title, boot logos,
  ACCIDENT banner, event labels, illness picture, 62 tricks) with real colours, checked that each rip packs back to
  the original bytes, and wrote `src/gfx/orig/art/README.md` saying what each piece of lettering means.
- **Decision (lead):** the shop's ちりょう option became "Heal", because "Treat" clashed with the food "Treats".

## Phase 8: art redraw, v0.12 (2026-11-02)
- The lead asked whether Claude could restyle lettering "in a way that doesn't look like a font". Claude drew
  KOFF cough marks on the illness picture pixel by pixel in two styles (`src/gfx/demo/`). The lead: "That looks
  much better than I'd thought. Give it a go for the rest of the sheets."
- Claude wrote a lettering tool (`tools/letter.py`: its own stroke alphabet with slant, wobble, outline, shadow),
  a screen-space editor that maps screen pixels to tile pixels from a save state (`tools/frame.py`,
  `tools/screen.py`), a wavy-ribbon renderer (`tools/ribbon.py`), and `tools/make_art.py` with one function per sheet.
- **Constraint:** tiles shared across a screen (for example a blank tile used everywhere) cannot take ink, so
  lettering sometimes zigzags around them.
- **Dead end:** 17 tricks seemed to have no lettering. The capture script pressed A, which skips to the end of a
  trick. Recaptured without input, the lettering appeared and was redrawn. Tricks 19 and 57 have only sweat and
  pain marks and were left alone.
- Event labels became BIRTH / DEATH / OUCH! / SICK / GONE!, with a small code tweak so each label's halves sit
  together. Sound-effect words like CHI, WAG, GRIP, ITCH, FREEZE!, GO NE and RUB are loose renderings and were
  flagged to the lead for review.

## Testing summary
- Claude: PyBoy 2.9 (headless) only. Fresh game to week 3, all 8 contests (forced), all trick animations,
  boot and title. Every build: QA 0 errors, BPS re-applied to the clean ROM.
- The lead: played builds in their own emulator and reported the contest problems. No real-hardware or flash-cart
  test is recorded.
- Not tested: the birth event, Breeders' Cup contest variants, a full playthrough.

## How Claude worked and what it could not do
- It could run the game headless and look at screenshots, RAM and VRAM, but not play by feel. Contests were
  reached by poking RAM, not by playing to them.
- Its own checks: `rhtk qa` (box fit, tokens), a ROM-wide leftover-text scan, round-trip checks for every ripped
  graphic, and re-applying the BPS to the clean dump after every build. On 2026-11-22 the published source was
  rebuilt from a clean copy and matched the release byte for byte.
- Art direction and the final say on wording were the lead's.

## Known gaps and ideas
- Compare the dump with the No-Intro DAT (no hash was found published online).
- Find and check the birth event screen; play the Breeders' Cup variants.
- A read-through of the whole script by a native speaker in the emulator.
- Review the looser sound-effect words.
- The `title` and `boot` art functions need two save states that were not kept (see `src/BUILD.md`).
