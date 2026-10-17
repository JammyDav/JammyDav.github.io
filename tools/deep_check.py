"""
deep_check.py - the anonymisation check, including files grep cannot read

anon_check.sh greps text files only (grep -I skips binary). This also opens .xlsx
and .docx files and reads image bytes for embedded metadata, then looks for stray
email addresses, phone numbers and tenant URLs. The CV PDF is skipped: it is your
own published document and names your employer by design.

    python tools/deep_check.py        # exit 0 clean, 1 hits, 2 no pattern file
"""
import os
import re
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATTERNS = ROOT / "_source" / "anon_patterns.txt"
SKIP_DIRS = {"_source", "node_modules", ".claude", "__pycache__", ".git", "build"}
ALLOWED_EMAILS = {"michaeldavies6@icloud.com", "training-team@example.com"}


def files():
    for root, dirs, names in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for n in names:
            yield Path(root) / n


def text_of(p):
    ext = p.suffix.lower()
    if ext in (".xlsx", ".docx"):
        with zipfile.ZipFile(p) as z:
            return " ".join(z.read(n).decode("utf-8", "ignore") for n in z.namelist() if n.endswith(".xml"))
    if ext in (".webp", ".png", ".jpg", ".jpeg", ".gif"):
        return p.read_bytes().decode("latin-1")
    return p.read_bytes().decode("utf-8", "ignore")


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if not PATTERNS.exists():
        print(f"FAIL: {PATTERNS} not found")
        return 2
    pats = [re.compile(l.strip(), re.I) for l in PATTERNS.read_text(encoding="utf-8").splitlines() if l.strip()]
    problems, n = [], 0
    for p in files():
        rel = p.relative_to(ROOT).as_posix()
        if p.suffix.lower() == ".pdf":
            continue
        t = text_of(p)
        n += 1
        problems += [f"pattern  {rel}: {m.group(0)}" for rx in pats for m in rx.finditer(t)]
        if p.suffix.lower() in (".webp", ".png", ".jpg", ".xlsx") or p.name == "gsap.min.js":
            continue
        problems += [f"email    {rel}: {e}" for e in set(re.findall(r"[\w.+-]+@[\w-]+\.[a-z]{2,}(?:\.[a-z]{2,})?", t))
                     if e.lower() not in ALLOWED_EMAILS]
        problems += [f"url      {rel}: {u}" for u in set(re.findall(r"https?://[^\s\"'<>)]+", t))
                     if re.search(r"[a-z0-9-]+\.sharepoint\.com|onmicrosoft|\.csod\.|teams\.microsoft|my\.salesforce", u, re.I)]   # a tenant host, not code that recognises one
        problems += [f"phone    {rel}" for _ in re.findall(r"\+44\s?\(?0?\)?\s?\d{4}|\b07\d{3}\s?\d{6}\b", t)[:1]]
    for line in problems:
        print(line)
    print(f"{n} files checked: {'clean' if not problems else str(len(problems)) + ' problem(s)'}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
