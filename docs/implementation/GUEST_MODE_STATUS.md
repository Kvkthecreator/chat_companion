# Guest Mode Implementation Status

> **Last Updated**: 2026-01-14
> **Status**: Backend Complete, Frontend Partial

---

## ✅ COMPLETED

### Phase 1: Database Migration
- ✅ Created [/supabase/migrations/059_guest_sessions.sql](../../supabase/migrations/059_guest_sessions.sql)
  - Made `user_id` nullable in sessions
  - Added guest tracking columns (`guest_session_id`, `guest_ip_hash`, `guest_created_at`, `guest_converted_at`)
  - Updated RLS policies for guest access
  - Added cleanup function for expired sessions
  - **Status**: Ready to run migration

### Phase 2: Backend API
- ✅ Updated [/substrate-api/api/src/app/routes/sessions.py](../../substrate-api/api/src/app/routes/sessions.py)
  - `POST /sessions/guest` - Create guest session (with IP rate limiting)
  - `POST /sessions/guest/convert` - Convert guest to authenticated

- ✅ Updated [/substrate-api/api/src/app/routes/conversation.py](../../substrate-api/api/src/app/routes/conversation.py)
  - Modified `POST /conversation/{character_id}/send` to accept guest sessions
  - Added `X-Guest-Session-Id` header support
  - Enforced 5-message limit for guests

- ✅ Updated [/substrate-api/api/src/app/services/conversation.py](../../substrate-api/api/src/app/services/conversation.py)
  - Made `user_id` optional in `send_message()` and `get_context()`
  - Skip analytics, rate limiting, memories, hooks for guests
  - Support guest session lookup by `guest_session_id`

### Phase 3: Frontend (Partial)
- ✅ Created [/web/src/hooks/useGuestSession.ts](../../web/src/hooks/useGuestSession.ts)
  - Manages guest session state in localStorage
  - Tracks messages remaining
  - Handles session conversion

- ✅ Updated [/web/src/lib/api/client.ts](../../web/src/lib/api/client.ts)
  - Added `X-Guest-Session-Id` header injection
  - Added `api.episodes.createGuest()` endpoint
  - Added `api.episodes.convertGuest()` endpoint

- ✅ Middleware [/web/src/lib/supabase/middleware.ts](../../web/src/lib/supabase/middleware.ts)
  - Already correct - `/chat` routes are NOT protected
  - Guests can access chat pages

---

## 🚧 IN PROGRESS / TODO

### Frontend Components (Still Needed)

#### 1. Update ChatContainer
**File**: `/web/src/components/chat/ChatContainer.tsx`

**Changes needed**:
```typescript
// Add to ChatContainer props or internal state
const { guestSessionId, isGuest, messagesRemaining, createGuestSession, clearGuestSession } = useGuestSession();
const { user } = useAuth(); // Supabase auth

// Initialize guest session if not authenticated
useEffect(() => {
  if (!user && episodeTemplateId && !guestSessionId) {
    // Create guest session for Episode 0
    api.episodes.createGuest({
      character_id: characterId,
      episode_template_id: episodeTemplateId,
    })
      .then((response) => {
        createGuestSession({
          guest_session_id: response.guest_session_id,
          session_id: response.session_id,
          messages_remaining: response.messages_remaining,
        });
      })
      .catch(console.error);
  }
}, [user, episodeTemplateId, characterId, guestSessionId]);

// Convert guest session after login
useEffect(() => {
  if (user && guestSessionId) {
    api.episodes.convertGuest(guestSessionId)
      .then(() => {
        clearGuestSession();
        window.location.reload(); // Reload to show authenticated session
      })
      .catch(console.error);
  }
}, [user, guestSessionId]);

// Show signup modal when message limit reached
const handleMessageLimitReached = () => {
  setShowSignupModal(true);
};

// Guest indicator
{isGuest && messagesRemaining !== null && (
  <div className="guest-indicator">
    {messagesRemaining} messages remaining •
    <button onClick={() => setShowSignupModal(true)}>Sign up free</button>
  </div>
)}
```

#### 2. Create SignupModal Component
**File**: `/web/src/components/guest/SignupModal.tsx` (NEW)

```typescript
interface SignupModalProps {
  onClose: () => void;
  guestSessionId: string | null;
  trigger: 'message_limit' | 'memory_snapshot';
}

export function SignupModal({ onClose, guestSessionId, trigger }: SignupModalProps) {
  const handleSignup = () => {
    // Store guest session ID for conversion after login
    if (guestSessionId) {
      sessionStorage.setItem('converting_guest_session', guestSessionId);
    }
    window.location.href = '/login?next=' + window.location.pathname;
  };

  return (
    <Modal open onClose={onClose}>
      <h2>
        {trigger === 'message_limit'
          ? "You've reached the message limit"
          : "Sign up to see what happens next"}
      </h2>
      <p>Create an account to continue and unlock all episodes.</p>
      <ul>
        <li>✓ Unlimited messages</li>
        <li>✓ Your choices are remembered</li>
        <li>✓ Continue through all 8 episodes</li>
      </ul>
      <Button onClick={handleSignup}>Continue with Google</Button>
      <Button variant="secondary" onClick={onClose}>Not now</Button>
    </Modal>
  );
}
```

#### 3. Create GuestBanner Component (Optional)
**File**: `/web/src/components/guest/GuestBanner.tsx` (NEW)

```typescript
interface GuestBannerProps {
  messagesRemaining: number;
  onSignup: () => void;
}

export function GuestBanner({ messagesRemaining, onSignup }: GuestBannerProps) {
  return (
    <div className="guest-banner">
      <span>Trial mode: {messagesRemaining} messages remaining</span>
      <button onClick={onSignup}>Sign up free</button>
    </div>
  );
}
```

