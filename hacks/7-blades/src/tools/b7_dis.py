"""Disassemble an ELF (load vaddr 0x200000 at file 0x1000). usage: b7_dis.py elf vaddr count"""
import sys,capstone
elf,va,n=sys.argv[1],int(sys.argv[2],16),int(sys.argv[3])
d=open(elf,'rb').read(); off=va-0x200000+0x1000
md=capstone.Cs(capstone.CS_ARCH_MIPS,capstone.CS_MODE_MIPS64+capstone.CS_MODE_LITTLE_ENDIAN)
for i in range(n):
    w=d[off+4*i:off+4*i+4]; ins=list(md.disasm(w,va+4*i))
    print('%08x: %s'%(va+4*i, f'{ins[0].mnemonic} {ins[0].op_str}' if ins else w[::-1].hex()))
