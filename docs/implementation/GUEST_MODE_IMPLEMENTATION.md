# Guest Mode Implementation Plan

> **Created**: 2026-01-14
> **Status**: Ready for Review
> **Objective**: Remove login gate for Episode 0 trials to increase activation rate from 25% to 60%+

---

## TL;DR

**Problem**: 75% of users bounce at the login gate before experiencing the product.

**Solution**: Allow anonymous users to chat for Episode 0 (up to 5 messages) before requiring signup.

**How it works**:
1. User clicks "Start Episode 0" → immediately in chat (no login)
2. Real AI conversation for 5 messages
3. "Sign up to continue" → all messages preserved and linked to account

**Expected Impact**:
- Trial rate: 20% → 60% (+200%)
- Activation rate: 25% → 60% (+140%)
- Cost per activation: $34.56 → $11.52 (-67%)

**Implementation Effort**: 16-24 hours
**Risk Level**: Low-Medium (mitigated with phased rollout)

---

## Quick Implementation Checklist

### Phase 1: Database (2-3 hours)
- [ ] Migration: Make `user_id` nullable in sessions
- [ ] Add `guest_session_id`, `guest_ip_hash`, `guest_created_at` columns
- [ ] Update RLS policies for guest access
- [ ] Add cleanup job for expired sessions

### Phase 2: Backend (6-8 hours)
- [ ] Endpoint: `POST /sessions/guest` (create guest session)
- [ ] Update: `POST /conversation/send` (accept guest header)
- [ ] Endpoint: `POST /sessions/guest/convert` (link to user)
- [ ] IP-based rate limiting (3 sessions/24h)
- [ ] Unit tests

### Phase 3: Frontend (6-8 hours)
- [ ] Hook: `useGuestSession` (localStorage management)
- [ ] Update: API client with `X-Guest-Session-Id` header
- [ ] Update: ChatContainer for guest mode
- [ ] Remove `/chat` from middleware protection
- [ ] Component: SignupModal with conversion
- [ ] Component: GuestBanner (messages remaining)

### Phase 4: Testing & Rollout (2-3 hours + 1 week)
- [ ] Integration tests
- [ ] Manual QA (full guest → signup → conversion flow)
- [ ] Security review (RLS policies)
- [ ] Soft launch (10% traffic, 2 days)
- [ ] Ramp to 50% (2 days)
- [ ] Full rollout (100%)

---

## Executive Summary

---

## Current Architecture Audit

### Authentication Flow (Middleware)

**File**: `/web/src/middleware.ts` + `/web/src/lib/supabase/middleware.ts`

**Current behavior**:
```
Request → Middleware → Check auth.getUser()
  ↓
If protected route + no user → Redirect to /login
```

**Protected routes**:
- `/dashboard/*`
- `/studio/*`
- `/admin/*`
- `/chat/*` ← **PROBLEM: Chat is login-gated**

**Impact**: Users can't access `/chat/[characterId]` without authentication.

---

### Session Management (Backend)

**File**: `/substrate-api/api/src/app/routes/sessions.py`
**Model**: `/substrate-api/api/src/app/models/session.py`

**Current session creation** (Line 217-270):
```python
@router.post("", response_model=Session, status_code=status.HTTP_201_CREATED)
async def create_session(
    data: SessionCreate,
    user_id: UUID = Depends(get_current_user_id),  # ← REQUIRES AUTH
    db=Depends(get_db),
):
```

**Session table** (`sessions` - formerly `episodes`):
```sql
CREATE TABLE sessions (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id),  -- ← REQUIRED
    character_id UUID NOT NULL,
    episode_template_id UUID,
    -- ... other fields
)
```

**RLS Policies**:
```sql
CREATE POLICY sessions_select_own ON sessions
    FOR SELECT USING (auth.uid() = user_id);  -- ← Requires auth
```

**Impact**: Cannot create sessions without authenticated `user_id`.

---

### Message Flow (Backend)

**File**: `/substrate-api/api/src/app/routes/conversation.py`

**Current send_message endpoint** (Line 19-65):
```python
@router.post("/{character_id}/send", response_model=Message)
async def send_message(
    character_id: UUID,
    data: MessageCreate,
    user_id: UUID = Depends(get_current_user_id),  # ← REQUIRES AUTH
    db=Depends(get_db),
):
```

**Impact**: Cannot send messages without authentication.

---

### Frontend Chat Flow

**File**: `/web/src/components/chat/ChatContainer.tsx` (739 lines)

**Current initialization**:
1. Component loads with `characterId` + optional `episodeTemplateId`
2. `useChat` hook initializes (line 120-192)
3. Hook calls backend APIs (authenticated via Supabase client)
4. Chat renders messages

