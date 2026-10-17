"""
make_posters.py - small-screen preview images for the live demos

Under 700 px wide the shell shows a still of each demo plus an Open full screen
link instead of the iframe. This script takes those stills with headless Chrome
or Edge and saves them as WebP in assets/img/.

    python -m http.server 8765        # in the repo root, in another terminal
    python tools/make_posters.py      # needs Pillow: pip install pillow
"""
import argparse
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SHOTS = [
    # name, path + hash, width, height
    ("training-designer-poster", "demos/training-designer/index.html", 1280, 800),
    ("skills-matrix-poster", "demos/skills-matrix/index.html#site=alder&gap=1", 1280, 800),
    ("asset-risk-poster", "demos/asset-risk/index.html#film/t=77", 1280, 720),
    ("training-store-poster", "demos/training-store/index.html", 1280, 800),
    ("procedure-library-poster", "demos/procedure-library/index.html#strip", 1280, 800),
]
CANDIDATES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    "google-chrome", "chromium", "chromium-browser", "msedge",
]


def browser():
    for c in CANDIDATES:
        if Path(c).exists() or shutil.which(c):
            return c
    raise SystemExit("No Chrome or Edge found")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://127.0.0.1:8765/")
    args = ap.parse_args()
    exe = browser()
    out_dir = ROOT / "assets" / "img"
    with tempfile.TemporaryDirectory() as tmp:
        for name, path, w, h in SHOTS:
            png = Path(tmp) / f"{name}.png"
            subprocess.run([exe, "--headless=new", "--disable-gpu", "--hide-scrollbars", f"--window-size={w},{h}",
                            "--virtual-time-budget=6000", f"--user-data-dir={tmp}{os.sep}profile",
                            f"--screenshot={png}", args.base + path], check=True, capture_output=True)
            img = Image.open(png).convert("RGB")
            dest = out_dir / f"{name}.webp"
            img.save(dest, "WEBP", quality=78, method=6)
            print(f"{dest.relative_to(ROOT)}  {img.size[0]}x{img.size[1]}  {dest.stat().st_size / 1024:,.0f} KB")


if __name__ == "__main__":
    main()
