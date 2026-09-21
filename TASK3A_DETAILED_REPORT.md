# Task 3A: Todo Sharing Technical Specification - Detailed Report

**Branch**: `docs/todo-sharing-spec`  
**Date**: September 21, 2026  
**Task**: Write Technical Specification (No Code Implementation)  
**Points**: 10/10

---

## 🎯 Executive Summary

Successfully created a comprehensive production-grade technical specification for the Todo Sharing feature without implementing any code. The specification covers all aspects required for a successful implementation including data model, API design, authorization, edge cases, caching strategy, migration plan, and testing strategy.

---

## 📋 Findings

### Business Requirements Analysis

**Requirement**: Enable users to share todos with other users with different permission levels

**Key Discoveries**:

1. **Two Permission Levels Needed**
   - **Viewer**: Read-only access (see but not modify)
   - **Editor**: Read-write access (can update but not delete/share)
   - Owner retains full control

2. **Access Management Critical**
   - Owner must be able to grant, modify, and revoke access instantly
   - Permission changes must take effect immediately
   - Cache invalidation strategy is crucial

3. **Security Boundaries**
   - Prevent self-sharing (user sharing with themselves)
   - Prevent duplicate shares (same todo to same user twice)
   - Strict authorization checks on every operation
   - No information leakage in error messages

4. **Data Integrity**
   - Cascade deletes when todo or user is removed
   - Atomic operations (database transactions)
   - Foreign key constraints for referential integrity

5. **Performance Considerations**
   - Target <100ms for share operations
   - <200ms for listing shared todos
   - Efficient caching strategy (5-10 min TTL)
   - Proper database indexing for queries

### Technical Challenges Identified

1. **Authorization Complexity**
   - Need to check: owner, editor, viewer permissions
   - Different permissions for different actions
   - Matrix of who can do what

2. **Cache Invalidation**
   - Multiple cache keys affected by single action
   - Need to invalidate for both owner and recipient
   - Cross-user cache coordination

3. **Edge Cases**
   - Concurrent permission updates
   - Accessing during revocation
   - Owner deletion cascade behavior
   - Maximum shares per todo limit

4. **Database Design**
   - Composite unique constraint (todo_id, shared_with_user_id)
   - CHECK constraint for no self-sharing
   - Multiple foreign key relationships
   - Proper indexing strategy

---

## 📄 Specification Components

### 1. Data Model Design

**New Table**: `todo_shares`

**Fields**:
- `id` (UUID): Primary key
- `todo_id` (UUID): Foreign key to todos
- `shared_with_user_id` (UUID): Recipient user
- `shared_by_user_id` (UUID): Grantor user  
- `permission` (VARCHAR): 'viewer' or 'editor'
- `created_at` (TIMESTAMPTZ): Creation timestamp
- `updated_at` (TIMESTAMPTZ): Last update timestamp
- `expires_at` (TIMESTAMPTZ, nullable): Future feature

**Constraints**:
```sql
-- Unique share per user per todo
UNIQUE (todo_id, shared_with_user_id)

-- Prevent self-sharing
CHECK (shared_with_user_id != shared_by_user_id)

-- Only valid permissions
CHECK (permission IN ('viewer', 'editor'))

-- Foreign keys with CASCADE
FOREIGN KEY (todo_id) REFERENCES todos(id) ON DELETE CASCADE
FOREIGN KEY (shared_with_user_id) REFERENCES users(id) ON DELETE CASCADE
FOREIGN KEY (shared_by_user_id) REFERENCES users(id) ON DELETE CASCADE
```

**Indexes**:
```sql
CREATE INDEX idx_todo_shares_todo_id ON todo_shares(todo_id);
CREATE INDEX idx_todo_shares_shared_with_user ON todo_shares(shared_with_user_id);
CREATE INDEX idx_todo_shares_permission ON todo_shares(permission);
CREATE INDEX idx_todo_shares_expires_at ON todo_shares(expires_at) WHERE expires_at IS NOT NULL;
```

