import html, json, re, shutil
from pathlib import Path
from markdown_it import MarkdownIt

HERE = Path(__file__).parent
TUT = HERE.parent.parent  # qaoa_tutorial/
BLOG = TUT / "slide_version"  # output folder
BACKUP = TUT  # the Fourier + diffusion tutorial the slide version was built from
STAGING = BLOG
old_html = (BACKUP / "qaoa_hamming_cube.html").read_text(encoding="utf-8")
old_plain = (BACKUP / "QAOAOnTheHammingCube").read_text(encoding="utf-8")
footer = (HERE.parent / "qaoa_lukaslatentspace_v3" / "footer.txt").read_text(encoding="utf-8").rstrip("\n")
src = (HERE / "post.md").read_text(encoding="utf-8")
data = json.loads((HERE / "data.json").read_text(encoding="utf-8"))

# ---------- the problem and the cube stay as they are, only the hand-over sentence changes
OLD_T = "Next we will look at the frequencies of this graph, which make the mixer's action particularly simple."
NEW_T = "Both are just $2^n \\times 2^n$ matrices, and as we will see now, the answer to Problem 1 is hidden in one of them."
def cut(text, start, end):
    a, b = text.index(start), text.index(end)
    part = text[a:b].rstrip("\n")
    assert part.count(OLD_T) == 1
    return part.replace(OLD_T, NEW_T)
stage_plain = cut(old_plain, "## The problem", "## Fourier analysis on the cube")
stage_html = cut(old_html, "<h2>The problem</h2>", "<h2>Fourier analysis on the cube</h2>")

# ---------- 1. plain-text post in the LukasLatentSpace format
marker = re.compile(r"^<!-- (FIG|TOY):[a-z0-9]+ -->\n\n?", re.M)
assert src.count("<!-- STAGE -->") == 1
plain = marker.sub("", src.replace("<!-- STAGE -->", stage_plain)).rstrip("\n") + "\n" + footer + "\n"

# ---------- 2. Markdown -> HTML with math protected
fence = re.compile(r"```.*?```", re.S)
mathre = re.compile(r"\$\$.+?\$\$|\$[^$\n]+?\$", re.S)
store = []
def protect(text):
    out, pos = [], 0
    sub = lambda t: mathre.sub(lambda m: (store.append(m.group(0)), f"@@M{len(store)-1}@@")[1], t)
    for f in fence.finditer(text):
        out.append(sub(text[pos:f.start()])); out.append(f.group(0)); pos = f.end()
    out.append(sub(text[pos:]))
    return "".join(out)
md = MarkdownIt("commonmark", {"html": True}).enable("table")
body = md.render(protect(src))
body = re.sub(r"@@M(\d+)@@", lambda m: html.escape(store[int(m.group(1))], quote=False), body)
body = body.replace("<table>", '<div class="tablewrap"><table>').replace("</table>", "</table></div>")
body = re.sub(r"<h1>(.*?)</h1>", r'<h1 id="top">\1</h1>', body, count=1)
assert body.count("<!-- STAGE -->") == 1
body = body.replace("<!-- STAGE -->", stage_html)

toy_slide = '''<p>You can play with this yourself. Move $s$ and watch the levels and the ground state, or press Play and let the slide run.</p>
<div class="toy" id="toySlide">
  <div class="toy-head"><span><strong>Toy 1.</strong> Sliding from the cube to the cut on the prism</span></div>
  <div class="controls">
    <div class="slider"><label for="slS">s</label><input type="range" id="slS" min="0" max="100" value="0"><output id="slSOut" for="slS"></output></div>
    <button type="button" class="btn" id="slPlay">Play</button>
  </div>
  <div class="readouts">
    <div class="ro"><span class="k">Gap at this s</span><span class="val" id="slGap"></span></div>
    <div class="ro"><span class="k">Smallest gap on the slide</span><span class="val" id="slMin"></span></div>
    <div class="ro"><span class="k">P(maximum cut)</span><span class="val" id="slP"></span></div>
    <div class="ro"><span class="k">Expected cut</span><span class="val" id="slE"></span></div>
  </div>
  <div class="two">
    <div>
      <div class="panel-label">Energy levels of H(s)</div>
      <svg class="plot" id="slLevels" viewBox="0 0 300 204" role="img" aria-label="The eight energy levels of H(s) that the slide can reach, plotted against s, with the gap marked at the current s"></svg>
      <p class="caption">The 8 levels the slide can reach. Teal: the ground state. Dark: the next level up. The blue bar is the gap.</p>
    </div>
    <div>
      <div class="panel-label">Ground state: what you would measure</div>
      <svg class="plot" id="slHist" viewBox="0 0 300 204" role="img" aria-label="Probability of each cut value when the ground state of H(s) is measured, compared with random guessing"></svg>
      <p class="caption">Probability of each cut value, the maximum cut in plum. Dashed outlines: random guessing. Cuts of 1 and 2 are impossible on the prism.</p>
    </div>
  </div>
</div>'''