**Impact**: All API calls require Supabase auth token in headers.

---

## Implementation Strategy

### Option A: Database Guest Sessions (RECOMMENDED)

**Approach**: Create real sessions with `user_id = NULL` for guests, convert on signup.

**Pros**:
- Real AI conversations (full experience)
- Clean conversion to permanent sessions
- Minimal frontend changes
- Can reuse existing conversation service

**Cons**:
- Database schema changes required
- RLS policies need updates
- Slightly more complex backend logic

**Verdict**: Best balance of UX and maintainability.

---

### Option B: Client-Side Only Trial

**Approach**: Mock conversation entirely in frontend, replay to backend on signup.

**Pros**:
- No database changes
- Simpler backend

**Cons**:
- Fake AI responses (defeats the purpose)
- OR complex client-side LLM integration (expensive, slow)
- Replay complexity on signup
- Doesn't prove product value

**Verdict**: ❌ Rejected - Users need to experience real AI to convert.

---

### Option C: Temporary Anonymous Users

**Approach**: Auto-create anonymous Supabase users, link to real user on signup.

**Pros**:
- Leverages existing auth system
- Minimal code changes

**Cons**:
- Clutters user table with anonymous users
- Complex user merging logic
- Supabase session management overhead

**Verdict**: ❌ Rejected - Over-engineered for this use case.

---

## Detailed Implementation Plan (Option A)

### Phase 1: Database Schema Updates

**File**: Create `/supabase/migrations/XXX_guest_sessions.sql`

#### 1.1 Make user_id nullable in sessions

```sql
-- Allow NULL user_id for guest sessions
ALTER TABLE sessions
ALTER COLUMN user_id DROP NOT NULL;

-- Add constraint: Either user_id OR guest_session_id must be set
ALTER TABLE sessions
ADD CONSTRAINT sessions_user_or_guest_check
CHECK (user_id IS NOT NULL OR guest_session_id IS NOT NULL);

-- Add guest session tracking
ALTER TABLE sessions
ADD COLUMN guest_session_id TEXT,
ADD COLUMN guest_created_at TIMESTAMPTZ,
ADD COLUMN guest_ip_hash TEXT,  -- For rate limiting by IP
ADD COLUMN guest_converted_at TIMESTAMPTZ;

-- Index for guest session lookups
CREATE INDEX idx_sessions_guest ON sessions(guest_session_id)
WHERE guest_session_id IS NOT NULL;

-- Index for guest session cleanup (expire after 24 hours)
CREATE INDEX idx_sessions_guest_expired ON sessions(guest_created_at)
WHERE user_id IS NULL AND guest_created_at < NOW() - INTERVAL '24 hours';
```

**Rationale**:
- `guest_session_id`: UUID stored in client localStorage for session continuity
- `guest_ip_hash`: SHA256 of IP for abuse prevention (rate limit 3 sessions/IP/day)
- `guest_created_at`: Track session age for cleanup
- `guest_converted_at`: Analytics - when guest became real user

---

#### 1.2 Update RLS policies to allow guest reads

```sql
-- Drop existing restrictive policy
DROP POLICY sessions_select_own ON sessions;

-- New policy: Allow selecting own sessions OR guest sessions by guest_session_id
CREATE POLICY sessions_select_own ON sessions
FOR SELECT USING (
    auth.uid() = user_id  -- Authenticated users see their own
    OR guest_session_id = current_setting('request.jwt.claim.guest_session_id', true)  -- Guests see their session
);

-- Update insert policy to allow guest sessions
DROP POLICY sessions_insert_own ON sessions;

CREATE POLICY sessions_insert_own ON sessions
FOR INSERT WITH CHECK (
    auth.uid() = user_id  -- Authenticated users create with their user_id
    OR (user_id IS NULL AND guest_session_id IS NOT NULL)  -- Guests create with guest_session_id
);

-- Prevent guests from updating sessions (read-only trial)
CREATE POLICY sessions_update_authenticated_only ON sessions
FOR UPDATE USING (auth.uid() = user_id);
```

**Note**: RLS with `guest_session_id` requires passing it via request headers or JWT claims. See implementation details below.

---

#### 1.3 Update messages RLS

```sql
-- Drop existing message policies
DROP POLICY messages_select_own ON messages;
DROP POLICY messages_insert_own ON messages;

-- Allow reading messages from guest sessions
CREATE POLICY messages_select_own ON messages
FOR SELECT USING (
    EXISTS (
        SELECT 1 FROM sessions
        WHERE sessions.id = messages.episode_id
        AND (
            sessions.user_id = auth.uid()  -- Authenticated user's session
            OR sessions.guest_session_id = current_setting('request.jwt.claim.guest_session_id', true)  -- Guest's session
        )
    )
);

-- Allow inserting messages to guest sessions
CREATE POLICY messages_insert_own ON messages
FOR INSERT WITH CHECK (
    EXISTS (
        SELECT 1 FROM sessions
        WHERE sessions.id = messages.episode_id
        AND (
            sessions.user_id = auth.uid()
            OR sessions.guest_session_id = current_setting('request.jwt.claim.guest_session_id', true)
        )
    )
);
```

