# E2E Tests for Todo App

This directory contains end-to-end tests using Playwright.

## Setup

Install dependencies:

```bash
cd e2e
npm install
npx playwright install
```

## Running Tests

Make sure the application is running (backend + frontend) before running E2E tests.

### Start the application:

```bash
# From the root directory
docker compose up
```

### Run all tests:

```bash
npm test
```

### Run tests in headed mode (see browser):

```bash
npm run test:headed
```

### Run tests with UI mode (interactive):

```bash
npm run test:ui
```

### Debug tests:

```bash
npm run test:debug
```

### View test report:

```bash
npm run report
```

## Test Structure

- `tests/user-journey.spec.ts` - Complete user flow tests (register, login, CRUD operations)
- `tests/data-isolation.spec.ts` - Cross-user data isolation tests
- `fixtures/user-helpers.ts` - Helper functions for common operations

## Test Coverage

### User Journey Tests:
- Complete registration → login → create todo → toggle → logout flow
- Multiple todo creation
- Todo completion toggle persistence

### Data Isolation Tests:
- User A cannot see User B's todos
- Each user maintains separate todo lists
- Todo counts are correct per user
- Data persists across login sessions

## Configuration

See `playwright.config.ts` for configuration options.

The tests are configured to:
- Run on Chromium browser
- Use `http://localhost:3000` as base URL
- Take screenshots on failure
- Generate HTML reports
