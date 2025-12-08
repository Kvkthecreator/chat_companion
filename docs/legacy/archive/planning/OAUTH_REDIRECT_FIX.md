# OAuth Authentication - Architecture & Resolution

## Status: ✅ RESOLVED

This document captures the OAuth authentication issues encountered during the multi-basket refactor and their resolution.

## Root Causes

### Issue 1: URL Redirect Chain (Initial)
The redirect chain was:
1. Google OAuth → `galytxxkrbksilekmhcw.supabase.co/auth/v1/callback`
2. Supabase → `yarnnn.com/auth/callback` ❌ (no www)
3. Next.js middleware → `www.yarnnn.com/` (strips query params during redirect)
4. Result: User lands on root page without auth code

**Resolution**: Update Supabase Site URL to use `www.yarnnn.com`

### Issue 2: Session Storage Mismatch (Critical)
**Root Cause**: Client and server used different session storage mechanisms:
- **Client** (`createBrowserClient`): Used `createClient()` directly → stored sessions in **localStorage**
- **Server** (`createServerComponentClient`): Expected sessions in **cookies**

**Result**: 
1. OAuth callback creates session in localStorage ✅
2. Client-side sees session ✅
3. Server-side cannot read localStorage ❌
4. Server redirects to `/login` ❌
5. Infinite redirect loop

**Resolution**: Changed `createBrowserClient()` to use `createClientComponentClient()` from auth-helpers, which stores sessions in cookies that both client and server can read.

## Solution

### 1. Supabase Dashboard Configuration
**URL**: https://supabase.com/dashboard/project/galytxxkrbksilekmhcw/auth/url-configuration

**Required Settings:**
- **Site URL**: `https://www.yarnnn.com` (WITH www)
- **Redirect URLs**: 
  - `https://www.yarnnn.com/auth/callback`
  - `http://localhost:3000/auth/callback` (for local development)

### 2. Vercel Environment Variables
**Location**: Vercel Dashboard → Project Settings → Environment Variables

**Required Variable:**
```
NEXT_PUBLIC_SITE_URL=https://www.yarnnn.com
```

### 3. Local Development (.env.local)
```bash
NEXT_PUBLIC_SITE_URL=https://www.yarnnn.com
```

### 4. Code Changes Made
- Enhanced OAuth callback debugging (commit: 0bf6c7d4)
- Simplified redirect logic to use Next.js router (commit: 5f42d9a1)

## Testing Checklist
- [ ] Update Supabase Site URL to `https://www.yarnnn.com`
- [ ] Add `https://www.yarnnn.com/auth/callback` to Supabase Redirect URLs
- [ ] Set `NEXT_PUBLIC_SITE_URL` in Vercel environment variables
- [ ] Trigger new Vercel deployment
- [ ] Clear browser cookies for www.yarnnn.com
- [ ] Test OAuth login flow
- [ ] Verify console shows debug logs
- [ ] Confirm redirect to `/baskets` after successful login

## Expected Flow After Fix
1. User clicks "Continue with Google" at `www.yarnnn.com/login`
2. Google OAuth completes → redirects to Supabase callback
3. Supabase → `www.yarnnn.com/auth/callback?code=...` (WITH www)
4. Auth callback exchanges code for session
5. User redirected to `/baskets`
6. Console shows: `✅ Auth complete! Redirecting to: /baskets`

## Critical Notes
- **Always use `www.yarnnn.com`** in all OAuth configurations
- The `www` subdomain is canonical per Next.js config redirects
- Never use `yarnnn.com` without www in production settings

## Hardened Architecture

### Cookie-Based Session Storage
**File**: `web/lib/supabase/clients.ts`

```typescript
export const createBrowserClient = (): SupabaseClient<Database> => {
  if (!browserClient) {
    // CRITICAL: Use auth-helpers for cookie-based session storage
    // This ensures server-side and client-side share sessions via cookies
    browserClient = createClientComponentClient<Database>();
  }
  return browserClient;
};
```

**Why This Matters**:
- Server components run on the server and can only read cookies (not localStorage)
- Auth-helpers automatically sync sessions to cookies
- Both client and server use the same session storage mechanism

### OAuth Callback Flow
**File**: `web/app/auth/callback/page.tsx`

```typescript
// Simplified, robust callback handler
const { data: { session } } = await supabase.auth.getSession();
// Session already in cookies via auth-helpers
// No manual token extraction needed
// No artificial delays needed
// Just verify and redirect
```

### Supabase Configuration
**Production Settings** (verified working):
- **Site URL**: `https://www.yarnnn.com` (WITH www)
- **Redirect URLs**: `https://www.yarnnn.com/auth/callback`
- **Flow**: Implicit flow (hash-based tokens) - handled automatically by auth-helpers

### Multi-Basket Redirect Flow
After successful OAuth:
1. Redirect to `/baskets` (basket index)
2. User selects or creates a basket
3. Navigate to `/baskets/{id}/memory`

**Previous flow** (single-basket):
- Redirect to `/dashboard/home` → auto-select basket → `/baskets/{id}/memory`

## Key Learnings

1. **Never mix session storage mechanisms** - If server expects cookies, client must use cookies
2. **Trust the framework** - Auth-helpers handle OAuth complexity automatically
3. **Cookie domains matter** - `yarnnn.com` vs `www.yarnnn.com` breaks the flow
4. **Simplicity wins** - Over-engineering (manual token extraction, delays) masked the real issue

## Testing Checklist

✅ Supabase Site URL configured with `www.yarnnn.com`  
✅ Redirect URLs include `https://www.yarnnn.com/auth/callback`  
✅ Browser client uses `createClientComponentClient()` for cookie storage  
✅ Server components can read session from cookies  
✅ OAuth redirects to `/baskets` (multi-basket index)  
✅ No redirect loops  
✅ Session persists across page reloads

---
**Date**: 2025-10-01  
**Status**: ✅ RESOLVED - Production Verified  
**Commits**: 
- `a649211e` - Fix session storage to use cookies
- `61705b4e` - Redirect to /baskets after OAuth
- `c023703c` - Simplify callback to match pre-multi-basket code
