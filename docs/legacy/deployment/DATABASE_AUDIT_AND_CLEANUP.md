# Database Audit & Cleanup Plan
**Date**: 2025-11-04
**Purpose**: Prepare production database for owner testing of Phase 6 onboarding

---

## Current State Audit

### Users (auth.users)
- **Total**: 11 users
- **Test accounts**: 3 (e2e.test@yarnnn.com, test@example.com, playwright.test@yarnnn.com)
- **Owner accounts**: 2 (kvkthecreator@gmail.com, kvkthecreator@yarnnn.com)
- **Other users**: 6 (aarikgulaya, steven, haydenkai, ziyanda, youuna.k)

### Workspaces
- **Total**: 6 workspaces
- **Workspace ownership**: Linked to user IDs above
- **Default workspace pattern**: "My Workspace" auto-created on signup

### Data State
| Table | Count | Notes |
|-------|-------|-------|
| baskets | 1 | Minimal test data |
| raw_dumps | 3 | Minimal test data |
| documents | 2 | Minimal test data |
| agent_work_requests | 0 | **Empty - Phase 5 table** |
| workspace_memberships | 6 | Matches workspace count |

### Phase 5 Trial Status
- **agent_work_requests** table is empty
- All users have **10 free trials remaining** (clean slate)

---

## Cleanup Strategy

### Option 1: Full Reset (Recommended for Pre-Production)
**Delete all test data, keep only owner account**

**Advantages:**
- Clean slate for testing
- No confusion from old data
- Simulates new user experience

**Steps:**
1. Delete all test accounts (e2e.test, test@example.com, playwright.test)
2. Delete all non-owner user accounts (optionally keep aarikgulaya if needed)
3. Keep kvkthecreator@gmail.com OR kvkthecreator@yarnnn.com (your choice)
4. CASCADE delete will clean up: workspaces, baskets, documents, raw_dumps

### Option 2: Selective Cleanup (Keep Specific Users)
**Keep certain users, delete test accounts only**

**Who to keep:**
- kvkthecreator@gmail.com (owner)
- kvkthecreator@yarnnn.com (owner)
- aarikgulaya@gmail.com (if active collaborator)

**Who to delete:**
- playwright.test@yarnnn.com
- e2e.test@yarnnn.com
- test@example.com
- steven@travelle.inc (unless needed)
- haydenkai@gmail.com (unless needed)
- ziyanda.ndabisa@gmail.com (unless needed)
- youuna.k@gmail.com (unless needed)

---

## Recommended Cleanup Script

### Step 1: Backup Current State (Safety)
```sql
-- Create backup of users before deletion
CREATE TABLE IF NOT EXISTS auth.users_backup_2025_11_04 AS
SELECT * FROM auth.users;

-- Backup workspaces
CREATE TABLE IF NOT EXISTS workspaces_backup_2025_11_04 AS
SELECT * FROM workspaces;
```

### Step 2: Delete Test Accounts
```sql
-- Delete test accounts (CASCADE will clean up related data)
DELETE FROM auth.users
WHERE email IN (
  'playwright.test@yarnnn.com',
  'e2e.test@yarnnn.com',
  'test@example.com'
);
```

### Step 3 (OPTIONAL): Delete Other Users
```sql
-- Only run if you want FULL cleanup
-- Review carefully before executing!
DELETE FROM auth.users
WHERE email NOT IN (
  'kvkthecreator@gmail.com',
  'kvkthecreator@yarnnn.com'
);
```

### Step 4: Verify Cleanup
```sql
-- Check remaining users
SELECT email, id, created_at FROM auth.users ORDER BY created_at;

-- Check remaining workspaces
SELECT id, owner_id, name FROM workspaces;

-- Check data counts
SELECT 'baskets' as table_name, COUNT(*) FROM baskets
UNION ALL SELECT 'raw_dumps', COUNT(*) FROM raw_dumps
UNION ALL SELECT 'documents', COUNT(*) FROM documents
UNION ALL SELECT 'agent_work_requests', COUNT(*) FROM agent_work_requests;
```

---

## Post-Cleanup Testing Plan

### 1. Login/Signup Flow Verification
- **Test**: Navigate to production login page
- **Verify**: Supabase auth redirects work correctly
- **Check**: Dashboard redirect after login
- **Confirm**: User session persists

### 2. Dashboard State
- **Current**: Unknown (need to check frontend)
- **Required**: Landing page after login
- **Phase 6 Integration**: Add temporary button for new onboarding

### 3. Phase 6 Onboarding Test
Once cleaned up, you should be able to:
1. Login as kvkthecreator@gmail.com (or @yarnnn.com)
2. Land on /dashboard
3. Click "New Onboarding" button (to be added)
4. Fill out onboarding form:
   - Agent type: research/content/reporting
   - Initial context: "Test Phase 6 onboarding flow"
   - Basket name: "Phase 6 Test Basket"
5. Submit → POST /api/work-requests/new
6. Verify response:
   - work_request_id created
   - basket_id created
   - dump_id created
   - remaining_trials: 10 → 9

---

## Frontend Integration Points

### Files to Check/Modify
1. **Login/Signup Page**
   - Location: Likely in `web/` directory (Next.js app)
   - Verify: Supabase auth integration
   - Check: Redirect to `/dashboard` after login

2. **Dashboard Page**
   - Location: `web/app/dashboard/page.tsx` (or similar)
   - Current state: Unknown
   - Required: Add temporary "New Onboarding" button
   - Modal: Similar to current "new basket" flow

3. **Onboarding Modal/Flow**
   - Create new modal component
   - Form fields:
     - Agent type dropdown (research, content, reporting)
     - Initial context textarea
     - Basket name input (optional, auto-generated if empty)
   - Submit handler: POST /api/work-requests/new

---

## Questions to Resolve

1. **Which owner account to keep?**
   - kvkthecreator@gmail.com
   - kvkthecreator@yarnnn.com
   - Both?

2. **Keep any collaborators?**
   - aarikgulaya@gmail.com?
   - Others?

3. **Frontend repo location?**
   - Is it in `/web` directory?
   - Separate repo?
   - Need to check current dashboard implementation

4. **Current login flow?**
   - Supabase hosted UI?
   - Custom login page?
   - OAuth providers?

---

## Next Steps

1. **Get your approval** on cleanup scope (Option 1 or 2)
2. **Execute cleanup** (with backup first)
3. **Verify login flow** (check frontend redirect)
4. **Locate dashboard** page in frontend code
5. **Add onboarding button** to dashboard
6. **Test end-to-end** Phase 6 flow

**Ready to proceed?** Let me know which cleanup option you prefer, and whether you want me to check the frontend codebase first.
