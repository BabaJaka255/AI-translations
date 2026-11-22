"""Mode 1 CD sector EDC/ECC (ECMA-130)."""
EDC=[0]*256
for i in range(256):
    e=i
    for _ in range(8): e=(e>>1)^(0xD8018001 if e&1 else 0)
    EDC[i]=e
F=[0]*256; B=[0]*256
for i in range(256):
    j=(i<<1)^(0x11D if i&0x80 else 0); F[i]=j&0xff; B[i^j&0xff]=i
def edc(data):
    e=0
    for b in data: e=(e>>8)^EDC[(e^b)&0xff]
    return e
def _ecc(sec,major,minor,mmul,minc,dest):
    size=major*minor
    for m in range(major):
        idx=(m>>1)*mmul+(m&1); a=b=0
        for n in range(minor):
            t=sec[12+idx]; idx+=minc
            if idx>=size: idx-=size
            a^=t; b^=t; a=F[a]
        a=B[F[a]^b]
        sec[12+dest+m]=a; sec[12+dest+m+major]=a^b
def mode1(sector2352):
    s=bytearray(sector2352)
    e=edc(s[0:0x810]); s[0x810:0x814]=e.to_bytes(4,'little'); s[0x814:0x81c]=bytes(8)
    _ecc(s,86,24,2,86,0x81C-12)
    _ecc(s,52,43,86,88,0x8C8-12)
    return bytes(s)
if __name__=='__main__':
    import sys
    d=open(sys.argv[1],'rb').read(); bad=0
    for i in range(int(sys.argv[2]),int(sys.argv[3])):
        s=d[i*2352:(i+1)*2352]
        if mode1(s)!=s: bad+=1
    print('mismatch',bad)
