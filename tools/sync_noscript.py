"""
sync_noscript.py - rewrite the crawler copy in index.html from content/case-studies.json

The page renders its copy from the JSON at load. This keeps a plain-HTML copy
of the same prose inside <noscript> (between the noscript:start/end markers)
for crawlers and for anyone without JavaScript. Run after every copy edit.

    python tools/sync_noscript.py
"""
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
START, END = "<!-- noscript:start", "<!-- noscript:end -->"


def t(s):
    s = html.escape(s, quote=False)
    s = re.sub(r"\{\{CONFIRM:([^}]*)\}\}", r"\1 (to confirm)", s)
    return re.sub(r"\{\{PLACEHOLDER:([^}]*)\}\}", r"[placeholder: \1]", s)


def main():
    d = json.loads((ROOT / "content" / "case-studies.json").read_text(encoding="utf-8"))
    h, out = d["hero"], []
    out.append('<div class="wrap static">')
    out.append(f"<h1>{t(h['name'])}</h1>")
    out += [f"<p>{t(p)}</p>" for p in h["pitch"]]
    if h.get("proof"):
        out.append(f"<p>{t(h['proof'])}</p>")
    out.append(f'<p><a href="{h["links"][0]["href"]}">{t(h["links"][0]["label"])}</a></p>')
    p = d["pattern"]
    out.append(f"<h2>{t(p['title'])}</h2>")
    out.append(f"<p>{t(p['intro'])}</p>")
    out.append("<ul>")
    out += [f"<li><strong>{t(s['title'])}.</strong> {t(s['text'])}</li>" for s in p["steps"]]
    out.append("</ul>")
    for cs in d["caseStudies"]:
        out.append(f'<article id="{cs["id"]}-static">')
        out.append(f"<h2>{t(cs['title'])}</h2>")
        out.append(f"<p><em>{t(cs['pitch'])}</em></p>")
        for head, key in (("Context", "context"), ("What I built", "built"), ("How", "how")):
            out.append(f"<h3>{head}</h3>")
            out += [f"<p>{t(x)}</p>" for x in cs[key]]
        out.append("<h3>Outcome</h3>")
        out.append("<ul>")
        out += [f"<li>{t(x)}</li>" for x in cs["outcome"]]
        out.append("</ul>")
        pn = cs["panel"]
        link = f' <a href="{pn["src"]}">Open the demo</a>' if pn.get("src") else ""
        out.append(f"<p>{'Demo' if pn['type'] == 'live' else 'Visual'}: {t(pn['alt'])}{link}</p>")
        out.append("</article>")
    a = d["alsoBuilt"]
    out.append(f"<h2>{t(a['title'])}</h2>")
    out.append("<ul>")
    out += [f"<li><strong>{t(x['title'])}.</strong> {t(x['text'])}</li>" for x in a["tiles"]]
    out.append("</ul>")
    c = d["contact"]
    out.append(f"<h2>{t(c['title'])}</h2>")
    out.append(f"<p>{t(c['intro'])}</p>")
    out.append(f'<p>Email: <a href="mailto:{c["email"]}">{c["email"]}</a></p>')
    out.append(f'<p><a href="{c["cv"]}">Download CV (PDF)</a></p>')
    if c.get("linkedin"):
        out.append(f'<p><a href="{c["linkedin"]}">LinkedIn</a></p>')
    out.append("</div>")

    page = (ROOT / "index.html").read_text(encoding="utf-8")
    i, j = page.index(START), page.index(END)
    i = page.index("\n", i) + 1
    page = page[:i] + "\n".join(out) + "\n" + page[j:]
    (ROOT / "index.html").write_text(page, encoding="utf-8")
    print(f"index.html: noscript copy refreshed ({len(out)} lines)")


if __name__ == "__main__":
    main()
