#!/usr/bin/env python3
"""
Flatten a GitHub repo into a single static HTML page for fast skimming and Ctrl+F.
"""

from __future__ import annotations
import argparse
import html
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import webbrowser
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional
import tiktoken
from openai import OpenAI

# External deps
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import get_lexer_for_filename, TextLexer
import markdown

MAX_DEFAULT_BYTES = 50 * 1024
BINARY_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".svg", ".ico",
    ".pdf", ".zip", ".tar", ".gz", ".bz2", ".xz", ".7z", ".rar",
    ".mp3", ".mp4", ".mov", ".avi", ".mkv", ".wav", ".ogg", ".flac",
    ".ttf", ".otf", ".eot", ".woff", ".woff2",
    ".so", ".dll", ".dylib", ".class", ".jar", ".exe", ".bin",
}
MARKDOWN_EXTENSIONS = {".md", ".markdown", ".mdown", ".mkd", ".mkdn"}

@dataclass
class RenderDecision:
    include: bool
    reason: str  # "ok" | "binary" | "too_large" | "ignored"

@dataclass
class FileInfo:
    path: pathlib.Path  # absolute path on disk
    rel: str            # path relative to repo root (slash-separated)
    size: int
    decision: RenderDecision
    tokens: int = 0


def count_tokens(text: str, model: str = "gpt-4o") -> int:
    try:
        encoding = tiktoken.encoding_for_model(model)
        return len(encoding.encode(text))
    except Exception:
        # Fallback to rough estimation: ~4 chars per token
        return len(text) // 4


def run(cmd: List[str], cwd: str | None = None, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=cwd, check=check, text=True, capture_output=True)


def git_clone(url: str, dst: str) -> None:
    run(["git", "clone", "--depth", "1", url, dst])


def git_head_commit(repo_dir: str) -> str:
    try:
        cp = run(["git", "rev-parse", "HEAD"], cwd=repo_dir)
        return cp.stdout.strip()
    except Exception:
        return "(unknown)"


def bytes_human(n: int) -> str:
    """Human-readable bytes: 1 decimal for KiB and above, integer for B."""
    units = ["B", "KiB", "MiB", "GiB", "TiB"]
    f = float(n)
    i = 0
    while f >= 1024.0 and i < len(units) - 1:
        f /= 1024.0
        i += 1
    if i == 0:
        return f"{int(f)} {units[i]}"
    else:
        return f"{f:.1f} {units[i]}"


def looks_binary(path: pathlib.Path) -> bool:
    ext = path.suffix.lower()
    if ext in BINARY_EXTENSIONS:
        return True
    try:
        with path.open("rb") as f:
            chunk = f.read(8192)
        if b"\x00" in chunk:
            return True
        # Heuristic: try UTF-8 decode; if it hard-fails, likely binary
        try:
            chunk.decode("utf-8")
        except UnicodeDecodeError:
            return True
        return False
    except Exception:
        # If unreadable, treat as binary to be safe
        return True


def decide_file(path: pathlib.Path, repo_root: pathlib.Path, max_bytes: int) -> FileInfo:
    rel = str(path.relative_to(repo_root)).replace(os.sep, "/")
    try:
        size = path.stat().st_size
    except FileNotFoundError:
        size = 0
    # Ignore VCS and build junk
    if "/.git/" in f"/{rel}/" or rel.startswith(".git/"):
        return FileInfo(path, rel, size, RenderDecision(False, "ignored"))
    if size > max_bytes:
        return FileInfo(path, rel, size, RenderDecision(False, "too_large"))
    if looks_binary(path):
        return FileInfo(path, rel, size, RenderDecision(False, "binary"))
    return FileInfo(path, rel, size, RenderDecision(True, "ok"))


