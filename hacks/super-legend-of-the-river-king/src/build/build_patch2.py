import paths as P
import sys,re,json,struct
sys.path.insert(0,P.BUILD)
from asm import assemble
from PIL import ImageFont
P.check_rom(); ROMP=P.ROM
rom=bytearray(open(ROMP,'rb').read()); orig=bytes(rom)
rom+=b'\xFF'*(0x200000-len(rom))
import translations, tr_batch2
import tr_batch3
EN=dict(translations.EN); EN.update(tr_batch2.EN2); EN.update(tr_batch3.EN3)
try:
    import user_edits      # edits imported from the script workbook (script_io.py)
except ImportError:
    user_edits=None
if user_edits: EN.update(user_edits.EN_USER)
script={x['id']:x for x in json.load(open(P.b('script.json')))}
MAXCOL=23
WID={'CD':8,'DA':6,'D4':6}
def w(off,data): rom[off:off+len(data)]=data
# --- font (bank $30 @ $9000), 95 glyphs ASCII 0x20.. ---
from PIL import PcfFontFile, Image
pcf=PcfFontFile.PcfFontFile(open(P.font('koi8x16.pcf'),'rb'))
FONT=0x180000+0x2000
for g in range(95):
    im=pcf.glyph[0x20+g][3].convert('1'); assert im.size==(8,16)
    px=im.load(); base=FONT+(g>>3)*0x100+(g&7)*0x10
    for y in range(16):
        b=0
        for x in range(8):
            if px[x,y]: b|=0x80>>x
        # rows 0-7 -> +0..7 (TL), rows 8-15 -> +0x80..0x87 (BL); right halves zero
        rom[base+(y if y<8 else 0x80+y-8)]=b
        # right halves already 0 (+8..15, +0x88..0x8F) but ensure
    for y in range(8): rom[base+8+y]=0; rom[base+0x88+y]=0
# --- strings ---
ERR=[]
WIDE={289,297,53}
POSTCARD={527,528,531,534}   # copied into the postcard buffer: 5 lines x 28 columns, max 159 bytes
NODF={6,7,8,9}   # drawn by the wide (32-column) layout routine
def enc(s,MAXCOL=MAXCOL):
    out=bytearray([0xDF]); 
    for line in s.split('\n'):
        cols=0; i=0
        while i<len(line):
            m=re.match(r'\{([0-9A-Fa-f]{2})\}',line[i:])
            if m: out.append(int(m.group(1),16)); cols+=WID.get(m.group(1).upper(),12); i+=m.end(); continue
            c=ord(line[i]); assert 0x20<=c<0x7F,(line,line[i]); out.append(c); cols+=1; i+=1
        if cols>MAXCOL: ERR.append((cols,line))
        out.append(0xCC)
    out[-1]=0  # last line break -> terminator
    return bytes(out)

import pickle
from knt2lib import load_single,load_kanji,decode
from zones_en import Z
if user_edits: Z.update(user_edits.Z_USER)
single=load_single(); kanji=load_kanji()
zones=pickle.load(open(P.data('zones.pkl'),'rb'))
entries={}   # old ptr -> bytes
for sid,txt in sorted(EN.items()):
    assert script[sid]['snes'].startswith('05:')
    e_=enc(txt,48 if sid==53 else (32 if sid in WIDE else (28 if sid in POSTCARD else MAXCOL)))
    if sid in POSTCARD: assert txt.count('\n')<=4 and len(e_)<=0xA0,(sid,'postcard text: max 5 lines / 159 bytes')
    if sid in NODF: e_=e_[1:]   # copied into the name buffer; names are always drawn in English mode
    entries[int(script[sid]['snes'].split(':')[-1],16)]=e_
zones['bait']=list(zones['bait'])+[(0x29FE7,0x29FEA)]
zones['lure']=list(zones['lure'])+[(0x2A5EC+8*k,0x2A5EC+8*k+7) for k in range(13)]
nz=0
for zn,L in zones.items():
    for s,e in L:
        jp=decode(orig,s,e,single,kanji)
        if jp in Z:
            entries[0x8000+(s-0x28000)]=enc(Z[jp]); nz+=1
from fish_desc_en import D as FD
if user_edits: FD=dict(FD); FD.update(user_edits.FD_USER)
def wrap(t):
    words=t.split(); lines=[]; cur=''; wd_=22
    for wd in words:
        if len(cur)+len(wd)+(1 if cur else 0)<=wd_: cur=(cur+' '+wd) if cur else wd
        else: lines.append(cur); cur=wd; wd_=27
    lines.append(cur); assert len(lines)<=4,t
    return '\n'.join(lines)
for k,t in FD.items():
    o=0x28018+k*23
    dp=struct.unpack('<H',orig[o+0x13:o+0x15])[0]
    entries[dp]=enc(wrap(t),27)
if ERR:
    for e_ in ERR: print('TOO LONG',e_)
    raise SystemExit(1)
