import { Page, expect } from '@playwright/test';

export interface TestUser {
  email: string;
  password: string;
}

export async function registerUser(page: Page, user: TestUser): Promise<void> {
  await page.goto('/register');
  await page.fill('[name="email"]', user.email);
  await page.fill('[name="password"]', user.password);
  await page.click('button[type="submit"]');
  
  // Wait for redirect to todos page after successful registration
  await page.waitForURL('/todos', { timeout: 10000 });
}

export async function loginUser(page: Page, user: TestUser): Promise<void> {
  await page.goto('/login');
  await page.fill('[name="email"]', user.email);
  await page.fill('[name="password"]', user.password);
  await page.click('button[type="submit"]');
  
  // Wait for redirect to todos page
  await page.waitForURL('/todos', { timeout: 10000 });
}

export async function logoutUser(page: Page): Promise<void> {
  await page.click('button:has-text("Logout"), button:has-text("Log out")');
  await page.waitForURL(/\/(login|register)/, { timeout: 5000 });
}

export async function createTodo(page: Page, title: string, description?: string): Promise<void> {
  // Find the input for adding a new todo
  const todoInput = page.locator('input[placeholder*="Add"], input[placeholder*="new todo"]').first();
  await todoInput.fill(title);
  
  // If description field exists, fill it
  if (description) {
    const descInput = page.locator('input[name="description"], textarea[name="description"]').first();
    if (await descInput.count() > 0) {
      await descInput.fill(description);
    }
  }
  
  // Click add button
  await page.click('button:has-text("Add")');
  
  // Wait for todo to appear
  await expect(page.locator(`text=${title}`).first()).toBeVisible({ timeout: 5000 });
}

export async function toggleTodoCompletion(page: Page, todoTitle: string): Promise<void> {
  // Find the todo item and click its checkbox
  const todoItem = page.locator(`[data-testid="todo-item"]:has-text("${todoTitle}")`).first();
  const checkbox = todoItem.locator('input[type="checkbox"], [role="checkbox"]').first();
  await checkbox.click();
}

export function generateUniqueEmail(): string {
  return `test${Date.now()}${Math.random().toString(36).substring(7)}@example.com`;
}
