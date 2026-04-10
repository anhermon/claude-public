#!/usr/bin/env python3
"""
kb-to-wiki.py — Convert a markdown knowledge base into a browsable HTML wiki.

Modes:
  Server mode (default): Starts a local HTTP server that dynamically loads
      markdown files via API endpoints. Open http://localhost:<port> to browse.

  Static mode (--no-server): Generates a single self-contained HTML file with
      all content embedded. No server or internet connection required to view.

Usage:
  python kb-to-wiki.py --source ~/knowledge-base --title "My KB" --port 8000
  python kb-to-wiki.py --source ~/docs --output wiki.html --no-server

Requirements: Python 3.8+, stdlib only. PyYAML is optional (used if installed).
"""

import argparse
import fnmatch
import html
import json
import os
import re
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import unquote, quote

# ---------------------------------------------------------------------------
# YAML frontmatter parser (stdlib fallback; uses pyyaml when available)
# ---------------------------------------------------------------------------

def _parse_frontmatter_stdlib(text):
    """Extract YAML frontmatter using only stdlib. Returns (meta_dict, body)."""
    meta = {}
    if not text.startswith("---"):
        return meta, text
    end = text.find("\n---", 3)
    if end == -1:
        return meta, text
    block = text[3:end].strip()
    body = text[end + 4:].lstrip("\n")
    for line in block.splitlines():
        if ":" not in line:
            continue
        key, _, val = line.partition(":")
        key = key.strip()
        val = val.strip()
        if not key:
            continue
        # Handle inline lists: [a, b, c]
        if val.startswith("[") and val.endswith("]"):
            items = [v.strip().strip("\"'") for v in val[1:-1].split(",") if v.strip()]
            meta[key] = items
        else:
            meta[key] = val.strip("\"'")
    return meta, body


def parse_frontmatter(text):
    """Parse YAML frontmatter from markdown text. Returns (meta, body)."""
    try:
        import yaml  # pyyaml
        if text.startswith("---"):
            end = text.find("\n---", 3)
            if end != -1:
                block = text[3:end]
                body = text[end + 4:].lstrip("\n")
                try:
                    meta = yaml.safe_load(block) or {}
                    return meta, body
                except yaml.YAMLError:
                    pass
        return {}, text
    except ImportError:
        return _parse_frontmatter_stdlib(text)


# ---------------------------------------------------------------------------
# File tree builder
# ---------------------------------------------------------------------------

DEFAULT_EXCLUDE = {".git", "__pycache__", ".DS_Store", "node_modules", ".obsidian"}


def build_tree(source_dir: Path, exclude_patterns: list[str]) -> dict:
    """Recursively build a JSON-serializable file tree of all .md files."""

    def should_exclude(name: str) -> bool:
        for pat in exclude_patterns:
            if fnmatch.fnmatch(name, pat):
                return True
        return name in DEFAULT_EXCLUDE

    def walk(directory: Path, rel_base: Path) -> dict:
        node = {
            "name": directory.name,
            "type": "folder",
            "path": str(directory.relative_to(source_dir)).replace("\\", "/"),
            "children": [],
        }
        try:
            entries = sorted(directory.iterdir(), key=lambda p: (p.is_file(), p.name.lower()))
        except PermissionError:
            return node

        for entry in entries:
            if should_exclude(entry.name):
                continue
            if entry.is_dir():
                child = walk(entry, rel_base)
                # Only add folders that contain at least one .md file
                if child["children"]:
                    node["children"].append(child)
            elif entry.is_file() and entry.suffix.lower() == ".md":
                rel_path = entry.relative_to(source_dir)
                rel_str = str(rel_path).replace("\\", "/")
                title = extract_title(entry)
                node["children"].append({
                    "name": entry.stem,
                    "type": "file",
                    "path": rel_str,
                    "title": title,
                })
        return node

    return walk(source_dir, source_dir)


def extract_title(file_path: Path) -> str:
    """Extract the best title for a file: frontmatter > first H1 > filename."""
    try:
        text = file_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return file_path.stem.replace("-", " ").replace("_", " ").title()

    meta, body = parse_frontmatter(text)
    if meta.get("title"):
        return str(meta["title"])

    for line in body.splitlines():
        line = line.strip()
        if line.startswith("# "):
            return line[2:].strip()

    return file_path.stem.replace("-", " ").replace("_", " ").title()