---

#### 1.4 Guest session cleanup job

```sql
-- Function to delete expired guest sessions (>24 hours old, not converted)
CREATE OR REPLACE FUNCTION cleanup_expired_guest_sessions()
RETURNS void AS $$
BEGIN
    DELETE FROM sessions
    WHERE user_id IS NULL
    AND guest_session_id IS NOT NULL
    AND guest_created_at < NOW() - INTERVAL '24 hours'
    AND guest_converted_at IS NULL;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Schedule via pg_cron or external cron job
-- Example: SELECT cron.schedule('cleanup-guests', '0 2 * * *', 'SELECT cleanup_expired_guest_sessions()');
```

**Deployment note**: Set up cron job to run daily at 2 AM UTC.

---

### Phase 2: Backend API Updates

#### 2.1 New endpoint: Create guest session

**File**: `/substrate-api/api/src/app/routes/sessions.py`

Add after existing `create_session` endpoint:

```python
from datetime import datetime, timezone
import hashlib
import uuid as uuid_lib

class GuestSessionCreate(BaseModel):
    """Data for creating a guest session."""
    character_id: UUID
    episode_template_id: UUID  # Always Episode 0 for guests
    guest_session_id: Optional[str] = None  # Client-provided or generated

class GuestSessionResponse(BaseModel):
    """Response for guest session creation."""
    session_id: str
    guest_session_id: str
    messages_remaining: int  # 5 minus current message count
    episode_template_id: str

@router.post("/guest", response_model=GuestSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_guest_session(
    data: GuestSessionCreate,
    request: Request,
    db=Depends(get_db),
):
    """Create an anonymous guest session for Episode 0 trial.

    Rate limiting: Max 3 guest sessions per IP per 24 hours.
    Message limit: 5 messages per guest session.
    """
    # Get client IP for rate limiting
    forwarded_for = request.headers.get("X-Forwarded-For")
    client_ip = forwarded_for.split(",")[0].strip() if forwarded_for else request.client.host
    ip_hash = hashlib.sha256(client_ip.encode()).hexdigest()

    # Check IP-based rate limit (prevent abuse)
    count_query = """
        SELECT COUNT(*) as session_count
        FROM sessions
        WHERE guest_ip_hash = :ip_hash
        AND guest_created_at > NOW() - INTERVAL '24 hours'
    """
    row = await db.fetch_one(count_query, {"ip_hash": ip_hash})

    if row and row["session_count"] >= 3:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Guest session limit reached. Please sign up to continue."
        )

    # Verify episode template is Episode 0
    template_query = """
        SELECT episode_number, series_id
        FROM episode_templates
        WHERE id = :template_id
    """
    template = await db.fetch_one(template_query, {"template_id": str(data.episode_template_id)})

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Episode template not found"
        )

    if template["episode_number"] != 0:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Guest sessions only allowed for Episode 0"
        )

    # Generate or use provided guest_session_id
    guest_session_id = data.guest_session_id or str(uuid_lib.uuid4())

    # Check if guest session already exists (resuming)
    existing_query = """
        SELECT id, message_count
        FROM sessions
        WHERE guest_session_id = :guest_id
        AND user_id IS NULL
    """
    existing = await db.fetch_one(existing_query, {"guest_id": guest_session_id})

    if existing:
        # Resume existing session
        return GuestSessionResponse(
            session_id=str(existing["id"]),
            guest_session_id=guest_session_id,
            messages_remaining=max(0, 5 - (existing["message_count"] or 0)),
            episode_template_id=str(data.episode_template_id),
        )

    # Create new guest session
    query = """
        INSERT INTO sessions (
            user_id,
            character_id,
            episode_template_id,
            series_id,
            episode_number,
            guest_session_id,
            guest_created_at,
            guest_ip_hash,
            session_state
        )
        VALUES (
            NULL,
            :character_id,
            :episode_template_id,
            :series_id,
            0,
            :guest_session_id,
            :created_at,
            :ip_hash,
            'active'
        )
        RETURNING id
    """

    row = await db.fetch_one(
        query,
        {
            "character_id": str(data.character_id),
            "episode_template_id": str(data.episode_template_id),
            "series_id": str(template["series_id"]) if template["series_id"] else None,
            "guest_session_id": guest_session_id,
            "created_at": datetime.now(timezone.utc),
            "ip_hash": ip_hash,
        },
    )

    return GuestSessionResponse(
        session_id=str(row["id"]),
        guest_session_id=guest_session_id,
        messages_remaining=5,
        episode_template_id=str(data.episode_template_id),
    )
```

