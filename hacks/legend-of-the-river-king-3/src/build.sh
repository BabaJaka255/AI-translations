#!/bin/sh
# Build the English ROM, IPS and xdelta. The ROM must be at rom/k5.gba (or set K5_ROM). Run from src/: ./build.sh
set -e
cd "$(dirname "$0")"
ROM="${K5_ROM:-rom/k5.gba}"
python3 tools/dump_script.py "$ROM" out/script_jp.json      # Japanese script from your ROM
python3 tools/ui_strings.py "$ROM" out/ui_jp.json           # menu/UI string candidates
python3 tools/wrap_script.py                                # text/script_en_*.txt -> out/script.json
mkdir -p release
python3 tools/make_release.py "$ROM" 0.9.2                  # -> release/*.ips, *.xdelta
