"""Wrap paged speech-box text (tutorial: pages split by /p, lines by /r) to a pixel width.

  python3 c3_wrap_pages.py <out.tsv> --ids 787 788 [--width 340] [--lines 4]

Reads the English from script/elf.json (set C3_ELF to a built ELF so widths match the English fonts), keeps
every /p and control code, and rewraps each page with /r so the game never wraps by itself (it splits words:
"take i/t"). A page longer than the box (4 lines) is split at a sentence end into two pages joined with the
script's own "/w045/kB/s00/p"; pages with no sentence end to split at are reported.
"""
import argparse
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import c3_tr as T  # noqa: E402
from c3font import idx, table  # noqa: E402

PAGE = re.compile(r"(/p)")
NEWPAGE = "/w045/kB/s00/p"
SENT = re.compile(r"(?<=[.!?])(?:/c0)? ")
ACTION = re.compile(r"/i[0-9]+")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--ids", type=int, nargs="+", required=True)
    ap.add_argument("--width", type=int, default=340)
    ap.add_argument("--lines", type=int, default=4)
    ap.add_argument("--src", help="TSV with the unwrapped English (default: script/elf.json)")
    ap.add_argument("--margin", type=int, default=0,
                    help="follow each /m box: wrap width = box width (4th number of its 2nd group) - margin, "
                         "lines = its 5th number; --width/--lines only until the first /m")
    a = ap.parse_args()
    box = {"w": a.width, "lines": a.lines}
    elf = open(T.ELF_PATH, "rb").read()
    t, nt = table(elf, "talk"), table(elf, "name")

    def w(code):
        e = t[idx(code)] if 0 <= idx(code) < len(t) else (0xFF,)
        if e[0] == 0xFF and 0 <= idx(code) < len(nt):
            e = nt[idx(code)]
        return e[3] if e[0] != 0xFF else 18

    def wrap(seg_text):
        lines = []
        for seg in seg_text.split("/r"):  # existing /r breaks are kept
            cur = ""
            for word in seg.split(" "):
                trial = (cur + " " + word) if cur else word
                if cur and T._width(trial, w) > box["w"]:
                    lines.append(cur)
                    cur = word
                else:
                    cur = trial
            lines.append(cur)
        return lines

    def fit(text, where):
        """text of one box (no /p, no action): wrapped, split into pages if too long."""
        lines = wrap(text)
        if len(lines) <= box["lines"]:
            return "/r".join(lines)
        cuts = [m.start() for m in SENT.finditer(text)]
        if not cuts:
            print(f"#{where}: {len(lines)} lines, no sentence end to split at: {text[:70]}")
            return "/r".join(lines)
        mid = len(text) / 2
        c = min(cuts, key=lambda x: abs(x - mid))
        m = SENT.match(text, c)
        left, right = text[:m.end() - 1], text[m.end():]
        return fit(left, where) + NEWPAGE + fit(right, where)

    by = {e["id"]: e for e in T.load("elf")["entries"]}
    if a.src:
        for line in open(a.src, encoding="utf-8"):
            if line[:1].isdigit():
                k, v = line.rstrip("\n").split("\t", 1)
                by[int(k.rstrip("!"))] = {"en": v}
    out = []
    for i in a.ids:
        box.update(w=a.width, lines=a.lines)
        res = []
        for pg in PAGE.split(by[i]["en"]):
            if pg == "/p":
                res.append(pg)
                continue
            # control-code tail (waits/sounds) and tutorial actions stay where they are
            parts = re.split(r"((?:/w[0-9]+|/k[A-Z]|/s[0-9]+|/i[0-9]+|/m(?:\([^)]*\))+)+)", pg)
            for k, part in enumerate(parts):
                if k % 2:
                    m = re.findall(r"/m\([^)]*\)\(([-0-9]+),([-0-9]+),([-0-9]+),([0-9]+),([0-9]+)\)", part)
                    if m and a.margin:
                        box.update(w=int(m[-1][3]) - a.margin, lines=int(m[-1][4]))
                res.append(part if k % 2 else fit(part, i) if part else part)
        out.append(f"{i}\t{''.join(res)}")
    open(a.out, "w", encoding="utf-8").write("\n".join(out) + "\n")


if __name__ == "__main__":
    main()
