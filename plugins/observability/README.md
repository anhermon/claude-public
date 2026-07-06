# observability plugin

Practical skills for inspecting the Paperclip observability stack — Loki logs, Prometheus metrics, Tempo traces, Grafana dashboards, and cross-agent error analysis.

## Skills

| Skill | Trigger / Use When |
|-------|--------------------|
| `loki-logs` | Querying logs, finding errors, tracing agent activity by run ID |
| `prometheus-metrics` | Token usage, heartbeat rates, API latency, budget utilization |
| `tempo-traces` | Distributed trace lookup by run ID, span analysis, slow path detection |
| `grafana-dashboards` | Dashboard navigation, health summary, programmatic panel queries |
| `error-patterns` | Cross-agent error aggregation, recurring failure analysis, incident prep |

## Stack Endpoints

Configure via environment variables (or your `.env` file):

| Variable | Default | Service |
|----------|---------|---------|
| `LOKI_URL` | `http://localhost:3100` | Loki log aggregation |
| `PROMETHEUS_URL` | `http://localhost:9090` | Prometheus metrics |
| `TEMPO_URL` | `http://localhost:3200` | Tempo distributed traces |
| `GRAFANA_URL` | `http://localhost:3000` | Grafana dashboards |
| `GRAFANA_USER` | `admin` | Grafana auth user |
| `GRAFANA_PASSWORD` | `admin` | Grafana auth password |
| `LOKI_USER` | _(empty)_ | Loki auth user (if enabled) |
| `LOKI_PASSWORD` | _(empty)_ | Loki auth password (if enabled) |

These endpoints match the Paperclip observability stack deployed via `docker-compose.observability.yml` (see [ANGA-399](/ANGA/issues/ANGA-399)).

## Quick Verification

After the stack is up, run these checks:

```bash
# Loki
curl -s "${LOKI_URL:-http://localhost:3100}/ready"

# Prometheus
curl -s "${PROMETHEUS_URL:-http://localhost:9090}/-/healthy"

# Tempo
curl -s "${TEMPO_URL:-http://localhost:3200}/ready"

# Grafana
curl -s "${GRAFANA_URL:-http://localhost:3000}/api/health" | jq '.'
```

All should return HTTP 200 and a success response.

## Installation

This plugin is part of the `claude-private` repo. To install in Claude Desktop:

1. Open Claude Desktop → Settings → Developer → Edit Config
2. Add the plugin source pointing to this repo
3. The `observability` plugin and all its skills will be available

Or install via the Paperclip marketplace if published there.

## Usage Example

Load a skill in Claude Code:

```
/observability:loki-logs
```

Then ask:
```
Show me the last 30 minutes of errors for agent 754f0eda
```

Or run the error report directly:
```
/observability:error-patterns
```

Then ask:
```
Give me a full error report for the last 6 hours and identify any patterns worth creating issues for.
```
