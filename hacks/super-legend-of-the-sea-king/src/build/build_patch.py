"""Umi no Nushi Tsuri English patch: ROM expansion, English text engine, string relocation.

Ported from the Kawa no Nushi Tsuri 2 build (build_patch2.py in the River King toolkit).
Same design: a DF byte switches a string to ASCII, English strings live in new banks,
and a lookup routine (xl) swaps each old string pointer for its English one."""
import paths as P
import sys,re,json,struct
sys.path.insert(0,P.BUILD)
from asm import assemble
P.check_rom()
rom=bytearray(open(P.ROM,'rb').read()); orig=bytes(rom)
assert len(rom)==0x200000
# --- expand 16 -> 32 Mbit. New space is ROM 0x200000+, banks $C0-$FF (FastROM mirror) ---
rom+=b'\xFF'*(0x400000-len(rom))
assert orig[0x7FD7]==0x0B; rom[0x7FD7]=0x0C
def lo(bank,addr): return (bank&0x7F)*0x8000+(addr&0x7FFF)
def w(off,data): rom[off:off+len(data)]=data
XBANK=0xC0                    # $C0:8000 index, $C0:8200 table, $C0:A000 ASCII font
SBANK=0xC1                    # English strings from $C1:8000
FONT=lo(XBANK,0xA000)

# --- 8x16 ASCII font in the 16x16 slot layout the glyph blitter ($82:875F) reads ---
from PIL import PcfFontFile
pcf=PcfFontFile.PcfFontFile(open(P.font('koi8x16.pcf'),'rb'))
for g in range(95):
    im=pcf.glyph[0x20+g][3].convert('1'); assert im.size==(8,16)
    px=im.load(); base=FONT+(g>>3)*0x100+(g&7)*0x10
    for y in range(16):
        rom[base+(y if y<8 else 0x80+y-8)]=sum(0x80>>x for x in range(8) if px[x,y])
    for y in range(8): rom[base+8+y]=0; rom[base+0x88+y]=0

# --- strings ---
import translations
from umilib import jp_width, WID
EN=dict(translations.EN)
script={x['id']:x for x in json.load(open(P.out('script.json'),encoding='utf-8'))}
ERR=[]
# worst-case columns of each insert in English: the longest name it can show (fish 14, bait 16, hooks 15,
# lures 17, rods 17, food 13, items 15, creatures 15, places 10, numbers 6, compass direction 5)
EN_WID=dict(WID,D8=14,CE=16,CF=15,D0=15,D1=17,D2=15,D3=17,D5=13,D6=15,D7=5,D9=15,DB=10)
def enc(sid,s,maxcol,maxlines=None):
    out=bytearray([0xDF]); lines=s.split('\n')
    if maxlines and len(lines)>maxlines: ERR.append((sid,'%d lines, max %d'%(len(lines),maxlines),s))
    for line in lines:
        cols=0; i=0
        while i<len(line):
            m=re.match(r'\{([0-9A-Fa-f]{2})\}',line[i:])
            if m: out.append(int(m.group(1),16)); cols+=EN_WID.get(m.group(1).upper(),12); i+=m.end(); continue
            c=ord(line[i]); assert 0x20<=c<0x7F,(sid,line,line[i]); out.append(c); cols+=1; i+=1
        if cols>maxcol: ERR.append((sid,'%d cols, max %d'%(cols,maxcol),line))
        out.append(0xCC)
    out[-1]=0
    return bytes(out)
entries={}   # (bank, old ptr) -> bytes
for sid,txt in sorted(EN.items()):
    e=script[sid]; assert e['snes'].startswith('86:'),sid
    jw,jl=jp_width(bytes.fromhex(e['raw']))
    entries[(0x86,int(e['snes'].split(':')[1],16))]=enc(sid,txt,*translations.limits(sid,jw,jl))
