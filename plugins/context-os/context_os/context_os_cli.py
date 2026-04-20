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


_ANSI_RE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")


def _cc_lens_port_range() -> range:
    """Ports cc-lens may bind to (Next.js picks the first free one starting at 3000).
    Excludes ports we know are used by other services.
    """
    skip = {3001}  # Grafana
    env = os.environ.get("CONTEXT_OS_CC_LENS_SKIP_PORTS", "")
    for p in env.split(","):
        p = p.strip()
        if p.isdigit():
            skip.add(int(p))
    return [p for p in range(3000, 3020) if p not in skip]


def _probe_cc_lens(base: str, timeout: float = 12.0) -> bool:
    try:
        req = urllib.request.Request(base + "/api/stats", headers={"User-Agent": "context-os-audit"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            if r.status != 200:
                return False
            ct = (r.headers.get("Content-Type") or "").lower()
            return "json" in ct
    except Exception:
        return False


def _discover_cc_lens() -> str | None:
    """Scan the range for a live cc-lens. Env override wins."""
    env = os.environ.get("CC_LENS_BASE_URL") or os.environ.get("CONTEXT_OS_CC_LENS_URL")
    if env:
        base = env.rstrip("/")
        return base if _probe_cc_lens(base) else None
    for port in _cc_lens_port_range():
        base = f"http://localhost:{port}"
        if _probe_cc_lens(base):
            return base
    return None


def _start_cc_lens() -> tuple[bool, str]:
    """Launch `npx cc-lens` detached. cc-lens auto-picks a free port (Next.js)."""
    npx = shutil.which("npx") or shutil.which("npx.cmd")
    if not npx:
        return False, "npx not found on PATH"
    log_path = Path(os.environ.get("TEMP", "/tmp")) / "cc-lens.log"
    try:
        log = open(log_path, "ab")
    except Exception:
        log = subprocess.DEVNULL
    env = os.environ.copy()
    env["BROWSER"] = "none"
    kwargs: dict = {"stdout": log, "stderr": log, "stdin": subprocess.DEVNULL, "env": env}
    if os.name == "nt":
        DETACHED_PROCESS = 0x00000008
        CREATE_NEW_PROCESS_GROUP = 0x00000200
        kwargs["creationflags"] = DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP
        kwargs["close_fds"] = True
    else:
        kwargs["start_new_session"] = True
    try:
        subprocess.Popen([npx, "--yes", "cc-lens"], **kwargs)
    except Exception as e:
        return False, f"failed to spawn: {e}"
    return True, f"spawned npx cc-lens (log: {log_path})"


def _wait_cc_lens(max_seconds: int = 90) -> str | None:
    """Wait for a cc-lens instance to appear in the port range. Returns base URL or None."""
    import time
    deadline = time.time() + max_seconds
    while time.time() < deadline:
        base = _discover_cc_lens()
        if base:
            return base
        time.sleep(2.0)
    return None


def _render_health_cards(health: dict) -> str:
    cards = [
        ("Total nodes", health.get("total_nodes", 0)),
        ("Orphans", health.get("orphan_count", 0)),
        ("Stale (60d)", health.get("stale_count", 0)),
        ("Hubs", len(health.get("hubs", []) or [])),
    ]
    out = ['<div class="cards">']
    for label, value in cards:
        cls = "zero" if value == 0 else ("warn" if label in ("Orphans", "Stale (60d)") and value else "")
        out.append(f'<div class="card {cls}"><div class="v">{value}</div><div class="l">{html.escape(label)}</div></div>')
    out.append("</div>")
    return "".join(out)


def _render_list_table(title: str, items: list, cols: list) -> str:
    if not items:
        return f'<section><h2>{html.escape(title)}</h2><p class="muted">None.</p></section>'
    head = "".join(f"<th>{html.escape(c)}</th>" for c in cols)
    rows = []
    for it in items[:50]:
        if isinstance(it, dict):
            tds = "".join(f"<td>{html.escape(str(it.get(c, '')))}</td>" for c in cols)
        else:
            tds = f"<td>{html.escape(str(it))}</td>" * len(cols)
        rows.append(f"<tr>{tds}</tr>")
    more = f'<p class="muted">Showing first 50 of {len(items)}.</p>' if len(items) > 50 else ""
    return (
        f'<section><h2>{html.escape(title)}</h2>'
        f'<table><thead><tr>{head}</tr></thead><tbody>{"".join(rows)}</tbody></table>'
        f'{more}</section>'
    )


def cmd_filemap(args: argparse.Namespace) -> int:
    from context_os.file_map import run_cli as _filemap_run
    return _filemap_run(args)


def _run_filemap_for_audit(days: int = 30) -> dict | None:
    """Invoke file_map.scan_file_map against the discovered cc-lens. Returns result dict or None."""
    base = _discover_cc_lens()
    if not base:
        return None
    try:
        os.environ["CC_LENS_BASE_URL"] = base
        from context_os.file_map import scan_file_map
        return scan_file_map(base_url=base, days=days)
    except Exception as e:
        return {"error": str(e)}


def _render_filemap_section(fm: dict | None) -> str:
    if not fm:
        return (
            '<section><h2>File-map bloat</h2>'
            '<p class="muted">cc-lens not reachable — run <code>context-os filemap</code> once cc-lens is up.</p></section>'
        )
    if fm.get("error"):
        return (
            f'<section><h2>File-map bloat</h2>'
            f'<p class="muted">file_map error: {html.escape(str(fm["error"]))}</p></section>'
        )
    flagged = fm.get("flagged", [])[:20]
    cards = [
        ("Sessions scanned", fm.get("sessions_scanned", 0)),
        ("Files observed", fm.get("files_observed", 0)),
        ("Bloat candidates", fm.get("bloat_candidates", 0)),
    ]
    cards_html = '<div class="cards">' + "".join(
        f'<div class="card {"warn" if label=="Bloat candidates" and value else ("zero" if value==0 else "")}">'
        f'<div class="v">{value}</div><div class="l">{html.escape(label)}</div></div>'
        for label, value in cards
    ) + "</div>"
    if not flagged:
        table = '<p class="muted">No bloat candidates detected.</p>'
    else:
        rows = []
        for e in flagged:
            rows.append(
                "<tr>"
                f"<td>{html.escape(str(e.get('path','')))}</td>"
                f"<td>{e.get('read_count',0)}</td>"
                f"<td>{e.get('file_line_count',0)}</td>"
                f"<td>{e.get('file_size_bytes',0):,}</td>"
                f"<td>{html.escape(str(e.get('suggestion') or ''))}</td>"
                "</tr>"
            )
        table = (
            '<table><thead><tr><th>Path</th><th>Reads</th><th>Lines</th><th>Size (B)</th><th>Suggestion</th></tr></thead>'
            f'<tbody>{"".join(rows)}</tbody></table>'
        )
    return f'<section><h2>File-map bloat (last 30d)</h2>{cards_html}{table}</section>'


def cmd_audit(args: argparse.Namespace) -> int:
    KG = _graph_module()
    g = KG(Path(args.graph))
    g.load()
    health = g.health(stale_days=60)

    # ccusage
    ccusage_txt = ""
    ccusage_err = ""
    try:
        exe = sys.executable
        script = SCRIPTS_DIR / "ccusage_wrapper.py"
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        r = subprocess.run(
            [exe, str(script), "daily"],
            capture_output=True,
            timeout=120,
            env=env,
        )
        ccusage_txt = (r.stdout or b"").decode("utf-8", errors="replace")
        if r.returncode != 0:
            ccusage_err = (r.stderr or b"").decode("utf-8", errors="replace")[:2000]
    except Exception as e:
        ccusage_err = f"ccusage unavailable: {e}"
    ccusage_clean = _ANSI_RE.sub("", ccusage_txt)[:16000]

    # cc-lens: discover existing instance, else start one
    cc_status = "unknown"
    cc_started = False
    cc_message = ""
    cc_base: str | None = _discover_cc_lens()
    if cc_base:
        cc_status = f"running at {cc_base}"
    else:
        ok, msg = _start_cc_lens()
        cc_message = msg
        if ok:
            cc_started = True
            cc_base = _wait_cc_lens(max_seconds=90)
            if cc_base:
                cc_status = f"started at {cc_base}"
            else:
                cc_status = "starting (no /api/stats within 90s — check cc-lens.log)"
        else:
            cc_status = "unavailable"

    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    spec_path = f"/tmp/context-os-audit-spec-{ts}.json"
    lens_html_path = f"/tmp/context-os-audit-{ts}.html"
    analyze_ok = False
    analyze_err = ""
    if cc_base:
        try:
            exe = sys.executable
            analyze = SCRIPTS_DIR / "analyze.py"
            gen = SCRIPTS_DIR / "generate_dashboard.py"
            an_env = os.environ.copy()
            an_env["CC_LENS_BASE_URL"] = cc_base
            existing_pp = an_env.get("PYTHONPATH", "")
            an_env["PYTHONPATH"] = (
                str(PLUGIN_ROOT) + (os.pathsep + existing_pp if existing_pp else "")
            )
            r = subprocess.run(
                [exe, str(analyze), "--top-n", "3", "--output", spec_path],
                capture_output=True,
                timeout=180,
                env=an_env,
            )
            analyze_ok = r.returncode == 0
            if not analyze_ok:
                analyze_err = (r.stderr or b"").decode("utf-8", errors="replace")[:2000]
            else:
                subprocess.run(
                    [exe, str(gen), "--spec", spec_path, "--output", lens_html_path],
                    timeout=180,
                )
        except Exception as e:
            analyze_err = str(e)

    # Build dashboard
    cards_html = _render_health_cards(health)
    orphans_html = _render_list_table("Orphans", health.get("orphans", []) or [], ["path"] if health.get("orphans") and isinstance(health["orphans"][0], dict) else ["node"])
    stale_html = _render_list_table("Stale nodes (>60d)", health.get("stale", []) or [], ["path"] if health.get("stale") and isinstance(health["stale"][0], dict) else ["node"])
    hubs_html = _render_list_table("Hubs", health.get("hubs", []) or [], ["path"] if health.get("hubs") and isinstance(health["hubs"][0], dict) else ["node"])
    status_counts = health.get("status_counts", {}) or {}
    status_rows = "".join(f"<tr><td>{html.escape(k)}</td><td>{v}</td></tr>" for k, v in sorted(status_counts.items()))
    status_html = (
        f'<section><h2>Status counts</h2><table><thead><tr><th>Status</th><th>Count</th></tr></thead>'
        f'<tbody>{status_rows or "<tr><td colspan=2 class=muted>No nodes ingested yet.</td></tr>"}</tbody></table></section>'
    )

    if analyze_ok:
        lens_block = (
            f'<p><span class="pill ok">cc-lens {cc_status}</span> '
            f'Forensics report: <a href="file:///{lens_html_path.lstrip("/")}">{html.escape(lens_html_path)}</a></p>'
        )
    else:
        lens_block = (
            f'<p><span class="pill warn">cc-lens {html.escape(cc_status)}</span> '
            f'{html.escape(cc_message)}</p>'
        )
        if analyze_err:
            lens_block += f'<details><summary>analyze error</summary><pre>{html.escape(analyze_err)}</pre></details>'

    ccusage_block = f'<pre class="ccusage">{html.escape(ccusage_clean) or "<em>no output</em>"}</pre>'
    if ccusage_err:
        ccusage_block += f'<details><summary>ccusage stderr</summary><pre>{html.escape(ccusage_err)}</pre></details>'

    # file-map bloat section
    try:
        filemap_result = _run_filemap_for_audit(days=30)
    except Exception as _fm_e:
        filemap_result = {"error": str(_fm_e)}
    filemap_html = _render_filemap_section(filemap_result)

    graph_root = html.escape(str(health.get("root", args.graph)))
    gen_ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    css = """
    :root { --bg:#0b0d10; --panel:#14181d; --fg:#e7ecf3; --muted:#8a96a4; --accent:#6aa6ff; --warn:#f0a868; --ok:#6dd58c; --bad:#ff6b6b; --border:#242a31; }
    * { box-sizing:border-box; }
    body { margin:0; font:14px/1.5 -apple-system,Segoe UI,Roboto,sans-serif; background:var(--bg); color:var(--fg); }
    header { padding:20px 28px; border-bottom:1px solid var(--border); display:flex; justify-content:space-between; align-items:baseline; flex-wrap:wrap; gap:8px; }
    header h1 { margin:0; font-size:18px; letter-spacing:0.3px; }
    header .meta { color:var(--muted); font-size:12px; font-family:ui-monospace,Consolas,monospace; }
    main { padding:24px 28px; max-width:1200px; margin:0 auto; }
    section { background:var(--panel); border:1px solid var(--border); border-radius:10px; padding:18px 20px; margin-bottom:18px; }
    section h2 { margin:0 0 12px; font-size:14px; font-weight:600; color:var(--muted); text-transform:uppercase; letter-spacing:0.6px; }
    .cards { display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr)); gap:12px; }
    .card { background:var(--panel); border:1px solid var(--border); border-radius:10px; padding:16px; }
    .card .v { font-size:28px; font-weight:600; }
    .card .l { color:var(--muted); font-size:12px; margin-top:4px; text-transform:uppercase; letter-spacing:0.5px; }
    .card.warn { border-color:var(--warn); } .card.warn .v { color:var(--warn); }
    .card.zero .v { color:var(--muted); }
    table { width:100%; border-collapse:collapse; font-family:ui-monospace,Consolas,monospace; font-size:12.5px; }
    th,td { text-align:left; padding:6px 10px; border-bottom:1px solid var(--border); }
    th { color:var(--muted); font-weight:500; }
    .muted { color:var(--muted); }
    pre.ccusage { background:#07090b; padding:12px; border-radius:8px; overflow:auto; font-size:12px; max-height:520px; }
    .pill { display:inline-block; padding:2px 8px; border-radius:999px; font-size:11px; margin-right:6px; font-weight:600; }
    .pill.ok { background:rgba(109,213,140,0.15); color:var(--ok); }
    .pill.warn { background:rgba(240,168,104,0.15); color:var(--warn); }
    a { color:var(--accent); }
    details { margin-top:8px; } details pre { background:#07090b; padding:10px; border-radius:6px; overflow:auto; font-size:11.5px; }
    """

    page = f"""<!DOCTYPE html><html lang="en"><head>
<meta charset="utf-8"><title>context-os audit — {gen_ts}</title>
<style>{css}</style></head><body>
<header>
  <h1>context-os audit</h1>
  <div class="meta">{gen_ts} · graph: {graph_root}</div>
</header>
<main>
  <section><h2>Graph health</h2>{cards_html}</section>
  {status_html}
  {orphans_html}
  {stale_html}
  {hubs_html}
  {filemap_html}
  <section><h2>cc-lens</h2>{lens_block}</section>
  <section><h2>ccusage (daily)</h2>{ccusage_block}</section>
</main>
</body></html>"""

    bundle_ts = Path(f"/tmp/context-os-audit-bundle-{ts}.html")
    bundle_ts.parent.mkdir(parents=True, exist_ok=True)
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
                "cc_lens_status": cc_status,
                "cc_lens_started": cc_started,
                "cc_lens_html": lens_html_path if analyze_ok else None,
                "filemap": {
                    "bloat_candidates": (filemap_result or {}).get("bloat_candidates"),
                    "files_observed":   (filemap_result or {}).get("files_observed"),
                    "sessions_scanned": (filemap_result or {}).get("sessions_scanned"),
                } if filemap_result and not filemap_result.get("error") else None,
            },
            indent=2,
        )
    )
    return 0


