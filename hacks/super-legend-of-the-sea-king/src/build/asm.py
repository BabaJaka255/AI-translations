"""Tiny 65816 assembler (16-bit M/X assumed for immediates marked with '#w')."""
import re
OPS={ # mnemonic: {mode: opcode}
 'LDA':{'ily':0xB7,'dp':0xA5,'imm':0xA9,'longx':0xBF},'STA':{'dp':0x85,'longx':0x9F},'AND':{'imm':0x29},'CMP':{'imm':0xC9,'dp':0xC5},
 'SBC':{'imm':0xE9},'ADC':{'imm':0x69,'dp':0x65},'PHA':{'imp':0x48},'PLA':{'imp':0x68},'SEC':{'imp':0x38},'CLC':{'imp':0x18},
 'ASL':{'imp':0x0A},'LSR':{'imp':0x4A},'BEQ':{'rel':0xF0},'BNE':{'rel':0xD0},'BCC':{'rel':0x90},'BCS':{'rel':0xB0},'BRA':{'rel':0x80},
 'JMP':{'abs':0x4C},'JSR':{'abs':0x20},'RTS':{'imp':0x60},'RTL':{'imp':0x6B},'LDX':{'imm':0xA2},'LDY':{'imm':0xA0},'INX':{'imp':0xE8},'INY':{'imp':0xC8},
 'CPX':{'imm':0xE0},'CPY':{'imm':0xC0},'ORA':{'imm':0x09},'DEC':{'dp':0xC6},'NOP':{'imp':0xEA},'PHY':{'imp':0x5A},'PLY':{'imp':0x7A},'PHX':{'imp':0xDA},'XBA':{'imp':0xEB},'TAX':{'imp':0xAA},'PLX':{'imp':0xFA},
}
def assemble(src,org,ext=None):
    lines=[]; 
    for l in src.splitlines():
        l=l.split(';')[0].strip()
        if l: lines.append(l)
    items=[]; labels=dict(ext or {}); pc=org
    for l in lines:
        m=re.match(r'^(\w+):\s*(.*)$',l)
        if m:
            labels[m.group(1)]=pc; l=m.group(2)
            if not l: continue
        parts=l.split(None,1); mn=parts[0].upper(); arg=parts[1].strip() if len(parts)>1 else None
        if mn=='.DB': items.append(('db',arg)); pc+=len(arg.split(',')); continue
        t=OPS[mn]
        if arg is None: mode='imp'; n=1
        elif arg.startswith('['): mode='ily'; n=2
        elif arg.startswith('#'): mode='imm'; n=3
        elif mn in('BEQ','BNE','BCC','BCS','BRA'): mode='rel'; n=2
        elif re.search(r',\s*X$',arg,re.I) and mn in('LDA','STA'): mode='longx'; n=4
        elif mn in('JMP','JSR'): mode='abs'; n=3
        else: mode='dp'; n=2
        items.append((mn,mode,arg,pc,n)); pc+=n
    out=bytearray()
    def val(a):
        a=a.strip()
        if a in labels: return labels[a]
        return int(a.replace('$','0x'),16) if a.startswith('$') else int(a,0)
    for it in items:
        if it[0]=='db': out+=bytes(val(x) for x in it[1].split(',')); continue
        mn,mode,arg,pc,n=it; op=OPS[mn][mode]; out.append(op)
        if mode=='imp': pass
        elif mode=='imm': v=val(arg[1:]); out+=bytes([v&255,v>>8])
        elif mode=='rel':
            d=val(arg)-(pc+2); assert -128<=d<=127,(mn,arg,d); out.append(d&255)
        elif mode=='abs': v=val(arg); out+=bytes([v&255,(v>>8)&255])
        elif mode=='longx': v=val(re.sub(r',\s*X$','',arg,flags=re.I)); out+=bytes([v&255,(v>>8)&255,v>>16])
        elif mode=='ily': out.append(val(re.match(r'\[(.*)\]',arg).group(1)))
        else: out.append(val(arg))
    return bytes(out),labels
