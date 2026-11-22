"""Swap the embedded level-data stream of a 7 Blades movie (PSS).

66 of the 94 movies carry the next stage's files inside private stream 1
(PES 0xBD, payload header ff 90 00 00, then an NCB-style archive). The PAL code
must get the PAL archive, so this keeps the Japanese video/audio packs and
refills every data PES, in order, with the PAL data stream. When the PAL data is
bigger, all-data packs are duplicated (evenly spread) to add room.

usage: b7_remux.py jp.pss pal.data out.pss      (pal.data = concatenated PAL payloads)
"""
import sys

PACK = 16384


def split_packs(s):
    return [s[i:i + PACK] for i in range(0, len(s), PACK)]


def data_pes(pack):
    """(payload_offset, payload_len) of each data PES in one pack; also whether the pack is data-only."""
    out = []; only = True
    if pack[:4] != b'\0\0\1\xba':
        return out, False
    i = 14 + (pack[13] & 7)
    while i < len(pack) - 6 and pack[i:i + 3] == b'\0\0\1':
        sid = pack[i + 3]
        if sid == 0xb9:
            only = False; break
        ln = int.from_bytes(pack[i + 4:i + 6], 'big')
        if sid == 0xbd:
            hl = pack[i + 8]; o = i + 9 + hl; L = ln - 3 - hl
            if pack[o + 1] == 0x90:
                out.append((o + 4, L - 4))
            else:
                only = False
        else:
            only = False
        i += 6 + ln
    return out, only and bool(out)


def extract(s):
    d = bytearray()
    for p in split_packs(s):
        for o, L in data_pes(p)[0]:
            d += p[o:o + L]
    return bytes(d)


def remux(jp, pal):
    packs = split_packs(jp)
    info = [data_pes(p) for p in packs]
    cap = sum(L for pes, _ in info for _, L in pes)
    if len(pal) > cap:
        only = [k for k, (pes, o) in enumerate(info) if o]
        per = sum(L for _, L in info[only[0]][0])
        need = -(-(len(pal) - cap) // per)
        if need > len(only):
            raise ValueError('not enough data packs to duplicate')
        dup = {only[int((j + 0.5) * len(only) / need)] for j in range(need)}
        newp = []
        for k, p in enumerate(packs):
            newp.append(p)
            if k in dup:
                newp.append(p)
        packs = newp
        info = [data_pes(p) for p in packs]
    out = bytearray(); pos = 0
    for p, (pes, _) in zip(packs, info):
        p = bytearray(p)
        for o, L in pes:
            chunk = pal[pos:pos + L]; pos += len(chunk)
            p[o:o + L] = chunk + bytes(L - len(chunk))
        out += p
    assert pos == len(pal)
    return bytes(out)


if __name__ == '__main__':
    jp = open(sys.argv[1], 'rb').read(); pal = open(sys.argv[2], 'rb').read()
    out = remux(jp, pal)
    assert extract(out)[:len(pal)] == pal
    open(sys.argv[3], 'wb').write(out)
    print(f'{sys.argv[1]}: {len(jp)} -> {len(out)} bytes ({(len(out) - len(jp)) // PACK:+d} packs)')
