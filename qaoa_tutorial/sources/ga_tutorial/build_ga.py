import html, re
from pathlib import Path
from markdown_it import MarkdownIt

HERE = Path(__file__).parent
LLS = HERE.parent / "qaoa_lukaslatentspace_v3"  # shared footer and stylesheet
OUT = HERE.parent.parent / "ga"
OUT.mkdir(exist_ok=True)
src = (HERE / "post.md").read_text(encoding="utf-8")
footer = (LLS / "footer.txt").read_text(encoding="utf-8").rstrip("\n")

marker = re.compile(r"^<!-- (FIG|TOY):[a-z0-9]+ -->\n\n?", re.M)
plain = marker.sub("", src).rstrip("\n") + "\n" + footer + "\n"
(OUT / "GeneticAlgorithmsOnTheHammingCube").write_text(plain, encoding="utf-8")

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

toy_evolve = '''<p>You can play with this yourself. Pick the selection strength and the mutation rate, then let the population evolve. With an infinite population you see the power method at work. With a finite one you see the lottery on top of it.</p>
<div class="toy" id="toyEvolve">
  <div class="toy-head"><span><strong>Toy 1.</strong> Evolving a population on the prism</span></div>
  <div class="controls">
    <div class="slider"><label for="gaGamma">γ</label><input type="range" id="gaGamma" min="0" max="300" value="100"><output id="gaGammaOut" for="gaGamma"></output></div>
    <div class="slider"><label for="gaQ">q</label><input type="range" id="gaQ" min="0" max="500" value="50"><output id="gaQOut" for="gaQ"></output></div>
  </div>
  <div class="controls">
    <div class="seg" role="group" aria-label="Population size">
      <button type="button" id="popInf" aria-pressed="true">N = ∞</button>
      <button type="button" id="pop200" aria-pressed="false">N = 200</button>
      <button type="button" id="pop30" aria-pressed="false">N = 30</button>
    </div>
    <button type="button" class="btn" id="gaStep">Step</button>
    <button type="button" class="btn" id="gaRun">Run</button>
    <button type="button" class="btn" id="gaReset">Reset</button>
  </div>
  <div class="readouts">
    <div class="ro"><span class="k">Generation</span><span class="val" id="gaGen"></span></div>
    <div class="ro"><span class="k">P(max cut) now</span><span class="val" id="gaPmax"></span></div>
    <div class="ro"><span class="k">Quasispecies P(max cut)</span><span class="val" id="gaPfix"></span></div>
    <div class="ro"><span class="k">Expected cut now</span><span class="val" id="gaMean"></span></div>
  </div>
  <div class="two">
    <div>
      <div class="panel-label">Cut value distribution</div>
      <svg class="plot" id="gaHist" viewBox="0 0 260 172" role="img" aria-label="Distribution of cut values in the current population, with the quasispecies as dashed outlines"></svg>
      <p class="caption">Bars: the population now, the maximum cut in plum. Dashed outlines: the quasispecies.</p>
    </div>
    <div>
      <div class="panel-label">P(max cut) per generation</div>
      <svg class="plot" id="gaTraj" viewBox="0 0 260 172" role="img" aria-label="Probability of a maximum cut over the generations"></svg>
      <p class="caption">Dashed: the quasispecies level. Dotted: random guessing.</p>
    </div>
  </div>
</div>'''

toy_threshold = '''<p>And here you can move the threshold around. The curve is the master's share in the quasispecies for every mutation rate, and the dashed line marks $q_c$.</p>
<div class="toy" id="toyThreshold">
  <div class="toy-head"><span><strong>Toy 2.</strong> The error threshold on a needle</span></div>
  <div class="controls">
    <div class="slider"><label for="thN">n</label><input type="range" id="thN" min="8" max="40" value="20"><output id="thNOut" for="thN"></output></div>
    <div class="slider"><label for="thG">γ</label><input type="range" id="thG" min="20" max="300" value="100"><output id="thGOut" for="thG"></output></div>
  </div>
  <div class="readouts">
    <div class="ro"><span class="k">q_c = 1 − e^(−γ/n)</span><span class="val" id="thQc"></span></div>
    <div class="ro"><span class="k">P(master) at q_c / 2</span><span class="val" id="thBelow"></span></div>
    <div class="ro"><span class="k">P(master) at 1.25 q_c</span><span class="val" id="thAbove"></span></div>
    <div class="ro"><span class="k">Random guess 2^(−n)</span><span class="val" id="thUni"></span></div>
  </div>
  <svg class="plot" id="thPlot" viewBox="0 0 520 240" role="img" aria-label="Share of the master string in the quasispecies against the mutation rate, with the error threshold marked"></svg>
  <p class="caption">Larger n makes the drop sharper and moves it to smaller q.</p>
</div>'''

for key, snippet in {"TOY:evolve": toy_evolve, "TOY:threshold": toy_threshold}.items():
    tag = f"<!-- {key} -->"
    assert body.count(tag) == 1, key
    body = body.replace(tag, snippet)

lines = footer.splitlines()
foot_html = f'''<footer>
  <div class="dashes" aria-hidden="true">{lines[0]}</div>
  <p>{html.escape(lines[1])}<br>Google scholar: <a href="https://scholar.google.com/citations?user=aD3-DrQAAAAJ&amp;hl=de">https://scholar.google.com/citations?user=aD3-DrQAAAAJ&amp;hl=de</a></p>
</footer>'''

css = (LLS / "style.css").read_text(encoding="utf-8").replace(
    "/* Layout: a single notebook column like a Markdown post on GitHub; teal and plum stay the +1 / -1 colours of the figures. */",
    "/* Layout: a single notebook column like a Markdown post on GitHub; teal marks the population, plum the maximum cut and the threshold. */")
css += '''
svg .trace { fill: none; stroke: var(--pos); stroke-width: 2; stroke-linejoin: round; }
svg .dot { fill: var(--pos); }
svg .grid { stroke: var(--rule); stroke-width: 1; }
svg .uni { stroke: var(--muted); stroke-width: 1.2; stroke-dasharray: 1 3; }
svg .qline { stroke: var(--neg); stroke-width: 1.4; stroke-dasharray: 4 3; }
'''
script = "<script>\n(() => {\n" + (HERE / "engine.js").read_text(encoding="utf-8") + "\n" + (HERE / "ui.js").read_text(encoding="utf-8") + "\n})();\n</script>"
page = f'''<title>Genetic Algorithms on the Hamming Cube</title>
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
(OUT / "ga_hamming_cube.html").write_text(page, encoding="utf-8")
print("plain post:", len(plain.split()), "words; html bytes:", len(page.encode()))
