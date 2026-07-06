---
name: observability
description: Observability conventions for logging, distributed tracing, and metrics. Use when instrumenting any Python or TypeScript service with structured logs, OpenTelemetry traces, or Prometheus metrics.
license: MIT
compatibility: opencode
metadata:
  audience: developers
  workflow: observability
---

## What I do

I provide conventions for instrumenting services with structured logging, distributed tracing, and metrics. Covers both Python (FastAPI) and TypeScript (Hono) stacks.

---

## Stack

| Concern | Python | TypeScript |
|---|---|---|
| Logging | loguru | Hono logger middleware + `console` structured JSON |
| Distributed traces | opentelemetry-sdk | OpenTelemetry JS SDK |
| Metrics | starlette-exporter (Prometheus) | Prometheus client or Hono middleware |

---

## Logging

### Python — loguru

Use `loguru` everywhere. Never use stdlib `logging` in new code.

```python
from loguru import logger

# Configure once at startup in main.py
import sys
logger.configure(handlers=[{
    "sink": sys.stdout,
    "format": "{time:ISO8601} | {level} | {name}:{line} | {message} | {extra}",
    "serialize": True,   # outputs JSON
}])

# Usage — structured context via bind()
logger.bind(user_id=user.id, request_id=request_id).info("User logged in")
logger.bind(order_id=order.id).error("Payment failed")
```

**Conventions:**
- Always emit structured JSON in production — set `serialize=True`.
- Use `logger.bind()` to attach structured context rather than interpolating into the message string.
- Log at the service boundary (routes/handlers), not deep in domain logic.
- Never log PII (emails, tokens, passwords) — log IDs and reference keys only.

### TypeScript — structured JSON

Use Hono's built-in logger middleware for request logging. For application-level events, emit structured JSON via `console.log` with a consistent shape.

```typescript
import { logger } from 'hono/logger'
app.use('*', logger())

// Application events — structured, not interpolated strings
const log = (level: string, msg: string, ctx: Record<string, unknown> = {}) =>
  console.log(JSON.stringify({ level, msg, time: new Date().toISOString(), ...ctx }))

log('info', 'Payment processed', { orderId, amount, userId })
log('error', 'DB connection failed', { error: err.message })
```

**Same rules apply:** never log PII, log IDs not values, attach context as fields not string interpolation.

---

## Distributed tracing — OpenTelemetry

### Python

```python
# main.py — instrument at startup
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

provider = TracerProvider()
provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
trace.set_tracer_provider(provider)

FastAPIInstrumentor.instrument_app(app)   # auto-instruments all routes

# Manual spans for significant operations
tracer = trace.get_tracer(__name__)

async def process_payment(order_id: str):
    with tracer.start_as_current_span("process_payment") as span:
        span.set_attribute("order.id", order_id)
        # ... logic
```

### TypeScript

```typescript
import { NodeSDK } from '@opentelemetry/sdk-node'
import { OTLPTraceExporter } from '@opentelemetry/exporter-trace-otlp-grpc'
import { trace } from '@opentelemetry/api'

const sdk = new NodeSDK({ traceExporter: new OTLPTraceExporter() })
sdk.start()

// Manual span
const tracer = trace.getTracer('my-service')
const span = tracer.startSpan('process-payment')
span.setAttribute('order.id', orderId)
// ... logic
span.end()
```

**Conventions:**
- Always instrument at the framework level (FastAPIInstrumentor, Hono middleware) for automatic route tracing.
- Add manual spans only for significant business operations — not every function call.
- Attach business-relevant attributes (`order.id`, `user.id`) to spans, not technical noise.
- Export to OTLP endpoint (Jaeger, Tempo, or whatever collector is configured per project).

---

## Metrics — Prometheus

### Python — starlette-exporter

```python
from starlette_exporter import PrometheusMiddleware, handle_metrics

app.add_middleware(PrometheusMiddleware)
app.add_route("/metrics", handle_metrics)
```

This automatically exposes:
- `starlette_requests_total` — request count by method, path, status
- `starlette_request_duration_seconds` — latency histogram

**Custom metrics:**
```python
from prometheus_client import Counter, Histogram

payments_processed = Counter("payments_processed_total", "Total payments", ["status"])
payment_duration = Histogram("payment_duration_seconds", "Payment processing time")

# Usage
payments_processed.labels(status="success").inc()
with payment_duration.time():
    await process_payment(order)
```

### TypeScript — Hono + prom-client

```typescript
import { Registry, Counter, collectDefaultMetrics } from 'prom-client'

const registry = new Registry()
collectDefaultMetrics({ register: registry })

const httpRequests = new Counter({
  name: 'http_requests_total',
  help: 'Total HTTP requests',
  labelNames: ['method', 'path', 'status'],
  registers: [registry],
})

// Expose /metrics endpoint
app.get('/metrics', async (c) => {
  return c.text(await registry.metrics(), 200, {
    'Content-Type': registry.contentType,
  })
})
```

**Conventions:**
- Always expose a `/metrics` endpoint — never push metrics directly from services.
- Use labels for dimensions (`status`, `method`, `path`) — keep cardinality low.
- Name metrics following Prometheus conventions: `<namespace>_<name>_<unit>` (e.g. `payments_processed_total`, `db_query_duration_seconds`).
- Do not create per-user or per-request-ID labels — high cardinality will OOM the collector.

---

## What not to do

- Do not use stdlib `logging` in Python — use loguru.
- Do not log PII (emails, names, tokens) — log IDs only.
- Do not interpolate context into log message strings — use structured fields.
- Do not add manual OpenTelemetry spans to every function — instrument at the boundary level, add manual spans only for significant operations.
- Do not use high-cardinality labels in Prometheus metrics (user IDs, request IDs, etc.).
- Do not skip the `/metrics` endpoint — it is required for any service running in Kubernetes.
