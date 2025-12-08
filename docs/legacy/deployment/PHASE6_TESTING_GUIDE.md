# Phase 6 Testing Guide
**Date**: 2025-11-04
**For**: Manual testing by product owner

---

## ✅ Ready to Test!

Phase 6 (Basket-First Onboarding) is fully deployed and ready for your testing:

### Backend Deployed ✅
- Commit: `218e4675` - Phase 6: Basket-First Onboarding Implementation
- POST /api/work-requests/new (work-platform)
- POST /api/baskets (substrate-api)
- Onboarding scaffolder service
- All services live and healthy

### Frontend Deployed ✅
- Commit: `18fcaf99` - Fix Vercel build error: Correct UI component imports
- Previous: `dc99d36f` - Phase 6: Frontend - New Onboarding Button & Dialog
- New Onboarding button in dashboard header
- NewOnboardingDialog modal component
- Form validation and error handling
- **FIXED**: Import paths for Dialog and Select components (lowercase)

---

## Testing Instructions

### Prerequisites
- ✅ Your account exists (kvkthecreator@gmail.com OR kvkthecreator@yarnnn.com)
- ✅ Workspace already created
- ✅ **10 free trials remaining** (agent_work_requests table is empty)
- ✅ No database cleanup needed!

### Step 1: Login to Production
1. Navigate to: https://rightnow-agent-app-fullstack.onrender.com (or your frontend URL)
2. Login with your existing account
3. Should redirect to `/dashboard`

### Step 2: Find the Onboarding Button
1. On the dashboard page, look at the **top right** of the "Control Tower" header
2. You should see a blue button: **"🚀 New Onboarding (Phase 6)"**
3. Click the button to open the dialog

### Step 3: Fill Out the Form
The dialog will show a form with 3 fields:

#### **Agent Type** (Required)
- Dropdown with 3 options:
  - Research Agent
  - Content Agent
  - Reporting Agent
- **Test with**: "Research Agent"

#### **Initial Context** (Required)
- Large text area
- Min: 10 characters
- Max: 50,000 characters
- **Test with**:
  ```
  Research the latest developments in AI-powered knowledge management systems.
  Focus on:
  1. Multi-agent collaboration frameworks
  2. Context-aware document processing
  3. Semantic search implementations
  4. Real-time knowledge graph updates

  Provide a comprehensive analysis with examples and best practices.
  ```

#### **Basket Name** (Optional)
- Text input
- Max: 200 characters
- **Test with**: "AI Knowledge Management Research"
- **Or leave blank** to test auto-generation

### Step 4: Submit and Verify

1. **Click "Create Work Request"**
2. **Wait for response** (loading state shows "Creating...")

3. **Success Case** - You should see:
   - Alert popup with details:
     - ✅ Basket created successfully!
     - Basket ID: `[uuid]`
     - Work Request ID: `[uuid]`
     - Remaining Trials: `9` (was 10, now 9)
     - Next step: Use POST /api/agents/run with basket_id
   - **Automatic redirect** to `/baskets/[basket_id]/overview`
   - Dashboard refreshes to show new basket

4. **Error Cases to Test**:
   - Leave "Initial Context" empty → Should show error
   - Enter only 5 characters → Should show "Minimum 10 characters"
   - Submit 10 times → Should see "Trial exhausted" on 11th request

---

## Expected Results

### Database Changes

After successful submission, check these tables:

#### **baskets** table
```sql
SELECT id, name, workspace_id, user_id, status, origin_template, created_at
FROM baskets
WHERE origin_template = 'work_platform_onboarding'
ORDER BY created_at DESC
LIMIT 1;
```
**Expected**:
- New row with your basket
- `name`: "AI Knowledge Management Research" (or auto-generated)
- `status`: "INIT"
- `origin_template`: "work_platform_onboarding"
- `user_id`: Your user UUID
- `workspace_id`: Your workspace UUID

#### **raw_dumps** table
```sql
SELECT id, basket_id, content, metadata, created_at
FROM raw_dumps
ORDER BY created_at DESC
LIMIT 1;
```
**Expected**:
- New row with initial context
- `content`: Your text from the form
- `basket_id`: Matches the basket created above
- `metadata`: Contains agent_type, work_mode, source

#### **agent_work_requests** table
```sql
SELECT
  id, user_id, workspace_id, basket_id, agent_type, work_mode,
  request_payload, is_trial_request, created_at
FROM agent_work_requests
ORDER BY created_at DESC
LIMIT 1;
```
**Expected**:
- New row for your work request
- `agent_type`: "research"
- `basket_id`: Matches basket above
- `is_trial_request`: `true`
- `request_payload`: Contains basket_name, initial_context excerpt

#### **Trial Counter Check**
```sql
SELECT
  u.email,
  COUNT(awr.id) as requests_used,
  (10 - COUNT(awr.id)) as requests_remaining
FROM auth.users u
LEFT JOIN agent_work_requests awr ON awr.user_id = u.id
WHERE u.email = 'kvkthecreator@gmail.com'  -- or your email
GROUP BY u.email;
```
**Expected**:
- `requests_used`: 1
- `requests_remaining`: 9

---

## Frontend Behavior Verification

