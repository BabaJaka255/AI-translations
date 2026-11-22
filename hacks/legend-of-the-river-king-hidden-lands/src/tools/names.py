"""Name entry: letters typed one after another are packed two per word (the engine's letter-pair
words), so the 4-word name buffer holds up to 8 letters. Rewrites the -O0 append block at
0x8006A6CC (brother/father table) / 0x8006A728 (sister/mother table) in place."""
import hook
START, FEMALE, END = 0x8006a6cc, 0x8006a728, 0x8006a7b8
ENG = hook.ENG_BASE
CAP = 0x8006a67c                      # sltiu $v1, $v0, 4 (word count before appending)
DELETES = (0x8006a404, 0x8006a818)    # 15-word "count -= 1; buf[count] = 0xffff" blocks
DELETE = """
        lui $t1, 0x8011
        lw $t4, -0x7638($t1)
        nop
        sll $t6, $t4, 1
        addu $t6, $t6, $fp
        lh $t7, 0x1e($t6)
        ori $t9, $zero, 0xffff
        slti $t8, $t7, 0x2000
        bnez $t8, del
        andi $t7, $t7, 0xff
        b store
        addiu $t9, $t7, %d          # back to a lone letter glyph (ENG + c - 0x21), so it can pair again
del:    addiu $t4, $t4, -1
        sw $t4, -0x7638($t1)
store:  sh $t9, 0x1e($t6)
""" % (ENG - 0x21)

def patch():
    src = f'''
        lui $t0, 0x800d
        b common
        addiu $t0, $t0, -0x420
''' + '        nop\n' * ((FEMALE - START) // 4 - 3) + f'''
        lui $t0, 0x800d
        addiu $t0, $t0, -0x340
common:
        lui $t1, 0x8011
        lw $t2, -0x762c($t1)
        lw $t4, -0x7638($t1)
        sll $t2, $t2, 1
        addu $t0, $t0, $t2
        lhu $t3, 0($t0)
        addiu $t5, $fp, 0x20
        sll $t6, $t4, 1
        beqz $t4, append
        addu $t6, $t5, $t6
        lhu $t7, -2($t6)
        addiu $t9, $t3, -{ENG}
        addiu $t8, $t7, -{ENG}
        sltiu $t8, $t8, 94
        beqz $t8, append
        sltiu $t9, $t9, 94
        beqz $t9, append
        addiu $t7, $t7, -{ENG - 0x21}
        addiu $t3, $t3, -{ENG - 0x21}
        sll $t3, $t3, 8
        or $t7, $t7, $t3
        j {END:#x}
        sh $t7, -2($t6)
append:
        sltiu $t8, $t4, 4              # a 5th word only ever holds the end mark
        beqz $t8, full
        nop
        sh $t3, 0($t6)
        addiu $t4, $t4, 1
        sw $t4, -0x7638($t1)
        ori $t7, $zero, 0xffff
        j {END:#x}
        sh $t7, 2($t6)
full:
        j {END:#x}
        nop
'''
    blob = hook.asm(src, START)
    assert START + len(blob) <= END, hex(START + len(blob))
    out = {START: blob}
    # the caller only lets a letter through while fewer than 4 words are used; let it through at 4 too,
    # so an 8th letter can join the 7th in the last word (the append above refuses a 5th word)
    out[CAP] = hook.asm('sltiu $v1, $v0, 5', CAP)
    # delete (X button and the "<" key): take one letter off a letter pair instead of the whole word
    for a in DELETES:
        b = hook.asm(DELETE, a); assert len(b) <= 60, len(b); out[a] = b
    out.update(postcard())
    return out

# postcard writing: the three "store the picked glyph" sites jump to a merge routine placed in the
# dead stretch of the old glyph path (0x800201A4-0x800201F0)
PC_MERGE = 0x800201a4
PC_SITES = (0x80075698, 0x80075700, 0x80075774)
PC_STORE, PC_NEXT = 0x8007577c, 0x8007578c

def postcard():
    src = f'''
        lbu $t0, 0($s4)
        beqz $t0, plain
        addiu $t2, $v0, -{ENG}
        lhu $t1, -2($a0)
        sltiu $t2, $t2, 94
        beqz $t2, plain
        addiu $t3, $t1, -{ENG}
        sltiu $t3, $t3, 94
        beqz $t3, plain
        addiu $t1, $t1, -{ENG - 0x21}
        addiu $t2, $v0, -{ENG - 0x21}
        sll $t2, $t2, 8
        or $t1, $t1, $t2
        j {PC_NEXT:#x}
        sh $t1, -2($a0)
plain:
        j {PC_STORE:#x}
        sh $v0, 0($a0)
'''
    blob = hook.asm(src, PC_MERGE)
    assert PC_MERGE + len(blob) <= 0x800201f0, hex(PC_MERGE + len(blob))
    out = {PC_MERGE: blob}
    for a in PC_SITES:
        out[a] = hook.asm(f'j {PC_MERGE:#x}\nnop', a)
    return out

if __name__ == '__main__':
    b = patch()[START]; print(len(b), hex(START + len(b)))