---

#### 2.2 Update conversation endpoint for guest support

**File**: `/substrate-api/api/src/app/routes/conversation.py`

Modify `send_message` endpoint:

```python
@router.post("/{character_id}/send", response_model=Message)
async def send_message(
    character_id: UUID,
    data: MessageCreate,
    request: Request,
    user_id: Optional[UUID] = Depends(get_optional_user_id),  # ← Change to optional
    db=Depends(get_db),
):
    """Send a message to a character and get a response.

    Supports both authenticated users and guest sessions.
    """
    # Extract guest_session_id from headers (if present)
    guest_session_id = request.headers.get("X-Guest-Session-Id")

    # Require either user_id OR guest_session_id
    if not user_id and not guest_session_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication or guest session ID required"
        )

    # Guest session validation
    if guest_session_id:
        # Verify session exists and belongs to this guest
        session_query = """
            SELECT id, message_count, episode_template_id, user_id
            FROM sessions
            WHERE guest_session_id = :guest_id
            AND character_id = :character_id
        """
        session = await db.fetch_one(session_query, {
            "guest_id": guest_session_id,
            "character_id": str(character_id),
        })

        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Guest session not found"
            )

        # Check if session was converted (has user_id)
        if session["user_id"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Session has been converted. Please log in."
            )

        # Enforce 5-message limit for guests
        if session["message_count"] >= 5:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "guest_message_limit",
                    "message": "You've reached the message limit. Sign up to continue!",
                    "messages_sent": session["message_count"],
                    "limit": 5,
                }
            )

        # Use guest session for conversation
        episode_id = session["id"]
        episode_template_id = session["episode_template_id"]
        effective_user_id = None  # No user_id for guests
    else:
        # Authenticated user flow (existing logic)
        effective_user_id = user_id
        # ... existing get_or_create_episode logic

    service = ConversationService(db)

    # Pass effective_user_id (can be None for guests)
    try:
        response = await service.send_message(
            user_id=effective_user_id,
            character_id=character_id,
            content=data.content,
            episode_template_id=data.episode_template_id,
            episode_id=episode_id if guest_session_id else None,  # Use existing for guests
        )
        return response
    except ... # existing error handling
```

**New dependency**: Create `get_optional_user_id` in `/substrate-api/api/src/app/dependencies.py`:

```python
async def get_optional_user_id(request: Request) -> Optional[UUID]:
    """Get current user ID if authenticated, None otherwise."""
    try:
        return await get_current_user_id(request)
    except HTTPException:
        return None
```

---

#### 2.3 New endpoint: Convert guest session to authenticated

**File**: `/substrate-api/api/src/app/routes/sessions.py`

```python
class ConvertGuestSessionRequest(BaseModel):
    guest_session_id: str

class ConvertGuestSessionResponse(BaseModel):
    session_id: str
    message_count: int
    converted: bool

@router.post("/guest/convert", response_model=ConvertGuestSessionResponse)
async def convert_guest_session(
    data: ConvertGuestSessionRequest,
    user_id: UUID = Depends(get_current_user_id),  # Requires auth
    db=Depends(get_db),
):
    """Convert a guest session to an authenticated user's session.

    Called after user signs up - links the guest conversation to their account.
    """
    # Find guest session
    query = """
        SELECT id, character_id, message_count, user_id
        FROM sessions
        WHERE guest_session_id = :guest_id
    """
    session = await db.fetch_one(query, {"guest_id": data.guest_session_id})

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Guest session not found"
        )

    if session["user_id"]:
        # Already converted
        if str(session["user_id"]) == str(user_id):
            return ConvertGuestSessionResponse(
                session_id=str(session["id"]),
                message_count=session["message_count"],
                converted=True,
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Session already belongs to another user"
            )

    # Convert session to authenticated
    update_query = """
        UPDATE sessions
        SET
            user_id = :user_id,
            guest_converted_at = NOW()
        WHERE guest_session_id = :guest_id
        AND user_id IS NULL
        RETURNING id, message_count
    """
    result = await db.fetch_one(update_query, {
        "user_id": str(user_id),
        "guest_id": data.guest_session_id,
    })

    if not result:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to convert session"
        )

    # Create or update engagement record
    eng_query = """
        INSERT INTO engagements (user_id, character_id)
        VALUES (:user_id, :character_id)
        ON CONFLICT (user_id, character_id) DO UPDATE
        SET updated_at = NOW()
    """
    await db.execute(eng_query, {
        "user_id": str(user_id),
        "character_id": str(session["character_id"]),
    })

    return ConvertGuestSessionResponse(
        session_id=str(result["id"]),
        message_count=result["message_count"],
        converted=True,
    )
```

