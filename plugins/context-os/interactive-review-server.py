#!/usr/bin/env python3
"""
Interactive review server — serve markdown content with an inline feedback form.
Feedback is saved to <workspace>/feedback.json. Claude reads it after the user submits.

Usage:
    python3 server.py <content.md> [--workspace DIR] [--port PORT] [--title TITLE]
                      [--options OPTIONS_JSON]
"""

import argparse
import json
import os
import re
import signal
import subprocess
import sys
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

PORT = 3118


# ---------------------------------------------------------------------------
# Minimal markdown → HTML (no deps)
# ---------------------------------------------------------------------------

def md_to_html(md: str) -> str:
    lines = md.split("\n")
    out = []
    in_code = False
    in_list = False
    in_table = False
    buf = []

    def flush_para():
        if buf:
            text = " ".join(buf).strip()
            if text:
                out.append(f"<p>{inline(text)}</p>")
            buf.clear()

    def flush_list():
        nonlocal in_list
        if in_list:
            out.append("</ul>")
            in_list = False

    def flush_table():
        nonlocal in_table
        if in_table:
            out.append("</tbody></table>")
            in_table = False

    def inline(text: str) -> str:
        text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
        text = re.sub(r"\*(.+?)\*", r"<em>\1</em>", text)
        text = re.sub(r"`(.+?)`", r"<code>\1</code>", text)
        text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', text)
        return text

    i = 0
    while i < len(lines):
        line = lines[i]

        # Fenced code block
        if line.startswith("```"):
            flush_para(); flush_list(); flush_table()
            lang = line[3:].strip()
            code_lines = []
            i += 1
            while i < len(lines) and not lines[i].startswith("```"):
                code_lines.append(lines[i])
                i += 1
            code = "\n".join(code_lines).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            out.append(f'<pre><code class="language-{lang}">{code}</code></pre>')
            i += 1
            continue

        # Headings
        m = re.match(r"^(#{1,4})\s+(.*)", line)
        if m:
            flush_para(); flush_list(); flush_table()
            level = len(m.group(1))
            text = inline(m.group(2))
            out.append(f"<h{level}>{text}</h{level}>")
            i += 1
            continue

        # HR
        if re.match(r"^---+$", line.strip()):
            flush_para(); flush_list(); flush_table()
            out.append("<hr>")
            i += 1
            continue

        # Blockquote
        if line.startswith("> "):
            flush_para(); flush_list(); flush_table()
            out.append(f'<blockquote>{inline(line[2:])}</blockquote>')
            i += 1
            continue

        # List item
        m = re.match(r"^[-*]\s+(.*)", line)
        if m:
            flush_para(); flush_table()
            if not in_list:
                out.append("<ul>")
                in_list = True
            out.append(f"<li>{inline(m.group(1))}</li>")
            i += 1
            continue

        # Table
        if "|" in line and i + 1 < len(lines) and re.match(r"^\|[-| :]+\|", lines[i + 1]):
            flush_para(); flush_list()
            if not in_table:
                out.append('<table><thead><tr>')
                for cell in line.strip("|").split("|"):
                    out.append(f"<th>{inline(cell.strip())}</th>")
                out.append("</tr></thead><tbody>")
                in_table = True
                i += 2  # skip separator row
                continue
        if in_table and "|" in line:
            out.append("<tr>")
            for cell in line.strip("|").split("|"):
                out.append(f"<td>{inline(cell.strip())}</td>")
            out.append("</tr>")
            i += 1
            continue
        elif in_table:
            flush_table()

        # Blank line — flush paragraph
        if not line.strip():
            flush_para(); flush_list(); flush_table()
            i += 1
            continue

        # Accumulate paragraph text
        flush_list(); flush_table()
        buf.append(line)
        i += 1

    flush_para(); flush_list(); flush_table()
    return "\n".join(out)


# ---------------------------------------------------------------------------
# HTML template
# ---------------------------------------------------------------------------

TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>{title}</title>
  <style>
    :root {{ --bg:#faf9f5; --surface:#fff; --border:#e8e6dc; --text:#141413;
             --accent:#d97757; --accent2:#c4613f; --green:#788c5d; --radius:6px; }}
    * {{ box-sizing:border-box; margin:0; padding:0; }}
    body {{ font-family:Georgia,serif; background:var(--bg); color:var(--text);
            max-width:900px; margin:0 auto; padding:2rem; }}
    h1,h2,h3,h4 {{ font-family:system-ui,sans-serif; margin:1.25rem 0 0.5rem; }}
    h1 {{ font-size:1.6rem; border-bottom:2px solid var(--border); padding-bottom:0.4rem; }}
    h2 {{ font-size:1.2rem; }}
    p {{ line-height:1.7; margin:0.75rem 0; }}
    pre {{ background:#f5f5f0; padding:1rem; border-radius:var(--radius); overflow-x:auto; margin:1rem 0; }}
    code {{ background:#f5f5f0; padding:0.1em 0.35em; border-radius:3px; font-size:0.88em; }}
    pre code {{ background:none; padding:0; font-size:0.875rem; }}
    blockquote {{ border-left:3px solid var(--accent); padding-left:1rem; color:#666; margin:1rem 0; }}
    ul {{ padding-left:1.5rem; margin:0.75rem 0; line-height:1.8; }}
    hr {{ border:none; border-top:1px solid var(--border); margin:1.5rem 0; }}
    table {{ border-collapse:collapse; width:100%; margin:1rem 0; }}
    th,td {{ border:1px solid var(--border); padding:0.45rem 0.75rem; text-align:left; }}
    th {{ background:#f5f5f0; font-family:system-ui,sans-serif; font-size:0.875rem; }}
    a {{ color:var(--accent); }}
    .content {{ background:var(--surface); border:1px solid var(--border);
                border-radius:var(--radius); padding:2rem; margin-bottom:2rem; }}
    .feedback-box {{ background:var(--surface); border:1px solid var(--border);
                     border-radius:var(--radius); padding:1.5rem; }}
    .feedback-box h2 {{ margin-top:0; font-size:1rem; }}
    textarea {{ width:100%; min-height:120px; font-family:inherit; font-size:0.95rem;
                border:1px solid var(--border); border-radius:4px; padding:0.75rem;
                resize:vertical; background:var(--bg); }}
    textarea:focus {{ outline:none; border-color:var(--accent); }}
    .btn {{ background:var(--accent); color:#fff; border:none; padding:0.55rem 1.4rem;
            border-radius:4px; font-size:0.95rem; cursor:pointer; margin-top:0.75rem; }}
    .btn:hover {{ background:var(--accent2); }}
    .saved {{ color:var(--green); font-size:0.875rem; margin-left:0.75rem; display:none; }}
    .options-list {{ margin:0.75rem 0 1.25rem; display:flex; flex-direction:column; gap:0.5rem; }}
    .option-card {{ display:flex; flex-direction:column; padding:0.75rem 1rem;
                    border:1px solid var(--border); border-radius:var(--radius);
                    background:var(--bg); cursor:pointer; transition:border-color 0.15s; }}
    .option-card-top {{ display:flex; align-items:flex-start; gap:0.75rem; }}
    .option-card:hover {{ border-color:var(--accent); }}
    .option-card input[type=checkbox] {{ margin-top:0.2rem; accent-color:var(--accent);
                                         width:1rem; height:1rem; flex-shrink:0; cursor:pointer; }}
    .option-card .option-label {{ font-family:system-ui,sans-serif; font-weight:600;
                                   font-size:0.925rem; color:var(--text); }}
    .option-card .option-desc {{ font-size:0.875rem; color:#666; margin-top:0.2rem;
                                  line-height:1.5; }}
    .select-all-bar {{ display:flex; align-items:center; justify-content:space-between;
                      margin-bottom:0.75rem; padding:0.4rem 0; border-bottom:1px solid var(--border); }}
    .btn-select-all {{ background:transparent; border:1px solid var(--accent); color:var(--accent);
                      padding:0.3rem 0.9rem; border-radius:4px; font-size:0.825rem; cursor:pointer;
                      font-family:system-ui,sans-serif; transition:background 0.15s; }}
    .btn-select-all:hover {{ background:var(--accent); color:#fff; }}
    .selection-count {{ font-size:0.8rem; color:#888; }}
  </style>
</head>
<body>
  <div class="content">{content}</div>
  <div class="feedback-box">
    <h2>Feedback</h2>
    <p style="font-size:0.875rem;color:#888;margin-bottom:0.75rem;">
      Leave feedback, questions, or change requests. Submit empty to signal approval.
    </p>
    {options_html}
    <textarea id="fb" placeholder="Your feedback..."></textarea>
    <div>
      <button class="btn" onclick="submit()">Submit</button>
      <span class="saved" id="saved">✓ Saved</span>
    </div>
  </div>
  <script>
    function countSelected() {{
      return Array.from(document.querySelectorAll('.option-card input[type=checkbox]')).filter(b=>b.checked).length;
    }}
    function updateSelectAllUI() {{
      const boxes = document.querySelectorAll('.option-card input[type=checkbox]');
      if (!boxes.length) return;
      const n = boxes.length;
      const checked = countSelected();
      const allChecked = checked === n;
      const btn = document.getElementById('toggle-all-btn');
      const cnt = document.getElementById('selection-count');
      if (btn) btn.textContent = allChecked ? `Deselect all (${{n}})` : `Select all (${{n}})`;
      if (cnt) cnt.textContent = `${{checked}} of ${{n}} selected`;
    }}
    function toggleAll() {{
      const boxes = document.querySelectorAll('.option-card input[type=checkbox]');
      const allChecked = countSelected() === boxes.length;
      boxes.forEach(b => {{ b.checked = !allChecked; }});
      updateSelectAllUI();
    }}
    document.querySelectorAll('.option-card-top').forEach(top => {{
      top.addEventListener('click', function(e) {{
        if (e.target.tagName !== 'INPUT') {{
          const cb = this.querySelector('input[type=checkbox]');
          cb.checked = !cb.checked;
        }}
        updateSelectAllUI();
      }});
    }});
    document.addEventListener('DOMContentLoaded', updateSelectAllUI);
    function submit() {{
      const text = document.getElementById('fb').value.trim();
      const boxes = document.querySelectorAll('.option-card input[type=checkbox]');
      const selected = Array.from(boxes).filter(b => b.checked).map(b => b.value);
      const payload = {{feedback: text, timestamp: new Date().toISOString()}};
      if (boxes.length) payload.selected = selected;
      fetch('/api/feedback', {{
        method: 'POST',
        headers: {{'Content-Type': 'application/json'}},
        body: JSON.stringify(payload)
      }}).then(r => r.json()).then(() => {{
        const s = document.getElementById('saved');
        s.style.display = 'inline';
        s.textContent = text ? '✓ Feedback saved' : '✓ Approval submitted';
        setTimeout(() => {{ s.style.display = 'none'; }}, 4000);
      }});
    }}
  </script>
</body>
</html>
"""


def _render_options_html(options: list) -> str:
    """Render checkbox option cards. Returns empty string when options is empty."""
    if not options:
        return ""

    def esc(s):
        return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")

    cards = []
    for opt in options:
        oid = opt.get("id", "")
        label = opt.get("label", "")
        desc = opt.get("description", "")
        preview_url = opt.get("preview_url", "")

        # Build the top row: checkbox + text
        top = (
            f'<div class="option-card-top">'
            f'<input type="checkbox" value="{esc(oid)}">'
            f'<div><div class="option-label">{esc(label)}</div>'
            f'<div class="option-desc">{esc(desc)}</div></div>'
            f'</div>'
        )

        # Optionally append an iframe preview
        iframe = ""
        if preview_url:
            iframe = (
                f'<iframe src="{esc(preview_url)}" '
                f'width="100%" height="500" '
                f'style="border:1px solid var(--border);border-radius:6px;margin-top:8px;" '
                f'loading="lazy"></iframe>'
            )

        cards.append(f'<div class="option-card">{top}{iframe}</div>')

    inner = "\n    ".join(cards)
    n = len(options)
    return (
        f'<div class="select-all-bar">'
        f'<button class="btn-select-all" id="toggle-all-btn" onclick="toggleAll()">Select all ({n})</button>'
        f'<span class="selection-count" id="selection-count">0 of {n} selected</span>'
        f'</div>\n'
        f'    <div class="options-list">\n    {inner}\n    </div>'
    )


# ---------------------------------------------------------------------------
# HTTP server
# ---------------------------------------------------------------------------

class Handler(BaseHTTPRequestHandler):
    def __init__(self, content_path: Path, workspace: Path, title: str, options: list,
                 preview_dir: Path | None, *args, **kwargs):
        self.content_path = content_path
        self.workspace = workspace
        self.title = title
        self.options = options
        self.preview_dir = preview_dir
        super().__init__(*args, **kwargs)

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            md = self.content_path.read_text()
            body = TEMPLATE.format(
                title=self.title,
                content=md_to_html(md),
                options_html=_render_options_html(self.options),
            )
            data = body.encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        elif self.path.startswith("/preview/") and self.preview_dir:
            filename = self.path[len("/preview/"):]
            # Prevent path traversal
            file_path = (self.preview_dir / filename).resolve()
            if self.preview_dir.resolve() in file_path.parents and file_path.is_file():
                data = file_path.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
            else:
                self.send_error(404)
        else:
            self.send_error(404)

    def do_POST(self):
        if self.path == "/api/feedback":
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length))
            fb_path = self.workspace / "feedback.json"
            existing = []
            if fb_path.exists():
                try:
                    existing = json.loads(fb_path.read_text()).get("reviews", [])
                except Exception:
                    pass
            entry = {"feedback": body.get("feedback", ""), "timestamp": body.get("timestamp", "")}
            if "selected" in body:
                entry["selected"] = body["selected"]
            existing.append(entry)
            fb_path.write_text(json.dumps({"reviews": existing}, indent=2))
            resp = b'{"ok":true}'
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(resp)))
            self.end_headers()
            self.wfile.write(resp)
        else:
            self.send_error(404)

    def log_message(self, *args):
        pass


def _kill_port(port: int):
    try:
        r = subprocess.run(["lsof", "-ti", f":{port}"], capture_output=True, text=True, timeout=5)
        for pid in r.stdout.strip().split("\n"):
            if pid.strip():
                try:
                    os.kill(int(pid.strip()), signal.SIGTERM)
                except (ProcessLookupError, ValueError):
                    pass
        if r.stdout.strip():
            time.sleep(0.4)
    except Exception:
        pass


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("content", type=Path)
    parser.add_argument("--workspace", type=Path, default=None)
    parser.add_argument("--port", type=int, default=PORT)
    parser.add_argument("--title", type=str, default=None)
    parser.add_argument("--options", type=Path, default=None, metavar="OPTIONS_JSON")
    parser.add_argument("--preview-dir", type=Path, default=None, metavar="DIR",
                        help="Directory of static preview files served at /preview/<file>")
    args = parser.parse_args()

    content = args.content.resolve()
    workspace = (args.workspace or content.parent).resolve()
    title = args.title or content.stem.replace("-", " ").replace("_", " ").title()
    port = args.port

    options = []
    if args.options:
        options_path = args.options.resolve()
        options = json.loads(options_path.read_text())

    preview_dir = args.preview_dir.resolve() if args.preview_dir else None

    workspace.mkdir(parents=True, exist_ok=True)
    _kill_port(port)

    from functools import partial
    handler = partial(Handler, content, workspace, title, options, preview_dir)
    server = HTTPServer(("127.0.0.1", port), handler)
    url = f"http://localhost:{port}"

    print(f"\n  Interactive review: {url}")
    print(f"  Feedback → {workspace}/feedback.json")
    print(f"  Ctrl+C to stop\n")

    import webbrowser
    webbrowser.open(url)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Server stopped.")


if __name__ == "__main__":
    main()
