"""
build.py - synthetic rebuild of the asset risk film and explorer

    python make_synthetic.py && python build.py

Runs the real pipeline unchanged: build_data.py and inline.py are loaded from
_source/asset-risk/ (local reference material, never committed). Only the
inputs and a few CONFIG values are swapped for synthetic ones, and the page
template is index.src.html in this folder (the original, rebranded and with
every client reference removed). Output: index.html, one self-contained file
plus the vendored gsap.min.js beside it.
"""
import importlib.util
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PIPE = HERE.parents[1] / "_source" / "asset-risk"
FICTIONAL_CLIENT = "Example R&D Sciences (fictional client)"


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    if not (PIPE / "build_data.py").exists():
        sys.exit(f"Pipeline not found at {PIPE}. It lives in _source/, which is local-only reference material.")
    if not (HERE / "synthetic_register.xlsx").exists():
        sys.exit("Run make_synthetic.py first.")

    bd = load("build_data", PIPE / "build_data.py")
    bd.HERE = HERE                                  # read the synthetic workbook, write data.json here
    bd.CONFIG.update({
        "workbook": "synthetic_register.xlsx",
        "deck_claims": {"assets": 0, "High": 0, "Medium": 0},   # there is no earlier deck for invented data
        "name_overrides": {},
        "data_as_of": "1 Oct 2026",
        "fx": {"usd_to_gbp": 0.76, "date": "1 Oct 2026"},
        "methodology_text": (
            "Risk score = criticality (30%) + age vs expected life (25%) + breakdowns (25%) "
            "+ obsolescence (20%). Ratings: High ≥ 4.0 · Medium 2.5–3.99 · Low < 2.5. "
            "Synthetic demo: every asset, cost centre, supplier and budget is invented."
        ),
    })
    # The pipeline stamps its original client into meta; swap in the fictional one just before
    # data.json is written (find_nan runs on the finished dict immediately before the write).
    check = bd.find_nan

    def find_nan(o, path="data"):
        if path == "data":
            o["meta"]["client"] = FICTIONAL_CLIENT
            for c in o["cost_centres"]:   # singular agreement the original never hit
                c["headline"] = c["headline"].replace(" 1 overdue critical asset need ", " 1 overdue critical asset needs ")
        return check(o, path)

    bd.find_nan = find_nan
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    bd.main()

    # inline.py resolves its folder from __file__, so point that at this folder.
    code = (PIPE / "inline.py").read_text(encoding="utf-8")
    exec(compile(code, str(PIPE / "inline.py"), "exec"), {"__file__": str(HERE / "inline.py"), "__name__": "__main__"})


if __name__ == "__main__":
    main()
