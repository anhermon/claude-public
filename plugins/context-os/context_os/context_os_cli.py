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


_AUDIT_CSS = """
:root{--bg:#0f1419;--panel:#1a2029;--panel2:#222a36;--border:#2d3642;
--text:#e6edf3;--muted:#8b949e;--accent:#58a6ff;--ok:#3fb950;--warn:#d29922;
--hi:#db6d28;--crit:#f85149;--gray:#6e7681;}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--text);
font:14px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;padding:24px}
h1{margin:0 0 4px;font-size:22px}
h2{margin:0 0 12px;font-size:15px;color:var(--muted);text-transform:uppercase;letter-spacing:.08em}
.meta{color:var(--muted);font-size:12px;margin-bottom:20px}
.meta a{color:var(--accent);margin-right:14px;text-decoration:none}
.grid{display:grid;gap:16px;grid-template-columns:repeat(auto-fit,minmax(280px,1fr))}
.card{background:var(--panel);border:1px solid var(--border);border-radius:10px;padding:18px;overflow:hidden}
.card.wide{grid-column:1/-1}
.tile-row{display:grid;grid-template-columns:repeat(auto-fit,minmax(110px,1fr));gap:10px;margin-top:8px}
.tile{background:var(--panel2);border-radius:8px;padding:12px;text-align:center}
.tile .n{font-size:22px;font-weight:600;color:var(--accent)}
.tile .l{font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:.05em;margin-top:4px}
table{width:100%;border-collapse:collapse;margin-top:8px;font-size:13px}
th,td{text-align:left;padding:6px 8px;border-bottom:1px solid var(--border)}
th{color:var(--muted);font-weight:500;font-size:11px;text-transform:uppercase}
.badge{display:inline-block;padding:2px 8px;border-radius:10px;font-size:11px;font-weight:600}
.b-gray{background:#30363d;color:#c9d1d9}
.b-yellow{background:#3a2f12;color:#d29922}
.b-orange{background:#431f0f;color:#db6d28}
.b-red{background:#4d1017;color:#f85149}
.bar-row{display:flex;align-items:center;gap:8px;margin:4px 0;font-size:12px}
.bar-row .d{width:80px;color:var(--muted)}
.bar-row .b{flex:1;height:14px;background:var(--panel2);border-radius:3px;overflow:hidden}
.bar-row .b>div{height:100%;background:linear-gradient(90deg,var(--accent),#79c0ff)}
.bar-row .v{width:70px;text-align:right;font-variant-numeric:tabular-nums}
.warn-card{background:#2d1f0a;border-color:#6b4a0f}
.warn-card h2{color:var(--warn)}
.cta{display:inline-block;margin-top:8px;padding:6px 12px;background:var(--accent);
color:#000;border-radius:6px;font-weight:600;text-decoration:none;font-size:12px}
code{background:var(--panel2);padding:1px 6px;border-radius:3px;font-size:12px}
ul.rb{list-style:none;padding:0;margin:8px 0 0;font-size:12px}
ul.rb li{padding:4px 0;border-bottom:1px solid var(--border);display:flex;justify-content:space-between}
"""


def _vs_normal_badge(label: str | None) -> str:
    if not label:
        return ""
    cls = {"below normal": "b-gray", "normal": "b-gray", "elevated": "b-yellow",
           "high": "b-orange", "record": "b-red"}.get(label.lower(), "b-gray")
    return f'<span class="badge {cls}">{html.escape(label)}</span>'


