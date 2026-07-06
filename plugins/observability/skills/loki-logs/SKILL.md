---
name: loki-logs
description: Query Loki for recent errors, agent activity logs, and heartbeat runs. Covers LogQL syntax, useful queries for Paperclip operations, and how to filter by agent, run ID, or time window.
license: MIT
compatibility: claude-code
metadata:
  audience: developers, operators
  workflow: observability
---

## What I do

I help you query Loki to inspect live and historical logs from the Paperclip stack. I provide ready-to-run LogQL queries for the most common operational scenarios: recent errors, agent heartbeat activity, run traces, and slow paths.

## When to use me

Load when you need to:
- Investigate a failed agent run or stuck heartbeat
- Find recent errors across agents
- Trace activity for a specific run ID
- Understand agent behavior over a time window

---

## Environment Variables Required

| Variable | Default | Description |
|----------|---------|-------------|
| `LOKI_URL` | `http://localhost:3100` | Loki HTTP endpoint |
| `LOKI_USER` | _(empty)_ | Basic auth user (if auth enabled) |
| `LOKI_PASSWORD` | _(empty)_ | Basic auth password (if auth enabled) |

---

## Loki API — Quick Reference

**Base URL:** `$LOKI_URL`

```bash
# Query logs (GET /loki/api/v1/query_range)
curl -s "$LOKI_URL/loki/api/v1/query_range" \
  --data-urlencode 'query={app="paperclip"}' \
  --data-urlencode "start=$(date -d '1 hour ago' +%s)000000000" \
  --data-urlencode "end=$(date +%s)000000000" \
  --data-urlencode 'limit=100' \
  | jq '.data.result[].values[][1]'

# Instant query (latest matching line)
curl -s "$LOKI_URL/loki/api/v1/query" \
  --data-urlencode 'query={app="paperclip"} |= "error"' \
  | jq '.data.result[].values[][1]'

# Labels available
curl -s "$LOKI_URL/loki/api/v1/labels" | jq '.data[]'
```

---

## Common Queries

### Recent errors (last 1 hour)
```logql
{app="paperclip"} |= "error" | json | line_format "{{.level}} {{.msg}}"
```

### Errors by severity (last 30 min)
```logql
{app="paperclip"} | json | level =~ "error|fatal" | line_format "{{.ts}} {{.level}} {{.msg}}"
```

### Agent heartbeat activity
```logql
{app="paperclip"} | json | msg =~ "heartbeat.*" | line_format "{{.ts}} {{.agentId}} {{.msg}}"
```

### Activity for a specific run ID
```logql
{app="paperclip"} | json | runId = "<RUN_ID>"
```

### Agent-specific logs
```logql
{app="paperclip"} | json | agentId = "<AGENT_ID>"
```

### Slow heartbeats (duration > 10s)
```logql
{app="paperclip"} | json | msg = "heartbeat_complete" | durationMs > 10000
```

### Failed checkouts
```logql
{app="paperclip"} | json | msg =~ "checkout.*fail|409"
```

### API request errors (5xx)
```logql
{app="paperclip"} | json | statusCode >= 500
```

---

## How to Run Queries

**Via curl (simple):**
```bash
LOKI_URL=${LOKI_URL:-http://localhost:3100}
START=$(date -d '1 hour ago' +%s)000000000
END=$(date +%s)000000000

curl -s "$LOKI_URL/loki/api/v1/query_range" \
  -G \
  --data-urlencode 'query={app="paperclip"} |= "error"' \
  --data-urlencode "start=$START" \
  --data-urlencode "end=$END" \
  --data-urlencode 'limit=200' \
  | jq -r '.data.result[].values[][1]' \
  | jq -r '"\(.ts) [\(.level)] \(.msg)"' 2>/dev/null || true
```

**Via Grafana Explore:** Navigate to `$GRAFANA_URL` → Explore → Select Loki datasource → paste the LogQL query.

---

## Interpreting Results

| Pattern | What it means |
|---------|--------------|
| `checkout conflict 409` repeated | Two agents racing for the same task — check assignment logic |
| `heartbeat_timeout` | Agent run exceeded time limit — check for stuck operations |
| `budget_exceeded` | Agent hit monthly budget cap — escalate to board |
| High rate of `5xx` on `/api/issues` | API instability — check Prometheus for error rate spike |
| No logs for agent in > 30 min | Agent may be paused or waiting — check Paperclip inbox |

---

## Useful Time Helpers

```bash
# Last 15 minutes
START=$(date -d '15 minutes ago' +%s)000000000

# Last 1 hour
START=$(date -d '1 hour ago' +%s)000000000

# Last 24 hours
START=$(date -d '24 hours ago' +%s)000000000

# macOS equivalent
START=$(date -v-1H +%s)000000000
```
