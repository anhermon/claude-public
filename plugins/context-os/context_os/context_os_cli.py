#!/usr/bin/env python3
"""
Bundled context-os CLI (context-os plugin). Stdlib-first.
"""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.request
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path


def _plugin_root() -> Path:
    """Repo root when running from a checkout; package dir when wheel-only install."""
    env = os.environ.get("CONTEXT_OS_PLUGIN_ROOT")
    if env:
        return Path(env).resolve()
    here = Path(__file__).resolve().parent
    parent = here.parent
    if (parent / "hooks").is_dir():
        return parent
    return here


PLUGIN_ROOT = _plugin_root()
SCRIPTS_DIR = Path(__file__).resolve().parent


def _graph_module():
    from context_os.graph import KnowledgeGraph  # noqa: E402

    return KnowledgeGraph


def parse_since(s: str) -> datetime | None:
    s = s.strip().lower()
    if not s:
        return None
    now = datetime.now(timezone.utc)
    if s.endswith("d"):
        return now - timedelta(days=int(s[:-1] or "7"))
    if s.endswith("h"):
        return now - timedelta(hours=int(s[:-1] or "24"))
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        return now - timedelta(days=7)


def iter_session_files() -> list[Path]:
    root = Path.home() / ".claude" / "projects"
    if not root.is_dir():
        return []
    return sorted(root.rglob("*.jsonl"))


def cmd_graph_health(args: argparse.Namespace) -> int:
    KG = _graph_module()
    g = KG(Path(args.graph))
    g.load()
    h = g.health(stale_days=args.stale_days)
    if args.format == "json":
        print(json.dumps(h, indent=2))
    else:
        print(f"total={h['total_nodes']} orphans={h['orphan_count']} stale={h['stale_count']}")
        for hub in h.get("hubs", [])[:5]:
            print(f"  hub {hub['path']} links={hub['links_out']+hub['links_in']}")
    return 0


def cmd_graph_query(args: argparse.Namespace) -> int:
    KG = _graph_module()
    g = KG(Path(args.graph))
    g.load()
    r = g.query(args.term)
    print(json.dumps(r, indent=2))
    return 0


def cmd_graph_show(args: argparse.Namespace) -> int:
    KG = _graph_module()
    g = KG(Path(args.graph))
    g.load()
    r = g.show(args.name)
    if not r:
        print(json.dumps({"error": "not found", "name": args.name}))
        return 1
    print(json.dumps(r, indent=2))
    return 0


def cmd_sessions_list(args: argparse.Namespace) -> int:
    since = parse_since(args.since)
    files = iter_session_files()
    out: list[dict] = []
    sub = (args.path_contains or "").lower()
    for f in files:
        try:
            st = f.stat()
        except OSError:
            continue
        mtime = datetime.fromtimestamp(st.st_mtime, tz=timezone.utc)
        if since and mtime < since.replace(tzinfo=timezone.utc):
            continue
        rel = f.relative_to(Path.home()).as_posix()
        if sub:
            try:
                txt = f.read_text(encoding="utf-8", errors="replace")[:500_000]
            except OSError:
                continue
            if sub not in txt.lower():
                continue
        out.append(
            {
                "path": rel,
                "name": f.name,
                "mtime": mtime.isoformat(),
            }
        )
    print(json.dumps({"sessions": out, "count": len(out)}, indent=2))
    return 0


def cmd_sessions_replay(args: argparse.Namespace) -> int:
    from context_os.cc_lens_url import resolve_cc_lens_base_url

    sid = args.session_id
    base = resolve_cc_lens_base_url()
    url = f"{base}/api/sessions/{sid}/replay"
    try:
        with urllib.request.urlopen(url, timeout=30) as r:
            data = json.loads(r.read().decode("utf-8"))
        print(json.dumps(data, indent=2)[:200_000])
        return 0
    except Exception as e:
        print(json.dumps({"error": str(e), "hint": "Start dashboard: npx cc-lens"}, indent=2))
        return 1


_PATH_RE = re.compile(
    r"(?:file_path|path|pattern)[\"']?\s*:\s*[\"']([^\"']+)[\"']",
    re.I,
)


