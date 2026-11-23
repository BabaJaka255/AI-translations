"""English text engine for Umi no Nushi Tsuri (PS1). Assembled with keystone.

draw_word(a0 window, a1 word, a2 attr, a3 line-start x) is called from msg()'s three glyph sites
(main text, FFFA inserts, FFF7 names). It reads/updates the caller's x in $s3 and y in $s7.
Word types: < ENG_BASE original glyph; ENG_BASE+k English cell k (a 16 px glyph holding 1-4 letters,
advance from the width table; cell 0 is a space and draws nothing); 0x1Ecc tab (x = line start + cc);
0x8000+k dictionary entry k (cell words ending in 0, via a pointer table).
"""
import re
from keystone import Ks, KS_ARCH_MIPS, KS_MODE_MIPS32, KS_MODE_LITTLE_ENDIAN
ks = Ks(KS_ARCH_MIPS, KS_MODE_MIPS32 + KS_MODE_LITTLE_ENDIAN)
ENG_BASE = 196
SPACE_W = 4
DRAWER = 0x80019328
LOOP = 0x80018b68

def hi(a): return ((a + 0x8000) >> 16) & 0xffff
def lo(a): return a & 0xffff if a & 0xffff < 0x8000 else (a & 0xffff) - 0x10000
LOADS = ('lb', 'lbu', 'lh', 'lhu', 'lw')

def fix_load_delay(src):
    lines = src.split('\n'); out = []
    for i, ln in enumerate(lines):
        out.append(ln)
        p = ln.split()
        if not p or p[0] not in LOADS: continue
        reg = p[1].rstrip(',')
        for nxt in lines[i + 1:]:
            q = nxt.strip()
            if not q or q.endswith(':'): continue
            ops = q.split(None, 1)[1] if ' ' in q else ''
            if re.search(re.escape(reg) + r'\b', ops): out.append('        nop')
            break
    return '\n'.join(out)

def asm(src, addr):
    enc, _ = ks.asm('.set noreorder\n' + fix_load_delay(src), addr)
    return bytes(enc)

def measure_src(wt, dict_ptr, asct):
    """measure: a0 = word string (ends at any word >= 0xFFF0) -> v0 = drawn width in px. Uses t0-t7 only."""
    n = [0]
    def lab():
        n[0] += 1; return 'mL%d' % n[0]
    def asc(r):
        sp, dn = lab(), lab()
        return f"""        addiu ${r}, ${r}, -0x21
        sltiu $t6, ${r}, 94
        beqz $t6, {sp}
        sll $t6, ${r}, 1
        lui $t7, {hi(asct)}
        addu $t7, $t7, $t6
        lhu ${r}, {lo(asct)}($t7)
        b {dn}
        nop
{sp}:
        ori ${r}, $zero, {ENG_BASE}
{dn}:
"""
    def cw(r):
        nz, dn = lab(), lab()
        return f"""        addiu $t6, ${r}, -{ENG_BASE}
        bnez $t6, {nz}
        lui $t7, {hi(wt)}
        b {dn}
        addiu $v0, $v0, {SPACE_W}
{nz}:
        addu $t7, $t7, $t6
        lbu $t6, {lo(wt)}($t7)
        addu $v0, $v0, $t6
{dn}:
"""
    return f"""
measure:
        move $v0, $zero
m_loop:
        lhu $t0, 0($a0)
        ori $t2, $zero, 0xfff0
        sltu $t1, $t0, $t2
        beqz $t1, m_end
        addiu $a0, $a0, 2
        srl $t1, $t0, 15
        bnez $t1, m_dict
        srl $t1, $t0, 8
        ori $t2, $zero, 0x1e
        beq $t1, $t2, m_loop
        ori $t2, $zero, 0x1f
        beq $t1, $t2, m_single
        sltiu $t2, $t1, 0x20
        beqz $t2, m_pair
        sltiu $t2, $t0, {ENG_BASE}
        beqz $t2, m_cell
        sltiu $t2, $t0, 0x16
        bnez $t2, m_loop
        addiu $v0, $v0, 8
        b m_loop
        addiu $v0, $v0, 8
m_cell:
{cw('t0')}        b m_loop
        nop
m_single:
        andi $t5, $t0, 0xff
{asc('t5')}{cw('t5')}        b m_loop
        nop
m_pair:
        andi $t5, $t0, 0xff
{asc('t5')}{cw('t5')}        srl $t5, $t0, 8
{asc('t5')}{cw('t5')}        b m_loop
        nop
m_dict:
        addiu $t3, $t0, -0x8000
        sll $t3, $t3, 2
        lui $t4, {hi(dict_ptr)}
        addu $t4, $t4, $t3
        lw $t4, {lo(dict_ptr)}($t4)
m_dl:
        lhu $t5, 0($t4)
        beqz $t5, m_loop
        addiu $t4, $t4, 2
{cw('t5')}        b m_dl
        nop
m_end:
        jr $ra
        nop
"""

