# Notification & Channel Philosophy

> **Status**: Committed
> **Date**: January 2026
> **Decision**: Dedicated app model with owned surfaces only

---

## Core Philosophy

> **"A dedicated space for your emotional wellbeing"**

The companion is not a chatbot that lives in third-party messengers. It's a **place you go** — intentionally, daily — to check in with yourself.

The app boundary creates psychological separation from the chaos of daily life. Opening the companion app is an *intentional act* of self-care. It's a ritual.

---

## The Decision

### What We Own (Keep & Invest)

| Surface | Role | Chat | Notifications |
|---------|------|------|---------------|
| **Mobile App** | Primary experience | ✓ | Push |
| **Web App** | Equal citizen | ✓ | None |

### What We Don't Own (Deprecate)

| Channel | Decision | Reasoning |
|---------|----------|-----------|
| **Telegram** | Freeze (hide from UI, keep running) | Third-party platform, mixed context, dilutes product identity |
| **WhatsApp** | Don't build | API costs, same issues as Telegram, no differentiation |

---

## Why This Matters

### Owned vs. Third-Party Channels

| Factor | Owned (Mobile/Web) | Third-Party (Telegram/WhatsApp) |
|--------|-------------------|--------------------------------|
| Emotional context | Dedicated companion space | Mixed with spam, work, memes |
| Privacy perception | Feels private, intentional | "Just another chat" |
| Experience depth | Rich (voice, UI, visualizations) | Text-only, constrained |
| Ritual/habit | Opening app = intentional act | Notification lost in noise |
| User investment | Higher (chose to be here) | Lower (drive-by interaction) |
| Control | Full | Platform-dependent |

### The Insight from Industry

Mental health apps like Calm and Headspace aren't mobile-only because of technical simplicity. They're mobile-only because **the contained environment IS part of the therapeutic value**.

We extend this to web because:
- It's still our owned surface
- Desktop users have legitimate needs (work context, keyboard preference)
- No additional notification complexity (they come to us)

---

## Notification Strategy

### Simplified Model

```
Daily check-in time reached
        ↓
User has active push token?
        ↓
    Yes → Send push to most recently active device (single device)
    No  → No notification (they visit organically)
```

### What We Removed

- ❌ `preferred_channel` preference (push/telegram/whatsapp/none)
- ❌ Channel fallback cascades
- ❌ Multi-device push (all devices)
- ❌ Telegram message delivery from scheduler
- ❌ WhatsApp integration plans

### What We Keep

- ✓ Push notifications to mobile (single device)
- ✓ User-controlled notification time
- ✓ Notification enable/disable toggle
- ✓ Push token lifecycle management
- ✓ Delivery tracking and receipt checking

---

## The Trade-off We Accept

**We lose**: Users who refuse to install an app or visit a website

**We gain**:
- Focus and simplicity
- Coherent product identity
- Better experience for committed users
- Reduced maintenance burden
- Faster iteration on what matters

**Our belief**: Someone unwilling to install an app for their emotional wellbeing is not our core user. We optimize for depth over reach.

---

## Implementation Principles

1. **Mobile and web are equal citizens** — same API, same conversations, seamless sync
2. **Push is a nudge, not a guarantee** — if they miss it, the companion is still there waiting
3. **One notification per check-in** — single device, no duplicates
4. **The app is the sanctuary** — calm, focused, free of external noise
5. **Telegram is frozen, not deleted** — existing users can continue, but no new investment

---

## Migration Plan

### Phase 1: Simplify (Immediate)
- [ ] Remove Telegram from onboarding UI
- [ ] Remove Telegram from settings UI
- [ ] Remove `preferred_channel` selector from settings
- [ ] Update user preferences schema/defaults

### Phase 2: Complete Push Implementation
- [ ] Wire scheduler to send push notifications
- [ ] Implement single-device delivery (most recent)
- [ ] Add receipt checking cron job
- [ ] Test end-to-end daily check-in flow

### Phase 3: Clean Up (Later)
- [ ] Remove `preferred_channel` column (or repurpose)
- [ ] Deprecate Telegram-related API routes
- [ ] Archive Telegram bot code (don't delete)
- [ ] Update documentation

---

## Success Metrics

After implementation, we should see:
- Push notifications successfully delivered for daily check-ins
- No duplicate notifications across devices
- Clean, simple notification preferences UI
- Reduced code paths in scheduler

---

## Future Considerations

If we ever reconsider third-party channels:
- Require clear user demand signal (not speculation)
- Evaluate as separate product/experiment, not core feature
- Consider the "sanctuary" principle — does it fit?

---

## References

- [Notification System Analysis](./internationalization.md) (related thinking)
- Industry examples: Calm, Headspace (dedicated app model)
- Knock, Novu, Courier (notification infrastructure patterns we chose NOT to need)