toy_walk = '''<p>Again, you can play with it. Choose the number of layers $p$ and the total time $T$ of the slide, and compare the slide with QAOA's tuned angles. The button jumps to the best $T$ for the current $p$. Fun fact on the side: at short times the chopped slide can even beat the fine one (at $p = 4$ and $T \\approx 4.6$, compare the teal and the gray curve). Being sloppy about the slide is not always bad, and that is the first hint at what QAOA does.</p>
<div class="toy" id="toyWalk">
  <div class="toy-head"><span><strong>Toy 2.</strong> Walk slowly, or walk cleverly</span></div>
  <div class="controls">
    <div class="slider"><label for="wkP">p</label><input type="range" id="wkP" min="1" max="8" value="4"><output id="wkPOut" for="wkP"></output></div>
    <div class="slider"><label for="wkT">T</label><input type="range" id="wkT" min="0" max="400" value="93"><output id="wkTOut" for="wkT"></output></div>
    <button type="button" class="btn" id="wkBest">Best T</button>
  </div>
  <div class="readouts">
    <div class="ro"><span class="k">Slide: P(maximum cut)</span><span class="val" id="wkSlideP"></span></div>
    <div class="ro"><span class="k">Slide: expected cut</span><span class="val" id="wkSlideE"></span></div>
    <div class="ro"><span class="k">QAOA, tuned: P(maximum cut)</span><span class="val" id="wkQaoaP"></span></div>
    <div class="ro"><span class="k">QAOA, tuned: expected cut</span><span class="val" id="wkQaoaE"></span></div>
    <div class="ro"><span class="k">Fine slide (p = 40) at this T</span><span class="val" id="wkFineP"></span></div>
  </div>
  <div class="two">
    <div>
      <div class="panel-label">Angles per layer</div>
      <svg class="plot" id="wkAngles" viewBox="0 0 300 204" role="img" aria-label="Angles gamma and beta for every layer: bars for the slide, dark ticks for the tuned QAOA angles"></svg>
      <p class="caption">Bars: the slide, teal for the cost angle γ and plum for the mixer angle β. Dark ticks: QAOA's tuned angles.</p>
    </div>
    <div>
      <div class="panel-label">P(maximum cut) against T</div>
      <svg class="plot" id="wkCurve" viewBox="0 0 300 204" role="img" aria-label="Probability of a maximum cut against the total time T for the slide with p layers, a fine slide with 40 layers, and QAOA with tuned angles"></svg>
      <p class="caption">Teal: the slide with p layers, faint where its pieces get longer than π/2. Gray: a fine slide with 40 layers. Dashed blue: QAOA with p tuned layers. Dotted: random guessing.</p>
    </div>
  </div>
</div>'''

for key, snippet in {"TOY:slide": toy_slide, "TOY:walk": toy_walk}.items():
    tag = f"<!-- {key} -->"
    assert body.count(tag) == 1, key
    body = body.replace(tag, snippet)

lines = footer.splitlines()
foot_html = f'''<footer>
  <div class="dashes" aria-hidden="true">{lines[0]}</div>
  <p>{html.escape(lines[1])}<br>Google scholar: <a href="https://scholar.google.com/citations?user=aD3-DrQAAAAJ&amp;hl=de">https://scholar.google.com/citations?user=aD3-DrQAAAAJ&amp;hl=de</a></p>
</footer>'''

# ---------- 3. style: the current one without the removed canvases, plus the new plots
css = old_html[old_html.index("<style>") + len("<style>"):old_html.index("</style>")].strip("\n")
for rule in ("#walsh16 {", "#heat {", ".heat-legend {", ".heat-legend .ramp {"):
    css = "\n".join(l for l in css.splitlines() if not l.startswith(rule))
css = css.replace(
    "/* Layout: a single notebook column like a Markdown post on GitHub; teal and plum stay the +1 / -1 colours of the figures. */",
    "/* Layout: a single notebook column like a Markdown post on GitHub; teal marks the ground state and the slide, plum the maximum cut and the mixer angle. */")
