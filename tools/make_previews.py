"""
make_previews.py - looping preview clips and hero thumbnails for the five demos

Drives each demo through a few real states in headless Chrome (over the DevTools
protocol), screenshots each state, and stitches the frames into a looping
animated WebP for the launch card. Also writes a small static thumbnail per demo
for the hero index.

    python -m http.server 8765        # in the repo root, in another terminal
    python tools/make_previews.py     # needs: pip install pillow websocket-client

Writes assets/img/<demo>-preview.webp and assets/img/<demo>-thumb.webp.
"""
import base64
import io
import json
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

import websocket
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "img"
BASE = "http://127.0.0.1:8765/"
PORT = 9333
W, H = 1280, 800
CANDIDATES = [r"C:\Program Files\Google\Chrome\Application\chrome.exe",
              r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
              "google-chrome", "chromium", "msedge"]

# which captured frame becomes the hero thumbnail
THUMB_FRAME = {"training-designer": 0, "skills-matrix": 1, "asset-risk": 3, "training-store": 1, "procedure-library": 1}

CLICK_TEXT = """(t => { const b = [...document.querySelectorAll('button, a')].find(x => x.textContent.trim().startsWith(t)); if (b) b.click(); return !!b; })(%s)"""

# Each step: ("nav", path) | ("js", code) | ("wait", ms) | ("shot", hold_ms)
DEMOS = {
    "training-designer": (W, H, [
        ("nav", "demos/training-designer/index.html"), ("js", "localStorage.clear()"),
        ("nav", "demos/training-designer/index.html"), ("wait", 1200), ("shot", 1400),
        ("js", CLICK_TEXT % json.dumps("Start course")), ("wait", 900), ("shot", 1200),
        ("js", CLICK_TEXT % json.dumps("What is gas chromatography?")), ("wait", 900), ("js", "window.scrollBy(0, 700)"), ("wait", 500), ("shot", 1200),
        ("js", CLICK_TEXT % json.dumps("Inside the instrument")), ("wait", 900), ("js", "window.scrollBy(0, 400)"), ("wait", 500), ("shot", 1200),
        ("js", CLICK_TEXT % json.dumps("Check your knowledge")), ("wait", 900), ("shot", 1400),
        ("js", "localStorage.clear()"),
    ]),
    "skills-matrix": (W, H, [
        ("nav", "demos/skills-matrix/index.html"), ("wait", 1200), ("shot", 1200),
        ("js", "location.hash='site=alder&gap=1'; dispatchEvent(new HashChangeEvent('hashchange')); location.reload()"), ("wait", 1500), ("shot", 1300),
        ("js", "location.hash='site=brook&train=1&gap=1'; location.reload()"), ("wait", 1500), ("shot", 1300),
        ("js", "location.hash='cls=hplc&level=3'; location.reload()"), ("wait", 1500), ("shot", 1100),
        ("js", "document.querySelector('th.rowh button').click()"), ("wait", 600), ("shot", 1300),
    ]),
    "asset-risk": (W, 720, [
        ("nav", "demos/asset-risk/index.html#film/t=13"), ("wait", 1500), ("shot", 1100),
        ("js", "location.hash='#film/t=24'"), ("wait", 1200), ("shot", 1100),
        ("js", "location.hash='#film/t=40'"), ("wait", 1200), ("shot", 1100),
        ("js", "location.hash='#film/t=59'"), ("wait", 1200), ("shot", 1100),
        ("js", "location.hash='#film/t=77'"), ("wait", 1200), ("shot", 1300),
        ("js", "location.hash='#explorer/estate'"), ("wait", 1200), ("shot", 1300),
    ]),
    "training-store": (W, H, [
        ("nav", "demos/training-store/index.html"), ("js", "localStorage.clear()"),
        ("nav", "demos/training-store/index.html"), ("wait", 1200), ("shot", 1100),
        ("js", "(q => { q.value = 'AB500'; q.dispatchEvent(new Event('input')); })(document.getElementById('q'))"), ("wait", 600), ("shot", 1500),
        ("js", "document.querySelector('button.add').click(); document.querySelectorAll('button.add')[1].click()"), ("wait", 600), ("shot", 1200),
        ("js", "document.getElementById('tab-validation').click()"), ("wait", 600), ("shot", 1100),
        ("js", "(q => { q.value = 'centrifuge'; q.dispatchEvent(new Event('input')); document.getElementById('tab-training').click(); })(document.getElementById('q'))"), ("wait", 600), ("shot", 1200),
        ("js", "localStorage.clear()"),
    ]),
    "procedure-library": (W, H, [
        ("nav", "demos/procedure-library/index.html#index"), ("wait", 1500), ("shot", 1300),
        ("js", "document.getElementById('t-strip').click()"), ("wait", 800), ("shot", 1500),
        ("js", "document.querySelectorAll('.scroll')[1].scrollTop = 220"), ("wait", 400), ("shot", 1300),
        ("js", "document.getElementById('t-pack').click()"), ("wait", 600), ("shot", 1200),
    ]),
}


