"""Make and verify an IPS patch: make_ips.py ORIGINAL.sfc PATCHED.sfc OUT.ips
Handles the 8 -> 16 Mbit expansion (records past the original end; long runs use IPS RLE records)."""
import sys, zlib
def make(a, b):
    out = bytearray(b'PATCH'); i = 0; n = len(b)
    a = a + b'\x00' * (n - len(a))
    while i < n:
        if a[i] == b[i] and i < len(a): i += 1; continue
        j = i
        while j < n and (a[j] != b[j]) and j - i < 0xFFFF: j += 1
        # extend over short equal gaps (cheaper than a new record header)
        while j < n and j - i < 0xFFF0:
            k = j
            while k < n and a[k] == b[k] and k - j < 6: k += 1
            if k < n and k - j < 6 and a[k] != b[k]:
                j = k
                while j < n and a[j] != b[j] and j - i < 0xFFFF: j += 1
            else: break
        chunk = b[i:j]
        if i == 0x454F46: i -= 1; chunk = b[i:j]          # avoid the 'EOF' offset
        if len(set(chunk)) == 1 and len(chunk) > 8:
            out += i.to_bytes(3, 'big') + b'\x00\x00' + len(chunk).to_bytes(2, 'big') + chunk[:1]
        else:
            out += i.to_bytes(3, 'big') + len(chunk).to_bytes(2, 'big') + chunk
        i = j
    return bytes(out + b'EOF' + n.to_bytes(3, 'big'))     # truncation extension: final size
def apply(a, p):
    assert p[:5] == b'PATCH'; r = bytearray(a); i = 5
    while True:
        if p[i:i+3] == b'EOF' and i + 3 >= len(p) - 3:
            if len(p) - (i + 3) == 3: n = int.from_bytes(p[i+3:i+6], 'big'); r = r[:n] + b'\x00' * max(0, n - len(r))
            break
        o = int.from_bytes(p[i:i+3], 'big'); s = int.from_bytes(p[i+3:i+5], 'big'); i += 5
        if s == 0:
            s = int.from_bytes(p[i:i+2], 'big'); v = p[i+2]; i += 3; data = bytes([v]) * s
        else: data = p[i:i+s]; i += s
        if len(r) < o + s: r += b'\x00' * (o + s - len(r))
        r[o:o+s] = data
    return bytes(r)
if __name__ == '__main__':
    a = open(sys.argv[1], 'rb').read(); b = open(sys.argv[2], 'rb').read()
    p = make(a, b); open(sys.argv[3], 'wb').write(p)
    c = apply(a, p)
    assert c == b, 'patch does not reproduce the build'
    print('%s: %d bytes; original CRC32 %08X -> patched CRC32 %08X (%d bytes)' % (sys.argv[3], len(p), zlib.crc32(a), zlib.crc32(b), len(b)))
