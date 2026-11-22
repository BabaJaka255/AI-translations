import sys as _s, os as _o; _d=_o.path.dirname(_o.path.abspath(__file__))
while not _o.path.exists(_o.path.join(_d,'build','paths.py')): _d=_o.path.dirname(_d)
_s.path.insert(0,_o.path.join(_d,'build')); _s.path.insert(0,_o.path.dirname(_o.path.abspath(__file__))); import paths as P
import sys
# compact 65816 disassembler. modes: i imp, a acc, M imm(m), X imm(x), 1 imm8, d dp, dx, dy, A abs, Ax, Ay, L long, Lx, (d), (d,x), (d),y, [d], [d],y, s, (s),y, r rel, R rel16, (A), (A,x), [A], b blk, P pea
ops={}
g1=["ORA","AND","EOR","ADC","STA","LDA","CMP","SBC"]
m1={0x01:'(d,x)',0x03:'s',0x05:'d',0x07:'[d]',0x09:'M',0x0D:'A',0x0F:'L',0x11:'(d),y',0x12:'(d)',0x13:'(s),y',0x15:'dx',0x17:'[d],y',0x19:'Ay',0x1D:'Ax',0x1F:'Lx'}
for i,n in enumerate(g1):
    for o,m in m1.items():
        if n=="STA" and m=='M': continue
        ops[i*0x20+o]=(n,m)
