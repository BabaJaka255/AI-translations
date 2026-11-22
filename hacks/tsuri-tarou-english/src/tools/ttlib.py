"""Shared helpers for Tsuri Tarou: table loading and 8x8 text decode."""
import os
HERE=os.path.dirname(os.path.abspath(__file__))
def load_tbl(path=os.path.join(HERE,'..','data','tt_8x8.tbl')):
    t={}
    for l in open(path,encoding='utf-8'):
        l=l.rstrip('\n')
        if not l or l.startswith('#'): continue
        k,_,v=l.partition('='); t[int(k,16)]=v
    return t
T=load_tbl()
def decode(bs):
    """Decode 8x8-font text. 1A/2A are dakuten/handakuten marks placed before a kana."""
    out=[]; i=0
    while i<len(bs):
        b=bs[i]
        if b in (0x1A,0x2A) and i+1<len(bs):
            k=T.get(bs[i+1],'?'); out.append(k+('゛' if b==0x1A else '゜')); i+=2; continue
        out.append(T.get(b,'{%02X}'%b)); i+=1
    s=''.join(out)
    import unicodedata
    return unicodedata.normalize('NFC',s.replace('゛','゙').replace('゜','゚'))

def load_story():
    t=dict(T); t.update(load_tbl(os.path.join(HERE,'..','data','tt_story.tbl'))); return t
TS=load_story()
def mark(base,m):
    """Combine a kana with a dakuten/handakuten mark drawn on the row above."""
    import unicodedata
    return unicodedata.normalize('NFC',base+('\u3099' if m=='゛' else '\u309a'))