def collect_files(repo_root: pathlib.Path, max_bytes: int) -> List[FileInfo]:
    infos: List[FileInfo] = []
    for p in sorted(repo_root.rglob("*")):
        if p.is_symlink():
            continue
        if p.is_file():
            info = decide_file(p, repo_root, max_bytes)
            if info.decision.include:
                try:
                    text = read_text(p)
                    info.tokens = count_tokens(text)
                except Exception:
                    info.tokens = 0
            infos.append(info)
    return infos


def generate_tree_fallback(root: pathlib.Path) -> str:
    """Minimal tree-like output if `tree` command is missing."""
    lines: List[str] = []

    def walk(dir_path: pathlib.Path, prefix: str = ""):
        entries = [e for e in dir_path.iterdir() if e.name != ".git"]
        entries.sort(key=lambda e: (not e.is_dir(), e.name.lower()))
        for i, e in enumerate(entries):
            last = i == len(entries) - 1
            branch = "└── " if last else "├── "
            lines.append(prefix + branch + e.name)
            if e.is_dir():
                extension = "    " if last else "│   "
                walk(e, prefix + extension)

    lines.append(root.name)
    walk(root)
    return "\n".join(lines)


def try_tree_command(root: pathlib.Path) -> str:
    try:
        cp = run(["tree", "-a", "."], cwd=str(root))
        return cp.stdout
    except Exception:
        return generate_tree_fallback(root)


