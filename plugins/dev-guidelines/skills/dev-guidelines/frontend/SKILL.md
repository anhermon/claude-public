---
name: frontend
description: Frontend conventions. Starts with a framework decision tree (Next.js vs Vite/React vs Remix) with trade-offs, then provides implementation conventions for the chosen stack. Covers state management, data fetching, component libraries, and testing boundaries. Load after dev-guidelines.
license: MIT
compatibility: opencode
metadata:
  audience: developers
  workflow: frontend-development
---

## What I do

I guide frontend framework decisions and provide implementation conventions. I start with the framework choice — read the decision tree, confirm which applies, then follow that path.

## When to use me

Load when writing or modifying any UI, frontend pages, components, or full-stack web applications.

---

## Framework Decision Tree

```
Is this a new project or greenfield?
├── Yes → Is SEO / server rendering required?
│   ├── Yes → Does the app have tightly coupled server logic / API routes?
│   │   ├── Yes → Next.js App Router  ← default for full-stack React
│   │   └── No  → Remix (server-first, nested routing, form actions)
│   └── No  → Is it a pure SPA / dashboard / admin panel?
│       ├── Yes → Vite + React  ← default for SPA
│       └── No  → Next.js (static export mode)
└── No (existing project) → match existing framework
```

**Trade-offs:**

| Framework | Best for | Watch out for |
|---|---|---|
| **Next.js App Router** | Full-stack React, SEO, server components, tRPC | Build complexity; `.next/` cache corruption; App Router learning curve |
| **Vite + React** | SPAs, dashboards, fast DX, no SSR needed | No built-in SSR; routing via React Router or TanStack Router |
| **Remix** | Server-first, form-heavy apps, nested layouts, progressive enhancement | Smaller ecosystem; opinionated loader/action pattern |

---

## Component Library Decision Tree

```
Does the project already have a UI library?
├── Yes → Use it; do not introduce a second one
└── No  → Is it a design-system-heavy product with custom branding?
    ├── Yes → shadcn/ui (copy-paste, fully customizable)  ← default
    ├── No, need fast prototyping → shadcn/ui or Radix UI primitives
    └── Internal tool, no design system → shadcn/ui or Tailwind + Headless UI
```

| Library | Best for | Watch out for |
|---|---|---|
| **shadcn/ui** | Customizable, accessible, copy-paste ownership | Must be committed to repo; not an npm dependency |
| **Radix UI** | Unstyled accessible primitives, roll your own styles | Requires Tailwind or CSS to style |
| **MUI / Ant Design** | Opinionated design system, fast admin UIs | Heavy bundle; hard to customize away from system defaults |

---

## Styling Decision Tree

```
New project — which CSS approach?
├── Utility-first, flexible → Tailwind CSS  ← default
├── CSS-in-JS, dynamic theming → styled-components or vanilla-extract
└── Scoped, minimal runtime → CSS Modules
```

**Do not mix Tailwind and CSS-in-JS in the same project.**

---

## State Management Decision Tree

```
What kind of state?
├── Server state (fetched data, async) → TanStack Query (React Query)
│   └── In Server Components: native fetch + React cache — no library needed
├── Client UI state (modals, tabs, local form state) → useState / useReducer
├── Cross-component client state → Zustand  ← default; no Redux
└── Form state → React Hook Form + Zod resolver
```

| Tool | Best for | Watch out for |
|---|---|---|
| **TanStack Query** | Async server state, caching, invalidation | Only use in Client Components |
| **Zustand** | Lightweight global client state | Not a replacement for server state management |
| **Redux Toolkit** | Large teams with complex shared state, existing Redux | Overkill for most projects; adds significant boilerplate |

---

## Next.js App Router Conventions

### Runtime

```bash
bun install                  # dependencies
bun --bun run dev            # dev server on Bun runtime (--bun flag required)
bun --bun run build          # production build
```

