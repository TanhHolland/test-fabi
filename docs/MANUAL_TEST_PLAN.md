# Manual Test Plan - Todo Application

## Test Overview

This document outlines manual test cases for the Full-Stack Todo Application. Tests are organized by functional area and prioritized by severity and priority.

**Last Updated**: 2026-09-21  
**Version**: 1.0  
**Tester**: [To be filled during testing]

---

## Test Environment

- **Frontend URL**: http://localhost:3000
- **Backend URL**: http://localhost:8000
- **Database**: PostgreSQL
- **Cache**: Redis
- **Prerequisites**: Docker and Docker Compose installed

### Setup Instructions

```bash
# Start all services
docker compose up

# Verify all services are running
docker compose ps
```

---

## Authentication Test Cases

### TC-AUTH-001: User Registration with Valid Credentials
**Priority**: P0  
**Severity**: Critical

**Preconditions**: None

**Test Steps**:
1. Navigate to http://localhost:3000/register
2. Enter valid email: `test1@example.com`
3. Enter valid password: `Test@123456`
4. Click "Register" button

**Expected Result**:
- User is successfully registered
- Access token is generated
- User is redirected to `/todos` page
- Welcome message or user email is displayed

**Status**: [ ] Pass / [ ] Fail / [ ] Blocked

---

### TC-AUTH-002: User Registration with Existing Email
**Priority**: P1  
**Severity**: High

**Preconditions**: User with email `existing@example.com` already registered

**Test Steps**:
1. Navigate to `/register`
2. Enter email: `existing@example.com`
3. Enter password: `Test@123456`
4. Click "Register"

**Expected Result**:
- Registration fails
- Error message displayed: "Email already registered" or similar
- HTTP 400 status code
- User remains on registration page

**Status**: [ ] Pass / [ ] Fail / [ ] Blocked

---

### TC-AUTH-003: User Login with Valid Credentials
**Priority**: P0  
**Severity**: Critical

**Preconditions**: User `test1@example.com` exists

**Test Steps**:
1. Navigate to `/login`
2. Enter email: `test1@example.com`
3. Enter password: `Test@123456`
4. Click "Login"

**Expected Result**:
- Login successful
- Tokens generated
- Redirect to `/todos`
- User session established

**Status**: [ ] Pass / [ ] Fail / [ ] Blocked

---

### TC-AUTH-004: User Login with Invalid Password
**Priority**: P1  
**Severity**: High

**Preconditions**: User `test1@example.com` exists with password `Test@123456`

**Test Steps**:
1. Navigate to `/login`
2. Enter email: `test1@example.com`
3. Enter wrong password: `WrongPassword123`
4. Click "Login"

**Expected Result**:
- Login fails
- Error message: "Invalid credentials" or "Wrong email or password"
- HTTP 401 status code
- User remains on login page

**Status**: [ ] Pass / [ ] Fail / [ ] Blocked

---

### TC-AUTH-005: Access Protected Route Without Authentication
**Priority**: P0  
**Severity**: Critical

**Preconditions**: User is not logged in (no token)

**Test Steps**:
1. Open browser in incognito/private mode
2. Navigate directly to http://localhost:3000/todos

**Expected Result**:
- User is redirected to `/login` page
- Cannot access todos page without authentication
- Or shows "Unauthorized" message

**Status**: [ ] Pass / [ ] Fail / [ ] Blocked

---

### TC-AUTH-006: Token Expiration Handling
**Priority**: P1  
**Severity**: High

**Preconditions**: User logged in

**Test Steps**:
1. Login to the application
2. Note the token expiration time (default: 15 minutes)
3. Wait for token to expire OR manually set expiration to 1 minute in backend config
4. Try to perform an action (create/update todo)

**Expected Result**:
- Request fails with 401 Unauthorized
- User is logged out or prompted to login again
- Token refresh mechanism triggers (if implemented)

**Status**: [ ] Pass / [ ] Fail / [ ] Blocked

---

### TC-AUTH-007: User Logout
**Priority**: P1  
**Severity**: Medium

**Preconditions**: User is logged in

**Test Steps**:
1. Login to application
2. Click "Logout" button
3. Try to access `/todos` page

**Expected Result**:
- Token is cleared from storage
- User redirected to login page
- Cannot access protected routes after logout

**Status**: [ ] Pass / [ ] Fail / [ ] Blocked

---

## Authorization Test Cases

### TC-AUTHZ-001: User Cannot Access Other User's Todo by ID
**Priority**: P0  
**Severity**: Critical

**Preconditions**: 
- User A logged in with email `usera@example.com`
- User B has todo with ID `todo-b-123`

