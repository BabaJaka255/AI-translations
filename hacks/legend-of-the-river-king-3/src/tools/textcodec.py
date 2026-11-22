"""Text <-> bytes for Kawa5 script strings. Control bytes < 0x20 are written [XX] (0x01 is a newline)."""
import re

def decode(b):
    b = b.rstrip(b'\0'); out = []; i = 0
    while i < len(b):
        c = b[i]
        if c == 0x01: out.append('\n'); i += 1
        elif c < 0x20: out.append('[%02X]' % c); i += 1
        elif 0x81 <= c <= 0x9f or 0xe0 <= c <= 0xfc:
            out.append(b[i:i+2].decode('cp932', 'backslashreplace')); i += 2
        else:
            out.append(bytes([c]).decode('cp932', 'backslashreplace')); i += 1
    return ''.join(out)

def encode(s, charmap=None):
    out = bytearray(); i = 0
    while i < len(s):
        m = re.match(r'\[([0-9A-Fa-f]{2})\]', s[i:])
        if m: out.append(int(m.group(1), 16)); i += 4; continue
        ch = s[i]; i += 1
        if ch == '\n': out.append(1); continue
        if charmap and ch in charmap: out += charmap[ch]; continue
        out += ch.encode('cp932')
    return bytes(out)