S={0x00:("BRK","1"),0x02:("COP","1"),0x08:("PHP","i"),0x0A:("ASL","a"),0x0B:("PHD","i"),0x18:("CLC","i"),0x1A:("INC","a"),0x1B:("TCS","i"),0x20:("JSR","A"),0x22:("JSL","L"),0x28:("PLP","i"),0x2A:("ROL","a"),0x2B:("PLD","i"),0x38:("SEC","i"),0x3A:("DEC","a"),0x3B:("TSC","i"),0x40:("RTI","i"),0x44:("MVP","b"),0x48:("PHA","i"),0x4A:("LSR","a"),0x4B:("PHK","i"),0x4C:("JMP","A"),0x54:("MVN","b"),0x58:("CLI","i"),0x5A:("PHY","i"),0x5B:("TCD","i"),0x5C:("JML","L"),0x60:("RTS","i"),0x62:("PER","R"),0x68:("PLA","i"),0x6A:("ROR","a"),0x6B:("RTL","i"),0x6C:("JMP","(A)"),0x78:("SEI","i"),0x7A:("PLY","i"),0x7B:("TDC","i"),0x7C:("JMP","(A,x)"),0x80:("BRA","r"),0x82:("BRL","R"),0x88:("DEY","i"),0x8A:("TXA","i"),0x8B:("PHB","i"),0x98:("TYA","i"),0x9A:("TXS","i"),0x9B:("TXY","i"),0xA8:("TAY","i"),0xAA:("TAX","i"),0xAB:("PLB","i"),0xB8:("CLV","i"),0xBA:("TSX","i"),0xBB:("TYX","i"),0xC8:("INY","i"),0xCA:("DEX","i"),0xD8:("CLD","i"),0xDA:("PHX","i"),0xDC:("JML","[A]"),0xD4:("PEI","d"),0xF4:("PEA","A"),0xE8:("INX","i"),0xEA:("NOP","i"),0xEB:("XBA","i"),0xF8:("SED","i"),0xFA:("PLX","i"),0xFB:("XCE","i"),0xC2:("REP","1"),0xE2:("SEP","1"),0x10:("BPL","r"),0x30:("BMI","r"),0x50:("BVC","r"),0x70:("BVS","r"),0x90:("BCC","r"),0xB0:("BCS","r"),0xD0:("BNE","r"),0xF0:("BEQ","r"),0xFC:("JSR","(A,x)"),0x0C:("TSB","A"),0x04:("TSB","d"),0x1C:("TRB","A"),0x14:("TRB","d"),0x89:("BIT","M"),0x24:("BIT","d"),0x2C:("BIT","A"),0x34:("BIT","dx"),0x3C:("BIT","Ax"),0x06:("ASL","d"),0x0E:("ASL","A"),0x16:("ASL","dx"),0x1E:("ASL","Ax"),0x26:("ROL","d"),0x2E:("ROL","A"),0x36:("ROL","dx"),0x3E:("ROL","Ax"),0x46:("LSR","d"),0x4E:("LSR","A"),0x56:("LSR","dx"),0x5E:("LSR","Ax"),0x66:("ROR","d"),0x6E:("ROR","A"),0x76:("ROR","dx"),0x7E:("ROR","Ax"),0x84:("STY","d"),0x8C:("STY","A"),0x94:("STY","dx"),0x86:("STX","d"),0x8E:("STX","A"),0x96:("STX","dy"),0x64:("STZ","d"),0x74:("STZ","dx"),0x9C:("STZ","A"),0x9E:("STZ","Ax"),0xA0:("LDY","X"),0xA2:("LDX","X"),0xA4:("LDY","d"),0xAC:("LDY","A"),0xB4:("LDY","dx"),0xBC:("LDY","Ax"),0xA6:("LDX","d"),0xAE:("LDX","A"),0xB6:("LDX","dy"),0xBE:("LDX","Ay"),0xC0:("CPY","X"),0xC4:("CPY","d"),0xCC:("CPY","A"),0xE0:("CPX","X"),0xE4:("CPX","d"),0xEC:("CPX","A"),0xC6:("DEC","d"),0xCE:("DEC","A"),0xD6:("DEC","dx"),0xDE:("DEC","Ax"),0xE6:("INC","d"),0xEE:("INC","A"),0xF6:("INC","dx"),0xFE:("INC","Ax")}
ops.update(S)
LEN={'i':1,'a':1,'1':2,'d':2,'dx':2,'dy':2,'(d)':2,'(d,x)':2,'(d),y':2,'[d]':2,'[d],y':2,'s':2,'(s),y':2,'r':2,'A':3,'Ax':3,'Ay':3,'R':3,'(A)':3,'(A,x)':3,'[A]':3,'b':3,'L':4,'Lx':4}
def disasm(rom,o,count,m=False,x=False):
    out=[]
    for _ in range(count):
        op=rom[o]
        if op not in ops: out.append("%06X  %02X  ???"%(o,op)); o+=1; continue
        n,md=ops[op]
        ln=LEN.get(md) or ((2 if m else 3) if md=='M' else (2 if x else 3))
        b=rom[o+1:o+ln]; v=int.from_bytes(b,'little')
        off=0x8000+(o&0x7FFF); bank=0x80+(o>>15)
        if md in('i',): a=""
        elif md=='a': a="A"
        elif md=='M': a="#$%0*X"%(2 if m else 4,v)
        elif md=='X': a="#$%0*X"%(2 if x else 4,v)
        elif md=='1': a="#$%02X"%v
        elif md=='r': a="$%04X"%((off+2+(v-256 if v>127 else v))&0xFFFF)
        elif md=='R': a="$%04X"%((off+3+(v-65536 if v>32767 else v))&0xFFFF)
        elif md=='b': a="$%02X,$%02X"%(b[1],b[0])
        else:
            w=2 if ln==2 else (4 if ln==3 else 6)
            f="$%0*X"%(w,v)
            a={'d':f,'dx':f+",X",'dy':f+",Y",'(d)':"(%s)"%f,'(d,x)':"(%s,X)"%f,'(d),y':"(%s),Y"%f,'[d]':"[%s]"%f,'[d],y':"[%s],Y"%f,'s':f+",S",'(s),y':"(%s,S),Y"%f,'A':f,'Ax':f+",X",'Ay':f+",Y",'(A)':"(%s)"%f,'(A,x)':"(%s,X)"%f,'[A]':"[%s]"%f,'L':f,'Lx':f+",X"}[md]
        out.append("%02X:%04X  %-11s %s %s"%(bank,off,rom[o:o+ln].hex(' '),n,a))
        if n=='REP':
            if v&0x20:m=False
            if v&0x10:x=False
        if n=='SEP':
            if v&0x20:m=True
            if v&0x10:x=True
        o+=ln
    return out
if __name__=="__main__":
    rom=open(sys.argv[1],'rb').read()
    o=int(sys.argv[2],16);c=int(sys.argv[3])
    m=len(sys.argv)>4 and sys.argv[4]=='1';x=len(sys.argv)>5 and sys.argv[5]=='1'
    print("\n".join(disasm(rom,o,c,m,x)))