def source(wt, dict_ptr, asct):
    return f'''
draw_word:
        addiu $sp, $sp, -0x30
        sw $ra, 0x28($sp)
        sw $s0, 0x24($sp)
        sw $s1, 0x20($sp)
        sw $s2, 0x1c($sp)
        sw $s4, 0x18($sp)
        move $s2, $a0
        sw $a2, 0x10($sp)
        move $s4, $a3
        andi $s0, $a1, 0xffff
        srl $t0, $s0, 15
        bnez $t0, dict
        srl $t0, $s0, 8
        ori $t1, $zero, 0x1e
        beq $t0, $t1, tab
        ori $t1, $zero, 0x1f
        beq $t0, $t1, single
        sltiu $t1, $t0, 0x20
        beqz $t1, pair
        sltiu $t0, $s0, {ENG_BASE}
        bnez $t0, orig
        nop
        bal cell
        move $a0, $s0
        b done
        nop
orig:
        move $a0, $s2
        andi $a1, $s3, 0xff
        andi $a2, $s7, 0xff
        jal {DRAWER:#x}
        move $a3, $s0
        sltiu $t0, $s0, 0x16
        beqz $t0, wide
        ori $t1, $zero, 16
        ori $t1, $zero, 8
wide:
        b done
        addu $s3, $s3, $t1
single:
        bal asc
        andi $a0, $s0, 0xff
        b done
        nop
pair:
        bal asc
        andi $a0, $s0, 0xff
        bal asc
        srl $a0, $s0, 8
        b done
        nop
tab:
        andi $t3, $s0, 0xff
        b done
        addu $s3, $s4, $t3
dict:
        addiu $t0, $s0, -0x8000
        sll $t0, $t0, 2
        lui $t1, {hi(dict_ptr)}
        addu $t1, $t1, $t0
        lw $s1, {lo(dict_ptr)}($t1)
dloop:
        lhu $a0, 0($s1)
        beqz $a0, done
        nop
        bal cell
        addiu $s1, $s1, 2
        b dloop
        nop
done:
        lw $ra, 0x28($sp)
        lw $s0, 0x24($sp)
        lw $s1, 0x20($sp)
        lw $s2, 0x1c($sp)
        lw $s4, 0x18($sp)
        jr $ra
        addiu $sp, $sp, 0x30

asc:
        addiu $a0, $a0, -0x21
        sltiu $t0, $a0, 94
        beqz $t0, asc_sp
        sll $t0, $a0, 1
        lui $t1, {hi(asct)}
        addu $t1, $t1, $t0
        b cell
        lhu $a0, {lo(asct)}($t1)
asc_sp:
        ori $a0, $zero, {ENG_BASE}
cell:
        addiu $sp, $sp, -0x28
        sw $ra, 0x20($sp)
        sw $s0, 0x1c($sp)
        addiu $s0, $a0, -{ENG_BASE}
        bnez $s0, notspace
        nop
        b pret
        addiu $s3, $s3, {SPACE_W}
notspace:
        lw $t1, 0x38($sp)
        move $a3, $a0
        move $a0, $s2
        andi $a1, $s3, 0xff
        andi $a2, $s7, 0xff
        jal {DRAWER:#x}
        sw $t1, 0x10($sp)
        lui $t0, {hi(wt)}
        addu $t0, $t0, $s0
        lbu $t1, {lo(wt)}($t0)
        nop
        addu $s3, $s3, $t1
pret:
        lw $ra, 0x20($sp)
        lw $s0, 0x1c($sp)
        jr $ra
        addiu $sp, $sp, 0x28

name_add:
        lui $t0, 0x8010
        lw $t1, 0x2ef4($t0)
        beqz $t1, na_app
        sll $t2, $t1, 1
        addu $t2, $t2, $a0
        lhu $t3, -2($t2)
        ori $t5, $zero, 0x1f
        srl $t4, $t3, 8
        bne $t4, $t5, na_app
        srl $t4, $a1, 8
        bne $t4, $t5, na_app
        andi $t3, $t3, 0xff
        andi $t4, $a1, 0xff
        sll $t4, $t4, 8
        or $t3, $t3, $t4
        jr $ra
        sh $t3, -2($t2)
na_app:
        sltiu $t3, $t1, 4
        beqz $t3, na_ret
        sll $t2, $t1, 1
        addu $t2, $t2, $a0
        sh $a1, 0($t2)
        addiu $t1, $t1, 1
        sw $t1, 0x2ef4($t0)
        ori $t3, $zero, 0xffff
        sh $t3, 2($t2)
na_ret:
        jr $ra
        nop

name_del:
        lui $t0, 0x8010
        lw $t1, 0x2ef4($t0)
        beqz $t1, nd_none
        sll $t2, $t1, 1
        addu $t2, $t2, $a0
        lhu $t3, -2($t2)
        srl $t4, $t3, 8
        sltiu $t5, $t4, 0x20
        bnez $t5, nd_plain
        sltiu $t5, $t4, 0x7f
        beqz $t5, nd_plain
        andi $t3, $t3, 0xff
        ori $t3, $t3, 0x1f00
        sh $t3, -2($t2)
        jr $ra
        ori $v0, $zero, 1
nd_plain:
        addiu $t1, $t1, -1
        sw $t1, 0x2ef4($t0)
        ori $t3, $zero, 0xffff
        sh $t3, -2($t2)
        jr $ra
        ori $v0, $zero, 1
nd_none:
        jr $ra
        move $v0, $zero
''' + measure_src(wt, dict_ptr, asct) + '''
board_x:
        lui $t0, 0x8015
        lb $t0, -0x1fdf($t0)
        sll $t1, $t0, 5
        sll $t2, $t0, 4
        addu $t1, $t1, $t2
        sll $t2, $t0, 3
        addu $t1, $t1, $t2
        sll $t2, $t0, 1
        addu $t1, $t1, $t2
        lui $a0, 0x8010
        addiu $a0, $a0, 0x3bc0
        addu $a0, $a0, $t1
        move $t9, $ra
        bgezal $zero, measure
        nop
        move $ra, $t9
        jr $ra
        addiu $v0, $v0, 0x10

board_w:
        lhu $t8, 0($a0)
        addiu $sp, $sp, -8
        sh $t8, 0($sp)
        ori $t8, $zero, 0xffff
        sh $t8, 2($sp)
        move $a0, $sp
        move $t9, $ra
        bgezal $zero, measure
        nop
        move $ra, $t9
        addiu $sp, $sp, 8
        jr $ra
        move $a0, $v0

board_fix:
        lui $t0, 0x8015
        sb $s0, -0x2017($t0)
        bgezal $zero, board_x
        nop
        addiu $v0, $v0, -0x10
        lui $t0, 0x8010
        sw $v0, 0x2e6c($t0)
        j 0x80089b5c
        nop

board_room:
        lui $v0, 0x8010
        lw $v0, 0x2e6c($v0)
        lui $t0, 0x8015
        lb $t0, -0x2017($t0)
        sltiu $v0, $v0, 0xd8
        sltiu $t0, $t0, 27
        jr $ra
        and $v0, $v0, $t0

board_p:
        lb $t0, 0($s1)
        nop
        addiu $t0, $t0, -2
        sltiu $t1, $t0, 4
        beqz $t1, bp_out
        ori $t2, $zero, 0x1f2c
        beqz $t0, bp_go
        addiu $t0, $t0, -1
        ori $t2, $zero, 0x1f2e
        beqz $t0, bp_go
        addiu $t0, $t0, -1
        ori $t2, $zero, 0x1f22
        beqz $t0, bp_go
        nop
        ori $t2, $zero, 0x1f3a
bp_go:
        lb $v1, 1($s2)
        nop
        sll $v0, $v1, 3
        subu $v0, $v0, $v1
        sll $v0, $v0, 2
        addu $v0, $v0, $v1
        sll $v0, $v0, 1
        addu $v0, $v0, $s6
        lb $v1, 1($s1)
        nop
        sll $v1, $v1, 1
        addu $v1, $v1, $v0
        sh $t2, 0($v1)
        lbu $v0, 1($s1)
        nop
        addiu $v0, $v0, 1
        sb $v0, 1($s1)
        bgezal $zero, board_w
        move $a0, $v1
        j 0x80089854
        nop
bp_out:
        j 0x800896f0
        nop

place_ptr:
        lw $v0, -0x2bd8($1)
        lui $t1, 0x800d
        ori $t1, $t1, 0x24
        bne $1, $t1, pp_out
        nop
        lui $t2, 0x8001
        lw $v0, 0x510($t2)
        nop
        addiu $v0, $v0, 2
pp_out:
        jr $ra
        lui $1, 0x8010
'''

