# Tsuri Tarou English patch v0.9: test checklist

## Applying
- Base ROM: **Tsuri Tarou (Japan)**, 1,048,576 bytes, no copier header, CRC32 **BBBFF8D8**.
- Apply `Tsuri Tarou (English) v0.9.ips` with Flips, Lunar IPS or your emulator's soft-patching.
- The result is 2 MB (16 Mbit) with CRC32 **D5678007**. If your patcher reports a different size or CRC, tell me which tool you used.

## Please check
1. **Title**: "START" under the logo (the logo stays Japanese on purpose).
2. **File select**: Start / Erase Data, columns Name / Fishing / Walking.
3. **Name entry**: the letter keyboard works, letters appear in the name box, B deletes, "End" finishes. Names are up to 6 characters.
4. **Date entry**: "Enter the date", date shows as 1994/ 01/ 01, "End" finishes.
5. **Opening story page** types out in English.
6. **Map**: "Fish" and "Walk" labels at the top. Walk into a spot: the sign shows the English fish name and 5 bullet points, none of it running off the board.
7. **SELECT fish list**: English names; press A on a fish: the records screen shows that fish's name at the top.
   Watch for a one-frame flicker or a black flash when the records screen opens (the name is drawn with a tiny
   screen blank). Tell me if it is visible or if the name ever shows the wrong fish.
8. **Fishing**: nothing should look different from the Japanese version; the fishing power counter during the fight is labelled "Fish".
9. **End of day / going home**: the story pages (next morning, came home early, day without the Nushi) are English.
10. **Save and reload**: quit, reload the save, check the name and records still look right.
11. **Erase Data** on a save: "Are you sure?" with Yes / No. (I couldn't reach this one in my emulator.)
12. **Ending** (if you catch the River Nushi): the ending page is English.

## Known limits
- Story pages can't show the digit 0 (that tile is the blank space on those screens). The current text doesn't use it.
- The 8x8 font raises the tails of g, j, p, q and y so lines don't touch; they can look a little like 9.
- Anything still in Japanese, or any garbled tiles: a screenshot and where it happened is all I need.