_DASHBOARD_HTML = r"""<!DOCTYPE html><html lang="en"><head>
<meta charset="utf-8"><title>context-os live dashboard</title>
<style>
:root { --bg:#0b0d10; --panel:#14181d; --fg:#e7ecf3; --muted:#8a96a4; --accent:#6aa6ff; --warn:#f0a868; --ok:#6dd58c; --bad:#ff6b6b; --border:#242a31; }
* { box-sizing:border-box; }
body { margin:0; font:14px/1.5 -apple-system,Segoe UI,Roboto,sans-serif; background:var(--bg); color:var(--fg); }
header { padding:20px 28px; border-bottom:1px solid var(--border); display:flex; justify-content:space-between; align-items:baseline; flex-wrap:wrap; gap:8px; }
header h1 { margin:0; font-size:18px; letter-spacing:0.3px; }
header .meta { color:var(--muted); font-size:12px; font-family:ui-monospace,Consolas,monospace; }
main { padding:24px 28px; max-width:1200px; margin:0 auto; }
section { background:var(--panel); border:1px solid var(--border); border-radius:10px; padding:18px 20px; margin-bottom:18px; }
section h2 { margin:0 0 12px; font-size:14px; font-weight:600; color:var(--muted); text-transform:uppercase; letter-spacing:0.6px; }
.cards { display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr)); gap:12px; }
.card { background:#0f1317; border:1px solid var(--border); border-radius:10px; padding:16px; }
.card .v { font-size:28px; font-weight:600; }
.card .l { color:var(--muted); font-size:12px; margin-top:4px; text-transform:uppercase; letter-spacing:0.5px; }
.card.warn { border-color:var(--warn); } .card.warn .v { color:var(--warn); }
.card.ok { border-color:var(--ok); } .card.ok .v { color:var(--ok); }
.card.zero .v { color:var(--muted); }
table { width:100%; border-collapse:collapse; font-family:ui-monospace,Consolas,monospace; font-size:12.5px; }
th,td { text-align:left; padding:6px 10px; border-bottom:1px solid var(--border); }
th { color:var(--muted); font-weight:500; }
.muted { color:var(--muted); }
.pill { display:inline-block; padding:2px 8px; border-radius:999px; font-size:11px; margin-right:6px; font-weight:600; }
.pill.ok { background:rgba(109,213,140,0.15); color:var(--ok); }
.pill.warn { background:rgba(240,168,104,0.15); color:var(--warn); }
.pill.bad { background:rgba(255,107,107,0.15); color:var(--bad); }
a { color:var(--accent); }
.dot { display:inline-block; width:8px; height:8px; border-radius:50%; background:var(--muted); margin-right:6px; }
.dot.live { background:var(--ok); box-shadow:0 0 8px var(--ok); animation:pulse 1.8s infinite; }
@keyframes pulse { 0%{opacity:1} 50%{opacity:.4} 100%{opacity:1} }
</style></head><body>
<header>
  <h1>context-os live dashboard</h1>
  <div class="meta"><span id="dot" class="dot"></span><span id="status">connecting…</span> · <span id="ts"></span></div>
</header>
<main>
  <section><h2>Graph health</h2><div id="graph-cards" class="cards"><div class="muted">loading…</div></div></section>
  <section><h2>cc-lens stats</h2><div id="lens-cards" class="cards"><div class="muted">loading…</div></div><p class="muted" id="lens-meta"></p></section>
  <section><h2>Recent sessions</h2><div id="sessions"><p class="muted">loading…</p></div></section>
</main>
<script>
const POLL_MS = 5000;
function el(tag, cls, txt){ const e=document.createElement(tag); if(cls)e.className=cls; if(txt!=null)e.textContent=txt; return e; }
function card(label, value, cls){
  const d = el("div","card "+(cls||""));
  d.appendChild(el("div","v", value==null?"—":String(value)));
  d.appendChild(el("div","l", label));
  return d;
}
async function j(url){ const r = await fetch(url); if(!r.ok) throw new Error(url+" "+r.status); return r.json(); }
function setStatus(ok, msg){
  document.getElementById("dot").className = "dot " + (ok?"live":"");
  document.getElementById("status").textContent = msg;
  document.getElementById("ts").textContent = new Date().toLocaleTimeString();
}
function renderGraph(h){
  const c = document.getElementById("graph-cards"); c.innerHTML="";
  const orph = h.orphan_count||0, stale = h.stale_count||0;
  c.appendChild(card("Total nodes", h.total_nodes||0, (h.total_nodes?"":"zero")));
  c.appendChild(card("Orphans", orph, orph>0?"warn":"zero"));
  c.appendChild(card("Stale (60d)", stale, stale>0?"warn":"zero"));
  c.appendChild(card("Hubs", (h.hubs||[]).length, "ok"));
}
function renderLens(s, meta){
  const c = document.getElementById("lens-cards"); c.innerHTML="";
  if(!s){ c.appendChild(el("div","muted","cc-lens unavailable")); }
  else {
    const fields = [
      ["Sessions", s.totalSessions ?? s.sessions ?? s.total_sessions],
      ["Messages", s.totalMessages ?? s.messages ?? s.total_messages],
      ["Tokens", s.totalTokens ?? s.tokens ?? s.total_tokens],
      ["Cost", s.totalCost!=null ? ("$"+Number(s.totalCost).toFixed(2)) : s.cost],
      ["Projects", s.totalProjects ?? s.projects],
    ];
    for(const [k,v] of fields){ if(v!=null) c.appendChild(card(k, typeof v==="number"?v.toLocaleString():v)); }
    if(!c.children.length){ c.appendChild(el("div","muted","no stats fields"));}
  }
  document.getElementById("lens-meta").textContent = meta || "";
}
function renderSessions(arr){
  const wrap = document.getElementById("sessions"); wrap.innerHTML="";
  if(!arr || !arr.length){ wrap.appendChild(el("p","muted","No sessions.")); return; }
  const t = el("table"); const th = el("thead");
  th.innerHTML = "<tr><th>Session</th><th>Project</th><th>Messages</th><th>Tokens</th><th>Updated</th></tr>";
  t.appendChild(th);
  const tb = el("tbody");
  for(const s of arr.slice(0,25)){
    const tr = el("tr");
    const id = s.id || s.sessionId || s.session_id || "";
    tr.innerHTML = `<td>${(id+"").slice(0,8)}</td><td>${s.project||s.projectName||s.cwd||""}</td><td>${s.messageCount??s.messages??""}</td><td>${(s.totalTokens??s.tokens??"").toLocaleString?.()||""}</td><td>${s.lastActivity||s.updatedAt||s.mtime||""}</td>`;
    tb.appendChild(tr);
  }
  t.appendChild(tb); wrap.appendChild(t);
}
async function tick(){
  try {
    const d = await j("/api/state");
    renderGraph(d.graph||{});
    renderLens(d.lens_stats, d.lens_base ? ("source: "+d.lens_base) : "cc-lens not reachable");
    renderSessions(d.lens_sessions||[]);
    setStatus(true, "live");
  } catch (e) {
    setStatus(false, "error: "+e.message);
  }
}
tick(); setInterval(tick, POLL_MS);
</script></body></html>"""


