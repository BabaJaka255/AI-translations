#!/bin/sh
# Build the English disc image and xdelta. The .bin must be at rom/orig.bin. Run from src/: ./build.sh
set -e
cd "$(dirname "$0")"
ln -sf rom/orig.bin orig.bin
python3 tools/iso.py orig.bin files > files.txt              # extract the disc's files into files/ (not committed)
python3 tools/build.py rel096.bin
xdelta3 -e -f -9 -S lzma -s orig.bin rel096.bin KawaNoNushiTsuriHikyou_EN_v0.9.6.xdelta
