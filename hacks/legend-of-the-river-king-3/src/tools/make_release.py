"""Build the patched ROM and the IPS + xdelta patches: python3 make_release.py ORIGINAL.gba VERSION"""
import hashlib, os, subprocess, sys, zlib
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from build_patch import build

def ips(orig, new):
    out = bytearray(b'PATCH'); i = 0; n = len(new)
    while i < n:
        if i < len(orig) and orig[i] == new[i]: i += 1; continue
        j = i
        while j < n and j - i < 0xFFFF and not (j < len(orig) and orig[j] == new[j]
                                                  and j + 4 < n and orig[j:j + 4] == new[j:j + 4]): j += 1
        if i == 0x454F46: i -= 1          # offset 'EOF' is reserved
        run = new[i:j]
        if len(run) > 8 and run.count(run[0]) == len(run):
            out += i.to_bytes(3, 'big') + b'\0\0' + len(run).to_bytes(2, 'big') + run[:1]
        else:
            out += i.to_bytes(3, 'big') + len(run).to_bytes(2, 'big') + run
        i = j
    out += b'EOF'
    if len(new) > len(orig): pass        # IPS readers grow the file as records extend past the end
    return bytes(out)

def hashes(b):
    return dict(size=len(b), crc=f'{zlib.crc32(b) & 0xFFFFFFFF:08X}', md5=hashlib.md5(b).hexdigest(),
                sha1=hashlib.sha1(b).hexdigest())

if __name__ == '__main__':
    src, ver = sys.argv[1], sys.argv[2]
    rel = os.path.join(os.path.dirname(HERE), 'release')
    name = f'Kawa no Nushi Tsuri 5 (English) v{ver}'
    tmp = f'/tmp/k5_{ver}.gba'
    build(src, tmp)
    o = open(src, 'rb').read(); n = open(tmp, 'rb').read()
    open(os.path.join(rel, name + '.ips'), 'wb').write(ips(o, n))
    x = os.path.join(rel, name + '.xdelta')
    if os.path.exists(x): os.remove(x)
    subprocess.run(['xdelta3', '-e', '-9', '-S', 'djw', '-s', src, tmp, x], check=True)
    print('original', hashes(o)); print('patched', hashes(n))
