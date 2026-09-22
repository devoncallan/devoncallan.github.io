#!/usr/bin/env python3
"""Regenerate index.html from the HTML files in tools/.

Run it directly, or let ./publish run it for you:

    python3 build.py

For each file in tools/ it reads the <title> and <meta name="description">
out of the file itself, checks site.json for any overrides, and writes a row
into index.html. It also makes sure each tool page starts with a doctype and
carries a noindex tag, so the pages render in standards mode and stay out of
search results. Nothing else in your files is touched.
"""

import html
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TOOLS = ROOT / "tools"
OVERRIDES = ROOT / "site.json"

SITE_TITLE = "Devon Callan"
SITE_EYEBROW = "UCSB · Materials"
SITE_LEDE = "Self-contained interactive explorers for experimental data."
SECTION_LABEL = "Data explorers"

NOINDEX = '<meta name="robots" content="noindex, nofollow">'


# --------------------------------------------------------------------------
# reading the tool pages
# --------------------------------------------------------------------------

def normalize(path: Path) -> None:
    """Ensure the page is a valid standalone document and is not indexed."""
    raw = path.read_text(encoding="utf-8", errors="replace")
    head = raw[:2000].lower()
    add = []
    if "<!doctype" not in head:
        add.append("<!doctype html>")
    if "charset" not in head:
        add.append('<meta charset="utf-8">')
    if 'name="robots"' not in head:
        add.append(NOINDEX)
    if not add:
        return
    metas = "\n".join(a for a in add if a != "<!doctype html>")
    doctype = re.match(r"\s*<!doctype[^>]*>[^\S\n]*\n?", raw, re.I)
    if "<head>" in raw[:2000]:
        # proper document: slot the tags inside the existing head
        out = raw.replace("<head>", "<head>\n" + metas, 1) if metas else raw
        if "<!doctype html>" in add:
            out = "<!doctype html>\n" + out
    elif doctype:
        # has a doctype but no explicit head: the doctype must stay the very
        # first thing in the file or the browser falls back to quirks mode
        cut = doctype.end()
        out = raw[:cut] + (metas + "\n" if metas else "") + raw[cut:]
    else:
        # fragment: a leading doctype is enough, the parser builds head/body
        out = "\n".join(add) + "\n" + raw
    path.write_text(out, encoding="utf-8")
    print(f"  normalized {path.name}: added {', '.join(a.split()[0].strip('<') for a in add)}")


def meta(raw: str, name: str) -> str:
    m = re.search(
        r'<meta\s+name=["\']%s["\']\s+content=["\'](.*?)["\']\s*/?>' % re.escape(name),
        raw, re.I | re.S)
    return html.unescape(m.group(1)).strip() if m else ""


def title_of(raw: str, path: Path) -> str:
    m = re.search(r"<title>(.*?)</title>", raw, re.I | re.S)
    if m:
        return html.unescape(re.sub(r"\s+", " ", m.group(1))).strip()
    return path.stem.replace("-", " ").replace("_", " ").title()


def updated(path: Path) -> datetime:
    """Last commit date for the file, or its modification time if uncommitted."""
    try:
        out = subprocess.run(
            ["git", "log", "-1", "--format=%cI", "--", str(path.relative_to(ROOT))],
            cwd=ROOT, capture_output=True, text=True, timeout=15).stdout.strip()
        if out:
            return datetime.fromisoformat(out).astimezone()
    except Exception:
        pass
    return datetime.fromtimestamp(path.stat().st_mtime).astimezone()


def size_of(path: Path) -> str:
    kb = path.stat().st_size / 1024
    return f"{kb/1024:.1f} MB" if kb >= 1024 else f"{kb:.0f} KB"


def collect() -> list[dict]:
    over = {}
    if OVERRIDES.exists():
        over = json.loads(OVERRIDES.read_text(encoding="utf-8")).get("tools", {})

    items = []
    for path in sorted(TOOLS.glob("*.html")):
        normalize(path)
        raw = path.read_text(encoding="utf-8", errors="replace")
        o = over.get(path.name, {})
        if o.get("hidden"):
            continue
        items.append({
            "file": path.name,
            "href": f"tools/{path.name}",
            "name": o.get("title") or title_of(raw, path),
            "desc": o.get("description") or meta(raw, "description"),
            "when": updated(path),
            "size": size_of(path),
        })
    # newest first, by the same date the row shows: the file's last commit
    # date, or its modification time while it is still uncommitted.
    items.sort(key=lambda i: -i["when"].timestamp())
    return items