# string 14: the Fishing Note contents labels, drawn as one run of glyphs (see content_page.py)
import content_page
entries[(0x86,int(script[14]['snes'].split(':')[1],16))]=enc(14,content_page.TEXT,64,1)
# string 13: the fish page side labels, drawn as one run; the page shows tiles 0-3 釣果, 4-7 最長, 8-11 釣率,
# 12-15 利用 and 16-19 生活 (the second 16-tile staging block), four letters each
entries[(0x86,int(script[13]['snes'].split(':')[1],16))]=enc(13,'Qty BestRateUsesInfo',32,1)
# string 22: the cup ranking header, drawn as one run (see rank_board.py)
import rank_board
entries[(0x86,int(script[22]['snes'].split(':')[1],16))]=enc(22,rank_board.TEXT,16,1)
import letters
for sid in letters.ADDRESS:
    if len(EN[sid])>16: ERR.append((sid,'envelope address over 16 letters',EN[sid]))
for sid in letters.SENDER:
    if len(EN[sid])>8: ERR.append((sid,'envelope sender over 8 letters',EN[sid]))
# the rivals (strings 30-61) are copied into 8-letter name slots on the board
for sid in range(30,62):
    if len(EN.get(sid,''))>8: ERR.append((sid,'rival name over 8 letters',EN[sid]))
import cs_panel
for off,txt in cs_panel.SEGS.items():
    entries[(0x86,int(script[3]['snes'].split(':')[1],16)+off)]=enc(3,txt,64,1)
# name entry keyboards (strings 10-12) and the letters copied by 81:DDCB (see name_entry.py)
import name_entry
for sid,txt in name_entry.DISPLAY.items():
    entries[(0x86,int(script[sid]['snes'].split(':')[1],16))]=enc(sid,txt,256,1)
import board
for sid,txt in board.DISPLAY.items():
    entries[(0x86,int(script[sid]['snes'].split(':')[1],16))]=enc(sid,txt,256,1)
for sid in translations.FIXED:
    k=(0x86,int(script[sid]['snes'].split(':')[1],16))
    if k in entries: assert len(entries[k])<=0xA1,(sid,len(entries[k]))
# names in the data tables (bank $86) and the fish records (bank $87)
import tr_names, fishdata
NAME_MAX=18
for ptr,txt in tr_names.NAMES86.items():
    entries[(0x86,ptr)]=enc('name %04X'%ptr,txt,NAME_MAX,1)
for n,ptrs in fishdata.records(orig):
    if n not in tr_names.FISH: continue
    name,alias,cook=tr_names.FISH[n]
    entries[(0x87,ptrs[0])]=enc('fish %d'%n,name,NAME_MAX,1)
    if alias: entries[(0x87,ptrs[1])]=enc('fish %d alias'%n,alias,NAME_MAX,1)
    entries[(0x87,ptrs[3])]=enc('fish %d cook'%n,cook,NAME_MAX+2,1)
    d=getattr(tr_names,'FISH_DESC',{}).get(n)
    if d: entries[(0x87,ptrs[2])]=enc('fish %d desc'%n,fishdata.wrap(d),*fishdata.DESC_LIMIT)
if ERR:
    for e in ERR: print('TOO LONG',e)
    raise SystemExit(1)
bank=SBANK; pos=0; tables={0x86:[],0x87:[]}
for key in sorted(entries):
    e=entries[key]
    if pos+len(e)>0x8000: bank+=1; pos=0
    w(lo(bank,0x8000)+pos,e); tables[key[0]].append((key[1],0x8000+pos,bank)); pos+=len(e)
assert bank<0xF0
print('strings',len(entries),'last bank %02X pos %04X'%(bank,pos))
# index: 128 words per source bank ($C0:8000 for $86, $C0:8100 for $87) -> offset into the table at $C0:8200.
# Each bank's run of 6-byte entries (old, new, bank) is sorted and ends with an FFFF sentinel.
tb=bytearray(); idx=[]
for sb in (0x86,0x87):
    table=sorted(tables[sb]); base=len(tb)
    for h in range(128):
        k=0
        while k<len(table) and (table[k][0]>>8)<h+0x80: k+=1
        idx.append(base+k*6)
    tb+=b''.join(struct.pack('<HHH',o,n,b) for o,n,b in table)+struct.pack('<HHH',0xFFFF,0,0)
