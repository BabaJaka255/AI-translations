"""English text -> game bytes.  Text cells hold 2 ASCII letters; control codes take one cell."""
import re
W = 24
CODES = {'A0': 0xA0, 'B0': 0xB0, 'B1': 0xB1, 'B2': 0xB2, 'B3': 0xB3, 'V0': 0xC0, 'V1': 0xC1, 'V2': 0xC2,
         'V3': 0xC3, 'V5': 0xC5, 'V6': 0xC6, 'NUM': 0xF0, 'NAME': 0xD0}
CODE_W = {'A0': 4, 'B0': 2, 'B1': 10, 'B2': 4, 'B3': 4, 'V0': 4, 'V1': 4, 'V2': 4, 'V3': 8, 'V5': 4, 'NUM': 6}
TOK = re.compile(r'(\{\w+\})')
def wrap(text, width=W):
    """Word-wrap to lines of `width` columns. Control codes count as their estimated printed width."""
    lines = []
    for para in text.split('\n'):
        cur = ''; curw = 0
        for word in para.split(' '):
            ww = sum(CODE_W.get(t[1:-1], 2) if TOK.fullmatch(t) else len(t) for t in TOK.split(word) if t)
            if cur and curw + 1 + ww > width:
                lines.append((cur, curw)); cur, curw = word, ww
            else:
                cur = cur + ' ' + word if cur else word; curw += (1 if curw else 0) + ww
        lines.append((cur, curw))
    return lines
def encode(text, reflow=True, width=W):
    """Returns bytes ending in 0000. With reflow, lines are padded to `width` columns except the last."""
    if reflow:
        ls = wrap(text, width)
        s = ''.join(l + ' ' * (width - w) if i < len(ls) - 1 else l for i, (l, w) in enumerate(ls))
    else:
        s = text
    out = bytearray()
    for part in TOK.split(s):
        if not part: continue
        m = TOK.fullmatch(part)
        if m:
            if len(out) % 2: out += b' '
            c = CODES[part[1:-1]]; out += bytes([c, c])
        else:
            out += part.encode('ascii')
    if len(out) % 2: out += b' '
    return bytes(out) + b'\0\0'
