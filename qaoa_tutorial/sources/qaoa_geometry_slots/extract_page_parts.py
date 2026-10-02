"""One-off: cut the hand-edited page of commit f690c1a into source pieces for build_page.py.

Writes page/style.css, page/page.js and page/snippets/*.html. Run once from this folder, before
qaoa_hamming_cube.html is rebuilt; afterwards the pieces are edited directly.
"""
import os

src = open('../../qaoa_hamming_cube.html', encoding='utf-8').read()
os.makedirs('page/snippets', exist_ok=True)


def cut(start, end, include_end=True):
    """The text from `start` up to the first `end` after it."""
    i = src.index(start)
    j = src.index(end, i + len(start))
    return src[i:j + len(end)] if include_end else src[i:j]


style = cut('<style>\n', '</style>')[len('<style>\n'):-len('</style>')]
script = cut('<script>\n(() => {', '</script>')[len('<script>\n'):-len('</script>')]
open('page/style.css', 'w', encoding='utf-8').write(style)
open('page/page.js', 'w', encoding='utf-8').write(script)

snippets = {
    'maxcut_cube': cut('<div class="toy" id="maxcut-cube"', '</figure>\n'),
    'corner_table': cut('<div class="tablewrap">\n<table>\n<thead><tr><th scope="col">$x$', '</table>\n</div>\n'),
    'walsh16': cut('<figure class="fig narrow">', '</figure>\n'),
    'toy1': cut('<div class="toy" id="labA">', '<h2>The cost layer', include_end=False),
    'prism_figure': cut('<figure class="fig medium">', '</figure>\n'),
    'toy2': cut('<div class="toy" id="labB">', '<h2>Rotate time', include_end=False),
}
for name, text in snippets.items():
    open(f'page/snippets/{name}.html', 'w', encoding='utf-8').write(text)
    print(f'{name:13s} {text.count(chr(10)):4d} lines')
print('style.css', style.count('\n'), 'lines;  page.js', script.count('\n'), 'lines')
