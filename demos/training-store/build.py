"""
build.py - synthetic rebuild of the Training Store

    python make_synthetic.py && python build.py

Runs the real pipeline, _source/training-store/build_data.py (local reference
material, never committed). That script has its input paths written into
module-level constants, so this wrapper swaps just those lines for the
synthetic files and executes the rest untouched. The resulting
course_data.json is then inlined into template.html (the original page,
rebranded, with the mailbox, LMS links and product names removed) to make
index.html: one self-contained file.
"""
import json
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PIPE = HERE.parents[1] / "_source" / "training-store" / "build_data.py"
MARKER = "/*__DATA__*/"

INPUTS = {
    "UP": "",
    "LMS": str(HERE / "synthetic_lms.xlsx"),
    "MATRIX": str(HERE / "synthetic_matrix.json"),
    "ACT": str(HERE / "synthetic_equipment.xlsx"),
    "GENERATED": "2026-10-01",
}


def main():
    if not PIPE.exists():
        sys.exit(f"Pipeline not found at {PIPE}. It lives in _source/, which is local-only reference material.")
    for k in ("LMS", "MATRIX", "ACT"):
        if not Path(INPUTS[k]).exists():
            sys.exit("Run make_synthetic.py first.")

    code = PIPE.read_text(encoding="utf-8")
    for name, value in INPUTS.items():
        line = f"{name} = {value!r}"
        code, n = re.subn(rf"^{name}\s*=.*$", lambda m: line, code, count=1, flags=re.M)
        if n != 1:
            sys.exit(f"Could not find the {name} = ... line in the pipeline")

    cwd = os.getcwd()
    os.chdir(HERE)                       # the pipeline writes course_data.json to the working directory
    try:
        exec(compile(code, str(PIPE), "exec"), {"__name__": "__main__", "__file__": str(PIPE)})
    finally:
        os.chdir(cwd)

    data = json.loads((HERE / "course_data.json").read_text(encoding="utf-8"))
    # A model number that resolves to HPLC training, for the hint in the page header
    example = next((k for k, v in sorted(data["synonyms"].items()) if "LC SYSTEM" in v and any(c.isdigit() for c in k)), "")
    blob = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/").replace("<!--", "<\\!--")
    tpl = (HERE / "template.html").read_text(encoding="utf-8")
    if tpl.count(MARKER) != 1:
        sys.exit(f"template.html must contain {MARKER} exactly once")
    out = HERE / "index.html"
    out.write_text(tpl.replace(MARKER, blob).replace("__EXAMPLE_MODEL__", example), encoding="utf-8")

    cards = data["courses"]
    classes = sorted({k for c in cards for k in c["cls"]})
    print(f"Wrote {out.name} ({out.stat().st_size / 1024:,.0f} KB): {len(cards)} cards, "
          f"{sum(1 for c in cards if c['eq'])} mapped to equipment, {len(classes)} equipment classes, "
          f"{len(data['synonyms'])} model/series synonyms. Example model: {example}")


if __name__ == "__main__":
    main()
