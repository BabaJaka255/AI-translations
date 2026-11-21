# Kawa no Nushi Tsuri 2 (SFC) — engine notes

What we learned about the game's internals while making *Super Legend of the River King*.
Addresses are SNES `bank:addr` (LoROM) unless marked **ROM** (file offset, no header).

    ROM offset = (bank & 0x7F) * 0x8000 + (addr & 0x7FFF)

Everything here was confirmed by building a patch that works in Mesen-S. Notes marked
*(inferred)* were never checked separately.

---

## 1. Cartridge layout

| | |
|---|---|
| Original | 12 Mbit LoROM, 1,572,864 bytes, CRC32 `716D3EFF` |
| Patched | expanded to 16 Mbit (2 MB). Banks `$30`–`$3F` are new free space |
| Checksum | recomputed at ROM `0x7FDC`–`0x7FDF` (see end of `build_patch2.py`) |

Data banks in the original:

| ROM | SNES | Contents |
|---|---|---|
| `0x28000`– | `$05:8000`– | fish records, name lists, main script, pointer table |
| `0x30000`– | `$06:8000`– | main 16×16 font (1bpp) |
| `0x38000`–`0x3B2FF` | `$07:8000`– | pre-rendered menu label art (2bpp) |
| `0x4C000`, `0x56000`, `0x58000`, `0x5C000` | | raw (uncompressed) 4bpp sprite sheets: gear and item icons |
| various | `$1E`–`$27` | LZSS-compressed tilesets, tilemaps and title graphics |

---

## 2. Text

### 2.1 Script and pointer table
* There are 537 pointers at **ROM `0x2BAD5`** (`$05:BAD5`), each a 16-bit address in bank `$05`. They point to 526 unique strings, and the text runs to ROM `0x2F379`.
* `dump_script.py` writes `script.json` (id, address, aliases, Japanese, raw hex).
* `reinsert.py` packs the strings back in place. Its round trip is byte-identical, which makes it a good first sanity check.

### 2.2 Encoding (Japanese)
| Byte | Meaning |
|---|---|
| `00` | end of string |
| `01`–`CB` | single-byte glyph: font index `(b-1)+0x2C0` (digits, punctuation, kana; see `knt2_single_byte.tbl`) |
| `CC` | line break |
| `CD`–`DF` | control codes, handled at `$82:871E` |
| `E0`–`EF xx` | two-byte kanji: glyph `((b&0x0F)<<8) \| xx` |

Insert codes used by the script (from `script_io.py`):

| Code | Inserts |
|---|---|
| `CD` | player name (up to 8 letters) |
| `CE` | bait name |
| `CF` | float/hook name |
| `D0`, `D2` | fly name |
| `D1` | lure name |
| `D3` | rod name |
| `D4` | second number or place |
| `D5` | food name |
| `D6` | tool or boat name |
| `D7` | compass direction |
| `D8` | fish name |
| `D9` | creature name |
| `DA` | a number |

The kanji were identified by matching glyph bitmaps against Noto Sans CJK:
* `analysis/match_kanji.py` and `run_match2.py` do the matching, with results in `build/data/match_res2.pkl`.
* Manual fixes are in `build/kanji_overrides.txt`.
* `build/data/knt2_kanji.tbl` is the merged table.

### 2.3 How English was added
* **English marker.** Byte `DF` (unused in the original) switches the rest of the string to English mode by setting bit `0x100` in `$0C`. In English mode, bytes `0x20`–`0x7E` are ASCII.
* **English glyphs.** An 8×16 ASCII font sits at **`$30:A000`** in the main font's 16×16 slot layout. Character `c` is drawn from

      $30:A000 + ((c-0x20)&7)*0x10 + ((c-0x20)&0xF8)*0x20

  using the game's own glyph blitter (`JSR $8956`) with `$06/$08` pointing at it.
* **Relocation.** English strings live in banks `$31`–`$32`. A lookup routine `xl` (in bank `$82` free space from `$F882`) maps old pointers to new ones:
  * It runs only when `$0C`=5 and `$0A`≥`$8000`.
  * It uses a 128-entry index at `$30:8000` (keyed by the high byte), then a sorted table at `$30:8200` of 6-byte entries (`old ptr, new ptr, new bank`), terminated by `FFFF`.
  * Strings with no entry fall through unchanged.
* **Three text loops are hooked.** Each has an entry hook (`t1`/`t3`/`t5`, which runs `xl` and restores) and a character hook (`t2`/`t4`/`t6`):

  | Loop | Entry hook | Character hook |
  |---|---|---|
  | `$82:8B47` (dialogue) | at `8B4D` | at `8B59` |
  | `$82:861F` (windows/menus) | `861F` | `862B` |
  | `$82:D695` | `D695` | `D6A1` |

