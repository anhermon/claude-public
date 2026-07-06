---
name: grafana-dashboards
description: Navigate and query Grafana dashboards for the Paperclip observability stack. Covers dashboard URLs, API access, panel queries, and how to extract data programmatically from Grafana.
license: MIT
compatibility: claude-code
metadata:
  audience: developers, operators
  workflow: observability
---

## What I do

I help you navigate Grafana to access dashboards for the Paperclip observability stack and query dashboard data programmatically via the Grafana HTTP API. I cover dashboard discovery, panel queries, and how to pull snapshots of key metrics without opening a browser.

## When to use me

Load when you need to:
- Find and access a specific dashboard
- Get a high-level health summary from the board's perspective
- Query Grafana API to extract panel data programmatically
- Share a dashboard link with a specific time range pre-selected

---

## Environment Variables Required

| Variable | Default | Description |
|----------|---------|-------------|
| `GRAFANA_URL` | `http://localhost:3000` | Grafana base URL |
| `GRAFANA_USER` | `admin` | Grafana username |
| `GRAFANA_PASSWORD` | `admin` | Grafana password |

---

## Grafana API — Quick Reference

```bash
GF=${GRAFANA_URL:-http://localhost:3000}
GF_USER=${GRAFANA_USER:-admin}
GF_PASS=${GRAFANA_PASSWORD:-admin}
AUTH="$GF_USER:$GF_PASS"

# Health check
curl -s "$GF/api/health" | jq '.'

# List all dashboards
curl -s -u "$AUTH" "$GF/api/search?type=dash-db" \
  | jq '.[] | {uid: .uid, title: .title, url: .url}'

# Get dashboard by UID
curl -s -u "$AUTH" "$GF/api/dashboards/uid/<DASHBOARD_UID>" \
  | jq '.dashboard | {title: .title, panels: [.panels[].title]}'

# List datasources
curl -s -u "$AUTH" "$GF/api/datasources" \
  | jq '.[] | {id: .id, name: .name, type: .type, url: .url}'

# Query a datasource directly via Grafana proxy
curl -s -u "$AUTH" -X POST "$GF/api/ds/query" \
  -H "Content-Type: application/json" \
  -d '{
    "queries": [{
      "datasourceId": 1,
      "expr": "up",
      "queryType": "range",
      "range": true
    }],
    "from": "now-1h",
    "to": "now"
  }' | jq '.'
```

---

## Key Dashboards

These dashboards should be available after the observability stack is deployed:

| Dashboard | UID / Path | What it shows |
|-----------|-----------|---------------|
| **Paperclip Overview** | `paperclip-overview` | Agent heartbeat rates, error rates, active runs |
| **Agent Performance** | `paperclip-agents` | Per-agent token usage, run duration, budget utilization |
| **API Health** | `paperclip-api` | Request rate, latency p50/p95/p99, error rate |
| **Infrastructure** | `paperclip-infra` | Container CPU/memory, disk I/O, network |
| **Loki Logs** | _(Explore)_ | Live log tail, error filtering |

To get the actual UIDs after deployment:
```bash
GF=${GRAFANA_URL:-http://localhost:3000}
curl -s -u "${GRAFANA_USER:-admin}:${GRAFANA_PASSWORD:-admin}" \
  "$GF/api/search?type=dash-db" \
  | jq -r '.[] | "\(.uid)\t\(.title)"'
```

---

## Direct Dashboard Links

Construct time-ranged dashboard links for sharing:

```
# Last 1 hour
${GRAFANA_URL}/d/<DASHBOARD_UID>/<DASHBOARD_SLUG>?orgId=1&from=now-1h&to=now

# Last 24 hours
${GRAFANA_URL}/d/<DASHBOARD_UID>/<DASHBOARD_SLUG>?orgId=1&from=now-24h&to=now

# Specific run time window (epoch ms)
${GRAFANA_URL}/d/<DASHBOARD_UID>/<DASHBOARD_SLUG>?orgId=1&from=<start_ms>&to=<end_ms>

# With agent filter variable
${GRAFANA_URL}/d/<DASHBOARD_UID>/<DASHBOARD_SLUG>?orgId=1&from=now-1h&to=now&var-agent_id=<AGENT_ID>
```

---

## Programmatic Panel Data Extraction

To pull data from a specific panel without opening Grafana:

```bash
GF=${GRAFANA_URL:-http://localhost:3000}
AUTH="${GRAFANA_USER:-admin}:${GRAFANA_PASSWORD:-admin}"
DASHBOARD_UID="paperclip-overview"

# Step 1: get panel IDs
curl -s -u "$AUTH" "$GF/api/dashboards/uid/$DASHBOARD_UID" \
  | jq '.dashboard.panels[] | {id: .id, title: .title, type: .type}'

# Step 2: render panel as PNG (useful for reporting)
curl -s -u "$AUTH" \
  "$GF/render/d-solo/$DASHBOARD_UID/paperclip-overview?orgId=1&panelId=<PANEL_ID>&width=800&height=400&from=now-1h&to=now" \
  --output panel.png

echo "Panel saved to panel.png"
```

---

## Organization Health Summary Script

Run this to get a quick health overview from the board's perspective:

```bash
#!/bin/bash
GF=${GRAFANA_URL:-http://localhost:3000}
PROM=${PROMETHEUS_URL:-http://localhost:9090}
AUTH="${GRAFANA_USER:-admin}:${GRAFANA_PASSWORD:-admin}"

echo "=== Grafana Health ==="
curl -s "$GF/api/health" | jq -r '"Status: \(.database)"'

echo ""
echo "=== Datasource Status ==="
curl -s -u "$AUTH" "$GF/api/datasources" \
  | jq -r '.[] | "\(.name) (\(.type)): \(.url)"'

echo ""
echo "=== Available Dashboards ==="
curl -s -u "$AUTH" "$GF/api/search?type=dash-db" \
  | jq -r '.[] | "[\(.uid)] \(.title) — \(.url)"'

echo ""
echo "=== Alert Status ==="
curl -s -u "$AUTH" "$GF/api/alerts?state=alerting" \
  | jq -r 'if length == 0 then "No active alerts" else .[] | "ALERT: \(.name) [\(.state)]" end'
```

---

## Alerting

List active alerts programmatically:

```bash
GF=${GRAFANA_URL:-http://localhost:3000}
AUTH="${GRAFANA_USER:-admin}:${GRAFANA_PASSWORD:-admin}"

# Grafana Alerting (unified alerts — Grafana 8+)
curl -s -u "$AUTH" "$GF/api/alertmanager/grafana/api/v2/alerts" \
  | jq '.[] | {labels: .labels, state: .status.state, starts: .startsAt}'

# Legacy alerts (Grafana 7 and below)
curl -s -u "$AUTH" "$GF/api/alerts?state=alerting" \
  | jq '.[] | {id: .id, name: .name, state: .state}'
```
