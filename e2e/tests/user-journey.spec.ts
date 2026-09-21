import { test, expect } from '@playwright/test';
import { 
  registerUser, 
  loginUser, 
  logoutUser, 
  createTodo, 
  toggleTodoCompletion,
  generateUniqueEmail,
  type TestUser 
} from '../fixtures/user-helpers';

test.describe('Full User Journey', () => {
  let testUser: TestUser;

  test.beforeEach(() => {
    testUser = {
      email: generateUniqueEmail(),
      password: 'Test@123456',
    };
  });

  test('Complete user flow: Register → Login → Create Todo → Toggle → Logout', async ({ page }) => {
    // Step 1: Register
    await registerUser(page, testUser);
    await expect(page).toHaveURL('/todos');
    
    // Verify we're on the todos page
    await expect(page.locator('h1, h2').filter({ hasText: /todos/i }).first()).toBeVisible();

    // Step 2: Create a todo
    const todoTitle = 'Buy groceries';
    await createTodo(page, todoTitle);
    
    // Verify todo appears in the list
    await expect(page.locator(`text=${todoTitle}`).first()).toBeVisible();

    // Step 3: Toggle completion
    await toggleTodoCompletion(page, todoTitle);
    
    // Wait a bit for the update to process
    await page.waitForTimeout(1000);
    
    // Verify the todo is marked as completed (checkbox should be checked)
    const todoItem = page.locator('[data-testid="todo-item"]').filter({ hasText: todoTitle }).first();
    const checkbox = todoItem.locator('input[type="checkbox"], [role="checkbox"]').first();
    await expect(checkbox).toBeChecked();

    // Step 4: Logout
    await logoutUser(page);
    await expect(page).toHaveURL(/\/(login|register)/);

    // Step 5: Login again
    await loginUser(page, testUser);
    await expect(page).toHaveURL('/todos');

    // Step 6: Verify todo persisted
    await expect(page.locator(`text=${todoTitle}`).first()).toBeVisible();
  });

  test('User can create multiple todos and see them all', async ({ page }) => {
    await registerUser(page, testUser);

    // Create multiple todos
    const todos = ['Task 1', 'Task 2', 'Task 3'];
    
    for (const todo of todos) {
      await createTodo(page, todo);
    }

    // Verify all todos are visible
    for (const todo of todos) {
      await expect(page.locator(`text=${todo}`).first()).toBeVisible();
    }
  });

  test('User can toggle todo completion status multiple times', async ({ page }) => {
    await registerUser(page, testUser);

    const todoTitle = 'Toggle test todo';
    await createTodo(page, todoTitle);

    const todoItem = page.locator('[data-testid="todo-item"]').filter({ hasText: todoTitle }).first();
    const checkbox = todoItem.locator('input[type="checkbox"], [role="checkbox"]').first();

    // Initially should be unchecked
    await expect(checkbox).not.toBeChecked();

    // Toggle to completed
    await toggleTodoCompletion(page, todoTitle);
    await page.waitForTimeout(500);
    await expect(checkbox).toBeChecked();

    // Toggle back to not completed
    await toggleTodoCompletion(page, todoTitle);
    await page.waitForTimeout(500);
    await expect(checkbox).not.toBeChecked();
  });
});
