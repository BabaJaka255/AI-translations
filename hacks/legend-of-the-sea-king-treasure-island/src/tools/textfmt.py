"""English script format: id|text. Controls: {E} newline, {D} page, {9} wait, {A} insert, {B} number,
{C:n} number width n, {7:n} name n, {8:n} sound n, {4}{5}{6} colour, {>N} tab to line start + N px,
{#hhhh} raw word. Everything else is ASCII text."""
import re, glob, os
TOK = re.compile(r'\{([0-9A-F])(?::(\d+))?\}|\{>(\d+)\}|\{#([0-9a-fA-F]{4})\}')
def tokens(s):
    """-> list of (kind, value): ('t', text) ('c', [words]) ('tab', px)"""
    out = []; i = 0
    for m in TOK.finditer(s):
        if m.start() > i: out.append(('t', s[i:m.start()]))
        if m.group(1):
            w = [0xfff0 | int(m.group(1), 16)]
            if m.group(2) is not None: w.append(int(m.group(2)))
            out.append(('c', w))
        elif m.group(3): out.append(('tab', int(m.group(3))))
        else: out.append(('c', [int(m.group(4), 16)]))
        i = m.end()
    if i < len(s): out.append(('t', s[i:]))
    return out
from font_en import tiny_char
def name_words(s):
    """{N:Koichi} -> letter pairs as name entry stores them (0x2020-0x7E7E, low byte first; odd last letter 0x1Fcc),
    so backspace removes one letter at a time from a default name too."""
    out = ''
    for k in range(0, len(s), 2):
        a = s[k:k + 2]
        out += '{#%04x}' % ((ord(a[1]) << 8 | ord(a[0])) if len(a) == 2 else (0x1f00 | ord(a)))
    return out

def load_en(d='text'):
    en = {}
    for fn in sorted(glob.glob(os.path.join(d, 'en_*.txt'))):
        for ln in open(fn, encoding='utf-8'):
            ln = ln.rstrip('\n')
            if not ln.strip() or ln.startswith('#'): continue
            i, t = ln.split('|', 1)
            t = re.sub('‹([^›]*)›', lambda m: tiny_char(m[1]), t)
            en[int(i)] = re.sub(r'\{N:([^}]*)\}', lambda m: name_words(m[1]), t)
    return en
