"""
list_placeholders.py - every {{PLACEHOLDER:...}} and {{CONFIRM:...}} in the site copy, plus pending panels

    python tools/list_placeholders.py
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def walk(o, path=""):
    if isinstance(o, dict):
        for k, v in o.items():
            yield from walk(v, f"{path}.{k}" if path else k)
    elif isinstance(o, list):
        for i, v in enumerate(o):
            yield from walk(v, f"{path}[{i}]")
    elif isinstance(o, str):
        yield path, o


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    d = json.loads((ROOT / "content" / "case-studies.json").read_text(encoding="utf-8"))
    rows = []
    for path, s in walk(d):
        if path == "_readme":
            continue
        for kind, text in re.findall(r"\{\{(PLACEHOLDER|CONFIRM):([^}]*)\}\}", s):
            rows.append((kind, path, text))
        if path.endswith("placeholder") and not path.endswith("panel.placeholder"):
            rows.append(("PLACEHOLDER", path, s))
    for cs in d["caseStudies"]:
        p = cs["panel"]
        if p.get("status") != "ready":
            rows.append(("PLACEHOLDER", f"{cs['id']}.panel", p["placeholder"]))
        for still in p.get("visual", {}).get("stills", []):
            rows.append(("PLACEHOLDER", f"{cs['id']}.panel.stills", still))
        for st in cs["stats"]:
            if st.get("confirm"):
                rows.append(("CONFIRM", f"{cs['id']}.stats", f"{st.get('text') or st.get('value')} {st['label']}"))
    for kind, path, text in rows:
        print(f"{kind:<12} {path:<40} {text}")
    print(f"\n{sum(1 for r in rows if r[0] == 'PLACEHOLDER')} placeholders, {sum(1 for r in rows if r[0] == 'CONFIRM')} figures to confirm")


if __name__ == "__main__":
    main()
