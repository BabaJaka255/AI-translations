#!/usr/bin/env python3
"""Build the GitHub Pages hub from every hacks/<slug>/hack.json.

    python3 site/build_site.py [output_dir]      (default: _site)

Writes:
  index.html                   list of every hack
  hacks.json                   all hack.json files in one list
  hacks/<slug>/index.html      details, downloads and (when practical) an in-browser patcher
  hacks/<slug>/patches/...     copies of the patch files, so the patcher can fetch them
Needs only the Python standard library.
"""
import html
import json
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "_site"
REPO = os.environ.get("GITHUB_REPOSITORY", "BabaJaka255/AI-translations")
BRANCH = os.environ.get("SITE_BRANCH", "main")
REPO_URL = f"https://github.com/{REPO}"

# Above this, browsers struggle to hold the image in memory, so the page offers downloads only.
BROWSER_LIMIT = 512 * 1024 * 1024
FORMAT_PREFERENCE = ["bps", "ups", "xdelta", "vcdiff", "ppf", "ips", "aps"]
DISC_PLATFORMS = ("playstation", "pc engine cd", "sega cd", "mega cd", "saturn", "dreamcast", "gamecube")

TESTED = {
    "hardware": ("Tested on hardware", "good"),
    "emulator": ("Tested in an emulator", "ok"),
    "untested": ("Untested", "warn"),
}
SOURCE = {
    "verified": ("Source rebuilds the patch byte for byte", "good"),
    "unverified": ("Source included, build not verified", "warn"),
    "none": ("No source", "warn"),
}

e = html.escape