* **String copies.** Some code copies a string into a buffer instead of drawing it. Copy sites that start with `LDA #5 / STA $0C` get a `JSL cp1`:
  * `$81:B898`
  * `$83:8823`, `8A21`, `8BB2`, `8BD3`, `8E54`, `90D0`, `928B`, `92A7`, `AEF7`, `AF45`
* **Postcard copies.** The four ending-letter copies at `$81:DEDC`, `DF42`, `DFA8` and `E00E` go through `cp3`, which copies 0xA0 bytes to `7F:2B90`.
* **Names** (player names, postcard messages) are stored without the `DF` marker. Every site that draws them was changed from `LDA #$0000/#$7000 → $0C` to `#$0100/#$7001` so they always render in English (see `name_entry.py`).
* **Line limits** (characters at 8 px):

  | Text | Limit |
  |---|---|
  | dialogue | 23 |
  | wide windows (ids 289, 297) | 32 |
  | contents page (id 53) | 48 |
  | postcards (ids 527, 528, 531, 534) | 28 per line, 5 lines, 0xA0 bytes |
  | fish notes | 22 on line 1, then 27; 4 lines |

### 2.4 Name lists and fish records
* **Fish records:** 73 records of 23 bytes from **ROM `0x28018`**. Bytes `+0x11` and `+0x13` are pointers to the name and the description.
* **Item and creature name lists** are in bank `$05`. Their ranges are stored in `build/data/zones.pkl`:

  | List | Entries |
  |---|---|
  | fish | 219 |
  | bait | 22 |
  | hook | 13 |
  | float | 10 |
  | lure | 68 |
  | rod | 21 |
  | fly | 135 |
  | food | 10 |
  | item | 23 |
  | animal | 30 |

* Their English names are in `build/zones_en.py`, keyed by the Japanese text.
* Name width limits are in `script_io.py` (`ZONE_LIMIT`).
* **Fishery price window:** 13 tiles wide, with short names from `fishery.py`.
* **Map labels:** 9 characters, with short names from `map_labels.py`.

### 2.5 Dialogue rendering (useful for the simulator)
* The staging buffer is at `7F:F000`, and the column → tile-offset table is at **ROM `0x10A22`**.
* `analysis/sim.py` runs the real text routines in a small 65816 interpreter (`cpu65816.py`) and renders the staging buffer as a PNG. It lets you check that every string fits without playing the game.
* `analysis/regression.py` compares every string against a baseline patch (`KNT2_REG_IPS`).

---

## 3. Graphics

### 3.1 LZSS compression (decoder at `$00:E5C2`)
* **Header:** 2-byte little-endian decompressed size.
* **Flag bytes** are read LSB-first: 1 = a literal byte, 0 = a 2-byte reference.
* **References** `b0 b1`: length = `(b1 & 0x0F) + 3`, position = `b0 | (b1>>4)<<8`. The window is a 4K ring, and the distance is `(out_len - pos) & 0xFFF`.
* The decoder handles bank crossing.
* In `build/lzss.py`:
  * `compress()` is a real greedy compressor.
  * `compress_literal()` stores all-literals (bigger, but trivially correct).
* **Typical loader:**

      LDA #src : STA $3E
      LDA #bank : STA $40
      LDA #dest : STA $42
      JSL $00:DA62 / $00:DA66

  `analysis/gfx/scan.py` finds every loader by this byte pattern. To replace a compressed asset, store a new blob in free space and rewrite the `#src`/`#bank` immediates at the call site. That's what `ui_font.py`, `content_page.py`, `cs_names.py`, `title_logo.py` and `map_labels.py` do.

### 3.2 DMA helpers
* `JSL $00:DA6A`: VRAM DMA with `$42/$44` = source, `$46` = VRAM word address, `$3E` = size.
* `JSL $00:DA52`: the same, used by name entry and postcards.
* `$00:DA42` multiplies `$3E*$42 → $46` (the simulator hooks it).

### 3.3 Fonts and label art
| What | Where | Format |
|---|---|---|
| Main font | ROM `0x30000`, glyph `g` at `0x30000+(g&0xFF8)*32+(g&7)*16`; TL/TR `+0/+8`, BL/BR `+0x80/+0x88` | 1bpp 16×16 |
| Window UI font (HP/Yen/EXP, Cmd) | LZSS `$0C:F800` → patched copy `$30:C000`; tiles `$100`–`$19F`, 8×16 = tile t + t+0x10; five loaders | 2bpp |
| Menu labels | ROM `0x38000`–`0x3B2FF`. 12-tile rows (0x180 bytes: 12 top tiles, then 12 bottom) to `0x3A3FF`, then 16-tile rows (0x200) | 2bpp, bg 1 / ink 3 |
| Map label font | LZSS `$06:F000` (80 tiles, loaded at `$81:C0F6`); tile = code + `$84` | 2bpp 8×8 |
| Name-entry keyboard | VRAM `$2A00` (48 cells) + `$3000` (62 cells); selection tables at `$01:B518…` | 16×16 cells, staging layout |
| Postcard keyboard | VRAM `$3400`, 3 modes × 50 cells, code `$01:E7EE`, `$01:EDxx`–`F480` | same |

