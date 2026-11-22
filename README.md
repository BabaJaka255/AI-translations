# AI-translations
Collection of Claude-translated romhacks. Done mostly out of desperation. Use human translations when able.

**Website: https://babajaka255.github.io/AI-translations/** lists every hack and lets you apply the patches in your browser.

## What's here
Each hack lives in its own folder under [`hacks/`](hacks/):

| Path | What it is |
|---|---|
| `README.md` | What the patch does, which game file it needs (with checksums), how to apply it, and how it was tested |
| `patches/` | The patch files |
| `src/` | Everything needed to rebuild the patch from your own copy of the game: build scripts, tools, the original and translated script, tables, extracted and edited graphics. `src/BUILD.md` has the steps |
| `docs/ENGINE_NOTES.md` | How the game works under the hood: text encoding, compression, fonts, hooks and addresses |
| `DEVLOG.md` | How the hack was made, in order: what was tried, what failed, the bugs found in testing, and who decided what |
| `hack.json` | Metadata used to build the website |

No ROMs, disc images or patched games are hosted here. You need your own copy of the game.

## About AI use
Every hack here was made with substantial help from Claude (Anthropic): reverse engineering, code, translation and graphics work. A human chose the games, supplied the dumps, tested the builds, made wording calls and reported bugs. Each hack's `DEVLOG.md` and README say exactly who did what, and how much testing each one has had.

## Building on this work
Fixes, improvements, retranslations and ports to related games are welcome. Start with the hack's `src/BUILD.md` to rebuild the patch, then `docs/ENGINE_NOTES.md` and `DEVLOG.md`.

License, unless a hack's README says otherwise:
- Code, tools and docs made for these projects: MIT.
- Translation text and new art: CC BY 4.0.
- Extracted game material remains the property of its rights holders and is included for research and modding.
- Third-party tools and fonts keep their own licenses, noted where they're used.

## The website
[`site/build_site.py`](site/build_site.py) builds the site from every `hack.json`, and [`.github/workflows/pages.yml`](.github/workflows/pages.yml) republishes it whenever a hack changes. In-browser patching uses [Rom Patcher JS](https://github.com/marcrobledo/RomPatcher.js) by Marc Robledo (MIT), vendored in `site/vendor/`. Games whose image is over 512 MiB get download links and instructions instead, since browsers can't patch files that large reliably.

To preview it locally: `python3 site/build_site.py _site`, then open `_site/index.html` through a local web server (for example `python3 -m http.server -d _site`).