**Test Steps**:
1. Login as User A
2. Note User B's todo ID (can get from database or API)
3. Try to access: `GET /api/v1/todos/todo-b-123` with User A's token
4. Or navigate to todo detail page for User B's todo

**Expected Result**:
- HTTP 403 Forbidden status
- Error message: "Access denied" or "Not authorized"
- User A cannot see User B's todo details

**Status**: [ ] Pass / [ ] Fail / [ ] Blocked

---

### TC-AUTHZ-002: User Cannot Update Other User's Todo
**Priority**: P0  
**Severity**: Critical

**Preconditions**:
- User A logged in
- User B has a todo with ID `todo-b-456`

**Test Steps**:
1. Login as User A
2. Attempt to update User B's todo:
   ```bash
   curl -X PUT http://localhost:8000/api/v1/todos/todo-b-456 \
     -H "Authorization: Bearer <user-a-token>" \
     -H "Content-Type: application/json" \
     -d '{"title": "Hacked by User A"}'
   ```

**Expected Result**:
- HTTP 403 Forbidden
- Todo is NOT updated
- User B's todo remains unchanged

**Status**: [ ] Pass / [ ] Fail / [ ] Blocked

---

### TC-AUTHZ-003: User Cannot Delete Other User's Todo
**Priority**: P0  
**Severity**: Critical

**Preconditions**:
- User A logged in
- User B has a todo with ID `todo-b-789`

**Test Steps**:
1. Login as User A
2. Attempt to delete User B's todo via API or UI

**Expected Result**:
- HTTP 403 Forbidden
- Todo is NOT deleted
- User B's todo still exists in database

**Status**: [ ] Pass / [ ] Fail / [ ] Blocked

---

### TC-AUTHZ-004: User List Shows Only Own Todos
**Priority**: P0  
**Severity**: Critical

**Preconditions**:
- User A has 3 todos
- User B has 5 todos

**Test Steps**:
1. Login as User A
2. Navigate to `/todos`
3. Count number of todos displayed

**Expected Result**:
- User A sees exactly 3 todos (their own)
- User A does NOT see any of User B's 5 todos
- Total count shows 3

**Status**: [ ] Pass / [ ] Fail / [ ] Blocked

---

### TC-AUTHZ-005: Cache Does Not Leak Data Between Users
**Priority**: P0  
**Severity**: Critical

**Preconditions**:
- User A logged in
- User B logged in (different session)

**Test Steps**:
1. User A creates todo "User A Private"
2. User A lists todos (populates cache)
3. User B lists todos
4. Verify User B does not see "User A Private"

**Expected Result**:
- Each user has separate cache keys
- User B sees only their own todos
- No cross-user cache pollution

**Status**: [ ] Pass / [ ] Fail / [ ] Blocked

---

## Business Logic Test Cases

### TC-LOGIC-001: Create Todo with Required Fields
**Priority**: P0  
**Severity**: Critical

**Preconditions**: User logged in

**Test Steps**:
1. Navigate to `/todos`
2. Enter title: "Buy milk"
3. Click "Add" or "Create Todo"

**Expected Result**:
- Todo is created successfully
- HTTP 201 status
- Todo appears in the list
- Default `completed` = false
- Timestamps created_at and updated_at are set

**Status**: [ ] Pass / [ ] Fail / [ ] Blocked

---

### TC-LOGIC-002: Create Todo with Optional Description
**Priority**: P1  
**Severity**: Medium

**Preconditions**: User logged in

**Test Steps**:
1. Create todo with title: "Go shopping"
2. Add description: "Get milk, eggs, and bread"
3. Submit

**Expected Result**:
- Todo created with both title and description
- Description is stored and displayed correctly

**Status**: [ ] Pass / [ ] Fail / [ ] Blocked

---

### TC-LOGIC-003: Toggle Todo Completion Status
**Priority**: P0  
**Severity**: Critical

**Preconditions**: 
- User logged in
- Todo exists with `completed = false`

**Test Steps**:
1. Click checkbox to mark todo as completed
2. Verify visual change (strikethrough, different color)
3. Refresh page
4. Verify completed status persisted

**Expected Result**:
- Todo marked as completed
- Visual indication shown
- Status persists after page refresh
- updated_at timestamp changes

**Status**: [ ] Pass / [ ] Fail / [ ] Blocked

---

### TC-LOGIC-004: Toggle Todo from Completed to Not Completed
**Priority**: P1  
**Severity**: High

**Preconditions**:
- User logged in
- Todo exists with `completed = true`

**Test Steps**:
1. Click checkbox to unmark todo
2. Refresh page
3. Verify status

**Expected Result**:
- Todo changes to `completed = false`
- Visual style reverts to uncompleted state
- Change persists after refresh

