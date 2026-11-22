"""Merge translations into the script files and check them.

  python3 c3_tr.py add elf|cn3 <file.tsv>   lines "id<TAB>english" (literal \\t not allowed in text);
                                           "id!" = no letter pairs (strings drawn with the name font);
                                           an empty english clears the entry
  python3 c3_tr.py addjp elf|cn3 <file.tsv>  lines "japanese<TAB>english": every entry with that Japanese
  python3 c3_tr.py check [elf|cn3]          width and size warnings for every translated entry

Width check: each English line (split on /n, /r, /N) is measured with the small font's glyph widths
(+2 px gap, 6 px space) and compared with the widest Japanese line of the same string. Size check:
encoded bytes (letter pairs ranked from all current English) against the slot.
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
GAME = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import c3_glyphs as G  # noqa: E402
from c3font import idx, table  # noqa: E402

FILES = {"elf": "elf.json", "cn3": "cn3.json"}
FIELDS = (16, 32, 64, 128, 224, 256, 259)
ELF_PATH = os.environ.get("C3_ELF", os.path.join(GAME, "build", "disc", "SLPM_623.22"))


def load(block):
    return json.load(open(os.path.join(GAME, "script", FILES[block]), encoding="utf-8"))


def save(block, data):
    p = os.path.join(GAME, "script", FILES[block])
    json.dump(data, open(p + ".tmp", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    os.replace(p + ".tmp", p)


def add(block, tsv):
    data = load(block)
    by = {e["id"]: e for e in data["entries"]}
    n = 0
    for line in open(tsv, encoding="utf-8"):
        line = line.rstrip("\n")
        if not line.strip() or line.startswith("#"):
            continue
        i, _, en = line.partition("\t")
        if i.endswith("!"):  # "123!" = plain glyphs only (name-entry font, memory card title)
            i = i[:-1]
            by[int(i)]["nopairs"] = True
        by[int(i)]["en"] = en
        n += 1
    save(block, data)
    print(f"{block}: {n} lines merged")


def addjp(block, tsv):
    """Lines "japanese<TAB>english": fill every entry whose Japanese matches exactly ("jp!" = no pairs)."""
    data = load(block)
    by = {}
    for e in data["entries"]:
        by.setdefault(e["jp"], []).append(e)
    n = miss = 0
    for line in open(tsv, encoding="utf-8"):
        line = line.rstrip("\n")
        if not line.strip() or line.startswith("#"):
            continue
        jp, _, en = line.partition("\t")
        nop = jp.endswith("!")
        jp = jp[:-1] if nop else jp
        if jp not in by:
            print("no entry:", jp)
            miss += 1
            continue
        for e in by[jp]:
            if e.get("skip"):
                continue
            e["en"] = en
            if nop:
                e["nopairs"] = True
            n += 1
    save(block, data)
    print(f"{block}: {n} entries filled, {miss} lines without a match")


SYNTH = {"-": 7, "'": 4, '"': 9}  # glyphs made by c3_glyphs._synth_quotes
SPLIT = re.compile(r"/[nrN]|/k[A-Z]|/p")


def _width(text, w):
    text = G.CTRL.sub("", text)
    px = 0
    for ch in text:
        if ch == " ":
            px += 6
        elif ch in SYNTH:
            px += SYNTH[ch] + 2
        else:
            c = G.sjis(ch)
            px += (w(c) if c else 20) + 2
    return px


def check(blocks=("elf", "cn3")):
    elf = open(ELF_PATH, "rb").read()
    tabs = {f: table(elf, f) for f in ("small", "talk")}
    # Latin glyphs the talk font lacks are borrowed from the 26 px name font: use its widths
    name_tab = table(elf, "name")

    def wf(f, code):
        t = tabs[f]
        e = t[idx(code)] if 0 <= idx(code) < len(t) else (0xFF,)
        if e[0] == 0xFF and 0 <= idx(code) < len(name_tab) and name_tab[idx(code)][0] != 0xFF:
            e = name_tab[idx(code)]
        return e[3] if e[0] != 0xFF else 18

    def wjpf(f, ch):
        try:
            return wf(f, int.from_bytes(ch.encode("cp932"), "big"))
        except UnicodeEncodeError:
            return 18

    allen = []
    datas = {b: load(b) for b in blocks}
    for b in blocks:
        allen += [e["en"] for e in datas[b]["entries"] if e.get("en")]
    corpus = "\n".join(allen)
    # pair set estimate: the top pairs (the real set is decided at build time)
    pairs = {p: 0x88A0 + k for k, p in enumerate(G.pair_ranking(corpus + "\n" + corpus)[:480])}
    pairs[" "] = 0x889F  # blank glyph: speech-box text writes unpaired spaces with it (2 bytes)
    warn = 0
    for b in blocks:
        for e in datas[b]["entries"]:
            en = e.get("en")
            if not en:
                continue
            if e.get("lead"):  # career line: {y} = year digits, 4 more bytes of room
                en = en.replace("{y}", "10")
            jp_lines = SPLIT.split(e["jp"])
            en_lines = SPLIT.split(en)
            for f in (("small", "talk") if len(jp_lines) > 1 else ("small",)):
                jmax = max(sum(wjpf(f, c) + 2 for c in G.CTRL.sub("", l)) for l in jp_lines)
                bad = False
                for l in en_lines:
                    ew = _width(l, lambda c: wf(f, c))
                    multi = len(jp_lines) > 1
                    limit = jmax * 1.08 if multi else jmax * 1.6 + 30
                    if ew > limit:
                        print(f"{b} #{e['id']} WIDE({f}) {ew}px > {jmax}px: {l}")
                        warn += 1
                        bad = True
                if bad:
                    break
            try:
                n = len(G.encode(en, {} if e.get("nopairs") else pairs))
            except ValueError as x:
                print(f"{b} #{e['id']} GLYPH {x}")
                warn += 1
                continue
            cap = e.get("length", e.get("cap"))
            jb = len(e["jp"].encode("cp932"))
            std = next((f for f in FIELDS if f >= jb + 1), None)
            if ((b == "cn3" and len(e["where"]) < 3 and not e.get("lead") and not e.get("field")) or e.get("kind") == "code") and std:
                cap = min(cap, std - 1)
            if e.get("field"):
                cap = min(e.get("length", e.get("cap")), e["field"] - 1)
            cap = (min(cap, 258) if b == "cn3" else cap) + e.get("lead", 0)
            if n > cap and not e.get("repoint"):
                print(f"{b} #{e['id']} LONG {n}/{cap} bytes: {en}")
                warn += 1
            if re.search(r"/[nrNp][0-9]", en):  # the game reads digits after a break as its parameter
                print(f"{b} #{e['id']} DIGIT after a line break: {en[:60]}")
                warn += 1
            stray = [c for c in set(re.findall(r"/(?:[A-MO-QS-Za-mo-qs-z][0-9]*)", en))
                     if en.count(c) > e["jp"].count(c) and not re.fullmatch(r"/[QG][0-9]", c)]  # /Qn: c3_pad, /Gn: c3_gcode
            if stray:  # a "/" before a letter is a control code to the game ("w/chair" = colour code)
                print(f"{b} #{e['id']} SLASH {stray}: {en[:60]}")
                warn += 1
            for code in ("%s", "%d") + tuple(f"/{k}" for k in range(10)):
                if e["jp"].count(code) != en.count(code) + en.count("/Q" + code[1:]) + en.count("/G" + code[1:]):
                    print(f"{b} #{e['id']} ARGS {code} count differs")
                    warn += 1
    done = {b: sum(1 for e in datas[b]["entries"] if e.get("en")) for b in blocks}
    total = {b: sum(1 for e in datas[b]["entries"] if not e.get("skip")) for b in blocks}
    print("translated:", {b: f"{done[b]}/{total[b]}" for b in blocks}, "warnings:", warn)


if __name__ == "__main__":
    if sys.argv[1] == "add":
        add(sys.argv[2], sys.argv[3])
    elif sys.argv[1] == "addjp":
        addjp(sys.argv[2], sys.argv[3])
    else:
        check(tuple(sys.argv[2:]) or ("elf", "cn3"))
