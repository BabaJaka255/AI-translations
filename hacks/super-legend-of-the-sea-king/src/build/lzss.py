"""Graphics compression (LZSS, 4K window). Same format in Kawa no Nushi Tsuri 2 ($00:E5C2) and Umi no Nushi Tsuri ($80:92C6)."""
def lo(bank,addr): return (bank&0x7F)*0x8000+(addr&0x7FFF)
def decompress(rom,off):
    n=rom[off]|rom[off+1]<<8; p=off+2; out=bytearray()
    flags=0;bits=0
    while len(out)<n:
        if bits==0: flags=rom[p];p+=1;bits=8
        bits-=1
        if flags&1:
            out.append(rom[p]);p+=1
        else:
            b0,b1=rom[p],rom[p+1];p+=2
            ln=(b1&0xF)+3; pos=b0|((b1>>4)<<8)
            y=len(out); d=(y-pos)&0xFFF; s=y-d
            for i in range(ln):
                out.append(out[s+i] if s+i>=0 else 0)
        flags>>=1
    return bytes(out[:n]),p-off
def compress_literal(data):
    out=bytearray([len(data)&255,len(data)>>8])
    for i in range(0,len(data),8):
        chunk=data[i:i+8]; out.append(0xFF); out+=chunk
    return bytes(out)
def compress(data):
    """Greedy LZSS matching the game's decoder (4K window, lengths 3..18)."""
    n=len(data); out=bytearray([n&255,n>>8]); i=0
    from collections import defaultdict
    heads=defaultdict(list)
    while i<n:
        flagpos=len(out); out.append(0); flags=0
        for bit in range(8):
            if i>=n: break
            best=0; bs=0
            if i+3<=n:
                key=data[i:i+3]
                cand=heads.get(key,[])
                for s in reversed(cand[-64:]):
                    if i-s>4095: break
                    l=3; mx=min(18,n-i)
                    while l<mx and data[s+l]==data[i+l]: l+=1
                    if l>best: best=l; bs=s
                    if l==18: break
            if best>=3:
                pos=bs&0xFFF
                out.append(pos&255); out.append(((pos>>8)<<4)|(best-3))
                for k in range(i,i+best):
                    if k+3<=n: heads[data[k:k+3]].append(k)
                i+=best
            else:
                flags|=1<<bit; out.append(data[i])
                if i+3<=n: heads[data[i:i+3]].append(i)
                i+=1
        out[flagpos]=flags
    return bytes(out)
