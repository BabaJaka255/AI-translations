"""Dump every text line of Kawa no Nushi Tsuri (FC) into script/lines.json.

A line is a run of tiles ending in FF.  The game reaches each line through
LDX #hi / LDY #lo stubs that jump to one print routine per bank (or fall into
it), plus two sequential readers (intro, ending) that walk FF-terminated
lines from one LDA #hi/STA $13/LDA #lo/STA $12 start.
Run from the game folder: python3 tools/knt_extract.py
"""
import json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from knt_common import JP, decode_jp, prg

COMMONS = {0xBE07: 8, 0xB134: 9, 0xAA57: 10, 0xB242: 10, 0xB0DB: 12, 0xA573: 13, 0xB718: 13}
SEQ = [  # (prg offset of LDA #hi, number of lines, name)
    (0x117C6 - 0x10 + 0x10, 16, "ending"),
]


def main():
    P = prg(open("rom/original.nes", "rb").read())
    lines = {}

    def add(off, ref):
        lines.setdefault(off, {"refs": []})["refs"].append(ref)

    for addr, bank in COMMONS.items():
        base = bank * 0x2000
        seg = P[base:base + 0x2000]
        # fall-through stub right before the common block
        c = base + (addr - 0xA000)
        assert P[c - 4] == 0xA2 and P[c - 2] == 0xA0
        add(base + ((P[c - 3] << 8 | P[c - 1]) - 0xA000), {"type": "stub", "at": c - 4})
        for m in re.finditer(re.escape(bytes([0x4C, addr & 0xFF, addr >> 8])), seg):
            j = base + m.start()
            assert P[j - 4] == 0xA2 and P[j - 2] == 0xA0, hex(j)
            add(base + ((P[j - 3] << 8 | P[j - 1]) - 0xA000), {"type": "stub", "at": j - 4})
    # sequential readers: LDA #hi STA $13 LDA #lo STA $12 JSR $C037
    seqs = []
    for m in re.finditer(rb"\xa9\x10\x8d\x5c\x07|\xa9\x11\x8d\x5c\x07", P):
        j = m.start(); count = P[j + 1]
        k = j + 5
        assert P[k] == 0xA9 and P[k + 2] == 0x85 and P[k + 3] == 0x13
        hi, lo = P[k + 1], P[k + 5]
        bank = j // 0x2000
        start = bank * 0x2000 + ((hi << 8 | lo) - 0xA000)
        offs = [start]
        for _ in range(count - 1):
            offs.append(P.index(0xFF, offs[-1]) + 1)
        seqs.append({"at": k, "count": count, "lines": offs})
    out = []
    for off in sorted(lines):
        out.append({"id": f"{off:05X}", "bank": off // 0x2000, "refs": lines[off]["refs"],
                    "jp": decode_jp(P, off), "en": "", "notes": ""})
    for s in seqs:
        for n, off in enumerate(s["lines"]):
            out.append({"id": f"{off:05X}", "bank": off // 0x2000,
                        "refs": [{"type": "seq", "at": s["at"], "index": n, "count": s["count"]}],
                        "jp": decode_jp(P, off), "en": "", "notes": ""})
    out.sort(key=lambda e: int(e["id"], 16))
    os.makedirs("script", exist_ok=True)
    json.dump(out, open("script/lines.json", "w"), ensure_ascii=False, indent=1)
    print(len(out), "lines")


if __name__ == "__main__":
    main()