# --------------------------------------------------------------------------
# the page
# --------------------------------------------------------------------------

def row(item: dict) -> str:
    e = html.escape
    desc = f'<p class="desc">{e(item["desc"])}</p>' if item["desc"] else ""
    w = item["when"]
    when = f"{w:%b} {w.day}, {w:%Y}"
    return f"""      <li class="row">
        <a class="hit" href="{e(item['href'])}">
          <span class="main">
            <span class="name">{e(item['name'])}</span>
            {desc}
          </span>
          <span class="meta">
            <span class="when">{e(when)}</span>
            <span class="size">{e(item['size'])}</span>
          </span>
          <svg class="go" viewBox="0 0 16 16" aria-hidden="true"><path d="M5.5 3.5 10 8l-4.5 4.5"/></svg>
        </a>
      </li>"""


AXIS = """<svg class="axis" viewBox="0 0 600 12" preserveAspectRatio="none" aria-hidden="true">
      <line class="base" x1="0" y1="11" x2="600" y2="11"/>
      <g class="tick">
        <line x1="0.5" y1="11" x2="0.5" y2="1"/><line x1="60" y1="11" x2="60" y2="6"/>
        <line x1="120" y1="11" x2="120" y2="6"/><line x1="180" y1="11" x2="180" y2="1"/>
        <line x1="240" y1="11" x2="240" y2="6"/><line x1="300" y1="11" x2="300" y2="6"/>
        <line x1="360" y1="11" x2="360" y2="1"/><line x1="420" y1="11" x2="420" y2="6"/>
        <line x1="480" y1="11" x2="480" y2="6"/><line x1="540" y1="11" x2="540" y2="1"/>
        <line x1="599.5" y1="11" x2="599.5" y2="6"/>
      </g>
    </svg>"""

