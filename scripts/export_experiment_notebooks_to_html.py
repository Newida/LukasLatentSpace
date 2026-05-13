#!/usr/bin/env python3
"""Export all experiment notebooks to static HTML.

The repository intentionally keeps this converter lightweight so agents can run
it in minimal environments without nbconvert or nbformat.  It handles the
notebook structures used in this repo: markdown, code cells, stream output,
errors, text output, HTML output, and embedded images.
"""

from __future__ import annotations

import argparse
import html
import json
import re
from pathlib import Path
from typing import Any

try:
    from pygments import highlight
    from pygments.formatters import HtmlFormatter
    from pygments.lexers import PythonLexer
except Exception:  # pragma: no cover - optional dependency fallback
    highlight = None
    HtmlFormatter = None
    PythonLexer = None


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT_DIR = REPO_ROOT / "experiments"
DEFAULT_OUTPUT_DIR = REPO_ROOT / "experiments_html"


def join_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return "".join(str(item) for item in value)
    return str(value)


def slugify(text: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", text.strip().lower()).strip("-")
    return slug or "section"


def notebook_title(notebook: dict[str, Any], fallback: str) -> str:
    for cell in notebook.get("cells", []):
        if cell.get("cell_type") != "markdown":
            continue
        for line in join_text(cell.get("source")).splitlines():
            match = re.match(r"^#\s+(.+?)\s*$", line)
            if match:
                return match.group(1)
    return fallback


def inline_markdown(text: str) -> str:
    placeholders: list[str] = []

    def stash_code(match: re.Match[str]) -> str:
        placeholders.append(f"<code>{html.escape(match.group(1))}</code>")
        return f"\u0000{len(placeholders) - 1}\u0000"

    escaped = re.sub(r"`([^`]+)`", stash_code, html.escape(text))
    escaped = re.sub(
        r"\*\*(.+?)\*\*",
        r"<strong>\1</strong>",
        escaped,
    )
    escaped = re.sub(
        r"\[([^\]]+)\]\(([^)]+)\)",
        lambda match: (
            f'<a href="{html.escape(match.group(2), quote=True)}">'
            f"{match.group(1)}</a>"
        ),
        escaped,
    )

    for index, replacement in enumerate(placeholders):
        escaped = escaped.replace(f"\u0000{index}\u0000", replacement)
    return escaped


def render_markdown(source: str) -> str:
    output: list[str] = []
    lines = source.splitlines()
    index = 0

    def emit_paragraph(paragraph_lines: list[str]) -> None:
        if paragraph_lines:
            output.append(f"<p>{inline_markdown(' '.join(paragraph_lines))}</p>")

    while index < len(lines):
        line = lines[index]
        stripped = line.strip()

        if not stripped:
            index += 1
            continue

        if stripped == "$$":
            math_lines = [line]
            index += 1
            while index < len(lines):
                math_lines.append(lines[index])
                if lines[index].strip() == "$$":
                    index += 1
                    break
                index += 1
            output.append(
                '<div class="math-block">'
                + html.escape("\n".join(math_lines))
                + "</div>"
            )
            continue

        fence_match = re.match(r"^```(\w+)?\s*$", stripped)
        if fence_match:
            language = fence_match.group(1) or ""
            code_lines: list[str] = []
            index += 1
            while index < len(lines) and lines[index].strip() != "```":
                code_lines.append(lines[index])
                index += 1
            index += 1
            output.append(
                f'<pre class="markdown-code language-{html.escape(language)}">'
                f"<code>{html.escape(chr(10).join(code_lines))}</code></pre>"
            )
            continue

        heading = re.match(r"^(#{1,6})\s+(.+?)\s*$", line)
        if heading:
            level = len(heading.group(1))
            text = heading.group(2)
            output.append(
                f'<h{level} id="{slugify(text)}">{inline_markdown(text)}</h{level}>'
            )
            index += 1
            continue

        bullet_match = re.match(r"^\s*[-*]\s+(.+)$", line)
        if bullet_match:
            items: list[str] = []
            while index < len(lines):
                item_match = re.match(r"^\s*[-*]\s+(.+)$", lines[index])
                if not item_match:
                    break
                items.append(f"<li>{inline_markdown(item_match.group(1))}</li>")
                index += 1
            output.append("<ul>" + "".join(items) + "</ul>")
            continue

        numbered_match = re.match(r"^\s*\d+\.\s+(.+)$", line)
        if numbered_match:
            items = []
            while index < len(lines):
                item_match = re.match(r"^\s*\d+\.\s+(.+)$", lines[index])
                if not item_match:
                    break
                items.append(f"<li>{inline_markdown(item_match.group(1))}</li>")
                index += 1
            output.append("<ol>" + "".join(items) + "</ol>")
            continue

        paragraph = [stripped]
        index += 1
        while index < len(lines):
            candidate = lines[index]
            candidate_stripped = candidate.strip()
            if not candidate_stripped:
                break
            if (
                candidate_stripped == "$$"
                or re.match(r"^#{1,6}\s+", candidate)
                or re.match(r"^\s*[-*]\s+", candidate)
                or re.match(r"^\s*\d+\.\s+", candidate)
                or re.match(r"^```(\w+)?\s*$", candidate_stripped)
            ):
                break
            paragraph.append(candidate_stripped)
            index += 1
        emit_paragraph(paragraph)

    return "\n".join(output)


def render_code(source: str) -> str:
    if highlight and HtmlFormatter and PythonLexer:
        return highlight(source, PythonLexer(), HtmlFormatter(nowrap=True))
    return html.escape(source)


def render_output(output: dict[str, Any]) -> str:
    output_type = output.get("output_type")

    if output_type == "stream":
        name = html.escape(output.get("name", "stream"))
        text = html.escape(join_text(output.get("text")))
        return f'<pre class="cell-output stream-output {name}">{text}</pre>'

    if output_type == "error":
        traceback_text = "\n".join(output.get("traceback", []))
        if not traceback_text:
            traceback_text = f"{output.get('ename', '')}: {output.get('evalue', '')}"
        return f'<pre class="cell-output error-output">{html.escape(traceback_text)}</pre>'

    if output_type in {"display_data", "execute_result"}:
        data = output.get("data", {})
        rendered: list[str] = []
        image_png = join_text(data.get("image/png"))
        image_jpeg = join_text(data.get("image/jpeg"))
        text_html = join_text(data.get("text/html"))
        text_plain = join_text(data.get("text/plain"))

        if image_png:
            rendered.append(
                '<img class="cell-image" alt="notebook output image" '
                f'src="data:image/png;base64,{image_png}">'
            )
        elif image_jpeg:
            rendered.append(
                '<img class="cell-image" alt="notebook output image" '
                f'src="data:image/jpeg;base64,{image_jpeg}">'
            )
        elif text_html:
            rendered.append(f'<div class="html-output">{text_html}</div>')
        elif text_plain:
            rendered.append(
                f'<pre class="cell-output text-output">{html.escape(text_plain)}</pre>'
            )

        return "\n".join(rendered)

    return (
        '<pre class="cell-output text-output">'
        + html.escape(json.dumps(output, indent=2))
        + "</pre>"
    )


def pygments_css() -> str:
    if HtmlFormatter is None:
        return ""
    return HtmlFormatter().get_style_defs(".highlight")


def page_css() -> str:
    return f"""
:root {{
  color-scheme: light;
  --page: #f7f7f4;
  --text: #1f2428;
  --muted: #66717a;
  --border: #d9dedb;
  --code-bg: #f0f2f1;
  --output-bg: #ffffff;
  --accent: #0f766e;
}}

* {{ box-sizing: border-box; }}

body {{
  margin: 0;
  background: var(--page);
  color: var(--text);
  font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  line-height: 1.55;
}}

main {{
  max-width: 1080px;
  margin: 0 auto;
  padding: 40px 24px 72px;
}}

.notebook-header {{
  border-bottom: 1px solid var(--border);
  margin-bottom: 28px;
  padding-bottom: 20px;
}}

.notebook-header h1 {{
  margin: 0 0 8px;
  font-size: 2.1rem;
}}

.notebook-meta {{
  color: var(--muted);
  margin: 0;
}}

.cell {{
  margin: 22px 0;
}}

.markdown-cell h1,
.markdown-cell h2,
.markdown-cell h3 {{
  line-height: 1.2;
  margin-top: 1.25em;
}}

.markdown-cell p,
.markdown-cell li {{
  max-width: 88ch;
}}

.math-block {{
  overflow-x: auto;
  padding: 8px 0;
}}

code {{
  background: var(--code-bg);
  border-radius: 4px;
  padding: 0.1em 0.3em;
}}

.input-label {{
  color: var(--muted);
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size: 0.85rem;
  margin-bottom: 6px;
}}

.code-input,
.cell-output,
.markdown-code {{
  border: 1px solid var(--border);
  border-radius: 8px;
  overflow-x: auto;
}}

.code-input {{
  background: var(--code-bg);
  margin: 0;
  padding: 14px 16px;
}}

.cell-output {{
  background: var(--output-bg);
  margin: 8px 0 0;
  padding: 12px 14px;
  white-space: pre-wrap;
}}

.error-output {{
  border-color: #dc2626;
  color: #991b1b;
}}

.cell-image {{
  background: #ffffff;
  border: 1px solid var(--border);
  border-radius: 8px;
  display: block;
  height: auto;
  margin-top: 10px;
  max-width: 100%;
}}

a {{
  color: var(--accent);
}}

{pygments_css()}
"""


def render_notebook(notebook_path: Path, notebook: dict[str, Any]) -> str:
    title = notebook_title(notebook, notebook_path.stem)
    cells_html: list[str] = []

    for index, cell in enumerate(notebook.get("cells", []), start=1):
        cell_type = cell.get("cell_type")
        source = join_text(cell.get("source"))

        if cell_type == "markdown":
            cells_html.append(
                '<section class="cell markdown-cell">'
                + render_markdown(source)
                + "</section>"
            )
            continue

        if cell_type == "code":
            execution_count = cell.get("execution_count")
            label = f"In [{execution_count}]" if execution_count is not None else "In [ ]"
            outputs = "\n".join(render_output(out) for out in cell.get("outputs", []))
            cells_html.append(
                '<section class="cell code-cell">'
                f'<div class="input-label">{html.escape(label)}</div>'
                f'<pre class="code-input highlight"><code>{render_code(source)}</code></pre>'
                f"{outputs}"
                "</section>"
            )
            continue

        cells_html.append(
            '<section class="cell raw-cell">'
            f"<pre>{html.escape(source)}</pre>"
            "</section>"
        )

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)}</title>
  <style>{page_css()}</style>
  <script>
    window.MathJax = {{
      tex: {{ inlineMath: [['$', '$'], ['\\\\(', '\\\\)']] }},
      svg: {{ fontCache: 'global' }}
    }};
  </script>
  <script async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-svg.js"></script>
