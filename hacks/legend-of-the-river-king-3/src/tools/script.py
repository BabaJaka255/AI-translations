"""Parse Kawa5 [SCRIPT] bytecode: [op][len][u16 arg][...]; op 0x16 is followed by u32 textlen + text."""
import struct, glob

TEXT_OPS = (0x16, 0x1b)

def parse(d):
    assert d[:8] == b'[SCRIPT]'
    size = struct.unpack_from('<I', d, 8)[0]
    p = 12; ins = []
    while p < len(d):
        op, ln = d[p], d[p+1]
        if ln == 0: raise ValueError('zero len at %x' % p)
        raw = d[p:p+ln]
        text = None
        if op in TEXT_OPS:
            tl = struct.unpack_from('<I', d, p+4)[0]
            text = d[p+8:p+8+tl]
            ln = 8 + tl
        ins.append((p, op, d[p:p+ln], text))
        p += ln
    return size, ins
