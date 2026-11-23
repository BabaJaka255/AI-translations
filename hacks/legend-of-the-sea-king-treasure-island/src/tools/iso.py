"""PS1 MODE2/2352 disc: ISO9660 directory listing and file extraction."""
import struct, sys, os
SEC = 2352

def read_sector(f, lba):
    f.seek(lba * SEC)
    return f.read(SEC)

def user(f, lba):
    return read_sector(f, lba)[24:24 + 2048]

def read_extent(f, lba, size):
    out = bytearray()
    n = (size + 2047) // 2048
    for i in range(n):
        out += user(f, lba + i)
    return bytes(out[:size])

def walk(f, lba, size, path=''):
    data = read_extent(f, lba, size)
    i = 0
    while i < len(data):
        l = data[i]
        if l == 0:
            i = (i // 2048 + 1) * 2048
            continue
        rec = data[i:i + l]
        elba = struct.unpack_from('<I', rec, 2)[0]
        esize = struct.unpack_from('<I', rec, 10)[0]
        flags = rec[25]
        nl = rec[32]
        name = rec[33:33 + nl]
        i += l
        if name in (b'\0', b'\1'):
            continue
        name = name.decode('ascii')
        full = path + '/' + name
        if flags & 2:
            yield from walk(f, elba, esize, full)
        else:
            yield full, elba, esize

def listing(fn):
    with open(fn, 'rb') as f:
        pvd = user(f, 16)
        assert pvd[1:6] == b'CD001'
        root = pvd[156:156 + 34]
        rl, rs = struct.unpack_from('<I', root, 2)[0], struct.unpack_from('<I', root, 10)[0]
        return list(walk(f, rl, rs))

if __name__ == '__main__':
    fn = sys.argv[1]
    files = listing(fn)
    for p, l, s in sorted(files, key=lambda x: x[1]):
        print(f'{l:6d} {s:9d} {p}')
    if len(sys.argv) > 2:
        out = sys.argv[2]
        with open(fn, 'rb') as f:
            for p, l, s in files:
                d = os.path.join(out, p.lstrip('/').split(';')[0])
                os.makedirs(os.path.dirname(d), exist_ok=True)
                open(d, 'wb').write(read_extent(f, l, s))
