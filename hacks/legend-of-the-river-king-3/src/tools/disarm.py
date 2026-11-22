"""Disassemble GBA ROM code: python3 dis.py ROM ADDR LEN [arm]"""
import sys
from capstone import Cs, CS_ARCH_ARM, CS_MODE_THUMB, CS_MODE_ARM
def dis(rom, addr, n, arm=False):
    md = Cs(CS_ARCH_ARM, CS_MODE_ARM if arm else CS_MODE_THUMB)
    off = addr & 0x1ffffff
    for i in md.disasm(rom[off:off+n], addr):
        print('%08X: %-8s %s' % (i.address, i.mnemonic, i.op_str))
if __name__ == '__main__':
    rom = open(sys.argv[1], 'rb').read()
    dis(rom, int(sys.argv[2], 16), int(sys.argv[3], 16), len(sys.argv) > 4)
