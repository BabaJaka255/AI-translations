"""Test helpers: a compact rewrite of the secret-name gift, and a Select+step area warp that lives in the space it frees.

The secret name (string 59, "FishTaro", originally つり太郎) given to Taro (record 0) at name entry calls GIFT,
which fills the record with rods, lures, flies, gear and items. The original is ~8.8 KB of unrolled stores; here it
is a table walk with the same stores in the same order.

Area warp: after every step the field loop reads the travel byte 0x80108702 (set by trigger tiles) and, if it is
non-zero, leaves the field for main state 13, the game's own travel scene. The hook replaces that read: if Select is
held (game pad word 0x80108840 & 0x100) it first sets the byte to the travel entry for the next area (Select+L1:
the previous one), then returns the byte as before."""
import struct, sys
sys.path.insert(0, 'tools')
from hook import asm

T = 0x8000f800
EXE = 'files/SLPS_015.36'
GIFT, GIFT_END = 0x8006b068, 0x8006d2f4
# field loop, after each step: lui $v0,0x8011 / lbu $v0,-0x78fe($v0), then bnez -> main state 13 (travel)
TRAVEL_CHECKS = (0x8002e3e4, 0x8002e4dc)
# travel entries (0x80108702 values) for areas 1..7: Stream, Alpine, Creek, Lake, Plains, Coast, Secret
DESTS = [2, 1, 3, 5, 7, 9, 11]


def gift_stores(d):
    """(size, record offset from 0x80170000, value) in the original order; the 60-byte loop expanded in place."""
    from capstone import Cs, CS_ARCH_MIPS, CS_MODE_MIPS32, CS_MODE_LITTLE_ENDIAN
    md = Cs(CS_ARCH_MIPS, CS_MODE_MIPS32 + CS_MODE_LITTLE_ENDIAN)
    out, v = [], None
    for i in md.disasm(d[GIFT - T:GIFT_END - T], GIFT):
        m, o = i.mnemonic, i.op_str
        if m == 'ori' and o.startswith('$v1, $zero'): v = int(o.split(',')[-1], 16)
        elif m in ('sb', 'sh') and '($at)' in o:
            assert o.startswith(('$zero', '$v1')), o
            out.append((m, int(o.split(',')[1].split('(')[0], 16), 0 if o.startswith('$zero') else v))
        elif i.address == 0x8006ccd0:            # for i in 0..59: rec[0x63a7 + i] = i + 1
            out += [('sb', 0x63a7 + k, k + 1) for k in range(60)]
    return out


def patch():
    d = open(EXE, 'rb').read()
    st = gift_stores(d)
    assert len(st) == 205 and st[0] == ('sh', 0x6362, 0x64) and all(m == 'sb' for m, _, _ in st[1:]), st[:3]
    table = b''.join(struct.pack('<HBB', off, val, 0) for _, off, val in st[1:]) + b'\0\0\0\0'
    gift = """
        lui $t0, 0x8011
        lbu $t1, -0x7900($t0)
        ori $t3, $zero, 1410
        multu $t1, $t3
        mflo $t2
        lui $t3, 0x8017
        addu $t2, $t2, $t3
        ori $t3, $zero, 0x64
        sh $t3, 0x6362($t2)
        lui $t4, %d
        addiu $t4, $t4, %d
g_loop: lhu $t5, 0($t4)
        lbu $t6, 2($t4)
        beqz $t5, g_done
        addu $t7, $t2, $t5
        sb $t6, 0($t7)
        b g_loop
        addiu $t4, $t4, 4
g_done: jr $ra
        nop
    """
    code_len = len(asm(gift % (0, 0), GIFT))
    tab_addr = GIFT + code_len
    hi, lo = (tab_addr + 0x8000) >> 16, tab_addr & 0xffff
    lo = lo - 0x10000 if lo & 0x8000 else lo
    gift_bin = asm(gift % (hi, lo), GIFT) + table
    warp = (GIFT + len(gift_bin) + 3) & ~3
    dests = warp + 0x100
    dh, dl = (dests + 0x8000) >> 16, dests & 0xffff
    dl = dl - 0x10000 if dl & 0x8000 else dl
    warp_src = """
        lui $at, 0x8011
        lhu $t0, -0x77c0($at)
        nop
        andi $t1, $t0, 0x100
        beqz $t1, w_done
        nop
        lbu $t1, -0x7900($at)
        ori $t3, $zero, 1410
        multu $t1, $t3
        mflo $t2
        lui $t3, 0x8017
        addu $t2, $t2, $t3
        lbu $t1, 0x6348($t2)
        andi $t0, $t0, 4
        beqz $t0, w_next
        nop
        addiu $t1, $t1, -2
        bgez $t1, w_pick
        nop
        b w_pick
        ori $t1, $zero, 6
w_next: slti $t3, $t1, 7
        bnez $t3, w_pick
        nop
        move $t1, $zero
w_pick: lui $t3, %d
        addiu $t3, $t3, %d
        addu $t3, $t3, $t1
        lbu $t1, 0($t3)
        nop
        sb $t1, -0x78fe($at)
w_done: jr $ra
        lbu $v0, -0x78fe($at)
    """ % (dh, dl)
    warp_bin = asm(warp_src, warp)
    assert len(warp_bin) <= 0x100
    blob = gift_bin.ljust(warp - GIFT, b'\0') + warp_bin.ljust(0x100, b'\0') + bytes(DESTS)
    assert GIFT + len(blob) <= GIFT_END, hex(GIFT + len(blob))
    blob = blob.ljust(GIFT_END - GIFT, b'\0')
    out = {GIFT: blob}
    for a in TRAVEL_CHECKS: out[a] = asm('jal 0x%x\nnop' % warp, a)
    return out
