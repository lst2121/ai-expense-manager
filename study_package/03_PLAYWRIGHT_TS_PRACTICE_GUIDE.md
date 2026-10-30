# 🎭 PLAYWRIGHT & TYPESCRIPT: COMPREHENSIVE SDET MASTERY GUIDE
**Target**: Complete Architecture, Setup, Locators, Web-First Assertions, POM, Fixtures & CI Execution  
**Candidate**: Lokender Singh (8+ yrs Exp)  
*Note: This is an exhaustive, self-contained reference and practice guide. It explains every internal concept from initial installation through advanced enterprise framework patterns with zero spoilers for your code challenges.*

---

## 1. Installation & Environment Setup from Scratch

### Prerequisites
- **Node.js**: LTS version (v18, v20, or v24). Check via `node -v` and `npm -v`.
- **Operating System**: Windows, macOS, or Linux.

### Method A: Initialize a Brand New Playwright Project
To create a clean Playwright project in a fresh directory:
```bash
npm init playwright@latest
```
*Prompts during interactive setup*:
- Do you want to use TypeScript or JavaScript? $\rightarrow$ **TypeScript**
- Where to put your end-to-end tests? $\rightarrow$ **e2e** or **tests**
- Add a GitHub Actions workflow? $\rightarrow$ **Yes**
- Install Playwright browsers? $\rightarrow$ **Yes** (Runs `npx playwright install`)

### Method B: Adding Playwright to an Existing Repository (Our Workspace)
If you already have a repository (like our `frontend/` directory):
```bash
# 1. Install Playwright Test runner and TypeScript typings as devDependencies
npm install -D @playwright/test typescript @types/node

# 2. Download browser binaries (Chromium, Firefox, WebKit) and OS dependencies
npx playwright install --with-deps chromium
```

### Essential CLI Execution Commands
| Command | What It Does |
| :--- | :--- |
| `npx playwright test` | Runs all tests in headless mode across all configured projects. |
| `npx playwright test --headed` | Launches visible browser windows (great for local debugging). |
| `npx playwright test --project=chromium` | Runs tests only against Chromium (skips Firefox/WebKit). |
| `npx playwright test e2e/tests/auth.spec.ts` | Runs an individual test spec file. |
| `npx playwright test -g "bilingual switch"` | Runs tests matching a specific title regex (`-g` or `--grep`). |
| `npx playwright test --debug` | Launches the interactive **Playwright Inspector** (step through test line-by-line). |
| `npx playwright test --ui` | Launches Playwright's **Interactive UI Mode** (time-travel, watch mode, locators). |
| `npx playwright show-report` | Serves the generated HTML test report on a local port. |
| `npx playwright show-trace path/to/trace.zip` | Opens the standalone **Trace Viewer** for post-mortem failure triage. |

---

## 2. Core Architecture: Why Playwright Outperforms Selenium & Cypress

### The WebSocket Connection vs. HTTP WebDriver Protocol
- **Selenium**: Uses the W3C WebDriver wire protocol over HTTP. Every command (`click`, `findElement`) is an independent HTTP request transmitted to a driver binary (`chromedriver.exe`), which then talks to the browser. Under network jitter, high test concurrency, or CI load, this causes protocol latency, connection timeouts, and synchronization failures.
- **Playwright**: Communicates directly with the browser engine through a single, persistent, bidirectional **WebSocket connection** using native browser debugging protocols (Chrome DevTools Protocol for Chromium, and equivalent native protocol layers for Firefox and WebKit).
- **The Result**: Real-time event notifications (DOM changes, network requests, console errors) are streamed instantly to Playwright without polling.

### The 3 Core Primitives: Browser $\rightarrow$ BrowserContext $\rightarrow$ Page
Understanding this hierarchy is a mandatory interview question:

```
[ Browser Instance: e.g. chromium.exe (Heavy OS Process, ~150MB-300MB RAM) ]
   │
   ├── [ BrowserContext 1 ] (Isolated Incognito Sandbox: own Cookies, localStorage, Cache)
   │      ├── Page 1 (Tab A)
   │      └── Page 2 (Tab B)
   │
   └── [ BrowserContext 2 ] (Completely isolated Incognito Sandbox)
          └── Page 3 (Tab C)
```

1. **`Browser`**: A physical operating system process launched by Playwright (e.g. headless Chrome). Spinning up a browser takes ~300ms–800ms.
2. **`BrowserContext`**: A lightweight, isolated incognito session within an existing `Browser`. Creating a `BrowserContext` takes **less than 5 milliseconds**.
   - Playwright automatically creates a fresh `BrowserContext` for **every single test function**.
   - Cookies, local storage, session storage, and cache do NOT leak between tests.
   - Tests run completely isolated in parallel without spinning up 20 heavy browser executables.
