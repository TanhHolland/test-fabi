# Technical Specification: Todo Sharing Feature

**Version**: 1.0  
**Date**: September 21, 2026  
**Author**: Engineering Team  
**Status**: Draft for Review

---

## Table of Contents

1. [Overview & Goals](#overview--goals)
2. [User Stories](#user-stories)
3. [Acceptance Criteria](#acceptance-criteria)
4. [Data Model](#data-model)
5. [API Design](#api-design)
6. [Authorization Rules](#authorization-rules)
7. [Edge Cases & Error Handling](#edge-cases--error-handling)
8. [Cache Invalidation Strategy](#cache-invalidation-strategy)
9. [Migration Strategy](#migration-strategy)
10. [Out of Scope](#out-of-scope)
11. [Testing Strategy](#testing-strategy)
12. [Open Questions](#open-questions)

---

## Overview & Goals

### Business Context

Users currently can only manage their own private todo lists. To enable collaboration, we need to allow users to share their todos with other users, with different permission levels.

### Feature Goals

1. **Enable Collaboration**: Allow users to share todos with other registered users
2. **Permission Control**: Support two permission levels: viewer (read-only) and editor (read-write)
3. **Access Management**: Todo owners can grant and revoke access at any time
4. **Security**: Ensure shared todos maintain proper authorization boundaries
5. **Performance**: Maintain sub-200ms response times with caching strategy

### Success Metrics

- Share operation completes in <100ms
- Permission changes reflected immediately (cache invalidation)
- Zero cross-user unauthorized access incidents
- 95% of shares are successful on first attempt

---

## User Stories

### US-1: Share Todo with Viewer Permission

**As a** todo owner  
**I want to** share my todo with another user as a viewer  
**So that** they can see my todo but not modify it

**Acceptance Criteria**:
- Owner can share todo by specifying recipient email
- Recipient receives viewer permission
- Recipient can see todo title, description, completed status
- Recipient CANNOT modify or delete the todo
- Owner sees list of users with access

### US-2: Share Todo with Editor Permission

**As a** todo owner  
**I want to** share my todo with another user as an editor  
**So that** they can help me manage the todo

**Acceptance Criteria**:
- Owner can share todo with editor permission
- Editor can update title, description, and completed status
- Editor CANNOT delete the todo
- Editor CANNOT share the todo with others
- All changes tracked with `updated_by` field

### US-3: Upgrade/Downgrade Permissions

**As a** todo owner  
**I want to** change a user's permission level  
**So that** I can adjust access as needed

**Acceptance Criteria**:
- Owner can upgrade viewer to editor
- Owner can downgrade editor to viewer
- Permission changes take effect immediately
- Cache invalidated for both users

### US-4: Revoke Access

**As a** todo owner  
**I want to** revoke a user's access to my shared todo  
**So that** they can no longer see or edit it

**Acceptance Criteria**:
- Owner can remove any user's access
- Revoked user immediately loses access
- Revoked user no longer sees todo in their shared list
- Cache invalidated for revoked user

### US-5: View Shared Todos

**As a** user  
**I want to** see todos that others have shared with me  
**So that** I can view or collaborate on them

**Acceptance Criteria**:
- User sees separate section "Shared with Me"
- List shows todo title, owner, permission level, shared date
- Can filter by owner or permission type
- Can access shared todos with appropriate permissions

### US-6: View Share Status

**As a** todo owner  
**I want to** see who has access to my todo  
**So that** I can manage permissions

**Acceptance Criteria**:
- Owner sees list of all users with access
- List shows email, permission level, shared date
- Can quickly upgrade/downgrade or revoke access
- Shows "Not shared" if no users have access

### US-7: Notification of Shares (Out of MVP Scope)

**As a** recipient  
**I want to** be notified when someone shares a todo with me  
**So that** I'm aware of new collaborations

**Note**: Email/push notifications are out of scope for MVP

---

## Acceptance Criteria

### Functional Requirements

1. **Sharing**
   - ✅ Owner can share todo with registered user by email
   - ✅ Support viewer and editor permission levels
   - ✅ Prevent self-sharing
   - ✅ Prevent duplicate shares to same user
   - ✅ Share operation is atomic (database transaction)

2. **Viewing**
   - ✅ Viewer can read todo title, description, completed status
   - ✅ Viewer cannot modify any fields
   - ✅ Viewer sees "read-only" indicator in UI

3. **Editing**
   - ✅ Editor can update title, description, completed status
   - ✅ Editor cannot delete todo
   - ✅ Editor cannot share with other users
   - ✅ Editor cannot change owner

4. **Permission Management**
   - ✅ Owner can upgrade viewer to editor
   - ✅ Owner can downgrade editor to viewer
   - ✅ Owner can revoke any user's access
   - ✅ Permission changes are immediate

5. **Access Control**
   - ✅ Only owner can manage shares
   - ✅ Only owner can delete todo
   - ✅ Shared users respect permission boundaries
   - ✅ Deleting todo cascades to delete all shares

### Non-Functional Requirements

1. **Performance**
   - Response time <100ms for share operations
   - Response time <200ms for listing shared todos
   - Cache shared todo lists (5-minute TTL)

2. **Security**
   - All operations require authentication
   - Authorization checks on every request
   - No information leakage in error messages
   - SQL injection prevention (parameterized queries)

3. **Scalability**
   - Support up to 50 shares per todo
   - Efficient queries with proper indexing
   - Cache strategy to reduce database load

4. **Reliability**
   - Database transactions for atomicity
   - Proper error handling and rollback
   - Idempotent operations where possible

---

## Data Model

### New Tables

#### `todo_shares` Table

```sql
CREATE TABLE todo_shares (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    todo_id UUID NOT NULL,
    shared_with_user_id UUID NOT NULL,
    shared_by_user_id UUID NOT NULL,
    permission VARCHAR(20) NOT NULL CHECK (permission IN ('viewer', 'editor')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ,
    
    -- Foreign Keys
    CONSTRAINT fk_todo
        FOREIGN KEY (todo_id)
        REFERENCES todos(id)
        ON DELETE CASCADE,
    
    CONSTRAINT fk_shared_with_user
        FOREIGN KEY (shared_with_user_id)
        REFERENCES users(id)
        ON DELETE CASCADE,
    
    CONSTRAINT fk_shared_by_user
        FOREIGN KEY (shared_by_user_id)
        REFERENCES users(id)
        ON DELETE CASCADE,
    
    -- Constraints
    CONSTRAINT unique_todo_user_share
        UNIQUE (todo_id, shared_with_user_id),
    
    CONSTRAINT no_self_share
        CHECK (shared_with_user_id != shared_by_user_id)
);

-- Indexes
CREATE INDEX idx_todo_shares_todo_id ON todo_shares(todo_id);
CREATE INDEX idx_todo_shares_shared_with_user ON todo_shares(shared_with_user_id);
CREATE INDEX idx_todo_shares_permission ON todo_shares(permission);
CREATE INDEX idx_todo_shares_expires_at ON todo_shares(expires_at) WHERE expires_at IS NOT NULL;
```

### Field Descriptions

| Field | Type | Nullable | Description |
|-------|------|----------|-------------|
| `id` | UUID | No | Primary key |
| `todo_id` | UUID | No | Reference to shared todo |
| `shared_with_user_id` | UUID | No | User receiving access |
| `shared_by_user_id` | UUID | No | User granting access (typically owner) |
| `permission` | VARCHAR(20) | No | 'viewer' or 'editor' |
| `created_at` | TIMESTAMPTZ | No | When share was created |
| `updated_at` | TIMESTAMPTZ | No | When permission was last modified |
| `expires_at` | TIMESTAMPTZ | Yes | Optional expiration (future feature) |

### Relationships

```
users (1) ----< (N) todo_shares (as shared_with_user)
users (1) ----< (N) todo_shares (as shared_by_user)
todos (1) ----< (N) todo_shares
```

### Cascade Behavior

1. **Delete Todo**: All related shares are deleted (CASCADE)
2. **Delete User (shared_with)**: All shares granted to that user are deleted (CASCADE)
3. **Delete User (owner)**: All their todos and shares are deleted (CASCADE via todos)

### Constraints

1. **Unique Share**: A todo can only be shared once with each user
2. **No Self-Share**: User cannot share todo with themselves
3. **Permission Values**: Only 'viewer' or 'editor' allowed
4. **Foreign Key Integrity**: All referenced users and todos must exist

---

## API Design

### 1. Share Todo

**Endpoint**: `POST /api/v1/todos/{todo_id}/shares`

**Description**: Share a todo with another user

**Authorization**: Only todo owner can share

**Request Body**:
```json
{
  "shared_with_email": "user@example.com",
  "permission": "viewer"
}
```

**Request Schema**:
```typescript
{
  shared_with_email: string (email format, required)
  permission: "viewer" | "editor" (required)
}
```

**Response 201 Created**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "todo_id": "123e4567-e89b-12d3-a456-426614174000",
  "shared_with_user": {
    "id": "789e4567-e89b-12d3-a456-426614174000",
    "email": "user@example.com"
  },
  "permission": "viewer",
  "created_at": "2026-09-21T10:00:00Z"
}
```

**Error Responses**:

- **400 Bad Request**: Invalid permission value
  ```json
  {"detail": "Permission must be 'viewer' or 'editor'"}
  ```

- **403 Forbidden**: Not todo owner
  ```json
  {"detail": "Only todo owner can share"}
  ```

- **404 Not Found**: Todo or user doesn't exist
  ```json
  {"detail": "Todo not found"}
  ```
  ```json
  {"detail": "User with email 'user@example.com' not found"}
  ```

- **409 Conflict**: Already shared with user
  ```json
  {"detail": "Todo already shared with this user"}
  ```

- **422 Unprocessable Entity**: Self-share attempt
  ```json
  {"detail": "Cannot share todo with yourself"}
  ```

---

### 2. List Todo Shares

**Endpoint**: `GET /api/v1/todos/{todo_id}/shares`

**Description**: Get list of users who have access to a todo

**Authorization**: Only todo owner can view shares

**Query Parameters**: None

**Response 200 OK**:
```json
{
  "todo_id": "123e4567-e89b-12d3-a456-426614174000",
  "shares": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "shared_with_user": {
        "id": "789e4567-e89b-12d3-a456-426614174000",
        "email": "user1@example.com"
      },
      "permission": "editor",
      "created_at": "2026-09-21T10:00:00Z",
      "updated_at": "2026-09-21T10:00:00Z"
    },
    {
      "id": "660e8400-e29b-41d4-a716-446655440001",
      "shared_with_user": {
        "id": "890e4567-e89b-12d3-a456-426614174001",
        "email": "user2@example.com"
      },
      "permission": "viewer",
      "created_at": "2026-09-21T11:00:00Z",
      "updated_at": "2026-09-21T11:00:00Z"
    }
  ],
  "total": 2
}
```

**Error Responses**:

- **403 Forbidden**: Not todo owner
  ```json
  {"detail": "Only todo owner can view shares"}
  ```

- **404 Not Found**: Todo doesn't exist
  ```json
  {"detail": "Todo not found"}
  ```

---

### 3. Update Share Permission

**Endpoint**: `PATCH /api/v1/todos/{todo_id}/shares/{share_id}`

**Description**: Change permission level for a shared user

**Authorization**: Only todo owner can update

**Request Body**:
```json
{
  "permission": "editor"
}
```

**Response 200 OK**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "todo_id": "123e4567-e89b-12d3-a456-426614174000",
  "shared_with_user": {
    "id": "789e4567-e89b-12d3-a456-426614174000",
    "email": "user@example.com"
  },
  "permission": "editor",
  "created_at": "2026-09-21T10:00:00Z",
  "updated_at": "2026-09-21T12:00:00Z"
}
```

**Error Responses**:

- **400 Bad Request**: Invalid permission
  ```json
  {"detail": "Permission must be 'viewer' or 'editor'"}
  ```

- **403 Forbidden**: Not todo owner
  ```json
  {"detail": "Only todo owner can update shares"}
  ```

- **404 Not Found**: Share doesn't exist
  ```json
  {"detail": "Share not found"}
  ```

---

### 4. Revoke Access

**Endpoint**: `DELETE /api/v1/todos/{todo_id}/shares/{share_id}`

**Description**: Remove user's access to a todo

**Authorization**: Only todo owner can revoke

**Response 204 No Content**

**Error Responses**:

- **403 Forbidden**: Not todo owner
  ```json
  {"detail": "Only todo owner can revoke access"}
  ```

- **404 Not Found**: Share doesn't exist
  ```json
  {"detail": "Share not found"}
  ```

---

### 5. List Shared With Me

**Endpoint**: `GET /api/v1/todos/shared-with-me`

**Description**: Get todos that other users have shared with current user

**Authorization**: Any authenticated user

**Query Parameters**:
- `permission` (optional): Filter by permission type ('viewer' or 'editor')
- `owner_email` (optional): Filter by owner email
- `page` (optional, default: 1): Page number
- `size` (optional, default: 20): Items per page

**Response 200 OK**:
```json
{
  "items": [
    {
      "share_id": "550e8400-e29b-41d4-a716-446655440000",
      "todo": {
        "id": "123e4567-e89b-12d3-a456-426614174000",
        "title": "Team Meeting Notes",
        "description": "Discuss Q4 goals",
        "completed": false,
        "owner": {
          "id": "456e4567-e89b-12d3-a456-426614174000",
          "email": "owner@example.com"
        }
      },
      "permission": "editor",
      "shared_at": "2026-09-21T10:00:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "size": 20
}
```

---

### 6. Get Shared Todo (Extended Endpoint)

**Endpoint**: `GET /api/v1/todos/{todo_id}`

**Description**: Get todo details (updated to support shared access)

**Authorization**: Owner OR user with share access

**Response 200 OK**:
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "title": "Team Meeting Notes",
  "description": "Discuss Q4 goals",
  "completed": false,
  "user_id": "456e4567-e89b-12d3-a456-426614174000",
  "created_at": "2026-09-20T10:00:00Z",
  "updated_at": "2026-09-21T10:00:00Z",
  "user_email": "owner@example.com",
  "shared_with_me": {
    "permission": "editor",
    "shared_at": "2026-09-21T10:00:00Z"
  },
  "is_owner": false
}
```

**Notes**:
- `shared_with_me` field only present if accessing via share
- `is_owner` indicates if current user is the owner

---

### 7. Update Shared Todo (Extended Endpoint)

**Endpoint**: `PUT /api/v1/todos/{todo_id}`

**Description**: Update todo (extended to support editors)

**Authorization**: Owner OR user with 'editor' permission

**Request Body**:
```json
{
  "title": "Updated Title",
  "description": "Updated Description",
  "completed": true
}
```

**Response 200 OK**: Same as GET response

**Error Responses**:

- **403 Forbidden**: Viewer trying to update
  ```json
  {"detail": "You only have viewer permission for this todo"}
  ```

---

## Authorization Rules

### Permission Matrix

| Action | Owner | Editor | Viewer | Not Shared |
|--------|-------|--------|--------|------------|
| View todo | ✅ | ✅ | ✅ | ❌ |
| Update todo | ✅ | ✅ | ❌ | ❌ |
| Delete todo | ✅ | ❌ | ❌ | ❌ |
| Share todo | ✅ | ❌ | ❌ | ❌ |
| View shares | ✅ | ❌ | ❌ | ❌ |
| Update permission | ✅ | ❌ | ❌ | ❌ |
| Revoke access | ✅ | ❌ | ❌ | ❌ |

### Authorization Flow

```python
def can_access_todo(user_id: UUID, todo_id: UUID) -> Tuple[bool, Optional[str]]:
    """
    Check if user can access todo and return permission level.
    Returns: (can_access, permission_level)
    permission_level: 'owner', 'editor', 'viewer', or None
    """
    # Check if owner
    todo = get_todo(todo_id)
    if todo.user_id == user_id:
        return (True, 'owner')
    
    # Check if shared
    share = get_share(todo_id=todo_id, user_id=user_id)
    if share:
        return (True, share.permission)
    
    return (False, None)

def can_modify_todo(user_id: UUID, todo_id: UUID) -> bool:
    """Check if user can modify todo"""
    can_access, permission = can_access_todo(user_id, todo_id)
    return can_access and permission in ['owner', 'editor']

def is_todo_owner(user_id: UUID, todo_id: UUID) -> bool:
    """Check if user is todo owner"""
    can_access, permission = can_access_todo(user_id, todo_id)
    return permission == 'owner'
```

### Implementation Notes

1. **Middleware Authorization**
   - Create `require_todo_access` dependency
   - Create `require_todo_modify` dependency
   - Create `require_todo_owner` dependency

2. **Database Queries**
   - Always join `todo_shares` when fetching todos
   - Include permission level in response
   - Filter by user_id OR shared_with_user_id

3. **Error Messages**
   - Don't reveal if todo exists when access denied
   - Use generic "Not found" for unauthorized access
   - Log authorization failures for security monitoring

---

## Edge Cases & Error Handling

### Edge Case 1: Self-Sharing

**Scenario**: User tries to share todo with themselves

**Prevention**: Database CHECK constraint + API validation

**Implementation**:
```python
if shared_with_user_id == current_user.id:
    raise HTTPException(
        status_code=422,
        detail="Cannot share todo with yourself"
    )
```

**Database Constraint**:
```sql
CONSTRAINT no_self_share
    CHECK (shared_with_user_id != shared_by_user_id)
```

---

### Edge Case 2: Duplicate Shares

**Scenario**: Owner tries to share todo twice with same user

**Prevention**: UNIQUE constraint on (todo_id, shared_with_user_id)

**Handling**:
```python
try:
    db.add(todo_share)
    db.commit()
except IntegrityError:
    raise HTTPException(
        status_code=409,
        detail="Todo already shared with this user. Use PATCH to update permission."
    )
```

---

### Edge Case 3: Sharing Non-Existent User

**Scenario**: Owner tries to share with email that doesn't exist

**Handling**:
```python
recipient = db.query(User).filter(User.email == shared_with_email).first()
if not recipient:
    raise HTTPException(
        status_code=404,
        detail=f"User with email '{shared_with_email}' not found"
    )
```

---

### Edge Case 4: Concurrent Permission Updates

**Scenario**: Two requests try to update same share simultaneously

**Prevention**: Use database transactions + optimistic locking

**Implementation**:
```python
with db.begin():
    share = db.query(TodoShare).filter(
        TodoShare.id == share_id
    ).with_for_update().first()
    
    if not share:
        raise HTTPException(404, "Share not found")
    
    share.permission = new_permission
    share.updated_at = datetime.now(timezone.utc)
    db.commit()
```

---

### Edge Case 5: Owner Deletion Cascading

**Scenario**: Todo owner is deleted from system

**Behavior**: All todos and their shares are deleted (CASCADE)

**Implementation**: Database foreign key with ON DELETE CASCADE

**Notification**: Consider queuing notifications to affected users (future)

---

### Edge Case 6: Accessing Expired Shares

**Scenario**: User tries to access todo after share expired

**Handling** (Future Feature):
```python
share = get_share(todo_id, user_id)
if share and share.expires_at and share.expires_at < datetime.now(timezone.utc):
    raise HTTPException(
        status_code=403,
        detail="Your access to this todo has expired"
    )
```

---

### Edge Case 7: Maximum Shares Per Todo

**Scenario**: Owner tries to share with 51st user (limit: 50)

**Prevention**: Application-level validation

**Implementation**:
```python
share_count = db.query(TodoShare).filter(
    TodoShare.todo_id == todo_id
).count()

if share_count >= 50:
    raise HTTPException(
        status_code=400,
        detail="Maximum 50 users can access a single todo"
    )
```

---

### Edge Case 8: Revoke While User Is Viewing

**Scenario**: User is viewing todo when owner revokes access

**Handling**:
- Cache invalidation immediately removes access
- User's next action gets 403 Forbidden
- Frontend shows "Access revoked" message
- User redirected to their own todos list

---

## Cache Invalidation Strategy

### Cache Keys

```python
# User's own todos list
f"todos:list:{user_id}"

# Shared todos list
f"todos:shared:{user_id}"

# Specific todo (includes permission level)
f"todo:{todo_id}:{user_id}"

# Todo shares list (for owner)
f"todo:shares:{todo_id}"
```

### Invalidation Rules

| Action | Keys to Invalidate |
|--------|-------------------|
| Create share | `todos:shared:{recipient_id}`, `todo:shares:{todo_id}` |
| Update permission | `todos:shared:{recipient_id}`, `todo:{todo_id}:{recipient_id}`, `todo:shares:{todo_id}` |
| Revoke share | `todos:shared:{recipient_id}`, `todo:{todo_id}:{recipient_id}`, `todo:shares:{todo_id}` |
| Update shared todo | `todo:{todo_id}:{owner_id}`, `todo:{todo_id}:{editor_id}`, `todos:list:{owner_id}`, `todos:shared:{editor_id}` |
| Delete todo | All related cache keys |

### Implementation Example

```python
async def create_share(
    db: AsyncSession,
    redis: RedisClient,
    todo_id: UUID,
    shared_with_user_id: UUID,
    permission: str
) -> TodoShare:
    # Create share
    share = TodoShare(...)
    db.add(share)
    await db.commit()
    
    # Invalidate caches
    await redis.delete(f"todos:shared:{shared_with_user_id}")
    await redis.delete(f"todo:shares:{todo_id}")
    
    return share
```

### Cache TTL Strategy

- Todo lists: 5 minutes (300 seconds)
- Individual todos: 10 minutes (600 seconds)
- Share lists: 5 minutes (300 seconds)
- Use Redis SETEX for automatic expiration
- Manual invalidation on mutations

---

## Migration Strategy

### Phase 1: Database Schema (Week 1)

1. **Create Migration**
   ```bash
   alembic revision -m "add_todo_sharing_tables"
   ```

2. **Run Migration on Staging**
   ```bash
   alembic upgrade head
   ```

3. **Verify Constraints**
   - Test unique constraint
   - Test foreign key cascades
   - Test check constraints

### Phase 2: Backend Implementation (Week 2)

1. **Models & Schemas**
   - Create `TodoShare` model
   - Create Pydantic schemas
   - Update `Todo` model to include shares relationship

2. **API Endpoints**
   - Implement 5 new endpoints
   - Add authorization middleware
   - Update existing todo endpoints

3. **Testing**
   - Unit tests for models
   - API tests for all endpoints
   - Authorization boundary tests
   - Cache invalidation tests

### Phase 3: Frontend Implementation (Week 3)

1. **UI Components**
   - Share modal/dialog
   - Shared users list
   - "Shared with Me" section
   - Permission badges

2. **State Management**
   - React Query hooks
   - Cache invalidation
   - Optimistic updates

3. **Testing**
   - Component tests
   - E2E tests for sharing flow

### Phase 4: Production Deployment (Week 4)

1. **Staged Rollout**
   - Deploy to 10% of users
   - Monitor error rates
   - Check performance metrics

2. **Full Deployment**
   - Deploy to 100% of users
   - Monitor for 48 hours
   - Document any issues

### Rollback Plan

If critical issues arise:

1. **Database**: Keep `todo_shares` table but disable feature flag
2. **Backend**: Revert API endpoints
3. **Frontend**: Hide share UI components
4. **Data**: Shares remain in database for future re-enable

---

## Out of Scope

### Not Included in MVP

1. **Email Notifications**
   - No email sent when todo is shared
   - No notifications when permissions change
   - Future: Implement with async job queue

2. **Share Expiration**
   - `expires_at` field exists but not enforced
   - Future: Background job to cleanup expired shares

3. **Share Links**
   - No public share links (share-by-link)
   - Only direct user-to-user sharing
   - Future: Generate shareable URLs with tokens

4. **Comment/Activity Log**
   - No tracking of who made what changes
   - Future: Add `activity_log` table

5. **Share Request/Approval Flow**
   - Owner directly shares (no request needed)
   - Future: Allow users to request access

6. **Bulk Sharing**
   - Can only share with one user at a time
   - Future: Share with multiple users or groups

7. **Groups/Teams**
   - No concept of user groups
   - Future: Share with entire team

8. **Advanced Permissions**
   - Only viewer and editor (no custom roles)
   - Future: Granular permissions

---

## Testing Strategy

### Unit Tests (Backend)

```python
# tests/test_todo_sharing.py

def test_create_share_success():
    """Owner can share todo with another user"""
    
def test_create_share_prevents_self_sharing():
    """User cannot share todo with themselves"""
    
def test_create_share_prevents_duplicate():
    """Cannot share same todo twice with same user"""
    
def test_update_permission_success():
    """Owner can change permission level"""
    
def test_revoke_access_success():
    """Owner can revoke user's access"""
    
def test_viewer_cannot_update_todo():
    """User with viewer permission cannot modify todo"""
    
def test_editor_can_update_todo():
    """User with editor permission can modify todo"""
    
def test_editor_cannot_delete_todo():
    """Editor cannot delete todo (only owner can)"""
    
def test_editor_cannot_share_todo():
    """Editor cannot share todo with others"""
    
def test_list_shared_with_me():
    """User sees todos shared with them"""
    
def test_cache_invalidation_on_share():
    """Cache invalidated when todo is shared"""
    
def test_cascade_delete_on_todo_deletion():
    """Shares deleted when todo is deleted"""
```

### Integration Tests (API)

```bash
# Test full sharing flow
1. User A creates todo
2. User A shares with User B (editor)
3. User B fetches shared todos list
4. User B updates shared todo
5. User A sees changes
6. User A downgrades B to viewer
7. User B cannot update anymore
8. User A revokes access
9. User B cannot access todo
```

### E2E Tests (Playwright)

```typescript
test('Complete sharing workflow', async ({ page, context }) => {
  // Two browser contexts (User A and User B)
  const userA = await context.newPage();
  const userB = await context.newPage();
  
  // User A creates and shares todo
  await userA.goto('/todos');
  await userA.fill('[name="title"]', 'Shared Todo');
  await userA.click('button:has-text("Add")');
  await userA.click('[data-testid="share-button"]');
  await userA.fill('[name="email"]', 'userb@example.com');
  await userA.select('[name="permission"]', 'editor');
  await userA.click('button:has-text("Share")');
  
  // User B sees shared todo
  await userB.goto('/todos/shared');
  await expect(userB.locator('text=Shared Todo')).toBeVisible();
  
  // User B can edit
  await userB.click('text=Shared Todo');
  await userB.fill('[name="title"]', 'Updated by B');
  await userB.click('button:has-text("Save")');
  
  // User A sees update
  await userA.reload();
  await expect(userA.locator('text=Updated by B')).toBeVisible();
});
```

### Manual Test Cases

1. **TC-SHARE-001**: Share with viewer permission
2. **TC-SHARE-002**: Share with editor permission
3. **TC-SHARE-003**: Upgrade viewer to editor
4. **TC-SHARE-004**: Downgrade editor to viewer
5. **TC-SHARE-005**: Revoke access
6. **TC-SHARE-006**: Attempt self-sharing (should fail)
7. **TC-SHARE-007**: Duplicate share (should fail)
8. **TC-SHARE-008**: Share non-existent user (should fail)
9. **TC-SHARE-009**: Viewer tries to edit (should fail)
10. **TC-SHARE-010**: Editor tries to delete (should fail)

### Performance Tests

- Share operation: <100ms (p95)
- List shared todos: <200ms (p95)
- Update permission: <100ms (p95)
- Cache hit rate: >90%

---

## Open Questions

1. **Share Limits**: Should there be a limit on total shares per user?
   - Proposed: 100 shares per user across all todos

2. **Notification Preferences**: When notifications added, allow opt-out?
   - Proposed: Yes, add user preference for share notifications

3. **Analytics**: Track share adoption rate?
   - Proposed: Yes, add metrics for shares created, active shares

4. **API Rate Limiting**: Different limits for share endpoints?
   - Proposed: Same as other endpoints (100 req/min)

5. **Audit Log**: Track all share operations?
   - Proposed: Yes, but in Phase 2

---

## Appendix

### Database Diagram

```
┌─────────────┐
│    users    │
└──────┬──────┘
       │
       │ (1:N)
       │
┌──────┴──────────┐
│      todos      │
└──────┬──────────┘
       │
       │ (1:N)
       │
┌──────┴──────────┐
│  todo_shares    │
└─────────────────┘
       │
       │ (N:1)
       │
┌──────┴──────────┐
│     users       │
│ (shared_with)   │
└─────────────────┘
```

### Example SQL Queries

**Get todos accessible by user (own + shared)**:
```sql
SELECT t.*, 
       CASE 
         WHEN t.user_id = $1 THEN 'owner'
         ELSE ts.permission 
       END as access_level
FROM todos t
LEFT JOIN todo_shares ts ON t.id = ts.todo_id AND ts.shared_with_user_id = $1
WHERE t.user_id = $1 OR ts.shared_with_user_id = $1
ORDER BY t.created_at DESC;
```

**Get share details for todo**:
```sql
SELECT ts.*, u.email as shared_with_email
FROM todo_shares ts
JOIN users u ON ts.shared_with_user_id = u.id
WHERE ts.todo_id = $1;
```

---

**Document End**

**Review Checklist**:
- [ ] All user stories documented
- [ ] Data model complete with constraints
- [ ] All API endpoints specified
- [ ] Authorization rules clearly defined
- [ ] Edge cases identified and handled
- [ ] Cache strategy documented
- [ ] Migration plan outlined
- [ ] Testing strategy comprehensive
- [ ] Out of scope items listed
- [ ] Open questions documented

**Next Steps**:
1. Review with team
2. Get stakeholder approval
3. Create implementation tickets
4. Begin Phase 1 (database migration)
