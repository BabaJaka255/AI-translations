"""Dump the Japanese text of PAC/CN3.PAC to script/cn3.json.

CN3.PAC holds 30 per-map data files (same message templates in each, plus map-specific names), the
angel advice lines (#024, 224-byte slots, three voices per event) and customer types (#026, 80-byte records).
Strings sit in fixed-size, zero-padded slots, so text is replaced in place; `cap` is the most bytes a
translation may use (one zero byte is kept as terminator). Identical Japanese is one entry with every
location in `where` ([member, offset, cap]); the smallest cap wins.
Usage: python3 c3_cn3dump.py <CN3.PAC> <out.json>  (keeps existing "en"/"notes")
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from c3pac import pac_read, lzs_decompress  # noqa: E402

RUN = re.compile(rb"(?:[\x81-\x9F\xE0-\xEF][\x40-\x7E\x80-\xFC]|[\x20-\x7E])+")
JP = re.compile(r"[぀-ヿ一-鿿０-ｚ]")


def members(pac):
    for i, raw in enumerate(pac_read(pac)):
        yield i, (lzs_decompress(raw) if raw[:4] == b"LZS\0" else raw)


def strings(d):
    for m in RUN.finditer(d):
        o, s = m.start(), m.group()
        # leading binary that happens to be ASCII (record fields before a name)
        o0 = o
        lead = re.match(rb"(?:(?!/[A-Za-z]|%[sd])[\x20-\x7E])*", s).end()
        o, s = o + lead, s[lead:]
        if len(s) < 4 or (o + len(s) < len(d) and d[o + len(s)] != 0):
            continue
        k = o0 - 1
        while k > o0 - 3 and k > 0 and d[k] not in (0,) and not 0x20 <= d[k] < 0x7F:
            k -= 1  # a stray byte or two (cut multibyte char) right after a terminator
        if k >= 1 and d[k] == 0 and 0x20 <= d[k - 1] <= 0xFC:
            continue  # leftover tail of an older, longer string after a terminator
        try:
            t = s.decode("cp932")
        except UnicodeDecodeError:
            continue
        j = len(JP.findall(t))
        if j < 2 or j * 2 < len(t.replace("/n", "")) - t.count("%s") * 2 - len(re.findall(r"/\w\d*", t)) * 3:
            continue
        end = o + len(s)
        while end < len(d) and d[end] == 0:
            end += 1
        yield o, t, end - o - 1


def main(pac_path, out):
    old = {}
    if os.path.exists(out):
        old = {e["jp"]: e for e in json.load(open(out, encoding="utf-8"))["entries"]}
    by = {}
    for i, d in members(open(pac_path, "rb").read()):
        for o, t, cap in strings(d):
            by.setdefault(t, []).append([i, f"0x{o:05X}", cap])
    entries = []
    for t, where in by.items():
        p = old.get(t, {})
        entries.append({"id": len(entries), "cap": min(w[2] for w in where), "where": where,
                        "jp": t, "en": p.get("en", ""), "notes": p.get("notes", "")})
    json.dump({"block": "cn3", "file": "PAC/CN3.PAC",
               "encoding": "full-width Shift-JIS; same control codes as elf.json; cap = max bytes",
               "entries": entries}, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(len(entries), "unique strings,", sum(len(e["jp"]) for e in entries), "chars,",
          sum(len(e["where"]) for e in entries), "locations")


if __name__ == "__main__":
    main(*sys.argv[1:3])
