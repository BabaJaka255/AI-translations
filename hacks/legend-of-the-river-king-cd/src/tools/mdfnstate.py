"""Parse Mednafen (Beetle PCE Fast) savestates: sections -> {var: (offset, bytes)}."""
import struct
def parse(st):
    p=32; out={}
    while p+36<=len(st):
        name=st[p:p+32].rstrip(b'\0').decode(); size=struct.unpack('<I',st[p+32:p+36])[0]; p+=36
        end=p+size; sec={}
        while p<end:
            n=st[p]; var=st[p+1:p+1+n].decode(); p+=1+n
            sz=struct.unpack('<I',st[p:p+4])[0]; p+=4
            sec[var]=(p,st[p:p+sz]); p+=sz
        out[name]=sec; p=end
    return out
if __name__=='__main__':
    import sys
    for s,v in parse(open(sys.argv[1],'rb').read()).items():
        print(s, ', '.join('%s:%d'%(k,len(b)) for k,(o,b) in v.items()))
