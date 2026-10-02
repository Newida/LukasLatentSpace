"""Build ../../qaoa_hamming_cube.html from the plain post ../../QAOAOnTheHammingCube.

The post is rendered with markdown-it-py (commonmark plus tables). Math is swapped for placeholders before
rendering and put back afterwards, so MathJax sees it untouched. Toys and figures from page/snippets are
inserted after fixed anchor texts of the post, and page/style.css and page/page.js are inlined.
Run from this folder: python build_page.py
"""
import html
import re
from markdown_it import MarkdownIt

POST = '../../QAOAOnTheHammingCube'
OUT = '../../qaoa_hamming_cube.html'
DASHES = '-' * 100


def read(path):
    return open(path, encoding='utf-8').read()


def snippet(name):
    return read(f'page/snippets/{name}.html')


text = read(POST)
body, footer = text.split('\n' + DASHES + '\n')

# ---------------------------------------------------------------- math out of the way of markdown
for block in re.findall(r'```.*?```', body, flags=re.S):
    assert '$' not in block, 'math inside a code block would be mangled'
maths = []


def stash(tex, display):
    maths.append(('$$' + tex + '$$') if display else ('$' + tex + '$'))
    return f'MATHPH{len(maths) - 1}X'


def display(m):
    # inside a blockquote, the lines of a display formula carry the '> ' prefix
    lines = m.group(1).split('\n')
    lines = [lines[0]] + [re.sub(r'^\s*>\s?', '', line) for line in lines[1:]]
    return stash('\n'.join(lines), True)


body = re.sub(r'\$\$(.+?)\$\$', display, body, flags=re.S)
body = re.sub(r'(?<!\$)\$([^$\n]+?)\$', lambda m: stash(m.group(1), False), body)
assert '$' not in body, 'unmatched dollar sign'

md = MarkdownIt('commonmark', {'html': True}).enable('table')
out = md.render(body)
out = re.sub(r'MATHPH(\d+)X', lambda m: html.escape(maths[int(m.group(1))], quote=False), out)


# ---------------------------------------------------------------- toys, figures and small fixes
def replace_once(old, new, s):
    assert s.count(old) == 1, (s.count(old), old[:80])
    return s.replace(old, new)


def insert_after(anchor, end, new, s):
    """Insert `new` right after the first `end` that follows the unique `anchor`."""
    assert s.count(anchor) == 1, (s.count(anchor), anchor[:80])
    i = s.index(anchor)
    j = s.index(end, i) + len(end)
    return s[:j] + new + s[j:]


out = replace_once('<h1>', '<h1 id="top">', out)

# the static cube figure and its caption become the interactive figure (with the static one as fallback)
fig = re.search(r'<p><img src="assets/maxcut-hypercube.svg".*?</p>\n<p><em>A cut on the problem graph.*?</em></p>\n', out, flags=re.S)
out = out[:fig.start()] + snippet('maxcut_cube') + out[fig.end():]
table = re.search(r'<p>The values on all eight corners are:</p>\n<table>.*?</table>\n', out, flags=re.S)
out = out[:table.start()] + '<p>The values on all eight corners of the path example are:</p>\n' + snippet('corner_table') + out[table.end():]

out = re.sub(r'(?<!<div class="tablewrap">\n)<table>(.*?)</table>', r'<div class="tablewrap"><table>\1</table></div>', out, flags=re.S)
out = out.replace('<blockquote>\n<p><strong>On the tree.</strong>', '<blockquote class="stage">\n<p><strong>On the tree.</strong>')

out = insert_after('<pre><code> s \\ x   000', '</code></pre>\n', snippet('walsh16'), out)
out = insert_after('<pre><code> level  node', '</code></pre>\n', snippet('haar16'), out)
out = insert_after('The tree mixer is', '</blockquote>\n',
                   '<p>You can play with this yourself. Click a corner or a leaf to start the walk there, then switch '
                   'between the classical heat flow and the quantum mixer, and between the cube and the tree.</p>\n'
                   + snippet('toy1'), out)
out = insert_after('<pre><code> vertex             1    2', '</code></pre>\n', snippet('prism_figure'), out)
out = insert_after('Same prism, same cost, but the tree mixer', '</blockquote>\n',
                   '<p>Again, you can play with it. Click or drag on the landscape to pick $(\\gamma, \\beta)$, or press '
                   'the button to jump to the best point. The stage switch puts the tree mixer on the same prism.</p>\n'
                   + snippet('toy2'), out)

# ---------------------------------------------------------------- footer and page
author, scholar = [line.strip() for line in footer.strip().split('\n')]
url = scholar.split(': ', 1)[1]
footer_html = (
    '<footer>\n'
    f'  <div class="dashes" aria-hidden="true">{DASHES}</div>\n'
    f'  <p>{html.escape(author)}<br>Google scholar: <a href="{html.escape(url)}">{html.escape(url)}</a></p>\n'
    '</footer>\n'
)
title = re.search(r'^# (.+)$', text, flags=re.M).group(1)
page = f'''<!doctype html>
<html lang="en">
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500&family=STIX+Two+Text:ital@0;1&display=swap">
<style>
{read('page/style.css')}</style>
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
{out}
{footer_html}</main>

<script>
{read('page/page.js')}</script>
'''
open(OUT, 'w', encoding='utf-8').write(page)
print(f'wrote {OUT}: {len(page)} bytes, {len(maths)} formulas')
