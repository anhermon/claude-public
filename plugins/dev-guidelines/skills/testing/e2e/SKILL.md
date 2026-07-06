---
name: e2e
description: E2E and integration scenario testing conventions using Playwright. Covers BDD scenario structure, page objects, selector conventions, subset execution via tagging, and environment reuse to manage execution time. Use when writing or modifying Playwright tests.
license: MIT
compatibility: opencode
metadata:
  audience: developers
  workflow: testing
---

## What I do

I provide E2E testing conventions using Playwright. Always load `testing/` first for the tier model and BDD scenario convention — this skill covers the Playwright implementation.

---

## Stack

| Concern | Tool |
|---|---|
| E2E framework | Playwright |
| Test runner | Playwright test runner (`npx playwright test` / `bunx playwright test`) |
| Assertions | `expect` from `@playwright/test` |
| Fixtures | Playwright fixtures (extend base `test`) |

---

## Scenario structure — BDD

E2E tests are written as BDD scenarios. Each test maps to a user story or acceptance criterion.

```typescript
import { test, expect } from "../fixtures"

test.describe("Checkout flow", () => {

  test("given authenticated user with items in cart, when checkout initiated, then order confirmation shown",
    async ({ page, authenticatedUser }) => {
      await page.goto("/cart")
      await page.getByRole("button", { name: /checkout/i }).click()
      await page.getByLabel("Card number").fill("4242424242424242")
      await page.getByRole("button", { name: /pay now/i }).click()
      await expect(page.getByRole("heading", { name: /order confirmed/i })).toBeVisible()
    }
  )

  test("given unauthenticated user, when checkout page accessed, then redirected to login",
    async ({ page }) => {
      await page.goto("/checkout")
      await expect(page).toHaveURL(/\/login/)
    }
  )

})
```

**One scenario per test.** Do not chain multiple user journeys in a single test.

---

## Tagging for subset execution

Use Playwright tags to implement the layered switching pattern.

```typescript
test("given user logs in, when dashboard loads, then widgets are visible",
  { tag: ["@smoke"] },
  async ({ page }) => { ... }
)

test("given complex multi-step onboarding, when completed, then account is active",
  { tag: ["@full"] },
  async ({ page }) => { ... }
)
```

**Taskfile mapping:**
```yaml
tasks:
  test:e2e:smoke:
    cmd: bunx playwright test --grep @smoke

  test:e2e:full:
    cmd: bunx playwright test

  test:e2e:
    cmd: bunx playwright test --grep @smoke   # default to smoke in most CI contexts
```

**Smoke tag criteria:** covers the critical happy path for each major user-facing flow. Should complete in under 5 minutes. Everything else is `@full`.

---

## Page Object Model

Encapsulate page interactions in Page Objects. Tests describe scenarios; Page Objects describe how to interact with pages.

```typescript
// tests/pages/checkout.page.ts
import { Page, Locator, expect } from "@playwright/test"

export class CheckoutPage {
  readonly page: Page
  readonly cardNumberInput: Locator
  readonly payButton: Locator
  readonly confirmationHeading: Locator

  constructor(page: Page) {
    this.page = page
    this.cardNumberInput = page.getByLabel("Card number")
    this.payButton = page.getByRole("button", { name: /pay now/i })
    this.confirmationHeading = page.getByRole("heading", { name: /order confirmed/i })
  }

  async fillCard(number: string) {
    await this.cardNumberInput.fill(number)
  }

  async submitPayment() {
    await this.payButton.click()
    await expect(this.confirmationHeading).toBeVisible()
  }
}
```

```typescript
// In test
import { CheckoutPage } from "../pages/checkout.page"

test("...", async ({ page }) => {
  const checkout = new CheckoutPage(page)
  await checkout.fillCard("4242424242424242")
  await checkout.submitPayment()
})
```

Create a Page Object for any page or significant UI section that appears in more than one test.

---

## Selector conventions

Use semantic selectors in priority order:

1. `getByRole` — preferred for interactive elements
2. `getByLabel` — for form inputs
3. `getByText` — for content assertions
4. `getByTestId` — last resort only, when no semantic selector is available