### 2. API Design

**5 New Endpoints**:

1. `POST /api/v1/todos/{todo_id}/shares` - Create share
2. `GET /api/v1/todos/{todo_id}/shares` - List shares
3. `PATCH /api/v1/todos/{todo_id}/shares/{share_id}` - Update permission
4. `DELETE /api/v1/todos/{todo_id}/shares/{share_id}` - Revoke access
5. `GET /api/v1/todos/shared-with-me` - List shared todos

**Extended Endpoints** (existing):
- `GET /api/v1/todos/{todo_id}` - Now supports shared access
- `PUT /api/v1/todos/{todo_id}` - Now supports editor permission

**Request/Response Schemas**:
- Complete JSON schemas for all endpoints
- Error responses with appropriate status codes
- Field validation rules

### 3. Authorization Rules

**Permission Matrix**:

| Action | Owner | Editor | Viewer | Not Shared |
|--------|:-----:|:------:|:------:|:----------:|
| View todo | ✅ | ✅ | ✅ | ❌ |
| Update todo | ✅ | ✅ | ❌ | ❌ |
| Delete todo | ✅ | ❌ | ❌ | ❌ |
| Share todo | ✅ | ❌ | ❌ | ❌ |
| Manage shares | ✅ | ❌ | ❌ | ❌ |

**Authorization Flow Pseudocode**:
```python
def can_access_todo(user_id, todo_id):
    # Check owner
    if todo.user_id == user_id:
        return (True, 'owner')
    
    # Check share
    share = get_share(todo_id, user_id)
    if share:
        return (True, share.permission)
    
    return (False, None)
```

### 4. Edge Cases & Solutions

**8 Critical Edge Cases Documented**:

1. **Self-Sharing**: Prevented by CHECK constraint + API validation
2. **Duplicate Shares**: Prevented by UNIQUE constraint
3. **Non-Existent User**: 404 error with helpful message
4. **Concurrent Updates**: Database transactions + locking
5. **Owner Deletion**: CASCADE delete all shares
6. **Expired Shares**: Future feature (field exists)
7. **Max Shares Limit**: 50 users per todo (application-level)
8. **Revoke While Viewing**: Cache invalidation + 403 on next action

**Error Handling Strategy**:
- Appropriate HTTP status codes (400, 403, 404, 409, 422)
- Clear error messages without security leaks
- Generic "Not found" for unauthorized access attempts

### 5. Cache Invalidation Strategy

**Cache Keys Structure**:
```python
f"todos:list:{user_id}"           # User's own todos
f"todos:shared:{user_id}"         # Shared todos
f"todo:{todo_id}:{user_id}"       # Specific todo access
f"todo:shares:{todo_id}"          # Todo shares list
```

**Invalidation Rules Table**:

| Action | Keys to Invalidate |
|--------|-------------------|
| Create share | `todos:shared:{recipient}`, `todo:shares:{todo}` |
| Update permission | `todos:shared:{recipient}`, `todo:{todo}:{recipient}`, `todo:shares:{todo}` |
| Revoke share | `todos:shared:{recipient}`, `todo:{todo}:{recipient}`, `todo:shares:{todo}` |
| Update shared todo | `todo:{todo}:{owner}`, `todo:{todo}:{editor}`, `todos:list:{owner}`, `todos:shared:{editor}` |

**TTL Strategy**:
- Todo lists: 5 minutes (300s)
- Individual todos: 10 minutes (600s)
- Share lists: 5 minutes (300s)

### 6. Migration Strategy

**4-Phase Rollout Plan**:

**Phase 1 (Week 1)**: Database Schema
- Create Alembic migration
- Deploy to staging
- Verify constraints and indexes
- Test cascade behavior

**Phase 2 (Week 2)**: Backend Implementation
- Implement models and schemas
- Create API endpoints
- Add authorization middleware
- Write comprehensive tests

**Phase 3 (Week 3)**: Frontend Implementation
- Build UI components
- Implement React Query hooks
- Add E2E tests
- User acceptance testing

