---
name: prometheus-metrics
description: Query Prometheus for token usage, heartbeat rates, API latency, and error rates across the Paperclip stack. Covers PromQL queries, metric names, and alert thresholds.
license: MIT
compatibility: claude-code
metadata:
  audience: developers, operators
  workflow: observability
---

## What I do

I help you query Prometheus metrics from the Paperclip stack. I provide ready-to-run PromQL queries for the most actionable operational views: token usage trends, heartbeat success rates, API latency percentiles, and error rates.

## When to use me

Load when you need to:
- Check token/cost burn rate per agent
- Measure heartbeat success/failure rates
- Identify slow API endpoints
- Detect error rate spikes
- Understand system performance over time

---

## Environment Variables Required

| Variable | Default | Description |
|----------|---------|-------------|
| `PROMETHEUS_URL` | `http://localhost:9090` | Prometheus HTTP endpoint |

---

## Prometheus API — Quick Reference

**Base URL:** `$PROMETHEUS_URL`

```bash
PROM=${PROMETHEUS_URL:-http://localhost:9090}

# Instant query
curl -s "$PROM/api/v1/query" \
  --data-urlencode 'query=up' \
  | jq '.data.result[]'

# Range query (last 1 hour, 1-minute resolution)
curl -s "$PROM/api/v1/query_range" \
  --data-urlencode 'query=up' \
  --data-urlencode "start=$(date -d '1 hour ago' +%s)" \
  --data-urlencode "end=$(date +%s)" \
  --data-urlencode 'step=60' \
  | jq '.data.result[]'

# List all available metrics
curl -s "$PROM/api/v1/label/__name__/values" | jq '.data[]'

# Check targets / scrape health
curl -s "$PROM/api/v1/targets" | jq '.data.activeTargets[] | {job: .labels.job, health: .health, lastError: .lastError}'
```

---

## Key Metrics

### Agent & Heartbeat Metrics

| Metric | Description |
|--------|-------------|
| `paperclip_heartbeat_total` | Total heartbeats, labeled by `agent_id`, `status` |
| `paperclip_heartbeat_duration_seconds` | Heartbeat duration histogram |
| `paperclip_run_active` | Currently active runs (gauge) |
| `paperclip_run_total` | Total completed runs, by `status` |
| `paperclip_budget_used_cents` | Monthly budget consumed per agent |
| `paperclip_budget_limit_cents` | Monthly budget limit per agent |

### API Metrics

| Metric | Description |
|--------|-------------|
| `http_requests_total` | Request count by `method`, `path`, `status_code` |
| `http_request_duration_seconds` | Latency histogram by `method`, `path` |
| `http_requests_in_flight` | Current in-flight requests |

### Token / Cost Metrics

| Metric | Description |
|--------|-------------|
| `paperclip_tokens_input_total` | Input tokens consumed, by `agent_id`, `model` |
| `paperclip_tokens_output_total` | Output tokens consumed, by `agent_id`, `model` |
| `paperclip_cost_usd_total` | Estimated cost in USD, by `agent_id` |

---

## Common Queries

### Heartbeat success rate (last 1 hour)
```promql
sum(rate(paperclip_heartbeat_total{status="success"}[1h])) /
sum(rate(paperclip_heartbeat_total[1h]))
```

### Heartbeat failure rate by agent
```promql
rate(paperclip_heartbeat_total{status="failed"}[30m]) > 0
```

### 95th percentile heartbeat duration
```promql
histogram_quantile(0.95, rate(paperclip_heartbeat_duration_seconds_bucket[1h]))
```

### API error rate (5xx, last 15 min)
```promql
sum(rate(http_requests_total{status_code=~"5.."}[15m])) by (path)
```

### API latency p99 by endpoint
```promql
histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket[5m])) by (le, path))
```

### Token consumption rate by agent (last 1 hour)
```promql
sum(rate(paperclip_tokens_input_total[1h])) by (agent_id)
```

### Budget utilization per agent (%)
```promql
(paperclip_budget_used_cents / paperclip_budget_limit_cents) * 100
```

### Active runs (snapshot)
```promql
paperclip_run_active
```

### Currently running agents
```promql
count(paperclip_run_active > 0) by (agent_id)
```

---

## How to Run Queries

```bash
PROM=${PROMETHEUS_URL:-http://localhost:9090}

# Run an instant query and show results
query() {
  curl -s "$PROM/api/v1/query" \
    --data-urlencode "query=$1" \
    | jq -r '.data.result[] | "\(.metric | to_entries | map("\(.key)=\(.value)") | join(" ")) => \(.value[1])"'
}

# Example: heartbeat success rate
query 'sum(rate(paperclip_heartbeat_total{status="success"}[1h])) / sum(rate(paperclip_heartbeat_total[1h]))'

# Example: agents consuming the most tokens
query 'topk(5, sum(rate(paperclip_tokens_input_total[1h])) by (agent_id))'
```

---

## Alert Thresholds (Reference)

| Condition | Threshold | Action |
|-----------|-----------|--------|
| Heartbeat failure rate | > 20% over 15m | Investigate stuck agents |
| API error rate | > 5% over 5m | Check logs, escalate to on-call |
| API latency p99 | > 2s over 10m | Profile slow endpoints |
| Budget utilization | > 80% | Pause non-critical agents |
| Active runs stalled | Same run active > 30m | Kill and re-trigger |

---

## Scrape Health Check

```bash
PROM=${PROMETHEUS_URL:-http://localhost:9090}
curl -s "$PROM/api/v1/targets" \
  | jq -r '.data.activeTargets[] | "\(.labels.job) [\(.health)] - \(.lastScrape)"'
```

If any target shows `health: "down"`, the metrics for that service are stale. Check the scrape config and service health.