3. **`Page`**: A single browser tab or window within a `BrowserContext`.

---

## 3. Configuration Deep Dive (`playwright.config.ts`)

The configuration file is the central nervous system of your framework:

```typescript
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  // Root directory where test files (.spec.ts) are located
  testDir: './e2e',

  // Maximum time (ms) a single test can run before timing out
  timeout: 30 * 1000, // 30 seconds

  // Web-first assertion retry timeout
  expect: {
    timeout: 5000, // 5 seconds
  },

  // Run tests within each file in parallel
  fullyParallel: true,

  // Fail CI build if test.only() was accidentally left in code
  forbidOnly: !!process.env.CI,

  // Retry failed tests in CI to handle transient network blips
  retries: process.env.CI ? 2 : 0,

  // Number of parallel worker processes
  workers: process.env.CI ? 2 : undefined,

  // Reporter formats: list for CLI output, html for rich failure artifacts
  reporter: [
    ['list'],
    ['html', { outputFolder: 'playwright-report', open: 'never' }]
  ],

  // Shared settings for all projects
  use: {
    // Prepended to page.goto('/login') -> http://localhost:5173/login
    baseURL: 'http://localhost:5173',

    // Record complete trace file only when a test fails on its first run
    trace: 'on-first-retry',

    // Take screenshot on failure
    screenshot: 'only-on-failure',

    // Record video on failure
    video: 'retain-on-failure',

    // Standard viewport resolution
    viewport: { width: 1280, height: 720 },

    // Bypass HTTPS certificate errors in staging
    ignoreHTTPSErrors: true,
  },

  // Multi-browser execution matrix
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
    },
    {
      name: 'mobile-chrome',
      use: { ...devices['Pixel 7'] },
    },
  ],

  // Automatically start local web server before running tests
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:5173',
    reuseExistingServer: !process.env.CI,
    timeout: 60 * 1000,
  },
});
```

---

## 4. Locators & Strict Mode Mastery

### Why User-Facing Locators Beat XPath and CSS
In legacy frameworks, testers wrote brittle selectors:
```typescript
// ❌ Brittle XPath/CSS (Brakes when designers change layout/classes):
page.locator('//div[@id="main"]/div[2]/form/div[3]/button');
page.locator('.btn-primary.submit-v2');
```
Playwright advocates **Accessibility-First (User-Facing) Locators** that mimic how real users and assistive screen-readers interact with the application:

1. **`page.getByRole(role, { name: ... })`** (The Gold Standard):
   - Targets elements by their ARIA accessibility role (`button`, `heading`, `link`, `checkbox`, `dialog`, `textbox`, `combobox`, `alert`).
   - *Example*: `page.getByRole('button', { name: 'Post to Ledger' })`
   - *Example*: `page.getByRole('heading', { level: 2, name: 'Transactions' })`
2. **`page.getByLabel(text)`**:
   - Locates form inputs associated with a `<label>`.
   - *Example*: `page.getByLabel('Date of Birth')`
3. **`page.getByPlaceholder(text)`**:
   - Locates `<input>` or `<textarea>` by placeholder text.
   - *Example*: `page.getByPlaceholder('e.g. AWS Cloud Infrastructure')`
4. **`page.getByText(text, { exact: false })`**:
   - Locates elements containing visible text content.
5. **`page.getByTestId(id)`**:
   - Locates elements with `data-testid="submit-btn"` (great for dynamic custom widgets where ARIA roles are ambiguous).

### Strict Mode Mechanics
By default, Playwright locators operate in **Strict Mode**:
- If a locator matches **more than one element**, invoking an action (`click()`, `fill()`) immediately throws a `Strict Mode Violation` error.
- **Why this is beneficial**: It prevents tests from silently interacting with the wrong element when two buttons share the same name.
- **How to resolve Strict Mode cleanly**:
  1. *Filter by child text*: `page.locator('tr').filter({ hasText: 'Swiggy' })`
  2. *Filter by child element*: `page.locator('tr').filter({ has: page.getByRole('button', { name: 'Delete' }) })`
  3. *Scope within a parent container*: `modal.getByRole('button', { name: 'Cancel' })`
  4. *Explicit index*: `locator.first()`, `locator.last()`, `locator.nth(2)`

### Interacting with Complex DOM Elements

#### 1. Dropdowns (`<select>`)
```typescript
await page.locator('select#category').selectOption('healthcare');
await page.locator('select#category').selectOption({ label: 'Health & Pharmacy' });
```

#### 2. Checkboxes & Radio Buttons
```typescript
await page.getByLabel('Agree to Terms').check();
expect(await page.getByLabel('Agree to Terms').isChecked()).toBe(true);
```