</head>
<body>
  <main>
    <header class="notebook-header">
      <h1>{html.escape(title)}</h1>
      <p class="notebook-meta">Generated from {html.escape(str(notebook_path))}</p>
    </header>
    {''.join(cells_html)}
  </main>
</body>
</html>
"""


def export_notebook(notebook_path: Path, input_dir: Path, output_dir: Path) -> Path:
    notebook = json.loads(notebook_path.read_text())
    relative = notebook_path.relative_to(input_dir).with_suffix(".html")
    output_path = output_dir / relative
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_notebook(notebook_path, notebook), encoding="utf-8")
    return output_path


def find_notebooks(input_dir: Path) -> list[Path]:
    return sorted(
        path
        for path in input_dir.rglob("*.ipynb")
        if ".ipynb_checkpoints" not in path.parts
    )


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export all Jupyter notebooks in experiments/ to static HTML."
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=DEFAULT_INPUT_DIR,
        help=f"Notebook directory to scan. Default: {DEFAULT_INPUT_DIR}",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help=f"Directory for generated HTML files. Default: {DEFAULT_OUTPUT_DIR}",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_dir = args.input_dir.resolve()
    output_dir = args.output_dir.resolve()

    notebooks = find_notebooks(input_dir)
    if not notebooks:
        print(f"No notebooks found in {input_dir}")
        return

    print(f"Exporting {len(notebooks)} notebook(s) from {input_dir}")
    print(f"Writing HTML files to {output_dir}")
    for notebook_path in notebooks:
        output_path = export_notebook(notebook_path, input_dir, output_dir)
        print(f"{display_path(notebook_path)} -> {display_path(output_path)}")


if __name__ == "__main__":
    main()