# ---------------------------------------------------------------------------
# HTML / JS generation helpers
# ---------------------------------------------------------------------------

# The full UI is self-contained in this string. Placeholders:
#   {{TITLE}}        — wiki title
#   {{THEME_CLASS}}  — "dark" or ""
#   {{MODE}}         — "server" or "static"
#   {{STATIC_DATA}}  — JSON blob (static mode only), or empty string

_HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en" class="{{THEME_CLASS}}">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{{TITLE}}</title>
<style>
/* ---- Reset & Variables ---- */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

:root {
  --bg: #ffffff;
  --bg2: #f8f8f8;
  --border: #e0e0e0;
  --text: #202020;
  --text2: #555555;
  --accent: #2563eb;
  --accent-hover: #1d4ed8;
  --sidebar-w: 260px;
  --toc-w: 220px;
  --header-h: 48px;
  --code-bg: #f3f3f3;
  --tag-bg: #e8f0fe;
  --tag-text: #1a56db;
}
html.dark {
  --bg: #1a1a1a;
  --bg2: #242424;
  --border: #333333;
  --text: #e8e8e8;
  --text2: #999999;
  --accent: #60a5fa;
  --accent-hover: #93c5fd;
  --code-bg: #2d2d2d;
  --tag-bg: #1e3a5f;
  --tag-text: #93c5fd;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif;
  background: var(--bg);
  color: var(--text);
  line-height: 1.6;
  height: 100vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* ---- Header ---- */
#header {
  height: var(--header-h);
  background: var(--bg2);
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: center;
  padding: 0 1rem;
  gap: 1rem;
  flex-shrink: 0;
  z-index: 100;
}
#header h1 { font-size: 1rem; font-weight: 600; white-space: nowrap; }
#search-wrap { flex: 1; max-width: 480px; position: relative; }
#search {
  width: 100%;
  padding: 0.3rem 0.75rem;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: var(--bg);
  color: var(--text);
  font-size: 0.875rem;
  outline: none;
}
#search:focus { border-color: var(--accent); box-shadow: 0 0 0 2px color-mix(in srgb, var(--accent) 20%, transparent); }
#search-results {
  position: absolute;
  top: calc(100% + 4px);
  left: 0; right: 0;
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: 6px;
  max-height: 320px;
  overflow-y: auto;
  z-index: 200;
  box-shadow: 0 4px 20px rgba(0,0,0,0.15);
  display: none;
}
#search-results.open { display: block; }
.search-item {
  padding: 0.5rem 0.75rem;
  cursor: pointer;
  border-bottom: 1px solid var(--border);
}
.search-item:last-child { border-bottom: none; }
.search-item:hover, .search-item.active { background: var(--bg2); }
.search-item-title { font-size: 0.875rem; font-weight: 500; }
.search-item-path { font-size: 0.75rem; color: var(--text2); }
.search-highlight { background: color-mix(in srgb, var(--accent) 25%, transparent); border-radius: 2px; padding: 0 1px; }

#dark-toggle {
  margin-left: auto;
  background: none;
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 0.25rem 0.6rem;
  cursor: pointer;
  font-size: 1rem;
  color: var(--text);
  line-height: 1;
}
#dark-toggle:hover { background: var(--bg2); }

/* ---- Layout ---- */
#layout {
  display: flex;
  flex: 1;
  overflow: hidden;
}

/* ---- Sidebar ---- */
#sidebar {
  width: var(--sidebar-w);
  background: var(--bg2);
  border-right: 1px solid var(--border);
  overflow-y: auto;
  flex-shrink: 0;
  padding: 0.75rem 0;
}
.sidebar-section { margin-bottom: 0.25rem; }
.sidebar-folder {
  display: flex;
  align-items: center;
  padding: 0.3rem 0.75rem;
  cursor: pointer;
  font-size: 0.8rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.03em;
  color: var(--text2);
  user-select: none;
  gap: 0.4rem;
}
.sidebar-folder:hover { color: var(--text); }
.folder-arrow { transition: transform 0.15s; font-size: 0.65rem; }
.folder-arrow.open { transform: rotate(90deg); }
.sidebar-children { padding-left: 0.75rem; }
.sidebar-children.collapsed { display: none; }
.sidebar-file {
  display: block;
  padding: 0.28rem 0.75rem;
  font-size: 0.845rem;
  color: var(--text2);
  cursor: pointer;
  border-radius: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  text-decoration: none;
}
.sidebar-file:hover { background: var(--border); color: var(--text); }
.sidebar-file.active {
  background: color-mix(in srgb, var(--accent) 15%, transparent);
  color: var(--accent);
  font-weight: 500;
}