# lay out strings in banks $31,$32
bank=0x31; pos=0; table=[]
def baseoff(b): return (b-0x30)*0x8000+0x180000
for old in sorted(entries):
    e=entries[old]
    if pos+len(e)>0x8000: bank+=1; pos=0
    w(baseoff(bank)+pos,e); table.append((old,0x8000+pos,bank)); pos+=len(e)
print('banks used up to',hex(bank),'pos',hex(pos),'zone strings',nz)
# index + table in bank $30: index @8000 (256B), entries @8200 (6 bytes each, sorted, FFFF terminated)
table.sort()
idx=[0]*128
for h in range(128):
    k=0
    while k<len(table) and (table[k][0]>>8)<h+0x80: k+=1
    idx[h]=k*6
w(0x180000,b''.join(struct.pack('<H',x) for x in idx))
tb=b''.join(struct.pack('<HHH',o,n,b) for o,n,b in table)+struct.pack('<HHH',0xFFFF,0,0)
assert len(tb)<=0x2000-0x200
w(0x180200,tb)
# --- code ---
def lo(a,bank=2): return 0x8000*bank+(a&0x7FFF)
XL="""
xl: LDA $0C
    AND #$00FF
    CMP #$0005
    BNE out
    LDA $0A
    CMP #$8000
    BCC out
    XBA
    AND #$00FF
    SEC
    SBC #$0080
    ASL
    TAX
    LDA $308000,X
    TAX
lp: LDA $308200,X
    CMP $0A
    BEQ fnd
    BCS out
    INX
    INX
    INX
    INX
    INX
    INX
    BRA lp
fnd: LDA $308202,X
    STA $0A
    LDA $308204,X
    STA $0C
out: RTS
"""
def entry(name,loopaddr):
    return f"""
{name}: LDA $0A
    PHA
    LDA $0C
    PHA
    JSR xl
    LDY #$0000
    JSR ${loopaddr:04X}
    PLA
    STA $0C
    PLA
    STA $0A
    RTS
"""
def chk(name,ctl,jpnext,pre='',jpcall=0x8674):
    return f"""
{name}: CMP #$00CC
    BCS {name}ctl
    PHA
    LDA $0C
    AND #$0100
    BEQ {name}jp
    PLA
    CMP #$0020
    BCS {name}en
    JSR ${jpcall:04X}
    JMP ${jpnext:04X}
{name}en:
{pre}    SEC
    SBC #$0020
    STA $08
    AND #$0007
    ASL
    ASL
    ASL
    ASL
    STA $06
    LDA $08
    AND #$00F8
    ASL
    ASL
    ASL
    ASL
    ASL
    CLC
    ADC $06
    CLC
    ADC #$A000
    STA $06
    LDA #$0030
    STA $08
    JSR $8956
    DEC $10
    DEC $10
    JMP ${jpnext:04X}
{name}jp: PLA
    JSR ${jpcall:04X}
    JMP ${jpnext:04X}
{name}ctl: CMP #$00DF
    BNE {name}c2
    LDA $0C
    ORA #$0100
    STA $0C
    DEC $10
    DEC $10
    DEC $10
    DEC $10
    JMP ${jpnext:04X}
{name}c2: JMP ${ctl:04X}
"""
CP1="""
cp1: PHX
    LDA #$0005
    STA $0C
    JSR xl
    PLX
    RTL
cp3: STA $0A
    LDA #$0005
    STA $0C
    JSR xl
    LDX #$0000
    LDY #$0000
cp3l: LDA [$0A],Y
    STA $7F2B90,X
    INX
    INX
    INY
    INY
    CPY #$00A0
    BCC cp3l
    RTL
"""
cur=0xF882
GL={}
blocks={}
def place(src):
    global cur
    code,lab=assemble(src,cur,GL); w(lo(cur),code); r=dict(lab); GL.update({k:v for k,v in r.items() if k in('xl',)}); cur+=len(code); return r
L={}
L.update(place(XL))
L.update(place(entry('t1',0x8B50)))
L.update(place(entry('t3',0x8622)))
L.update(place(chk('t2',0x8B64,0x8B96)))
L.update(place(CP1))
L.update(place(chk('t4',0x8636,0x8668)))
L.update(place(entry('t5',0xD698)))
L.update(place(chk('t6',0xD6AC,0xD6F2,pre='    JSR $D707\n    LDA $12\n',jpcall=0xD71F)))
assert cur<0x10000,hex(cur)
print('trampolines end',hex(cur))
def hook(addr,old,newb):
    assert orig[lo(addr):lo(addr)+len(old)]==old,hex(addr)
    w(lo(addr),newb)
