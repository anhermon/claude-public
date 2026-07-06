---
name: error-patterns
description: Aggregate and analyze error patterns across agents — identify recurring failures, classify error types, correlate with agent activity, and produce actionable summaries from Loki + Prometheus data.
license: MIT
compatibility: claude-code
metadata:
  audience: developers, operators
  workflow: observability
---

## What I do

I help you aggregate errors across all agents and identify patterns: which errors repeat, which agents produce the most failures, what sequences lead to incidents, and which are actionable vs. noise. I combine Loki log queries and Prometheus metrics to produce a consolidated error report.

## When to use me

Load when you need to:
- Get a cross-agent error summary (not just one agent)
- Identify the top recurring failure types
- Find which agent runs are failing and why
- Prepare an incident report or self-improvement issue

---

## Environment Variables Required

| Variable | Default | Description |
|----------|---------|-------------|
| `LOKI_URL` | `http://localhost:3100` | Loki endpoint |
| `PROMETHEUS_URL` | `http://localhost:9090` | Prometheus endpoint |

---

## Error Summary Workflow

Run these steps in sequence to build a full error picture:

### Step 1 — Count errors by type (Prometheus)

```bash
PROM=${PROMETHEUS_URL:-http://localhost:9090}

echo "=== Error rate by HTTP path (last 1h) ==="
curl -s "$PROM/api/v1/query" \
  --data-urlencode 'query=topk(10, sum(rate(http_requests_total{status_code=~"5.."}[1h])) by (path))' \
  | jq -r '.data.result[] | "\(.metric.path): \(.value[1] | tonumber | . * 100 | round / 100)/s"'

echo ""
echo "=== Heartbeat failures by agent (last 1h) ==="
curl -s "$PROM/api/v1/query" \
  --data-urlencode 'query=sort_desc(sum(rate(paperclip_heartbeat_total{status="failed"}[1h])) by (agent_id))' \
  | jq -r '.data.result[] | "\(.metric.agent_id): \(.value[1])"'
```

### Step 2 — Sample error log lines (Loki)

```bash
LOKI=${LOKI_URL:-http://localhost:3100}
START=$(date -d '1 hour ago' +%s)000000000
END=$(date +%s)000000000

echo "=== Recent error log lines ==="
curl -s "$LOKI/loki/api/v1/query_range" \
  -G \
  --data-urlencode 'query={app="paperclip"} | json | level =~ "error|fatal"' \
  --data-urlencode "start=$START" \
  --data-urlencode "end=$END" \
  --data-urlencode 'limit=200' \
  | jq -r '.data.result[].values[][1]' \
  | jq -r '"\(.ts // "?") [\(.level // "?")] \(.agentId // "?") — \(.msg // .message // "?")"' 2>/dev/null \
  | sort | uniq -c | sort -rn | head -30
```

### Step 3 — Identify top recurring error messages

```bash
LOKI=${LOKI_URL:-http://localhost:3100}
START=$(date -d '6 hours ago' +%s)000000000
END=$(date +%s)000000000

echo "=== Top recurring error messages (last 6h) ==="
curl -s "$LOKI/loki/api/v1/query_range" \
  -G \
  --data-urlencode 'query={app="paperclip"} | json | level = "error"' \
  --data-urlencode "start=$START" \
  --data-urlencode "end=$END" \
  --data-urlencode 'limit=1000' \
  | jq -r '.data.result[].values[][1]' \
  | jq -r '.msg // .message // empty' 2>/dev/null \
  | sort | uniq -c | sort -rn | head -20
```

### Step 4 — Find failing agent runs

```bash
LOKI=${LOKI_URL:-http://localhost:3100}
START=$(date -d '24 hours ago' +%s)000000000
END=$(date +%s)000000000

echo "=== Failed run IDs (last 24h) ==="
curl -s "$LOKI/loki/api/v1/query_range" \
  -G \
  --data-urlencode 'query={app="paperclip"} | json | msg = "heartbeat_failed"' \
  --data-urlencode "start=$START" \
  --data-urlencode "end=$END" \
  --data-urlencode 'limit=100' \
  | jq -r '.data.result[].values[][1]' \
  | jq -r '{runId: .runId, agentId: .agentId, error: .error}' 2>/dev/null
```

