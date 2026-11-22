#!/bin/sh
# Build the English ROM, IPS and xdelta. The ROM must be at rom/k34.gba. Run from src/: ./build.sh
set -e
cd "$(dirname "$0")"
mkdir -p out_build
python3 tools/make_release.py rom/k34.gba 1.0 out_build