/* ---- Article ---- */
#content {
  flex: 1;
  overflow-y: auto;
  padding: 2rem 2.5rem;
  min-width: 0;
}
#article-meta { margin-bottom: 1.5rem; }
#article-meta .tags { display: flex; flex-wrap: wrap; gap: 0.4rem; margin-top: 0.5rem; }
.tag {
  font-size: 0.75rem;
  background: var(--tag-bg);
  color: var(--tag-text);
  padding: 0.15rem 0.5rem;
  border-radius: 999px;
}
#article-meta .description { font-size: 0.9rem; color: var(--text2); margin-top: 0.4rem; }
#article { max-width: 820px; }

/* Markdown rendered content */
#article h1 { font-size: 1.8rem; margin: 1.5rem 0 0.75rem; border-bottom: 1px solid var(--border); padding-bottom: 0.4rem; }
#article h2 { font-size: 1.35rem; margin: 1.4rem 0 0.6rem; }
#article h3 { font-size: 1.1rem; margin: 1.2rem 0 0.5rem; }
#article h4, #article h5, #article h6 { font-size: 1rem; margin: 1rem 0 0.4rem; }
#article p { margin: 0.75rem 0; }
#article ul, #article ol { margin: 0.75rem 0 0.75rem 1.5rem; }
#article li { margin: 0.2rem 0; }
#article a { color: var(--accent); text-decoration: none; }
#article a:hover { text-decoration: underline; }
#article code {
  font-family: "Fira Code", "Cascadia Code", Consolas, monospace;
  font-size: 0.875em;
  background: var(--code-bg);
  padding: 0.1em 0.35em;
  border-radius: 3px;
}
#article pre {
  background: var(--code-bg);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 1rem;
  overflow-x: auto;
  margin: 1rem 0;
}
#article pre code { background: none; padding: 0; font-size: 0.85rem; }
#article blockquote {
  border-left: 3px solid var(--accent);
  padding: 0.5rem 1rem;
  margin: 1rem 0;
  color: var(--text2);
  background: var(--bg2);
  border-radius: 0 4px 4px 0;
}
#article table { border-collapse: collapse; width: 100%; margin: 1rem 0; }
#article th, #article td { border: 1px solid var(--border); padding: 0.5rem 0.75rem; text-align: left; }
#article th { background: var(--bg2); font-weight: 600; }
#article img { max-width: 100%; border-radius: 4px; }
#article hr { border: none; border-top: 1px solid var(--border); margin: 1.5rem 0; }

.wiki-link { color: var(--accent); text-decoration: none; cursor: pointer; }
.wiki-link:hover { text-decoration: underline; }
.wiki-link-missing { color: var(--text2); text-decoration: line-through; cursor: default; }

/* Loading / empty state */
#welcome {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 60%;
  color: var(--text2);
  text-align: center;
  gap: 0.5rem;
}
#welcome h2 { color: var(--text); }
#loading { color: var(--text2); padding: 2rem; }

/* ---- TOC ---- */
#toc {
  width: var(--toc-w);
  flex-shrink: 0;
  overflow-y: auto;
  padding: 1.5rem 1rem;
  border-left: 1px solid var(--border);
  font-size: 0.8rem;
}
#toc h3 { font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.06em; color: var(--text2); margin-bottom: 0.5rem; }
#toc-list { list-style: none; }
#toc-list li { margin: 0.2rem 0; }
#toc-list a { color: var(--text2); text-decoration: none; display: block; padding: 0.1rem 0; }
#toc-list a:hover, #toc-list a.active { color: var(--accent); }
#toc-list .toc-h3 { padding-left: 0.75rem; font-size: 0.77rem; }
#toc-list .toc-h4 { padding-left: 1.5rem; font-size: 0.75rem; }

@media (max-width: 900px) {
  #toc { display: none; }
  :root { --sidebar-w: 220px; }
}
@media (max-width: 620px) {
  #sidebar { display: none; }
  #content { padding: 1rem; }
}
</style>
</head>
<body>

<header id="header">
  <h1 id="wiki-title">{{TITLE}}</h1>
  <div id="search-wrap">
    <input id="search" type="search" placeholder="Search…" autocomplete="off" spellcheck="false">
    <div id="search-results"></div>
  </div>
  <button id="dark-toggle" title="Toggle dark mode" aria-label="Toggle dark mode">🌙</button>
