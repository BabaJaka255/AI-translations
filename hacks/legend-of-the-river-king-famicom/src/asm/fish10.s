; Kawa no Nushi Tsuri (FC) English catch messages, bank 10, free space at $BD65.
;
; Japanese printed "<fish name><D0>" and the D0 code continued with one of three
; suffixes picked by $074A (D1 got away, D2 landed, D3 let go).  English needs the
; name inside the sentence, so each fish has three whole lines in the text banks
; and this routine (called instead of $A151 at $A8F4) points $12/$13 at the right one.
.segment "FISH"
FISHPTR:
        jsr $C02E          ; X = fish number (area*12 + kind)
        stx $0C
        txa
        asl a
        adc $0C            ; *3 (carry is clear: X < 60)
        sta $0C
        lda $074A
        sec
        sbc #$D1           ; 0 got away, 1 landed, 2 let go
        clc
        adc $0C
        tax
        lda FHI,x
        sta $13
        lda FLO,x
        sta $12
        rts
FLO:    .res 59*3, $FF     ; filled by knt_build.py
FHI:    .res 59*3, $FF
