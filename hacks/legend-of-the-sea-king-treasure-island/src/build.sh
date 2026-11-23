#!/bin/sh
# Rebuild the English patch from the original disc. Run from src/:  ./build.sh
# Needs rom/orig.bin (see BUILD.md). Writes files/, out/, view/, gfx_out/, test.bin and the .xdelta (all git-ignored).
set -e
cd "$(dirname "$0")"
[ -f rom/orig.bin ] || { echo "put the original disc image in src/rom/orig.bin (see BUILD.md)"; exit 1; }
ln -sf rom/orig.bin orig.bin                       # the xdelta stores the names orig.bin / test.bin
mkdir -p out view/tim gfx_out
python3 tools/iso.py orig.bin files > /dev/null     # extract the disc's files
python3 tools/dump.py > /dev/null                   # Japanese script dump -> out/script_jp.json (same as the committed one)
python3 tools/timdump.py files/ENDING/STAF*.TIM > /dev/null   # staff roll pictures for tools/credits.py
python3 tools/gfx_build.py > /dev/null              # English graphics -> gfx_out/
python3 tools/build.py test.bin                     # text, font, hooks, labels and graphics -> test.bin
xdelta3 -e -9 -f -s orig.bin test.bin UmiNoNushiTsuriTakarajima_EN_v1.0.xdelta
python3 tools/export_script.py
python3 - <<'PY'
import zlib, hashlib
c = 0; h = hashlib.sha1()
with open('test.bin', 'rb') as f:
    while (b := f.read(1 << 24)): c = zlib.crc32(b, c); h.update(b)
print('test.bin CRC32 %08X SHA-1 %s (expected 563EA50F)' % (c, h.hexdigest()))
PY
