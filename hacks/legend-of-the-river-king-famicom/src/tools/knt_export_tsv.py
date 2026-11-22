"""Export the script as one TSV row per line: id, location, original, translation, limits, notes.

  python3 tools/knt_export_tsv.py > script/script.tsv

Reads script/lines.json (ids, pointer locations, Japanese) and script/en_lines.txt (the English the
build uses).  The TSV is for reading and diffing; edit en_lines.txt, then re-export.
Location: "stub@0x..." = file offset (in the original ROM) of the LDX #hi / LDY #lo stub that points at
the line; "seq@0x...#n" = n-th line of a sequential block whose pointer setup is at that offset.
"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
os.chdir(os.path.join(HERE, ".."))
import knt_build

LIMITS = "2 rows x 18 tiles; auto-wrap at a space, | forces the break; <B1> counts 15, number codes 2-4"


def main():
    lines = json.load(open("script/lines.json", encoding="utf-8"))
    en = knt_build.load_en("script/en_lines.txt")
    out = ["id\tbank\tlocation\tjapanese\tenglish\tlimits\tnotes"]
    for d in lines:
        loc = ";".join(f"{r['type']}@0x{r['at']:X}" + (f"#{r['index']}" if r["type"] == "seq" else "")
                       for r in d["refs"])
        row = [d["id"], str(d["bank"]), loc, d["jp"], en.get(d["id"], ""), LIMITS, d.get("notes", "")]
        out.append("\t".join(str(x).replace("\t", " ").replace("\n", " ") for x in row))
    sys.stdout.write("\n".join(out) + "\n")


if __name__ == "__main__":
    main()
