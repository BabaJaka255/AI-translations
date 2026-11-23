"""PsyQ MND .SYM parser -> list of (addr, kind, name) and function info."""
import struct, sys
def parse(path):
    d = open(path, 'rb').read(); assert d[:3] == b'MND'
    i = 8; out = []; fn = None
    def pstr(j):
        n = d[j]; return d[j+1:j+1+n].decode('latin1'), j+1+n
    while i < len(d):
        val, tag = struct.unpack_from('<IB', d, i); i += 5
        if tag < 0x80:
            name, i = pstr(i); out.append((val, 'sym%d' % tag, name))
        elif tag == 0x80: pass
        elif tag == 0x82: i += 1
        elif tag == 0x84: i += 2
        elif tag == 0x86: i += 4
        elif tag == 0x88: i += 4; name, i = pstr(i)
        elif tag == 0x8a: pass
        elif tag == 0x8c:
            i += 2 + 4 + 2 + 4 + 4 + 4; f, i = pstr(i); name, i = pstr(i); out.append((val, 'func', name)); fn = name
        elif tag == 0x8e: i += 4
        elif tag == 0x90: i += 4
        elif tag == 0x92: i += 4
        elif tag == 0x94:
            cls, typ, size = struct.unpack_from('<HHI', d, i); i += 8; name, i = pstr(i)
            out.append((val, 'def%d' % cls, name, typ, size, fn))
        elif tag == 0x96:
            cls, typ, size, nd = struct.unpack_from('<HHIH', d, i); i += 10 + 4 * nd
            tg, i = pstr(i); name, i = pstr(i); out.append((val, 'def%d' % cls, name, typ, size, fn, tg))
        elif tag == 0x98: i += 8
        elif tag == 0x9a: pass
        else: raise ValueError('tag %x at %x' % (tag, i - 5))
    return out
if __name__ == '__main__':
    for r in parse(sys.argv[1]):
        print('%08x %s %s' % (r[0], r[1], ' '.join(str(x) for x in r[2:])))
