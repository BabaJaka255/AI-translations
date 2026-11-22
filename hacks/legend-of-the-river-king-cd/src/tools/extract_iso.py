"""Extract the 2048-byte user data of Track 02 (from file sector 224) into data.iso.
usage: extract_iso.py "(Track 02).bin" data.iso"""
import sys
RAW, PREGAP = 2352, 224
d = open(sys.argv[1], 'rb').read()
with open(sys.argv[2], 'wb') as f:
    for n in range(PREGAP, len(d) // RAW):
        f.write(d[n * RAW + 16:n * RAW + 16 + 2048])