def load_hacks():
    hacks = []
    for f in sorted((ROOT / "hacks").glob("*/hack.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        d["_dir"] = f.parent
        d.setdefault("slug", f.parent.name)
        hacks.append(d)
    hacks.sort(key=lambda h: (h.get("platform", ""), h.get("name", "").lower()))
    return hacks


def human_size(n):
    if not n:
        return ""
    for unit in ("bytes", "KiB", "MiB", "GiB"):
        if n < 1024 or unit == "GiB":
            return f"{n:,} bytes" if unit == "bytes" else f"{n:.1f} {unit}".replace(".0 ", " ")
        n /= 1024


def is_disc(h):
    return any(p in h.get("platform", "").lower() for p in DISC_PLATFORMS)


def browser_patch(h):
    """The patch to offer in the browser, or None when the base image is too big."""
    base = h.get("base") or {}
    if not base or not base.get("size") or base["size"] > BROWSER_LIMIT:
        return None
    patches = [p for p in h.get("patches", []) if (h["_dir"] / p["file"]).is_file()]
    if not patches:
        return None
    rank = lambda p: FORMAT_PREFERENCE.index(p.get("format", "").lower()) if p.get("format", "").lower() in FORMAT_PREFERENCE else 99
    return sorted(patches, key=rank)[0]


def badge(label_kind):
    label, kind = label_kind
    return f'<span class="badge {kind}">{e(label)}</span>'


def doc_links(h):
    d, slug = h["_dir"], h["slug"]
    items = [
        ("README.md", "Full README"),
        ("src/BUILD.md", "Build from source"),
        ("docs/ENGINE_NOTES.md", "Engine notes"),
        ("DEVLOG.md", "Development log"),
    ]
    out = [f'<a href="{REPO_URL}/blob/{BRANCH}/hacks/{slug}/{p}">{e(t)}</a>' for p, t in items if (d / p).is_file()]
    if (d / "src").is_dir():
        out.append(f'<a href="{REPO_URL}/tree/{BRANCH}/hacks/{slug}/src">Source folder</a>')
    if (d / "docs").is_dir():
        out.append(f'<a href="{REPO_URL}/tree/{BRANCH}/hacks/{slug}/docs">Docs folder</a>')
    return out


def page(title, body, depth, head=""):
    up = "../" * depth
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<link rel="stylesheet" href="{up}style.css">
{head}</head>
<body>
<header class="top"><a class="home" href="{up}index.html">AI-translations</a><a href="{REPO_URL}">GitHub</a></header>
<main>
{body}
</main>
<footer>
Patches only: bring your own legally dumped game. Every hack here was made with substantial help from Claude (Anthropic); each one's development log says who did what.
In-browser patching by <a href="https://github.com/marcrobledo/RomPatcher.js">Rom Patcher JS</a> (MIT).
</footer>
</body>
</html>
"""


def index_page(hacks):
    platforms = sorted({h.get("platform", "") for h in hacks})
    buttons = '<button class="on" data-p="">All</button>' + "".join(
        f'<button data-p="{e(p)}">{e(p)}</button>' for p in platforms
    )
    cards = []
    for h in hacks:
        cards.append(f"""<a class="card" href="hacks/{e(h['slug'])}/index.html" data-p="{e(h.get('platform', ''))}">
<span class="platform">{e(h.get('platform', ''))}</span>
<span class="name">{e(h.get('name', h['slug']))}</span>
<span class="summary">{e(h.get('summary', ''))}</span>
<span class="meta">v{e(str(h.get('version', '')))} · {e(TESTED.get(h.get('tested_on'), ('', ''))[0])}</span>
</a>""")
    body = f"""<section class="intro">
<h1>AI-translations</h1>
<p class="lede">Collection of Claude-translated romhacks. Done mostly out of desperation. Use human translations when able.</p>
<p>Each hack has an English patch you can apply right here in your browser, plus everything needed to rebuild it or build on it:
the full source, the original and translated script, the engine notes and a log of how it was made. You need your own copy of the game;
no ROMs or disc images are hosted here.</p>
</section>
<nav class="filters" aria-label="Filter by platform">{buttons}</nav>
<section class="grid">
{''.join(cards)}
</section>
<script>
document.querySelectorAll('.filters button').forEach(function (b) {{
  b.addEventListener('click', function () {{
    document.querySelectorAll('.filters button').forEach(function (x) {{ x.classList.toggle('on', x === b); }});
    var p = b.getAttribute('data-p');
    document.querySelectorAll('.card').forEach(function (c) {{ c.hidden = p !== '' && c.getAttribute('data-p') !== p; }});
  }});
}});
</script>"""
    return page("AI-translations", body, 0)


PATCHER_HTML = """<div id="rom-patcher-container">
  <div class="rom-patcher-row margin-bottom" id="rom-patcher-row-file-rom">
    <div class="text-right"><label for="rom-patcher-input-file-rom" data-localize="yes">ROM file:</label></div>
    <div class="rom-patcher-container-input"><input type="file" id="rom-patcher-input-file-rom" class="empty" disabled /></div>
  </div>
  <div class="margin-bottom text-selectable text-mono text-muted" id="rom-patcher-rom-info">
    <div class="rom-patcher-row"><div class="text-right">CRC32:</div><div class="text-truncate"><span id="rom-patcher-span-crc32"></span></div></div>
    <div class="rom-patcher-row"><div class="text-right">MD5:</div><div class="text-truncate"><span id="rom-patcher-span-md5"></span></div></div>
    <div class="rom-patcher-row"><div class="text-right">SHA-1:</div><div class="text-truncate"><span id="rom-patcher-span-sha1"></span></div></div>
    <div class="rom-patcher-row" id="rom-patcher-row-info-rom"><div class="text-right">ROM:</div><div class="text-truncate"><span id="rom-patcher-span-rom-info"></span></div></div>
  </div>
  <div class="rom-patcher-row margin-bottom" id="rom-patcher-row-file-patch">
    <div class="text-right"><label for="rom-patcher-input-file-patch" data-localize="yes">Patch file:</label></div>
    <div class="rom-patcher-container-input"><select id="rom-patcher-select-patch"></select></div>
  </div>
  <div class="rom-patcher-row margin-bottom" id="rom-patcher-row-patch-description">
    <div class="text-right text-mono text-muted" data-localize="yes">Description:</div>
    <div class="text-truncate" id="rom-patcher-patch-description"></div>
  </div>
  <div class="rom-patcher-row margin-bottom text-selectable text-mono text-muted" id="rom-patcher-row-patch-requirements">
    <div class="text-right text-mono" id="rom-patcher-patch-requirements-type">ROM requirements:</div>
    <div class="text-truncate" id="rom-patcher-patch-requirements-value"></div>
  </div>
  <div class="text-center" id="rom-patcher-row-apply">
    <div id="rom-patcher-row-error-message" class="margin-bottom"><span id="rom-patcher-error-message"></span></div>
    <button id="rom-patcher-button-apply" data-localize="yes" disabled>Apply patch</button>
  </div>
</div>"""


def hack_page(h):
    slug, base = h["slug"], h.get("base") or {}
    bp = browser_patch(h)
    badges = " ".join(
        b for b in (
            badge(TESTED[h["tested_on"]]) if h.get("tested_on") in TESTED else "",
            badge(SOURCE[h["source"]]) if h.get("source") in SOURCE else "",
            badge(("AI-assisted", "ai")) if h.get("ai_assisted") else "",
        ) if b
    )

    rows = []
    if base:
        rows += [
            ("Required file", f"<code>{e(base.get('name', ''))}</code>"),
            ("Size", e(f"{base['size']:,} bytes ({human_size(base['size'])})") if base.get("size") else ""),
            ("Header", "yes" if base.get("header") else "none"),
            ("CRC32", f"<code>{e(base.get('crc32', ''))}</code>"),
            ("SHA-1", f"<code>{e(base.get('sha1', ''))}</code>"),
        ]
    req = "".join(f"<tr><th>{k}</th><td>{v}</td></tr>" for k, v in rows if v)

    dl = []
    for p in h.get("patches", []):
        exists = (h["_dir"] / p["file"]).is_file()
        name = Path(p["file"]).name
        size = human_size((h["_dir"] / p["file"]).stat().st_size) if exists else ""
        link = f'<a href="{e(p["file"])}" download>{e(name)}</a>' if exists else e(name)
        dl.append(f"<li>{link} <span class=\"muted\">{e(p.get('format', '').upper())} · {e(size)}</span></li>")
    for z in sorted((h["_dir"] / "patches").glob("*.zip")):
        rel = f"patches/{z.name}"
        if rel not in {p["file"] for p in h.get("patches", [])}:
            dl.append(f'<li><a href="{e(rel)}" download>{e(z.name)}</a> <span class="muted">release zip · {e(human_size(z.stat().st_size))}</span></li>')

    readme = f"{REPO_URL}/blob/{BRANCH}/hacks/{slug}/README.md"
    formats = [p.get("format", "").lower() for p in h.get("patches", [])]
    variant_note = (
        f'<p class="note">Each patch is for a different version of the game file. The <a href="{readme}">README</a> says which one to use.</p>'
        if len(formats) != len(set(formats)) else ""
    )
    if bp:
        out_name = Path(base.get("name", slug)).stem if is_disc(h) else f"{h.get('name', slug)} (English v{h.get('version', '')})"
        info = {
            "file": bp["file"],
            "name": f"{h.get('name', slug)} v{h.get('version', '')}",
            "description": h.get("summary", ""),
            "outputName": out_name,
        }
        if base.get("crc32"):
            info["inputCrc32"] = base["crc32"]
        disc_note = (
            "<p class=\"note\">Disc game: the patched file keeps the original's name so your .cue sheet still finds it. "
            "Check the README for which track or image to pick.</p>" if is_disc(h) else ""
        )
        patcher = f"""<section class="box">
<h2>Patch in your browser</h2>
<p>Pick your copy of <code>{e(base.get('name', 'the game'))}</code>. Nothing is uploaded: the patch is applied on your own computer.</p>
{disc_note}
{PATCHER_HTML}
</section>
<script src="rom-patcher-js/RomPatcher.webapp.js"></script>
<script>
window.addEventListener('load', function () {{
  try {{
    RomPatcherWeb.initialize({{ language: 'en', requireValidation: true, outputSuffix: false }}, {json.dumps(info)});
  }} catch (err) {{
    var c = document.getElementById('rom-patcher-container');
    c.textContent = /incompatible browser|RomPatcherWeb/i.test(err.message) ? 'Your browser is too old for the in-browser patcher. Download the patch below instead.' : err.message;
    c.classList.add('error');
  }}
}});
</script>"""
    elif base:
        patcher = f"""<section class="box">
<h2>How to patch</h2>
<p>This game's image is {e(human_size(base.get('size')))}, too large to patch reliably in a browser. Download a patch above and apply it with
<a href="https://github.com/jmacd/xdelta-gpl/releases">xdelta3</a>, xdelta UI or Delta Patcher. The <a href="{readme}">README</a> has the exact steps.</p>
</section>"""
    else:
        patcher = f'<section class="box"><h2>How to use</h2><p>See the <a href="{readme}">README</a>.</p></section>'

    results = [p for p in h.get("patches", []) if p.get("result_sha1")]
    result_line = ""
    if results:
        p = results[0]
        result_line = f'<p class="muted">Correctly patched result: CRC32 <code>{e(p.get("result_crc32", ""))}</code>, SHA-1 <code>{e(p["result_sha1"])}</code></p>'

    body = f"""<article>
<p class="platform">{e(h.get('platform', ''))} · {e(h.get('type', ''))}</p>
<h1>{e(h.get('name', slug))}</h1>
<p class="lede">{e(h.get('summary', ''))}</p>
<p class="badges"><span class="badge">v{e(str(h.get('version', '')))}</span> {badges}</p>
<div class="cols">
<section class="box">
<h2>What you need</h2>
{f'<table>{req}</table>' if req else '<p>No specific game file.</p>'}
</section>
<section class="box">
<h2>Downloads</h2>
<ul class="dl">{''.join(dl)}</ul>
{variant_note}
{result_line}
</section>
</div>
{patcher}
<section class="box">
<h2>Build on this</h2>
<p>Everything used to make this patch is in the repository: the build scripts and tools, the original and translated script,
extracted and edited graphics, engine notes with addresses, and a development log of how it was made, including what Claude did and what was tested by hand.</p>
<p class="links">{' · '.join(doc_links(h))}</p>
<p class="muted">Updated {e(h.get('updated', ''))}.</p>
</section>
</article>"""
    head = '<link rel="stylesheet" href="rom-patcher-js/style.css">\n' if bp else ""
    return page(f"{h.get('name', slug)} · AI-translations", body, 2, head)


def build():
    hacks = load_hacks()
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    shutil.copy(SITE / "style.css", OUT / "style.css")
    (OUT / ".nojekyll").write_text("")
    (OUT / "index.html").write_text(index_page(hacks), encoding="utf-8")
    manifest = [{k: v for k, v in h.items() if not k.startswith("_")} for h in hacks]
    (OUT / "hacks.json").write_text(json.dumps(manifest, indent=1, ensure_ascii=False), encoding="utf-8")
    for h in hacks:
        dest = OUT / "hacks" / h["slug"]
        if (h["_dir"] / "patches").is_dir():
            shutil.copytree(h["_dir"] / "patches", dest / "patches")
        dest.mkdir(parents=True, exist_ok=True)
        if browser_patch(h):
            shutil.copytree(SITE / "vendor" / "rom-patcher-js", dest / "rom-patcher-js")
        (dest / "index.html").write_text(hack_page(h), encoding="utf-8")
        print(f"{h['slug']}: {'browser patcher' if browser_patch(h) else 'download only'}")
    print(f"{len(hacks)} hacks -> {OUT}")


if __name__ == "__main__":
    build()