def _render_limits_card(report: dict) -> str:
    if not report or report.get("error"):
        err = html.escape(str(report.get("error", "no data")) if report else "no data")
        return f'<div class="card warn-card"><h2>Rate limits</h2><p>Unavailable: {err}</p></div>'
    parts = ['<div class="card"><h2>Rate limits</h2>']
    a = report.get("active_5h_window")
    if a:
        parts.append('<div style="font-size:12px;color:var(--muted)">Active 5h window</div>')
        parts.append('<div class="tile-row">')
        parts.append(f'<div class="tile"><div class="n">${a.get("cost_usd",0):.2f}</div><div class="l">cost</div></div>')
        parts.append(f'<div class="tile"><div class="n">{a.get("tokens",0):,}</div><div class="l">tokens</div></div>')
        parts.append('</div>')
        models = ", ".join(html.escape(str(m)) for m in (a.get("models") or [])) or "—"
        parts.append(f'<div style="margin-top:8px;font-size:12px">Models: {models} {_vs_normal_badge(a.get("vs_normal"))}</div>')
    else:
        parts.append('<p style="color:var(--muted)">No active 5h block — idle.</p>')
    w = report.get("weekly_rolling_7d") or {}
    if w:
        total = w.get("total_cost_usd", 0)
        fam = w.get("cost_by_family_usd") or {}
        wtotal = w.get("total") if isinstance(w.get("total"), dict) else {}
        parts.append('<div style="margin-top:14px;font-size:12px;color:var(--muted)">Weekly rolling 7d</div>')
        parts.append('<div class="tile-row">')
        parts.append(f'<div class="tile"><div class="n">${total:.2f}</div><div class="l">total {_vs_normal_badge(wtotal.get("vs_normal") if isinstance(wtotal,dict) else None)}</div></div>')
        parts.append(f'<div class="tile"><div class="n">${fam.get("sonnet",0):.2f}</div><div class="l">sonnet</div></div>')
        parts.append(f'<div class="tile"><div class="n">${fam.get("opus",0):.2f}</div><div class="l">opus</div></div>')
        parts.append('</div>')
    recent = report.get("recent_5h_blocks") or []
    if recent:
        parts.append('<div style="margin-top:14px;font-size:12px;color:var(--muted)">Recent 5h blocks</div>')
        parts.append('<ul class="rb">')
        for b in recent[-5:]:
            active_mark = " •" if b.get("active") else ""
            parts.append(
                f'<li><span>{html.escape(str(b.get("start","")))}{active_mark}</span>'
                f'<span>${b.get("cost_usd",0):.2f} · {b.get("tokens",0):,} tok</span></li>'
            )
        parts.append('</ul>')
    parts.append('</div>')
    return "".join(parts)


def _render_graph_card(health: dict) -> str:
    orphan_n = health.get("orphan_count", len(health.get("orphans") or []))
    stale_n = len(health.get("stale") or [])
    hubs = health.get("hubs") or []
    parts = [
        '<div class="card"><h2>Graph health</h2>',
        '<div class="tile-row">',
        f'<div class="tile"><div class="n">{health.get("total_nodes",0)}</div><div class="l">nodes</div></div>',
        f'<div class="tile"><div class="n">{orphan_n}</div><div class="l">orphans</div></div>',
        f'<div class="tile"><div class="n">{stale_n}</div><div class="l">stale</div></div>',
        f'<div class="tile"><div class="n">{len(hubs)}</div><div class="l">hubs</div></div>',
        '</div>',
    ]
    if hubs:
        parts.append('<table><thead><tr><th>Top hub</th><th>in</th><th>out</th></tr></thead><tbody>')
        for h in hubs[:5]:
            parts.append(
                f'<tr><td>{html.escape(str(h.get("name") or h.get("path","")))}</td>'
                f'<td>{h.get("links_in",0)}</td><td>{h.get("links_out",0)}</td></tr>'
            )
        parts.append('</tbody></table>')
    parts.append('</div>')
    return "".join(parts)