class Page:
    def __init__(self, ws_url):
        self.ws = websocket.create_connection(ws_url, timeout=30, suppress_origin=True)
        self.n = 0
        self.call("Page.enable")
        self.call("Emulation.setDeviceMetricsOverride", width=W, height=H, deviceScaleFactor=1, mobile=False)

    def call(self, method, **params):
        self.n += 1
        self.ws.send(json.dumps({"id": self.n, "method": method, "params": params}))
        while True:
            msg = json.loads(self.ws.recv())
            if msg.get("id") == self.n:
                if "error" in msg:
                    raise RuntimeError(f"{method}: {msg['error']}")
                return msg.get("result", {})

    def js(self, code):
        return self.call("Runtime.evaluate", expression=code, awaitPromise=True, returnByValue=True)

    def nav(self, url):
        self.call("Page.navigate", url=url)
        for _ in range(100):
            time.sleep(0.1)
            r = self.js("document.readyState").get("result", {}).get("value")
            if r == "complete":
                return

    def shot(self, w, h):
        self.call("Emulation.setDeviceMetricsOverride", width=w, height=h, deviceScaleFactor=1, mobile=False)
        data = self.call("Page.captureScreenshot", format="png")["data"]
        return Image.open(io.BytesIO(base64.b64decode(data))).convert("RGB")


def browser():
    for c in CANDIDATES:
        if Path(c).exists() or shutil.which(c):
            return c
    sys.exit("No Chrome or Edge found")


def main():
    only = sys.argv[1:]
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        proc = subprocess.Popen([browser(), "--headless=new", "--disable-gpu", "--hide-scrollbars", f"--remote-debugging-port={PORT}",
                                 f"--user-data-dir={tmp}", f"--window-size={W},{H}", "about:blank"],
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            for _ in range(50):
                try:
                    targets = json.load(urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json/list"))
                    page = next(t for t in targets if t["type"] == "page")
                    break
                except Exception:
                    time.sleep(0.2)
            p = Page(page["webSocketDebuggerUrl"])
            for name, (w, h, steps) in DEMOS.items():
                if only and name not in only:
                    continue
                frames, holds = [], []
                p.call("Emulation.setDeviceMetricsOverride", width=w, height=h, deviceScaleFactor=1, mobile=False)
                for kind, arg in steps:
                    if kind == "nav":
                        p.nav(BASE + arg)
                    elif kind == "js":
                        p.js(arg)
                        time.sleep(0.15)
                    elif kind == "wait":
                        time.sleep(arg / 1000)
                    elif kind == "shot":
                        frames.append(p.shot(w, h).resize((w * 3 // 4, h * 3 // 4), Image.LANCZOS))
                        holds.append(arg)
                prev = OUT / f"{name}-preview.webp"
                frames[0].save(prev, "WEBP", save_all=True, append_images=frames[1:], duration=holds, loop=0, quality=72, method=6)
                thumb = OUT / f"{name}-thumb.webp"
                frames[THUMB_FRAME.get(name, 0)].resize((480, 480 * h // w), Image.LANCZOS).save(thumb, "WEBP", quality=78, method=6)
                print(f"{prev.relative_to(ROOT)}  {len(frames)} frames  {prev.stat().st_size / 1024:,.0f} KB   "
                      f"{thumb.relative_to(ROOT)} {thumb.stat().st_size / 1024:,.0f} KB")
        finally:
            proc.terminate()
            proc.wait(timeout=10)


if __name__ == "__main__":
    main()
