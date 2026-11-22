"""Test build only: L / R warp between the fishing zones (areas 1-7, area 8 is the town).
Reads out/umi_en.sfc, writes out/umi_warp_test.sfc and out/umi_warp_test.ips (against the original ROM).

The field loop's LDA $141A / BEQ at $80:B234 (every frame, walking or on the boat) becomes a JSL to a helper
and a NOP; the helper does the BEQ itself. On a new L or R press in the field ($141A = 2, walking or on the boat) the helper does what the game's own exits do: sound and
fade ($80:951A, $80:9CB0), new area/x/y in $1442/$1444/$1446 (also $0998/$099A so a door under the spawn point
does not fire), $141A = 1 to reload the area, then leaves the JSL frame and jumps to the loop's RTS at $80:B27E so no
exit check runs on the stale position. R goes to the next zone, L to the previous one (1-7, wrapping); from the town R
goes to zone 1 and L to zone 7. Spawn points are the spots the game itself puts the player on."""
import struct,sys
import paths as P
from lzss import lo

def ips(a,b):
    """IPS with RLE records, so the 2 MB of padding costs a few bytes."""
    out=bytearray(b'PATCH'); i=0; n=len(b)
    def same(k): return k<len(a) and a[k]==b[k]
    while i<n:
        if same(i): i+=1; continue
        if i==0x454F46: i-=1
        r=i
        while r<n and r-i<0xFFFF and b[r]==b[i] and not same(r): r+=1
        if r-i>=16:
            out+=struct.pack('>I',i)[1:]+b'\0\0'+struct.pack('>H',r-i)+b[i:i+1]; i=r; continue
        j=i
        while j<n and j-i<0xFFFF and not same(j):
            if j+16<=n and len(set(b[j:j+16]))==1 and not any(same(k) for k in range(j,j+16)): break
            j+=1
        out+=struct.pack('>I',i)[1:]+struct.pack('>H',j-i)+b[i:j]; i=j
    return bytes(out+b'EOF')

SITE=(0x80,0xB234); OLD=bytes.fromhex('ad1a14f045')
BASE=0xFE00                        # $82:FE00, zero padding in the built ROM
SPAWN=[(0x20,0x05),(0x3E,0x03),(0x3B,0x05),(0x20,0x38),(0x18,0x2F),(0x20,0x02),(0x10,0x3B)]

def code(base):
    tbl=base+0x100
    out=bytearray(); lab={}; fix=[]
    def b(*x): out.extend(x)
    def w16(v): b(v&255,v>>8)
    def L(n): lab[n]=base+len(out)
    def br(op,n): b(op,0); fix.append((len(out)-1,n))
    b(0xAD); w16(0x141A); br(0xF0,'out')      # LDA $141A / BEQ out (the original BEQ $B27E)
    b(0xAD); w16(0x0224)                      # LDA $0224 (new presses)
    b(0x29); w16(0x0030)                      # AND #$0030 (L|R)
    br(0xF0,'done')
    b(0x48)                                   # PHA
    b(0xAD); w16(0x141A); b(0xC9); w16(2)     # field running?
    br(0xF0,'go')
    b(0x68); br(0x80,'done')                  # PLA / BRA done
    L('go'); b(0x68)
    b(0x29); w16(0x0010)                      # R?
    br(0xF0,'prev')
    b(0xAD); w16(0x1442); b(0xC9); w16(7)
    br(0xB0,'one')                            # 7 or town -> 1
    b(0x1A); br(0x80,'set')                   # INC A
    L('one'); b(0xA9); w16(1); br(0x80,'set')
    L('prev'); b(0xAD); w16(0x1442); b(0x3A)  # DEC A
    br(0xF0,'seven')                          # 1 -> 7
    b(0xC9); w16(7); br(0x90,'set')           # 2-7 -> 1-6
    L('seven'); b(0xA9); w16(7)               # town (8) -> 7 as well
    L('set'); b(0x8D); w16(0x1442)
    b(0x0A,0x0A,0xAA)                         # ASL ASL TAX
    b(0xBF); w16(tbl-4); b(0x82)              # LDA tbl-4,X (long)
    b(0x8D); w16(0x1444); b(0x8D); w16(0x0998)
    b(0xBF); w16(tbl-2); b(0x82)
    b(0x8D); w16(0x1446); b(0x8D); w16(0x099A)
    b(0xA9); w16(1); b(0x85,0x3E)             # LDA #1 / STA $3E
    for n,target in (('r1',0x951A),('r2',0x9CB0)):
        b(0x4B)                               # PHK
        b(0xF4); fix.append((len(out),n+'-1')); w16(0)   # PEA ret-1 (for the RTL)
        b(0xF4); w16(0xB222)                  # PEA $B222 -> RTS lands on the RTL at $80:B223
        b(0x5C); w16(target); b(0x80)         # JML $80xxxx
        L(n)
    b(0xA9); w16(1); b(0x8D); w16(0x141A)     # reload area
    L('out'); b(0x68,0xE2,0x20,0x68,0xC2,0x20)   # drop the JSL return (PLA, SEP, PLA, REP)
    b(0x5C); w16(0xB27E); b(0x80)             # JML $80:B27E (RTS)
    L('done'); b(0x6B)                        # RTL
    for i,n in fix:
        if n.endswith('-1'):
            v=lab[n[:-2]]-1; out[i]=v&255; out[i+1]=v>>8
        else:
            d=lab[n]-(base+i+1); assert -128<=d<128,n; out[i]=d&255
    assert len(out)<0x100
    t=b''.join(struct.pack('<HH',x,y) for x,y in SPAWN)
    return bytes(out)+bytes(0x100-len(out))+t

def main():
    orig=open(P.ROM,'rb').read()
    rom=bytearray(open(P.out('umi_en.sfc'),'rb').read())
    c=code(BASE); o=lo(0x82,BASE); assert set(rom[o:o+len(c)])=={0}; rom[o:o+len(c)]=c
    s=lo(*SITE); assert rom[s:s+5]==OLD and rom[lo(0x80,0xB223)]==0x6B
    rom[s:s+5]=bytes([0x22,BASE&255,BASE>>8,0x82,0xEA])
    open(P.out('umi_warp_test.sfc'),'wb').write(rom)
    open(P.out('umi_warp_test.ips'),'wb').write(ips(orig,bytes(rom)))
    print('wrote',P.out('umi_warp_test.sfc'))
if __name__=='__main__': main()