def _render_ccusage_card() -> tuple[str, bool]:
    try:
        r = subprocess.run(
            ["npx", "ccusage@latest", "daily", "--json"],
            capture_output=True, text=True, timeout=120, shell=(os.name == "nt"),
        )
        if r.returncode != 0:
            raise RuntimeError((r.stderr or "")[:300] or "non-zero exit")
        data = json.loads(r.stdout or "{}")
    except Exception as e:
        msg = html.escape(str(e)[:200])
        return (
            '<div class="card warn-card"><h2>ccusage</h2>'
            f'<p>ccusage not installed or failed: <code>{msg}</code></p>'
            '<a class="cta" href="#" onclick="return false">Run <code>context-os doctor</code></a>'
            '</div>', False
        )
    days = data.get("daily") or data.get("data") or []
    if not isinstance(days, list):
        days = []
    last7 = days[-7:]
    rows = []
    for d in last7:
        date_s = str(d.get("date") or d.get("day") or "")
        cost = float(d.get("totalCost") or d.get("cost") or d.get("totalCostUsd") or 0)
        rows.append((date_s, cost))
    max_cost = max((c for _, c in rows), default=0) or 1.0
    parts = ['<div class="card"><h2>ccusage — last 7d</h2>']
    if not rows:
        parts.append('<p style="color:var(--muted)">No daily data.</p>')
    else:
        total = sum(c for _, c in rows)
        parts.append(f'<div style="font-size:12px;color:var(--muted);margin-bottom:8px">Total: ${total:.2f}</div>')
        for date_s, cost in rows:
            w = int((cost / max_cost) * 100) if max_cost else 0
            parts.append(
                f'<div class="bar-row"><div class="d">{html.escape(date_s)}</div>'
                f'<div class="b"><div style="width:{w}%"></div></div>'
                f'<div class="v">${cost:.2f}</div></div>'
            )
    parts.append('</div>')
    return "".join(parts), True


def _render_cclens_card(ts: str) -> tuple[str, str | None, bool]:
    try:
        from context_os.cc_lens_url import find_running_cc_lens
        url = find_running_cc_lens()
    except Exception:
        url = None
    if not url:
        return (
            '<div class="card warn-card"><h2>cc-lens</h2>'
            '<p>cc-lens not running — start with <code>npx cc-lens</code>.</p>'
            '<a class="cta" href="#" onclick="return false">Run <code>context-os doctor</code></a>'
            '</div>', None, False
        )
    html_path = f"/tmp/cc-lens-report-{ts}.html"
    spec_path = f"/tmp/cc-lens-spec-{ts}.json"
    analyze_ok = False
    try:
        exe = sys.executable
        analyze = SCRIPTS_DIR / "analyze.py"
        gen = SCRIPTS_DIR / "generate_dashboard.py"
        r = subprocess.run(
            [exe, str(analyze), "--top-n", "3", "--output", spec_path],
            capture_output=True, timeout=120,
        )
        if r.returncode == 0:
            r2 = subprocess.run(
                [exe, str(gen), "--spec", spec_path, "--output", html_path],
                capture_output=True, timeout=120,
            )
            analyze_ok = r2.returncode == 0
    except Exception:
        analyze_ok = False
    safe_url = html.escape(url)
    parts = [
        '<div class="card"><h2>cc-lens</h2>',
        f'<p><a class="cta" href="{safe_url}" target="_blank">Open cc-lens dashboard →</a></p>',
    ]
    if analyze_ok:
        parts.append(f'<p style="margin-top:8px;font-size:12px"><a href="file://{html.escape(html_path)}" style="color:var(--accent)">Open local cc-lens report →</a></p>')
    else:
        parts.append('<p style="margin-top:8px;font-size:12px;color:var(--muted)">Local report generation failed.</p>')
    parts.append('</div>')
    return "".join(parts), (html_path if analyze_ok else None), True


