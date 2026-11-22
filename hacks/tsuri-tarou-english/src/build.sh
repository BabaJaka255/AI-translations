#!/bin/sh
# Build the English ROM and IPS from the original. Run from src/: ./build.sh
set -e
cd "$(dirname "$0")"
ROM="${TT_ROM:-rom/Tsuri Tarou (Japan).sfc}"
mkdir -p out_build
python3 tools/build.py "$ROM" out_build/tt_en.sfc
python3 tools/make_ips.py "$ROM" out_build/tt_en.sfc out_build/TsuriTarou_EN_v0.9.1.ips
