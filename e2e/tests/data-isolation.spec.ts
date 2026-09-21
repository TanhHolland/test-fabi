import { test, expect } from '@playwright/test';
import { 
  registerUser, 
  logoutUser, 
  loginUser,
  createTodo, 
  generateUniqueEmail,
  type TestUser 
} from '../fixtures/user-helpers';

test.describe('Cross-User Data Isolation', () => {
  let userA: TestUser;
  let userB: TestUser;

  test.beforeEach(() => {
    userA = {
      email: generateUniqueEmail(),
      password: 'UserA@123',
    };
    userB = {
      email: generateUniqueEmail(),
      password: 'UserB@123',
    };
  });

  test('User A cannot see User B\'s todos', async ({ page }) => {
    // User A registers and creates a todo
    await registerUser(page, userA);
    const todoA = 'User A private todo';
    await createTodo(page, todoA);
    
    // Verify User A can see their todo
    await expect(page.locator(`text=${todoA}`).first()).toBeVisible();
    
    // Logout User A
    await logoutUser(page);

    // User B registers and creates a todo
    await registerUser(page, userB);
    const todoB = 'User B private todo';
    await createTodo(page, todoB);

    // Verify User B can see their own todo
    await expect(page.locator(`text=${todoB}`).first()).toBeVisible();

    // Verify User B CANNOT see User A's todo
    await expect(page.locator(`text=${todoA}`).first()).not.toBeVisible();
  });

  test('User B cannot see User A\'s todos after login', async ({ page }) => {
    // User A registers and creates todos
    await registerUser(page, userA);
    await createTodo(page, 'User A Todo 1');
    await createTodo(page, 'User A Todo 2');
    await logoutUser(page);

    // User B registers
    await registerUser(page, userB);

    // User B should not see User A's todos
    await expect(page.locator('text=User A Todo 1').first()).not.toBeVisible();
    await expect(page.locator('text=User A Todo 2').first()).not.toBeVisible();

    // User B creates their own todo
    await createTodo(page, 'User B Own Todo');
    await expect(page.locator('text=User B Own Todo').first()).toBeVisible();
  });

  test('Each user maintains their own todo list after multiple logins', async ({ page }) => {
    // User A creates todos
    await registerUser(page, userA);
    await createTodo(page, 'User A Task');
    await logoutUser(page);

    // User B creates todos
    await registerUser(page, userB);
    await createTodo(page, 'User B Task');
    await logoutUser(page);

    // User A logs back in
    await loginUser(page, userA);
    await expect(page.locator('text=User A Task').first()).toBeVisible();
    await expect(page.locator('text=User B Task').first()).not.toBeVisible();
    await logoutUser(page);

    // User B logs back in
    await loginUser(page, userB);
    await expect(page.locator('text=User B Task').first()).toBeVisible();
    await expect(page.locator('text=User A Task').first()).not.toBeVisible();
  });

  test('Todo count is correct for each user independently', async ({ page }) => {
    // User A creates 3 todos
    await registerUser(page, userA);
    await createTodo(page, 'Todo 1');
    await createTodo(page, 'Todo 2');
    await createTodo(page, 'Todo 3');
    
    // Check User A has 3 todos
    const userATodos = await page.locator('[data-testid="todo-item"]').count();
    expect(userATodos).toBe(3);
    
    await logoutUser(page);

    // User B creates 1 todo
    await registerUser(page, userB);
    await createTodo(page, 'Single Todo');
    
    // Check User B has only 1 todo
    const userBTodos = await page.locator('[data-testid="todo-item"]').count();
    expect(userBTodos).toBe(1);
  });
});