</header>

<div id="layout">
  <nav id="sidebar" aria-label="File tree"></nav>

  <main id="content">
    <div id="welcome">
      <h2>{{TITLE}}</h2>
      <p>Select a file from the sidebar, or use the search bar.</p>
    </div>
    <div id="loading" style="display:none">Loading…</div>
    <div id="article-meta" style="display:none">
      <div class="description" id="meta-desc"></div>
      <div class="tags" id="meta-tags"></div>
    </div>
    <div id="article"></div>
  </main>

  <aside id="toc">
    <h3>Contents</h3>
    <ul id="toc-list"></ul>
  </aside>
</div>

<script>
// ---- Configuration ----
const WIKI_MODE = "{{MODE}}";  // "server" or "static"
const STATIC_DATA = {{STATIC_DATA}};  // null in server mode, {tree, files} in static

// ---- State ----
let fileTree = null;
let allFiles = [];   // flat list: {path, title}
let currentPath = null;
let searchIndex = [];  // [{path, title, content}]

// ---- Dark mode ----
(function initTheme() {
  const saved = localStorage.getItem("wiki-theme");
  if (saved === "dark" || (!saved && window.matchMedia("(prefers-color-scheme: dark)").matches)) {
    document.documentElement.classList.add("dark");
  } else {
    document.documentElement.classList.remove("dark");
  }
  updateToggleIcon();
})();

function updateToggleIcon() {
  document.getElementById("dark-toggle").textContent =
    document.documentElement.classList.contains("dark") ? "☀️" : "🌙";
}

document.getElementById("dark-toggle").addEventListener("click", () => {
  const isDark = document.documentElement.classList.toggle("dark");
  localStorage.setItem("wiki-theme", isDark ? "dark" : "light");
  updateToggleIcon();
});

// ---- Marked.js loader ----
function ensureMarked(cb) {
  if (window.marked) return cb();
  const s = document.createElement("script");
  s.src = "https://cdn.jsdelivr.net/npm/marked/marked.min.js";
  s.onload = cb;
  s.onerror = () => {
    // Minimal fallback renderer if CDN is unavailable
    window.marked = { parse: minimalMarkdown };
    cb();
  };
  document.head.appendChild(s);
}

// Minimal fallback markdown renderer (covers headings, bold, italic, code, links, lists)
function minimalMarkdown(md) {
  let h = md
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
    // Fenced code blocks
    .replace(/```[\w]*\n([\s\S]*?)```/gm, (_, c) => `<pre><code>${c.trimEnd()}</code></pre>`)
    // Headings
    .replace(/^#{6}\s+(.+)$/gm, "<h6>$1</h6>")
    .replace(/^#{5}\s+(.+)$/gm, "<h5>$1</h5>")
    .replace(/^#{4}\s+(.+)$/gm, "<h4>$1</h4>")
    .replace(/^###\s+(.+)$/gm, "<h3>$1</h3>")
    .replace(/^##\s+(.+)$/gm, "<h2>$1</h2>")
    .replace(/^#\s+(.+)$/gm, "<h1>$1</h1>")
    // Blockquote
    .replace(/^>\s(.+)$/gm, "<blockquote>$1</blockquote>")
    // Horizontal rule
    .replace(/^(---|\*\*\*|___)\s*$/gm, "<hr>")
    // Bold / italic
    .replace(/\*\*\*(.+?)\*\*\*/g, "<strong><em>$1</em></strong>")
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/\*(.+?)\*/g, "<em>$1</em>")
    .replace(/__(.+?)__/g, "<strong>$1</strong>")
    .replace(/_(.+?)_/g, "<em>$1</em>")
    // Inline code
    .replace(/`([^`]+)`/g, "<code>$1</code>")
    // Links
    .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2">$1</a>')
    // Unordered list items
    .replace(/^\s*[-*+]\s+(.+)$/gm, "<li>$1</li>")
    // Ordered list items
    .replace(/^\s*\d+\.\s+(.+)$/gm, "<li>$1</li>")
    // Wrap consecutive <li> in <ul>
    .replace(/(<li>[\s\S]*?<\/li>)(\n<li>[\s\S]*?<\/li>)*/g, m => `<ul>${m}</ul>`)
    // Paragraphs — blank-line separated
    .replace(/\n\n([^<\n][^\n]*)\n\n/g, "\n\n<p>$1</p>\n\n");
  return h;
}

// ---- Obsidian wiki-link preprocessing ----
// Convert [[path|text]] and [[path]] to placeholder spans before marked renders
function preprocessWikiLinks(md) {
  return md.replace(/\[\[([^\]|]+?)(?:\|([^\]]+?))?\]\]/g, (_, path, display) => {
    const text = display || path.split("/").pop().replace(/\.md$/, "");
    const encoded = encodeURIComponent(path.trim());
    return `<WIKILINK data-path="${encoded}" data-text="${text.replace(/"/g, "&quot;")}">`;
  });
}