---

### Phase 3: Frontend Updates

#### 3.1 Guest session management hook

**File**: Create `/web/src/hooks/useGuestSession.ts`

```typescript
import { useState, useEffect } from 'react';

const GUEST_SESSION_KEY = 'ep0_guest_session_id';

export function useGuestSession() {
  const [guestSessionId, setGuestSessionId] = useState<string | null>(null);
  const [isGuest, setIsGuest] = useState(false);

  useEffect(() => {
    // Load guest session ID from localStorage on mount
    const stored = localStorage.getItem(GUEST_SESSION_KEY);
    if (stored) {
      setGuestSessionId(stored);
      setIsGuest(true);
    }
  }, []);

  const createGuestSession = (sessionId: string) => {
    localStorage.setItem(GUEST_SESSION_KEY, sessionId);
    setGuestSessionId(sessionId);
    setIsGuest(true);
  };

  const clearGuestSession = () => {
    localStorage.removeItem(GUEST_SESSION_KEY);
    setGuestSessionId(null);
    setIsGuest(false);
  };

  return {
    guestSessionId,
    isGuest,
    createGuestSession,
    clearGuestSession,
  };
}
```

---

#### 3.2 Update API client to support guest headers

**File**: `/web/src/lib/api/client.ts`

Add guest session header injection:

```typescript
// Existing imports...

// Add guest session ID to headers if present
function getHeaders(includeGuestSession = true): HeadersInit {
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
  };

  if (includeGuestSession && typeof window !== 'undefined') {
    const guestSessionId = localStorage.getItem('ep0_guest_session_id');
    if (guestSessionId) {
      headers['X-Guest-Session-Id'] = guestSessionId;
    }
  }

  return headers;
}

// Update all fetch calls to use getHeaders()
export const api = {
  conversation: {
    async sendMessage(characterId: string, content: string, episodeTemplateId?: string) {
      const res = await fetch(`${API_URL}/conversation/${characterId}/send`, {
        method: 'POST',
        headers: getHeaders(),  // ← Add guest header
        body: JSON.stringify({ content, episode_template_id: episodeTemplateId }),
      });
      // ... rest of implementation
    },
  },
  sessions: {
    async createGuest(characterId: string, episodeTemplateId: string, guestSessionId?: string) {
      const res = await fetch(`${API_URL}/sessions/guest`, {
        method: 'POST',
        headers: getHeaders(false),  // Don't include guest header in creation
        body: JSON.stringify({
          character_id: characterId,
          episode_template_id: episodeTemplateId,
          guest_session_id: guestSessionId,
        }),
      });
      if (!res.ok) throw new Error('Failed to create guest session');
      return res.json();
    },
    async convertGuest(guestSessionId: string, authToken: string) {
      const res = await fetch(`${API_URL}/sessions/guest/convert`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${authToken}`,
        },
        body: JSON.stringify({ guest_session_id: guestSessionId }),
      });
      if (!res.ok) throw new Error('Failed to convert guest session');
      return res.json();
    },
  },
  // ... existing endpoints
};
```

---

#### 3.3 Update ChatContainer for guest support

**File**: `/web/src/components/chat/ChatContainer.tsx`

Add guest initialization logic:

```typescript
export function ChatContainer({ characterId, episodeTemplateId }: ChatContainerProps) {
  const { guestSessionId, isGuest, createGuestSession, clearGuestSession } = useGuestSession();
  const { user } = useAuth();  // Supabase auth hook
  const [showSignupModal, setShowSignupModal] = useState(false);
  const [messagesRemaining, setMessagesRemaining] = useState<number | null>(null);

  // Initialize guest session if not authenticated and episodeTemplateId provided
  useEffect(() => {
    if (!user && episodeTemplateId && !guestSessionId) {
      // Create guest session
      api.sessions.createGuest(characterId, episodeTemplateId)
        .then((response) => {
          createGuestSession(response.guest_session_id);
          setMessagesRemaining(response.messages_remaining);
        })
        .catch(console.error);
    }
  }, [user, episodeTemplateId, characterId, guestSessionId, createGuestSession]);

  // Convert guest session after login
  useEffect(() => {
    if (user && guestSessionId) {
      // User just logged in with active guest session - convert it
      api.sessions.convertGuest(guestSessionId, user.accessToken)
        .then(() => {
          clearGuestSession();  // Clear guest state
          // Reload chat to show authenticated session
          window.location.reload();
        })
        .catch(console.error);
    }
  }, [user, guestSessionId, clearGuestSession]);

  // Update useChat hook to pass guest flag
  const { messages, sendMessage, ...rest } = useChat({
    characterId,
    episodeTemplateId,
    enabled: shouldInitChat || isGuest,  // Enable for guests too
    isGuest,
    onMessageLimitReached: () => {
      setShowSignupModal(true);
    },
  });

  // Show signup modal after 5 messages
  const handleSendMessage = async (content: string) => {
    if (isGuest && messagesRemaining !== null && messagesRemaining <= 0) {
      setShowSignupModal(true);
      return;
    }

    await sendMessage(content);

    if (isGuest && messagesRemaining !== null) {
      setMessagesRemaining(prev => Math.max(0, (prev || 0) - 1));
    }
  };

  return (
    <>
      <div className="chat-container">
        {/* Existing chat UI */}
        <MessageInput onSend={handleSendMessage} />

        {/* Guest indicator */}
        {isGuest && messagesRemaining !== null && (
          <div className="guest-indicator">
            {messagesRemaining} messages remaining •
            <button onClick={() => setShowSignupModal(true)}>
              Sign up to continue
            </button>
          </div>
        )}
      </div>

      {/* Signup modal */}
      {showSignupModal && (
        <SignupModal
          onClose={() => setShowSignupModal(false)}
          guestSessionId={guestSessionId}
        />
      )}
    </>
  );
}
```

---

#### 3.4 Remove /chat from protected routes

**File**: `/web/src/lib/supabase/middleware.ts`

Update protected routes check:

```typescript
// BEFORE:
const isProtectedRoute =
  path.startsWith('/dashboard') ||
  path.startsWith('/studio') ||
  path.startsWith('/admin');

