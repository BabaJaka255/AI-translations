"""English text engine for the main executable (MIPS, assembled with keystone).

* The mode-0 half of the glyph drawer (0x8002027C) is rewritten compactly; the freed space holds
  draw_word / putc and the width table. The mode-0 sprite ring now wraps at 240 instead of 140.
* The three glyph call sites of the text printer (main, FFFA inserts, FFF7 names) call draw_word,
  which handles: glyph < 0x500 (original), ENG_BASE.. (one English letter, used by names),
  0x1Fcc (one letter), 0x2020-0x7F7F (two letters, low byte first), 0x8000+ (dictionary entry).
"""
from keystone import Ks, KS_ARCH_MIPS, KS_MODE_MIPS32, KS_MODE_LITTLE_ENDIAN
ks = Ks(KS_ARCH_MIPS, KS_MODE_MIPS32 + KS_MODE_LITTLE_ENDIAN)
ENG_BASE = 177
SPACE_W = 4
DRAWER = 0x80020220
SOUND = 0x800766dc
SPRITE_SHOW = 0x8001dbf0
CODE = 0x8002027c
CODE_END = 0x800204f8
DATA = 0x80020140

def hi(a): return ((a + 0x8000) >> 16) & 0xffff
def lo(a): return a & 0xffff if a & 0xffff < 0x8000 else (a & 0xffff) - 0x10000

def asm(src, addr):
    enc, _ = ks.asm('.set noreorder\n' + src, addr)
    return bytes(enc)