def cmd_heat(args: argparse.Namespace) -> int:
    since = parse_since(f"{args.days}d")
    files = iter_session_files()
    counts: Counter[str] = Counter()
    session_hits: Counter[str] = Counter()
    sub = (args.path_contains or "").lower()
    path_re = _PATH_RE

    for f in files:
        try:
            st = f.stat()
            mtime = datetime.fromtimestamp(st.st_mtime, tz=timezone.utc)
        except OSError:
            continue
        if since and mtime < since:
            continue
        try:
            txt = f.read_text(encoding="utf-8", errors="replace")[:800_000]
        except OSError:
            continue
        if sub and sub not in txt.lower():
            continue
        paths = path_re.findall(txt)
        for p in re.findall(r"[\w\-./]+\.(?:md|py|ts|tsx|json|yaml|yml)", txt):
            if "/" in p or p.endswith(".md"):
                paths.append(p)
        for p in paths:
            counts[p] += 1
        if paths:
            session_hits[f.relative_to(Path.home()).as_posix()] += 1

    rows = []
    for path, n in counts.most_common(int(args.limit)):
        rows.append(
            {
                "path": path,
                "accesses": n,
                "level": "HOT" if n >= 10 else "WARM" if n >= 4 else "COOL",
            }
        )
    if args.format == "table":
        print("PATH\tACCESSES\tLEVEL")
        for row in rows:
            print(f"{row['path']}\t{row['accesses']}\t{row['level']}")
    else:
        print(json.dumps({"heat": rows, "sessions_touched": len(session_hits)}, indent=2))
    return 0


def cmd_ingest_session(args: argparse.Namespace) -> int:
    exe = sys.executable
    script = SCRIPTS_DIR / "ingest_session.py"
    cmd = [exe, str(script), args.session_id, "--graph", args.graph]
    if args.summary_only:
        cmd.append("--summary-only")
    if args.file:
        cmd.extend(["--file", args.file])
    return subprocess.call(cmd)


def cmd_ingest_file(args: argparse.Namespace) -> int:
    exe = sys.executable
    script = SCRIPTS_DIR / "ingest_source.py"
    return subprocess.call([exe, str(script), str(args.path), "--graph", args.graph])


def cmd_ingest_source(args: argparse.Namespace) -> int:
    exe = sys.executable
    script = SCRIPTS_DIR / "ingest_source.py"
    return subprocess.call([exe, str(script), args.source, "--graph", args.graph])


