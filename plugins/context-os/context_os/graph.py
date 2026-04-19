#!/usr/bin/env python3
"""
Local knowledge graph over markdown files: frontmatter + [[wiki-links]].
Stdlib only; optional PyYAML if installed.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

WIKI_LINK_RE = re.compile(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]")


def _load_yaml_block(block: str) -> dict[str, Any]:
    try:
        import yaml  # type: ignore

        return yaml.safe_load(block) or {}
    except Exception:
        return _parse_simple_frontmatter(block)


def _parse_simple_frontmatter(block: str) -> dict[str, Any]:
    """Minimal key: value and list parsing when PyYAML is absent."""
    meta: dict[str, Any] = {}
    lines = block.splitlines()
    i = 0
    current_key: str | None = None
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        m = re.match(r"^([a-zA-Z0-9_]+):\s*(.*)$", line)
        if m and not line.startswith(" "):
            key, rest = m.group(1), m.group(2).strip()
            if rest in ("|", "") and i + 1 < len(lines) and lines[i + 1].lstrip().startswith("-"):
                current_key = key
                meta[key] = []
                i += 1
                while i < len(lines) and lines[i].strip().startswith("-"):
                    item = lines[i].strip()[1:].strip().strip('"').strip("'")
                    meta[key].append(item)
                    i += 1
                current_key = None
                continue
            if rest.startswith("[") and rest.endswith("]"):
                inner = rest[1:-1]
                meta[key] = [x.strip().strip("'\"") for x in inner.split(",") if x.strip()]
            elif rest:
                meta[key] = rest.strip().strip('"').strip("'")
            else:
                meta[key] = ""
            current_key = key
        elif line.strip().startswith("-") and current_key:
            item = line.strip()[1:].strip().strip('"').strip("'")
            if current_key not in meta or not isinstance(meta[current_key], list):
                meta[current_key] = []
            meta[current_key].append(item)
        i += 1
    return meta


def parse_markdown_node(path: Path, text: str) -> tuple[dict[str, Any], str]:
    """Return (frontmatter dict, body)."""
    m = re.match(r"^---\s*\r?\n(.*?)\r?\n---\s*\r?\n?", text, re.DOTALL)
    if not m:
        return {}, text
    fm = _load_yaml_block(m.group(1))
    body = text[m.end() :]
    return fm, body


def extract_wiki_links(text: str) -> list[str]:
    return [x.strip() for x in WIKI_LINK_RE.findall(text)]


@dataclass
class GraphNode:
    path: str  # relative posix
    name: str
    frontmatter: dict[str, Any]
    outbound: list[str] = field(default_factory=list)
    inbound: list[str] = field(default_factory=list)
    link_count_out: int = 0
    link_count_in: int = 0


class KnowledgeGraph:
    def __init__(self, root: Path):
        self.root = root.resolve()
        self.nodes: dict[str, GraphNode] = {}
        self._name_to_paths: dict[str, list[str]] = {}

    def load(self) -> None:
        if not self.root.is_dir():
            return
        for md in sorted(self.root.rglob("*.md")):
            rel = md.relative_to(self.root).as_posix()
            try:
                text = md.read_text(encoding="utf-8")
            except OSError:
                continue
            fm, body = parse_markdown_node(md, text)
            stem = md.stem
            name = str(fm.get("name") or stem)
            outbound = extract_wiki_links(body)
            # also frontmatter related_concepts
            rc = fm.get("related_concepts")
            if isinstance(rc, list):
                for x in rc:
                    if isinstance(x, str):
                        for ln in extract_wiki_links(x):
                            if ln not in outbound:
                                outbound.append(ln)
            node = GraphNode(
                path=rel,
                name=name,
                frontmatter=fm,
                outbound=outbound,
            )
            self.nodes[rel] = node
            self._name_to_paths.setdefault(name, []).append(rel)
            self._name_to_paths.setdefault(stem, []).append(rel)

        # inbound edges: target = wiki link text -> resolve to path
        for rel, node in self.nodes.items():
            for target in node.outbound:
                tgt_paths = self._resolve_link(target)
                for tp in tgt_paths:
                    if tp in self.nodes:
                        self.nodes[tp].inbound.append(rel)

        for rel, node in self.nodes.items():
            node.inbound = sorted(set(node.inbound))
            node.outbound = list(dict.fromkeys(node.outbound))  # dedupe preserve order
            node.link_count_out = len(node.outbound)
            node.link_count_in = len(node.inbound)

    def _resolve_link(self, label: str) -> list[str]:
        """Map wiki label to relative path(s)."""
        label = label.strip()
        candidates: list[str] = []
        for rel in self.nodes:
            p = Path(rel)
            if p.stem == label or rel.endswith(label + ".md"):
                candidates.append(rel)
        # name field match
        for rel, n in self.nodes.items():
            if n.name == label:
                candidates.append(rel)
        return list(dict.fromkeys(candidates))

    def health(self, stale_days: int = 60) -> dict[str, Any]:
        from datetime import date, datetime

        today = date.today()
        orphans = [
            rel
            for rel, n in self.nodes.items()
            if n.link_count_out == 0 and n.link_count_in == 0
        ]
        hubs = sorted(
            self.nodes.values(),
            key=lambda x: x.link_count_out + x.link_count_in,
            reverse=True,
        )[:15]
        status_counts: dict[str, int] = {}
        stale: list[str] = []
        for rel, n in self.nodes.items():
            st = str(n.frontmatter.get("status") or "unknown")
            status_counts[st] = status_counts.get(st, 0) + 1
            lu = n.frontmatter.get("last_updated")
            if isinstance(lu, str):
                try:
                    d = datetime.strptime(lu[:10], "%Y-%m-%d").date()
                    if (today - d).days > stale_days:
                        stale.append(rel)
                except ValueError:
                    pass

        return {
            "root": str(self.root),
            "total_nodes": len(self.nodes),
            "orphans": sorted(orphans),
            "orphan_count": len(orphans),
            "hubs": [
                {
                    "path": h.path,
                    "name": h.name,
                    "links_out": h.link_count_out,
                    "links_in": h.link_count_in,
                }
                for h in hubs[:10]
            ],
            "status_counts": status_counts,
            "stale": sorted(stale),
            "stale_count": len(stale),
        }

    def query(self, term: str) -> list[dict[str, Any]]:
        term_l = term.lower()
        out: list[dict[str, Any]] = []
        for rel, n in self.nodes.items():
            blob = json.dumps(n.frontmatter, default=str).lower() + rel.lower()
            try:
                body_text = (self.root / rel).read_text(encoding="utf-8").lower()
            except OSError:
                body_text = ""
            if term_l in blob or term_l in body_text:
                out.append(
                    {
                        "path": rel,
                        "name": n.name,
                        "status": n.frontmatter.get("status"),
                        "snippet": rel,
                    }
                )
        return out

    def show(self, name_or_path: str) -> dict[str, Any] | None:
        key = name_or_path.strip()
        if key.endswith(".md"):
            rel = key
        else:
            matches = [r for r in self.nodes if Path(r).stem == key or self.nodes[r].name == key]
            rel = matches[0] if len(matches) == 1 else None
            if not rel:
                # try path substring
                subs = [r for r in self.nodes if key.lower() in r.lower()]
                rel = subs[0] if len(subs) == 1 else None
        if not rel or rel not in self.nodes:
            return None
        n = self.nodes[rel]
        neighbors = {
            "outbound": n.outbound,
            "inbound": [self.nodes[i].name for i in n.inbound if i in self.nodes],
        }
        return {
            "path": rel,
            "frontmatter": n.frontmatter,
            "neighbors": neighbors,
        }