def cmd_audit(args: argparse.Namespace) -> int:
    # New behavior: if --out is given (or legacy sidecar dashboard flag), build the
    # full forensic dashboard by parsing local JSONL. Works without cc-lens/ccusage.
    if getattr(args, "out", None):
        from context_os.forensic_dashboard import write_dashboard
        out_dir = Path(args.out).expanduser().resolve()
        days = int(getattr(args, "days", 30) or 30)
        project_filter = getattr(args, "project", None)
        try:
            idx = write_dashboard(out_dir, days=days, project_filter=project_filter)
        except Exception as e:
            print(json.dumps({"ok": False, "error": str(e)}), file=sys.stderr)
            return 1
        uri = idx.resolve().as_uri()
        print(json.dumps({
            "ok": True,
            "dashboard": str(idx),
            "data_dir": str(idx.parent / "data"),
            "days": days,
            "project_filter": project_filter,
        }, indent=2))
        print(f"\nOpen file:///{idx.resolve().as_posix().lstrip('/')}")
        print(f"(or: {uri})")
        return 0

    KG = _graph_module()
    g = KG(Path(args.graph))
    g.load()
    health = g.health(stale_days=60)

    rate_report: dict = {}
    try:
        from context_os.limits import compute_report
        rate_report = compute_report() or {}
    except Exception as e:
        rate_report = {"error": str(e)}

    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    limits_html = _render_limits_card(rate_report)
    graph_html = _render_graph_card(health)
    ccusage_html, ccusage_ok = _render_ccusage_card()
    cclens_html, cc_lens_html_path, cclens_ok = _render_cclens_card(ts)

    bundle_ts = Path(f"/tmp/context-os-audit-bundle-{ts}.html")
    header = (
        f'<h1>context-os — Context & Token Dashboard</h1>'
        f'<div class="meta">{html.escape(now_str)}'
        f' &nbsp;·&nbsp; <a href="file://{bundle_ts}">this bundle</a>'
    )
    if cc_lens_html_path:
        header += f' <a href="file://{html.escape(cc_lens_html_path)}">cc-lens report</a>'
    header += '</div>'

    page = (
        '<!DOCTYPE html><html><head><meta charset="utf-8">'
        '<title>context-os — Context & Token Dashboard</title>'
        f'<style>{_AUDIT_CSS}</style></head><body>'
        + header
        + '<div class="grid">'
        + limits_html
        + graph_html
        + ccusage_html
        + cclens_html
        + '</div></body></html>'
    )

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
                "rate_limits": rate_report,
                "dependencies": {"ccusage": ccusage_ok, "cc_lens": cclens_ok},
                "audit_html": str(bundle_ts),
                "audit_html_latest": "/tmp/context-os-audit-bundle-latest.html",
                "cc_lens_html": cc_lens_html_path,
            },
            indent=2,
            default=str,
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
    aud.add_argument("--days", type=int, default=30,
                     help="Session lookback window for forensic dashboard (default: 30)")
    aud.add_argument("--out", default=None,
                     help="Output directory for full forensic dashboard (index.html + data/). "
                          "When set, skips the legacy /tmp audit bundle and builds the full dashboard from local JSONL.")
    aud.add_argument("--project", default=None,
                     help="Only include sessions whose project folder name contains this substring")

    cl = sub.add_parser("cc-lens")
    cl.add_argument("subcommand", nargs="?", default="analyze")
    cl.add_argument("--top-n", type=int, default=5)
    cl.add_argument("--sort-by", default="cost")
    cl.add_argument("--sessions-per-project", type=int, default=3)
    cl.add_argument("--project", default=None)
    cl.add_argument("--session", default=None)

    cu = sub.add_parser("ccusage")
    cu.add_argument("rest", nargs=argparse.REMAINDER)

    lim = sub.add_parser("limits", help="Rate-limit view: 5h blocks + weekly per-model")
    lim.add_argument("--format", choices=["text", "json"], default="text")

    doc = sub.add_parser("doctor", help="Preflight checks")
    doc.add_argument("--format", choices=["text", "json"], default="text")

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
    if args.cmd == "limits":
        from context_os.limits import cmd_limits
        return cmd_limits(args)
    if args.cmd == "doctor":
        from context_os.doctor import cmd_doctor
        return cmd_doctor(args)
    return 1


def main(argv: list[str] | None = None) -> int:
    argv = list(argv if argv is not None else sys.argv[1:])
    if not argv:
        print(
            json.dumps(
                {
                    "help": "context-os doctor | graph health | graph query T | sessions list | heat | audit | ingest session ID | cc-lens analyze | ccusage daily",
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
