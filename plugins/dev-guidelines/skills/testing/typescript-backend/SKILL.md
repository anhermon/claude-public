---
name: typescript-backend
description: TypeScript backend testing conventions using Bun's built-in test runner and Hono test helpers. Implements the tier model and layered switching pattern from testing/. Use when writing or modifying tests in any TypeScript backend service.
license: MIT
compatibility: opencode
metadata:
  audience: developers
  workflow: testing
---

## What I do

I provide TypeScript backend testing conventions. Always load `testing/` first for philosophy and tier model — this skill covers the Bun + Hono implementation of those principles.

## Test Runner Decision Tree

```
Which test runner?
├── Runtime is Bun → bun test  ← built-in, zero-config, fastest
├── Runtime is Node, using Vite / ES modules → Vitest
│   └── Trade-off: same API as Jest; native ESM; fast HMR in watch mode
├── Runtime is Node, existing Jest codebase → Jest
│   └── Trade-off: requires ts-jest or babel-jest; slower than Vitest; huge ecosystem
└── Migrating from Jest to Vitest → near-identical API; usually a drop-in swap
```

**Trade-offs:**

| Runner | Best for | Watch out for |
|---|---|---|
| **bun test** | Bun projects; zero config; native TS; fastest cold start | Bun-only; mock API differs slightly from Jest |
| **Vitest** | Vite/Node projects; Jest-compatible API; fast ESM | Requires explicit config; not built into any runtime |
| **Jest** | Legacy Node.js codebases; maximum ecosystem | Requires transform setup for TS/ESM; slowest of the three |

This skill covers `bun test`. For Vitest: apply the same tier model (directory-based: `tests/unit/`, `tests/smoke/`, `tests/integration/`) and use `vitest.config.ts` to select subsets. For Jest: use `--testPathPattern` or `--testNamePattern` to select tiers.

---

## Stack

| Concern | Tool |
|---|---|
| Test runner | `bun test` (built-in, zero-config) |
| HTTP testing | Hono's `app.request()` test helper |
| Mocking | `bun:test` mock utilities (`mock()`, `spyOn()`) |
| Coverage | `bun test --coverage` — enforced at 80% |

---

## Tier tagging convention

Bun's test runner does not have a native marker system like pytest. Implement tier switching via naming convention + Taskfile filter.

**Convention: prefix test file names with tier.**

```
tests/
  unit/
    discount.test.ts
    order.test.ts
  smoke/
    auth.test.ts
    order-create.test.ts
  integration/
    payment-flow.test.ts
    order-fulfillment.test.ts
```

**Taskfile mapping:**
```yaml
tasks:
  test:unit:
    cmd: bun test tests/unit --coverage

  test:smoke:
    cmd: bun test tests/smoke

  test:integration:
    cmd: bun test tests/integration

  test:all:
    cmd: bun test --coverage
```

No changes to test code to switch tiers — the task controls which folder runs.

---

## BDD scenario naming

```typescript
// Unit — function contract
describe("calculateDiscount", () => {
  test("given zero items, when discount calculated, then returns zero", () => {
    expect(calculateDiscount([])).toBe(0)
  })
})

// Smoke — service happy path
describe("POST /auth/login", () => {
  test("given valid credentials, when login requested, then token returned", async () => {
    const res = await app.request("/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email: "test@example.com", password: "correct" }),
    })
    expect(res.status).toBe(200)
    const body = await res.json()
    expect(body).toHaveProperty("accessToken")
  })
})
```

---

## HTTP testing with Hono

Use `app.request()` — no need for a running server, no port binding, no teardown.

```typescript
import { app } from "../../src/index"

test("GET /health returns 200", async () => {
  const res = await app.request("/health")
  expect(res.status).toBe(200)
})

test("POST /orders with valid body creates order", async () => {
  const res = await app.request("/orders", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ productId: "prod_123", quantity: 2 }),
  })
  expect(res.status).toBe(201)
})
```

For authenticated routes, construct the request with an auth header using a test token helper — do not disable auth middleware.

```typescript
// tests/helpers/auth.ts
export const testAuthHeader = () => ({
  Authorization: `Bearer ${generateTestToken({ userId: "user_test_1" })}`,
})

// In test
const res = await app.request("/orders", {
  headers: { ...testAuthHeader(), "Content-Type": "application/json" },
  ...
})
```

---

## Mocking

Use `bun:test` mock utilities. Mock at the service boundary — never mock internal implementation details.

```typescript
import { mock, spyOn } from "bun:test"

// Mock an entire module
const mockCharge = mock(async (amount: number, token: string) => ({
  status: "success",
  chargeId: "ch_test_123",
}))

mock.module("../../src/lib/payment-gateway", () => ({
  charge: mockCharge,
}))

// Spy on a method without replacing it
const spy = spyOn(orderService, "sendConfirmation")
```

**Smoke tests inject mocks. Integration tests do not.**

```typescript
// tests/smoke/order-create.test.ts — uses mock
import { mock } from "bun:test"
mock.module("../../src/lib/payment-gateway", () => ({ charge: mockCharge }))

// tests/integration/order-fulfillment.test.ts — real gateway, no mock import
```

---

## Data setup

Keep test data setup explicit and local to the test file or a shared `fixtures/` helper. Avoid complex factory chains.

```typescript
// tests/fixtures/orders.ts
export const buildOrder = (overrides = {}) => ({
  productId: "prod_test_1",
  quantity: 1,
  userId: "user_test_1",
  ...overrides,
})

// In test
const order = buildOrder({ quantity: 5 })
```

For integration tests that need DB state: seed directly via the service layer or DB client in a `beforeAll` block, and clean up in `afterAll`. Use targeted deletes — not full DB teardown.

```typescript
beforeAll(async () => {
  await db.insert(users).values(testUser)
})

afterAll(async () => {
  await db.delete(users).where(eq(users.id, testUser.id))
})
```

---

## Coverage

```bash
# Enforce in CI via task
bun test --coverage --coverage-threshold 80
```

Coverage enforced on `test:unit` and `test:all`. Not enforced on `test:smoke` or `test:integration`.

---

## What not to do

- Do not use `fetch` against a running server in tests — use `app.request()`.
- Do not disable auth middleware in tests — use a test token helper.
- Do not share mutable state between tests via module-level variables.
- Do not use `setTimeout` to wait for async behavior — use `await` and proper async patterns.
- Do not mock internal implementation details — mock at the service boundary.
- Do not omit tier directory — every test file must live under `unit/`, `smoke/`, or `integration/`.