def engine(widths, dict_ptr):
    """Return {addr: bytes} patches. widths: 94 bytes for 0x21-0x7E. dict_ptr: address of the u32 pointer table."""
    # pass 1 to find label addresses: assemble twice
    def src(wt, attr):
        return f'''
        lui $t0, 0x8011
        lbu $t1, -0x74a0($t0)
        sll $t2, $t1, 3
        addu $t2, $t2, $t1
        sll $t2, $t2, 2
        addiu $a0, $t0, -0x3c54
        addu $a0, $a0, $t2
        lbu $v0, 0x11($fp)
        sh $v0, 4($a0)
        lbu $v0, 0x12($fp)
        sh $v0, 6($a0)
        ori $v0, $zero, 0x10
        sh $v0, 8($a0)
        sh $v0, 10($a0)
        lhu $v1, 0x14($fp)
        srl $v0, $v1, 8
        addiu $v0, $v0, 0x1b
        sh $v0, 12($a0)
        andi $v0, $v1, 0xf
        sll $v0, $v0, 4
        sb $v0, 14($a0)
        andi $v0, $v1, 0xf0
        sb $v0, 15($a0)
        lbu $v0, -0x7902($t0)
        jal {SPRITE_SHOW:#x}
        sh $v0, 0x10($a0)
        lui $t0, 0x8011
        lbu $t1, -0x74a0($t0)
        addiu $t1, $t1, 1
        sltiu $t2, $t1, 0xf0
        bnez $t2, ring_ok
        nop
        move $t1, $zero
ring_ok:
        sb $t1, -0x74a0($t0)
        j 0x80020a50
        nop

draw_word:
        addiu $sp, $sp, -0x28
        sw $ra, 0x20($sp)
        sw $s0, 0x1c($sp)
        sw $s1, 0x18($sp)
        lhu $s0, 0x2c($fp)
        lui $t3, 0x8002
        lw $t4, 0x1a4($t3)
        addiu $t4, $t4, 4
        andi $t4, $t4, 0x3c
        sw $t4, 0x1a4($t3)
        addu $t4, $t4, $t3
        lhu $t5, 0x28($fp)
        sh $t5, 0x1a8($t4)
        lbu $t1, 0x1b($fp)
        lui $t0, {hi(attr)}
        sb $t1, {lo(attr)}($t0)
        lui $t0, 0x8011
        lbu $t0, -0x78e8($t0)
        beqz $t0, no_sound
        nop
        jal {SOUND:#x}
        ori $a0, $zero, 0x10
no_sound:
        sltiu $t0, $s0, 0x500
        beqz $t0, big
        addiu $t1, $s0, -{ENG_BASE}
        sltiu $t2, $t1, 94
        beqz $t2, orig
        nop
        bal putc
        addiu $a0, $t1, 0x21
        b done
        nop
orig:
        lbu $a0, 0x18($fp)
        lbu $a1, 0x28($fp)
        lbu $a2, 0x2a($fp)
        move $a3, $s0
        lbu $t1, 0x1b($fp)
        jal {DRAWER:#x}
        sw $t1, 0x10($sp)
        sltiu $t0, $s0, 0x16
        beqz $t0, wide
        ori $t1, $zero, 16
        ori $t1, $zero, 8
wide:
        lhu $t2, 0x28($fp)
        lui $t3, 0x8002
        lw $t4, 0x1a4($t3)
        addu $t4, $t4, $t3
        sh $t2, 0x1aa($t4)
        addu $t2, $t2, $t1
        b done
        sh $t2, 0x28($fp)
big:
        srl $t0, $s0, 8
        ori $t1, $zero, 0x1f
        beq $t0, $t1, single
        srl $t1, $s0, 15
        bnez $t1, dict
        nop
        bal putc
        andi $a0, $s0, 0xff
        bal putc
        srl $a0, $s0, 8
        b done
        nop
single:
        bal putc
        andi $a0, $s0, 0xff
        b done
        nop
dict:
        addiu $t0, $s0, -0x8000
        sll $t0, $t0, 2
        lui $t1, {hi(dict_ptr)}
        addu $t1, $t1, $t0
        lw $s1, {lo(dict_ptr)}($t1)
dloop:
        lbu $a0, 0($s1)
        beqz $a0, done
        nop
        bal putc
        addiu $s1, $s1, 1
        b dloop
        nop
done:
        lw $ra, 0x20($sp)
        lw $s0, 0x1c($sp)
        lw $s1, 0x18($sp)
        jr $ra
        addiu $sp, $sp, 0x28

putc:
        addiu $sp, $sp, -0x28
        sw $ra, 0x20($sp)
        sw $s0, 0x1c($sp)
        ori $t0, $zero, 0x20
        bne $a0, $t0, notspace
        addiu $s0, $a0, -0x21
        lhu $t1, 0x28($fp)
        addiu $t1, $t1, {SPACE_W}
        b pret
        sh $t1, 0x28($fp)
notspace:
        lbu $a0, 0x18($fp)
        lbu $a1, 0x28($fp)
        lbu $a2, 0x2a($fp)
        addiu $a3, $s0, {ENG_BASE}
        lui $t0, {hi(attr)}
        lbu $t1, {lo(attr)}($t0)
        sb $zero, {lo(attr)}($t0)
        jal {DRAWER:#x}
        sw $t1, 0x10($sp)
        lui $t0, {hi(wt)}
        addu $t0, $t0, $s0
        lbu $t1, {lo(wt)}($t0)
        lhu $t2, 0x28($fp)
        addu $t2, $t2, $t1
        sh $t2, 0x28($fp)
pret:
        lw $ra, 0x20($sp)
        lw $s0, 0x1c($sp)
        jr $ra
        addiu $sp, $sp, 0x28
code_end:
'''
    attr = DATA                    # free space left in the old main glyph path
    wt = attr + 4
    code = asm(src(wt, attr), CODE)
    blob = code
    assert CODE + len(blob) <= CODE_END, hex(CODE + len(blob))
    assert wt + 94 <= 0x800201f0
    # find draw_word address: assemble prefix up to the label
    s = src(wt, attr)
    dw = CODE + len(asm(s.split('draw_word:')[0], CODE))
    patches = {CODE: blob, DATA: bytes(4) + bytes(widths)}
    patches[0x80020124] = asm(f'jal {dw:#x}\nnop\nj 0x800201f0\nnop', 0x80020124)
    patches[0x8001fa00] = asm(f'jal {dw:#x}\nnop\nj 0x8001fac4\nnop', 0x8001fa00)
    patches[0x8001fcbc] = asm(f'jal {dw:#x}\nnop\nj 0x8001fcf8\nnop', 0x8001fcbc)
    return patches, dw, CODE + len(blob)

if __name__ == '__main__':
    p, dw, end = engine([6] * 94, 0x80100000)
    print(hex(dw), hex(end), 'free', CODE_END - end)
