"""
build.py - run the real procedure library tools on the synthetic inputs

    python make_synthetic.py && python build.py

1. build_docs.py renders example/EX-01_*.md to .docx. It runs unchanged, pointed at
   engine/ (a neutral stand-in for the corporate Word engine it normally loads) with
   its flow-band colours set to the site's teal. The .docx is an intermediate: it stays
   in example/build/ and is not committed. Its file properties are rewritten to neutral
   values, because the script stamps its own owner and programme name into them.
2. check_docs.py checks the .docx against example/gaps.xlsx. Its report is saved as
   example/check_report.txt (two deliberate failures expected, so it exits 1).
3. Word (on Windows) exports the .docx to PDF and PyMuPDF renders each page to WebP:
   example/page-1.webp, page-2.webp ...
4. build_index.py renders register.json to register-index.html, with its page
   template swapped for index_template.html (the original, rebranded).
5. index.html is assembled from page_template.html with all of the above inlined.

The tools live in _source/procedure-library/tools/ (local-only reference material).
"""
import html
import importlib.util
import json
import os
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOOLS = HERE.parents[1] / "_source" / "procedure-library" / "tools"
PATTERNS = HERE.parents[1] / "_source" / "anon_patterns.txt"
EX = HERE / "example"
BUILD = EX / "build"


def master():
    found = sorted(EX.glob("EX-*.md"))
    if not found:
        sys.exit("Run make_synthetic.py first.")
    return found[0]


def build_docx(md):
    src = (TOOLS / "build_docs.py").read_text(encoding="utf-8")
    env = re.search(r"os\.environ\.get\('([A-Z_]+)'\)", src).group(1)   # the engine-folder override it honours
    os.environ[env] = str(HERE / "engine")
    spec = importlib.util.spec_from_file_location("build_docs", TOOLS / "build_docs.py")
    bd = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bd)
    bd.FLOW_GREEN, bd.FLOW_TINT = "0B6E69", "E3F1EF"
    bd.OUT = str(BUILD)
    out = Path(bd.build(str(md)))
    from docx import Document
    d = Document(out)
    cp = d.core_properties
    cp.author = cp.last_modified_by = "Synthetic demo"
    cp.category = "Synthetic demo"
    cp.comments = "Invented example built by build_docs.py for a public portfolio."
    cp.keywords = cp.subject = ""
    d.save(out)
    return out


def leak_check(path):
    """The repo-wide grep skips binary files, so check the .docx text here."""
    if not PATTERNS.exists():
        print("  (no pattern file; .docx leak check skipped)")
        return
    import zipfile
    xml = " ".join(zipfile.ZipFile(path).read(n).decode("utf-8", "ignore") for n in zipfile.ZipFile(path).namelist()
                   if n.endswith(".xml"))
    pats = [p.strip() for p in PATTERNS.read_text(encoding="utf-8").splitlines() if p.strip()]
    hits = [p for p in pats if re.search(p, xml, re.I)]
    if hits:
        sys.exit(f"FAIL: {len(hits)} real reference pattern(s) found inside {path.name}")
    print("  .docx text clean")


def check(docx):
    r = subprocess.run([sys.executable, str(TOOLS / "check_docs.py"), str(docx), "--gaps", str(EX / "gaps.xlsx")],
                       capture_output=True, text=True, encoding="utf-8")
    report = r.stdout.strip() + "\n"
    (EX / "check_report.txt").write_text(report, encoding="utf-8")
    print(report)
    return report


def render_pages(docx):
    pdf = BUILD / (docx.stem + ".pdf")
    ps = (f"$w = New-Object -ComObject Word.Application; $w.Visible = $false; "
          f"$d = $w.Documents.Open('{docx}', $false, $true); $d.ExportAsFixedFormat('{pdf}', 17); "
          f"$d.Close($false); $w.Quit()")
    subprocess.run(["powershell", "-NoProfile", "-Command", ps], check=True)
    import pymupdf as fitz
    from PIL import Image
    for old in EX.glob("page-*.webp"):
        old.unlink()
    pages = []
    with fitz.open(pdf) as doc:
        for i, page in enumerate(doc, 1):
            pix = page.get_pixmap(dpi=110)
            img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
            out = EX / f"page-{i}.webp"
            img.save(out, "WEBP", quality=80, method=6)
            pages.append((out.name, img.width, img.height))
    print(f"  {len(pages)} pages rendered")
    return pages


def build_index():
    code = (TOOLS / "build_index.py").read_text(encoding="utf-8")
    swaps = [
        (r"^REG = .*$", f"REG = {str(HERE / 'register.json')!r}"),
        (r"^OUT = .*$", f"OUT = {str(HERE / 'register-index.html')!r}"),
    ]
    for pat, line in swaps:
        code, n = re.subn(pat, lambda m: line, code, count=1, flags=re.M)
        if n != 1:
            sys.exit(f"build_index.py: no line matching {pat}")
    tpl = f"TEMPLATE = open({str(HERE / 'index_template.html')!r}, encoding='utf-8').read()"
    code, n = re.subn(r"TEMPLATE = r'''.*?'''", lambda m: tpl, code, count=1, flags=re.S)
    if n != 1:
        sys.exit("build_index.py: TEMPLATE block not found")
    exec(compile(code, str(TOOLS / "build_index.py"), "exec"), {"__name__": "__main__", "__file__": str(TOOLS / "build_index.py")})


def page(md, report, pages):
    def report_html(text):
        rows = []
        for line in text.splitlines():
            cls = "fail" if re.match(r"\s+FAIL", line) else "warn" if re.match(r"\s+WARN", line) else "pass" if re.match(r"\s+PASS", line) else "head"
            note = ""
            if cls == "fail" and " banned " in line:
                note = '<span class="why">deliberate: a banned word in step 5.2.3</span>'
            elif cls == "fail" and " verify " in line:
                note = '<span class="why">deliberate: the step 5.3.4 marker has no gap-register row</span>'
            rows.append(f'<span class="ln {cls}">{html.escape(line)}{note}</span>')
        return "".join(rows)   # each line is a block span; newlines inside <pre> would double the spacing

    reg = json.loads((HERE / "register.json").read_text(encoding="utf-8"))
    imgs = "".join(f'<img src="example/{n}" width="{w}" height="{h}" alt="Page {i} of the built procedure" loading="lazy">'
                   for i, (n, w, h) in enumerate(pages, 1))
    tpl = (HERE / "page_template.html").read_text(encoding="utf-8")
    out = (tpl.replace("__MASTER_NAME__", html.escape(md.name))
              .replace("__MASTER__", html.escape(md.read_text(encoding="utf-8")))
              .replace("__REPORT__", report_html(report))
              .replace("__PAGES__", imgs)
              .replace("__NDOCS__", str(len(reg["documents"]))))
    (HERE / "index.html").write_text(out, encoding="utf-8")
    print(f"Wrote index.html ({(HERE / 'index.html').stat().st_size / 1024:,.0f} KB)")


def main():
    if not TOOLS.exists():
        sys.exit(f"Tools not found at {TOOLS}. They live in _source/, which is local-only reference material.")
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    md = master()
    print("1. build_docs.py")
    docx = build_docx(md)
    leak_check(docx)
    print("2. check_docs.py")
    report = check(docx)
    print("3. render pages")
    pages = render_pages(docx)
    print("4. build_index.py")
    build_index()
    print("5. demo page")
    page(md, report, pages)


if __name__ == "__main__":
    main()