// AFTER:
const isProtectedRoute =
  path.startsWith('/dashboard') ||
  path.startsWith('/studio') ||
  path.startsWith('/admin');
// NOTE: /chat/* is now PUBLIC for guest access

// Still redirect to login if accessing dashboard/studio/admin without auth
if (isProtectedRoute && !user) {
  const url = request.nextUrl.clone();
  url.pathname = '/login';
  return NextResponse.redirect(url);
}
```

---

#### 3.5 Update series page CTA for direct trial

**File**: `/web/src/app/series/[slug]/SeriesPageClient.tsx`

Change "Start Free" button behavior:

```typescript
const handleStartEpisode = (episodeId: string) => {
  if (!user) {
    // Guest mode: Go directly to chat without login
    router.push(`/chat/${characterId}?episode=${episodeId}`);
  } else {
    // Authenticated: Existing flow
    router.push(`/chat/${characterId}?episode=${episodeId}`);
  }
};
```

**Remove**: The redirect to `/login?next=...` for Episode 0.

---

### Phase 4: UX Enhancements

#### 4.1 Guest signup modal

**File**: Create `/web/src/components/guest/SignupModal.tsx`

```typescript
interface SignupModalProps {
  onClose: () => void;
  guestSessionId: string | null;
  trigger: 'message_limit' | 'memory_snapshot';
}

