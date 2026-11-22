# Translation and localization style guide

**Goal:** English that reads as if the game had been written for English
speakers, while it remains plainly a Japanese game set in its own world. We
localize the *experience* (jokes land, characters sound like people, menus fit),
and we keep the cultural texture that makes the game what it is.

A game's own `notes/` can override any rule here. Write the reason down.

## 1. Priorities, in order

1. **Accuracy of meaning and intent.** Plot, information the player needs,
   puzzle clues, and foreshadowing must survive exactly. A clue that needs a
   Japanese pun gets a new English clue that works the same way, and a note
   explains the change.
2. **Character voice.** A gruff old swordsman, a polite shrine maiden, and a
   bratty kid must sound different in English, as they do in Japanese.
3. **Natural English.** No translationese: "As expected of Master!",
   "It can't be helped", "Eh?!", and "That person" for あの人 when a name or
   pronoun reads better.
4. **Fit.** Lines must fit the box and the font. Rewrite to fit. Don't cram or
   abbreviate. If it can't fit, ask for a font or space hack instead of
   dropping meaning.

## 2. Respecting Japanese culture

We don't turn the setting into an American one. Rice balls don't become
sandwiches, and yen doesn't become dollars.

- **Food, places, festivals, clothing, religion:** keep them
  (onigiri, Obon, kotatsu, torii, kami). If the term is unfamiliar and the
  game gives no context, add a few words of context in the line itself
  ("rice balls" the first time, "onigiri" later, or "the Obon festival for the
  dead") rather than a translator's note on screen.
- **Honorifics (-san, -kun, -chan, -sama, senpai, sensei):** choose one policy per game in
  `notes/characters.md`, by setting:
  - *Contemporary Japan* (school, slice of life, modern drama): **keep**
    honorifics. Who uses -chan versus a bare name is characterisation.
  - *Fantasy or non-Japanese setting*: **drop** them and carry the nuance in word
    choice ("Lady Aria", "Master", "big sis", a nickname, or use of the first name).
  - Never mix the two policies in one game. Keep "sensei" for teachers and doctors when
    the setting is Japanese.
- **Names:** use modified Hepburn romanization (Ryūji → Ryuji is fine for
  font limits; record the choice). Follow the official romanization when one
  exists (manuals, merchandise, later official releases). In a Japanese setting,
  use given name and family name in the order the game uses. Wordplay names (e.g. a
  character called "Pochi") can become English equivalents only if the joke matters
  to the story. Write the decision in the glossary.
- **Social register:** keigo, rough speech, and dialects carry status and personality.
  Show it with English register: formal versus casual vocabulary, contractions,
  sentence length. Kansai-ben is **not** automatically a Southern US accent. Use a
  light, consistent informal flavour and avoid real-world stereotypes.
- **Gender and pronouns:** Japanese often leaves out the subject. Don't
  guess a gender the source doesn't state. When the game hides a gender on
  purpose, keep it hidden.
- **Sensitive content:** translate what's there. Don't add slurs, crude humour, or
  internet slang that the source doesn't have. Don't remove or soften content
  either. Flag anything that might need a decision in the game's `notes/`
  and ask the project lead.
- **Wordplay and culture-specific jokes:** first try to rebuild a joke with the
  same function. If that fails, keep the meaning and the tone, even when the joke itself
  is lost. Never footnote a joke on screen.
- **On-screen Japanese in the art** (signs, shop curtains, kanji on clothing):
  leave decorative text as-is. Translate signage only when the player needs it,
  using the game's own text box if possible.

## 3. English conventions

- American English spelling, unless the game's notes say otherwise.
- Sentence case for dialogue. Title Case for proper nouns, item names, place names
  and skill names, which must follow the glossary exactly.
- Use an ellipsis as three periods `...` (or the font's `…` glyph if
  it has one; pick one for the game and use it throughout). Japanese stutters and pauses (「え、ええと…」)
  turn into natural English hesitation ("Uh... well..."), not every dot.
- Sound effects and interjections: use English ones ("Huh?", "Whoa!", "Ugh.")
  and not romaji ("Eh?!", "Ara ara") unless that character's voice depends on it.
- Use one exclamation mark at most, and a bare `?!` only for real shock. Japanese text
  uses 「！」 more than English wants.
- Use straight quotes `"` unless the font has curly quotes. Leave the Japanese
  brackets 「」『』 out of the English text.
- Numbers: digits for game stats and quantities, words for small counts in prose
  ("two keys" in dialogue, "x2" in menus).
- Menus and UI: short and consistent (Item, Equip, Status, Save). Use the same verb
  for the same action across the whole game.

## 4. Technical rules (enforced by `rhtk qa`)

- Keep every control code (`<name 01>`, `<wait>`, colour codes, `[XX]`)
  and its parameters. You may move one to a better place in the
  sentence, as long as it does the same job (e.g. a colour highlight on the
  translated item name).
- Respect `max_chars` per line and `max_lines` per page. Break lines yourself
  with the game's line-break token, at natural phrase boundaries.
- Use only characters the English font has (`tables/en.tbl`).
- No Japanese characters may remain in `en`.
- Leave `en` empty if a line isn't translated yet. Don't paste the Japanese.

## 5. Notes field

Use the entry's `notes` for anything a reviewer needs to know: a joke you
rewrote, an uncertain reading, a reference you looked up, or context like
"speaker is X". Write them in English, short, and explain *why*.
