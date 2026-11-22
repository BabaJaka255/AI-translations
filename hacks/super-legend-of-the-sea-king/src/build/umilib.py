"""Umi no Nushi Tsuri text helpers. Same encoding as Kawa no Nushi Tsuri 2 (see knt2lib.py there);
only the addresses and the fonts differ."""
import paths as P
import struct
ROMPATH=P.ROM
BANK=0x86                       # script bank; $86:8016 holds the table address
TABLE_OFF=0x31B25; TABLE_N=710  # $86:9B25
TEXT_START=0x320B2; TEXT_END=0x36678   # $86:A0B2 .. one past the last terminator
def p2r(p): return 0x30000+(p&0x7FFF)
def r2p(r): return 0x8000|((r-0x30000)&0x7FFF)
def _tbl(path):
    t={}
    for l in open(path,encoding='utf-8'):
        if l.startswith('#') or '=' not in l: continue
        k,v=l.rstrip('\n').split('=',1); t[int(k,16)]=v
    return t
def load_single(path=P.b('umi_single_byte.tbl')): return _tbl(path)
def load_kanji(path=P.b('umi_kanji.tbl')):
    return {k&0xFFF:v.rstrip('?') for k,v in _tbl(path).items()}
def strend(rom,r):
    i=r
    while rom[i]!=0: i+= 2 if 0xE0<=rom[i]<=0xEF else 1
    return i
def strings(rom):
    ptrs=[struct.unpack_from('<H',rom,TABLE_OFF+2*i)[0] for i in range(TABLE_N)]
    tg=[p2r(p) for p in ptrs]
    return ptrs,tg,{r:strend(rom,r) for r in set(tg)}
def decode(rom,start,end,single,kanji):
    out=[];i=start
    while i<end:
        b=rom[i]
        if b==0xCC: out.append("\n")
        elif 0xCD<=b<0xE0: out.append("{%02X}"%b)
        elif 0xE0<=b<=0xEF:
            g=((b&0xF)<<8)|rom[i+1]; out.append(kanji.get(g,"<K%03X>"%g)); i+=1
        else: out.append(single.get(b,"<%02X>"%b))
        i+=1
    return "".join(out)
def chunks(rom):
    """The text region split at every pointer target: [(start, end_of_chunk)]. Unlike Kawa 2, the table
    also points at small binary records stored between the strings, so a chunk can run past its 00."""
    ptrs,tg,ends=strings(rom); st=sorted(ends)
    return [(a,b) for a,b in zip(st,st[1:]+[TEXT_END])]
def data_ids(rom):
    """Pointer ids whose target is a binary record, not text (67 of them in the original ROM).
    Found as chunks that do not end exactly one byte after their terminator."""
    ptrs,tg,ends=strings(rom); first={}
    for i,r in enumerate(tg): first.setdefault(r,i)
    return sorted(first[a] for a,b in chunks(rom) if b!=ends[a]+1)
WID={'CD':8,'DA':6,'D4':6}      # columns (8 px) reserved for an insert code in English text; others 12
def jp_width(raw):
    """Widest line of an original string in 8 px columns, and its line count. 01-0C draw 8 px wide."""
    w=0; best=0; lines=1; i=0
    while i<len(raw):
        b=raw[i]
        if b==0xCC: best=max(best,w); w=0; lines+=1
        elif 0xE0<=b<=0xEF: w+=2; i+=1
        elif 0xCD<=b<=0xDF: w+=WID.get('%02X'%b,12)
        else: w+= 1 if b<0x0D else 2
        i+=1
    return max(best,w),lines
