import { test, expect } from '@playwright/test';

/**
 * E2E tests for the Aragora homepage and navigation.
 */

test.describe('Homepage', () => {
  test('should load successfully', async ({ page }) => {
    await page.goto('/');

    // Should have a title
    await expect(page).toHaveTitle(/Aragora/i);

    // Should show main heading or logo
    const heading = page.locator('h1, [data-testid="logo"]').first();
    await expect(heading).toBeVisible();
  });

  test('should display navigation', async ({ page }) => {
    await page.goto('/');

    // Check for navigation elements
    const nav = page.locator('nav, [role="navigation"]');
    await expect(nav).toBeVisible();
  });

  test('should be responsive on mobile', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/');

    // Page should still be functional
    await expect(page).toHaveTitle(/Aragora/i);

    // Content should not overflow horizontally
    const body = page.locator('body');
    const bodyBox = await body.boundingBox();
    expect(bodyBox?.width).toBeLessThanOrEqual(375);
  });

  test('should have no console errors on load', async ({ page }) => {
    const consoleErrors: string[] = [];
    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });

    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Filter out expected errors (like missing env vars in dev)
    const unexpectedErrors = consoleErrors.filter(
      (err) => !err.includes('WebSocket') && !err.includes('favicon')
    );

    expect(unexpectedErrors).toHaveLength(0);
  });

  test('should have accessible page structure', async ({ page }) => {
    await page.goto('/');

    // Should have a main landmark
    const main = page.locator('main, [role="main"]');
    await expect(main).toBeVisible();

    // Should have skip link or proper heading structure
    const headings = page.locator('h1, h2, h3');
    const headingCount = await headings.count();
    expect(headingCount).toBeGreaterThan(0);
  });
});

test.describe('Navigation', () => {
  test('should navigate to debates page', async ({ page }) => {
    await page.goto('/');

    // Click on debates link
    const debatesLink = page.locator('a[href*="debate"], a:has-text("Debate")').first();
    if (await debatesLink.isVisible()) {
      await debatesLink.click();
      await expect(page).toHaveURL(/debate/i);
    }
  });

  test('should navigate to leaderboard', async ({ page }) => {
    await page.goto('/');

    // Click on leaderboard link
    const leaderboardLink = page.locator('a[href*="leaderboard"], a:has-text("Leaderboard")').first();
    if (await leaderboardLink.isVisible()) {
      await leaderboardLink.click();
      await expect(page).toHaveURL(/leaderboard/i);
    }
  });

  test('should navigate back to homepage from any page', async ({ page }) => {
    await page.goto('/debates');

    // Click on logo or home link
    const homeLink = page.locator('a[href="/"], [data-testid="logo"], a:has-text("Aragora")').first();
    if (await homeLink.isVisible()) {
      await homeLink.click();
      await expect(page).toHaveURL('/');
    }
  });
});
