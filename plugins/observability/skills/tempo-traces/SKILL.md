---
name: tempo-traces
description: Query Tempo/Jaeger for distributed traces. Covers trace lookup by run ID, span analysis, latency breakdown, and how to correlate traces with Loki logs and Prometheus metrics.
license: MIT
compatibility: claude-code
metadata:
  audience: developers, operators
  workflow: observability
---

## What I do

I help you search and analyze distributed traces stored in Tempo. I cover trace lookup by Paperclip run ID, span analysis to find slow operations, and correlating traces with logs and metrics for root cause analysis.

## When to use me

Load when you need to:
- Trace exactly what happened during a specific heartbeat run
- Find slow spans and latency breakdowns
- Correlate a trace with its Loki logs
- Understand the call chain for a failed operation

---

## Environment Variables Required

| Variable | Default | Description |
|----------|---------|-------------|
| `TEMPO_URL` | `http://localhost:3200` | Tempo HTTP endpoint |
| `GRAFANA_URL` | `http://localhost:3000` | Grafana URL (for trace UI links) |

---

## Tempo API — Quick Reference

**Base URL:** `$TEMPO_URL`

Tempo supports the **Tempo HTTP API** and is also compatible with the **Jaeger HTTP API** for trace search.

```bash
TEMPO=${TEMPO_URL:-http://localhost:3200}

# Search traces (by tags, duration, time range)
curl -s "$TEMPO/api/search" \
  --data-urlencode 'q={resource.service.name="paperclip"}' \
  --data-urlencode "start=$(date -d '1 hour ago' +%s)" \
  --data-urlencode "end=$(date +%s)" \
  --data-urlencode 'limit=20' \
  | jq '.traces[] | {traceID: .traceID, rootName: .rootName, duration: .durationMs}'

# Get specific trace by ID
curl -s "$TEMPO/api/traces/<TRACE_ID>" | jq '.batches[].scopeSpans[].spans[] | {name: .name, duration: (.endTimeUnixNano - .startTimeUnixNano) / 1000000}'

# Check if Tempo is up
curl -s "$TEMPO/ready"

# List tags (for filtering)
curl -s "$TEMPO/api/search/tags" | jq '.tagNames[]'
```

---

## Search by Run ID

Paperclip injects `run.id` as an OTEL attribute on all spans for a heartbeat run.

```bash
TEMPO=${TEMPO_URL:-http://localhost:3200}
RUN_ID="<your-run-id>"

# Find traces by run ID
curl -s "$TEMPO/api/search" \
  -G \
  --data-urlencode "q={run.id=\"$RUN_ID\"}" \
  | jq '.traces[] | {traceID: .traceID, rootName: .rootName, durationMs: .durationMs}'
```

Once you have the `traceID`, fetch the full trace:

```bash
TRACE_ID="<trace-id>"
curl -s "$TEMPO/api/traces/$TRACE_ID" \
  | jq '.batches[].scopeSpans[].spans[] | {
      spanId: .spanId,
      name: .name,
      durationMs: ((.endTimeUnixNano - .startTimeUnixNano) / 1000000),
      status: .status
    }' \
  | sort_by(.durationMs) | reverse
```

---

## Common Searches

### All traces in the last 30 minutes
```bash
TEMPO=${TEMPO_URL:-http://localhost:3200}
curl -s "$TEMPO/api/search" \
  -G \
  --data-urlencode 'q={resource.service.name="paperclip"}' \
  --data-urlencode "start=$(date -d '30 minutes ago' +%s)" \
  --data-urlencode "end=$(date +%s)" \
  | jq '.traces[]'
```

### Traces for a specific agent
```bash
curl -s "$TEMPO/api/search" \
  -G \
  --data-urlencode 'q={agent.id="<AGENT_ID>"}' \
  --data-urlencode "start=$(date -d '1 hour ago' +%s)" \
  --data-urlencode "end=$(date +%s)" \
  | jq '.traces[]'
```

### Slow traces (> 5 seconds)
```bash
curl -s "$TEMPO/api/search" \
  -G \
  --data-urlencode 'q={resource.service.name="paperclip"} && duration > 5s' \
  --data-urlencode "start=$(date -d '1 hour ago' +%s)" \
  --data-urlencode "end=$(date +%s)" \
  | jq '.traces[] | {traceID: .traceID, durationMs: .durationMs, rootName: .rootName}'
```

### Failed traces (error spans)
```bash
curl -s "$TEMPO/api/search" \
  -G \
  --data-urlencode 'q={status=error}' \
  --data-urlencode "start=$(date -d '1 hour ago' +%s)" \
  --data-urlencode "end=$(date +%s)" \
  | jq '.traces[]'
```

---

## Span Analysis

After retrieving a trace, analyze spans to find bottlenecks:

```bash
TEMPO=${TEMPO_URL:-http://localhost:3200}
TRACE_ID="<trace-id>"

# Top 10 slowest spans
curl -s "$TEMPO/api/traces/$TRACE_ID" \
  | jq '[.batches[].scopeSpans[].spans[] | {
      name: .name,
      durationMs: ((.endTimeUnixNano - .startTimeUnixNano) / 1000000)
    }] | sort_by(.durationMs) | reverse | .[0:10]'

# Error spans only
curl -s "$TEMPO/api/traces/$TRACE_ID" \
  | jq '.batches[].scopeSpans[].spans[] | select(.status.code == 2) | {name: .name, message: .status.message}'
```

---

## Trace → Log Correlation

Tempo traces include `trace_id` which maps to Loki log lines (if the app emits structured logs with trace context):

```bash
TRACE_ID="<trace-id>"
LOKI=${LOKI_URL:-http://localhost:3100}
START=$(date -d '2 hours ago' +%s)000000000
END=$(date +%s)000000000

# Find logs for this trace
curl -s "$LOKI/loki/api/v1/query_range" \
  -G \
  --data-urlencode "query={app=\"paperclip\"} | json | traceId = \"$TRACE_ID\"" \
  --data-urlencode "start=$START" \
  --data-urlencode "end=$END" \
  | jq -r '.data.result[].values[][1]' | jq '.'
```

---

## Grafana Trace UI

To view a trace in the Grafana UI:

```
${GRAFANA_URL:-http://localhost:3000}/explore?orgId=1&left={"datasource":"Tempo","queries":[{"query":"<TRACE_ID>"}],"range":{"from":"now-1h","to":"now"}}
```

Or navigate to Grafana → Explore → Select Tempo datasource → paste trace ID.

---

## What to Look For

| Pattern | What it means |
|---------|--------------|
| Root span duration >> child spans | Overhead outside tracked spans — likely I/O or queue wait |
| Many small spans with same name | Tight loop or N+1 pattern |
| Error status on DB/HTTP spans | Downstream failure — check service health |
| Gap between parent end and child start | Scheduling delay or GC pause |
| Missing run spans | OTel instrumentation not capturing heartbeat entry point |
