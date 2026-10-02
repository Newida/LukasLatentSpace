import html, re, sys
from pathlib import Path
from markdown_it import MarkdownIt

HERE = Path(__file__).parent
TUT = HERE.parent.parent  # qaoa_tutorial/
OUT = HERE / "build_output"  # archival build, never overwrites the published files
OUT.mkdir(exist_ok=True)
src = (HERE / "post.md").read_text(encoding="utf-8")
footer = (HERE / "footer.txt").read_text(encoding="utf-8").rstrip("\n")

# ---------- 1. plain-text post in the LukasLatentSpace format
marker = re.compile(r"^<!-- (FIG|TOY):[a-z0-9]+ -->\n\n?", re.M)
plain = marker.sub("", src).rstrip("\n") + "\n" + footer + "\n"
(OUT / "QAOAOnTheHammingCube").write_text(plain, encoding="utf-8")

# ---------- 2. Markdown -> HTML with math protected
fence = re.compile(r"```.*?```", re.S)
mathre = re.compile(r"\$\$.+?\$\$|\$[^$\n]+?\$", re.S)
store = []
def protect(text):
    out, pos = [], 0
    for f in fence.finditer(text):
        out.append(mathre.sub(lambda m: (store.append(m.group(0)), f"@@M{len(store)-1}@@")[1], text[pos:f.start()]))
        out.append(f.group(0)); pos = f.end()
    out.append(mathre.sub(lambda m: (store.append(m.group(0)), f"@@M{len(store)-1}@@")[1], text[pos:]))
    return "".join(out)
md = MarkdownIt("commonmark", {"html": True}).enable("table")
body = md.render(protect(src))
body = re.sub(r"@@M(\d+)@@", lambda m: html.escape(store[int(m.group(1))], quote=False), body)
body = body.replace("<table>", '<div class="tablewrap"><table>').replace("</table>", "</table></div>")
body = re.sub(r"<h1>(.*?)</h1>", r'<h1 id="top">\1</h1>', body, count=1)

# ---------- 3. figures and toys
walsh16 = '''<figure class="fig narrow">
  <canvas id="walsh16" role="img" aria-label="The 16 by 16 Walsh matrix for four bits, rows sorted by Hamming weight"></canvas>
  <figcaption>And here are all 16 characters for $n = 4$, one row each, sorted by $|s|$. Teal is $+1$, plum is $-1$.</figcaption>
</figure>'''

pos = [(110, 18), (192, 160), (28, 160), (110, 72), (150, 136), (70, 136)]
vec = [2, -1, -1, -2, 1, 1]
E = [(0, 1), (1, 2), (2, 0), (3, 4), (4, 5), (5, 3), (0, 3), (1, 4), (2, 5)]
g = []
for i, j in E:
    cut = (vec[i] > 0) != (vec[j] > 0)
    g.append(f'<line x1="{pos[i][0]}" y1="{pos[i][1]}" x2="{pos[j][0]}" y2="{pos[j][1]}" class="gedge{" cut" if cut else ""}"/>')
for k, (x, y) in enumerate(pos):
    g.append(f'<circle cx="{x}" cy="{y}" r="12" class="{"gv0" if vec[k] > 0 else "gv1"}"/>')
    g.append(f'<text x="{x}" y="{y + 4}" class="gvl" text-anchor="middle">{k + 1}</text>')
bars = ['<line x1="14" y1="135" x2="206" y2="135" class="base"/>']
for k, lam in enumerate([0, 2, 3, 3, 5, 5]):
    x, h = 22 + 30 * k, 20 * lam
    if h:
        bars.append(f'<rect x="{x}" y="{135 - h}" width="22" height="{h}" class="{"bar-p" if lam == 5 else "bar-m"}"/>')
    bars.append(f'<text x="{x + 11}" y="{135 - h - 6}" class="lbl-ink" text-anchor="middle">{lam}</text>')
bars.append('<text x="110" y="156" class="lbl" text-anchor="middle">eigenvalues of the prism Laplacian</text>')
prism = f'''<figure class="fig medium">
  <div class="two">
    <div>
      <div class="panel-label">Signs of the top eigenvector</div>
      <svg class="plot" viewBox="0 0 220 190" role="img" aria-label="The triangular prism coloured by the signs of a top Laplacian eigenvector. Seven edges are cut, which is the maximum.">
        {"".join(g)}
      </svg>
    </div>
    <div>
      <div class="panel-label">Laplacian spectrum</div>
      <svg class="plot" viewBox="0 0 220 170" role="img" aria-label="Bar chart of the prism Laplacian eigenvalues: 0, 2, 3, 3, 5 and 5.">
        {"".join(bars)}
      </svg>
    </div>
  </div>
  <figcaption>The same thing as a picture. Teal is $+$, plum is $-$, solid edges are cut.</figcaption>
</figure>'''