w(lo(XBANK,0x8000),b''.join(struct.pack('<H',x) for x in idx))
assert len(tb)<=0x2000-0x200
w(lo(XBANK,0x8200),tb)

# --- code in bank $82 free space ---
# String pointer is [$12] (bank in $14). English mode = bit $0100 of $14 (the unused byte $15).
XL=f"""
xl: LDA $14
    AND #$00FF
    CMP #$0086
    BEQ b86
    CMP #$0087
    BNE out
    JSR hix
    BCC out
    LDA ${XBANK:02X}8100,X
    BRA cont
b86: JSR hix
    BCC out
    LDA ${XBANK:02X}8000,X
cont: TAX
lp: LDA ${XBANK:02X}8200,X
    CMP $12
    BEQ fnd
    BCS out
    INX
    INX
    INX
    INX
    INX
    INX
    BRA lp
fnd: LDA ${XBANK:02X}8202,X
    STA $12
    LDA ${XBANK:02X}8204,X
    STA $14
out: RTS
hix: LDA $12
    CMP #$8000
    BCC hr
    XBA
    AND #$00FF
    SEC
    SBC #$0080
    ASL
    TAX
    SEC
hr: RTS
"""
def entry(name,body):
    # replaces the loop's LDY #$0000; runs the rest of the loop with the pointer swapped
    return f"""
{name}: LDA $12
    PHA
    LDA $14
    PHA
    JSR xl
    LDA $14
    AND #$01FF
    CMP #$0100
    BEQ {name}k
    CMP #$0170
    BEQ {name}k
    CMP #$017F
    BEQ {name}k
    AND #$00FF
{name}k: STA $14
    LDY #$0000
    JSR ${body:04X}
    PLA
    STA $14
    PLA
    STA $12
    RTS
"""
def chk(name,ctl,jpnext,jpcall,pre=''):
    # replaces CMP #$00CC / BCS ctl (A = the string byte)
    return f"""
{name}: CMP #$00CC
    BCS {name}ctl
    PHA
    LDA $14
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
    STA $10
    AND #$0007
    ASL
    ASL
    ASL
    ASL
    STA $0E
    LDA $10
    AND #$00F8
    ASL
    ASL
    ASL
    ASL
    ASL
    CLC
    ADC $0E
    CLC
    ADC #$A000
    STA $0E
    LDA #${XBANK:04X}
    STA $10
    JSR $875F
    DEC $18
    DEC $18
    JMP ${jpnext:04X}
{name}jp: PLA
    JSR ${jpcall:04X}
    JMP ${jpnext:04X}
{name}ctl: CMP #$00DF
    BNE {name}c2
    LDA $14
    ORA #$0100
    STA $14
    DEC $18
    DEC $18
    DEC $18
    DEC $18
    JMP ${jpnext:04X}
{name}c2: JMP ${ctl:04X}
"""
cur=0xEC00
GL={}
def place(src):
    global cur
    code,lab=assemble(src,cur,GL); w(lo(0x82,cur),code); GL.update({k:v for k,v in lab.items() if k=='xl'}); cur+=len(code); return lab