def read_text(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def render_markdown_text(md_text: str) -> str:
    return markdown.markdown(md_text, extensions=["fenced_code", "tables", "toc"])  # type: ignore


def highlight_code(text: str, filename: str, formatter: HtmlFormatter) -> str:
    try:
        lexer = get_lexer_for_filename(filename, stripall=False)
    except Exception:
        lexer = TextLexer(stripall=False)
    return highlight(text, lexer, formatter)


def slugify(path_str: str) -> str:
    # Simple slug: keep alnum, dash, underscore; replace others with '-'
    out = []
    for ch in path_str:
        if ch.isalnum() or ch in {"-", "_"}:
            out.append(ch)
        else:
            out.append("-")
    return "".join(out)


def chunk_files(infos: List[FileInfo], max_tokens: int) -> List[List[FileInfo]]:
    """Group files into chunks based on token count."""
    chunks: List[List[FileInfo]] = []
    current_chunk: List[FileInfo] = []
    current_tokens = 0

    # Sort files by directory to keep logical domains together
    sorted_infos = sorted(infos, key=lambda i: i.rel)

    for info in sorted_infos:
        if not info.decision.include:
            continue
        
        if info.tokens > max_tokens:
            # Single file exceeds limit, put it in its own chunk
            if current_chunk:
                chunks.append(current_chunk)
            chunks.append([info])
            current_chunk = []
            current_tokens = 0
            continue

        if current_tokens + info.tokens > max_tokens:
            chunks.append(current_chunk)
            current_chunk = [info]
            current_tokens = info.tokens
        else:
            current_chunk.append(info)
            current_tokens += info.tokens

    if current_chunk:
        chunks.append(current_chunk)

    return chunks


def generate_structural_index(repo_dir: pathlib.Path, infos: List[FileInfo]) -> Dict[str, str]:
    """Generate a structural map of the repository without an LLM."""
    # Group paths and identify key files
    structural_data = {}
    seen_dirs = set()
    for i in infos:
        rel = i.rel
        parts = rel.split('/')
        # Add all parent directories
        for j in range(1, len(parts)):
            parent = '/'.join(parts[:j]) + '/'
            if parent not in seen_dirs:
                structural_data[parent] = "[Directory]"
                seen_dirs.add(parent)
        
        # Add key files
        if "/" not in rel or rel.endswith("README.md") or rel.endswith("__init__.py") or "main" in rel or "lib.rs" in rel:
            ext = pathlib.Path(rel).suffix
            structural_data[rel] = f"[File: {ext or 'no extension'}]"

    return structural_data


def format_index(index_data: Dict[str, str]) -> str:
    """Format the structural index into the Karpathy-style index.txt."""
    lines = []
    sorted_paths = sorted(index_data.keys())
    for i, path in enumerate(sorted_paths, 1):
        desc = index_data.get(path, "No description available.")
        lines.append(f"[{i:03d}] {path} - {desc}")
    return "\n".join(lines)


def generate_cxml_text(infos: List[FileInfo]) -> str:
    """Generate CXML format text for LLM consumption."""
    lines = ["<documents>"]

    rendered = [i for i in infos if i.decision.include]
    for index, i in enumerate(rendered, 1):
        lines.append(f'<document index="{index}">')
        lines.append(f"<source>{i.rel}</source>")
        lines.append("<document_content>")

        try:
            text = read_text(i.path)
            lines.append(text)
        except Exception as e:
            lines.append(f"Failed to read: {str(e)}")

        lines.append("</document_content>")
        lines.append("</document>")

    lines.append("</documents>")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="Flatten a GitHub repo into multiple CXML chunks and a semantic index")
    ap.add_argument("repo_url", help="GitHub repo URL (https://github.com/owner/repo[.git])")
    ap.add_argument("-o", "--out-dir", help="Output directory for CXML chunks and index.txt (default: current directory)")
    ap.add_argument("--max-bytes", type=int, default=MAX_DEFAULT_BYTES, help="Max file size to render (bytes)")
    ap.add_argument("--max-tokens", type=int, default=100000, help="Max tokens per CXML chunk (default: 100k)")
    ap.add_argument("--no-open", action="store_true", help="Don't open the output directory")
    args = ap.parse_args()

    # Set default output directory if not provided
    if args.out_dir is None:
        args.out_dir = "."
    out_dir = pathlib.Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    tmpdir = tempfile.mkdtemp(prefix="rendergit_")
    repo_dir = pathlib.Path(tmpdir, "repo")

    try:
        print(f"📁 Cloning {args.repo_url} to temporary directory: {repo_dir}", file=sys.stderr)
        git_clone(args.repo_url, str(repo_dir))
        head = git_head_commit(str(repo_dir))
        print(f"✓ Clone complete (HEAD: {head[:8]})", file=sys.stderr)

        print(f"📊 Scanning files and counting tokens...", file=sys.stderr)
        infos = collect_files(repo_dir, args.max_bytes)
        rendered_count = sum(1 for i in infos if i.decision.include)
        total_tokens = sum(i.tokens for i in infos)
        print(f"✓ Found {len(infos)} files, {rendered_count} to be rendered, total ~{total_tokens} tokens", file=sys.stderr)

        print(f"🏗️  Generating structural index...", file=sys.stderr)
        index_data = generate_structural_index(repo_dir, infos)
        index_txt = format_index(index_data)
        (out_dir / "index.txt").write_text(index_txt)
        print(f"✓ Wrote index.txt", file=sys.stderr)

        print(f"📦 Chunking files (max {args.max_tokens} tokens)...", file=sys.stderr)
        chunks = chunk_files(infos, args.max_tokens)
        print(f"✓ Created {len(chunks)} chunk(s)", file=sys.stderr)

        for idx, chunk in enumerate(chunks, 1):
            cxml_text = generate_cxml_text(chunk)
            chunk_filename = f"chunk_{idx:03d}.cxml"
            if len(chunks) == 1:
                chunk_filename = "repo.cxml"
            (out_dir / chunk_filename).write_text(cxml_text)
            print(f"✓ Wrote {chunk_filename}", file=sys.stderr)

        if not args.no_open:
            import subprocess
            if sys.platform == "darwin":
                subprocess.run(["open", str(out_dir)])
            elif sys.platform == "win32":
                os.startfile(str(out_dir))
            else:
                subprocess.run(["xdg-open", str(out_dir)])

        print(f"🗑️  Cleaning up temporary directory: {tmpdir}", file=sys.stderr)
        return 0
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == "__main__":
    main()
