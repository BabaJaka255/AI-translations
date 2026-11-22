# Translation process

How a script goes from a raw dump to a polished English script. This is written
for agents working in project threads, and it works the same for people.

## Before the first line

1. **Gather context.** Play footage, the manual, a wiki or TCRF page, and the official
   English names of anything in a series that already has English releases.
   Write sources in `notes/rom.md`.
2. **Glossary (`notes/glossary.md`).** Pull out every recurring proper
   noun and game term: characters, places, items, skills, enemies, and menu words.
   Decide on each one once, with the reason. The menu and item blocks are
   usually the fastest way to get these.
3. **Character sheets (`notes/characters.md`).** For each speaking
   character: their Japanese speech traits and the English voice we'll give them, plus
   the honorific policy (see STYLE_GUIDE §2).
4. the project lead reviews the glossary and the voice choices before the bulk of the work
   starts. Changing them later means editing hundreds of lines.

## Translating

- Work through a script in order of **scene**, not in ID order, when the IDs jump around.
  Read 20 to 50 entries before and after for context: who's speaking, and what just happened.
- Fill in only `en` and `notes`. Don't change `id`, `offset`, `length`,
  `pointers` or `jp`.
- Keep the speaker, the tone, and the control codes. Rewrite lines to fit the box
  limits from the block's `box` setting.
- Translate in batches of a manageable size (one scene, or about 100 lines), then
  run `rhtk qa` and fix everything before moving on.
- If something is unclear (an obscure reading, a pun, missing context), give your best
  reading and add `notes: "UNSURE: ..."`. Don't stall on it. Reviewers search for `UNSURE`.
- Machine translation (including the DeepL connector) is useful for checking
  your reading of a hard line, but it isn't the final text. Every line has to be
  written to this style guide by the translator.

## Passes

1. **Translation pass.** Faithful and complete, with every line filled in and QA clean.
2. **Edit pass.** Read in English only, scene by scene. Fix stiffness, character
   voice, repetition, and inconsistencies with the glossary. Check against the Japanese
   only where a line seems off.
3. **In-game pass.** After a build: line breaks, pacing, text that runs out of its box,
   and lines that read wrong in context. Fix them in the script, then rebuild.

## Status markers

Use the `notes` field so progress can be grepped:

- `UNSURE: ...` needs a second opinion
- `REWRITE: ...` meaning was changed on purpose (puns, cultural references), with the original sense given
- `CHECK-INGAME` should be looked at in context during playtesting

`rhtk qa` reports translated and total counts per block, so use it for
progress updates.
