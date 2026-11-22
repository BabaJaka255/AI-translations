# Tables

- `jp.tbl` decodes the original game text. Build it with `rhtk search`, then fill gaps by viewing the font in a tile viewer.
- `en.tbl` encodes the translation. It maps to the English font you insert (usually over unused kana/kanji tiles). Keep control-code lines (`/`, `*`, `$`) identical to `jp.tbl` so tokens survive.
- Keep both under version control and note every non-obvious code in `../notes/rom.md`.
