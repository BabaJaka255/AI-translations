"""Fishery price window (template 02:C7F6, drawn at 82:AAE6): the fish name is drawn into 12 tiles
($1A0-$1AB / $1B0-$1BB) at window columns 2-13; the price digits sit at columns 15-17.
We widen the field to 13 tiles (columns 1-13) and give names longer than 13 a short form here only."""
from name_entry import lo
BANK=0x38; SHORT_A=0xCD00; CODE_A=0xCE80
SHORT={'Bagrid Catfish':'Bagrid C.fish','Torrent Catfish':'Torrent Catf.','Amur Snakehead':'Amur Snakehd.',
       'Pacific Redfin':'Pac. Redfin','Japanese Lates':'Jpn. Lates','Starry Flounder':'Star Flounder',
       'Redspot Salmon':'Redspot Salm.','Softshell Turtle':'Softshell'}
MAXC=13
def apply(rom,orig,names):
    """names: {bank-5 pointer: English name} for every fish record name."""
    tbl=bytearray(); strs=bytearray(); pairs=[]
    for p,en in sorted(names.items()):
        if len(en)<=MAXC: continue
        s=SHORT[en]; assert len(s)<=MAXC,s
        pairs.append((p,s))
    strbase=SHORT_A+4*len(pairs)+2
    for p,s in pairs:
        tbl+=bytes([p&255,p>>8,(strbase+len(strs))&255,(strbase+len(strs))>>8])
        strs+=b'\xdf'+s.encode()+b'\x00'
    tbl+=b'\x00\x00'
    blob=tbl+strs; assert SHORT_A+len(blob)<CODE_A
    o=lo(BANK,SHORT_A); rom[o:o+len(blob)]=blob
    T=SHORT_A
    code=bytes([0xDA,                          # PHX
        0x85,0x0A, 0xA9,0x05,0x00,0x85,0x0C,   # STA $0A ; $0C=5
        0xA2,0x00,0x00,                        # LDX #0
        0xBF,T&255,T>>8,BANK,                  # lp: LDA long tbl,X
        0xF0,0x17,                             # BEQ done
        0xC5,0x0A,                             # CMP $0A
        0xF0,0x06,                             # BEQ hit
        0xE8,0xE8,0xE8,0xE8,                   # INX x4
        0x80,0xF2,                             # BRA lp
        0xBF,(T+2)&255,(T+2)>>8,BANK,          # hit: LDA long tbl+2,X
        0x85,0x0A, 0xA9,BANK,0x00,0x85,0x0C,   # $0A=str, $0C=bank
        0xFA,0x6B])                            # done: PLX RTL
    # fix branch offsets: lp at 11; BEQ done -> done index; hit index
    code=bytearray(code)
    lp=11; i_beq=15; i_hit=27; i_done=len(code)-2
    code[i_beq+1]=i_done-(i_beq+2)
    code[19+1]=i_hit-(19+2)
    code[25+1]=(lp-(25+2))&0xFF
    o=lo(BANK,CODE_A); rom[o:o+len(code)]=code
    o=lo(2,0xABE0); assert orig[o:o+7]==bytes.fromhex('850aa9050085 0c'.replace(' ',''))
    rom[o:o+7]=bytes([0x22,CODE_A&255,CODE_A>>8,BANK,0xEA,0xEA,0xEA])
    # DMA 13 tiles instead of 12 (top and bottom halves)
    for a in (0xABFE,0xAC16):
        o=lo(2,a); assert orig[o:o+3]==bytes.fromhex('a9c000'); rom[o+1]=0xD0
    # window template: name row 8/9 -> columns 1..13
    base=lo(2,0xC7F6)+8; W=20
    for r,t0 in ((8,0x1A0),(9,0x1B0)):
        attr=(orig[base+2*(r*W+2)]|orig[base+2*(r*W+2)+1]<<8)&0xFC00
        assert (orig[base+2*(r*W+2)]|orig[base+2*(r*W+2)+1]<<8)&0x3FF==t0
        for c in range(13):
            v=attr|(t0+c); i=base+2*(r*W+1+c); rom[i]=v&255; rom[i+1]=v>>8
    return pairs
