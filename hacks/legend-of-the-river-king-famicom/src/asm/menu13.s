; Kawa no Nushi Tsuri (FC) English menus, bank 13 ($A000 window), free space at $B985.
;
; The food and item windows become one-column lists (one name per row, rows 1-10,
; 9 letters each), so the shared menu cursor steps 8 px there and ignores left/right.
; Shop windows put each name on the upper row of its pair with the price below it,
; so the shop cursor starts one row higher.  Everything else keeps the original logic.

MODE    = $079E          ; command index: 0 bait, 1 gear, 2 talk, $10 eat, $11 bag, $12 items
BATEAT  = $0757          ; nonzero while eating in battle (food window)
TALKTO  = $07A4          ; $0C = shopkeeper
IDX     = $07BE
CURY    = $0228

.segment "MENU"

; A = 0 normal, 1 list (food/items), 2 shop
STYLE:  lda BATEAT
        bne @list
        lda MODE
        cmp #$10
        beq @list
        cmp #$12
        beq @list
        cmp #$02
        bne @norm
        lda TALKTO
        cmp #$0C
        bne @norm
        lda #2
        rts
@list:  lda #1
        rts
@norm:  lda #0
        rts

; up: A = new Y, carry set when blocked          (called from $A60B)
UPCALC: jsr STYLE
        tax
        lda CURY
        sec
        sbc STEP,x
        cmp MINY,x
        bcc @blk
        clc
        rts
@blk:   sec
        rts

; down: A = new Y, carry set when blocked        (called from $A63A)
DNCALC: jsr STYLE
        tax
        beq @norm
        lda CURY
        clc
        adc STEP,x
        cmp #$78
        bcs @blk
        sta $0C
        cpx #1
        bne @ok
        ldx IDX
        inx
        ldy LISTSLOT,x
        ldx $0100,y
        cpx #$FE
        beq @blk
@ok:    lda $0C
        clc
        rts
@norm:  lda BATEAT          ; original rule: gear window stops at $70, others at $80
        bne @n80
        lda MODE
        cmp #$01
        bne @n80
        lda #$70
        bne @nset
@n80:   lda #$80
@nset:  sta $0C
        lda CURY
        clc
        adc #$10
        cmp $0C
        bcs @blk
        sta $0C
        ldx IDX
        inx
        ldy ORIGSLOT,x
        ldx $0100,y
        cpx #$FE
        beq @blk
        lda $0C
        clc
        rts
@blk:   sec
        rts

; left/right allowed? carry set = yes             (called from $A5ED)
LRCHK:  jsr STYLE
        cmp #1
        beq @no
        lda MODE
        cmp #$0A
        bcs @yes
        lda BATEAT
        bne @yes
@no:    clc
        rts
@yes:   sec
        rts

; draw one food/item name: X = entry*8 (as the game passes it), Y = window offset
NAMEDRAW:
        txa
        lsr a
        lsr a
        lsr a
        sta $0C
        txa
        clc
        adc $0C            ; entry*9
        tax
        lda #9
        sta $0C
@l:     lda NAMES,x
        sta $0100,y
        inx
        iny
        dec $0C
        bne @l
        rts

; rod name across the whole top border (10 tiles at $0101)
RODTITLE:
        lda $07EA
        asl a
        sta $0C
        asl a
        asl a
        clc
        adc $0C            ; rod*10
        tax
        ldy #0
@l:     lda RODS,x
        sta $0101,y
        inx
        iny
        cpy #10
        bcc @l
        rts

STEP:   .byte $10, $08, $10
MINY:   .byte $30, $28, $28
ORIGSLOT: .byte $1A, $32, $4A, $62, $7A, $1F, $37, $4F, $67, $7F, $7F
LISTSLOT: .byte $0E, $1A, $26, $32, $3E, $4A, $56, $62, $6E, $7A, $7A
NAMES:  .res 13*9, $FE     ; filled by knt_build.py
RODS:   .res 4*10, $72     ; filled by knt_build.py
ITEMTITLE: .res 6, $72     ; title cols 3-8 of the item window