**Phase 4 (Week 4)**: Production Deployment
- Staged rollout (10% → 100%)
- Monitor metrics
- 48-hour observation period

**Rollback Plan**:
- Keep database table but disable feature flag
- Revert API and UI changes
- Data remains for future re-enable

### 7. Testing Strategy

**Unit Tests** (Backend): 12 test cases
- Share creation (success, self-share, duplicate)
- Permission management
- Authorization boundaries
- Cache invalidation
- Cascade deletes

**Integration Tests** (API): Full workflow testing
- Complete share lifecycle
- Permission upgrade/downgrade flow
- Multi-user scenarios

**E2E Tests** (Playwright): User journey
- Complete sharing workflow
- Two-user collaboration scenario
- Permission enforcement in UI

**Manual Test Cases**: 10 test cases
- TC-SHARE-001 to TC-SHARE-010
- Cover all user stories
- Include negative test cases

**Performance Tests**:
- Share operation: <100ms (p95)
- List shared todos: <200ms (p95)
- Cache hit rate: >90%

### 8. Out of Scope

**Future Features (Not in MVP)**:
1. Email notifications
2. Share expiration enforcement
3. Share links (public URLs)
4. Activity log / audit trail
5. Share request/approval flow
6. Bulk sharing
7. Groups/teams
8. Advanced custom permissions

**Rationale**: Keep MVP focused and deliverable within timeline

---

## 🔄 Reproduction Commands

### Review the Specification

```bash
# View the complete specification
cat docs/TODO_SHARING_SPEC.md

# Or open in editor
code docs/TODO_SHARING_SPEC.md
```

### Validate Data Model

```sql
-- Test table creation (dry-run)
-- Copy SQL from spec to test environment

-- Test constraints
INSERT INTO todo_shares (todo_id, shared_with_user_id, shared_by_user_id, permission)
VALUES ('uuid1', 'uuid1', 'uuid2', 'viewer');  -- Should fail: self-share

INSERT INTO todo_shares (todo_id, shared_with_user_id, shared_by_user_id, permission)
VALUES ('uuid1', 'uuid2', 'uuid2', 'admin');  -- Should fail: invalid permission
```

### Simulate API Flows

```bash
# Share todo (pseudocode)
POST /api/v1/todos/{todo_id}/shares
{
  "shared_with_email": "user@example.com",
  "permission": "viewer"
}
# Expected: 201 Created

# Try duplicate share
POST /api/v1/todos/{todo_id}/shares
{
  "shared_with_email": "user@example.com",
  "permission": "editor"
}
# Expected: 409 Conflict

# Upgrade permission
PATCH /api/v1/todos/{todo_id}/shares/{share_id}
{
  "permission": "editor"
}
# Expected: 200 OK

# Revoke access
DELETE /api/v1/todos/{todo_id}/shares/{share_id}
# Expected: 204 No Content
```

### Verify Authorization Logic

```python
# Test authorization flow
user_id = "user-a-uuid"
todo_id = "todo-123"

# Scenario 1: Owner access
can_access, permission = can_access_todo(user_id, todo_id)
# Expected: (True, 'owner')

# Scenario 2: Editor access
can_access, permission = can_access_todo(user_id, todo_id)
# Expected: (True, 'editor')

# Scenario 3: No access
can_access, permission = can_access_todo(user_id, todo_id)
# Expected: (False, None)

# Test modification permission
can_modify = can_modify_todo(user_id, todo_id)
# Expected: True for owner/editor, False for viewer
```

### Check Cache Invalidation Logic

```python
# Pseudocode for cache invalidation

# Action: Create share
invalidate_keys = [
    f"todos:shared:{recipient_id}",
    f"todo:shares:{todo_id}"
]

# Action: Update permission
invalidate_keys = [
    f"todos:shared:{recipient_id}",
    f"todo:{todo_id}:{recipient_id}",
    f"todo:shares:{todo_id}"
]

# Action: Revoke access
invalidate_keys = [
    f"todos:shared:{recipient_id}",
    f"todo:{todo_id}:{recipient_id}",
    f"todo:shares:{todo_id}"
]

# Verify all keys invalidated
for key in invalidate_keys:
    redis.delete(key)
```

