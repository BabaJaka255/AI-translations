"""Find strings of little-endian Shift-JIS words ending in 0000. usage: scan_text.py data.iso [minlen]"""
import sys
d=open(sys.argv[1],'rb').read(); mn=int(sys.argv[2]) if len(sys.argv)>2 else 3
def ok(w):
    h,l=w>>8,w&0xff
    return (0x81<=h<=0x9f or 0xe0<=h<=0xea) and (0x40<=l<=0xfc and l!=0x7f)
def scan(par):
    out=[];i=par;start=None
    while i+1<len(d):
        w=d[i]|d[i+1]<<8
        if ok(w):
            if start is None: start=i
        else:
            if start is not None and (i-start)//2>=mn:
                try: out.append((start,b''.join(bytes([d[j+1],d[j]]) for j in range(start,i,2)).decode('cp932'),w==0))
                except UnicodeDecodeError: pass
            start=None
        i+=2
    return out
res=sorted(scan(0)+scan(1))
for o,t,z in res: print('%06x %03x %s %s'%(o,o//2048,'Z' if z else ' ',t))
