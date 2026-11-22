#!/bin/sh
# Build the English Track 02 and both patches. Run from src/: ./build.sh
set -e
cd "$(dirname "$0")"
TRACK="${KS_TRACK:-rom/Kawa no Nushitsuri - Shizen-ha (Japan) (Track 02).bin}"
mkdir -p out_build
python3 tools/extract_iso.py "$TRACK" out_build/data.iso     # 2048-byte user data, for the script dump
python3 tools/dump_script.py out_build/data.iso out             # out/script.json + out/script_dump.txt
cp "$TRACK" out_build/track02.bin
python3 tools/build_patch.py out_build/track02.bin out_build/en_track02.bin
python3 tools/make_ips.py out_build/track02.bin out_build/en_track02.bin out_build/KawaNoNushiTsuriShizenha_EN_v0.9.6.ips
# xdelta stores the file names, so encode from inside out_build to get the published bytes
cd out_build && xdelta3 -e -f -S lzma -s track02.bin en_track02.bin KawaNoNushiTsuriShizenha_EN_v0.9.6.xdelta