// After marked renders, replace WIKILINK placeholders with real elements
function postprocessWikiLinks(htmlStr) {
  return htmlStr.replace(
    /<WIKILINK data-path="([^"]*)" data-text="([^"]*)"><\/WIKILINK>|<WIKILINK data-path="([^"]*)" data-text="([^"]*)">|<p>(<WIKILINK[^>]*>)<\/p>/g,
    (full, p1, t1, p2, t2) => {
      const path = decodeURIComponent(p1 || p2 || "");
      const text = t1 || t2 || path;
      return `<a class="wiki-link" data-path="${encodeURIComponent(path)}" href="#">${escHtml(text)}</a>`;
    }
  );
}

// Second pass: simpler replacement for leftover WIKILINK tags
function fixWikiLinks(container) {
  container.querySelectorAll("a.wiki-link[data-path]").forEach(a => {
    a.addEventListener("click", e => {
      e.preventDefault();
      const path = decodeURIComponent(a.dataset.path);
      // Try to find matching file by path or stem
      const match = allFiles.find(f =>
        f.path === path ||
        f.path === path + ".md" ||
        f.path.endsWith("/" + path) ||
        f.path.endsWith("/" + path + ".md") ||
        f.title.toLowerCase() === path.toLowerCase()
      );
      if (match) loadFile(match.path);
    });
  });
}

function escHtml(s) {
  return s.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");
}

// ---- File tree rendering ----
function flattenTree(node, acc = []) {
  if (node.type === "file") {
    acc.push({ path: node.path, title: node.title });
  } else if (node.children) {
    node.children.forEach(c => flattenTree(c, acc));
  }
  return acc;
}

function renderSidebar(tree) {
  const nav = document.getElementById("sidebar");
  nav.innerHTML = "";
  if (!tree.children || tree.children.length === 0) {
    nav.innerHTML = '<p style="padding:1rem;font-size:0.8rem;color:var(--text2)">No .md files found.</p>';
    return;
  }
  tree.children.forEach(child => nav.appendChild(renderNode(child, 0)));
}

function renderNode(node, depth) {
  if (node.type === "file") {
    const a = document.createElement("a");
    a.className = "sidebar-file";
    a.textContent = node.title || node.name;
    a.title = node.path;
    a.href = "#";
    a.dataset.path = node.path;
    a.addEventListener("click", e => { e.preventDefault(); loadFile(node.path); });
    return a;
  }

  // Folder
  const section = document.createElement("div");
  section.className = "sidebar-section";

  const header = document.createElement("div");
  header.className = "sidebar-folder";
  const arrow = document.createElement("span");
  arrow.className = "folder-arrow open";
  arrow.textContent = "▶";
  header.appendChild(arrow);
  header.appendChild(document.createTextNode(node.name));
  section.appendChild(header);

  const children = document.createElement("div");
  children.className = "sidebar-children";
  (node.children || []).forEach(child => children.appendChild(renderNode(child, depth + 1)));
  section.appendChild(children);

  header.addEventListener("click", () => {
    const collapsed = children.classList.toggle("collapsed");
    arrow.classList.toggle("open", !collapsed);
  });

  return section;
}

// ---- TOC generation ----
function buildToc(container) {
  const tocList = document.getElementById("toc-list");
  tocList.innerHTML = "";
  const headings = container.querySelectorAll("h2, h3, h4");
  if (headings.length === 0) return;

  headings.forEach((h, i) => {
    const id = `toc-${i}`;
    h.id = id;
    const li = document.createElement("li");
    const a = document.createElement("a");
    a.href = `#${id}`;
    a.textContent = h.textContent;
    a.className = `toc-${h.tagName.toLowerCase()}`;
    li.appendChild(a);
    tocList.appendChild(li);
  });

  // Highlight on scroll
  const obs = new IntersectionObserver(entries => {
    entries.forEach(e => {
      const link = tocList.querySelector(`a[href="#${e.target.id}"]`);
      if (link) link.classList.toggle("active", e.isIntersecting);
    });
  }, { rootMargin: "0px 0px -70% 0px" });
  headings.forEach(h => obs.observe(h));
}

