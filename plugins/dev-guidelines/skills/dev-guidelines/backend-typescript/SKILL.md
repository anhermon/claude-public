---
name: backend-typescript
description: TypeScript backend conventions. Starts with a framework and runtime decision tree (Hono/Bun vs Express/Node vs Fastify) with trade-offs, then provides implementation conventions for the chosen stack. Load after dev-guidelines.
license: MIT
compatibility: opencode
metadata:
  audience: developers
  workflow: backend-development
---

## What I do

I guide TypeScript backend decisions and provide implementation conventions. I start with the runtime and framework choice — read the decision tree, confirm which applies, then follow that path.

## When to use me

Load when writing or modifying any TypeScript backend service, API, worker, or microservice. For API routes tightly coupled to a Next.js frontend, load `frontend` instead and use tRPC via Route Handlers.

---

## Runtime Decision Tree

```
Is this a standalone service (not inside Next.js)?
├── Yes → Is it greenfield / no existing runtime constraint?
│   ├── Yes → Is edge/serverless deployment a requirement?
│   │   ├── Yes → Hono (edge-compatible) on Bun or Node
│   │   └── No  → Hono on Bun  ← default for new services
│   └── No  → Match existing runtime (Bun / Node)
└── No (inside Next.js) → Load `frontend` skill; use tRPC Route Handlers
```

**Runtime trade-offs:**

| Runtime | Best for | Watch out for |
|---|---|---|
| **Bun** | New services; fast startup; native TS; built-in test runner | Smaller ecosystem; some npm packages have compatibility issues |
| **Node.js** | Legacy codebases; max npm compatibility; broad ecosystem | Slower startup; requires ts-node or compile step |

---

## Framework Decision Tree

```
New service — which framework?
├── Lightweight microservice / edge / Bun-native → Hono  ← default
├── Large existing Express codebase to extend → Express
│   └── Express is sync by default; add express-async-errors for async routes
├── High-throughput JSON API, plugin ecosystem → Fastify
│   └── JSON schema validation built-in; steeper learning curve
└── API tightly coupled to Next.js → tRPC via Route Handlers (load `frontend`)
```

**Framework trade-offs:**

| Framework | Best for | Watch out for |
|---|---|---|
| **Hono** | Edge, Bun, lightweight APIs, fast cold starts | Smaller middleware ecosystem than Express |
| **Express** | Legacy migration, large middleware ecosystem | Sync by default; requires careful async error handling |
| **Fastify** | High-throughput APIs, JSON schema validation, plugin system | Schema-first approach requires upfront schema design |

---

## ORM Decision Tree

```
What is your DB?
├── PostgreSQL / SQLite → Drizzle ORM  ← default (type-safe, migration-explicit)
│                      → Prisma (if team prefers schema-first DX)
├── MySQL / MariaDB    → Drizzle (mysql2 dialect) or Prisma
└── MongoDB            → Mongoose or native driver

Do you have an existing schema?
├── Yes → Drizzle (introspect with drizzle-kit pull)
└── No  → Either; Drizzle migrations are more explicit
```

| ORM | Best for | Watch out for |
|---|---|---|
| **Drizzle** | Type-safety, explicit migrations, lightweight | No query builder GUI; smaller community |
| **Prisma** | Schema-first DX, auto-generated client, Prisma Studio | Generated client adds weight; less transparent SQL |

**Do not mix Drizzle and Prisma in the same project.**

---

## Hono + Bun Conventions

### Project Structure

```
src/
  index.ts          ← app entry, Hono instance, middleware registration
  routes/           ← route handlers grouped by domain
  services/         ← business logic, no direct DB access in routes
  db/               ← Drizzle schema, migrations, client
  lib/              ← utilities, shared logic
  env.ts            ← Zod-validated env schema, exported as `env`
tests/
  unit/             ← plain bun test
  smoke/            ← fast integration, mocks at boundary
  integration/      ← real deps, no mocks
```

### Conventions

**Environment**
```typescript
// env.ts — define once, import everywhere
import { z } from 'zod'

const schema = z.object({
  DATABASE_URL: z.string().url(),
  PORT: z.coerce.number().default(3000),
})

export const env = schema.parse(process.env)
```
Never access `process.env` directly outside `env.ts`.

**Routing**
- Group routes by domain in `routes/`. Register on the Hono app in `index.ts`.
- Never put business logic in route handlers — delegate to `services/`.
- Validate all incoming request bodies and params with Zod before touching them.
- Return typed errors — never leak internal error details in responses.

**TypeScript**
- Strict mode always. No `any`. No `@ts-ignore` without a documented reason.
- Prefer `unknown` + type narrowing over `as` casts.
- Explicit return types on all exported functions.

**Commands**

| Context | Command |
|---|---|
| Install dependencies | `bun install` |
| Run service | `bun run src/index.ts` |
| Run tests | `bun test` |
| One-off scripts | `bun run ./scripts/my-script.ts` |

Never use `npx`, `node`, or `ts-node` in a Bun project.

### Pre-commit additions (TypeScript block)

```yaml
  - repo: https://github.com/pre-commit/mirrors-eslint
    rev: v9.6.0
    hooks:
      - id: eslint
        stages: [commit]
        files: \.(ts|tsx|js|jsx)$
        additional_dependencies:
          - eslint
          - typescript
          - "@typescript-eslint/parser"
          - "@typescript-eslint/eslint-plugin"

  - repo: https://github.com/pre-commit/mirrors-prettier
    rev: v4.0.0-alpha.8
    hooks:
      - id: prettier
        stages: [commit]
        files: \.(ts|tsx|js|jsx|json|md|yaml|yml|css)$
```

TypeScript type checking (`tsc --noEmit`) runs at push stage.

---

## Express (Node.js) Conventions

Use when extending an existing Express codebase or when npm ecosystem compatibility is the primary constraint.

### Key conventions

- Always use `express-async-errors` — import at app entry to catch async errors globally.
- Use `express-validator` or Zod for input validation on all routes.
- Middleware order: cors → body-parser → auth → routes → error handler.
- Error handler middleware must have 4 parameters: `(err, req, res, next)`.
- Use `helmet` for security headers in production.

```typescript
// Validated env — same pattern as Hono
import { z } from 'zod'
export const env = z.object({ PORT: z.coerce.number().default(3000) }).parse(process.env)
```

---

## Fastify Conventions

Use when building high-throughput APIs where JSON schema validation and plugin isolation matter.

### Key conventions

- Define JSON schemas for all routes (`schema: { body, querystring, params, response }`).
- Use `@fastify/type-provider-typebox` or `zod-to-json-schema` for TypeScript integration.
- Plugins are the primary extension mechanism — never monkey-patch the instance.
- Use `fastify.register()` for all route groups with prefix isolation.
- `fastify.inject()` for testing — no running server needed.

---

## What not to do (all frameworks)

- Do not access `process.env` directly — use the validated `env` module.
- Do not put business logic in route handlers — delegate to `services/`.
- Do not use `any` or suppress TypeScript errors without a documented reason.
- Do not mix ORMs in the same project.
- Do not use `npx`, `node`, or `ts-node` in Bun projects.
- Do not hardcode secrets — see `dev-guidelines` for `.env.local` / SOPS workflow.