**Status**: [ ] Pass / [ ] Fail / [ ] Blocked

---

### TC-LOGIC-005: Partial Update - Title Only
**Priority**: P1  
**Severity**: High

**Preconditions**:
- Todo exists: {title: "Old Title", description: "Original Description", completed: false}

**Test Steps**:
1. Edit todo to update only title to "New Title"
2. Save changes
3. Verify result

**Expected Result**:
- Title updated to "New Title"
- Description remains "Original Description"
- completed status remains false
- Other fields NOT deleted or nullified

**Status**: [ ] Pass / [ ] Fail / [ ] Blocked

---

### TC-LOGIC-006: Partial Update - Description Only
**Priority**: P1  
**Severity**: High

**Preconditions**:
- Todo exists: {title: "Keep This Title", description: "Old Desc", completed: true}

**Test Steps**:
1. Update only description to "New Description"
2. Save

**Expected Result**:
- Description updated
- Title remains unchanged
- completed status remains true

**Status**: [ ] Pass / [ ] Fail / [ ] Blocked

---

### TC-LOGIC-007: Delete Todo
**Priority**: P1  
**Severity**: High

**Preconditions**: User has a todo

**Test Steps**:
1. Click delete/trash icon on todo
2. Confirm deletion (if confirmation dialog exists)
3. Refresh page

**Expected Result**:
- Todo removed from list immediately
- HTTP 204 No Content response
- Todo deleted from database
- Does not reappear after refresh

**Status**: [ ] Pass / [ ] Fail / [ ] Blocked

---

### TC-LOGIC-008: Pagination Works Correctly
**Priority**: P2  
**Severity**: Medium

**Preconditions**: User has 25 todos

**Test Steps**:
1. Navigate to `/todos`
2. Verify page 1 shows 20 todos (default size)
3. Navigate to page 2
4. Verify page 2 shows remaining 5 todos

**Expected Result**:
- Correct number of items per page
- Total count = 25
- Pagination controls work correctly

**Status**: [ ] Pass / [ ] Fail / [ ] Blocked

---

## Cache Invalidation Test Cases

### TC-CACHE-001: Cache Invalidates on Create
**Priority**: P1  
**Severity**: Medium

**Preconditions**: User logged in, todo list cached

**Test Steps**:
1. Load todo list (populates cache)
2. Create new todo
3. Verify new todo appears immediately

**Expected Result**:
- Cache invalidated after create
- New todo visible without manual refresh
- Updated data fetched from database

**Status**: [ ] Pass / [ ] Fail / [ ] Blocked

---

### TC-CACHE-002: Cache Invalidates on Update
**Priority**: P1  
**Severity**: Medium

**Preconditions**: User has todos, list is cached

**Test Steps**:
1. Load todo list
2. Update a todo title
3. Go back to list view

**Expected Result**:
- Updated title shown immediately
- Cache invalidated
- No stale data displayed

**Status**: [ ] Pass / [ ] Fail / [ ] Blocked

---

### TC-CACHE-003: Cache Invalidates on Delete
**Priority**: P1  
**Severity**: Medium

**Preconditions**: User has todos, list is cached

**Test Steps**:
1. Load todo list
2. Delete a todo
3. Verify it's removed from list

**Expected Result**:
- Deleted todo no longer shown
- Cache invalidated
- Accurate count displayed

**Status**: [ ] Pass / [ ] Fail / [ ] Blocked

---

## Test Execution Summary

| Category | Total Cases | Passed | Failed | Blocked | Pass Rate |
|----------|-------------|--------|--------|---------|-----------|
| Authentication | 7 | - | - | - | - |
| Authorization | 5 | - | - | - | - |
| Business Logic | 8 | - | - | - | - |
| Cache | 3 | - | - | - | - |
| **TOTAL** | **23** | **-** | **-** | **-** | **-** |

---

## Test Environment Details

- **OS**: [Fill in]
- **Browser**: [Fill in - Chrome, Firefox, Safari]
- **Browser Version**: [Fill in]
- **Screen Resolution**: [Fill in]
- **Date Tested**: [Fill in]

---

## Issues Found

| Issue ID | Test Case | Severity | Description | Status |
|----------|-----------|----------|-------------|--------|
| BUG-001 | TC-XXX-XXX | Critical | [Description] | Open |

---

## Notes

- All test cases should be executed in order within each category
- Before starting, ensure all services are running via `docker compose up`
- Use different user accounts for authorization tests
- Clear browser cache between test runs for cache-related tests
- Document any deviations from expected results with screenshots

---

## Sign-off

**Tested By**: ___________________________  
**Date**: ___________________________  
**Signature**: ___________________________
