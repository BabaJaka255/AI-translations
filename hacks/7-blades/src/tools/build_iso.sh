# build_iso.sh <jp.iso> <out.iso> [hooks] : JP ELF + PEACE.NCB + the movies' stage archives -> patched ISO
# needs: mips64el cross gcc (see b7_build_jp.py), romhack-toolkit (rhtk). Work files go to $W (default build/work).
set -eo pipefail
JP=$1; OUT=$2; HOOKS=${3:-play,pic,send,tut,str,font,status,kills,save,fx,press,opt}
W=${W:-build/work}; mkdir -p $W/stagemov
cd "$(dirname "$0")/.."
B7_HOOKS="$HOOKS" python3 tools/b7_build_jp.py $W/SLPM_650.08 | tail -1
python3 tools/b7_peace.py $W/PEACE.NCB | tail -1
python3 tools/b7_stagedata.py "$JP" $W/PEACE.NCB $W/stagemov | wc -l
python3 -c "
import sys, json; sys.path.insert(0,'toolkit')
from rhtk.ps2 import patch_iso
rep={'/SLPM_650.08':'$W/SLPM_650.08','/EFF/PEACE.NCB':'$W/PEACE.NCB'}
rep.update({k: v['file'] for k, v in json.load(open('$W/stagemov/map.json')).items()})
patch_iso('$JP','$OUT',rep)" | grep -v 'in place' | tail -3
# release: xdelta3 -e -9 -S djw -s "$JP" "$OUT" build/release/7blades-en.xdelta
