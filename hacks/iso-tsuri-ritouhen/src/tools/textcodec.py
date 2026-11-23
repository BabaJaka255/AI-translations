"""Shift-JIS text codec for Iso Tsuri: Ritou-hen.

Decoding shows control bytes as the game's own ASCII codes (] newline, ^ cursor stop, ~ skip, < katakana,
> hiragana, / end) and anything else unusual as {XX}. Encoding English: plain ASCII, with
  {nbsp}  -> 0xA0, a blank that label-width code does not treat as a word break
  {XX}    -> raw byte
"""
import re

def decode(b, i=0, end=None, stop=True):
    out = []
    end = len(b) if end is None else end
    while i < end:
        c = b[i]
        if c == 0x2f and stop:
            i += 1
            break
        if c == 0xff:
            out.append('{FF%02X}' % b[i + 1]); i += 2; continue
        if 0x81 <= c <= 0x9f or 0xe0 <= c <= 0xef:
            try: out.append(b[i:i + 2].decode('shift_jis'))
            except UnicodeDecodeError: out.append('{%02X%02X}' % (c, b[i + 1]))
            i += 2; continue
        if 0xa1 <= c <= 0xdf:
            out.append(bytes([c]).decode('shift_jis')); i += 1; continue
        if 0x20 <= c < 0x7f:
            out.append(chr(c)); i += 1; continue
        out.append('{%02X}' % c); i += 1
    return ''.join(out), i

RESERVED = set('/]^~<>')

def encode(s, allow=''):
    """English text -> bytes. Reserved engine characters are only allowed when listed in allow."""
    out = bytearray()
    for tok in re.split(r'(\{[^}]*\})', s):
        if not tok: continue
        if tok.startswith('{'):
            t = tok[1:-1]
            out += b'\xa0' if t == 'nbsp' else bytes.fromhex(t)
            continue
        for ch in tok:
            if ch in RESERVED and ch not in allow:
                raise ValueError('reserved character %r in %r' % (ch, s))
            if not (0x20 <= ord(ch) < 0x7f):
                raise ValueError('non-ASCII %r in %r' % (ch, s))
            out.append(ord(ch))
    return bytes(out)

def columns(b):
    """On-screen width in 8 px columns of encoded English bytes (control bytes take none)."""
    return sum(1 for c in b if c not in (0x2f, 0x5d, 0x5e, 0x7e, 0x3c, 0x3e))
