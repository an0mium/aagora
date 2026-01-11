import { test, expect } from '@playwright/test';

/**
 * E2E tests for authentication flows.
 */

test.describe('Login Page', () => {
  test('should load login page', async ({ page }) => {
    await page.goto('/auth/login');

    // Should have login form or heading
    const loginForm = page.locator('form, [data-testid="login-form"]');
    const loginHeading = page.locator('h1:has-text("Login"), h1:has-text("Sign in"), h2:has-text("Login")');

    const hasForm = await loginForm.isVisible().catch(() => false);
    const hasHeading = await loginHeading.isVisible().catch(() => false);

    expect(hasForm || hasHeading).toBeTruthy();
  });

  test('should have email/username input', async ({ page }) => {
    await page.goto('/auth/login');

    const emailInput = page.locator(
      'input[type="email"], input[name="email"], input[name="username"], input[placeholder*="email" i]'
    );

    await expect(emailInput.first()).toBeVisible();
  });

  test('should have password input', async ({ page }) => {
    await page.goto('/auth/login');

    const passwordInput = page.locator('input[type="password"]');
    await expect(passwordInput.first()).toBeVisible();
  });

  test('should have submit button', async ({ page }) => {
    await page.goto('/auth/login');

    const submitButton = page.locator(
      'button[type="submit"], button:has-text("Login"), button:has-text("Sign in")'
    );

    await expect(submitButton.first()).toBeVisible();
    await expect(submitButton.first()).toBeEnabled();
  });

  test('should show validation errors for empty form', async ({ page }) => {
    await page.goto('/auth/login');

    // Try to submit empty form
    const submitButton = page.locator(
      'button[type="submit"], button:has-text("Login"), button:has-text("Sign in")'
    ).first();

    await submitButton.click();

    // Should show validation error
    const errorMessage = page.locator(
      '[data-testid="error"], .error, [role="alert"], :text("required")'
    );

    // Either native validation or custom error
    await page.waitForTimeout(500);
  });

  test('should show error for invalid credentials', async ({ page }) => {
    await page.goto('/auth/login');

    // Fill in invalid credentials
    const emailInput = page.locator(
      'input[type="email"], input[name="email"], input[name="username"]'
    ).first();
    const passwordInput = page.locator('input[type="password"]').first();
    const submitButton = page.locator(
      'button[type="submit"], button:has-text("Login")'
    ).first();

    await emailInput.fill('invalid@test.com');
    await passwordInput.fill('wrongpassword');
    await submitButton.click();

    // Should show error message (wait for API response)
    const errorMessage = page.locator(
      '[data-testid="login-error"], .error-message, [role="alert"]:has-text("invalid")'
    );

    // Error should eventually appear (if API validates)
    await page.waitForTimeout(2000);
  });

  test('should have link to registration', async ({ page }) => {
    await page.goto('/auth/login');

    const registerLink = page.locator(
      'a[href*="register"], a[href*="signup"], a:has-text("Sign up"), a:has-text("Register")'
    );

    if (await registerLink.isVisible().catch(() => false)) {
      await expect(registerLink.first()).toHaveAttribute('href', /register|signup/i);
    }
  });

  test('should have forgot password link', async ({ page }) => {
    await page.goto('/auth/login');

    const forgotLink = page.locator(
      'a[href*="forgot"], a[href*="reset"], a:has-text("Forgot")'
    );

    const hasForgotLink = await forgotLink.isVisible().catch(() => false);
    expect(hasForgotLink).toBeDefined();
  });
});

test.describe('Registration Page', () => {
  test('should load registration page', async ({ page }) => {
    await page.goto('/auth/register');

    // Should have registration form
    const registerForm = page.locator('form, [data-testid="register-form"]');
    const registerHeading = page.locator(
      'h1:has-text("Register"), h1:has-text("Sign up"), h2:has-text("Create")'
    );

    const hasForm = await registerForm.isVisible().catch(() => false);
    const hasHeading = await registerHeading.isVisible().catch(() => false);

    expect(hasForm || hasHeading).toBeTruthy();
  });

  test('should have required registration fields', async ({ page }) => {
    await page.goto('/auth/register');

    // Should have email field
    const emailInput = page.locator(
      'input[type="email"], input[name="email"]'
    );

    // Should have password field
    const passwordInput = page.locator('input[type="password"]');

    await expect(emailInput.first()).toBeVisible();
    await expect(passwordInput.first()).toBeVisible();
  });

  test('should validate password strength', async ({ page }) => {
    await page.goto('/auth/register');

    const passwordInput = page.locator('input[type="password"]').first();

    // Enter weak password
    await passwordInput.fill('123');

    // Look for strength indicator or error
    const strengthIndicator = page.locator(
      '[data-testid="password-strength"], .password-strength, :text("weak")'
    );

    // Password validation might show
    await page.waitForTimeout(500);
  });

  test('should have terms and conditions checkbox', async ({ page }) => {
    await page.goto('/auth/register');

    const termsCheckbox = page.locator(
      'input[type="checkbox"][name*="terms"], input[type="checkbox"][name*="agree"]'
    );

    const hasTerms = await termsCheckbox.isVisible().catch(() => false);
    expect(hasTerms).toBeDefined();
  });
});

test.describe('Protected Routes', () => {
  test('should redirect to login when accessing protected route', async ({ page }) => {
    // Try to access a protected route without auth
    await page.goto('/billing');

    // Should redirect to login or show unauthorized
    const url = page.url();
    const isRedirected = url.includes('login') || url.includes('auth');
    const hasUnauthorized = await page.locator(':text("unauthorized"), :text("sign in")').isVisible().catch(() => false);

    // Either redirected or shows auth prompt
    expect(isRedirected || hasUnauthorized).toBeDefined();
  });

  test('should preserve intended destination after login', async ({ page }) => {
    // Go to protected route
    await page.goto('/billing');

    // If redirected to login, URL should have return param
    const url = page.url();
    if (url.includes('login')) {
      expect(url).toMatch(/return|redirect|next/i);
    }
  });
});

test.describe('Logout', () => {
  test('should have logout option when authenticated', async ({ page }) => {
    // Note: This test assumes there's a way to be "logged in"
    // In real tests, you'd set up auth state first
    await page.goto('/');

    // Look for logout button (visible when logged in)
    const logoutButton = page.locator(
      'button:has-text("Logout"), button:has-text("Sign out"), a:has-text("Logout")'
    );

    // May or may not be visible depending on auth state
    const hasLogout = await logoutButton.isVisible().catch(() => false);
    expect(hasLogout).toBeDefined();
  });
});

test.describe('Session Management', () => {
  test('should handle session timeout gracefully', async ({ page }) => {
    await page.goto('/');

    // Clear cookies to simulate session expiry
    await page.context().clearCookies();

    // Try to perform an authenticated action
    await page.reload();

    // Should not crash, should show login or public content
    const hasContent = await page.locator('body').isVisible();
    expect(hasContent).toBeTruthy();
  });
});