`--bun` flag is required to run Next.js on the Bun runtime rather than spawning a Node child process. Never use `npx`, `node`, or `ts-node`.

### Project Structure

```
app/               ← Next.js App Router routes and layouts
components/
  ui/              ← shadcn/ui primitives (committed, not installed as package)
  <domain>/        ← feature/domain-specific components
lib/               ← utilities, shared logic, Zod schemas
server/            ← tRPC routers, DB access (when co-located with Next.js)
public/            ← static assets
```

### Server vs Client Components

- Default to **Server Components** — no `"use client"` unless the component requires hooks, interactivity, or browser APIs.
- Keep `"use client"` components as **leaf nodes** — push them down the tree, not up.
- Never fetch data in Client Components when a Server Component can do it.
- Never use TanStack Query in Server Components.

### shadcn/ui

- Use `bunx shadcn@latest add <component>` to add components.
- Components live in `components/ui/` and are committed to the repo — not installed as npm packages.
- Extend what exists; never rebuild what shadcn provides.

### Styling

- Apply Tailwind utility classes directly in JSX.
- Do not use `@apply` except in rare, justified base-layer cases.
- No CSS-in-JS (styled-components, emotion) in Tailwind projects.

### TypeScript

- Strict mode always. No `any`, no implicit `any`.
- Prefer `unknown` + type narrowing over `as` casts.
- Validate all external data (API responses, form input) with Zod.

### Data fetching

- In Server Components: `fetch()` directly + `cache()` to deduplicate.
- In Client Components: TanStack Query for async server state.

### Pre-commit additions (TypeScript / frontend block)

Same as `backend-typescript` skill — ESLint + Prettier at commit stage, `tsc --noEmit` at push stage.

---

## Vite + React SPA Conventions

Use for dashboards, admin panels, and SPAs where SSR is not needed.

### Project Structure

```
src/
  main.tsx          ← entry point, router setup
  routes/           ← page components (React Router or TanStack Router)
  components/       ← shared components
  hooks/            ← custom hooks
  lib/              ← utilities, API client, Zod schemas
  store/            ← Zustand stores
```

### Key conventions

- Use **TanStack Router** for new projects (type-safe, file-based routing).
- Use **React Router v6** for projects already on it — do not migrate mid-project.
- Data fetching via TanStack Query + a typed API client (axios or fetch wrapper).
- Environment variables: `VITE_*` prefix for client-side, validated at startup via Zod.

```typescript
// src/lib/env.ts
import { z } from 'zod'
const schema = z.object({ VITE_API_URL: z.string().url() })
export const env = schema.parse(import.meta.env)
```

---

## Remix Conventions

Use for server-first apps where form handling, progressive enhancement, and nested layouts are central.

### Key conventions

- Use **loaders** for server data fetching — no `useEffect` + fetch patterns.
- Use **actions** for mutations — no separate API layer needed for form submissions.
- Use **nested routes** for shared layouts — not manual composition.
- Defer non-critical data with `defer()` + `<Await>` to unblock initial render.
- `useFetcher` for non-navigating form submissions (inline edits, partial updates).

---

## Validation before done

After generating or modifying UI code:
- Describe the expected rendered output: layout, component hierarchy, all interactive states (default, hover, loading, error, empty).
- Account for responsive behavior (mobile, tablet, desktop).
- Do not declare done if loading and error states are unimplemented.

---

## What not to do (all frameworks)

- Do not install shadcn/ui as an npm dependency — copy-paste only.
- Do not use CSS-in-JS or CSS Modules in Tailwind projects.
- Do not use `any` or `@ts-ignore` without a documented reason.
- Do not use Redux — Zustand is the default for client state.
- Do not use TanStack Query in Server Components (Next.js).
- Do not fetch data in Client Components when a Server Component can handle it.
- Do not mix multiple routing libraries in the same project.
- Do not hardcode API keys or secrets in client-side code — they are visible in the browser.
