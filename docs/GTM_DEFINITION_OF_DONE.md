# Chat Companion - Definition of Done

> Get it to market. Stop building features. Start getting users.

**Created:** 2026-01-23
**Target Ship Date:** [TBD - you set this]

---

## Mindset Reminder

- You have enough features. Memory works. Outreach works. The product exists.
- Every day spent adding features is a day not spent finding product-market fit.
- The next 10 users will teach you more than the next 10 features.
- Ship, learn, iterate. Not: build, build, build, hope.

---

## Core Product Scope (What's In)

### The Promise
"An AI companion that actually remembers you and reaches out first."

### What Ships

| Feature | Status | Done When |
|---------|--------|-----------|
| Daily check-in messages | ✅ Working | Sends at user's preferred time |
| Memory extraction | ✅ Working | Extracts facts, threads, follow-ups from conversations |
| Silence detection | ✅ Working | Reaches out when user goes quiet |
| Web chat interface | ✅ Working | User can converse at `/chat` |
| Memory transparency UI | ✅ Working | User can see/edit what companion remembers |
| Push notifications (mobile) | ✅ Working | Via Expo push service |
| Email fallback | ✅ Working | For users without mobile |
| Onboarding flow | ✅ Working | Chat-based, captures name/time/style |

### What's NOT in V1 (Scope Cut)

| Feature | Why Cut |
|---------|---------|
| Manual memory creation | Nice-to-have, not launch-blocking |
| Memory versioning | Premature optimization |
| Event-based follow-ups (Phase 3) | Can add post-launch |
| Earned spontaneity (Phase 4) | Requires user maturity data first |
| Telegram/WhatsApp integration | Web + push is enough for V1 |
| Multiple companions | One is enough |

---

## Definition of Done Checklist

### 1. Core Functionality ✅
- [ ] Send 5 test messages via daily scheduler → all deliver
- [ ] Have 3 back-and-forth conversations → memory extracts correctly
- [ ] Go quiet for 3 days → silence check-in triggers
- [ ] Check Memory page → shows accurate data
- [ ] Edit/delete memory items → works without errors

### 2. Payments & Subscription
- [ ] Stripe/LemonSqueezy integration tested end-to-end
- [ ] New user → trial → checkout → subscription active
- [ ] Webhook idempotency verified (no double charges)
- [ ] Subscription portal works (cancel, update card)
- [ ] Free tier limits enforced (if applicable)

### 3. Authentication & Security
- [ ] Google OAuth login works
- [ ] Magic link login works
- [ ] Session refresh works (no unexpected logouts)
- [ ] User data properly isolated (can't see other users' data)

### 4. Production Infrastructure
- [ ] Render services stable (no random crashes)
- [ ] Database backups configured
- [ ] Error alerting set up (Sentry or similar)
- [ ] CORS configured for production domains
- [ ] Rate limiting on API endpoints

### 5. User Experience Polish
- [ ] Mobile web responsive (not broken on phone)
- [ ] Loading states present (no blank screens)
- [ ] Error messages user-friendly
- [ ] Empty states handled gracefully
- [ ] Onboarding completes without confusion

### 6. Legal/Compliance
- [ ] Privacy policy exists and linked
- [ ] Terms of service exists and linked
- [ ] Data deletion works (user can delete account)
- [ ] GDPR-style consent if needed

---

## GTM Readiness

### Pre-Launch (Before First Real User)
- [ ] Landing page live with clear value prop
- [ ] Contact form/email set up (support@...)
- [ ] Analytics tracking (Posthog, Mixpanel, or similar)
- [ ] One "real" test user (not you) completes full flow

### Launch Assets
- [ ] App Store / PWA install instructions (if applicable)
- [ ] 3 social media posts ready
- [ ] 1 launch thread (Twitter/X) drafted
- [ ] Product Hunt draft (if doing PH launch)

### Post-Launch Monitoring
- [ ] Daily active users metric visible
- [ ] Message delivery success rate tracked
- [ ] Error rate dashboard
- [ ] User feedback channel (Discord, email, form)

---

## Operational Checklist (Production-Level Required)

### Cron Jobs
- [ ] `message-scheduler` running every minute
- [ ] `silence-detection` running every 6 hours
- [ ] `pattern-computation` running daily
- [ ] All cron jobs have error alerting

### Environment Variables
- [ ] All secrets in Render env vars (not in code)
- [ ] Production Supabase URL (not dev)
- [ ] Production LLM API key (not personal key)
- [ ] Email service configured (Resend, SendGrid, etc.)

### Domains
- [ ] API domain: `api.yourchatcompanion.com` or similar
- [ ] Web domain: `app.yourchatcompanion.com` or similar
- [ ] SSL certificates valid
- [ ] DNS propagated

---

## What "Done" Looks Like

**You can say V1 is done when:**

1. A new user can sign up, complete onboarding, receive a daily message, have a conversation, and see their companion remembers them - without your intervention.

2. Payments work end-to-end with no manual fixes.

3. You can go to sleep and wake up knowing messages went out.

4. There's a way for users to contact you if something breaks.

---

## Timeline (You Fill In)

| Milestone | Target Date | Actual |
|-----------|-------------|--------|
| All checklist items verified | | |
| First external test user | | |
| Soft launch (friends/family) | | |
| Public launch | | |

---

## Updates Log

**2026-01-23:** Created this doc. Core product features complete. Memory extraction bugs fixed. Next: verify payments, polish UX, prepare GTM assets.

---

## Reminder

> "Don't ask for permission. Do what you think is best. You know best. You can do it. Get it to market."
