import struct,json
r=open('../rom/k34.gba','rb').read()
TT=[struct.unpack_from('<I',r,0xed88+4*i)[0]-0x08000000 for i in range(17)]
def table(n):
    s=TT[n]; e=TT[n+1] if n<16 else 0xfa20
    return [struct.unpack_from('<I',r,o)[0]-0x08000000 for o in range(s,e,4)]