// ---- File loading ----
async function loadFile(path) {
  currentPath = path;

  // Update active state
  document.querySelectorAll(".sidebar-file").forEach(a => {
    a.classList.toggle("active", a.dataset.path === path);
  });

  document.getElementById("welcome").style.display = "none";
  document.getElementById("loading").style.display = "block";
  document.getElementById("article").innerHTML = "";
  document.getElementById("toc-list").innerHTML = "";
  document.getElementById("article-meta").style.display = "none";

  let rawMarkdown;
  let meta = {};

  try {
    if (WIKI_MODE === "static") {
      rawMarkdown = STATIC_DATA.files[path];
      if (rawMarkdown === undefined) throw new Error("File not found in static data");
    } else {
      const encodedPath = path.split("/").map(p => encodeURIComponent(p)).join("/");
      const res = await fetch("/api/files/" + encodedPath);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      rawMarkdown = await res.text();
    }
  } catch (err) {
    document.getElementById("loading").style.display = "none";
    document.getElementById("article").innerHTML = `<p style="color:var(--text2)">Could not load <code>${escHtml(path)}</code>: ${escHtml(err.message)}</p>`;
    return;
  }

  // Parse frontmatter (client-side, simple)
  let body = rawMarkdown;
  if (rawMarkdown.startsWith("---")) {
    const end = rawMarkdown.indexOf("\n---", 3);
    if (end !== -1) {
      const block = rawMarkdown.slice(3, end);
      body = rawMarkdown.slice(end + 4).trimStart();
      block.split("\n").forEach(line => {
        const colon = line.indexOf(":");
        if (colon > 0) {
          const k = line.slice(0, colon).trim();
          let v = line.slice(colon + 1).trim();
          if (v.startsWith("[") && v.endsWith("]")) {
            v = v.slice(1, -1).split(",").map(s => s.trim().replace(/^['"]|['"]$/g, ""));
          } else {
            v = v.replace(/^['"]|['"]$/g, "");
          }
          meta[k] = v;
        }
      });
    }
  }

  // Render metadata
  const metaDiv = document.getElementById("article-meta");
  const descEl = document.getElementById("meta-desc");
  const tagsEl = document.getElementById("meta-tags");
  descEl.textContent = "";
  tagsEl.innerHTML = "";
  if (meta.description) { descEl.textContent = meta.description; metaDiv.style.display = ""; }
  if (Array.isArray(meta.tags) && meta.tags.length) {
    meta.tags.forEach(t => {
      const span = document.createElement("span");
      span.className = "tag";
      span.textContent = t;
      tagsEl.appendChild(span);
    });
    metaDiv.style.display = "";
  }

  ensureMarked(() => {
    document.getElementById("loading").style.display = "none";
    const article = document.getElementById("article");

    // Pre-process wiki links before markdown rendering
    const processed = preprocessWikiLinks(body);
    let rendered = marked.parse(processed);
    rendered = postprocessWikiLinks(rendered);
    article.innerHTML = rendered;

    fixWikiLinks(article);
    buildToc(article);

    // Scroll to top
    document.getElementById("content").scrollTop = 0;

    // Update page title
    const titleEl = article.querySelector("h1");
    document.title = (titleEl ? titleEl.textContent + " — " : "") + document.getElementById("wiki-title").textContent;
  });
}

// ---- Search ----
function buildSearchIndex(files) {
  searchIndex = [];
  if (WIKI_MODE === "static" && STATIC_DATA) {
    files.forEach(f => {
      const raw = STATIC_DATA.files[f.path] || "";
      const [, body] = extractFrontmatterText(raw);
      searchIndex.push({ path: f.path, title: f.title, content: body.toLowerCase() });
    });
  } else {
    // In server mode, we index titles only (fetching all files upfront is expensive)
    files.forEach(f => {
      searchIndex.push({ path: f.path, title: f.title, content: f.title.toLowerCase() });
    });
  }
}

function extractFrontmatterText(text) {
  if (!text.startsWith("---")) return [{}, text];
  const end = text.indexOf("\n---", 3);
  if (end === -1) return [{}, text];
  return [{}, text.slice(end + 4).trimStart()];
}

let searchTimeout;
const searchInput = document.getElementById("search");
const searchResults = document.getElementById("search-results");

searchInput.addEventListener("input", () => {
  clearTimeout(searchTimeout);
  searchTimeout = setTimeout(doSearch, 150);
});
searchInput.addEventListener("focus", () => { if (searchInput.value) doSearch(); });
searchInput.addEventListener("blur", () => setTimeout(() => searchResults.classList.remove("open"), 200));
document.addEventListener("keydown", e => {
  if (e.key === "Escape") { searchResults.classList.remove("open"); searchInput.blur(); }
});

function doSearch() {
  const q = searchInput.value.trim().toLowerCase();
  if (!q) { searchResults.classList.remove("open"); return; }
  const ql = q.toLowerCase();
  const results = searchIndex
    .filter(f => f.title.toLowerCase().includes(ql) || f.content.includes(ql))
    .slice(0, 20);

  searchResults.innerHTML = "";
  if (results.length === 0) {
    searchResults.innerHTML = '<div class="search-item" style="color:var(--text2)">No results</div>';
  } else {
    results.forEach(r => {
      const item = document.createElement("div");
      item.className = "search-item";
      item.innerHTML = `<div class="search-item-title">${highlightMatch(r.title, q)}</div><div class="search-item-path">${escHtml(r.path)}</div>`;
      item.addEventListener("mousedown", () => { loadFile(r.path); searchInput.value = ""; searchResults.classList.remove("open"); });
      searchResults.appendChild(item);
    });
  }
  searchResults.classList.add("open");
}

function highlightMatch(text, query) {
  const idx = text.toLowerCase().indexOf(query.toLowerCase());
  if (idx === -1) return escHtml(text);
  return escHtml(text.slice(0, idx)) +
    `<mark class="search-highlight">${escHtml(text.slice(idx, idx + query.length))}</mark>` +
    escHtml(text.slice(idx + query.length));
}

// ---- Initialization ----
async function init() {
  let tree;
  if (WIKI_MODE === "static") {
    tree = STATIC_DATA.tree;
  } else {
    try {
      const res = await fetch("/api/tree");
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      tree = await res.json();
    } catch (err) {
      document.getElementById("welcome").innerHTML =
        `<h2>Error loading wiki</h2><p>Could not fetch file tree: ${escHtml(err.message)}</p>`;
      return;
    }
  }
  fileTree = tree;
  allFiles = flattenTree(tree);
  renderSidebar(tree);
  buildSearchIndex(allFiles);

  // Auto-load first file if only one exists
  if (allFiles.length === 1) loadFile(allFiles[0].path);
}

init();
</script>
</body>
</html>
"""


# ---------------------------------------------------------------------------
# Static HTML generator
# ---------------------------------------------------------------------------

def generate_static(source_dir: Path, output: Path, title: str, theme: str,
                    exclude_patterns: list[str]) -> None:
    """Generate a single self-contained HTML file with all content embedded."""
    print(f"Scanning {source_dir} …")
    tree = build_tree(source_dir, exclude_patterns)
    all_files = _flatten_tree(tree)

    if not all_files:
        print("Warning: no .md files found in source directory.", file=sys.stderr)

    files_data: dict[str, str] = {}
    for f in all_files:
        file_path = source_dir / f["path"]
        try:
            files_data[f["path"]] = file_path.read_text(encoding="utf-8", errors="replace")
        except OSError as e:
            print(f"Warning: could not read {file_path}: {e}", file=sys.stderr)
            files_data[f["path"]] = f"*Could not read file: {e}*"

    static_data = {"tree": tree, "files": files_data}
    static_json = json.dumps(static_data, ensure_ascii=False)

    html_out = _render_html(title, theme, "static", static_json)

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(html_out, encoding="utf-8")
    print(f"Generated {output}  ({len(all_files)} files embedded)")


def _flatten_tree(node: dict, acc: list | None = None) -> list:
    if acc is None:
        acc = []
    if node.get("type") == "file":
        acc.append(node)
    for child in node.get("children", []):
        _flatten_tree(child, acc)
    return acc


def _render_html(title: str, theme: str, mode: str, static_data: str) -> str:
    out = _HTML_TEMPLATE
    out = out.replace("{{TITLE}}", html.escape(title))
    out = out.replace("{{THEME_CLASS}}", "dark" if theme == "dark" else "")
    out = out.replace("{{MODE}}", mode)
    out = out.replace("{{STATIC_DATA}}", static_data if mode == "static" else "null")
    return out


# ---------------------------------------------------------------------------
# HTTP server
# ---------------------------------------------------------------------------

def make_handler(source_dir: Path, tree: dict, title: str, theme: str):
    """Create a request handler class with the given configuration baked in."""
    html_shell = _render_html(title, theme, "server", "null")
    html_bytes = html_shell.encode("utf-8")
    tree_json = json.dumps(tree, ensure_ascii=False).encode("utf-8")

    class WikiHandler(BaseHTTPRequestHandler):
        def log_message(self, fmt, *args):  # suppress default noisy logging
            pass

        def send_json(self, data: bytes, status: int = 200):
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def send_text(self, data: bytes, content_type: str = "text/plain; charset=utf-8", status: int = 200):
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            path = self.path.split("?")[0]  # strip query string

            if path in ("/", "/index.html"):
                self.send_text(html_bytes, "text/html; charset=utf-8")
                return

            if path == "/api/tree":
                self.send_json(tree_json)
                return

            if path.startswith("/api/files/"):
                self._serve_file(path[11:])  # strip "/api/files/"
                return

            # 404 for anything else
            self.send_error(404, "Not found")

        def _serve_file(self, encoded_rel: str):
            rel_path = unquote(encoded_rel)
            # Normalize separators
            rel_path = rel_path.replace("\\", "/")
            # Security: prevent directory traversal
            try:
                target = (source_dir / rel_path).resolve()
                target.relative_to(source_dir.resolve())
            except (ValueError, OSError):
                self.send_error(403, "Forbidden")
                return
            if not target.exists() or not target.is_file():
                self.send_error(404, "File not found")
                return
            if target.suffix.lower() != ".md":
                self.send_error(403, "Only .md files are served")
                return
            try:
                content = target.read_bytes()
                self.send_text(content, "text/plain; charset=utf-8")
            except OSError as e:
                self.send_error(500, str(e))

    return WikiHandler


def run_server(source_dir: Path, title: str, theme: str, exclude_patterns: list[str], port: int):
    """Scan source dir and start the HTTP server."""
    print(f"Scanning {source_dir} …")
    tree = build_tree(source_dir, exclude_patterns)
    handler_cls = make_handler(source_dir, tree, title, theme)
    server = HTTPServer(("127.0.0.1", port), handler_cls)
    print(f"Serving wiki at http://localhost:{port} — press Ctrl+C to stop")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
    finally:
        server.server_close()


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Convert a markdown knowledge base into a browsable HTML wiki.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--source", required=True, metavar="DIR",
                        help="Path to the markdown directory (required)")
    parser.add_argument("--output", default="wiki.html", metavar="FILE",
                        help="Output HTML filename (default: wiki.html)")
    parser.add_argument("--title", default=None, metavar="TEXT",
                        help="Wiki title (default: source folder name)")
    parser.add_argument("--theme", choices=["light", "dark"], default="light",
                        help="Initial colour theme (default: light)")
    parser.add_argument("--exclude", default="", metavar="PATTERNS",
                        help="Comma-separated glob patterns to exclude (e.g. 'Templates,Archive')")
    parser.add_argument("--port", type=int, default=8000, metavar="PORT",
                        help="Server port (default: 8000)")
    parser.add_argument("--no-server", action="store_true",
                        help="Generate a static HTML file only; do not start server")

    args = parser.parse_args()

    source_dir = Path(args.source).expanduser().resolve()
    if not source_dir.exists():
        print(f"Error: source directory not found: {source_dir}", file=sys.stderr)
        sys.exit(1)
    if not source_dir.is_dir():
        print(f"Error: source path is not a directory: {source_dir}", file=sys.stderr)
        sys.exit(1)

    title = args.title or source_dir.name.replace("-", " ").replace("_", " ").title()
    exclude_patterns = [p.strip() for p in args.exclude.split(",") if p.strip()]

    if args.no_server:
        output = Path(args.output)
        generate_static(source_dir, output, title, args.theme, exclude_patterns)
    else:
        run_server(source_dir, title, args.theme, exclude_patterns, args.port)


if __name__ == "__main__":
    main()
