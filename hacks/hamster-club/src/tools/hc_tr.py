"""Fill script/events.json "en" fields from a compact authoring file.

Authoring format, one entry per line:  NNNN<TAB>text
  ／  forced line break      ‖  wait + clear (new page)
  ⏎  wait (no clear)        ¶  clear
  {n0}..{n5}  name tokens (<name 00>..)
  ^ at the start: the message begins on line 2 of a box already in use
  text@@menu   text pages, then a menu: rows split by "/", columns by "|"
  M:menu       a menu only (a leading ¶ is kept)
  =raw         exact en text, no wrapping (rhtk syntax)
Pages are word-wrapped to 18 columns and 2 lines; overflow continues on a
new page (<wait><clr>). Line 2 uses column 18 only for punctuation (the
"press A" icon blinks there). A sentence that would run off a page but fits
on one page starts a new page; sentences that still run over are printed as
warnings so they can be reworded. Text after ／ must fit on its line.
Menu labels: 8 columns in a 2-column row, 17 alone.

Usage (game folder): python3 tools/hc_tr.py script/events_en.txt
"""
from __future__ import annotations

import json
import re
import sys

W, LINES = 18, 2
# The blinking "press A" icon sits over the last column of line 2, so line 2
# only uses column 18 for punctuation (the Japanese script does the same).
PUNCT = '.,!?…"\''


def fits(line: int, end: int, word: str) -> bool:
    """Can a word ending at column `end` go on this line of the page?"""
    return end <= W - 1 or (end == W and (line % LINES == 0 or word[-1] in PUNCT))
NAME_W = {"0": 8, "1": 8, "2": 5, "3": 8, "4": 0, "5": 0}
MARK = {"／": "<br>", "‖": "<wait><clr>", "⏎": "<wait>", "¶": "<clr>"}


def width(word: str) -> int:
    w = len(re.sub(r"\{n\d\}", "", word))
    return w + sum(NAME_W[d] for d in re.findall(r"\{n(\d)\}", word))


def names(s: str) -> str:
    return re.sub(r"\{n(\d)\}", lambda m: f"<name 0{m.group(1)}>", s)


WARN: list[str] = []


def _lines(words: list[str], col: int = 0, line: int = 0) -> int:
    """Lines the words take when started at column col of the given line."""
    n = 1
    for word in words:
        w = width(word)
        need = w + (1 if col else 0)
        if not fits(line + n - 1, col + need, word):
            n, col = n + 1, w
        else:
            col += need
    return n


def wrap(text: str, start_line: int = 0) -> str:
    """Word-wrap to W x LINES pages. A sentence that would run off the page
    but fits on a page of its own starts a new page instead."""
    out = []
    line, col = start_line, 0
    page_used = start_line > 0
    after_br = False  # the text after a forced ／ must fit on its line
    for tok in re.split(r"([／‖⏎¶])", text):
        if tok in ("‖", "¶"):
            out.append(MARK[tok])
            line, col, page_used, after_br = 0, 0, False, False
            continue
        if tok == "⏎":
            out.append(MARK[tok])
            continue
        if tok == "／":
            out.append("<br>")
            line, col = line + 1, 0
            after_br = True
            continue
        sentences = [s.split(" ") for s in re.split(r"(?<=[.?!…])(?<!Mr\.)\s+(?=\S)", tok) if s.strip()]
        for words in sentences:
            words = [w for w in words if w]
            for word in words:
                if width(word) > W:
                    raise ValueError(f"word too wide: {word!r}")
            # lines this sentence needs from the current spot
            here = _lines(words, col, line)
            if not after_br and page_used and line + here > LINES and _lines(words) <= LINES:
                out.append("<wait><clr>")
                line, col = 0, 0
            first_page = True
            for word in words:
                w = width(word)
                need = w + (1 if col else 0)
                if not fits(line, col + need, word):
                    if after_br:
                        raise ValueError(f"line after ／ is too long: {' '.join(words)!r}")
                    line, col = line + 1, 0
                    if line >= LINES:
                        out.append("<wait><clr>")
                        line = 0
                        first_page = False
                    else:
                        out.append("<br>")
                    need = w
                if col:
                    out.append(" ")
                out.append(word)
                col += need
                page_used = True
            if not first_page:
                WARN.append(f"sentence runs over a page: {' '.join(words)[:24]!r}…")
        if line >= LINES:
            raise ValueError(f"page overflow in {text!r}")
    return names("".join(out))


def menu(spec: str) -> str:
    rows = []
    for row in spec.split("/"):
        cols = [c.strip() for c in row.split("|")]
        limit = 8 if len(cols) == 2 else 17
        for c in cols:
            if width(c) > limit:
                raise ValueError(f"menu label too long ({width(c)}/{limit}): {c!r}")
        rows.append(" " + cols[0] if len(cols) == 1 else " " + cols[0].ljust(8) + " " + cols[1])
    return "<br>".join(rows)


def build(src: str) -> str:
    if src.startswith("="):
        return src[1:]
    if src.startswith("M:"):
        spec = src[2:]
        pre = "<clr>" if spec.startswith("¶") else ""
        return pre + menu(spec.lstrip("¶"))
    start = 1 if src.startswith("^") else 0
    src = src.lstrip("^")
    text, _, m = src.partition("@@")
    return wrap(text, start) + (menu(m) if m else "")


def main(path: str, script: str = "script/events.json"):
    s = json.load(open(script, encoding="utf-8"))
    by = {e["id"][-4:]: e for e in s["entries"]}
    n = 0
    for ln in open(path, encoding="utf-8"):
        ln = ln.rstrip("\n")
        if not ln.strip() or ln.startswith("#"):
            continue
        key, _, src = ln.partition("\t")
        try:
            WARN.clear()
            by[key]["en"] = build(src)
        except ValueError as ex:
            sys.exit(f"{key}: {ex}")
        for w in WARN:
            print(f"{key}: {w}")
        n += 1
    # entries that are only control codes need no translation
    jp_chars = re.compile(r"[぀-ヿ㐀-鿿・]")
    for e in s["entries"]:
        if not e["en"] and not jp_chars.search(re.sub(r"<[^>]*>", "", e["jp"])):
            e["en"] = e["jp"].replace("　", " ")
            n += 1
    with open(script, "w", encoding="utf-8") as f:
        json.dump(s, f, ensure_ascii=False, indent=1)
        f.write("\n")
    print(f"{n} entries filled")


if __name__ == "__main__":
    main(*sys.argv[1:])