css += '''

/* The slide and its circuits. */
svg .grid { stroke: var(--rule); stroke-width: 1; }
svg .lvl { fill: none; stroke: var(--rule); stroke-width: 1.2; }
svg .lvl1 { fill: none; stroke: var(--ink); stroke-width: 1.4; stroke-opacity: 0.75; }
svg .lvl0 { fill: none; stroke: var(--pos); stroke-width: 2.6; }
svg .sline { stroke: var(--muted); stroke-width: 1; stroke-dasharray: 3 3; }
svg .gapbar { stroke: var(--accent); stroke-width: 2.2; }
svg .trace { fill: none; stroke: var(--pos); stroke-width: 2; stroke-linejoin: round; }
svg .trace.faint { stroke-opacity: 0.35; stroke-dasharray: 3 3; }
svg .fine { fill: none; stroke: var(--muted); stroke-width: 1.4; stroke-opacity: 0.8; }
svg .dot { fill: var(--pos); stroke: var(--panel); stroke-width: 1.5; }
svg .uni { stroke: var(--muted); stroke-width: 1.2; stroke-dasharray: 1 3; }
svg .qline { stroke: var(--accent); stroke-width: 1.6; stroke-dasharray: 6 3; }
svg .tick { stroke: var(--ink); stroke-width: 2.6; stroke-linecap: round; }
svg .clipmark { fill: var(--ink); }
'''

# ---------- 4. script: the shared helpers and the cube figure from the current page, then the new toys
old_script = old_html[old_html.rindex("<script>") + len("<script>"):old_html.rindex("</script>")]
head = old_script[:old_script.index("/* ---------- hero: 16x16 Walsh matrix ---------- */")].rstrip()
helpers_end = head.index("  /* ---------- MaxCut assignments")
helpers, cube = head[:helpers_end], head[helpers_end:]
# keep only the helpers the cube figure and the new toys still use
users = cube + (HERE / "engine.js").read_text() + (HERE / "ui.js").read_text()
stmts, cur = [], []
for line in helpers.splitlines(keepends=True):
    if re.match(r"  (const |function )", line) and cur:
        stmts.append("".join(cur)); cur = []
    cur.append(line)
stmts.append("".join(cur))
named = []
for st in stmts:
    m = re.match(r"  (?:const (\w+) =|function (\w+)\()", st)
    named.append((m and (m.group(1) or m.group(2)), st))
need = {n for n, _ in named if n and re.search(rf"\b{n}\b", users)}
while True:
    more = {n for n, _ in named if n and n not in need and any(re.search(rf"\b{n}\b", st) for m, st in named if m in need)}
    if not more: break
    need |= more
kept = [st for n, st in named if not n or n in need]
print("dropping unused helpers:", [n for n, _ in named if n and n not in need])
helpers = "".join(kept)
r4 = lambda v: round(v, 4)
slide = {"s": data["s"], "levels": [[r4(v) for v in row] for row in data["levels"]], "dists": [[r4(v) for v in row] for row in data["dists"]]}
tuned = [{"p": t["p"], "gamma": t["gamma"], "beta": t["beta"]} for t in data["tuned"]]
engine = (HERE / "engine.js").read_text(encoding="utf-8")
engine = "\n".join("  " + l if l else l for l in engine.splitlines())
script = ("<script>\n" + helpers.rstrip() + "\n\n" + cube.rstrip() + "\n\n"
          "  /* ---------- data: the slide on the prism (exact diagonalization) and tuned QAOA angles ---------- */\n"
          f"  const SLIDE = {json.dumps(slide, separators=(',', ':'))};\n"
          f"  const TUNED = {json.dumps(tuned, separators=(',', ':'))};\n\n"
          + engine + "\n\n" + (HERE / "ui.js").read_text(encoding="utf-8").rstrip() + "\n})();\n</script>")

mathjax = old_html[old_html.index("<script>\nwindow.MathJax"):old_html.index("</script>", old_html.index("window.MathJax")) + len("</script>")]
page = f'''<!doctype html>
<html lang="en">
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>QAOA on the Hamming Cube</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500&family=STIX+Two+Text:ital@0;1&display=swap">
<style>
{css}
</style>
{mathjax}
<script src="https://cdnjs.cloudflare.com/ajax/libs/mathjax/3.2.2/es5/tex-svg.min.js" async></script>

<main class="frame">
{body}
{foot_html}
</main>

{script}
'''
(BLOG / "qaoa_hamming_cube.html").write_text(page, encoding="utf-8")
(BLOG / "QAOAOnTheHammingCube").write_text(plain, encoding="utf-8")
STAGING.mkdir(exist_ok=True); (STAGING / "assets").mkdir(exist_ok=True)
(STAGING / "qaoa_hamming_cube.html").write_text(page, encoding="utf-8")
print("plain post:", len(plain.split()), "words; html bytes:", len(page.encode()))
