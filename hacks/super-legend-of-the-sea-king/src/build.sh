#!/bin/sh
# Build the English ROM and IPS. Put the ROM in rom/ (or set UMI_ROM). Run from src/: ./build.sh
set -e
cd "$(dirname "$0")"
python3 analysis/dump_script.py     # out/script.json and out/script_dump.txt from your ROM
python3 build/build_patch.py        # out/umi_en.sfc and out/umi_en.ips
