"""Tackle shop: the item window under the shelf. $83:97F4 copies the item name ([$12], bank $86) to $0C04,
adds CC DA E0 00 ("<newline><price>円") and draws the copy from bank $00, so the name never goes through
the English lookup. The copy is replaced by a helper that looks the name up first, and ends an English
name with " yen" in place of 円. Called from 8 shelf pages ($83:88C7 ... $83:94FD)."""
def lo(bank,addr): return (bank&0x7F)*0x8000+(addr&0x7FFF)
def code(rom,orig,place):
    lab=place("""
shn: JSR xl
    .db $E2,$20
    LDY #$0000
shl: LDA [$12],Y
    BEQ she
    .db $C9,$E0
    BNE shc
    .db $99,$04,$0C
    INY
    LDA [$12],Y
shc: .db $99,$04,$0C
    INY
    BRA shl
she: .db $BB
    LDY #$0000
    LDA [$12],Y
    .db $C9,$DF
    BEQ shen
    .db $A9,$CC,$9D,$04,$0C,$E8,$A9,$DA,$9D,$04,$0C,$E8,$A9,$E0,$9D,$04,$0C,$E8
    .db $A9,$00,$9D,$04,$0C,$E8,$9D,$04,$0C
    RTL
shen: .db $A9,$CC,$9D,$04,$0C,$E8,$A9,$DA,$9D,$04,$0C,$E8,$A9,$20,$9D,$04,$0C,$E8
    .db $A9,$79,$9D,$04,$0C,$E8,$A9,$65,$9D,$04,$0C,$E8,$A9,$6E,$9D,$04,$0C,$E8
    .db $A9,$00,$9D,$04,$0C
    RTL
""")
    o=lo(0x83,0x97F4); assert orig[o:o+7]==bytes.fromhex('e220a00000b712'),orig[o:o+7].hex()
    a=lab['shn']; rom[o:o+7]=bytes([0x22,a&255,(a>>8)&255,0x82,0x4C,0x2A,0x98])
