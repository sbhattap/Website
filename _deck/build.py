"""Build deck/index.html from the slide files in _deck/.

    python _deck/build.py

Jekyll skips folders that start with "_", so _deck/ is not published.
"""

import json
import re
import shutil
from pathlib import Path

SRC = Path(__file__).parent
OUT = SRC.parent / "deck"

# Uploaded images in the Slides artifact -> local files in _deck/img/
BLOBS = {
    "/_blob/d8e76cecaaa7c5fbf979efd888887802": "img/penguin-sunset.jpg",
    "/_blob/887d18b147fac6620b3b0cf997540e11": "img/jokulsarlon.jpg",
}

PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="Three data science projects: sepsis mortality benchmarking, clinical QA dataset artifacts, and an agentic recommender.">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?{fonts}&display=swap">
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
html, body {{ height: 100%; background: #1d3129; overflow: hidden; }}
#stage {{ position: absolute; width: 1920px; height: 1080px; left: 50%; top: 50%; transform-origin: center; }}
section {{ position: absolute; inset: 0; width: 1920px; height: 1080px; overflow: hidden;
  display: flex; flex-direction: column; font-size: 32px; line-height: 1.4; }}
/* Slides set display inline, so hiding needs !important */
body:not(.stack) section:not(.on) {{ display: none !important; }}
/* In the slide format a div with no display is a column; display:flex is a row */
section div:not([style*="display"]) {{ display: flex; flex-direction: column; }}
section aside {{ display: none; }}
h1, h2, h3 {{ font-weight: 600; }}
ul, ol {{ padding-left: 1.2em; }}
li + li {{ margin-top: 6px; }}
a {{ color: inherit; text-underline-offset: 4px; }}
table {{ border-collapse: collapse; }}
th, td {{ padding: 0.35em 0.6em; border-bottom: 1px solid currentColor; border-color: rgba(128,128,128,0.35); vertical-align: top; }}
th {{ font-weight: 600; }}
img {{ display: block; }}
#nav {{ position: fixed; right: 16px; bottom: 12px; font: 14px 'IBM Plex Mono', monospace;
  color: #acb5a8; display: flex; gap: 12px; align-items: center; z-index: 2; }}
#nav button {{ background: #263e35; border: 1px solid #66715f; color: #f7f6f0; border-radius: 6px;
  width: 36px; height: 30px; font: inherit; cursor: pointer; }}
#nav a {{ color: #acb5a8; }}
/* Phones: show every slide in one scrolling column */
body.stack {{ overflow-y: auto; overflow-x: hidden; }}
body.stack #stage {{ position: static; transform: none; width: auto; height: auto; }}
body.stack .wrap {{ position: relative; overflow: hidden; margin: 0 auto 8px; }}
body.stack section {{ transform-origin: top left; }}
body.stack #nav {{ display: none; }}
</style>
</head>
<body>
<div id="stage">
{slides}
</div>
<div id="nav"><a href="/projects.html">sbhatta.org</a><button id="prev" aria-label="Previous slide">&larr;</button><span id="count"></span><button id="next" aria-label="Next slide">&rarr;</button></div>
<script>
const stage = document.getElementById('stage');
const slides = [...stage.querySelectorAll('section')];
let i = 0;
function show(n) {{
  i = Math.max(0, Math.min(slides.length - 1, n));
  slides.forEach((s, k) => s.classList.toggle('on', k === i));
  document.getElementById('count').textContent = (i + 1) + ' / ' + slides.length;
  history.replaceState(null, '', '#' + (i + 1));
}}
function fit() {{
  const stack = innerWidth < 760 || innerHeight > innerWidth * 1.1;
  document.body.classList.toggle('stack', stack);
  if (stack) {{
    const w = document.documentElement.clientWidth;  // excludes the scrollbar
    const s = w / 1920;
    slides.forEach(sec => {{
      if (!sec.parentElement.classList.contains('wrap')) {{
        const wrap = document.createElement('div'); wrap.className = 'wrap';
        sec.before(wrap); wrap.append(sec);
      }}
      sec.parentElement.style.width = w + 'px';
      sec.parentElement.style.height = (1080 * s) + 'px';
      sec.style.transform = 'scale(' + s + ')';
    }});
  }} else {{
    document.querySelectorAll('.wrap').forEach(w => {{ w.replaceWith(w.firstChild); }});
    slides.forEach(sec => sec.style.transform = '');
    const s = Math.min(innerWidth / 1920, innerHeight / 1080);
    stage.style.transform = 'translate(-50%, -50%) scale(' + s + ')';
  }}
}}
document.getElementById('prev').onclick = () => show(i - 1);
document.getElementById('next').onclick = () => show(i + 1);
addEventListener('keydown', e => {{
  if (['ArrowRight', 'PageDown', ' '].includes(e.key)) {{ e.preventDefault(); show(i + 1); }}
  if (['ArrowLeft', 'PageUp'].includes(e.key)) {{ e.preventDefault(); show(i - 1); }}
  if (e.key === 'Home') show(0);
  if (e.key === 'End') show(slides.length - 1);
}});
stage.addEventListener('click', e => {{
  if (document.body.classList.contains('stack') || e.target.closest('a')) return;
  show(e.clientX > innerWidth / 2 ? i + 1 : i - 1);
}});
let x0 = null;
addEventListener('touchstart', e => x0 = e.touches[0].clientX, {{ passive: true }});
addEventListener('touchend', e => {{
  if (x0 === null || document.body.classList.contains('stack')) return;
  const dx = e.changedTouches[0].clientX - x0;
  if (Math.abs(dx) > 40) show(dx < 0 ? i + 1 : i - 1);
  x0 = null;
}});
document.querySelectorAll('a[href^="http"]').forEach(a => {{ a.target = '_blank'; a.rel = 'noopener'; }});
addEventListener('resize', fit);
fit();
show((parseInt(location.hash.slice(1)) || 1) - 1);
</script>
</body>
</html>
"""


def main() -> None:
    deck = json.loads((SRC / "deck.json").read_text())
    fonts = "&".join(re.search(r"family=[^&]+", f["href"]).group(0)
                     for f in deck["faces"].values())
    slides = []
    for sid in deck["order"]:
        html = (SRC / "slides" / f"{sid}.html").read_text().strip()
        for blob, path in BLOBS.items():
            html = html.replace(blob, path)
        slides.append(html)

    OUT.mkdir(exist_ok=True)
    shutil.copytree(SRC / "img", OUT / "img", dirs_exist_ok=True)
    title = deck["title"].replace("—", "·")
    (OUT / "index.html").write_text(PAGE.format(title=title, fonts=fonts, slides="\n".join(slides)))
    print(f"wrote {OUT / 'index.html'} ({len(slides)} slides)")


if __name__ == "__main__":
    main()
