#!/usr/bin/env python3
"""
cc-lens dashboard generator.

Reads a JSON spec from --spec and writes a self-contained HTML dashboard to --output.
No dependencies beyond stdlib.

Usage:
    python3 generate_dashboard.py --spec /tmp/cc-lens-spec.json --output /tmp/cc-lens-report.html
"""

import argparse
import json
import sys
from datetime import datetime


def safe_json(obj) -> str:
    """JSON-encode obj and escape sequences that break <script> tags."""
    return json.dumps(obj).replace("</", "<\\/")


def slim_replay(replay) -> dict | None:
    """Strip replay to chart-only data (index, cost, tokens, tool_count). No text."""
    if not replay:
        return None
    raw_turns = replay if isinstance(replay, list) else replay.get("turns", [])
    turns = []
    for i, t in enumerate(raw_turns):
        if not isinstance(t, dict):
            continue
        if t.get("type") != "assistant":
            continue
        usage = t.get("usage") or {}
        turns.append({
            "i": i,
            "cost": round(t.get("estimated_cost", 0), 6),
            "in": usage.get("input_tokens", 0),
            "out": usage.get("output_tokens", 0),
            "tools": len(t.get("tool_calls") or []),
        })
    return {"turns": turns[:120]} if turns else None

# ─── Waste category metadata ──────────────────────────────────────────────────

WASTE_LABELS = {
    "context_bloat":      "Context Bloat",
    "cache_inefficiency": "Cache Inefficiency",
    "tool_hammering":     "Tool Hammering",
    "compaction_absence": "Compaction Absence",
    "parallel_sprawl":    "Parallel Sprawl",
    "interruption_loops": "Interruption Loops",
    "thinking_waste":     "Thinking Waste",
}

WASTE_COLORS = {
    "context_bloat":      "#ef4444",
    "cache_inefficiency": "#f97316",
    "tool_hammering":     "#6366f1",
    "compaction_absence": "#06b6d4",
    "parallel_sprawl":    "#8b5cf6",
    "interruption_loops": "#ec4899",
    "thinking_waste":     "#84cc16",
}

WASTE_FIXES = {
    "context_bloat":
        "Break long sessions into focused sub-tasks. Run /compact when context feels heavy. "
        "Prune CLAUDE.md and memory files.",
    "cache_inefficiency":
        "Keep system prompts stable between turns. Avoid randomizing tool descriptions. "
        "Cache hit rate should be >40%.",
    "tool_hammering":
        "Batch shell commands into fewer calls. Use glob/grep instead of repeated reads. "
        "Delegate exploration to Agent subagents.",
    "compaction_absence":
        "Run /compact periodically for sessions >45 min. Configure auto-compaction threshold "
        "in settings.",
    "parallel_sprawl":
        "Avoid running multiple Claude Code sessions on the same project simultaneously. "
        "Consolidate work.",
    "interruption_loops":
        "Write clearer prompts upfront. Use TodoWrite to maintain shared task state. "
        "Reduce scope per session.",
    "thinking_waste":
        "Disable extended thinking for routine file edits, searches, and code changes. "
        "Reserve for complex reasoning.",
}

# ─── Scatter dataset builder ──────────────────────────────────────────────────

def build_scatter_datasets(sessions):
    """Group sessions by top_waste category, return list of Chart.js dataset dicts."""
    groups: dict = {}
    for s in sessions:
        cat = s.get("top_waste") or "unknown"
        if cat not in groups:
            color = WASTE_COLORS.get(cat, "#64748b")
            groups[cat] = {
                "label": WASTE_LABELS.get(cat, cat),
                "data": [],
                "backgroundColor": color + "cc",
                "borderColor": color,
                "pointRadius": 5,
                "pointHoverRadius": 8,
            }
        groups[cat]["data"].append({
            "x": round(s.get("duration_minutes", 0), 1),
            "y": round(s.get("estimated_cost", 0), 4),
            "label": s.get("session_id", "")[:8],
            "sid": s.get("session_id", ""),
        })
    return list(groups.values())


# ─── Projects bar chart builder ───────────────────────────────────────────────

def build_projects_bar(projects):
    """Return Chart.js stacked bar data: one dataset per waste category."""
    labels = [p.get("display_name", p.get("slug", "?")) for p in projects]
    datasets = []
    for cat in WASTE_LABELS:
        color = WASTE_COLORS[cat]
        datasets.append({
            "label": WASTE_LABELS[cat],
            "data": [p.get("waste_scores", {}).get(cat, 0) for p in projects],
            "backgroundColor": color + "bb",
            "borderColor": color,
            "borderWidth": 1,
        })
    return {"labels": labels, "datasets": datasets}


# ─── Sessions JS object ───────────────────────────────────────────────────────

def build_sessions_js(sessions):
    """Return a dict keyed by session_id for embedding in JS."""
    result = {}
    for s in sessions:
        sid = s.get("session_id", "")
        result[sid] = {
            "session_id": sid,
            "project_name": s.get("project_name", ""),
            "estimated_cost": s.get("estimated_cost", 0),
            "duration_minutes": s.get("duration_minutes", 0),
            "cache_hit_rate_pct": s.get("cache_hit_rate_pct", 0),
            "cache_reuse_ratio": s.get("cache_reuse_ratio", 0),
            "total_tools": s.get("total_tools", 0),
            "tool_breakdown": s.get("tool_breakdown", {}),
            "waste_score": s.get("waste_score", 0),
            "top_waste": s.get("top_waste", ""),
            "waste_scores": s.get("waste_scores", {}),
            "waste_evidence": s.get("waste_evidence", {}),
            "replay": slim_replay(s.get("replay")),
        }
    return result


# ─── HTML generation ──────────────────────────────────────────────────────────

