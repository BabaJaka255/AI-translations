import sys, capstone
EXE = 'files/SLPS_015.36'
d = open(EXE, 'rb').read()
md = capstone.Cs(capstone.CS_ARCH_MIPS, capstone.CS_MODE_MIPS32 + capstone.CS_MODE_LITTLE_ENDIAN)
def dis(addr, n):
    off = addr - 0x80010000 + 0x800
    for ins in md.disasm(d[off:off + n * 4], addr):
        print(f'{ins.address:08x}  {ins.mnemonic:8s} {ins.op_str}')
if __name__ == '__main__':
    dis(int(sys.argv[1], 16), int(sys.argv[2], 0))
