import sys
from capstone import Cs, CS_ARCH_MIPS, CS_MODE_MIPS32, CS_MODE_LITTLE_ENDIAN
EXE = 'files/SLPS_021.72'
d = open(EXE, 'rb').read()
md = Cs(CS_ARCH_MIPS, CS_MODE_MIPS32 + CS_MODE_LITTLE_ENDIAN)
def off(a): return a - 0x80010000 + 0x800
def dis(a, n):
    out = []
    for k in range(n):
        x = a + 4 * k
        ins = list(md.disasm(d[off(x):off(x) + 4], x))
        out.append('%08x  %s' % (x, ('%s %s' % (ins[0].mnemonic, ins[0].op_str)) if ins else '.word 0x%08x' % int.from_bytes(d[off(x):off(x)+4], 'little')))
    return out
if __name__ == '__main__':
    print('\n'.join(dis(int(sys.argv[1], 16), int(sys.argv[2]))))
