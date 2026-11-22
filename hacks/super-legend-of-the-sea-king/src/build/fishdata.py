"""Fish records in bank $87: 113 records of 0x21 bytes from ROM 0x3C219. Each holds four string pointers
(name, alias, description, cooking) into the strings at $87:D091-$87:F6E4. The description has no line
breaks in Japanese; the window wraps it."""
FIRST=0x3C219; SIZE=0x21; COUNT=113
# The page draws the description with loop C from column 14 (units of 2 per English letter), wraps at 60
# and starts later lines at 2: 23 letters on the first line, then 29. 0x1000 bytes of staging = 4 lines.
DESC_LIMIT=(28,4)
FIRST_LINE=22
def wrap(text):
    lines=[]; cur=''
    for word in text.split():
        lim=FIRST_LINE if not lines else DESC_LIMIT[0]
        if cur and len(cur)+1+len(word)>lim: lines.append(cur); cur=word
        else: cur=(cur+' '+word) if cur else word
    lines.append(cur)
    return '\n'.join(lines)
def records(rom):
    for n in range(COUNT):
        a=FIRST+n*SIZE
        yield n,[rom[a+2*k]|rom[a+2*k+1]<<8 for k in range(4)]

def center_code(rom,orig,place):
    """The fish page centres the name from its Japanese byte length (table $81:BE23: start = 16 - 2*len, in
    4px units). With an English name the start is 16 - letters instead."""
    def lo(bank,addr): return (bank&0x7F)*0x8000+(addr&0x7FFF)
    o=lo(0x81,0xBC0C)
    old=bytes.fromhex('ad081d8512a98700851 4e220a00000b712f003c880f9c22088980aaabf23be818518'.replace(' ',''))
    assert orig[o:o+len(old)]==old and len(old)==0x22,orig[o:o+0x22].hex()
    lab=place("""
fcn: .db $AD,$08,$1D
    STA $12
    PHA
    LDA #$0087
    STA $14
    JSR xl
    LDA $14
    AND #$00FF
    CMP #$0087
    BEQ fjp
    .db $E2,$20
    LDY #$0000
    LDX #$0000
fcl: LDA [$12],Y
    BEQ fcd
    .db $C9,$DF
    BEQ fcn2
    .db $C9,$20
    BCC fcn2
    INX
fcn2: INY
    BRA fcl
fcd: .db $C2,$20
    .db $8A
    CMP #$0011
    BCC fco
    LDA #$0010
fco: STA $18
    LDA #$0010
    SEC
    .db $E5,$18
    AND #$FFFE
    STA $18
    PLA
    STA $12
    LDA #$0087
    STA $14
    RTL
fjp: PLA
    STA $12
    LDA #$0087
    STA $14
    .db $E2,$20
    LDY #$0000
fjl: LDA [$12],Y
    BEQ fjd
    INY
    BRA fjl
fjd: .db $C2,$20
    .db $88,$98
    ASL
    TAX
    LDA $81BE23,X
    STA $18
    RTL
""")
    a=lab['fcn']; rom[o:o+0x22]=bytes([0x22,a&255,(a>>8)&255,0x82])+bytes([0xEA]*30)
    return lab
