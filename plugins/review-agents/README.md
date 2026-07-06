# review-agents

Full codebase review orchestrated across 9 specialized subagents, invoked via `/review`.

Complements the single-pass `code-review` plugin: `code-review` is a fast, self-contained skill for a quick pass over a diff; `review-agents` fans a review out across dedicated architecture/correctness/security/performance/observability/readability/contracts/data/ci subagents for a deeper, cross-domain pass.

## Usage

```
/review                                # full review, all 9 domains
/review --type microservice            # tailor for backend|microservice|frontend
/review --scope src/api services/pay   # scope to specific paths
/review --domain security              # run a single domain
```