#### 3. File Uploads (File Inputs)
Playwright handles `<input type="file">` without needing OS dialog automation:
```typescript
await page.locator('input[type="file"]').setInputFiles('path/to/statement.csv');
// For multiple files:
await page.locator('input[type="file"]').setInputFiles(['file1.pdf', 'file2.pdf']);
```

#### 4. Iframes (`frameLocator`)
Playwright can effortlessly pierce iframes:
```typescript
const paymentFrame = page.frameLocator('iframe#stripe-frame');
await paymentFrame.getByPlaceholder('Card Number').fill('424242424242');
```

#### 5. Shadow DOM
Unlike Selenium, **Playwright automatically pierces Open and Closed Shadow DOM trees by default!** You do not need `shadowRoot` scripts.

#### 6. Native Browser Dialogs (Alerts / Confirms)
```typescript
page.on('dialog', async (dialog) => {
  console.log(`Alert message: ${dialog.message()}`);
  await dialog.accept(); // or dialog.dismiss()
});
await page.getByRole('button', { name: 'Delete Account' }).click();
```

#### 7. Handling Popups / New Tabs
```typescript
const [newPage] = await Promise.all([
  context.waitForEvent('page'),
  page.getByRole('link', { name: 'Terms of Service' }).click()
]);
await newPage.waitForLoadState();
expect(newPage.url()).toContain('/terms');
```

---

## 5. Auto-Waiting & Web-First Assertions

### The 5 Actionability Checks
Before performing any action (`click()`, `fill()`, `check()`), Playwright automatically runs a series of checks on the target element:
1. **Attached**: The element is connected to the Document Object Model (DOM).
2. **Visible**: The element has non-zero dimensions and is not hidden by CSS (`display: none`, `visibility: hidden`).
3. **Stable**: The element is not animating, scrolling, or shifting positions.
4. **Enabled**: The element does not have the `disabled` attribute.
5. **Editable**: The element can accept text input.
6. **Receiving Pointer Events**: The element is not obscured by a floating modal backdrop, spinner, or sticky header.

### Why `page.waitForTimeout()` is Forbidden in Senior Code
- `waitForTimeout(5000)` halts the test execution for 5,000ms regardless of whether the element took 100ms or 4,900ms to load.
- In CI, under high CPU load, 5,000ms may not be enough, causing flaky tests.
- **The Senior SDET Pattern**: Always use **Web-First Assertions** (`expect(locator)`):
  Web-first assertions **automatically poll and auto-retry** the check until the condition becomes true or the 5,000ms timeout expires.

### Web-First Assertions Cheatsheet
| Assertion | What It Verifies |
| :--- | :--- |
| `await expect(locator).toBeVisible()` | Element is attached and visible on the page. |
| `await expect(locator).toBeHidden()` | Element is either detached or hidden. |
| `await expect(locator).toBeEnabled()` | Element is interactive (not disabled). |
| `await expect(locator).toBeChecked()` | Checkbox or radio button is checked. |
| `await expect(locator).toHaveText('Welcome')` | Exact visible inner text matches string or regex. |
| `await expect(locator).toContainText('Swiggy')` | Element contains substring. |
| `await expect(locator).toHaveValue('Swiggy')` | Input field has current value attribute. |
| `await expect(locator).toHaveAttribute('href', '/login')` | Attribute has specific value. |
| `await expect(locator).toHaveClass(/bg-indigo-600/)` | CSS class matches regex. |
| `await expect(locator).toHaveCount(15)` | Locator resolves to exactly 15 matching elements. |
| `await expect(page).toHaveURL(/.*dashboard/)` | Current browser page URL matches pattern. |
| `await expect(page).toHaveTitle(/Optum Healthcare/)` | Page document title matches. |

---

## 6. Page Object Model (POM) & Component Object Model (COM)

The Page Object Model encapsulates page locators and interaction logic into reusable TypeScript classes.

### Architectural Rules:
1. **Keep Locators in Constructor**: Locators are declared in the constructor as properties. They are evaluated lazily.
2. **Expose Intent, Not Implementation**: Write `login(email, password)`, not `clickEmailInput()`, `typeText()`, `clickSubmitButton()`.
3. **Return Promises**: Every async action must return `Promise<void>` or return the next Page Object (`Promise<DashboardPage>`).
4. **Do Not Over-Abstract Assertions**: Expose locators as `readonly` properties so that tests can make explicit, descriptive `expect()` assertions.
5. **Component Objects**: Break huge pages into sub-components (`SidebarComponent`, `NavbarComponent`, `ModalComponent`).

---

## 7. Custom Fixtures (`test.extend`) Deep Dive

