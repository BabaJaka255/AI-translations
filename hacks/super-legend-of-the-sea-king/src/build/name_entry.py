"""English name entry, player names and the two copy sites that read text straight from the ROM.

Name entry grid (cursor row $7F09BA, column $7F09B8): row 0 holds the buttons, rows 1-5 are the kana palette
(string 10 after the 4-byte 決定, one byte per cell; cells 46-49 run on into the first 4 bytes of string 11),
rows 6-11 the kanji palette (string 11 or 12 after its first 4 bytes, two bytes per cell). The palettes are
drawn as text into consecutive 16px glyph cells, and the chosen cell's bytes are copied into the name.

So the original strings get ASCII selection bytes in place (kanji cells become "X",00, which the name code
treats as a one-byte character), and the English display strings draw each key as a letter plus a space,
which keeps every key on its 16px cell.

Names are stored as plain ASCII without the DF marker, up to 8 letters (the 8-byte buffer at $1452, the
same room as 4 kanji). Every site that draws a name asks for English by setting bit $0100 in the bank word."""
ROWS=[
 "ABCDEFGHIJ",
 "KLMNOPQRST",
 "UVWXYZ.,'-",
 "abcdefghij",
 "klmnopqrst",
 "uvwxyz!?& ",
 "0123456789",
 "()/:;+*=#~",
 "          ",
 "          ",
 "          ",
]
CELLS=''.join(ROWS); assert len(CELLS)==110
KANA=CELLS[:46]; RUNON=CELLS[46:50]; KANJI=CELLS[50:]
MAXLEN=8
# English display strings (DF is added by the encoder). 決定 is 32px, the width of four letters.
def pairs(s): return ''.join(c+' ' for c in s)
DISPLAY={10:'Done'+pairs(KANA), 11:pairs(RUNON+KANJI), 12:pairs(RUNON+KANJI)}
DEFAULT_NAMES=["Ichiro","Mari","Katsu","Yoshie"]     # strings 4-7; Katsuhiro does not fit in 8 letters
for n in DEFAULT_NAMES: assert len(n)<=MAXLEN
NAMES_AT=(0xC0,0xF000)

def lo(bank,addr): return (bank&0x7F)*0x8000+(addr&0x7FFF)
def patch(rom,orig,off,old,new):
    assert orig[off:off+len(old)]==bytes(old),(hex(off),orig[off:off+len(old)].hex())
    rom[off:off+len(new)]=bytes(new)

def palettes(rom,orig,script):
    p=lambda sid:lo(0x86,int(script[sid]['snes'].split(':')[1],16))
    s10,s11,s12=p(10),p(11),p(12)
    assert orig[s10+50]==0 and s11==s10+51
    for i,c in enumerate(KANA): rom[s10+4+i]=ord(c)
    for base in (s11,s12):
        for i,c in enumerate(RUNON): rom[base+i]=ord(c)
        for i,c in enumerate(KANJI): rom[base+4+2*i]=ord(c); rom[base+5+2*i]=0

def code(rom,orig,place,xl_jsr):
    """place(src) assembles helpers into bank $82 and returns their labels."""
    # name length: 4 characters -> 8 letters, and the cursor steps 8px per letter instead of 16
    patch(rom,orig,lo(0x81,0x9BF7),[0xC9,0x04,0x00],[0xC9,MAXLEN,0x00])
    patch(rom,orig,lo(0x81,0x9C59),[0xC9,0x04,0x00,0xD0,0x03,0xA9,0x03,0x00,0x0A,0x0A,0x0A,0x0A],
                                    [0xC9,MAXLEN,0x00,0xD0,0x03,0xA9,MAXLEN-1,0x00,0x0A,0x0A,0x0A,0xEA])
    # draw names in English: bank word $0000 -> $0100 (name buffer), $0070 -> $0170 (save slots)
    for a in (0x81983F,0x819E13):
        patch(rom,orig,lo(a>>16,a&0xFFFF),[0xA9,0x00,0x00,0x85,0x14],[0xA9,0x00,0x01,0x85,0x14])
    patch(rom,orig,lo(0x82,0x856B),[0xA9,0x00,0x00,0x85,0x14],[0xA9,0x00,0x01,0x85,0x14])
    for a in (0x9005,0x9018,0x902B,0x903E,0xD6E7,0xDC9B):
        patch(rom,orig,lo(0x81,a),[0xA9,0x70,0x00,0x85,0x14],[0xA9,0x70,0x01,0x85,0x14])
    # default names: a table of pointers at NAMES_AT, then the ASCII names
    nb,na=NAMES_AT; o=lo(nb,na); ptrs=[]; q=na+8
    for n in DEFAULT_NAMES:
        ptrs.append(q); rom[lo(nb,q):lo(nb,q)+len(n)+1]=n.encode()+b'\0'; q+=len(n)+1
    for k,v in enumerate(ptrs): rom[o+2*k]=v&255; rom[o+2*k+1]=v>>8
    lab=place(f"""
nmp: .db $BB
    LDA ${nb:02X}{na-8:04X},X
    STA $12
    LDA #$00{nb:02X}
    STA $14
    RTL
lcp: STA $12
    LDA #$0086
    STA $14
    JSR xl
    LDY #$0000
    .db $E2,$20
lcl: LDA [$12],Y
    .db $99,$1A,$11
    BEQ lce
    INY
    CPY #$00A1
    BCC lcl
lce: .db $C2,$20
    RTL
""")
    J=lambda a:[0x22,a&255,(a>>8)&255,0x82]
    # 81:A13F  LDA [$0E],Y / STA $12 / LDA #$0086 / STA $14  ->  JSL nmp (Y = 8..14, the string id * 2)
    patch(rom,orig,lo(0x81,0xA13F),[0xB7,0x0E,0x85,0x12,0xA9,0x86,0x00,0x85,0x14],J(lab['nmp'])+[0xEA]*5)
    # 81:DDCB  TAX / PHB / LDY #$111A / LDA #$00A0 / MVN $86,$00 / PLB  ->  JSL lcp (copies the English letter)
    patch(rom,orig,lo(0x81,0xDDCB),[0xAA,0x8B,0xA0,0x1A,0x11,0xA9,0xA0,0x00,0x54,0x00,0x86,0xAB],J(lab['lcp'])+[0xEA]*8)
    return lab

def secret_name(rom,orig,name=b'BoatTaro'):
    """The brother's hidden name ふね太郎 ("Fune Taro") unlocks the same stocked tackle box as Kawa 2's
    つり太郎: $81:98F2 compares the 8-byte name at $1452 with $81:995B. English keyboard version."""
    o=0x995B; assert orig[o:o+8]==bytes.fromhex('4038e044e0220000') and len(name)<=8
    rom[o:o+8]=name.ljust(8,b'\0')
