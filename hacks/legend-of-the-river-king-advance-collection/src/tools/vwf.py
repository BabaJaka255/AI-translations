from keystone import *
from capstone import *
ks=Ks(KS_ARCH_ARM,KS_MODE_THUMB)
cs=Cs(CS_ARCH_ARM,CS_MODE_THUMB)

def vwf_src(st, var, widths, font, pad=0xee):
    # r0 = char code. st = text struct (col +0xf6, row +0xf7, W at +0x8f, tile base ptr at +0x9c)
    return f'''
    push {{r4-r7, lr}}
    ldr r7, lst
    ldr r6, lvar
    mov r4, r7
    adds r4, #0xf6
    ldrb r1, [r4]
    ldrb r2, [r4, #1]
    ldrb r3, [r6]
    adds r5, r3, #7
    lsrs r5, r5, #3
    cmp r5, r1
    beq ok1
    lsls r3, r1, #3
ok1:
    ldrb r5, [r6, #1]
    cmp r5, r2
    beq ok2
    lsls r3, r1, #3
    strb r2, [r6, #1]
ok2:
    cmp r0, #{pad}
    bne nopad
    adds r3, #7
    lsrs r3, r3, #3
    strb r3, [r4]
    lsls r3, r3, #3
    strb r3, [r6]
    pop {{r4-r7}}
    pop {{r0}}
    bx r0
nopad:
    ldr r5, lwid
    ldrb r5, [r5, r0]
    adds r5, r3, r5
    strb r5, [r6]
    adds r5, #7
    lsrs r5, r5, #3
    strb r5, [r4]
    mov r4, r7
    adds r4, #0x8f
    ldrb r4, [r4]
    muls r4, r2
    lsrs r1, r3, #3
    adds r4, r4, r1
    lsls r4, r4, #5
    mov r1, r7
    adds r1, #0x9c
    ldr r1, [r1]
    adds r4, r4, r1
    ldr r1, lfont
    lsls r2, r0, #5
    adds r1, r1, r2
    movs r2, #7
    ands r2, r3
    lsls r2, r2, #2
    movs r5, #32
    subs r5, r5, r2
    lsrs r6, r3, #3
    adds r6, #1
    ldr r0, lst
    adds r0, #0x8f
    ldrb r0, [r0]
    movs r3, #0
    cmp r6, r0
    bge nonx
    ldr r3, lbg
    lsls r3, r2
nonx:
    movs r7, #8
loop:
    ldr r0, [r1]
    cmp r3, #0
    beq skipn
    adds r6, r0, #0
    lsrs r6, r5
    orrs r6, r3
    str r6, [r4, #32]
skipn:
    cmp r2, #0
    beq plain
    lsls r0, r2
    ldr r6, [r4]
    orrs r0, r6
plain:
    str r0, [r4]
    adds r1, #4
    adds r4, #4
    subs r7, #1
    bne loop
    pop {{r4-r7}}
    pop {{r0}}
    bx r0
    .align 2
lst: .word {st:#x}
lvar: .word {var:#x}
lwid: .word {widths:#x}
lfont: .word {font:#x}
lbg: .word 0x11111111
'''

def assemble(src, addr):
    enc,_=ks.asm(src,addr)
    return bytes(enc)

def listing(code, addr):
    for i in cs.disasm(code, addr):
        print('%08x %d %s %s'%(i.address,i.size,i.mnemonic,i.op_str))

if __name__=='__main__':
    c=assemble(vwf_src(0x03000020,0x03006ff0,0x08300000,0x080d2220),0x08310000)
    listing(c,0x08310000)
