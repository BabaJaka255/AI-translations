# Mesen-S memory dumps

These are the dumps the tester took while the patch was being developed. Each one is a full VRAM (64 KB), CGRAM (512 B) or work RAM (128 KB) snapshot of a single screen.

| Dumps | Screen | Used for |
|---|---|---|
| `*Dialogue.dmp` | first dialogue box (unpatched game) | finding the font, text buffer and text routines |
| `*Shop.dmp`, `*Battle.dmp` | tackle shop, battle menu | menu label art, the shop copy routines, the status window |
| `*Title.dmp`, `*CS.dmp`, `*Content.dmp`, `*Creel.dmp` | title, character select, Fishing Note contents, creel (unpatched game) | window UI font, contents tilemap, title logo layout |
| `*Sign.dmp` | Stream village next to the dango banner (patched test build) | finding the banner on the second background layer |

Only one change was made to the originals: in `WorkRamSign.dmp`, the test character's name in the name buffer (`$086A`) was replaced with the default "Taro".

`src/tools/sim.py` uses `WorkRamDialogue.dmp` as the starting RAM for the 65816 text simulator.