toy_cube = '''<p>You can play with this yourself. Click a corner to start the walk there, then switch between the classical heat flow and the quantum mixer.</p>
<div class="toy" id="labA">
  <div class="toy-head"><strong>Toy 1.</strong> Diffusion on $Q_3$, classical versus quantum</div>
  <div class="controls">
    <div class="seg" role="group" aria-label="Kind of diffusion">
      <button type="button" id="modeC" aria-pressed="true">Classical heat flow</button>
      <button type="button" id="modeQ" aria-pressed="false">Quantum mixer</button>
    </div>
    <div class="slider">
      <label for="cubeTime" id="cubeTimeLabel">t</label>
      <input type="range" id="cubeTime" min="0" max="1000" value="250">
      <output id="cubeTimeOut" for="cubeTime"></output>
    </div>
    <button type="button" class="btn" id="cubePlay">Play</button>
  </div>
  <div class="two">
    <div>
      <div class="panel-label">Positions: corners</div>
      <svg class="plot" id="cubeSvg" viewBox="0 0 400 300" role="img" aria-label="Three-dimensional Hamming cube with probabilities on its corners"></svg>
    </div>
    <div>
      <div class="panel-label" id="modeLabel">Frequencies: Walsh modes</div>
      <svg class="plot" id="modeSvg" viewBox="0 0 430 200" role="img" aria-label="Walsh mode coefficients of the current state"></svg>
      <p class="caption" id="modeCaption"></p>
    </div>
  </div>
  <div class="readouts">
    <div class="ro"><span class="k">Per-bit flip probability</span><span class="val" id="roFlip"></span></div>
    <div class="ro"><span class="k">P(start corner)</span><span class="val" id="roStart"></span></div>
    <div class="ro"><span class="k">P(opposite corner)</span><span class="val" id="roOpp"></span></div>
  </div>
  <p class="caption" id="cubeColorNote"></p>
</div>'''

toy_prism = '''<p>Again, you can play with it. Click or drag on the landscape to pick $(\\gamma, \\beta)$, or press the button to jump to the best point.</p>
<div class="toy" id="labB">
  <div class="toy-head"><strong>Toy 2.</strong> The depth-1 landscape $\\langle C \\rangle(\\gamma, \\beta)$ on the prism
    <span class="heat-legend"><span id="heatMin"></span><span class="ramp" aria-hidden="true"></span><span id="heatMax"></span></span>
  </div>
  <canvas id="heat" tabindex="0" role="img" aria-label="Heatmap of the expected cut size over gamma and beta. Use the sliders below to choose a point."></canvas>
  <div class="controls">
    <div class="slider"><label for="gSlider">γ</label><input type="range" id="gSlider" min="0" max="1000" value="0"><output id="gOut" for="gSlider"></output></div>
    <div class="slider"><label for="bSlider">β</label><input type="range" id="bSlider" min="0" max="1000" value="0"><output id="bOut" for="bSlider"></output></div>
    <button type="button" class="btn" id="bestBtn">Jump to best</button>
  </div>
  <div class="readouts">
    <div class="ro"><span class="k">Expected cut ⟨C⟩</span><span class="val" id="roE"></span></div>
    <div class="ro"><span class="k">Approximation ratio ⟨C⟩/7</span><span class="val" id="roR"></span></div>
    <div class="ro"><span class="k">P(maximum cut)</span><span class="val" id="roP"></span></div>
    <div class="ro"><span class="k">Most likely string</span><span class="val" id="roMode"></span></div>
  </div>
  <div class="three">
    <div>
      <div class="panel-label">Most likely cut</div>
      <svg class="plot" id="graphSvg" viewBox="0 0 220 190" role="img" aria-label="The prism graph coloured by the most likely bitstring"></svg>
      <p class="caption">Solid edges are cut by the most likely string.</p>
    </div>
    <div>
      <div class="panel-label">Cut value distribution</div>
      <svg class="plot" id="histSvg" viewBox="0 0 220 170" role="img" aria-label="Probability of each cut value compared with uniform sampling"></svg>
      <p class="caption">Bars: after QAOA. Dashed outlines: a uniformly random string.</p>
    </div>
    <div>
      <div class="panel-label">Walsh weight by $|s|$</div>
      <svg class="plot" id="specSvg" viewBox="0 0 220 170" role="img" aria-label="Fourier weight of the state grouped by Hamming weight of the frequency"></svg>
      <p class="caption">Move only $\\beta$ and these bars stay put.</p>
    </div>
  </div>
</div>'''

for key, snippet in {"FIG:walsh16": walsh16, "FIG:prism": prism, "TOY:cube": toy_cube, "TOY:prism": toy_prism}.items():
    tag = f"<!-- {key} -->"
    assert body.count(tag) == 1, key
    body = body.replace(tag, snippet)

# ---------- 4. page script from the current tutorial, with a guard for the removed 8x8 grid
old = (TUT / "qaoa_hamming_cube.html").read_text(encoding="utf-8")
script = old[old.index("<script>"):old.index("</script>") + len("</script>")]
anchor = "const g = document.getElementById('walsh8');"
assert script.count(anchor) == 1
script = script.replace(anchor, anchor + "\n    if (!g) return;")

lines = footer.splitlines()
foot_html = f'''<footer>
  <div class="dashes" aria-hidden="true">{lines[0]}</div>
  <p>{html.escape(lines[1])}<br>Google scholar: <a href="https://scholar.google.com/citations?user=aD3-DrQAAAAJ&amp;hl=de">https://scholar.google.com/citations?user=aD3-DrQAAAAJ&amp;hl=de</a></p>
</footer>'''

css = (HERE / "style.css").read_text(encoding="utf-8")
page = f'''<title>QAOA on the Hamming Cube</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500&family=STIX+Two+Text:ital@0;1&display=swap">
<style>
{css}
</style>
<script>
window.MathJax = {{
  tex: {{
    inlineMath: [['$', '$'], ['\\\\(', '\\\\)']],
    displayMath: [['$$', '$$'], ['\\\\[', '\\\\]']],
    macros: {{ ket: ['\\\\left|#1\\\\right\\\\rangle', 1], bra: ['\\\\left\\\\langle #1\\\\right|', 1] }}
  }},
  svg: {{ fontCache: 'global' }}
}};
</script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/mathjax/3.2.2/es5/tex-svg.min.js" async></script>

<main class="frame">
{body}
{foot_html}
</main>

{script}
'''
(OUT / "qaoa_hamming_cube.html").write_text(page, encoding="utf-8")
print("plain post:", len(plain.split()), "words; html bytes:", len(page.encode()))