assert set(orig[lo(0x82,0xEB76):lo(0x82,0xFFFF)+1])=={0}
L={}
# three text loops: dialogue/window loop A ($82:843B, also used for every insert code),
# typewriter loop B ($82:8956), wrapping window loop C ($82:B19E)
L.update(place(XL))
L.update(place(entry('ta',0x843E)))
L.update(place(chk('ca',ctl=0x8452,jpnext=0x8484,jpcall=0x8490)))
L.update(place(entry('tb',0x8959)))
L.update(place(chk('cb',ctl=0x896D,jpnext=0x899F,jpcall=0x8490)))
L.update(place(entry('tc',0xB1A4)))
L.update(place(chk('cc',ctl=0xB1B8,jpnext=0xB1FE,jpcall=0xB22B,pre='    JSR $B213\n    LDA $1A\n')))
name_entry.code(rom,orig,lambda src:place(src),L['xl'])
name_entry.palettes(rom,orig,script)
name_entry.secret_name(rom,orig)
board.palettes(rom,orig,script)
board.code(rom,orig,lambda src:place(src))
fishdata.center_code(rom,orig,lambda src:place(src))
import shop
shop.code(rom,orig,lambda src:place(src))
import keepnet
keepnet.code(rom,orig,lambda src:place(src))
import map_labels
map_labels.apply(rom,orig,lambda src:place(src),
                 {ptrs[0]:tr_names.FISH[n][0] for n,ptrs in fishdata.records(orig) if n in tr_names.FISH})
import market
print('market short names',market.apply(rom,orig,lambda src:place(src),
                 {ptrs[0]:tr_names.FISH[n][0] for n,ptrs in fishdata.records(orig) if n in tr_names.FISH}))
assert cur<0x10000
print('code $82:EC00-%04X'%cur)
def hook(addr,old,new):
    o=lo(0x82,addr); assert orig[o:o+len(old)]==old,(hex(addr),orig[o:o+len(old)].hex()); w(o,new)
J=lambda a:bytes([0x4C,a&255,a>>8])
LDY0=bytes([0xA0,0,0]); CMPCC=bytes([0xC9,0xCC,0,0xB0,6])
hook(0x843B,LDY0,J(L['ta'])); hook(0x8447,CMPCC,J(L['ca'])+b'\xEA\xEA')
hook(0x8956,LDY0,J(L['tb'])); hook(0x8962,CMPCC,J(L['cb'])+b'\xEA\xEA')
hook(0xB1A1,LDY0,J(L['tc'])); hook(0xB1AD,CMPCC,J(L['cc'])+b'\xEA\xEA')

# --- label art and window UI font ---
import labels
labels.LABELS+=board.LABELS
bad=labels.apply(rom,orig); assert not bad,bad
content_page.apply(rom,orig)
cs_panel.apply(rom,orig)
import title
print('title logo sprites, block',title.apply(rom,orig))
import icons
icons.apply(rom,orig)
import field_signs
print('town tileset',field_signs.apply(rom,orig))
import fish_news
print('fish news',fish_news.apply(rom,orig))
print('rank board',rank_board.apply(rom,orig))
letters.apply(rom,orig)

# --- checksum, output ---
rom[0x7FDC:0x7FE0]=b'\xFF\xFF\x00\x00'
s=sum(rom)&0xFFFF
rom[0x7FDC:0x7FDE]=struct.pack('<H',s^0xFFFF); rom[0x7FDE:0x7FE0]=struct.pack('<H',s)
open(P.out('umi_en.sfc'),'wb').write(rom)
def ips(a,b):
    """IPS with RLE records, so the 2 MB of padding costs a few bytes."""
    out=bytearray(b'PATCH'); i=0; n=len(b)
    def same(k): return k<len(a) and a[k]==b[k]
    while i<n:
        if same(i): i+=1; continue
        if i==0x454F46: i-=1
        r=i
        while r<n and r-i<0xFFFF and b[r]==b[i] and not same(r): r+=1
        if r-i>=16:
            out+=struct.pack('>I',i)[1:]+b'\0\0'+struct.pack('>H',r-i)+b[i:i+1]; i=r; continue
        j=i
        while j<n and j-i<0xFFFF and not same(j):
            if j+16<=n and len(set(b[j:j+16]))==1 and not any(same(k) for k in range(j,j+16)): break
            j+=1
        out+=struct.pack('>I',i)[1:]+struct.pack('>H',j-i)+b[i:j]; i=j
    return bytes(out+b'EOF')
open(P.out('umi_en.ips'),'wb').write(ips(orig,bytes(rom)))
print('wrote',P.out('umi_en.sfc'))
