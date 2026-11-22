"""Check the fixture descriptions (CN3 #26, 64-byte fields) against the two places that show them.

  C3_ELF=<built ELF> python3 tools/c3_wrap_desc.py

The Fixture details panel (~250 px of the small font, 2 lines) now wraps by word on its own: c3_build encodes these
descriptions with a "/A" marker and 2-byte spaces, and tools/c3_wordwrap.py teaches the panel's layout to break
only at spaces. Line breaks in the text are not needed (the panel strips /n; the Edit Interior bar would show a
hidden second line). This reports any description that would need 3 panel lines (word wrap at LIMIT) or is wider
than the one-line bar (BAR). Writes nothing.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import c3_tr as T  # noqa: E402
from c3font import idx, table  # noqa: E402

LIMIT = 244
BAR = 430
elf = open(T.ELF_PATH, "rb").read()
tab = table(elf, "small")


def w(code):
    e = tab[idx(code)] if 0 <= idx(code) < len(tab) else (0xFF,)
    return e[3] if e[0] != 0xFF else 18


out, bad, n = [], 0, 0
for e in T.load("cn3")["entries"]:
    if e.get("field") != 64 or not e["en"] or not any(x[0] == 26 for x in e["where"]):
        continue
    n += 1
    lines, cur = [], ""
    for wd in e["en"].replace("/n", " ").split(" "):
        trial = f"{cur} {wd}" if cur else wd
        if cur and T._width(trial, w) > LIMIT:
            lines.append(cur)
            cur = wd
        else:
            cur = trial
    lines.append(cur)
    if len(lines) > 2:
        bad += 1
        print("3 lines:", e["id"], lines)
    if T._width(" ".join(lines), w) > BAR:
        bad += 1
        print("too wide for the bar:", e["id"], T._width(" ".join(lines), w), " ".join(lines))
print(len(out) if out else n, "checked,", bad, "to shorten")