def _find_free_port(preferred: int = 8787) -> int:
    import socket
    candidates = [preferred] + list(range(8788, 8820))
    for p in candidates:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.bind(("127.0.0.1", p))
            s.close()
            return p
        except OSError:
            s.close()
            continue
    # Last resort: OS-assigned
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def _fetch_lens_json(base: str, path: str, timeout: float = 4.0):
    try:
        req = urllib.request.Request(base + path, headers={"User-Agent": "context-os-dashboard"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception:
        return None


def cmd_dashboard(args: argparse.Namespace) -> int:
    import http.server
    import threading

    graph_path = Path(args.graph)

    # Discover / start cc-lens (reuse helpers)
    cc_base = _discover_cc_lens()
    cc_message = ""
    if not cc_base and not args.no_lens:
        ok, cc_message = _start_cc_lens()
        if ok:
            print(f"[dashboard] {cc_message}", file=sys.stderr)
            cc_base = _wait_cc_lens(max_seconds=args.lens_wait)
    if cc_base:
        print(f"[dashboard] cc-lens at {cc_base}", file=sys.stderr)
    else:
        print("[dashboard] cc-lens unavailable — graph-only mode", file=sys.stderr)

    state_lock = threading.Lock()
    state: dict = {"cc_base": cc_base}

    def build_state() -> dict:
        with state_lock:
            base = state.get("cc_base")
        # Re-probe if lost
        if not base:
            base = _discover_cc_lens()
            if base:
                with state_lock:
                    state["cc_base"] = base

        try:
            KG = _graph_module()
            g = KG(graph_path)
            g.load()
            health = g.health(stale_days=60)
        except Exception as e:
            health = {"error": str(e), "total_nodes": 0, "orphan_count": 0, "stale_count": 0, "hubs": []}

        lens_stats = None
        lens_sessions = None
        if base:
            lens_stats = _fetch_lens_json(base, "/api/stats")
            raw = _fetch_lens_json(base, f"/api/sessions?limit={args.session_limit}")
            if isinstance(raw, dict):
                lens_sessions = raw.get("sessions") or raw.get("data") or raw.get("items")
            elif isinstance(raw, list):
                lens_sessions = raw
        return {
            "graph": health,
            "lens_base": base,
            "lens_stats": lens_stats,
            "lens_sessions": lens_sessions or [],
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    class Handler(http.server.BaseHTTPRequestHandler):
        def log_message(self, fmt, *a):  # silence
            return

        def _send(self, code: int, body: bytes, ctype: str) -> None:
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            path = self.path.split("?", 1)[0]
            if path in ("/", "/index.html"):
                body = _DASHBOARD_HTML.encode("utf-8")
                self._send(200, body, "text/html; charset=utf-8")
                return
            if path == "/api/state":
                try:
                    data = build_state()
                except Exception as e:
                    data = {"error": str(e)}
                body = json.dumps(data).encode("utf-8")
                self._send(200, body, "application/json")
                return
            if path == "/api/stats":
                base = state.get("cc_base") or _discover_cc_lens()
                body = json.dumps(_fetch_lens_json(base, "/api/stats") if base else {"error": "no cc-lens"}).encode("utf-8")
                self._send(200, body, "application/json")
                return
            if path == "/api/sessions":
                base = state.get("cc_base") or _discover_cc_lens()
                qs = self.path.split("?", 1)[1] if "?" in self.path else ""
                body = json.dumps(_fetch_lens_json(base, f"/api/sessions?{qs}") if base else {"error": "no cc-lens"}).encode("utf-8")
                self._send(200, body, "application/json")
                return
            self._send(404, b"not found", "text/plain")

    port = _find_free_port(args.port)
    server = http.server.ThreadingHTTPServer(("127.0.0.1", port), Handler)
    url = f"http://127.0.0.1:{port}"
    print(json.dumps({"ok": True, "url": url, "cc_lens": cc_base, "graph": str(graph_path)}))
    sys.stdout.flush()

    if not args.no_browser:
        try:
            if os.name == "nt":
                subprocess.Popen(["cmd", "/c", "start", "", url], shell=False)
            else:
                subprocess.Popen(["xdg-open", url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[dashboard] shutting down…", file=sys.stderr)
    finally:
        server.shutdown()
        server.server_close()
    return 0


def _load_latest_recs() -> dict:
    """Read the stable multi-variant recs JSON emitted by analyze.py."""
    candidates = [
        Path("C:/tmp/context-os-recs-latest.json"),
        Path("/tmp/context-os-recs-latest.json"),
    ]
    for p in candidates:
        try:
            if p.exists():
                with p.open("r", encoding="utf-8") as f:
                    return json.load(f)
        except (OSError, json.JSONDecodeError):
            continue
    for root in (Path("C:/tmp"), Path("/tmp")):
        if not root.is_dir():
            continue
        files = sorted(
            root.glob("context-os-recs-*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        for f in files:
            try:
                with f.open("r", encoding="utf-8") as fh:
                    return json.load(fh)
            except (OSError, json.JSONDecodeError):
                continue
    return {}


def cmd_rec_list(args: argparse.Namespace) -> int:
    payload = _load_latest_recs()
    by_session = (payload or {}).get("recommendations_by_session", {}) or {}
    if not by_session:
        print(json.dumps({
            "error": "no recommendations file found",
            "hint": "run `context-os cc-lens analyze` or `context-os audit` first",
        }, indent=2))
        return 1

    sid = args.session
    if sid:
        keys = [k for k in by_session.keys() if k == sid or k.startswith(sid)]
        if not keys:
            print(json.dumps({"error": f"no recs for session prefix {sid!r}"}, indent=2))
            return 1
        recs = [r for k in keys for r in by_session[k]]
    else:
        recs = [r for rs in by_session.values() for r in rs]

    recs.sort(key=lambda r: -r.get("confidence", 0))
    if args.format == "json":
        print(json.dumps({"recommendations": recs, "count": len(recs)}, indent=2))
        return 0
    print(f"{len(recs)} recommendations")
    for r in recs[: args.limit]:
        conf = r.get("confidence", 0)
        print(f"- [{conf:.2f}] {r.get('id')}  {r.get('category')}/{r.get('variant')}  {r.get('title')}")
        if r.get("rationale"):
            print(f"     rationale: {r['rationale']}")
        if r.get("suggested_action"):
            print(f"     action:    {r['suggested_action']}")
    return 0


def cmd_rec_mark(args: argparse.Namespace) -> int:
    from context_os.feedback_store import record as fb_record

    payload = _load_latest_recs()
    by_session = (payload or {}).get("recommendations_by_session", {}) or {}
    found: dict | None = None
    for recs in by_session.values():
        for r in recs:
            if r.get("id") == args.rec_id:
                found = r
                break
        if found:
            break

    session_id = (found or {}).get("session_id", "")
    category   = (found or {}).get("category", "")
    signature  = (found or {}).get("signature", "")

    try:
        entry = fb_record(
            rec_id=args.rec_id,
            status=args.status,
            session_id=session_id,
            category=category,
            signature=signature,
            note=args.note,
        )
    except ValueError as e:
        print(json.dumps({"error": str(e)}, indent=2))
        return 1
    print(json.dumps({"ok": True, "entry": entry}, indent=2))
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

    dash = sub.add_parser("dashboard", help="Live HTTP dashboard (graph + cc-lens)")
    dash.add_argument("--graph", default="knowledge_base")
    dash.add_argument("--port", type=int, default=8787)
    dash.add_argument("--session-limit", type=int, default=25, dest="session_limit")
    dash.add_argument("--lens-wait", type=int, default=60, dest="lens_wait",
                      help="Seconds to wait for cc-lens to come up if we had to start it")
    dash.add_argument("--no-browser", action="store_true", dest="no_browser")
    dash.add_argument("--no-lens", action="store_true", dest="no_lens",
                      help="Skip auto-starting cc-lens (graph-only dashboard)")

    cl = sub.add_parser("cc-lens")
    cl.add_argument("subcommand", nargs="?", default="analyze")
    cl.add_argument("--top-n", type=int, default=5)
    cl.add_argument("--sort-by", default="cost")
    cl.add_argument("--sessions-per-project", type=int, default=3)
    cl.add_argument("--project", default=None)
    cl.add_argument("--session", default=None)

    cu = sub.add_parser("ccusage")
    cu.add_argument("rest", nargs=argparse.REMAINDER)

    rec = sub.add_parser("rec", help="Multi-variant recommendations")
    rsub = rec.add_subparsers(dest="rcmd", required=True)
    rl = rsub.add_parser("list", help="List recommendations (optionally for one session)")
    rl.add_argument("--session", default=None, help="Session ID or prefix")
    rl.add_argument("--format", choices=["text", "json"], default="text")
    rl.add_argument("--limit", type=int, default=20)
    rm = rsub.add_parser("mark", help="Record feedback on a recommendation")
    rm.add_argument("rec_id")
    rm.add_argument("--status", choices=["accepted", "rejected", "known"], required=True)
    rm.add_argument("--note", default=None)

    fm = sub.add_parser("filemap", help="Identify context bloat from repeatedly re-read large files")
    fm.add_argument("--days", type=int, default=30)
    fm.add_argument("--min-reads", type=int, default=3, dest="min_reads")
    fm.add_argument("--min-lines", type=int, default=800, dest="min_lines")
    fm.add_argument("--min-size", type=int, default=100_000, dest="min_size")
    fm.add_argument("--output", default=None)

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
    if args.cmd == "dashboard":
        return cmd_dashboard(args)
    if args.cmd == "cc-lens":
        return cmd_cc_lens(args)
    if args.cmd == "ccusage":
        return cmd_ccusage(args)
    if args.cmd == "rec":
        if args.rcmd == "list":
            return cmd_rec_list(args)
        if args.rcmd == "mark":
            return cmd_rec_mark(args)
    if args.cmd == "filemap":
        return cmd_filemap(args)
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
