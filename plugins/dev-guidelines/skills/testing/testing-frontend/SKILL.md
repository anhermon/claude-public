---
name: testing-frontend
description: Frontend component testing conventions using Jest and React Testing Library. Covers what belongs at this tier vs E2E, async patterns, and BDD scenario naming for UI components. Use when writing or modifying component or unit tests in a Next.js/React project.
license: MIT
compatibility: opencode
metadata:
  audience: developers
  workflow: testing
---

## What I do

I provide frontend testing conventions using Jest and React Testing Library. Always load `testing` first for philosophy and tier model. For user-journey and integration scenarios, load `e2e` instead.

---

## Stack

| Concern | Tool |
|---|---|
| Test runner | Jest |
| Component testing | React Testing Library (RTL) |
| Async | `waitFor`, `findBy*` queries |
| Mocking | Jest `mock()`, `spyOn()` |
| Coverage | `jest --coverage` — enforced at 80% |

---

## What belongs at this tier vs E2E

**Test here (component tier):**
- Component renders correctly given props
- Component state changes on user interaction
- Conditional rendering (loading, error, empty, populated states)
- Form validation feedback
- Accessibility (roles, labels, keyboard navigation)

**Test in E2E (`e2e`):**
- Multi-page user journeys
- Navigation and routing behavior
- Real API integration
- Flows that span multiple components in sequence

If in doubt: if the test needs a real browser and a running backend, it belongs in E2E.

---

## Tier tagging

```
tests/
  unit/             ← pure logic, hooks, utilities
  components/       ← RTL component tests (maps to "integration (fast)" tier)
```

**Taskfile mapping:**
```yaml
tasks:
  test:unit:
    cmd: jest tests/unit --coverage

  test:components:
    cmd: jest tests/components --coverage

  test:all:
    cmd: jest --coverage
```

---

## BDD scenario naming

Name tests by behavior, not by component internals.

```typescript
// ✅ Describes user-visible behavior
describe("CheckoutButton", () => {
  test("given cart is empty, when rendered, then button is disabled", () => { ... })
  test("given cart has items, when clicked, then loading state shows", async () => { ... })
  test("given payment fails, when error returned, then error message is displayed", async () => { ... })
})

// ❌ Describes implementation
describe("CheckoutButton", () => {
  test("calls setLoading(true) on click", () => { ... })
  test("renders <Spinner /> when isLoading is true", () => { ... })
})
```

---

## Core conventions

**Query by role, not by implementation detail.**

```typescript
// ✅ Queries the user can see
screen.getByRole("button", { name: /checkout/i })
screen.getByLabelText("Email address")
screen.getByText("Your cart is empty")

// ❌ Queries tied to implementation
screen.getByTestId("checkout-btn")
container.querySelector(".checkout-button")
```

Only use `data-testid` as a last resort when no semantic query is available.

**Test all meaningful states.**

Every component with conditional rendering must have a test for each branch:

```typescript
describe("OrderList", () => {
  test("given loading, when rendered, then skeleton is shown")
  test("given empty orders, when rendered, then empty state is shown")
  test("given orders exist, when rendered, then order cards are shown")
  test("given fetch error, when rendered, then error message is shown")
})
```

**Async interactions:**

```typescript
// Use findBy* for elements that appear asynchronously
test("given valid form, when submitted, then success message appears", async () => {
  render(<ContactForm />)
  await userEvent.type(screen.getByLabelText("Email"), "test@example.com")
  await userEvent.click(screen.getByRole("button", { name: /submit/i }))
  expect(await screen.findByText("Message sent")).toBeInTheDocument()
})

// Use waitFor for assertions that require async settling
await waitFor(() => {
  expect(screen.getByRole("status")).toHaveTextContent("Saved")
})
```

Never use `setTimeout` or arbitrary delays to wait for async behavior.

---

## Mocking

**Mock API calls at the fetch/client boundary, not inside components.**

```typescript
// Mock the API client module
jest.mock("@/lib/api", () => ({
  fetchOrders: jest.fn().mockResolvedValue([
    { id: "order_1", status: "pending", total: 49.99 }
  ]),
}))
```

**Mock Next.js router when components use navigation:**

```typescript
jest.mock("next/navigation", () => ({
  useRouter: () => ({ push: jest.fn(), replace: jest.fn() }),
  usePathname: () => "/checkout",
}))
```

**Do not mock child components** unless they are genuinely expensive (network calls, canvas, etc.). Render the real component tree.

---

## Setup

```typescript
// jest.config.ts
export default {
  testEnvironment: "jsdom",
  setupFilesAfterFramework: ["@testing-library/jest-dom"],
  moduleNameMapper: {
    "^@/(.*)$": "<rootDir>/src/$1",   // match tsconfig path aliases
  },
  coverageThreshold: {
    global: { lines: 80, functions: 80, branches: 80 },
  },
}
```

---

## What not to do

- Do not query by `data-testid` unless no semantic query is available.
- Do not test implementation details (state variable values, internal function calls).
- Do not mock child components unless they are genuinely expensive.
- Do not use `setTimeout` or `waitFor` with arbitrary delays.
- Do not test framework behavior (Next.js routing, React lifecycle) — test your component's response to it.
- Do not skip testing error and empty states — these are always required.
- Do not use `container.querySelector` — use RTL queries.