---

## 📝 DEPLOYMENT CHECKLIST

### Before Deploying

- [ ] Run database migration: `psql $DATABASE_URL -f supabase/migrations/059_guest_sessions.sql`
- [ ] Verify migration succeeded: `psql $DATABASE_URL -c "\d sessions"`
- [ ] Test guest session creation locally
- [ ] Test message sending as guest
- [ ] Test 5-message limit enforcement
- [ ] Test session conversion after signup

### Deploy Sequence

1. **Database First**
   ```bash
   # Run migration on production database
   psql $PRODUCTION_DATABASE_URL -f supabase/migrations/059_guest_sessions.sql
   ```

2. **Backend Second**
   ```bash
   # Deploy backend API
   # (your deployment process)
   ```

3. **Frontend Third**
   - Complete ChatContainer updates
   - Create SignupModal component
   - Deploy frontend
   ```bash
   # (your deployment process)
   ```

4. **Set up cron job** for guest session cleanup
   ```sql
   -- Run daily at 2 AM UTC
   SELECT cleanup_expired_guest_sessions();
   ```

### Rollback Plan

If issues arise:

1. **Immediate**: Disable guest endpoint
   ```python
   # In sessions.py
   @router.post("/guest", ...)
   async def create_guest_session(...):
       raise HTTPException(503, "Guest mode temporarily disabled")
   ```

2. **Within 1 hour**: Revert frontend to require login
   ```typescript
   // In middleware.ts
   const isProtectedRoute =
     path.startsWith('/dashboard') ||
     path.startsWith('/studio') ||
     path.startsWith('/admin') ||
     path.startsWith('/chat')  // ← Add this back
   ```

3. **Within 4 hours**: Rollback database migration
   ```sql
   -- Make user_id required again
   ALTER TABLE sessions ALTER COLUMN user_id SET NOT NULL;
   -- Drop guest columns
   ALTER TABLE sessions
     DROP COLUMN guest_session_id,
     DROP COLUMN guest_created_at,
     DROP COLUMN guest_ip_hash,
     DROP COLUMN guest_converted_at;
   ```

---

## 🧪 TESTING PLAN

### Manual Testing Flow

1. **Guest Session Creation**
   - [ ] Anonymous user visits `/series/death-flag-deleted`
   - [ ] Clicks "Start Episode 0"
   - [ ] Redirects to `/chat/[characterId]?episode=[ep0-id]`
   - [ ] Guest session auto-creates
   - [ ] Opening message appears immediately

2. **Guest Messaging**
   - [ ] User sends 5 messages
   - [ ] Each response works correctly
   - [ ] Message counter decrements

3. **Message Limit**
   - [ ] After 5th message, signup modal appears
   - [ ] Cannot send 6th message
   - [ ] Error message is clear

4. **Session Conversion**
   - [ ] User clicks "Sign up with Google"
   - [ ] Completes OAuth flow
   - [ ] Returns to chat
   - [ ] All previous messages visible
   - [ ] Can continue chatting (no limit)

5. **IP Rate Limiting**
   - [ ] Create 3 guest sessions from same IP
   - [ ] 4th attempt gets 429 error
   - [ ] Error message suggests signup

### Automated Testing (Future)

```python
# Backend tests
def test_guest_session_creation():
    """Test POST /sessions/guest"""
    pass

def test_guest_message_limit():
    """Test 5-message limit enforcement"""
    pass

def test_guest_session_conversion():
    """Test POST /sessions/guest/convert"""
    pass

def test_ip_rate_limiting():
    """Test 3 sessions per IP limit"""
    pass
```

---

## 📊 SUCCESS METRICS

### Week 1 (Technical Health)
- Guest session creation success rate > 95%
- Message send success rate > 95%
- Session conversion success rate > 90%
- Error rate < 2%

### Week 2-4 (Business Impact)
- Guest trial rate: 60% of series visitors
- Guest → signup conversion: 25%
- Overall activation rate: 60% (vs 25% current)
- Cost per activation: <$12 (vs $34.56 current)

---

## 🔗 RELATED FILES

**Documentation**:
- [GUEST_MODE_IMPLEMENTATION.md](./GUEST_MODE_IMPLEMENTATION.md) - Full technical spec

**Database**:
- [059_guest_sessions.sql](../../supabase/migrations/059_guest_sessions.sql) - Migration file

**Backend**:
- [routes/sessions.py](../../substrate-api/api/src/app/routes/sessions.py) - Guest endpoints
- [routes/conversation.py](../../substrate-api/api/src/app/routes/conversation.py) - Guest messaging
- [services/conversation.py](../../substrate-api/api/src/app/services/conversation.py) - Guest support

**Frontend**:
- [hooks/useGuestSession.ts](../../web/src/hooks/useGuestSession.ts) - Guest state management
- [lib/api/client.ts](../../web/src/lib/api/client.ts) - API client updates
- [components/chat/ChatContainer.tsx](../../web/src/components/chat/ChatContainer.tsx) - Needs updates

---

## 🎯 NEXT STEPS

1. **Complete ChatContainer integration** (2-3 hours)
   - Add guest session initialization
   - Add conversion logic after login
   - Add message limit handling

2. **Create SignupModal component** (1-2 hours)
   - Design modal UI
   - Implement conversion flow
   - Add to ChatContainer

3. **Run database migration** (5 minutes)
   - Test in local/staging first
   - Deploy to production

4. **Test end-to-end** (1-2 hours)
   - Manual QA of full guest flow
   - Verify all edge cases

5. **Deploy** (1 hour)
   - Backend first
   - Frontend second
   - Monitor logs

**Total remaining effort**: ~5-8 hours

---

**Status**: Ready for final implementation push!
