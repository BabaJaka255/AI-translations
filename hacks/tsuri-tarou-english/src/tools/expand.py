"""Expand Tsuri Tarou from 8 Mbit to 16 Mbit LoROM and fix the header checksum.
expand.py IN.sfc OUT.sfc
The new space (ROM 0x100000-0x1FFFFF, banks $20-$3F / $A0-$BF) is filled with 0xFF."""
import sys
def fix_checksum(r):
    r[0x7FDC:0x7FE0] = b'\xff\xff\x00\x00'
    s = sum(r) & 0xFFFF
    r[0x7FDC:0x7FDE] = (s ^ 0xFFFF).to_bytes(2, 'little'); r[0x7FDE:0x7FE0] = s.to_bytes(2, 'little')
    return s
if __name__ == '__main__':
    r = bytearray(open(sys.argv[1], 'rb').read())
    assert len(r) == 0x100000 and r[0x7FD5] == 0x20 and r[0x7FD7] == 0x0A, 'expected the original 8 Mbit LoROM'
    r += b'\xff' * 0x100000
    r[0x7FD7] = 0x0B
    s = fix_checksum(r)
    open(sys.argv[2], 'wb').write(r)
    print('wrote %s, %d bytes, checksum %04X' % (sys.argv[2], len(r), s))