J=lambda a:bytes([0x4C,a&255,a>>8])
hook(0x8B4D,bytes([0xA0,0,0]),J(L['t1']))
hook(0x8B59,bytes([0xC9,0xCC,0,0xB0,6]),J(L['t2'])+b'\xEA\xEA')
hook(0x861F,bytes([0xA0,0,0]),J(L['t3']))
def hookb(bank,addr,old,newb):
    o=lo(addr,bank); assert orig[o:o+len(old)]==old,(hex(bank),hex(addr),orig[o:o+len(old)].hex()); w(o,newb)
def JSL(a): return bytes([0x22,a&255,a>>8,0x02])
hookb(1,0xB898,bytes([0xA9,5,0,0x85,0x0C]),JSL(L['cp1'])+b'\xEA')
hookb(3,0xAF45,bytes([0xA9,5,0,0x85,0x0C]),JSL(L['cp1'])+b'\xEA')
for a_ in (0x8823,0x8A21,0x8BB2,0x8BD3,0x8E54,0x90D0,0x928B,0x92A7,0xAEF7):
    hookb(3,a_,bytes([0xA9,5,0,0x85,0x0C]),JSL(L['cp1'])+b'\xEA')
for a_ in (0xDEDC,0xDF42,0xDFA8,0xE00E):
    hookb(1,a_,bytes([0xAA,0x8B,0xA0,0x90,0x2B,0xA9,0x9F,0,0x54,0x7F,0x05]),JSL(L['cp3'])+b'\xEA'*7)
hook(0xD695,bytes([0xA0,0,0]),J(L['t5']))
hook(0xD6A1,bytes([0xC9,0xCC,0,0xB0,6]),J(L['t6'])+b'\xEA\xEA')
hook(0x862B,bytes([0xC9,0xCC,0,0xB0,6]),J(L['t4'])+b'\xEA\xEA')
import labels, glyph_patch
bad=labels.apply(rom); assert not bad,bad
glyph_patch.apply(rom)
import ui_font, creel_hook, content_page
ui_font.apply(rom,orig)
content_page.apply(rom,orig)
assert cur<0xFD00
creel_hook.apply(rom,orig,lo,L['xl'])
import name_entry
def kglyph(ch):
    im=pcf.glyph[ord(ch)][3].convert('1'); px=im.load()
    return [sum(0x80>>x for x in range(8) if px[x,y]) for y in range(16)]
name_entry.apply(rom,orig,kglyph)
name_entry.secret_name(rom,orig)
import postcard, fishery, cs_names
if user_edits: fishery.SHORT.update(user_edits.FISHERY_SHORT_USER)
postcard.apply(rom,orig,kglyph)
fnames={}
for i_ in range(73):
    o_=0x28018+i_*23; p_=struct.unpack('<H',orig[o_+0x11:o_+0x13])[0]
    e_=orig.index(b'\0',0x28000+p_-0x8000)
    jp_=decode(orig,0x28000+p_-0x8000,e_,single,kanji)
    if jp_ in Z: fnames[p_]=Z[jp_]
print('fishery short names',fishery.apply(rom,orig,fnames))
cs_names.apply(rom,orig)
import map_labels, field_signs
if user_edits: map_labels.SHORT.update(user_edits.MAP_SHORT_USER)
map_labels.apply(rom,orig,L['xl'],fnames)
print('signs',field_signs.apply(rom,orig))
import title_logo, item_icons
item_icons.apply(rom,orig)
import gear_placeholders
gear_placeholders.apply(rom,orig)
title_logo.apply(rom,orig)
# checksum
rom[0x7FDC:0x7FE0]=b'\0\0\0\0'
s=sum(rom)&0xFFFF
rom[0x7FDC:0x7FDE]=struct.pack('<H',s^0xFFFF); rom[0x7FDE:0x7FE0]=struct.pack('<H',s)
OUT=P.out('knt2_en.sfc')
open(OUT,'wb').write(rom)
# IPS
def ips(a,b):
    out=bytearray(b'PATCH'); i=0; n=len(b)
    a=a+b'\x00'*0  # extension handled as diff vs missing
    while i<n:
        if i<len(a) and a[i]==b[i]: i+=1; continue
        j=i
        while j<n and (j>=len(a) or a[j]!=b[j]) and j-i<0xFFFF: 
            j+=1
        # merge small gaps
        while True:
            k=j; 
            while k<n and k-j<8 and (k<len(a) and a[k]==b[k]): k+=1
            if k<n and k-j<8 and (k>=len(a) or a[k]!=b[k]) and j-i<0xF000: 
                j=k
                while j<n and (j>=len(a) or a[j]!=b[j]) and j-i<0xF000: j+=1
            else: break
        if i==0x454F46: i-=1  # avoid 'EOF' offset
        chunk=b[i:j]
        out+=struct.pack('>I',i)[1:]+struct.pack('>H',len(chunk))+chunk; i=j
    out+=b'EOF'; return bytes(out)
p=ips(orig,bytes(rom)); open(P.out('knt2_en.ips'),'wb').write(p)
print('ok strings',len(table),'ips',len(p))
