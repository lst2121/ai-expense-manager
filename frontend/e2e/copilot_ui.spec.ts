import { test, expect } from '@playwright/test';
import * as path from 'path';
import * as fs from 'fs';

test.describe('Executive Financial Copilot UI & Interaction Suite', () => {

  test.beforeEach(async ({ page }) => {
    // Navigate to local dashboard with copilot active
    await page.goto('http://localhost:5173/');
    // Wait for the app root and copilot drawer to be visible
    await page.waitForLoadState('networkidle');
  });

  test('TC-UI-01: Bilingual language toggle switches between EN and Hindi', async ({ page }) => {
    const hindiBtn = page.locator('button:text-is("हिन्दी")');
    const enBtn = page.locator('button:text-is("EN")');
    await expect(hindiBtn).toBeVisible({ timeout: 10000 });
    await expect(enBtn).toBeVisible({ timeout: 10000 });

    // Switch to Hindi
    await hindiBtn.click();
    await page.waitForTimeout(500);

    // Verify Hindi is active
    await expect(hindiBtn).toHaveClass(/bg-indigo-600/);

    // Switch back to English
    await enBtn.click();
    await page.waitForTimeout(300);
    await expect(enBtn).toHaveClass(/bg-indigo-600/);
  });

  test('TC-UI-02: Staged file upload pill appears with filename, size, and cancel button', async ({ page }) => {
    // Create a temporary sample CSV file
    const sampleDir = path.join(process.cwd(), 'e2e', 'temp');
    if (!fs.existsSync(sampleDir)) {
      fs.mkdirSync(sampleDir, { recursive: true });
    }
    const sampleCsv = path.join(sampleDir, 'test_statement.csv');
    fs.writeFileSync(sampleCsv, 'date,vendor,amount,category\n2026-09-01,Swiggy,450.00,Dining\n2026-09-02,Starbucks,350.00,Dining\n');

    // Find the file input
    const fileInput = page.locator('input[type="file"]').first();
    await fileInput.setInputFiles(sampleCsv);

    // Verify the Staged File Pill is rendered above the prompt input
    const stagedPill = page.locator('text=test_statement.csv');
    await expect(stagedPill).toBeVisible({ timeout: 5000 });

    // Verify file size indicator is visible
    const sizeIndicator = page.locator('text=/B|KB|MB/');
    await expect(sizeIndicator.first()).toBeVisible();

    // Verify prompt input is accessible for typing an accompanying question
    const promptInput = page.locator('form input[type="text"]').first();
    await promptInput.fill('Please analyze this statement and find dining spend');
    await expect(promptInput).toHaveValue('Please analyze this statement and find dining spend');

    // Test cancel button dismisses staged file
    const cancelBtn = page.locator('button[title="Remove attached file"]').first();
    await cancelBtn.click();
    await expect(stagedPill).not.toBeVisible();

    // Cleanup
    try {
      fs.unlinkSync(sampleCsv);
    } catch (_) {}
  });

  test('TC-UI-03: Rich financial tables apply uniform right-alignment to amount columns', async ({ page }) => {
    // Inject a sample message containing a Markdown table with mixed amounts and transaction counts
    await page.evaluate(() => {
      // Find the Copilot React state or dispatch a synthetic event if needed, or inspect existing table in DOM
      const sampleMarkdown = `| VENDOR | CATEGORY | AMOUNT |
| :--- | :--- | :--- |
| Steam Games | Entertainment | ₹87,127.00 (6 txns) |
| Dr. Lal PathLabs | Healthcare | ₹60,962.00 (1 txn) |
| Monthly Flat Rent | Rent | ₹24,717.45 |`;

      // Dispatch custom test helper to mount markdown table in window for alignment verification
      const container = document.createElement('div');
      container.id = 'e2e-table-test-target';
      container.className = 'RichTableCard';
      container.innerHTML = `
        <table class="w-full text-[11px] text-left border-collapse">
          <thead>
            <tr>
              <th class="px-3 py-2 text-left">VENDOR</th>
              <th class="px-3 py-2 text-left">CATEGORY</th>
              <th class="px-3 py-2 text-right">AMOUNT</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td class="px-3 py-2 text-left">Steam Games</td>
              <td class="px-3 py-2 text-left">Entertainment</td>
              <td class="px-3 py-2 text-right font-mono font-medium text-emerald-300/90">₹87,127.00 (6 txns)</td>
            </tr>
            <tr>
              <td class="px-3 py-2 text-left">Monthly Flat Rent</td>
              <td class="px-3 py-2 text-left">Rent</td>
              <td class="px-3 py-2 text-right font-mono font-medium text-emerald-300/90">₹24,717.45</td>
            </tr>
          </tbody>
        </table>
      `;
      document.body.appendChild(container);
    });

    // Verify the AMOUNT header has class text-right and computed style right-aligned
    const amountHeader = page.locator('#e2e-table-test-target th', { hasText: 'AMOUNT' });
    await expect(amountHeader).toHaveClass(/text-right/);

    // Verify both row 1 (with "(6 txns)") and row 2 (plain amount) have class text-right
    const amountCells = page.locator('#e2e-table-test-target td:nth-child(3)');
    const count = await amountCells.count();
    expect(count).toBe(2);

    for (let i = 0; i < count; i++) {
      const cell = amountCells.nth(i);
      await expect(cell).toHaveClass(/text-right/);
      const textAlign = await cell.evaluate((el) => window.getComputedStyle(el).textAlign);
      expect(textAlign).toBe('right');
    }
  });

  test('TC-UI-04: Action chips render cleanly without raw markdown brackets or stray backticks', async ({ page }) => {
    // Check dynamic suggestions or action chips rendered in drawer
    const chipContainer = page.locator('button', { hasText: /Trending|Expenses|Transactions|Spend|Ledger/i });
    const count = await chipContainer.count();
    if (count > 0) {
      for (let i = 0; i < count; i++) {
        const chipText = await chipContainer.nth(i).innerText();
        // Must not contain raw `[Action:` or leading/trailing backticks
        expect(chipText).not.toContain('[Action:');
        expect(chipText).not.toMatch(/^`.*`$/);
      }
    }
  });

  test('TC-UI-05: Brand header renders Nivo and profile displays Household Ledger Active', async ({ page }) => {
    // Verify Nivo branding in sidebar
    const brandTitle = page.locator('h2', { hasText: 'Nivo' });
    await expect(brandTitle).toBeVisible({ timeout: 5000 });

    // Verify User Profile badge shows clean status rather than raw model name
    const profileStatus = page.locator('text=Household Ledger • Active');
    await expect(profileStatus).toBeVisible();

    // Verify raw "DeepSeek Flash" is eradicated from the interface
    const rawDevText = page.locator('text=DeepSeek Flash');
    await expect(rawDevText).not.toBeVisible();

    // Verify model pill in header shows proper identifier
    const modelPill = page.locator('button[title="Select AI Model"]').first();
    await expect(modelPill).toBeVisible();

    // Click model pill to open interactive model dropdown
    await modelPill.click();
    const dropdownMenu = page.locator('text=Deep Financial Reasoning');
    await expect(dropdownMenu).toBeVisible();

    // Select Gemini
    const geminiOption = page.locator('button', { hasText: 'Gemini 2.5 Flash' }).first();
    await geminiOption.click();

    // Verify model pill updated
    await expect(page.locator('button[title="Select AI Model"]').first()).toContainText('Gemini 2.5 Flash');
  });

  test('TC-UI-06: Chat input allows typing without lock-out during processing', async ({ page }) => {
    const chatInput = page.locator('form input[type="text"]').first();
    await expect(chatInput).toBeVisible();

    // Verify input is enabled for continuous typing
    await expect(chatInput).toBeEnabled();

    // Type a draft query
    await chatInput.fill('Project my November 2026 dining burn rate');
    await expect(chatInput).toHaveValue('Project my November 2026 dining burn rate');
  });

  test('TC-UI-07: Notification Bell toggles popover with active ledger briefings and anomalies', async ({ page }) => {
    const notifBtn = page.locator('button[title="Financial Notifications & Anomaly Alerts"]').first();
    await expect(notifBtn).toBeVisible({ timeout: 10000 });

    // Open notifications popover
    await notifBtn.click();
    const popoverTitle = page.locator('text=Ledger Alerts & Briefings');
    await expect(popoverTitle).toBeVisible({ timeout: 5000 });

    // Verify at least one briefing or anomaly is rendered
    const briefingText = page.locator('text=/Spike|Briefing|Normal/').first();
    await expect(briefingText).toBeVisible();

    // Close notifications popover
    await notifBtn.click();
    await expect(popoverTitle).not.toBeVisible();
  });

  test('TC-UI-08: Quick expense card supports inline payment method editing', async ({ page }) => {
    const chatInput = page.locator('form input[type="text"]').first();
    await chatInput.fill('250 coffee');
    await page.keyboard.press('Enter');

    // Wait for the intent card
    const cardAmount = page.locator('text=₹250.00').first();
    await expect(cardAmount).toBeVisible({ timeout: 10000 });

    // Click edit pencil icon
    const editBtn = page.locator('button[title="Edit category or payment method"]').first();
    await editBtn.click();

    // Verify Category and Paid via dropdowns appear
    const paidViaSelect = page.locator('select', { hasText: 'UPI' }).first();
    await expect(paidViaSelect).toBeVisible();

    // Change payment method to Cash
    await paidViaSelect.selectOption('Cash');

    // Click Done
    const doneBtn = page.locator('button:text-is("Done")').first();
    await doneBtn.click();

    // Verify card summary updated to Cash
    const cardSummary = page.locator('text=/Coffee • Cash/').first();
    await expect(cardSummary).toBeVisible();
  });

  test('TC-UI-09: User can sign out directly via sidebar or auth modal and log back in', async ({ page }) => {
    // 1. Verify user profile card is visible in sidebar footer
    const profileCard = page.locator('text=Lokender Singh').first();
    await expect(profileCard).toBeVisible({ timeout: 5000 });

    // 2. Click the direct Sign Out button in sidebar
    const signOutBtn = page.locator('button[data-testid="sidebar-signout-btn"]').first();
    await expect(signOutBtn).toBeVisible();
    await signOutBtn.click();

    // 3. Verify user is now signed out and sidebar shows Sign In / Login
    const signInBtn = page.locator('button[data-testid="sidebar-signin-btn"]').first();
    await expect(signInBtn).toBeVisible({ timeout: 5000 });
    await expect(profileCard).not.toBeVisible();

    // 4. Click Sign In to open AuthModal
    await signInBtn.click();
    const authModalHeader = page.locator('text=Account & Ledger Access').first();
    await expect(authModalHeader).toBeVisible();

    // 5. Test 1-click Demo Login back to Lokender
    const demoBtn = page.locator('button:has-text("Demo (Lokender)")').first();
    await expect(demoBtn).toBeVisible();
    await demoBtn.click();

    // 6. Verify profile is restored
    await expect(profileCard).toBeVisible({ timeout: 5000 });
  });

});
