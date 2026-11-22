"""Analysis-only copy of an EE ELF: replace R5900-only opcodes (MMI 0x1c, LQ 0x1e, SQ 0x1f) with NOPs so stock Ghidra MIPS decodes it. Never use the output in a build."""
import sys,struct
d=bytearray(open(sys.argv[1],'rb').read()); n=0
for o in range(0x1000,len(d)-3,4):
    w=struct.unpack_from('<I',d,o)[0]
    if w>>26 in (0x1c,0x1e,0x1f): d[o:o+4]=b'\0\0\0\0'; n+=1
open(sys.argv[2],'wb').write(d); print(n,'words cleared')