"Staging layout" means 8 glyphs per 0x200-byte line, with TL/TR at `+0/+0x10` and BL/BR at `+0x100/+0x110`.

### 3.4 Screens we changed
| Screen | Data | Code site |
|---|---|---|
| Title logo + START | LZSS `$1E:EFE5` (0xC000 bytes; OBJ tiles at +0x8000); OBJ palette 0 at ROM `0x3FBC0`. Logo = sprite group `$01:9B08` (192×48); START = `$01:9CD0` | `$81:9819` |
| Fishing Note contents | tilemap LZSS `$21:A67F` → `7F:B800`, labels drawn from string 53 into tiles `$140`–`$19F` | ROM `0xCE3B` |
| Character select | tilemap LZSS `$21:9674` (two identical screens) | `$81:A664` |
| Fishery price window | template `$02:C7F6`, drawn at `$82:AAE6`; name tiles `$1A0`/`$1B0` | `$82:ABE0`, `ABFE`, `AC16` |
| Creel window | fish name copied at `$82:A9CA`, `A9FF` | |
| Fishing Note map labels | `$81:D143`–`D1AB` | |
| Field (town) tilesets | table at **ROM `0x74E`**: 4-byte (addr, bank) entries, one per area. Tilesets: `21:FAF7`, `22:E0AF`, `23:CE21`, `24:BDBB`, `25:A381`, `26:91D1`; shared interiors `26:F1EA`. Inn, fish-shop and tackle plaques are 2×2 tiles; the dango banner is on BG2 in set 21 | |
| Item icons | raw 4bpp, 16 tiles per 0x200-byte row from ROM `0x56000`. Stereo/Mono = row 12, cols 8–11 and 12–15 | |
| Empty gear slots | raw 4bpp. ROD `0x58000` r28 c14; FLOAT `0x5C000` r4 c14; SINKER r4 c12; HOOK r12 c14 (16×32 each); NONE `0x4C000` r26 c12 (32×16). Background 1, ink F | |

### 3.5 Other facts
* **Secret name:** `$81:B077` compares 8 bytes of the brother's name with **ROM `0xB0F0`** (originally つり太郎). It unlocks a fully stocked tackle box. The patch sets it to `FishTaro`.
* **Postcard buffer:** `7F:2B90`, 0xA0 bytes, 5 lines × 28 columns.
* **Name length:** the limit is at `$01:B38C`; the patch raises it from 4 to 8.

---

## 4. Free space used by the patch

| Where | Contents |
|---|---|
| `$30:8000` / `$30:8200` | relocation index and table |
| `$30:A000` | 8×16 ASCII font |
| `$30:C000`, `$30:D000` | window UI font, contents tilemap |
| `$31`–`$32` | English strings |
| `$38:8000`–`9D40` | name-entry blocks, tables, code |
| `$38:A000`–`CAB2`, `CC00` | postcard blocks, tables, code |
| `$38:CD00` / `CE80` | fishery short names / code |
| `$38:CF80` | map ASCII→slot table |
| `$38:D000` | character-select tilemap |
| `$39:8000` | title graphics (literal LZSS) |
| `$3B:8000` | map label font |
| `$3B:8800`–`$3D` | recompressed field tilesets |
| `$3F:8000` | map-only short names |
| `$82:F882`– | text trampolines (`xl`, `t1`–`t6`, `cp1`, `cp3`) |
| `$82:FD00` | creel helper |
| `$82:FD80` | map label helper |

---

## 5. Finding things you can't locate in the code
1. **Plane-mask scan** (`analysis/gfx/maskscan2.py`). Take a screenshot, threshold the white text, and slide 8×8 bit patterns over the raw ROM to find uncompressed tiles. This found every gear placeholder.
2. **Match against decompressed blocks** (`gfx/match.py`, `where.py`). Decompress every LZSS block found by `scan.py`, index its tiles by shape (palette-independent), and look up the tiles in a screenshot or VRAM dump.
3. **VRAM / CGRAM / WRAM dumps from Mesen-S** are the quickest way to find a screen's tiles. They were how the BG2 banner was found.
4. **Hooks always check the original bytes** before patching (`assert orig[...] == ...`). In a related game this turns "patched the wrong place" into an immediate, readable error.
