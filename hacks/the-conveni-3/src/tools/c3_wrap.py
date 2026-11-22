"""Insert line breaks into English talk-box text so the game never has to wrap it itself.

  python3 c3_wrap.py <in.tsv> <out.tsv> [--width PX] [--brk /r] [--font talk]

Lines are "id<TAB>text". Existing breaks (/r /n) are kept; words are wrapped greedily so no line is wider
than PX (default: the widest Japanese line among the entries that already have breaks, in that font).
"""
import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import c3_tr as T  # noqa: E402
from c3font import idx, table  # noqa: E402

BRK = re.compile(r"(/[nr])")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("inp")
    ap.add_argument("out")
    ap.add_argument("--width", type=int)
    ap.add_argument("--brk", default="/r")
    ap.add_argument("--font", default="talk")
    ap.add_argument("--block", default="cn3")
    a = ap.parse_args()
    elf = open(T.ELF_PATH, "rb").read()
    t, nt = table(elf, a.font), table(elf, "name")

    def w(code):
        e = t[idx(code)] if 0 <= idx(code) < len(t) else (0xFF,)
        if e[0] == 0xFF and 0 <= idx(code) < len(nt):
            e = nt[idx(code)]
        return e[3] if e[0] != 0xFF else 18

    rows = [l.rstrip("\n").split("\t", 1) for l in open(a.inp, encoding="utf-8") if "\t" in l]
    by = {e["id"]: e for e in T.load(a.block)["entries"]}
    width = a.width
    if not width:
        width = 0
        for i, _ in rows:
            jp = by[int(i.rstrip("!"))]["jp"]
            if "/r" in jp or "/n" in jp:
                for seg in T.SPLIT.split(jp):
                    seg = T.G.CTRL.sub("", seg)
                    width = max(width, sum(w(int.from_bytes(c.encode("cp932"), "big")) + 2 for c in seg))
    print("width", width)
    out = []
    for i, text in rows:
        lines = []
        for part in BRK.split(text):
            if BRK.fullmatch(part):
                continue
            def greedy(lim):
                res, cur = [], ""
                for word in part.split(" "):
                    trial = (cur + " " + word) if cur else word
                    if cur and T._width(trial, w) > lim:
                        res.append(cur)
                        cur = word
                    else:
                        cur = trial
                res.append(cur)
                return res
            best = greedy(width)
            lim = width
            while lim > 40:  # balance: the narrowest width that needs no more lines
                trial = greedy(lim - 8)
                if len(trial) > len(best):
                    break
                best, lim = trial, lim - 8
            lines += best
        # keep a trailing control code (e.g. /kA) on the last line
        out.append(f"{i}\t{a.brk.join(lines)}")
        if len(lines) > 3:
            print(f"#{i}: {len(lines)} lines")
    open(a.out, "w", encoding="utf-8").write("\n".join(out) + "\n")


if __name__ == "__main__":
    main()
