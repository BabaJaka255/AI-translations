"""All references from code (lui+addiu/ori/load-store) and data (dwords) into the text regions."""
import struct, sys
sys.path.insert(0, 'tools')
from strings import *
CODE_END = 0xb47c8
DATA_END = 0x4400    # rodata (pointer tables) before the first function
def refs(d, regions=None):
    lo_rg = [(BASE + a, BASE + b) for a, b in (regions or REGIONS)]
    def inrg(v): return any(a <= v <= b for a, b in lo_rg)
    out = []  # (kind, file offsets..., value)
    lui = {}
    for i in range(0x800, CODE_END, 4):
        ins = struct.unpack_from('<I', d, i)[0]
        op = ins >> 26; rs = (ins >> 21) & 31; rt = (ins >> 16) & 31; imm = ins & 0xffff
        if op == 0x0f: lui[rt] = (imm << 16, i); continue
        if op in (0x09, 0x0d, 0x23, 0x21, 0x25, 0x2b, 0x29, 0x28, 0x20, 0x24) and rs in lui and i - lui[rs][1] < 0x80:
            s = imm - 0x10000 if (imm & 0x8000 and op != 0x0d) else imm
            v = (lui[rs][0] + s) & 0xffffffff
            if inrg(v): out.append(('code', lui[rs][1], i, op, v))
        # jumps/branches end a basic block: forget lui (conservative)
        if op in (2, 3) or (op == 0 and (ins & 0x3f) in (8, 9)): pass
    for i in range(0, len(d) - 3, 4):
        if DATA_END <= i < CODE_END: continue
        v = struct.unpack_from('<I', d, i)[0]
        if inrg(v): out.append(('data', i, None, None, v))
    return out
if __name__ == '__main__':
    d = open(EXE, 'rb').read()
    st = set(BASE + s for s in starts(d))
    R = refs(d)
    ns = [r for r in R if r[4] not in st]
    print('refs', len(R), 'non-start', len(ns))
    for r in ns[:60]: print(r[0], hex(r[1] + BASE), hex(r[4]), hex(r[4] - BASE))