export function SignupModal({ onClose, guestSessionId, trigger }: SignupModalProps) {
  return (
    <Modal open onClose={onClose}>
      <div className="signup-prompt">
        <h2>
          {trigger === 'message_limit'
            ? "You've reached the message limit"
            : "Sign up to see what happens next"}
        </h2>

        {trigger === 'message_limit' ? (
          <p>Create an account to continue your conversation and unlock all episodes.</p>
        ) : (
          <p>The detective remembers what you said. Sign up to see how this affects the story.</p>
        )}

        <div className="benefits">
          <ul>
            <li>✓ Unlimited messages</li>
            <li>✓ Your choices are remembered</li>
            <li>✓ Continue through all 8 episodes</li>
            <li>✓ Try different story paths</li>
          </ul>
        </div>

        <Button
          onClick={() => {
            // Store guest session ID in sessionStorage for post-login conversion
            if (guestSessionId) {
              sessionStorage.setItem('converting_guest_session', guestSessionId);
            }
            window.location.href = '/login?next=' + window.location.pathname;
          }}
        >
          Continue with Google
        </Button>

        <Button variant="secondary" onClick={onClose}>
          Not now
        </Button>
      </div>
    </Modal>
  );
}
```

---

#### 4.2 Guest indicator banner

**File**: `/web/src/components/guest/GuestBanner.tsx`

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

**Styling**: Subtle, non-intrusive banner at top or bottom of chat.

---

### Phase 5: Rate Limiting & Abuse Prevention

#### 5.1 IP-based rate limiting (implemented in Phase 2.1)

**Strategy**:
- Max 3 guest sessions per IP per 24 hours
- SHA256 hash of IP stored in database
- Enforced at session creation

**Edge cases**:
- VPN/proxy users: Acceptable trade-off (prevent abuse > perfect UX)
- Shared IPs (offices): Low impact (3 sessions/day is generous)

---

#### 5.2 Message count enforcement

**Implemented in**: Phase 2.2 (`send_message` endpoint)

**Logic**:
- Check `message_count` before allowing message
- Return 403 with structured error after 5 messages
- Frontend shows signup modal

---

#### 5.3 Guest session expiration

**Implemented in**: Phase 1.4 (cleanup job)

**Strategy**:
- Delete unconverted guest sessions after 24 hours
- Cascade deletes messages automatically
- Run daily via cron

---

## Testing Plan

### Unit Tests

#### Backend

1. **Test guest session creation**
   - ✓ Creates session with NULL user_id
   - ✓ Generates guest_session_id if not provided
   - ✓ Enforces IP rate limit (3/day)
   - ✓ Rejects non-Episode-0 templates

2. **Test guest message sending**
   - ✓ Accepts guest_session_id header
   - ✓ Enforces 5-message limit
   - ✓ Rejects after limit reached
   - ✓ Returns proper error structure

3. **Test guest session conversion**
   - ✓ Links guest session to user_id
   - ✓ Sets guest_converted_at timestamp
   - ✓ Creates engagement record
   - ✓ Rejects if already converted to different user

#### Frontend

1. **Test guest session hook**
   - ✓ Loads from localStorage on mount
   - ✓ Persists across page reloads
   - ✓ Clears on logout

2. **Test signup modal triggers**
   - ✓ Shows after 5 messages
   - ✓ Shows after memory snapshot (future)
   - ✓ Stores session ID for conversion

---

### Integration Tests

1. **Full guest flow**
   ```
   1. Anonymous user lands on series page
   2. Clicks "Start Episode 0"
   3. Immediately in chat (no login)
   4. Sends 5 messages
   5. Sees signup modal
   6. Signs up with Google
   7. Redirected back to chat
   8. Session converted, can continue
   ```

2. **Rate limiting**
   ```
   1. Create 3 guest sessions from same IP
   2. Attempt 4th session
   3. Verify 429 error
   4. Wait 24 hours (or mock time)
   5. Verify new session allowed
   ```

3. **Session persistence**
   ```
   1. Start guest session
   2. Send 2 messages
   3. Close tab
   4. Reopen same URL
   5. Verify messages still visible
   6. Verify can send 3 more (5 total)
   ```

---

### Manual QA Checklist

- [ ] Anonymous user can access `/chat/[id]?episode=[ep0]`
- [ ] Guest session auto-creates on chat load
- [ ] Messages send successfully for guest
- [ ] Chat UI shows "X messages remaining"
- [ ] Signup modal appears after 5th message
- [ ] Cannot send 6th message as guest
- [ ] Login flow preserves guest session ID
- [ ] After login, guest session converts
- [ ] Converted session has all previous messages
- [ ] Authenticated user can continue beyond 5 messages
- [ ] Guest sessions clean up after 24 hours
- [ ] IP rate limit triggers after 3 sessions
- [ ] RLS prevents cross-guest session access

---

## Rollout Strategy

### Week 1: Development & Testing

**Day 1-2**: Backend implementation
- Database migration
- API endpoints
- Unit tests

**Day 3-4**: Frontend implementation
- Guest hooks
- API client updates
- UI components

**Day 5**: Integration testing
- Full flow testing
- Edge case validation
- Performance testing

**Day 6-7**: QA & bug fixes

---

### Week 2: Phased Rollout

**Day 8-9**: Internal testing
- Team dogfooding
- Invite 5-10 friends to test
- Monitor logs for errors

**Day 10**: Soft launch (10% traffic)
- Enable for 10% of users via feature flag
- Monitor metrics:
  - Guest session creation rate
  - Message send success rate
  - Conversion rate (guest → signup)
  - Error rate

**Day 11-12**: Ramp to 50%
- If metrics look good, increase to 50%
- Continue monitoring

**Day 13-14**: Full rollout (100%)
- Enable for all users
- Update ads to say "No signup required to try"

---

## Success Metrics

### Leading Indicators (Week 1)

- [ ] Guest session creation rate > 50% of series page visitors
- [ ] Guest message send success rate > 95%
- [ ] Guest session conversion rate > 20%
- [ ] Error rate < 2%

### Activation Impact (Week 2-4)

**Current baseline** (with login gate):
- Series page visitors: 100
- Signup attempts: 20 (20%)
- Activated users: 5 (25% of signups, 5% of visitors)

**Target** (with guest mode):
- Series page visitors: 100
- Guest trial starts: 60 (60%)
- Signups from guests: 15 (25% of trials)
- Activated users: 12 (80% of signups, 12% of visitors)

**Key metric**: Visitor → Activated user rate
- Current: 5%
- Target: 12%
- Improvement: **+140%**

---

## Risks & Mitigation

### Risk 1: Abuse (free message spam)

**Mitigation**:
- IP-based rate limiting (3 sessions/24h)
- Message limit per session (5 messages)
- Session expiration (24 hours)
- Monitor for patterns, add CAPTCHA if needed

**Severity**: Low (mitigated)

---

### Risk 2: Conversion rate lower than expected

**Scenario**: Guests try chat but don't sign up.

**Mitigation**:
- A/B test signup modal messaging
- Test different conversion triggers:
  - After 3 messages (early)
  - After 5 messages (current plan)
  - After memory snapshot (emotional hook)
- Add "Continue as guest" with limited features

**Severity**: Medium (can iterate)

---

### Risk 3: Database bloat from unconverted sessions

**Mitigation**:
- Automated cleanup after 24 hours
- Monitor session count growth
- Alert if cleanup job fails
- Manual cleanup script as backup

**Severity**: Low (automated)

---

### Risk 4: RLS complexity introduces security hole

**Mitigation**:
- Comprehensive RLS policy testing
- Security review before rollout
- Monitor for unauthorized access attempts
- Quick rollback plan if issues found

**Severity**: Medium (requires careful testing)

---

## Rollback Plan

### If critical bug found:

1. **Immediate**: Disable guest session creation endpoint (return 503)
2. **Within 1 hour**: Revert frontend to require login
3. **Within 4 hours**: Database migration rollback
4. **Within 24 hours**: Root cause analysis and fix

### Rollback triggers:

- Error rate > 10%
- Security vulnerability discovered
- Database performance degradation > 30%
- Guest → authenticated conversion failing > 50% of attempts

---

## Cost Analysis

### Infrastructure Costs

**Additional database storage**:
- Guest sessions: ~500 bytes per session
- Messages: ~200 bytes per message
- Estimated: 1000 guest sessions/day × 5 messages × 200 bytes = 1 MB/day
- Cost: Negligible

**API requests**:
- Guest session creation: +1 request per trial
- Message sends: Same as before (just different auth)
- Conversion: +1 request per signup
- Estimated: +2000 requests/day
- Cost: $0.02/day (within free tier)

**LLM costs**:
- Guests use same LLM as authenticated users
- No additional cost (same 5 messages, just earlier in funnel)

**Total additional cost**: < $1/day

---

### Cost per Activation Comparison

**Current** (with login gate):
- Ad spend: $50/week
- Activated users: 3/week
- Cost per activation: $16.67

**Projected** (with guest mode):
- Ad spend: $50/week
- Activated users: 12/week (4x improvement)
- Cost per activation: $4.17

**Savings**: $12.50 per activated user

---

## Open Questions

1. **Should we allow resuming guest sessions across devices?**
   - Current plan: localStorage only (single device)
   - Alternative: Share guest_session_id via URL param
   - Decision: Start with localStorage, add URL sharing if requested

2. **Should we generate opening message for guests automatically?**
   - Current plan: Yes (same as authenticated users)
   - Ensures immediate engagement
   - Decision: Approved

3. **Should we show different UI for guests vs authenticated?**
   - Current plan: Minimal difference (just message counter)
   - Alternative: More prominent "Sign up" CTAs throughout
   - Decision: Start minimal, A/B test if needed

4. **Should Episode 0 opening message count toward 5-message limit?**
   - Current plan: No (system message doesn't count)
   - User gets 5 actual responses
   - Decision: Approved

---

## Next Steps

1. **Review this document** - Stakeholder approval
2. **Create database migration** - Test locally
3. **Implement backend endpoints** - With unit tests
4. **Update frontend** - Guest mode hooks + UI
5. **Integration testing** - Full flow validation
6. **Soft launch** - 10% traffic for 48 hours
7. **Full rollout** - 100% if metrics are good
8. **Update marketing** - "No signup required" messaging

---

## Related Documents

- [ACTIVATION_TIMELINE.md](../marketing/ACTIVATION_TIMELINE.md) - Current activation issues
- [GTM_DISTRIBUTION_RESET.md](../marketing/GTM_DISTRIBUTION_RESET.md) - Distribution strategy
- [ADR-000](../decisions/ADR-000-founding-vision-and-strategic-evolution.md) - Strategic context

---

**Status**: Ready for implementation
**Estimated effort**: 16-24 hours
**Expected impact**: 140% increase in activation rate
**Risk level**: Low-Medium (mitigated with phased rollout)
