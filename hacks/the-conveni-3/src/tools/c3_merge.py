"""Re-merge every script TSV into script/elf.json and script/cn3.json in the canonical order (later wins).

  python3 tools/c3_merge.py

elf: addjp elf_labels.tsv, every elf_NNN*.tsv sorted, elf_angel.tsv.
cn3: every cn3_NNN*.tsv sorted, cn3_career, cn3_names, cn3_angel, then cn3_NNN*_late fixes that must beat the
names file (files whose name contains "_fit"). Always run this instead of adding one TSV alone.
"""
import glob
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TR = os.path.join(HERE, "..", "script", "tr")


def run(*a):
    subprocess.run([sys.executable, os.path.join(HERE, "c3_tr.py"), *a], check=True)


def numbered(prefix):
    return sorted(f for f in glob.glob(os.path.join(TR, prefix + "_[0-9][0-9][0-9]*.tsv")))


run("addjp", "elf", os.path.join(TR, "elf_labels.tsv"))
for f in numbered("elf"):
    run("add", "elf", f)
run("add", "elf", os.path.join(TR, "elf_angel.tsv"))
cn = numbered("cn3")
late = [f for f in cn if "_fit" in os.path.basename(f)]
for f in [f for f in cn if f not in late]:
    run("add", "cn3", f)
for n in ("cn3_career", "cn3_names", "cn3_angel"):
    run("add", "cn3", os.path.join(TR, n + ".tsv"))
for f in late:
    run("add", "cn3", f)
run("check")
