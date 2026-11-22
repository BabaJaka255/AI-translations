; Kawa no Nushi Tsuri (FC) English text hooks.  Lives in the fixed bank ($FE42-$FFCF).
;
; Line pointers ($12/$13) with bit 7 of $13 clear are English lines in an
; expansion bank: bits 6-5 of $13 pick one of four text banks, bits 4-0 are
; address bits 12-8 inside the $8000 window.  The hook maps that bank into
; $8000, reads the line, then restores the game's own $8000 bank via $C5E5.
;
; English lines fill both rows of the line buffer ($0650 = upper row, the
; row Japanese used for dakuten, $0662 = lower row), 18 tiles each. A line
; of 18 or fewer tiles is moved to the lower row, so it sits where Japanese did.

SAVE13  = $078B
ENFLAG  = $078E
CURBANK = $0795
TMPY    = $0799
PHASE   = $07D5          ; 1 while the top row of a two-row line is being revealed

.segment "HOOK"

TXT_BEGIN:                 ; replaces LDX #$12 / LDY #$00 at $F127
        lda $13
        sta SAVE13
        bmi @orig
        lsr a
        lsr a
        lsr a
        lsr a
        lsr a
        tax
        lda BANKTAB,x
        sta CURBANK
@retry: lda #$06
        sta $8000
        lda CURBANK
        sta $8001
        cmp $8000          ; every text bank starts with its own number
        bne @retry
        lda $13
        and #$1F
        ora #$80
        sta $13
        lda #$01
        sta ENFLAG
        ldx #$00
        ldy #$00
        rts
@orig:  lda #$00
        sta ENFLAG
        ldx #$12
        ldy #$00
        rts

TXT_END:                   ; replaces TXA/SEC/SBC #$12/STA $07BC at $F1EB
        lda #$00
        sta PHASE
        lda ENFLAG
        bne @en
        txa
        sec
        sbc #$12
        sta $07BC
        rts
@en:    sty TMPY
        lda SAVE13
        sta $13
        lda #$00
        sta ENFLAG
        jsr $C5E5          ; put the game's own bank back in $8000
        cpx #19
        bcs @two
        ; one row: move it down to the lower row
        txa
        bne @nz
        ldx #$01           ; empty line still needs one column
        txa
@nz:    sta $07BC
        tay                ; y = count
        ldx #$00
@mv:    lda $0650,x
        sta $0662,x
        lda #$FE
        sta $0650,x
        inx
        dey
        bne @mv
        ldy TMPY
        rts
@two:   lda #18
        sta $07BC
        lda #$01           ; reveal the top row first, then the bottom row
        sta PHASE
        ldy TMPY
        rts

BANKTAB: .byte 14, 15, 16, 17

; Menu cursor start row ($E4DC).  The food/item lists and the shops start one
; row higher ($28) than the other windows ($30); also does the original
; "lda #0 / sta $079F" that this call replaces.
INITY:  lda #$00
        sta $079F
        lda $0757
        bne @y28
        lda $079E
        cmp #$10
        beq @y28
        cmp #$12
        beq @y28
        cmp #$02
        bne @y30
        lda $07A4
        cmp #$0C
        beq @y28
@y30:   lda #$30
        rts
@y28:   lda #$28
        rts

; Typewriter (NMI, $E56E): write one column of the line.  While PHASE is set
; only the top row is shown; the bottom tile is written blank.
REVEAL: lda $0650,x
        sta $2007
        lda PHASE
        beq @both
        lda #$FE
        sta $2007
        rts
@both:  lda $0650,y
        sta $2007
        rts

; End of a column pass (NMI, $E5A0, replaces DEC $07BC / BNE).  Z clear = not
; finished.  After the top-row pass, go back to the line start for the bottom row.
REVEALEND:
        dec $07BC
        bne @go
        lda PHASE
        beq @done
        lda #$00
        sta PHASE
        sta $07BA
        lda #18
        sta $07BC
        lda $93
        sta $91
        lda $94
        sta $92
@go:    lda #$01
        rts
@done:  lda #$00
        rts

; Row break for English lines ($F13C).  English never uses the dakuten prefix
; $1A, so inside an English line $1A means "continue on the second row": the
; rest of the top row is filled with blanks.  Japanese lines take the original
; dakuten path.  (Replaces STA $0C / TXA at $F13C.)
NEWROW: sta $0C
        lda ENFLAG
        beq @jp
        lda $0C
        cmp #$1A
        bne @jp
        cpx #18
        bcs @done
        lda #$FE
@pad:   sta $0650,x
        inx
        cpx #18
        bcc @pad
@done:  jmp $F1E7
@jp:    txa
        jmp $F13F