CSS = """
/* Palette and type follow the explorer pages: paper ground, IBM Plex,
   hairline rules. Light only, matching their color-scheme:light. */
:root{
  color-scheme:light;
  --paper:#f7f6f3; --panel:#ffffff;
  --ink:#1e2126; --soft:#5a616b; --faint:#8b9096;
  --rule:#d8d5cd; --grid:#e6e3dc;
  --accent:#1d68c4; --accent-soft:rgba(42,120,214,.08);
  --shadow:0 1px 2px rgba(30,33,38,.05);
}

*{box-sizing:border-box}
body{
  margin:0; background:var(--paper); color:var(--ink);
  font:400 15px/1.55 "IBM Plex Sans",system-ui,-apple-system,"Segoe UI",sans-serif;
  -webkit-font-smoothing:antialiased; text-rendering:optimizeLegibility;
}
.page{max-width:820px; margin:0 auto; padding-block:56px 56px; padding-left:20px; padding-right:20px}

/* ---- header ---- */
.eyebrow{
  font:500 11px/1 "IBM Plex Mono",ui-monospace,Menlo,monospace;
  letter-spacing:.14em; text-transform:uppercase; color:var(--faint); margin:0 0 14px;
}
h1{
  font-size:29px; font-weight:600; letter-spacing:-.018em; line-height:1.12;
  margin:0 0 12px; text-wrap:balance;
}
.lede{max-width:63ch; color:var(--soft); font-size:15.5px; margin:0}
.axis{display:block; width:100%; height:12px; margin:30px 0 0; overflow:visible}
.axis .base{stroke:var(--rule); stroke-width:1}
.axis .tick line{stroke:var(--rule); stroke-width:1}

/* ---- list ---- */
.section{
  display:flex; align-items:baseline; gap:10px; margin:34px 0 10px;
  font:500 11px/1 "IBM Plex Mono",ui-monospace,Menlo,monospace;
  letter-spacing:.13em; text-transform:uppercase; color:var(--faint);
}
.section .count{color:var(--rule)}
.list{list-style:none; margin:0; padding:0; border-top:1px solid var(--rule)}
.row{border-bottom:1px solid var(--rule)}
.hit{
  display:grid; grid-template-columns:minmax(0,1fr) auto 16px;
  align-items:baseline; gap:0 20px;
  padding:18px 14px 18px 12px; margin:0 -12px;
  text-decoration:none; color:inherit; border-radius:7px;
  transition:background .13s ease, box-shadow .13s ease;
}
.hit:hover,.hit:focus-visible{background:var(--panel); box-shadow:var(--shadow)}
.hit:focus-visible{outline:2px solid var(--accent); outline-offset:1px}
.main{min-width:0}
.name{
  display:block; font-size:17.5px; font-weight:600; letter-spacing:-.012em;
  line-height:1.3; transition:color .13s ease;
}
.hit:hover .name,.hit:focus-visible .name{color:var(--accent)}
.desc{margin:5px 0 0; font-size:14px; line-height:1.5; color:var(--soft); max-width:56ch}
.meta{
  display:flex; flex-direction:column; align-items:flex-end; gap:3px;
  font:400 11.5px/1.4 "IBM Plex Mono",ui-monospace,Menlo,monospace;
  color:var(--faint); font-variant-numeric:tabular-nums; white-space:nowrap; padding-top:4px;
}
.meta .size{color:var(--rule)}
.go{
  width:16px; height:16px; align-self:start; margin-top:7px; fill:none;
  stroke:var(--rule); stroke-width:1.6; stroke-linecap:round; stroke-linejoin:round;
  transition:stroke .13s ease, transform .13s ease;
}
.hit:hover .go,.hit:focus-visible .go{stroke:var(--accent); transform:translateX(2px)}

.empty{
  border:1px dashed var(--rule); border-radius:9px; padding:22px;
  color:var(--faint); font-size:14px;
}
.empty code{
  font-family:"IBM Plex Mono",ui-monospace,Menlo,monospace; font-size:13px;
  background:var(--accent-soft); color:var(--accent); padding:1px 5px; border-radius:4px;
}

@media (max-width:620px){
  .page{padding-block:40px 40px}
  h1{font-size:25px}
  .hit{
    grid-template-columns:minmax(0,1fr) auto; gap:2px 14px;
    padding:16px 12px; margin:0 -12px;
  }
  .meta{
    grid-column:1/-1; flex-direction:row; align-items:baseline; gap:12px;
    padding-top:9px; justify-content:flex-start;
  }
  .go{display:none}
  .desc{max-width:none}
}
@media (prefers-reduced-motion:reduce){*{transition:none!important}}
"""


def render(items: list[dict]) -> str:
    rows = "\n".join(row(i) for i in items)
    if not items:
        body = ('    <div class="empty">No pages yet. Drop an HTML file into '
                '<code>tools/</code> and run <code>./publish</code>.</div>')
    else:
        body = f'    <ul class="list">\n{rows}\n    </ul>'
    n = len(items)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
{NOINDEX}
<meta name="description" content="Interactive data explorers from Devon Callan's work at UCSB, shared for collaborators.">
<meta name="color-scheme" content="light">
<title>{html.escape(SITE_TITLE)} · Data Explorers</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>{CSS}</style>
</head>
<body>
<div class="page">
  <header>
    <p class="eyebrow">{html.escape(SITE_EYEBROW)}</p>
    <h1>{html.escape(SITE_TITLE)}</h1>
    <p class="lede">{html.escape(SITE_LEDE)}</p>
    {AXIS}
  </header>

  <main>
    <h2 class="section">{html.escape(SECTION_LABEL)} <span class="count">{n:02d}</span></h2>
{body}
  </main>
</div>
</body>
</html>
"""


def main() -> int:
    if not TOOLS.exists():
        TOOLS.mkdir(parents=True)
    items = collect()
    (ROOT / "index.html").write_text(render(items), encoding="utf-8")
    print(f"index.html written — {len(items)} page(s):")
    for i in items:
        print(f"  {i['when']:%Y-%m-%d}  {i['size']:>8}  {i['name']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