### Dashboard After Success
1. **Basket appears** in "Context Baskets" section
2. **Count updated** (if it was 0, now shows 1)
3. **Basket card** clickable → redirects to basket detail page

### Basket Detail Page
1. Navigate to the new basket
2. Should show:
   - Basket name from form
   - Status: "INIT"
   - Created timestamp
   - Raw dump visible (your initial context)

---

## Testing Different Scenarios

### Scenario 1: Happy Path (Above)
- ✅ All fields filled correctly
- ✅ Success message shown
- ✅ Trial counter decrements
- ✅ Basket created and visible

### Scenario 2: Auto-Generated Basket Name
- Leave "Basket Name" field **empty**
- Expected basket name: `"Research Work - [first 8 chars of user_id]"`
- Example: `"Research Work - aa94fbd9"`

### Scenario 3: Different Agent Types
Test all 3 agent types:
- Research Agent → `agent_type: "research"`
- Content Agent → `agent_type: "content"`
- Reporting Agent → `agent_type: "reporting"`

### Scenario 4: Trial Exhaustion
1. Submit 10 work requests (use different contexts each time)
2. On the 11th request, should see error:
   ```
   403 Forbidden
   {
     "message": "Trial limit exhausted. Subscribe to continue.",
     "remaining_trials": 0,
     "agent_type": "research"
   }
   ```

### Scenario 5: Form Validation
- **Empty context**: Button disabled
- **< 10 chars**: Error message shown
- **> 50,000 chars**: Should be blocked by maxLength
- **Empty agent type**: Defaults to "research"

---

## Troubleshooting

### Issue 1: Button Not Visible
- **Check**: Frontend deployed? Look for commit `dc99d36f` in deployment logs
- **Fix**: Wait for frontend build to complete (~2-3 minutes)
- **Verify**: Hard refresh browser (Cmd+Shift+R)

### Issue 2: "Missing Token" Error
- **Cause**: Not logged in or session expired
- **Fix**: Logout and login again
- **Verify**: Check network tab for Authorization header

### Issue 3: "Failed to create basket" Error
- **Check**: Network tab → Response details
- **Common causes**:
  - Invalid workspace_id (check ensureWorkspaceForUser)
  - Database connection issue
  - RLS policy blocking insert
- **Debug**: Check Render logs for detailed error

### Issue 4: Success but No Redirect
- **Check**: Browser console for errors
- **Possible cause**: `/baskets/[id]/overview` route doesn't exist
- **Workaround**: Manually navigate to dashboard → Should see new basket

---

## Success Metrics

After testing, you should have verified:

- ✅ Login flow works (production auth)
- ✅ Dashboard loads correctly
- ✅ Button appears in header
- ✅ Dialog opens on click
- ✅ Form validation works
- ✅ Submission creates all 3 records (basket, raw_dump, work_request)
- ✅ Trial counter decrements correctly
- ✅ Success message shows correct IDs
- ✅ Redirect to basket detail works
- ✅ New basket appears in dashboard list

---

## Database Cleanup (If Needed)

If you want to reset and test again:

```sql
-- Delete test baskets created via onboarding
DELETE FROM baskets
WHERE origin_template = 'work_platform_onboarding';

-- Delete associated work requests (auto-deleted by CASCADE)
-- But if you want to verify:
DELETE FROM agent_work_requests
WHERE user_id = '[your-user-id]';

-- Note: raw_dumps will be CASCADE deleted with baskets
```

**Verify cleanup**:
```sql
SELECT COUNT(*) FROM agent_work_requests WHERE user_id = '[your-user-id]';
-- Should return 0 (10 trials restored)
```

---

## Next Steps After Testing

1. **Report results** - Document any issues found
2. **Frontend refinements** - Based on UX feedback
3. **Remove "Phase 6" label** - Once stable, remove emoji and version tag
4. **Production rollout** - Announce to users
5. **Monitor metrics**:
   - Trial usage patterns
   - Basket creation success rate
   - Error rates
   - User drop-off points

---

## Quick Reference

**URLs**:
- Frontend: https://rightnow-agent-app-fullstack.onrender.com
- Backend API: https://rightnow-agent-app-fullstack.onrender.com/api
- Dashboard: /dashboard
- Basket Detail: /baskets/[id]/overview

**Endpoints**:
- POST /api/work-requests/new (work-platform)
- POST /api/baskets (substrate-api via work-platform)
- POST /api/baskets/[id]/dumps (raw_dump creation)

**Database**:
- Host: aws-0-ap-northeast-2.pooler.supabase.com
- Tables: baskets, raw_dumps, agent_work_requests
- User: kvkthecreator@gmail.com (or @yarnnn.com)

**Commits**:
- Backend: `218e4675` - Phase 6: Basket-First Onboarding Implementation
- Frontend: `18fcaf99` - Fix Vercel build error: Correct UI component imports
- Frontend (initial): `dc99d36f` - Phase 6: Frontend - New Onboarding Button & Dialog

---

**Happy Testing! 🚀**

If you encounter any issues, check:
1. Browser console (JavaScript errors)
2. Network tab (API request/response details)
3. Render logs (backend errors)
4. Database state (verify records created)