def generate_html(spec: dict) -> str:
    summary = spec.get("summary", {})
    projects = spec.get("projects", [])
    sessions = spec.get("sessions", [])
    heatmap = spec.get("heatmap", {})
    time_series = spec.get("time_series", [])
    thresholds = spec.get("thresholds", {})
    generated_at = spec.get("generated_at", datetime.now().isoformat())

    # Truncate date string for display
    try:
        disp_date = datetime.fromisoformat(generated_at.replace("Z", "+00:00")).strftime("%Y-%m-%d %H:%M UTC")
    except Exception:
        disp_date = generated_at[:19]

    total_cost = summary.get("total_cost", 0)
    total_sessions = summary.get("total_sessions", 0)
    project_count = summary.get("project_count", 0)
    potential_savings = summary.get("potential_savings", 0)
    top_waste_label = summary.get("top_waste_label", "—")
    top_waste_color = summary.get("top_waste_color", "#6366f1")

    # Pre-sort sessions for table
    top_sessions = sorted(sessions, key=lambda s: s.get("estimated_cost", 0), reverse=True)[:50]

    # Build data blobs
    scatter_datasets = build_scatter_datasets(sessions)
    projects_bar = build_projects_bar(projects)
    sessions_js = build_sessions_js(sessions)

    radar_data = spec.get("waste_radar", None)
    if radar_data is None:
        # Build radar from projects
        radar_labels = list(WASTE_LABELS.values())
        radar_keys = list(WASTE_LABELS.keys())
        radar_colors = ["#6366f1", "#ef4444", "#f97316", "#06b6d4", "#8b5cf6"]
        radar_datasets = []
        for i, p in enumerate(projects[:5]):
            color = radar_colors[i % len(radar_colors)]
            radar_datasets.append({
                "label": p.get("display_name", p.get("slug", "")),
                "data": [p.get("waste_scores", {}).get(k, 0) for k in radar_keys],
                "backgroundColor": color + "33",
                "borderColor": color,
                "borderWidth": 2,
                "pointBackgroundColor": color,
            })
        radar_data = {"labels": radar_labels, "datasets": radar_datasets}

    waste_labels_json = safe_json(WASTE_LABELS)
    waste_colors_json = safe_json(WASTE_COLORS)
    waste_fixes_json  = safe_json(WASTE_FIXES)
    scatter_json      = safe_json(scatter_datasets)
    projects_bar_json = safe_json(projects_bar)
    sessions_js_json  = safe_json(sessions_js)
    radar_json        = safe_json(radar_data)
    heatmap_json      = safe_json(heatmap)
    time_series_json  = safe_json(time_series)
    thresholds_json   = safe_json(thresholds)

    def fmt_cost(v):
        return f"${v:,.2f}"

    def score_class(score):
        if score <= 30:
            return "badge-green"
        elif score <= 60:
            return "badge-amber"
        else:
            return "badge-red"

    def dur_str(mins):
        if mins < 60:
            return f"{int(mins)}m"
        h = int(mins // 60)
        m = int(mins % 60)
        return f"{h}h {m}m"

    # Build table rows
    table_rows = []
    for s in top_sessions:
        sid = s.get("session_id", "")
        sid8 = sid[:8]
        proj = s.get("project_name", "")
        cost = fmt_cost(s.get("estimated_cost", 0))
        dur = dur_str(s.get("duration_minutes", 0))
        cache = f"{s.get('cache_hit_rate_pct', 0):.0f}%"
        tools = s.get("total_tools", 0)
        ws = s.get("waste_score", 0)
        tw = s.get("top_waste", "")
        tw_label = WASTE_LABELS.get(tw, tw)
        tw_color = WASTE_COLORS.get(tw, "#64748b")
        sc = score_class(ws)
        table_rows.append(
            f'<tr onclick="openDrilldown(\'{sid}\')" data-sid="{sid}">'
            f'<td><a class="sid-link" onclick="event.stopPropagation();openDrilldown(\'{sid}\');return false;">{sid8}</a></td>'
            f'<td>{proj}</td>'
            f'<td class="num">{cost}</td>'
            f'<td class="num">{dur}</td>'
            f'<td class="num">{cache}</td>'
            f'<td class="num">{tools}</td>'
            f'<td class="num"><span class="badge {sc}">{ws}</span></td>'
            f'<td><span class="waste-tag" style="background:{tw_color}22;color:{tw_color};border:1px solid {tw_color}44">{tw_label}</span></td>'
            f'</tr>'
        )
    table_rows_html = "\n".join(table_rows)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>cc-lens Token Forensics</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.4/dist/chart.umd.min.js"></script>
<style>
  :root {{
    --bg: #0f1117;
    --surface: #1e293b;
    --surface2: #263248;
    --border: #334155;
    --text: #e2e8f0;
    --text-muted: #94a3b8;
    --accent: #6366f1;
    --green: #22c55e;
    --amber: #f59e0b;
    --red: #ef4444;
    --radius: 8px;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ background: var(--bg); color: var(--text); font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; font-size: 14px; }}
  a {{ color: var(--accent); text-decoration: none; }}
  a:hover {{ text-decoration: underline; }}

  /* ── Layout ── */
  #main-view {{ padding: 20px; max-width: 1600px; margin: 0 auto; }}
  #drilldown-view {{ display: none; padding: 20px; max-width: 1600px; margin: 0 auto; }}

  /* ── Header ── */
  .dash-header {{ display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px; }}
  .dash-header h1 {{ font-size: 22px; font-weight: 700; color: var(--text); }}
  .dash-header .meta {{ color: var(--text-muted); font-size: 13px; }}

  /* ── KPI cards ── */
  .kpi-row {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 20px; }}
  .kpi-card {{ background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 18px 20px; }}
  .kpi-card .kpi-label {{ font-size: 12px; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 6px; }}
  .kpi-card .kpi-value {{ font-size: 28px; font-weight: 700; color: var(--text); }}
  .kpi-card .kpi-sub {{ font-size: 12px; color: var(--text-muted); margin-top: 4px; }}

  /* ── Chart grid ── */
  .chart-row {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 20px; }}
  .chart-row.single {{ grid-template-columns: 1fr; }}
  .chart-card {{ background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 18px; }}
  .chart-card h3 {{ font-size: 13px; font-weight: 600; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 14px; }}
  .chart-wrap {{ position: relative; }}

  /* ── Heatmap ── */
  .heatmap-grid {{ overflow-x: auto; }}
  .heatmap-table {{ border-collapse: collapse; width: 100%; }}
  .heatmap-table th {{ font-size: 10px; color: var(--text-muted); text-align: center; padding: 2px 3px; font-weight: 400; }}
  .heatmap-table td.day-label {{ font-size: 11px; color: var(--text-muted); padding-right: 8px; white-space: nowrap; min-width: 32px; }}
  .heatmap-cell {{ width: 22px; height: 22px; border-radius: 3px; cursor: default; }}
  .heatmap-cell:hover {{ outline: 1px solid var(--accent); }}

  /* ── Table ── */
  .table-card {{ background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 18px; margin-bottom: 20px; overflow-x: auto; }}
  .table-card h3 {{ font-size: 13px; font-weight: 600; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 14px; }}
  table.sessions {{ width: 100%; border-collapse: collapse; }}
  table.sessions th {{ text-align: left; font-size: 12px; color: var(--text-muted); border-bottom: 1px solid var(--border); padding: 8px 10px; cursor: pointer; user-select: none; white-space: nowrap; }}
  table.sessions th:hover {{ color: var(--text); }}
  table.sessions th.sorted-asc::after {{ content: " ▲"; }}
  table.sessions th.sorted-desc::after {{ content: " ▼"; }}
  table.sessions td {{ padding: 9px 10px; border-bottom: 1px solid var(--border); vertical-align: middle; }}
  table.sessions tr:last-child td {{ border-bottom: none; }}
  table.sessions tr:hover {{ background: var(--surface2); cursor: pointer; }}
  td.num {{ text-align: right; font-variant-numeric: tabular-nums; }}
  .sid-link {{ font-family: monospace; font-size: 12px; color: var(--accent); cursor: pointer; }}
  .badge {{ display: inline-block; padding: 2px 8px; border-radius: 12px; font-size: 12px; font-weight: 600; }}
  .badge-green {{ background: #16532322; color: var(--green); border: 1px solid #22c55e44; }}
  .badge-amber {{ background: #78350f22; color: var(--amber); border: 1px solid #f59e0b44; }}
  .badge-red {{ background: #7f1d1d22; color: var(--red); border: 1px solid #ef444444; }}
  .waste-tag {{ display: inline-block; padding: 2px 8px; border-radius: 12px; font-size: 11px; font-weight: 500; }}

  /* ── Drilldown ── */
  .back-btn {{ display: inline-flex; align-items: center; gap: 6px; color: var(--text-muted); cursor: pointer; font-size: 13px; margin-bottom: 18px; background: none; border: none; padding: 0; }}
  .back-btn:hover {{ color: var(--text); }}
  .dd-header {{ display: flex; align-items: flex-start; justify-content: space-between; margin-bottom: 20px; flex-wrap: wrap; gap: 12px; }}
  .dd-title {{ font-size: 20px; font-weight: 700; }}
  .dd-title .dd-project {{ font-size: 14px; color: var(--text-muted); font-weight: 400; margin-top: 2px; }}
  .dd-cost {{ font-size: 28px; font-weight: 700; color: var(--accent); }}
  .dd-kpi-row {{ display: grid; grid-template-columns: repeat(5, 1fr); gap: 12px; margin-bottom: 20px; }}
  .dd-kpi-card {{ background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 14px 16px; }}
  .dd-kpi-card .kpi-label {{ font-size: 11px; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 4px; }}
  .dd-kpi-card .kpi-value {{ font-size: 22px; font-weight: 700; }}

  .findings-section {{ margin-bottom: 20px; }}
  .findings-section h3 {{ font-size: 13px; font-weight: 600; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 14px; }}
  .finding-card {{ background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 16px; margin-bottom: 12px; }}
  .finding-header {{ display: flex; align-items: center; gap: 10px; margin-bottom: 10px; }}
  .finding-cat {{ font-size: 14px; font-weight: 600; }}
  .finding-text {{ color: var(--text); font-size: 13px; line-height: 1.5; margin-bottom: 10px; }}
  .action-card {{ background: var(--surface2); border-radius: 6px; padding: 12px 14px; }}
  .action-card .action-title {{ font-size: 11px; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 6px; }}
  .action-card .action-text {{ font-size: 13px; color: var(--text); line-height: 1.5; }}

  .cache-card {{ background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 18px; margin-bottom: 20px; }}
  .cache-card h3 {{ font-size: 13px; font-weight: 600; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 14px; }}
  .cache-bar-row {{ display: flex; align-items: center; gap: 10px; margin-bottom: 8px; }}
  .cache-bar-label {{ font-size: 12px; color: var(--text-muted); min-width: 110px; }}
  .cache-bar-track {{ flex: 1; background: var(--surface2); border-radius: 4px; height: 14px; overflow: hidden; }}
  .cache-bar-fill {{ height: 100%; border-radius: 4px; }}
  .cache-bar-val {{ font-size: 12px; color: var(--text); min-width: 80px; text-align: right; font-variant-numeric: tabular-nums; }}
  .cache-ratio-row {{ margin-top: 12px; font-size: 13px; color: var(--text); }}
  .cache-ratio-row strong {{ color: var(--accent); }}

  .dd-chart-row {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 20px; }}
  .dd-chart-card {{ background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 18px; }}
  .dd-chart-card h3 {{ font-size: 13px; font-weight: 600; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 14px; }}
</style>
</head>
<body>

<!-- ═══════════════════════════ MAIN VIEW ════════════════════════════ -->
<div id="main-view">

  <div class="dash-header">
    <div>
      <h1>cc-lens Token Forensics</h1>
    </div>
    <div class="meta">Generated: {disp_date} &nbsp;·&nbsp; {total_sessions} sessions &nbsp;·&nbsp; {project_count} projects</div>
  </div>

  <!-- KPI row -->
  <div class="kpi-row">
    <div class="kpi-card">
      <div class="kpi-label">Total Cost</div>
      <div class="kpi-value">{fmt_cost(total_cost)}</div>
      <div class="kpi-sub">across all sessions</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-label">Top Waste</div>
      <div class="kpi-value" style="font-size:20px;color:{top_waste_color}">{top_waste_label}</div>
      <div class="kpi-sub">leading inefficiency</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-label">Sessions</div>
      <div class="kpi-value">{total_sessions:,}</div>
      <div class="kpi-sub">analyzed</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-label">Est. Savings</div>
      <div class="kpi-value" style="color:var(--green)">{fmt_cost(potential_savings)}</div>
      <div class="kpi-sub">if waste addressed</div>
    </div>
  </div>

  <!-- Charts row 1 -->
  <div class="chart-row">
    <div class="chart-card">
      <h3>Projects by Waste Score</h3>
      <div class="chart-wrap" style="height:260px">
        <canvas id="chartProjects"></canvas>
      </div>
    </div>
    <div class="chart-card">
      <h3>Sessions: Duration vs Cost</h3>
      <div class="chart-wrap" style="height:260px">
        <canvas id="chartScatter"></canvas>
      </div>
    </div>
  </div>

  <!-- Radar -->
  <div class="chart-row single">
    <div class="chart-card">
      <h3>Waste Radar — by Project</h3>
      <div class="chart-wrap" style="height:340px">
        <canvas id="chartRadar"></canvas>
      </div>
    </div>
  </div>

  <!-- Heatmap -->
  <div class="chart-card" style="margin-bottom:20px">
    <h3>Session Activity Heatmap</h3>
    <div class="heatmap-grid">
      <table class="heatmap-table" id="heatmapTable"></table>
    </div>
  </div>

  <!-- Trends over time -->
  <div class="chart-row" id="trendRow">
    <div class="chart-card">
      <h3>Daily Cost &amp; Sessions Over Time</h3>
      <div class="chart-wrap" style="height:260px">
        <canvas id="chartTimeCost"></canvas>
      </div>
    </div>
    <div class="chart-card">
      <h3>Cache Hit Rate &amp; Avg Waste Score Over Time</h3>
      <div class="chart-wrap" style="height:260px">
        <canvas id="chartTimeTrend"></canvas>
      </div>
    </div>
  </div>

  <!-- Sessions table -->
  <div class="table-card">
    <h3>Top Sessions (by cost)</h3>
    <table class="sessions" id="sessionsTable">
      <thead>
        <tr>
          <th onclick="sortTable(0)">Session ID</th>
          <th onclick="sortTable(1)">Project</th>
          <th onclick="sortTable(2)" class="num">Cost</th>
          <th onclick="sortTable(3)" class="num">Duration</th>
          <th onclick="sortTable(4)" class="num">Cache Hit%</th>
          <th onclick="sortTable(5)" class="num">Tools</th>
          <th onclick="sortTable(6)" class="num">Waste</th>
          <th onclick="sortTable(7)">Top Issue</th>
        </tr>
      </thead>
      <tbody id="sessionsBody">
{table_rows_html}
      </tbody>
    </table>
  </div>

</div><!-- /main-view -->

<!-- ═══════════════════════════ DRILLDOWN VIEW ════════════════════════════ -->
<div id="drilldown-view">
  <button class="back-btn" onclick="closeDrilldown()">← Back to Dashboard</button>
  <div id="dd-content"></div>
</div>

<!-- ═══════════════════════════ JAVASCRIPT ════════════════════════════ -->
<script>
// ── Data ──────────────────────────────────────────────────────────────────────
const SESSIONS = {sessions_js_json};
const WASTE_LABELS = {waste_labels_json};
const WASTE_COLORS = {waste_colors_json};
const WASTE_FIXES = {waste_fixes_json};
const THRESHOLDS = {thresholds_json};
const HEATMAP_DATA = {heatmap_json};
const TIME_SERIES = {time_series_json};
const SCATTER_DATASETS = {scatter_json};
const RADAR_DATA = {radar_json};
const PROJECTS_BAR = {projects_bar_json};

// ── Utilities ─────────────────────────────────────────────────────────────────
function fmtCost(v) {{
  return '$' + Number(v).toLocaleString('en-US', {{minimumFractionDigits:2, maximumFractionDigits:2}});
}}
function fmtDur(mins) {{
  if (mins < 60) return Math.round(mins) + 'm';
  const h = Math.floor(mins / 60), m = Math.round(mins % 60);
  return h + 'h ' + m + 'm';
}}
function scoreClass(s) {{
  if (s <= 30) return 'badge-green';
  if (s <= 60) return 'badge-amber';
  return 'badge-red';
}}
function wasteBadge(cat, score) {{
  const color = WASTE_COLORS[cat] || '#64748b';
  const label = WASTE_LABELS[cat] || cat;
  const cls = scoreClass(score);
  return `<span class="badge ${{cls}}" style="background:${{color}}22;color:${{color}};border:1px solid ${{color}}44">${{label}} ${{score}}</span>`;
}}

// ── Chart defaults ────────────────────────────────────────────────────────────
Chart.defaults.color = '#94a3b8';
Chart.defaults.borderColor = '#334155';
Chart.defaults.font.family = '-apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif';
Chart.defaults.animation = false;

// ── Projects bar chart ────────────────────────────────────────────────────────
(function() {{
  const ctx = document.getElementById('chartProjects').getContext('2d');
  new Chart(ctx, {{
    type: 'bar',
    data: PROJECTS_BAR,
    options: {{
      animation: false,
      responsive: true,
      maintainAspectRatio: false,
      plugins: {{
        legend: {{ position: 'bottom', labels: {{ boxWidth: 12, padding: 10 }} }},
        tooltip: {{
          callbacks: {{
            title: (items) => items[0].label,
            label: (item) => `${{item.dataset.label}}: ${{item.raw}}`,
          }}
        }}
      }},
      scales: {{
        x: {{ stacked: true, grid: {{ color: '#334155' }}, ticks: {{ color: '#94a3b8' }} }},
        y: {{ stacked: true, grid: {{ color: '#334155' }}, ticks: {{ color: '#94a3b8' }}, title: {{ display: true, text: 'Waste Score Sum', color: '#64748b' }} }},
      }}
    }}
  }});
}})();

// ── Scatter chart ─────────────────────────────────────────────────────────────
(function() {{
  const ctx = document.getElementById('chartScatter').getContext('2d');
  new Chart(ctx, {{
    type: 'scatter',
    data: {{ datasets: SCATTER_DATASETS }},
    options: {{
      animation: false,
      responsive: true,
      maintainAspectRatio: false,
      plugins: {{
        legend: {{ position: 'bottom', labels: {{ boxWidth: 12, padding: 10 }} }},
        tooltip: {{
          callbacks: {{
            label: (item) => {{
              const pt = item.raw;
              return [`${{pt.label || ''}}`, `Cost: ${{fmtCost(pt.y)}}`, `Duration: ${{fmtDur(pt.x)}}`];
            }}
          }}
        }}
      }},
      scales: {{
        x: {{ title: {{ display: true, text: 'Duration (min)', color: '#64748b' }}, grid: {{ color: '#334155' }}, ticks: {{ color: '#94a3b8' }} }},
        y: {{ title: {{ display: true, text: 'Cost ($)', color: '#64748b' }}, grid: {{ color: '#334155' }}, ticks: {{ color: '#94a3b8', callback: v => '$'+v.toFixed(0) }} }},
      }},
      onClick: (evt, elements) => {{
        if (elements.length > 0) {{
          const el = elements[0];
          const pt = SCATTER_DATASETS[el.datasetIndex].data[el.index];
          if (pt && pt.sid) openDrilldown(pt.sid);
        }}
      }}
    }}
  }});
}})();

// ── Radar chart ───────────────────────────────────────────────────────────────
(function() {{
  const ctx = document.getElementById('chartRadar').getContext('2d');
  // Ensure fill colors are set
  const datasets = RADAR_DATA.datasets.map((ds, i) => {{
    const colors = ['#6366f1','#ef4444','#f97316','#06b6d4','#8b5cf6'];
    const c = ds.borderColor || colors[i % colors.length];
    return Object.assign({{}}, ds, {{
      backgroundColor: ds.backgroundColor || c + '33',
      borderColor: ds.borderColor || c,
      pointBackgroundColor: ds.pointBackgroundColor || c,
    }});
  }});
  new Chart(ctx, {{
    type: 'radar',
    data: {{ labels: RADAR_DATA.labels, datasets }},
    options: {{
      animation: false,
      responsive: true,
      maintainAspectRatio: false,
      plugins: {{
        legend: {{ position: 'bottom', labels: {{ boxWidth: 12, padding: 10 }} }},
      }},
      scales: {{
        r: {{
          beginAtZero: true,
          max: 100,
          ticks: {{ stepSize: 25, color: '#64748b', backdropColor: 'transparent' }},
          grid: {{ color: '#334155' }},
          pointLabels: {{ color: '#94a3b8', font: {{ size: 11 }} }},
          angleLines: {{ color: '#334155' }},
        }}
      }}
    }}
  }});
}})();

// ── Heatmap ───────────────────────────────────────────────────────────────────
(function() {{
  const days = ['Sun','Mon','Tue','Wed','Thu','Fri','Sat'];
  const hours = Array.from({{length:24}}, (_,i) => String(i).padStart(2,'0'));
  const table = document.getElementById('heatmapTable');

  // Find max value for intensity scaling
  let maxVal = 1;
  for (let d = 0; d < 7; d++) {{
    for (let h = 0; h < 24; h++) {{
      const v = HEATMAP_DATA[String(d)]?.[String(h)] || 0;
      if (v > maxVal) maxVal = v;
    }}
  }}

  // Header row
  const headerRow = document.createElement('tr');
  headerRow.innerHTML = '<th></th>' + hours.map(h => `<th>${{h}}</th>`).join('');
  table.appendChild(headerRow);

  for (let d = 0; d < 7; d++) {{
    const row = document.createElement('tr');
    let cells = `<td class="day-label">${{days[d]}}</td>`;
    for (let h = 0; h < 24; h++) {{
      const val = HEATMAP_DATA[String(d)]?.[String(h)] || 0;
      const intensity = maxVal > 0 ? val / maxVal : 0;
      const alpha = Math.round(intensity * 200 + (val > 0 ? 40 : 0));
      const bg = val > 0
        ? `rgba(99,102,241,${{(intensity * 0.8 + 0.15).toFixed(2)}})`
        : 'rgba(30,41,59,0.5)';
      cells += `<td><div class="heatmap-cell" style="background:${{bg}}" title="${{days[d]}} ${{h.toString().padStart(2,'0')}}:00 — ${{val}} session${{val !== 1 ? 's' : ''}}"></div></td>`;
    }}
    row.innerHTML = cells;
    table.appendChild(row);
  }}
}})();

// ── Time series charts ────────────────────────────────────────────────────────
(function() {{
  if (!TIME_SERIES || TIME_SERIES.length === 0) {{
    document.getElementById('trendRow').style.display = 'none';
    return;
  }}
  const labels = TIME_SERIES.map(d => d.date);
  const costs  = TIME_SERIES.map(d => d.cost);
  const counts = TIME_SERIES.map(d => d.sessions);
  const cacheRates = TIME_SERIES.map(d => d.avg_cache_hit_rate);
  const wasteScores = TIME_SERIES.map(d => d.avg_waste_score);

  // Chart 1: cost (bar) + session count (line, right axis)
  new Chart(document.getElementById('chartTimeCost').getContext('2d'), {{
    type: 'bar',
    data: {{
      labels,
      datasets: [
        {{
          type: 'bar',
          label: 'Daily cost ($)',
          data: costs,
          backgroundColor: '#6366f177',
          borderColor: '#6366f1',
          borderWidth: 1,
          yAxisID: 'yCost',
        }},
        {{
          type: 'line',
          label: 'Sessions',
          data: counts,
          borderColor: '#f59e0b',
          backgroundColor: 'transparent',
          borderWidth: 2,
          pointRadius: 3,
          tension: 0.3,
          yAxisID: 'ySessions',
        }},
      ]
    }},
    options: {{
      animation: false,
      responsive: true,
      maintainAspectRatio: false,
      plugins: {{
        legend: {{ position: 'bottom', labels: {{ boxWidth: 12, padding: 10 }} }},
        tooltip: {{
          callbacks: {{
            label: (item) => item.dataset.label === 'Sessions'
              ? `Sessions: ${{item.raw}}`
              : `Cost: ${{fmtCost(item.raw)}}`,
          }}
        }}
      }},
      scales: {{
        x: {{ grid: {{ color: '#334155' }}, ticks: {{ color: '#94a3b8', maxTicksLimit: 12 }} }},
        yCost: {{
          position: 'left',
          grid: {{ color: '#334155' }},
          ticks: {{ color: '#94a3b8', callback: v => '$' + v.toFixed(0) }},
          title: {{ display: true, text: 'Cost ($)', color: '#64748b' }},
        }},
        ySessions: {{
          position: 'right',
          grid: {{ drawOnChartArea: false }},
          ticks: {{ color: '#f59e0b' }},
          title: {{ display: true, text: 'Sessions', color: '#f59e0b' }},
        }},
      }},
    }}
  }});

  // Chart 2: cache hit rate (line) + avg waste score (line, right axis)
  new Chart(document.getElementById('chartTimeTrend').getContext('2d'), {{
    type: 'line',
    data: {{
      labels,
      datasets: [
        {{
          label: 'Avg cache hit rate (%)',
          data: cacheRates,
          borderColor: '#22c55e',
          backgroundColor: '#22c55e22',
          borderWidth: 2,
          pointRadius: 3,
          tension: 0.3,
          fill: false,
          yAxisID: 'yCache',
        }},
        {{
          label: 'Avg waste score',
          data: wasteScores,
          borderColor: '#ef4444',
          backgroundColor: '#ef444422',
          borderWidth: 2,
          pointRadius: 3,
          tension: 0.3,
          fill: false,
          yAxisID: 'yWaste',
        }},
      ]
    }},
    options: {{
      animation: false,
      responsive: true,
      maintainAspectRatio: false,
      plugins: {{
        legend: {{ position: 'bottom', labels: {{ boxWidth: 12, padding: 10 }} }},
        tooltip: {{
          callbacks: {{
            label: (item) => item.dataset.label.includes('cache')
              ? `Cache hit: ${{item.raw.toFixed(1)}}%`
              : `Avg waste: ${{item.raw.toFixed(1)}}`,
          }}
        }}
      }},
      scales: {{
        x: {{ grid: {{ color: '#334155' }}, ticks: {{ color: '#94a3b8', maxTicksLimit: 12 }} }},
        yCache: {{
          position: 'left',
          min: 0, max: 100,
          grid: {{ color: '#334155' }},
          ticks: {{ color: '#22c55e', callback: v => v + '%' }},
          title: {{ display: true, text: 'Cache Hit %', color: '#22c55e' }},
        }},
        yWaste: {{
          position: 'right',
          min: 0, max: 100,
          grid: {{ drawOnChartArea: false }},
          ticks: {{ color: '#ef4444' }},
          title: {{ display: true, text: 'Avg Waste Score', color: '#ef4444' }},
        }},
      }},
    }}
  }});
}})();

// ── Table sorting ─────────────────────────────────────────────────────────────
let sortCol = 2, sortDir = -1;

function sortTable(col) {{
  const tbody = document.getElementById('sessionsBody');
  const rows = Array.from(tbody.querySelectorAll('tr'));
  const ths = document.querySelectorAll('#sessionsTable thead th');

  if (sortCol === col) {{ sortDir *= -1; }} else {{ sortCol = col; sortDir = -1; }}

  ths.forEach((th, i) => {{
    th.classList.remove('sorted-asc','sorted-desc');
    if (i === col) th.classList.add(sortDir > 0 ? 'sorted-asc' : 'sorted-desc');
  }});

  rows.sort((a, b) => {{
    const av = a.cells[col]?.textContent.trim() || '';
    const bv = b.cells[col]?.textContent.trim() || '';
    // Numeric detect
    const an = parseFloat(av.replace(/[$,%hm ]/g,''));
    const bn = parseFloat(bv.replace(/[$,%hm ]/g,''));
    if (!isNaN(an) && !isNaN(bn)) return (an - bn) * sortDir;
    return av.localeCompare(bv) * sortDir;
  }});

  rows.forEach(r => tbody.appendChild(r));
}}

// ── Drilldown ─────────────────────────────────────────────────────────────────
let ddToolChart = null;
let ddReplayChart = null;

function openDrilldown(sid) {{
  const s = SESSIONS[sid];
  if (!s) return;

  // Clean up old charts
  if (ddToolChart) {{ ddToolChart.destroy(); ddToolChart = null; }}
  if (ddReplayChart) {{ ddReplayChart.destroy(); ddReplayChart = null; }}

  const mainView = document.getElementById('main-view');
  const ddView = document.getElementById('drilldown-view');
  const ddContent = document.getElementById('dd-content');

  mainView.style.display = 'none';
  ddView.style.display = 'block';

  // Build HTML
  const topWaste = s.top_waste || '';
  const twColor = WASTE_COLORS[topWaste] || '#64748b';
  const twLabel = WASTE_LABELS[topWaste] || topWaste;
  const wsCls = scoreClass(s.waste_score || 0);

  // KPI cards
  const kpiHTML = `
    <div class="dd-kpi-row">
      <div class="dd-kpi-card">
        <div class="kpi-label">Cost</div>
        <div class="kpi-value" style="color:var(--accent)">${{fmtCost(s.estimated_cost)}}</div>
      </div>
      <div class="dd-kpi-card">
        <div class="kpi-label">Duration</div>
        <div class="kpi-value">${{fmtDur(s.duration_minutes)}}</div>
      </div>
      <div class="dd-kpi-card">
        <div class="kpi-label">Cache Hit%</div>
        <div class="kpi-value">${{(s.cache_hit_rate_pct||0).toFixed(0)}}%</div>
      </div>
      <div class="dd-kpi-card">
        <div class="kpi-label">Total Tools</div>
        <div class="kpi-value">${{s.total_tools||0}}</div>
        <div class="kpi-sub" style="font-size:11px;color:var(--text-muted);margin-top:4px">p95: ${{THRESHOLDS.max_tool_p95||'—'}}</div>
      </div>
      <div class="dd-kpi-card">
        <div class="kpi-label">Waste Score</div>
        <div class="kpi-value"><span class="badge ${{wsCls}}">${{s.waste_score||0}}</span></div>
      </div>
    </div>`;

  // Waste findings
  const wasteScores = s.waste_scores || {{}};
  const wasteEvidence = s.waste_evidence || {{}};
  const findingCards = Object.entries(wasteScores)
    .filter(([cat, score]) => score > 0)
    .sort(([,a],[,b]) => b - a)
    .map(([cat, score]) => {{
      const color = WASTE_COLORS[cat] || '#64748b';
      const label = WASTE_LABELS[cat] || cat;
      const cls = scoreClass(score);
      const ev = wasteEvidence[cat] || {{}};
      const finding = ev.finding || buildDefaultFinding(cat, score, s);
      const rec = ev.recommendation || WASTE_FIXES[cat] || '';
      const fix = WASTE_FIXES[cat] || rec;
      return `
        <div class="finding-card">
          <div class="finding-header">
            <span class="finding-cat" style="color:${{color}}">${{label}}</span>
            <span class="badge ${{cls}}" style="background:${{color}}22;color:${{color}};border:1px solid ${{color}}44">${{score}}</span>
          </div>
          <div class="finding-text">${{finding}}</div>
          <div class="action-card">
            <div class="action-title">What to change</div>
            <div class="action-text">${{fix}}</div>
          </div>
        </div>`;
    }}).join('');

  const findingsHTML = `
    <div class="findings-section">
      <h3>Waste Findings</h3>
      ${{findingCards || '<p style="color:var(--text-muted);font-size:13px">No significant waste detected.</p>'}}
    </div>`;

  // Cache efficiency
  const cacheRatio = s.cache_reuse_ratio || 0;
  const medianRatio = THRESHOLDS.cache_ratio_median || 15.8;
  const p25Ratio = THRESHOLDS.cache_ratio_p25 || 9.5;
  const p10Ratio = THRESHOLDS.cache_ratio_p10 || 4.6;
  let ratioContext = '';
  if (cacheRatio < p10Ratio) ratioContext = `Below p10 (${{p10Ratio.toFixed(1)}}×) — very low cache reuse.`;
  else if (cacheRatio < p25Ratio) ratioContext = `Below p25 (${{p25Ratio.toFixed(1)}}×) — below average.`;
  else if (cacheRatio < medianRatio) ratioContext = `Below median (${{medianRatio.toFixed(1)}}×) — moderate reuse.`;
  else ratioContext = `At or above dataset median (${{medianRatio.toFixed(1)}}×) — good cache reuse.`;

  const hitPct = s.cache_hit_rate_pct || 0;
  const hitBarW = Math.min(hitPct, 100);
  const ratioBarW = Math.min((cacheRatio / (medianRatio * 2)) * 100, 100);
  const hitColor = hitPct >= 40 ? '#22c55e' : hitPct >= 20 ? '#f59e0b' : '#ef4444';
  const ratioColor = cacheRatio >= medianRatio ? '#22c55e' : cacheRatio >= p25Ratio ? '#f59e0b' : '#ef4444';

  const cacheHTML = `
    <div class="cache-card">
      <h3>Cache Efficiency</h3>
      <div class="cache-bar-row">
        <div class="cache-bar-label">Cache hit rate</div>
        <div class="cache-bar-track">
          <div class="cache-bar-fill" style="width:${{hitBarW}}%;background:${{hitColor}}"></div>
        </div>
        <div class="cache-bar-val">${{hitPct.toFixed(1)}}% ${{hitPct>=40?'✓':'↓'}}</div>
      </div>
      <div class="cache-bar-row">
        <div class="cache-bar-label">Reuse ratio</div>
        <div class="cache-bar-track">
          <div class="cache-bar-fill" style="width:${{ratioBarW}}%;background:${{ratioColor}}"></div>
        </div>
        <div class="cache-bar-val">${{cacheRatio.toFixed(1)}}×</div>
      </div>
      <div class="cache-ratio-row">
        <strong>${{cacheRatio.toFixed(1)}}×</strong> cache reuse ratio — ${{ratioContext}}
      </div>
    </div>`;

  // Tool usage chart placeholder + replay placeholder
  const chartsHTML = `
    <div class="dd-chart-row">
      <div class="dd-chart-card">
        <h3>Tool Usage (top 10)</h3>
        <div style="position:relative;height:260px">
          <canvas id="ddToolChart"></canvas>
        </div>
      </div>
      ${{s.replay ? `
      <div class="dd-chart-card">
        <h3>Turn-by-Turn Cost</h3>
        <div style="position:relative;height:260px">
          <canvas id="ddReplayChart"></canvas>
        </div>
      </div>` : '<div></div>'}}
    </div>`;

  ddContent.innerHTML = `
    <div class="dd-header">
      <div class="dd-title">
        <div style="font-family:monospace;font-size:16px">${{sid.substring(0,12)}}…</div>
        <div class="dd-project">${{s.project_name}}</div>
      </div>
      <div class="dd-cost">${{fmtCost(s.estimated_cost)}}</div>
    </div>
    ${{kpiHTML}}
    ${{findingsHTML}}
    ${{cacheHTML}}
    ${{chartsHTML}}
  `;

  // Render tool chart
  const toolBreakdown = s.tool_breakdown || {{}};
  const toolEntries = Object.entries(toolBreakdown).sort(([,a],[,b]) => b-a).slice(0,10);
  const p75 = THRESHOLDS.max_tool_p75 || 54;
  const p95 = THRESHOLDS.max_tool_p95 || 143;

  if (toolEntries.length > 0) {{
    const tCtx = document.getElementById('ddToolChart').getContext('2d');
    ddToolChart = new Chart(tCtx, {{
      type: 'bar',
      data: {{
        labels: toolEntries.map(([k]) => k),
        datasets: [{{
          label: 'Call count',
          data: toolEntries.map(([,v]) => v),
          backgroundColor: toolEntries.map(([,v]) => v > p95 ? '#ef444499' : v > p75 ? '#f59e0b99' : '#6366f199'),
          borderColor: toolEntries.map(([,v]) => v > p95 ? '#ef4444' : v > p75 ? '#f59e0b' : '#6366f1'),
          borderWidth: 1,
        }}]
      }},
      options: {{
        animation: false,
        indexAxis: 'y',
        responsive: true,
        maintainAspectRatio: false,
        plugins: {{
          legend: {{ display: false }},
          tooltip: {{
            callbacks: {{
              label: (item) => {{
                const v = item.raw;
                let suffix = '';
                if (v > p95) suffix = ` (above p95=${{p95}})`;
                else if (v > p75) suffix = ` (above p75=${{p75}})`;
                return `${{v}} calls${{suffix}}`;
              }}
            }}
          }}
        }},
        scales: {{
          x: {{ grid: {{ color: '#334155' }}, ticks: {{ color: '#94a3b8' }} }},
          y: {{ grid: {{ color: '#334155' }}, ticks: {{ color: '#94a3b8' }} }},
        }}
      }}
    }});
  }}

  // Replay chart
  if (s.replay && s.replay.turns && s.replay.turns.length > 0) {{
    const turns = s.replay.turns;
    const rCtx = document.getElementById('ddReplayChart').getContext('2d');
    ddReplayChart = new Chart(rCtx, {{
      type: 'bar',
      data: {{
        labels: turns.map((t, i) => `T${{i+1}}`),
        datasets: [{{
          label: 'Turn cost ($)',
          data: turns.map(t => t.cost || 0),
          backgroundColor: '#6366f199',
          borderColor: '#6366f1',
          borderWidth: 1,
        }}]
      }},
      options: {{
        animation: false,
        responsive: true,
        maintainAspectRatio: false,
        plugins: {{
          legend: {{ display: false }},
          tooltip: {{
            callbacks: {{
              label: (item) => {{
                const t = turns[item.dataIndex];
                const lines = [`Cost: ${{fmtCost(item.raw)}}`];
                if (t && t.tools) lines.push(`Tool calls: ${{t.tools}}`);
                return lines;
              }}
            }}
          }}
        }},
        scales: {{
          x: {{ grid: {{ color: '#334155' }}, ticks: {{ color: '#94a3b8' }} }},
          y: {{ grid: {{ color: '#334155' }}, ticks: {{ color: '#94a3b8', callback: v => '$'+v.toFixed(3) }} }},
        }}
      }}
    }});
  }}

  window.scrollTo(0, 0);
}}

function buildDefaultFinding(cat, score, s) {{
  const tools = s.total_tools || 0;
  const p95 = THRESHOLDS.max_tool_p95 || 143;
  const p75 = THRESHOLDS.max_tool_p75 || 54;
  const medRatio = THRESHOLDS.cache_ratio_median || 15.8;
  switch(cat) {{
    case 'tool_hammering': {{
      const top = Object.entries(s.tool_breakdown||{{}}).sort(([,a],[,b])=>b-a)[0];
      const topStr = top ? `${{top[0]}} called ${{top[1]}}×` : `${{tools}} total tool calls`;
      let pctile = '';
      if (tools > p95) pctile = `dataset p95 is ${{p95}}, you are in the top 5%`;
      else if (tools > p75) pctile = `dataset p75 is ${{p75}}, you are above average`;
      return `${{topStr}} in this session. ${{pctile ? 'Compared to dataset: '+pctile+'.' : ''}} High tool call frequency suggests repetitive operations that could be batched.`;
    }}
    case 'cache_inefficiency': {{
      const ratio = s.cache_reuse_ratio || 0;
      return `Cache reuse ratio is ${{ratio.toFixed(1)}}× — dataset median is ${{medRatio.toFixed(1)}}×. Cache hit rate: ${{(s.cache_hit_rate_pct||0).toFixed(1)}}%. Low cache reuse inflates token costs significantly.`;
    }}
    case 'context_bloat': {{
      const dur = s.duration_minutes || 0;
      return `Session ran for ${{fmtDur(dur)}} without compaction. Long sessions accumulate large context windows, increasing per-turn cost. Score: ${{score}}/100.`;
    }}
    case 'compaction_absence': {{
      const dur = s.duration_minutes || 0;
      return `Session lasted ${{fmtDur(dur)}} with no detected compaction events. Sessions over 45 min benefit significantly from /compact to reduce context overhead.`;
    }}
    case 'parallel_sprawl': {{
      return `Parallel session activity detected. Multiple simultaneous sessions on the same project waste cache warming and increase total token spend. Score: ${{score}}/100.`;
    }}
    case 'interruption_loops': {{
      return `High interruption/clarification pattern detected. Frequent back-and-forth increases total turns and cost. Clearer upfront prompts would reduce this. Score: ${{score}}/100.`;
    }}
    case 'thinking_waste': {{
      return `Extended thinking tokens detected in routine operations. Thinking mode should be reserved for complex reasoning tasks, not standard file edits or searches. Score: ${{score}}/100.`;
    }}
    default:
      return `Waste category score: ${{score}}/100.`;
  }}
}}

function closeDrilldown() {{
  if (ddToolChart) {{ ddToolChart.destroy(); ddToolChart = null; }}
  if (ddReplayChart) {{ ddReplayChart.destroy(); ddReplayChart = null; }}
  document.getElementById('drilldown-view').style.display = 'none';
  document.getElementById('main-view').style.display = 'block';
  document.getElementById('dd-content').innerHTML = '';
}}
</script>
</body>
</html>"""

    return html


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="cc-lens dashboard generator")
    parser.add_argument("--spec", required=True, help="Path to JSON spec file (default: /tmp/cc-lens-spec.json)")
    parser.add_argument("--output", required=True, help="Output HTML path (default: /tmp/cc-lens-report.html)")
    args = parser.parse_args()

    try:
        with open(args.spec, "r", encoding="utf-8") as f:
            spec = json.load(f)
    except FileNotFoundError:
        print(f"Error: spec file not found: {args.spec}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: invalid JSON in spec file: {e}", file=sys.stderr)
        sys.exit(1)

    html = generate_html(spec)

    with open(args.output, "w", encoding="utf-8") as f:
        f.write(html)

    sessions_count = len(spec.get("sessions", []))
    projects_count = len(spec.get("projects", []))
    total_cost = spec.get("summary", {}).get("total_cost", 0)
    print(f"Dashboard written to: {args.output}")
    print(f"  Sessions: {sessions_count}  Projects: {projects_count}  Total cost: ${total_cost:,.2f}")


if __name__ == "__main__":
    main()
