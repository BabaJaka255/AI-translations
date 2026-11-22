"""7 Blades "1.\\." LZ: 4-byte magic, 4-byte BE decompressed size, then tokens.
byte b < 0x80: b literal bytes follow.  b >= 0x80: 16-bit BE v; copy ((~v>>8)&0x7f)+3 bytes from distance (v&0xff)+1.
Every stream on the disc ends with a 0 byte; the member decoder needs it."""
import struct
def decompress(d):
    assert d[:4]==b'1.\\.'
    n=struct.unpack('>I',d[4:8])[0]; out=bytearray(); i=8
    while len(out)<n and i<len(d):
        b=d[i]
        if b&0x80:
            if i+1>=len(d): break
            v=d[i]<<8|d[i+1]; i+=2
            L=((~v>>8)&0x7f)+3; D=(v&0xff)+1
            for _ in range(L): out.append(out[-D])
        else:
            i+=1; out+=d[i:i+b]; i+=b
    return bytes(out[:n])
def compress(d):
    """Greedy LZ, window 256, max copy 130. Uses the C version (b7_lz.c) when gcc is around."""
    import os, subprocess, tempfile
    exe = os.path.join(tempfile.gettempdir(), 'b7_lz_c')
    src = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'b7_lz.c')
    try:
        if not os.path.exists(exe) or os.path.getmtime(exe) < os.path.getmtime(src):
            subprocess.run(['gcc', '-O2', '-w', '-o', exe, src], check=True)
        with tempfile.NamedTemporaryFile() as t:
            t.write(d); t.flush()
            body = subprocess.run([exe, t.name], check=True, capture_output=True).stdout
        return b'1.\\.' + struct.pack('>I', len(d)) + body + b'\0'   # streams end with a 0 token (the game's member decoder stops on it)
    except (OSError, subprocess.CalledProcessError):
        return compress_py(d)
def compress_py(d):
    out=bytearray(b'1.\\.'+struct.pack('>I',len(d))); lit=bytearray(); i=0
    def flush():
        while lit:
            c=lit[:0x7f]; out.append(len(c)); out.extend(c); del lit[:len(c)]
    while i<len(d):
        best=(0,0)
        for D in range(1,min(256,i)+1):
            L=0
            while L<130 and i+L<len(d) and d[i+L-D]==d[i+L]: L+=1
            if L>best[0]: best=(L,D)
        if best[0]>=3:
            flush(); L,D=best; v=((~(L-3)&0x7f)<<8)|0x8000|(D-1); out+=struct.pack('>H',v); i+=L
        else: lit.append(d[i]); i+=1
    flush(); out.append(0); return bytes(out)
if __name__=='__main__':
    import sys; sys.stdout.buffer.write(decompress(open(sys.argv[1],'rb').read()))
