; Kawa no Nushi Tsuri (FC) English status window, bank 9, free space at $BFAB.
; The area name in the status window's top border grows from 6 to 10 tiles.
.segment "STAT"
AREATITLE:
        ldx $7B
        dex
        txa
        asl a
        sta $0C
        asl a
        asl a
        clc
        adc $0C            ; area*10
        tax
        ldy #0
@l:     lda AREAS,x
        sta $0101,y
        inx
        iny
        cpy #10
        bcc @l
        rts
AREAS:  .res 5*10, $72     ; filled by knt_build.py