def engine(code_addr, widths, dict_ptr, asc_cells):
    """Returns (patches {addr: bytes}, blob end). Blob = code, cell width table, ASCII->cell table (u16 x 94)."""
    import struct
    probe = asm(source(0x80100000, dict_ptr, 0x80100000), code_addr)
    wt = code_addr + len(probe)
    asct = (wt + len(widths) + 1) & ~1
    code = asm(source(wt, dict_ptr, asct), code_addr)
    assert len(code) == len(probe)
    blob = code + bytes(widths) + bytes(asct - wt - len(widths)) + struct.pack('<94H', *asc_cells)
    labels = {}
    for name in ('name_add', 'name_del', 'measure', 'board_x', 'board_w', 'board_fix', 'board_room', 'board_p', 'place_ptr'):
        labels[name] = code_addr + len(asm(source(wt, dict_ptr, asct).split(name + ':')[0], code_addr))
    dw = code_addr
    call = f'''lbu $a0, 0x28($sp)
andi $a1, $s1, 0xffff
lw $a2, 0x48($sp)
lbu $a3, 0x30($sp)
jal {dw:#x}
nop
'''
    P = {code_addr: blob}
    # 1. main text (0x800192b4..0x800192f0, 16 slots)
    P[0x800192b4] = asm(call + f'j {LOOP:#x}\nnop\n' + 'nop\n' * 8, 0x800192b4)
    # 2. FFFA insert loop body 0x80018e30..0x80018e64 (14 slots), continue at 0x80018e68
    P[0x80018e30] = asm(call + 'j 0x80018e68\nnop\n' + 'nop\n' * 6, 0x80018e30)
    # 3. FFF7 name loop body 0x80018fec..0x80019008 (8 slots); x advance in 0x80019034's delay slot removed
    P[0x80018fec] = asm(call + 'nop\nnop\n', 0x80018fec)
    P[0x80019034] = asm('nop', 0x80019034)
    # 4. name entry: append a key (pairs two letters into one word, 4 words = 8 letters) 0x8007e3ec..0x8007e4c0
    P[0x8007e3ec] = asm(f'''lui $v0, 0x8010
lw $v0, 0x2efc($v0)
lui $v1, 0x8010
lbu $v1, 0x2bcf($v1)
sll $v0, $v0, 1
addiu $a0, $zero, 1
lui $at, 0x800d
bne $v1, $a0, nmale
addu $at, $at, $v0
b ngot
lhu $a1, -0x10c6($at)
nmale:
lhu $a1, -0x11a6($at)
ngot:
jal {labels['name_add']:#x}
move $a0, $s1
j 0x8007e4c4
nop
''', 0x8007e3ec)
    assert 0x8007e3ec + len(P[0x8007e3ec]) <= 0x8007e4c4
    # 5. name entry: back key splits a letter pair before removing a word. 0x8007e4f4..0x8007e51c
    P[0x8007e4f4] = asm(f'''jal {labels['name_del']:#x}
move $a0, $s1
''' + '.word %#x\nnop\n' % (0x10400000 | (((0x8007e7f0 - 0x8007e500) >> 2) & 0xffff)) + 'nop\n' * 7, 0x8007e4f4)
    assert len(P[0x8007e4f4]) == 44
    # 6. name entry cursor: x = drawn width of the name (buffer at the caller's sp+0x18) + 12, not words * 16
    P[0x8007d254] = asm(f'''move $t8, $ra
jal {labels['measure']:#x}
addiu $a0, $sp, 0x18
move $ra, $t8
lui $v1, 0x8011
addiu $v1, $v1, 0x515e
addiu $t0, $zero, 0x22
sh $t0, 0($v1)
addiu $v0, $v0, 0xc
sh $v0, -2($v1)
''', 0x8007d254)
    assert len(P[0x8007d254]) == 40
    # 7. Fishing Note fish page: centre the fish name on x=128 by its drawn width (JP picked x from the word count)
    P[0x80087374] = asm(f'''lui $a0, 0x8010
jal {labels['measure']:#x}
lw $a0, 0x2f10($a0)
srl $v0, $v0, 1
ori $a1, $zero, 128
subu $a1, $a1, $v0
sw $zero, 0x10($sp)
addiu $a0, $zero, 0xa
lui $a3, 0x800d
addiu $a3, $a3, -0x1db4
jal 0x80018ab8
addiu $a2, $zero, 0x10
j 0x8008744c
nop
''', 0x80087374)
    assert 0x80087374 + len(P[0x80087374]) <= 0x8008744c
    # 8. shop menu box (Rod/Float/...): 8 px wider to the right, so the English columns fit
    P[0x8003e0a4] = asm('addiu $a1, $zero, 0x88', 0x8003e0a4)
    P[0x8003e0ac] = asm('addiu $a3, $zero, 0x68', 0x8003e0ac)
    # 9. message board pencil: x = drawn width of the current line + 16 (JP added 8/16 per word)
    P[0x8008a1e8] = asm(f'''jal {labels['board_x']:#x}
nop
nop
nop
sh $v0, 0($s0)
''', 0x8008a1e8)
    assert len(P[0x8008a1e8]) == 20
    # 10. message board: advance/retreat the pencil by the drawn width of the word, not 8/16
    P[0x80089840] = asm(f'''lbu $v0, 0($s3)
nop
addiu $v0, $v0, 1
jal {labels['board_w']:#x}
sb $v0, 0($s3)
''', 0x80089840)                      # falls into 0x80089854 jal 0x8008a264 with a0 = width
    P[0x80089174] = asm(f'''jal {labels['board_w']:#x}
move $a0, $v1
nop
nop
nop
nop
''', 0x80089174)                      # then 0x8008918c jal 0x8008a498 (backspace)
    # row 2 keys 3-6 (JP 、。゛゜) type , . " : instead
    P[0x80089630] = asm(f'''j {labels['board_p']:#x}
nop
''', 0x80089630)
    # ...and skip the JP dakuten/handakuten handlers for keys 5/6 so they reach that path
    P[0x80088dd4] = asm('j 0x80089414\nnop\n', 0x80088dd4)
    P[0x80088f00] = asm('j 0x80089414\nnop\n', 0x80088f00)
    # 11. rankings screen: columns moved left (rank 20, record 120, place 166), and "Treasure Isl." (string 76 minus its tab)
    #     in place of "Treasure Island" so the place column ends inside the board (x wraps at 256)
    for a in (0x8008b36c, 0x8008b5cc):
        P[a] = asm(f'jal {labels["place_ptr"]:#x}\nnop\n', a)
    P[0x8008b310] = asm('addiu $a1, $zero, 0x14', 0x8008b310)     # rank+name x (picture view)
    P[0x8008b570] = asm('addiu $a1, $zero, 0x14', 0x8008b570)     # rank+name x (list)
    P[0x8008b380] = asm('addiu $a1, $zero, 0x78', 0x8008b380)     # record+place x
    P[0x8008b5e0] = asm('addiu $a1, $zero, 0x78', 0x8008b5e0)
    # #12 fish shop / keep net sell list: size+price column (string 424) moved left so "yen" stays in the box
    for a in (0x80097818, 0x80097998, 0x80097b18, 0x80097c98):
        P[a] = asm('addiu $a1, $zero, 0x8c', a)
    # line-up rescan: 0x2e6c = drawn width of the previous line
    P[0x80089124] = asm(f'''j {labels['board_fix']:#x}
nop
nop
nop
''', 0x80089124)
    # full-line test: width < 216 AND fewer than 27 words (the JP maximum) (English letters are narrow; buffer is 29 words)
    P[0x8008941c] = asm(f'''jal {labels['board_room']:#x}
nop
nop
nop
''', 0x8008941c)
    import os
    if os.environ.get('NOBOARD'):
        for a in [a for a in P if 0x80088ac4 <= a < 0x8008b000]: del P[a]
    for a, b in P.items():
        if a != code_addr: assert len(b) % 4 == 0
    assert len(P[0x800192b4]) == 64 and len(P[0x80018e30]) == 56 and len(P[0x80018fec]) == 32
    return P, code_addr + len(blob)

if __name__ == '__main__':
    P, end = engine(0x800ce400, [6] * 872, 0x800ce800, [196] * 94)
    print({hex(a): len(b) for a, b in P.items()}, hex(end))