---

## Full Error Report Script

Run this for a consolidated operational report:

```bash
#!/bin/bash
set -e

LOKI=${LOKI_URL:-http://localhost:3100}
PROM=${PROMETHEUS_URL:-http://localhost:9090}
WINDOW=${1:-1h}  # default: last 1 hour

START=$(date -d "$WINDOW ago" +%s)000000000
END=$(date +%s)000000000
PROM_START=$(date -d "$WINDOW ago" +%s)
PROM_END=$(date +%s)

echo "=========================================="
echo "  Paperclip Error Report — Last $WINDOW"
echo "  $(date -u)"
echo "=========================================="

echo ""
echo "--- 1. API Error Rate ---"
curl -s "$PROM/api/v1/query" \
  --data-urlencode "query=sum(rate(http_requests_total{status_code=~\"5..\"}[${WINDOW}]))" \
  | jq -r '"5xx rate: \(.data.result[0].value[1] // "0")/s"'

echo ""
echo "--- 2. Heartbeat Failures ---"
curl -s "$PROM/api/v1/query" \
  --data-urlencode "query=sum(increase(paperclip_heartbeat_total{status=\"failed\"}[${WINDOW}])) by (agent_id)" \
  | jq -r '.data.result[] | "\(.metric.agent_id): \(.value[1]) failures"' \
  | sort -t: -k2 -rn | head -10

echo ""
echo "--- 3. Top Error Messages ---"
curl -s "$LOKI/loki/api/v1/query_range" \
  -G \
  --data-urlencode 'query={app="paperclip"} | json | level = "error"' \
  --data-urlencode "start=$START" \
  --data-urlencode "end=$END" \
  --data-urlencode 'limit=500' \
  | jq -r '.data.result[].values[][1]' \
  | jq -r '.msg // .message // empty' 2>/dev/null \
  | sort | uniq -c | sort -rn | head -15

echo ""
echo "--- 4. Budget Status ---"
curl -s "$PROM/api/v1/query" \
  --data-urlencode 'query=(paperclip_budget_used_cents / paperclip_budget_limit_cents) * 100' \
  | jq -r '.data.result[] | "\(.metric.agent_id): \(.value[1] | tonumber | floor)% used"' \
  | sort -t: -k2 -rn | head -10

echo ""
echo "=========================================="
echo "  Report complete"
echo "=========================================="
```

---

## Error Classification

When reviewing errors, classify each into one of these categories:

| Category | Examples | Action |
|----------|---------|--------|
| **Transient** | Network timeout, rate limit 429 | Monitor frequency; alert if persistent |
| **Configuration** | Wrong endpoint, missing env var | Fix config, create issue |
| **Conflict** | 409 checkout conflict, race condition | Check assignment logic |
| **Budget** | Budget exceeded, paused | Escalate to board |
| **Logic Bug** | Unhandled exception, null dereference | Create bug issue with trace ID |
| **External Dependency** | GitHub API down, DB connection refused | Track upstream; add retry/fallback |
| **Intentional** | Blocked task skip, permission denied | Verify this is expected behavior |

---

## Creating Follow-Up Issues

When you identify an actionable error pattern, create a Paperclip issue using the standard format:

```markdown
## Objective
Fix recurring error: "<error message>" seen N times in last 24h across agents X, Y, Z.

## Scope
**Touch:** [component where the error originates]
**Do not touch:** [unrelated systems]

## Verification
- [ ] Error no longer appears in Loki logs after fix
- [ ] Prometheus error rate drops to baseline
```

Use the `paperclip` skill to post the issue: `POST /api/companies/{companyId}/issues`.