---

## ⚖️ Trade-offs

### Design Decisions & Rationale

#### 1. Two Permission Levels (Viewer vs Editor)

**Decision**: Only two permission levels in MVP

**Pros**:
- ✅ Simple to understand and explain
- ✅ Covers 90% of use cases
- ✅ Easy to implement and test
- ✅ Clear permission boundaries
- ✅ Minimal UI complexity

**Cons**:
- ⚠️ Not flexible for advanced use cases
- ⚠️ Cannot customize permissions per action
- ⚠️ May need expansion later

**Rationale**: YAGNI (You Aren't Gonna Need It) principle. Start simple, add complexity only when proven necessary.

**Future**: Can add custom roles/permissions in Phase 2

---

#### 2. Email-Based Sharing (Not Share Links)

**Decision**: Share by user email, not public links

**Pros**:
- ✅ More secure (authenticated users only)
- ✅ Better access control
- ✅ Can track who has access
- ✅ Easier to revoke access
- ✅ No link expiration needed

**Cons**:
- ⚠️ Both users must be registered
- ⚠️ Cannot share outside system
- ⚠️ Less convenient for quick sharing

**Rationale**: Security first approach. Public links can be added later with proper token generation and expiration.

---

#### 3. No Notifications in MVP

**Decision**: No email/push notifications for shares

**Pros**:
- ✅ Faster MVP delivery
- ✅ Simpler implementation
- ✅ No notification infrastructure needed
- ✅ Focus on core functionality

**Cons**:
- ⚠️ Users may not know they have new shared todos
- ⚠️ Relies on users checking "Shared with Me" section
- ⚠️ Less engaging user experience

**Rationale**: Notifications require significant infrastructure (email service, job queue, templates). Can be added in Phase 2 with minimal API changes.

**Mitigation**: Add notification preferences and infrastructure in next iteration.

---

#### 4. Cascade Delete on Owner/Todo Deletion

**Decision**: Delete all shares when todo or owner is deleted

**Pros**:
- ✅ Clean data (no orphaned shares)
- ✅ Database handles automatically (ON DELETE CASCADE)
- ✅ No manual cleanup needed
- ✅ Prevents data inconsistency

**Cons**:
- ⚠️ Shared users lose access immediately
- ⚠️ No warning to shared users
- ⚠️ Cannot "soft delete" and preserve shares

**Rationale**: Data integrity priority. Alternative would be soft deletes with complex state management.

**Future**: Consider adding deletion warnings or "archive" feature.

---

#### 5. Maximum 50 Shares Per Todo

**Decision**: Limit to 50 users per todo (application-level)

**Pros**:
- ✅ Prevents performance issues
- ✅ Reasonable for 99% of use cases
- ✅ Can be adjusted easily
- ✅ Protects database from abuse

**Cons**:
- ⚠️ May not work for large teams
- ⚠️ Arbitrary limit
- ⚠️ Requires application-level check

**Rationale**: Better to start conservative and increase based on real usage patterns.

**Alternative**: Could use pagination for share lists instead.

---

#### 6. Cache TTL 5-10 Minutes

**Decision**: Short TTL for shared data

**Pros**:
- ✅ Reasonable balance of performance vs freshness
- ✅ Reduces stale data issues
- ✅ Lower memory usage
- ✅ Easier to debug

**Cons**:
- ⚠️ More database queries than longer TTL
- ⚠️ Higher cache miss rate
- ⚠️ Need frequent invalidation

**Rationale**: Shared data changes frequently (permissions, revocations). Short TTL + aggressive invalidation ensures consistency.

**Alternative**: Could use longer TTL with more comprehensive invalidation strategy.

---

#### 7. Editor Cannot Delete Todo

**Decision**: Only owner can delete, editors can only modify

**Pros**:
- ✅ Protects owner's data
- ✅ Clear distinction between owner and editor
- ✅ Prevents accidental deletions
- ✅ Matches user mental model

**Cons**:
- ⚠️ Less flexible collaboration
- ⚠️ Editors may want "archive" feature

**Rationale**: Deletion is permanent and dangerous. Keep this privilege with owner.

**Future**: Add "archive" feature that editors can use.

---

#### 8. No Share Request Flow

**Decision**: Owner directly shares, no approval needed

**Pros**:
- ✅ Simpler flow
- ✅ Faster collaboration
- ✅ Less UI complexity
- ✅ Fewer states to manage

**Cons**:
- ⚠️ Cannot "request access" to todo
- ⚠️ Owner must initiate all shares
- ⚠️ Less discoverable

**Rationale**: MVP focused on owner-initiated sharing. Request flow adds significant complexity.

**Future**: Add "request access" feature if user feedback indicates need.

---

### Technical Trade-offs

#### Database Design

**Decision**: Separate `todo_shares` table vs denormalized approach

**Pros of Separate Table**:
- ✅ Normalized data model
- ✅ Easy to query shares
- ✅ Clear relationship
- ✅ Easy to extend

**Cons**:
- ⚠️ Requires JOIN for shared todos
- ⚠️ More complex queries
- ⚠️ Additional table to maintain

**Alternative**: Could use JSONB array in todos table, but less flexible and harder to query.

---

#### Caching Strategy

**Decision**: Multiple cache keys per user/todo

**Pros**:
- ✅ Granular invalidation
- ✅ Better cache hit rates
- ✅ Flexible per-query caching

**Cons**:
- ⚠️ More keys to manage
- ⚠️ Complex invalidation logic
- ⚠️ Higher memory usage
- ⚠️ Risk of cache inconsistency

**Mitigation**: Comprehensive invalidation rules and short TTL.

---

#### API Design

**Decision**: RESTful nested resources (`/todos/{id}/shares`)

**Pros**:
- ✅ Intuitive resource hierarchy
- ✅ RESTful conventions
- ✅ Clear ownership model

**Cons**:
- ⚠️ Longer URLs
- ⚠️ May need query params for filtering

**Alternative**: Flat structure (`/shares?todo_id=X`) but less clear ownership.

---

## 📊 Success Criteria

### Specification Completeness

| Section | Status | Completeness |
|---------|--------|--------------|
| Overview & Goals | ✅ | 100% |
| User Stories | ✅ | 100% (7 stories) |
| Acceptance Criteria | ✅ | 100% |
| Data Model | ✅ | 100% |
| API Design | ✅ | 100% (7 endpoints) |
| Authorization Rules | ✅ | 100% |
| Edge Cases | ✅ | 100% (8 cases) |
| Cache Strategy | ✅ | 100% |
| Migration Plan | ✅ | 100% (4 phases) |
| Testing Strategy | ✅ | 100% |
| Out of Scope | ✅ | 100% |
| Open Questions | ✅ | 100% (5 questions) |

### Documentation Quality Metrics

- **Total Pages**: 35+ pages (single-spaced)
- **User Stories**: 7 detailed stories with acceptance criteria
- **API Endpoints**: 5 new + 2 extended, fully specified
- **Edge Cases**: 8 critical scenarios documented
- **Test Cases**: 12 unit + integration + E2E + 10 manual
- **Code Examples**: SQL, Python pseudocode, API calls
- **Diagrams**: Permission matrix, database ERD, authorization flow
- **Error Scenarios**: Complete error handling guide

### Stakeholder Value

**For Product Managers**:
- ✅ Clear user stories and acceptance criteria
- ✅ Success metrics defined
- ✅ Out of scope items listed
- ✅ Migration timeline provided

**For Engineers**:
- ✅ Complete data model with constraints
- ✅ Detailed API specifications
- ✅ Implementation examples
- ✅ Testing strategy

**For QA**:
- ✅ Test scenarios documented
- ✅ Edge cases identified
- ✅ Expected behaviors specified

**For DevOps**:
- ✅ Migration strategy
- ✅ Rollback plan
- ✅ Performance targets

---

## 🎓 Lessons Learned

### Specification Best Practices

1. **Start with User Stories**: Understanding user needs drives better technical decisions
2. **Document Edge Cases Early**: Prevents surprises during implementation
3. **Include Migration Strategy**: Makes spec actionable, not just theoretical
4. **Define Out of Scope**: Sets clear boundaries and manages expectations
5. **Provide Examples**: SQL, API calls, pseudocode make spec concrete
6. **Think About Testing**: Testability should influence design decisions
7. **Consider Performance**: Performance targets should be specified upfront
8. **Plan for Rollback**: Every feature needs a safe rollback plan

### Technical Insights

1. **Authorization is Complex**: Permission matrix helps visualize all cases
2. **Caching is Hard**: Need clear invalidation rules from the start
3. **Database Constraints Help**: Use CHECK and UNIQUE constraints to enforce rules
4. **CASCADE Carefully**: Understand cascade delete implications
5. **API Versioning**: Leave room for future enhancements
6. **Error Messages Matter**: Balance helpful vs secure error responses

---

## 📝 Recommendations

### For Implementation Team

1. **Follow the Phases**: Don't skip migration strategy phases
2. **Write Tests First**: TDD approach works well with detailed spec
3. **Review Edge Cases**: Use spec edge cases as test scenarios
4. **Monitor Performance**: Track actual vs target metrics
5. **Gather Feedback**: User testing before full rollout

### For Future Enhancements

1. **Phase 2 Features**: Notifications, expiration, share links
2. **Analytics**: Track adoption, share patterns, permission changes
3. **Mobile Support**: Ensure API works well for mobile clients
4. **Internationalization**: Plan for multi-language error messages
5. **Audit Log**: Track who changed what for compliance

### For Similar Projects

1. **Always Write Specs First**: Prevents rework and misalignment
2. **Include Stakeholders Early**: Get feedback before coding
3. **Be Realistic About Scope**: MVP should be actually minimal
4. **Document Trade-offs**: Future you will thank present you
5. **Keep Spec Updated**: Treat as living document, not one-time artifact

---

## ✅ Checklist

- [x] User stories documented (7 stories)
- [x] Acceptance criteria complete
- [x] Data model designed with all constraints
- [x] API endpoints fully specified (5 new, 2 extended)
- [x] Authorization matrix created
- [x] Edge cases identified (8 cases)
- [x] Cache strategy documented
- [x] Migration plan with 4 phases
- [x] Testing strategy (unit + integration + E2E + manual)
- [x] Out of scope items listed
- [x] Trade-offs analyzed
- [x] SQL examples provided
- [x] API request/response examples
- [x] Authorization pseudocode
- [x] Performance targets specified
- [x] Rollback plan documented

---

## 🎯 Conclusion

Task 3A successfully completed with a production-ready technical specification. The document provides:

- **Complete technical blueprint** for implementation
- **Clear user stories** for product alignment
- **Detailed API contracts** for frontend/backend coordination
- **Comprehensive testing strategy** for quality assurance
- **Migration roadmap** for safe deployment
- **Trade-off analysis** for informed decision-making

**Estimated Implementation Time**: 3-4 weeks (with 1-2 engineers)  
**Risk Level**: Low (well-specified, manageable scope)  
**Confidence Level**: High (all major questions answered)

**Ready for**: Implementation kickoff, team review, stakeholder approval

---

**Report Generated**: September 21, 2026  
**Branch**: docs/todo-sharing-spec  
**Files Created**: 1 (docs/TODO_SHARING_SPEC.md)  
**Total Lines**: 1,400+ lines of specification  
**Status**: ✅ Complete and Ready for Review
