"""Dump the Japanese strings of the ELF to script/elf.json (rhtk script format).

Each entry: offset (ELF file offset), length (bytes the string may use: its own bytes plus the zero
padding after it), pointers (file offsets of stored 32-bit pointers to it), kind:
  "ptr"   at least one stored pointer: can be repointed into free space later
  "code"  no stored pointer (built by lui/addiu, or a fixed field in a record): must fit `length`
Usage: python3 c3_dump.py <SLPM_623.22> <out.json>  (keeps existing "en"/"notes" when the file exists)
"""
import collections
import json
import os
import re
import struct
import sys

ELF_VADDR, ELF_FOFF = 0x205700, 0xF6700
STR = re.compile(rb"(?<=[\x00-\x0F])(?:[\x81-\x9F\xE0-\xEF][\x40-\x7E\x80-\xFC]|[\x20-\x7E\x0A])+\x00")
KANA = re.compile(rb"\x82[\x9F-\xF1]|\x83[\x40-\x96]|\x81[\x40-\x9F]")
# Not text to translate: (start, end, reason). Kept in the dump so offsets stay visible, marked "skip".
SKIP = [(0x149900, 0x149A00, "code bytes"), (0x171560, 0x171570, "code bytes"),
        (0x249540, 0x249600, "line-break (kinsoku) character tables"),
        (0x414202, 0x414203, "fragment"), (0x4152E9, 0x4152EA, "fragment"),
        (0x422200, 0x4235A0, "name-entry keyboard rows (input characters, not text)")]
CTRL_ONLY = re.compile(rb"/(?:[A-Za-z][0-9]*|[0-9])|%0?[0-9]*[sd]| ")
NOISE = [(0x23C000, 0x240000, "code/data bytes that decode as kanji")]
KEEP = ("field", "nopairs", "repoint")  # hand-set keys carried over from the previous dump
MB = re.compile(rb"[\x81-\x9F\xE0-\xEF][\x40-\x7E\x80-\xFC]")


def main(elf_path, out):
    d = open(elf_path, "rb").read()
    words = collections.defaultdict(list)
    for o in range(ELF_FOFF, len(d) - 3, 4):
        words[struct.unpack_from("<I", d, o)[0]].append(o)
    old = {}
    if os.path.exists(out):
        for e in json.load(open(out, encoding="utf-8"))["entries"]:
            old[e["offset"]] = e
    entries = []
    for m in STR.finditer(d, ELF_FOFF):
        s = m.group()[:-1]
        mb = MB.findall(s)
        if len(mb) < 1:
            continue
        if len(KANA.findall(s)) * 3 < len(mb):
            # kanji-only labels (初期資金, 道路): accept only clean, 4-aligned data strings made of
            # SJIS characters and control codes
            off0 = m.start()
            if off0 % 4 or off0 < 0x176000 or CTRL_ONLY.sub(b"", MB.sub(b"", s)):
                continue
        if any(a <= m.start() < b for a, b, _ in NOISE):
            continue
        try:
            jp = s.decode("cp932")
        except UnicodeDecodeError:
            continue
        off = m.start()
        end = m.end()
        while end < len(d) and d[end] == 0:
            end += 1
        ptrs = words.get(off - ELF_FOFF + ELF_VADDR, [])
        o = f"0x{off:06X}"
        prev = old.get(o, {})
        skip = next((r for a, b, r in SKIP if a <= off < b), "") or prev.get("skip", "")
        entries.append({"id": prev.get("id"), "offset": o, "length": end - off - 1, **({"skip": skip} if skip else {}),
                        "kind": "ptr" if ptrs else "code",
                        "pointers": [f"0x{p:06X}" for p in ptrs],
                        "jp": jp, "en": prev.get("en", ""), "notes": prev.get("notes", ""),
                        **{k: v for k, v in prev.items() if k in KEEP}})
    nxt = max([e["id"] for e in entries if e["id"] is not None] + [-1]) + 1
    for e in entries:  # strings new to this dump get ids after the old ones, so TSV ids stay valid
        if e["id"] is None:
            e["id"], nxt = nxt, nxt + 1
    entries.sort(key=lambda e: e["id"])
    json.dump({"block": "elf", "file": "SLPM_623.22", "encoding": "full-width Shift-JIS; /n = newline, /Innn = inline icon",
               "entries": entries}, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    k = collections.Counter(e["kind"] for e in entries)
    print(sum(1 for e in entries if "skip" in e), "marked skip;", end=" ")
    print(len(entries), "strings", dict(k), sum(len(e["jp"]) for e in entries), "chars")


if __name__ == "__main__":
    main(*sys.argv[1:3])
