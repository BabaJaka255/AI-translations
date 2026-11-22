"""Thumb-1 assembly helper (keystone) that refuses 32-bit Thumb-2 encodings except BL."""
from keystone import Ks, KS_ARCH_ARM, KS_MODE_THUMB
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB

_ks = Ks(KS_ARCH_ARM, KS_MODE_THUMB)
_cs = Cs(CS_ARCH_ARM, CS_MODE_THUMB)


def thumb(src, addr):
    enc, _ = _ks.asm(src, addr)
    code = bytes(enc)
    # verify: every instruction 2 bytes except bl
    a = 0
    lines = [l.split(';')[0].strip() for l in src.replace(';', '\n').split('\n')]
    for ins in _cs.disasm(code, addr):
        if ins.size == 4 and ins.mnemonic not in ('bl',):
            # literal pool words may decode as 32-bit instructions; only check before first pool
            raise ValueError('Thumb-2 instruction emitted: %s %s at %x' % (ins.mnemonic, ins.op_str, ins.address))
        if ins.mnemonic in ('b', 'bx') and False:
            pass
    return code


def check(code, addr, upto):
    """Check 32-bit encodings only within [addr, upto) (code part, before literal pools)."""
    for ins in _cs.disasm(code[:upto - addr], addr):
        if ins.size == 4 and ins.mnemonic != 'bl':
            raise ValueError('Thumb-2 instruction: %s %s at %x' % (ins.mnemonic, ins.op_str, ins.address))
