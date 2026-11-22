"""HuC6280 disassembler. usage: dis6280.py file offset addr count"""
import sys
M={'imp':0,'acc':0,'imm':1,'zp':1,'zpx':1,'zpy':1,'izx':1,'izy':1,'izp':1,'abs':2,'abx':2,'aby':2,'ind':2,'iax':2,'rel':1,'zrel':2,'tst_zp':2,'tst_abs':3,'tst_zpx':2,'tst_abx':3,'blk':6}
T={}
def op(c,n,m): T[c]=(n,m)
for base,n in [(0x00,'ora'),(0x20,'and'),(0x40,'eor'),(0x60,'adc'),(0x80,'sta'),(0xa0,'lda'),(0xc0,'cmp'),(0xe0,'sbc')]:
    for o,m in [(1,'izx'),(5,'zp'),(9,'imm'),(0xd,'abs'),(0x11,'izy'),(0x12,'izp'),(0x15,'zpx'),(0x19,'aby'),(0x1d,'abx')]:
        op(base+o,n,m)
del T[0x89]; op(0x89,'bit','imm')
for base,n in [(0x00,'asl'),(0x20,'rol'),(0x40,'lsr'),(0x60,'ror'),(0xc0,'dec'),(0xe0,'inc')]:
    op(base+6,n,'zp');op(base+0xe,n,'abs');op(base+0x16,n,'zpx');op(base+0x1e,n,'abx')
for c,n in [(0x0a,'asl'),(0x2a,'rol'),(0x4a,'lsr'),(0x6a,'ror'),(0x1a,'inc'),(0x3a,'dec')]: op(c,n,'acc')
for c,n in zip(range(0x10,0x100,0x20),['bpl','bmi','bvc','bvs','bcc','bcs','bne','beq']): op(c,n,'rel')
op(0x80,'bra','rel');op(0x44,'bsr','rel')
for c,n in [(0x00,'brk'),(0x08,'php'),(0x18,'clc'),(0x28,'plp'),(0x38,'sec'),(0x40,'rti'),(0x48,'pha'),(0x58,'cli'),(0x60,'rts'),(0x68,'pla'),(0x78,'sei'),(0x88,'dey'),(0x8a,'txa'),(0x98,'tya'),(0x9a,'txs'),(0xa8,'tay'),(0xaa,'tax'),(0xb8,'clv'),(0xba,'tsx'),(0xc8,'iny'),(0xca,'dex'),(0xd8,'cld'),(0xe8,'inx'),(0xea,'nop'),(0xf8,'sed'),(0x5a,'phy'),(0x7a,'ply'),(0xda,'phx'),(0xfa,'plx'),(0x02,'sxy'),(0x22,'sax'),(0x42,'say'),(0x62,'cla'),(0x82,'clx'),(0xc2,'cly'),(0xf4,'set'),(0xd4,'csh'),(0x54,'csl')]: op(c,n,'imp')
op(0x20,'jsr','abs');op(0x4c,'jmp','abs');op(0x6c,'jmp','ind');op(0x7c,'jmp','iax')
op(0x24,'bit','zp');op(0x2c,'bit','abs');op(0x34,'bit','zpx');op(0x3c,'bit','abx')
op(0x84,'sty','zp');op(0x8c,'sty','abs');op(0x94,'sty','zpx');op(0x86,'stx','zp');op(0x8e,'stx','abs');op(0x96,'stx','zpy')
op(0x64,'stz','zp');op(0x9c,'stz','abs');op(0x74,'stz','zpx');op(0x9e,'stz','abx')
op(0xa0,'ldy','imm');op(0xa4,'ldy','zp');op(0xac,'ldy','abs');op(0xb4,'ldy','zpx');op(0xbc,'ldy','abx')
op(0xa2,'ldx','imm');op(0xa6,'ldx','zp');op(0xae,'ldx','abs');op(0xb6,'ldx','zpy');op(0xbe,'ldx','aby')
op(0xc0,'cpy','imm');op(0xc4,'cpy','zp');op(0xcc,'cpy','abs');op(0xe0,'cpx','imm');op(0xe4,'cpx','zp');op(0xec,'cpx','abs')
op(0x04,'tsb','zp');op(0x0c,'tsb','abs');op(0x14,'trb','zp');op(0x1c,'trb','abs')
op(0x43,'tma','imm');op(0x53,'tam','imm');op(0x03,'st0','imm');op(0x13,'st1','imm');op(0x23,'st2','imm')
op(0x83,'tst','tst_zp');op(0x93,'tst','tst_abs');op(0xa3,'tst','tst_zpx');op(0xb3,'tst','tst_abx')
for c,n in [(0x73,'tii'),(0xc3,'tdd'),(0xd3,'tin'),(0xe3,'tia'),(0xf3,'tai')]: op(c,n,'blk')
for i in range(8):
    op(0x07+i*16,'rmb%d'%i,'zp');op(0x87+i*16,'smb%d'%i,'zp');op(0x0f+i*16,'bbr%d'%i,'zrel');op(0x8f+i*16,'bbs%d'%i,'zrel')
def dis(b,pc):
    c=b[0]
    if c not in T: return 1,'.db $%02x'%c
    n,m=T[c]; L=M[m]; a=b[1:1+L]
    w=lambda i: a[i]|a[i+1]<<8
    s={'imp':'','acc':'','imm':'#$%02x'%a[0] if L else '','zp':'$%02x'%a[0] if L else '','zpx':'$%02x,x'%a[0] if L else '','zpy':'$%02x,y'%a[0] if L else '',
    'izx':'($%02x,x)'%a[0] if L else '','izy':'($%02x),y'%a[0] if L else '','izp':'($%02x)'%a[0] if L else ''}.get(m)
    if s is None:
        if m=='abs': s='$%04x'%w(0)
        elif m=='abx': s='$%04x,x'%w(0)
        elif m=='aby': s='$%04x,y'%w(0)
        elif m=='ind': s='($%04x)'%w(0)
        elif m=='iax': s='($%04x,x)'%w(0)
        elif m=='rel': s='$%04x'%((pc+2+(a[0]^0x80)-0x80)&0xffff)
        elif m=='zrel': s='$%02x,$%04x'%(a[0],(pc+3+(a[1]^0x80)-0x80)&0xffff)
        elif m=='tst_zp': s='#$%02x,$%02x'%(a[0],a[1])
        elif m=='tst_zpx': s='#$%02x,$%02x,x'%(a[0],a[1])
        elif m=='tst_abs': s='#$%02x,$%04x'%(a[0],a[1]|a[2]<<8)
        elif m=='tst_abx': s='#$%02x,$%04x,x'%(a[0],a[1]|a[2]<<8)
        elif m=='blk': s='$%04x,$%04x,$%04x'%(w(0),w(2),w(4))
    return 1+L,(n+' '+s).strip()
if __name__=='__main__':
    f,off,addr,cnt=sys.argv[1],int(sys.argv[2],0),int(sys.argv[3],0),int(sys.argv[4],0)
    d=open(f,'rb').read(); p=off
    for _ in range(cnt):
        l,t=dis(d[p:p+7],addr); print('%04x  %-20s %s'%(addr,d[p:p+l].hex(' '),t)); p+=l; addr+=l