### How Dependency Injection Works in `@playwright/test`
Instead of writing repetitive `beforeEach` and `afterEach` hooks that leak state between tests, Playwright uses **Fixtures**.

### Anatomy of a Custom Fixture:
```typescript
import { test as base, Page } from '@playwright/test';
import { LoginPage } from '../pages/login.page';

interface MyFixtures {
  loginPage: LoginPage;
  authenticatedPage: Page;
}

export const test = base.extend<MyFixtures>({
  // Fixture 1: Instantiates a page object
  loginPage: async ({ page }, use) => {
    const login = new LoginPage(page);
    await login.navigateTo();
    await use(login); // hands off to test
  },

  // Fixture 2: Injects authentication and provides automatic teardown
  authenticatedPage: async ({ page }, use) => {
    // 1. SETUP
    await page.goto('/');
    await page.evaluate(() => localStorage.setItem('auth_token', 'mock_jwt'));
    
    // 2. HANDOFF TO TEST
    await use(page);

    // 3. TEARDOWN (Guaranteed to execute even if test fails!)
    await page.evaluate(() => localStorage.clear());
  },
});
```

---

## 8. API Testing via `Playwright APIRequestContext`

Playwright can execute HTTP requests directly without launching a browser:
```typescript
import { test, expect } from '@playwright/test';

test('verify transaction API contract', async ({ request }) => {
  const response = await request.post('/api/transactions', {
    data: {
      description: 'Pharmacy Supplies',
      amount: 1500.0,
      category: 'healthcare'
    },
    headers: {
      Authorization: `Bearer ${token}`
    }
  });

  expect(response.status()).toBe(201);
  const json = await response.json();
  expect(json.status).toBe('success');
  expect(json.data.amount).toBe(1500.0);
});
```
- **SDET Advantage**: You can use `request` inside a fixture to seed 50 database records in 200ms via REST API, then open the browser to verify UI rendering, speeding up test suites by 10x!

---

## 9. Debugging, Tracing & CI Execution

### The Playwright Trace Viewer
The Trace Viewer captures a full recorded post-mortem of the test run:
- **DOM Snapshots**: Inspect the exact DOM state before and after every single click or fill action.
- **Actionability Logs**: See why an auto-wait check failed or stalled.
- **Console Logs & Network Traffic**: Full request/response bodies, headers, and HTTP status codes.
- **Timeline**: Visual filmstrip of screenshots showing browser rendering frame-by-frame.
- *Open Trace*: `npx playwright show-trace test-results/path/to/trace.zip` or drag-and-drop into [trace.playwright.dev](https://trace.playwright.dev).

### CI / CD Troubleshooting (Passes Locally, Fails in CI)
When a test fails in CI but passes locally, check:
1. **Headless vs Headed Timing**: Headless execution runs much faster; race conditions in front-end JavaScript render faster or slower.
2. **Viewport Size**: Local headed opens your monitor's native size; CI defaults to `1280x720`, which may collapse buttons into a mobile hamburger menu!
3. **Resource Throttling**: CI runners (Docker/GitHub Actions) have limited CPU/RAM, causing rendering delays (solved by tuning `expect.timeout`).
4. **Timezones**: CI runs in UTC, causing date picker assertions to fail if code assumes local IST.

---

## 10. Your Step-by-Step Hands-On Practice Milestones

Build these files from scratch inside **`automation/ui/`**:

### Milestone 1: Core BasePage & Fixtures
1. Create `automation/ui/pages/base.page.ts`:
   - Class `BasePage` receiving `readonly page: Page`.
   - `navigateTo(path: string = '/')`
   - `waitForVisible(locator: Locator, timeoutMs = 7000)`
   - `injectAuthSession(token: string, user: object)` via `page.evaluate()`.
2. Create `automation/ui/fixtures/test.fixtures.ts`:
   - Extend `base.extend<CustomFixtures>()` with `authenticatedPage`.

### Milestone 2: Auth Page & Spec
1. Create `automation/ui/pages/auth.page.ts` with locators using `getByPlaceholder` and `getByRole`.
2. Implement `login(email, password)`.
3. Create `automation/ui/tests/auth.spec.ts` asserting valid and invalid login flows.

### Milestone 3: Ledger Table Page & Spec
1. Create `automation/ui/pages/ledger.page.ts` with:
   - `addEntryBtn = page.getByRole('button', { name: 'Add Entry' })`
   - Form inputs: description, amount, category select, submit button.
   - Category filter dropdown.
   - Dynamic row locator helper: `getTableRowByText(text: string): Locator`.
2. Create `automation/ui/tests/ledger.spec.ts` creating an expense and asserting row presence.
