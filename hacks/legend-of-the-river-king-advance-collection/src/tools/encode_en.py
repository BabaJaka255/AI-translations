# English character codes (shared by both games); space differs per game.
import font_en
CODES={}
for i in range(10): CODES[str(i)]=i
for i in range(26): CODES[chr(65+i)]=0x0a+i; CODES[chr(97+i)]=0x24+i
CODES.update({'.':0x8f, ',':0x90, '?':0x91, '!':0x92, '"':0x93, '-':0x96, '~':0x97, '/':0x9d,
              '(':0xa8, ')':0xaa, "'":0x3e, ':':0x3f, ';':0x40, '&':0x41, '+':0x42, '%':0x43, '*':0x44,
              '=':0x45, '_':0x46, '<':0x47, '>':0x48, '[':0xa0, ']':0xb6})
CODES.update({'Ⓛ': 0x80, 'Ⓖ': 0x81})   # Ⓛ = 'Lv', Ⓖ = 'Go' in one 8 px tile
PAD=0xee  # '|' : advance to next tile boundary (VWF special)
SPACE={'g4':0xb9,'g3':0xb7}
CTRL_NAMES={}
import re
def encode(s, game):
    """Text with {xx} hex control bytes, {n} for newline etc."""
    out=bytearray(); i=0
    while i<len(s):
        c=s[i]
        if c=='{':
            j=s.index('}',i); tok=s[i+1:j]; i=j+1
            for h in tok.split():
                out.append(int(h,16))
            continue
        if c==' ': out.append(SPACE[game])
        elif c=='…': out.append(0x95)
        elif c=='|': out.append(PAD)
        else: out.append(CODES[c])
        i+=1
    return bytes(out)
def width(code, game):
    return WIDTHS[game][code]
def build_widths(game):
    w=[8]*256
    for ch,c in CODES.items():
        w[c]=font_en.width(ch)
    w[SPACE[game]]=3
    w[0x95]=7
    w[PAD]=0
    w[0x80]=w[0x81]=8
    return bytes(w)
WIDTHS={g:build_widths(g) for g in SPACE}
def font_tiles():
    """dict code->32-byte tile"""
    t={c:font_en.tile(ch) for ch,c in CODES.items()}
    # ellipsis
    G=font_en.G
    font_en.g('…', ' ', ' ', ' ', ' ', ' ', '# # #')
    t[0x95]=font_en.tile('…')
    return t
