"""Shared helpers: text decoding for Kawa no Nushi Tsuri Shizen-ha (little-endian SJIS words, 0000 end)."""
CTRL = {0xF0: 'NUM', 0xD0: 'NAME', 0xC0: 'V0', 0xC1: 'V1', 0xC2: 'V2', 0xC3: 'V3', 0xC5: 'V5', 0xC6: 'V6',
        0xA0: 'A0', 0xB0: 'B0', 0xB1: 'B1', 0xB2: 'B2', 0xB3: 'B3'}
def sjis_ok(hi, lo):
    return (0x81 <= hi <= 0x9F or 0xE0 <= hi <= 0xEA) and 0x40 <= lo <= 0xFC and lo != 0x7F
def parse(d, o, maxlen=0x400):
    """Decode a string at d[o]. Returns (text, length incl. terminator) or None if it isn't a clean string."""
    out = []; p = o
    while p + 1 < len(d) and p - o < maxlen:
        lo, hi = d[p], d[p + 1]; p += 2
        if hi == 0:
            if lo != 0: return None
            return ''.join(out), p - o
        if hi in CTRL: out.append('[%s:%02X]' % (CTRL[hi], lo)); continue
        if not sjis_ok(hi, lo): return None
        try: out.append(bytes([hi, lo]).decode('cp932'))
        except UnicodeDecodeError: return None
    return None
