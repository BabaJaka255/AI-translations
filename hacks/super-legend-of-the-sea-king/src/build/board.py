"""Family message board keyboard (input code $81:CD14-D2D8, text buffer $111A, drawn at $81:D070).

Grid: row $7F09BA, column $7F09B8. Row 0: mode button (col 0), ー (col 1, byte AA), digits (col c -> byte c-1).
Row 1: ? ! 、 。 ゛ ゜ backspace space 改行 (bytes AC AB 0D 0E, dakuten handlers, $CF72, 0C, CC).
Rows 2-6: the palette for mode $7F09C2 (0 = string 75, 1 = string 76, 2 = string 77), cell (row-2)*10+col,
read from string + 6 (after ?!改行); modes 0/1 one byte per cell, mode 2 two bytes.
The palettes are drawn from the same strings with loop C, so as on the name entry the strings get ASCII
selection bytes in place and English display entries (each key a letter plus a space). Every mode is made
one byte per cell, the fixed keys insert ASCII, ゛/゜ are disabled, and the buffer is drawn in English."""
PALETTES={
 75:"ABCDEFGHIJ" "KLMNOPQRST" "UVWXYZ.,'-" "!?&()/:;+*" "=#%~@\"<>_ ",
 76:"abcdefghij" "klmnopqrst" "uvwxyz.,'-" "!?&()/:;+*" "=#%~@\"<>_ ",
 77:"0123456789" "!?&()/:;+*" "=#%~@\"<>_^" "[]{}|$`   " "          ",
}
for v in PALETTES.values(): assert len(v)==50
def pairs(s): return ''.join(c+' ' for c in s)
DISPLAY={sid:'? ! Line'+pairs(p) for sid,p in PALETTES.items()}
# mode button art in the label sheet (16-tile row at ROM 0x4B600): tiles 4-7 (かな) show while in mode 2,
# 8-11 (漢字) in mode 1, 12-15 (カナ) in mode 0, i.e. the mode the button switches to
LABELS=[(0x4B600,16,4,4,('(ABC)','ABC')),(0x4B600,16,8,4,('(#12)','#12')),(0x4B600,16,12,4,('(abc)','abc'))]

def lo(bank,addr): return (bank&0x7F)*0x8000+(addr&0x7FFF)
def patch(rom,orig,a,old,new):
    o=lo(a>>16,a&0xFFFF); assert orig[o:o+len(old)]==bytes(old),(hex(a),orig[o:o+len(old)].hex()); rom[o:o+len(new)]=bytes(new)

def palettes(rom,orig,script):
    for sid,p in PALETTES.items():
        o=lo(0x86,int(script[sid]['snes'].split(':')[1],16))
        for i,c in enumerate(p): rom[o+6+i]=ord(c)

def code(rom,orig,place):
    patch(rom,orig,0x81D29D,[0xC9,0x02,0x00,0xF0,0x17],[0xC9,0x02,0x00,0xEA,0xEA])   # every mode: one byte
    for a,old,new in ((0x81CDB6,0xAC,'?'),(0x81CDD7,0xAB,'!'),(0x81CDF8,0x0D,','),(0x81CE19,0x0E,'.'),
                      (0x81CF1A,0x0C,' '),(0x81D041,0xAA,'-')):
        patch(rom,orig,a,[0xA9,old],[0xA9,ord(new)])
    patch(rom,orig,0x81CE37,[0xF0,0x4A],[0x80,0x4A])        # ゛ and ゜: refuse (they rewrite the kana before)
    patch(rom,orig,0x81CE98,[0xF0,0x4B],[0x80,0x4B])
    lab=place("""
bdg: .db $AF,$B8,$09,$7F,$18,$69,$2E
    RTL
""")
    a=lab['bdg']                                             # digits: column + $2E is ASCII
    patch(rom,orig,0x81D05C,[0xAF,0xB8,0x09,0x7F,0x3A],[0x22,a&255,(a>>8)&255,0x82,0xEA])
    # $81:DEC2 and $81:DF45 measure the buffer (cursor column $0E, 28 half-width cells per line, 4 lines):
    # every single-byte character is now one cell, as English letters are 8px
    for a in (0x81DEDD,0x81DF60):
        patch(rom,orig,a,bytes.fromhex('20d4dfc90fb004e60e8004e60ee60e'),[0xE6,0x0E]+[0xEA]*13)
    # the buffer is shown in English: board editor, the board in a window, and the letter page
    patch(rom,orig,0x81D078,[0xA9,0x00,0x00,0x85,0x14],[0xA9,0x00,0x01,0x85,0x14])
    patch(rom,orig,0x81C09E,[0xA9,0x00,0x00,0x8D,0x0E,0x02],[0xA9,0x00,0x01,0x8D,0x0E,0x02])
    # the board itself: four messages at $7F:09F2 + $60*k, drawn at two sites each
    for a in (0x81C803,0x81C838,0x81C86D,0x81C8A2,0x81CA68,0x81CA9D,0x81CAD2,0x81CB07):
        patch(rom,orig,a,[0xA9,0x7F,0x00,0x85,0x14],[0xA9,0x7F,0x01,0x85,0x14])
    patch(rom,orig,0x81DE2F,[0xA9,0x00,0x00,0x85,0x14],[0xA9,0x00,0x01,0x85,0x14])