```typescript
// ✅
page.getByRole("button", { name: /submit order/i })
page.getByLabel("Delivery address")

// ❌
page.locator(".submit-btn")
page.locator("#order-form > div:nth-child(3) > input")
```

When `getByTestId` is unavoidable, add `data-testid` attributes with consistent naming: `data-testid="checkout-submit-button"`.

---

## Fixtures — authentication and shared state

Extend Playwright's base `test` with fixtures to avoid repeating setup in every test.

```typescript
// tests/fixtures/index.ts
import { test as base } from "@playwright/test"

type Fixtures = {
  authenticatedUser: { userId: string; token: string }
}

export const test = base.extend<Fixtures>({
  authenticatedUser: async ({ page }, use) => {
    // Set auth state via API call — faster than UI login flow
    const response = await page.request.post("/api/auth/test-token", {
      data: { userId: "user_test_1" },
    })
    const { token } = await response.json()
    await page.context().addCookies([{ name: "auth_token", value: token, url: "http://localhost:3000" }])
    await use({ userId: "user_test_1", token })
  },
})

export { expect } from "@playwright/test"
```

**Never log in through the UI in every test.** Use API-based auth setup in fixtures — it is faster and more reliable.

---

## Environment reuse and execution time

**Use existing environments** rather than spinning up infrastructure per test run where possible. For integration-tier Playwright runs, target a shared staging environment. For local dev, target `localhost`.

**Parallelize across files, not within them.** Playwright runs test files in parallel by default. Keep related scenarios in the same file to share setup costs; keep unrelated flows in separate files to parallelize.

```typescript
// playwright.config.ts
export default defineConfig({
  workers: process.env.CI ? 4 : 2,           // more workers in CI
  fullyParallel: false,                        // parallel across files, sequential within
  retries: process.env.CI ? 1 : 0,            // one retry in CI to catch flakiness
  use: {
    baseURL: process.env.BASE_URL ?? "http://localhost:3000",
    trace: "on-first-retry",                   // capture trace only on failure retry
    video: "on-first-retry",
  },
})
```

**Shared DB / state:**
- Seed test data once per suite in `globalSetup`, not in `beforeEach`.
- Use isolated user accounts per test (created via API in fixture) — don't share mutable user state between tests.
- For read-only flows, reuse the same pre-seeded user across the suite.

---

## Waiting and flakiness

- Never use `page.waitForTimeout()` (arbitrary sleep) — this is the primary source of flakiness.
- Use `expect(locator).toBeVisible()` — Playwright auto-waits.
- For network-triggered state changes, use `page.waitForResponse()` or assert on the resulting UI change.
- For complex async flows, use `expect.poll()` with a reasonable timeout.

```typescript
// ✅ Auto-waits for element
await expect(page.getByText("Order confirmed")).toBeVisible()

// ✅ Wait for specific network call to complete
await Promise.all([
  page.waitForResponse(res => res.url().includes("/api/orders") && res.status() === 201),
  page.getByRole("button", { name: /pay/i }).click(),
])

// ❌ Arbitrary sleep
await page.waitForTimeout(2000)
```

---

## CI integration

```yaml
# azure-pipelines.yml — E2E stage
- stage: E2E
  dependsOn: Test
  jobs:
    - job: SmokeE2E
      steps:
        - script: task test:e2e:smoke
          displayName: 'E2E smoke suite'
          env:
            BASE_URL: $(STAGING_URL)

    - job: FullE2E
      condition: eq(variables['Build.Reason'], 'PullRequest')
      steps:
        - script: task test:e2e:full
          displayName: 'E2E full suite'
          env:
            BASE_URL: $(STAGING_URL)
```

Smoke E2E runs on every build. Full E2E runs on PRs only.

---

## What not to do

- Do not log in through the UI in every test — use API-based auth fixtures.
- Do not use `waitForTimeout` — use Playwright's auto-waiting assertions.
- Do not chain multiple user journeys in a single test.
- Do not use CSS selectors or nth-child queries — use semantic selectors.
- Do not spin up a new environment per test run — reuse a shared staging environment.
- Do not duplicate scenario coverage from the component tier in E2E — E2E covers the happy path and critical error paths only.
- Do not skip the Page Object pattern for flows that appear in more than one test.
