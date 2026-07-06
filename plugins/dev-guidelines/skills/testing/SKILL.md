---
name: testing
description: Testing philosophy, TDD+BDD workflow, test tier model, coverage policy, and execution time principles. Entry point for all testing guidelines. Load this first, then load the relevant sub-skill for framework-specific conventions.
license: MIT
compatibility: claude-code
metadata:
  audience: developers
  workflow: testing
---

## What I do

I provide the testing philosophy, workflow, and tier model that applies across all projects and stacks. I define the *what* and *why* of testing. Sub-skills define the *how* for each framework.

## Sub-skill routing

| Context | Load |
|---|---|
| Any project | This skill (always) |
| Python backend tests | `python` |
| TypeScript backend tests | `typescript-backend` |
| Frontend component tests | `testing-frontend` |
| E2E and integration scenario tests | `e2e` |

Multiple sub-skills can be loaded together — e.g. `python` + `e2e` for a FastAPI project with Playwright scenarios.

---

## Philosophy

**Tests are specifications, not afterthoughts.** A test written before implementation is a design decision. A test written after is a regression guard. Both have value, but the first has more.

**Tests should read like behavior descriptions, not implementation traces.** A failing test should tell you what the system is supposed to do, not which line of code broke.

**Confidence over coverage.** 80% coverage is the floor, not the goal. 100% coverage with shallow assertions is worse than 75% coverage with tests that catch real regressions. Coverage measures what is executed — not what is verified.

---

## TDD Workflow

Use TDD when implementing any non-trivial logic from a specification or user story.

```
1. Read the spec / user story
2. Write a failing test that describes the expected behavior (Red)
3. Write the minimum code to make it pass (Green)
4. Refactor — clean up without breaking the test (Refactor)
5. Repeat for the next behavior
```

**What TDD is not:**
- Writing tests after the fact and calling it TDD
- Achieving coverage by testing every line
- Testing implementation details (internal function calls, private methods)

**When to apply TDD:**
- Service layer logic, business rules, data transformations
- Any function where the spec can be expressed as input → output
- Bug fixes — write a test that reproduces the bug first, then fix it

**When TDD is less applicable:**
- UI layout and visual behavior (use E2E instead)
- Infrastructure setup (DB migrations, container config)
- Exploratory spikes (throw away the spike, then TDD the real implementation)

---

## BDD Scenario Convention

BDD structures tests as human-readable scenarios describing system behavior from the user's or caller's perspective. No Gherkin framework is required — apply the convention in any test framework using Given/When/Then naming.

**Scenario anatomy:**
- **Given** — the starting state / preconditions
- **When** — the action or event
- **Then** — the expected outcome

**Applied in test naming:**
```
given_user_is_authenticated__when_they_select_plan__then_checkout_loads
given_empty_cart__when_item_is_added__then_cart_count_is_1
given_invalid_token__when_request_is_made__then_401_is_returned
```

**Conventions:**
- Scenario names describe behavior, not implementation (`test_payment_service_calls_stripe` is bad; `given_valid_card__when_payment_submitted__then_order_is_confirmed` is good).
- One scenario per test. Do not assert multiple unrelated behaviors in a single test.
- Scenarios at the integration and E2E tier map directly to user stories or acceptance criteria.
- Scenarios at the unit tier describe the contract of a single function or service method.

---

## Test Tier Model

Tests are organized into four tiers. Each tier has a defined scope, speed expectation, and role in CI.

| Tier | Scope | Mocks | Speed | CI Stage |
|---|---|---|---|---|
| **Unit** | Single function or class | All external deps mocked | < 1s per test | Every commit |
| **Integration (fast)** | Service + DB or service + service | External APIs mocked; real DB | < 10s per test | Every commit |
| **Integration (full)** | End-to-end service flows | No mocks; real dependencies | Seconds–minutes | PR / on-demand |
| **E2E** | Full stack through UI | No mocks | Minutes | PR / scheduled |

**Tier selection rules:**
- Test behavior at the lowest tier where it can be meaningfully verified.
- Do not duplicate coverage across tiers — if a flow is covered by integration tests, E2E tests verify the happy path only.
- Unit tests do not test framework behavior (routing, serialization) — that belongs at integration tier.

---

## The Layered Switching Pattern

The same scenario should be runnable in multiple modes without rewriting the test. The mechanism is layered:

**Layer 1 — Tags/markers** define what a test is (`unit`, `integration`, `smoke`, `e2e`).
**Layer 2 — Tasks** invoke the right subset (`task test:smoke`, `task test:integration`, `task test:e2e`).
**Layer 3 — Environment** controls whether real or mock dependencies are used (via config/fixture, not test code).

```
task test:unit        → runs tagged unit tests only (fast, always)
task test:smoke       → runs tagged smoke subset (fast integration, key paths)
task test:integration → runs full integration suite (real deps, no mocks)
task test:e2e         → runs Playwright scenarios
task test:all         → runs everything
```

This means CI can run `test:unit` + `test:smoke` on every commit and reserve `test:integration` + `test:e2e` for PRs or scheduled runs — without changing any test code.

Framework-specific implementation of tags and environment switching is in the relevant sub-skill.

---

## Execution Time Principles

Slow tests are not run. Tests that are not run provide no value. Manage execution time deliberately.

**Subset selection** — tag tests by tier and run the minimum meaningful subset for the context. A commit check should complete in under 2 minutes. A full PR run in under 15.

**Environment reuse** — prefer tests that run against a shared, pre-seeded environment over tests that spin up and tear down infrastructure per test. For integration tests against a DB: seed once per suite, reset state between tests with transactions or targeted deletes — not full teardown/rebuild.

**Parallelization** — run independent test suites in parallel in CI. Tests within a suite run sequentially unless the framework explicitly supports safe parallel execution.

**No sleeps** — never use `time.sleep()` or `setTimeout` to wait for async behavior. Use proper async waiting patterns, retries with backoff, or framework-provided waiters.

**Test isolation without full teardown** — tests must be independent, but independence does not require rebuilding all state. Wrap each test in a transaction and roll back; or reset only the tables/keys the test touched.

---

## Coverage Policy

- **Minimum threshold: 80%** — enforced in CI. A build below 80% fails.
- Coverage is measured at the **integration tier and below** — E2E tests are excluded from coverage reporting (they verify behavior, not code paths).
- Coverage below 80% is a signal of missing tests, not a target to game with trivial assertions.
- Do not write assertions purely to hit coverage. A covered line with no meaningful assertion is noise.

---

## What Not To Test

- Framework behavior (routing, serialization, ORM queries) — test your code, not the library.
- Configuration values — test behavior driven by config, not the config itself.
- Implementation details — private methods, internal state, call order between collaborators (unless order is the contract).
- Third-party service internals — mock the boundary, test your handling of responses.
- Trivial getters/setters with no logic.
- Generated code.

---

## What Always Gets Tests

- Any function with a non-trivial conditional
- Any service method that handles money, auth, or data mutation
- Any error handling path that the system is expected to recover from
- Any behavior derived from a user story or acceptance criterion
- Any bug that has been fixed — regression test required before fix is merged
