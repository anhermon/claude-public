---
description: Full codebase review using 9 specialized subagents (architecture, correctness, security, performance, observability, readability, contracts, data, ci). Use /review for a complete cross-domain report, or /review --domain security to target a single domain. Usage /review [--type backend|microservice|frontend] [--scope paths] [--domain DOMAIN]
argument-hint: "[--type TYPE] [--scope PATHS] [--domain DOMAIN]"
---

# Code Review Orchestrator

You are orchestrating a code review using specialized sub-agents.

## Parse arguments

From `$ARGUMENTS` extract:
- `--type`: `backend` | `microservice` | `frontend` (default: `backend`)
- `--scope`: Optional paths to focus review on (e.g., `--scope src/api services/payment`)
- `--domain`: Run a single domain instead of the full suite. Valid values:
  `architecture`, `correctness`, `security`, `performance`, `observability`,
  `readability`, `contracts`, `data`, `ci`

**Examples:**
- `/review --type microservice --scope services/payments` — full review, scoped
- `/review --domain security` — security only
- `/review --domain performance --scope src/hot-path.ts` — performance, scoped

## Domain → sub-agent mapping

| Domain | Sub-agent |
|---|---|
| architecture | architecture-reviewer |
| correctness | correctness-reviewer |
| observability | error-observability-reviewer |
| security | security-reviewer |
| performance | performance-reviewer |
| readability | readability-reviewer |
| contracts | api-contracts-reviewer |
| data | data-reviewer |
| ci | ci-deps-reviewer |

## Execution

**If `--domain` is provided:** invoke only that sub-agent. Skip the full report template — just output the sub-agent's findings directly.

**If no `--domain`:** invoke all 9 sub-agents in this order:
1. architecture-reviewer
2. correctness-reviewer
3. error-observability-reviewer
4. security-reviewer
5. performance-reviewer
6. readability-reviewer
7. api-contracts-reviewer
8. data-reviewer
9. ci-deps-reviewer

When invoking each sub-agent:
- Pass the project type
- If `--scope` was provided, restrict the sub-agent to those paths
- Request output as: top risks (H/M/L), concrete fixes with file:line references, code diffs where useful

## Full report format (no --domain only)

### 1. Executive Summary
- Key findings per domain
- Overall health assessment
- Critical issues requiring immediate attention

### 2. Findings by Category
Table: Category | Severity | Issue | File Reference

### 3. 72-Hour Action Plan
Prioritized fixes grouped by impact, with effort estimate (Quick/Moderate/Large)

### 4. Detailed Findings
Per domain: risks, recommended fixes, code snippets or diffs, path:line references