def cmd_cc_lens(args: argparse.Namespace) -> int:
    exe = sys.executable
    analyze = SCRIPTS_DIR / "analyze.py"
    gen = SCRIPTS_DIR / "generate_dashboard.py"
    sub = args.subcommand or "analyze"
    if sub == "up":
        from context_os.cc_lens_url import find_running_cc_lens

        existing = find_running_cc_lens()
        if existing:
            print(
                f"cc-lens is already running at {existing}\n"
                "Open that URL — do not start a second server (Next.js may use another port "
                "and show a blank page)."
            )
            return 0
        npx = shutil.which("npx")
        if not npx:
            print("npx not found; install Node.js", file=sys.stderr)
            return 1
        try:
            subprocess.Popen(
                [npx, "--yes", "cc-lens@latest"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
        except OSError as e:
            print(json.dumps({"error": str(e)}), file=sys.stderr)
            return 1
        print(
            "Started cc-lens in background. It picks a free port (often 3001) and may open your browser.\n"
            "If the page is blank, another instance may already be running — see README (cc-lens port)."
        )
        return 0
    if sub == "analyze":
        spec = "/tmp/cc-lens-spec.json"
        out_html = "/tmp/cc-lens-report.html"
        rc = subprocess.call(
            [
                exe,
                str(analyze),
                "--top-n",
                str(args.top_n),
                "--sort-by",
                args.sort_by,
                "--sessions-per-project",
                str(args.sessions_per_project),
                "--output",
                spec,
            ]
        )
        if rc != 0:
            return rc
        return subprocess.call([exe, str(gen), "--spec", spec, "--output", out_html])
    if sub == "project" and args.project:
        spec = f"/tmp/cc-lens-project-{args.project}.json"
        out_html = spec.replace(".json", ".html")
        rc = subprocess.call(
            [
                exe,
                str(analyze),
                "--project",
                args.project,
                "--sessions-per-project",
                str(args.sessions_per_project),
                "--output",
                spec,
            ]
        )
        if rc != 0:
            return rc
        return subprocess.call([exe, str(gen), "--spec", spec, "--output", out_html])
    if sub == "forensics" and args.session:
        spec = f"/tmp/cc-lens-session-{args.session}.json"
        out_html = spec.replace(".json", ".html")
        rc = subprocess.call(
            [exe, str(analyze), "--session", args.session, "--output", spec]
        )
        if rc != 0:
            return rc
        return subprocess.call([exe, str(gen), "--spec", spec, "--output", out_html])
    print(json.dumps({"error": "unknown cc-lens subcommand or missing --project/--session"}))
    return 1


def cmd_ccusage(args: argparse.Namespace) -> int:
    exe = sys.executable
    script = SCRIPTS_DIR / "ccusage_wrapper.py"
    rest = list(args.rest) if args.rest else ["daily"]
    return subprocess.call([exe, str(script), *rest])


def cmd_audit(args: argparse.Namespace) -> int:
    KG = _graph_module()
    g = KG(Path(args.graph))
    g.load()
    health = g.health(stale_days=60)

    ccusage_txt = ""
    try:
        exe = sys.executable
        script = SCRIPTS_DIR / "ccusage_wrapper.py"
        r = subprocess.run(
            [exe, str(script), "daily"],
            capture_output=True,
            text=True,
            timeout=90,
        )
        ccusage_txt = (r.stdout or "")[:8000]
    except Exception as e:
        ccusage_txt = f"(ccusage unavailable: {e})"

    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    spec_path = f"/tmp/context-os-audit-spec-{ts}.json"
    html_path = f"/tmp/context-os-audit-{ts}.html"
    analyze_ok = False
    try:
        exe = sys.executable
        analyze = SCRIPTS_DIR / "analyze.py"
        gen = SCRIPTS_DIR / "generate_dashboard.py"
        r = subprocess.run(
            [exe, str(analyze), "--top-n", "3", "--output", spec_path],
            capture_output=True,
            timeout=120,
        )
        analyze_ok = r.returncode == 0
        if analyze_ok:
            subprocess.run(
                [exe, str(gen), "--spec", spec_path, "--output", html_path],
                timeout=120,
            )
    except Exception:
        analyze_ok = False

    h_esc = html.escape(json.dumps(health, indent=2))
    cu_esc = html.escape(ccusage_txt)
    lens_block = (
        f'<p>Open cc-lens report: <code>file://{html_path}</code></p>'
        if analyze_ok
        else "<p>cc-lens report skipped (is <code>npx cc-lens</code> running on :3001?)</p>"
    )
    page = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>context-os audit</title></head>
<body>
<h1>context-os audit</h1>
<h2>Graph health</h2>
<pre>{h_esc}</pre>
<h2>ccusage (daily)</h2>
<pre>{cu_esc}</pre>
<h2>cc-lens</h2>
{lens_block}
</body></html>
"""
    bundle_ts = Path(f"/tmp/context-os-audit-bundle-{ts}.html")
    bundle_ts.write_text(page, encoding="utf-8")
    for legacy_name in (
        Path("/tmp/context-os-audit-bundle-latest.html"),
        Path("/tmp/context-os-audit-bundle.html"),
    ):
        try:
            if legacy_name.exists() or legacy_name.is_symlink():
                legacy_name.unlink()
            legacy_name.symlink_to(bundle_ts.name)
        except OSError:
            legacy_name.write_text(page, encoding="utf-8")

    print(
        json.dumps(
            {
                "ok": True,
                "graph": health,
                "audit_html": str(bundle_ts),
                "audit_html_latest": "/tmp/context-os-audit-bundle-latest.html",
                "cc_lens_html": html_path if analyze_ok else None,
            },
            indent=2,
        )
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="context-os")
    sub = p.add_subparsers(dest="cmd", required=True)

    gh = sub.add_parser("graph", help="Knowledge graph")
    gs = gh.add_subparsers(dest="gcmd", required=True)
    ghp = gs.add_parser("health", help="Orphans, hubs, status counts")
    ghp.add_argument("--graph", default="knowledge_base")
    ghp.add_argument("--stale-days", type=int, default=60)
    ghp.add_argument("--format", choices=["json", "text"], default="json")

    ghq = gs.add_parser("query", help="Search term in graph")
    ghq.add_argument("term")
    ghq.add_argument("--graph", default="knowledge_base")

    ghs = gs.add_parser("show", help="Show one node")
    ghs.add_argument("name")
    ghs.add_argument("--graph", default="knowledge_base")

    sh = sub.add_parser("sessions")
    ss = sh.add_subparsers(dest="scmd", required=True)
    sl = ss.add_parser("list")
    sl.add_argument("--since", default="30d")
    sl.add_argument("--path-contains", default="", dest="path_contains")

    sr = ss.add_parser("replay")
    sr.add_argument("session_id")

    ht = sub.add_parser("heat")
    ht.add_argument("--days", type=int, default=14)
    ht.add_argument("--path-contains", default="", dest="path_contains")
    ht.add_argument("--limit", type=int, default=50)
    ht.add_argument("--format", choices=["json", "table"], default="json")

    ing = sub.add_parser("ingest")
    ins = ing.add_subparsers(dest="icmd", required=True)
    i_sess = ins.add_parser("session")
    i_sess.add_argument("session_id")
    i_sess.add_argument("--graph", default="knowledge_base")
    i_sess.add_argument("--summary-only", action="store_true")
    i_sess.add_argument("--file")

    i_file = ins.add_parser("file")
    i_file.add_argument("path")
    i_file.add_argument("--graph", default="knowledge_base")

    i_src = ins.add_parser("source")
    i_src.add_argument("source")
    i_src.add_argument("--graph", default="knowledge_base")

    aud = sub.add_parser("audit")
    aud.add_argument("--graph", default="knowledge_base")

    cl = sub.add_parser("cc-lens")
    cl.add_argument("subcommand", nargs="?", default="analyze")
    cl.add_argument("--top-n", type=int, default=5)
    cl.add_argument("--sort-by", default="cost")
    cl.add_argument("--sessions-per-project", type=int, default=3)
    cl.add_argument("--project", default=None)
    cl.add_argument("--session", default=None)

    cu = sub.add_parser("ccusage")
    cu.add_argument("rest", nargs=argparse.REMAINDER)

    return p


def dispatch(args: argparse.Namespace) -> int:
    if args.cmd == "graph":
        if args.gcmd == "health":
            return cmd_graph_health(args)
        if args.gcmd == "query":
            return cmd_graph_query(args)
        if args.gcmd == "show":
            return cmd_graph_show(args)
    if args.cmd == "sessions":
        if args.scmd == "list":
            return cmd_sessions_list(args)
        if args.scmd == "replay":
            return cmd_sessions_replay(args)
    if args.cmd == "heat":
        return cmd_heat(args)
    if args.cmd == "ingest":
        if args.icmd == "session":
            return cmd_ingest_session(args)
        if args.icmd == "file":
            return cmd_ingest_file(args)
        if args.icmd == "source":
            return cmd_ingest_source(args)
    if args.cmd == "audit":
        return cmd_audit(args)
    if args.cmd == "cc-lens":
        return cmd_cc_lens(args)
    if args.cmd == "ccusage":
        return cmd_ccusage(args)
    return 1


def main(argv: list[str] | None = None) -> int:
    argv = list(argv if argv is not None else sys.argv[1:])
    if not argv:
        print(
            json.dumps(
                {
                    "help": "context-os graph health | graph query T | sessions list | heat | audit | ingest session ID | cc-lens analyze | ccusage daily",
                    "plugin_root": str(PLUGIN_ROOT),
                },
                indent=2,
            )
        )
        return 0
    p = build_parser()
    args = p.parse_args(argv)
    return dispatch(args)


if __name__ == "__main__":
    raise SystemExit(main())
