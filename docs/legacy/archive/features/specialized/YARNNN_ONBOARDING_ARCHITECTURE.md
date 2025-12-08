# YARNNN Onboarding Architecture — Dual Flow Design

**Document Purpose**: Lock in the intent and architecture of Yarnnn's dual onboarding system to prevent accidental elimination during refactoring.

## 🎯 Core Architecture: Dual Onboarding Flows

Yarnnn uses **two complementary onboarding flows**, not redundant ones:

### 1. **Route-Level Onboarding** (`/welcome`)
- **Purpose**: First-time user landing and initial identity capture
- **Trigger**: `ONBOARDING_MODE='welcome'` OR `ONBOARDING_MODE='auto'` + `isFirstEverUser()`
- **Location**: `/welcome` → redirects via `resolveUserLanding()`
- **UX**: Step-by-step wizard for complete profile capture

### 2. **Inline Memory Onboarding** (`OnboardingGate`)
- **Purpose**: In-context identity completion within the memory workspace
- **Trigger**: User reaches `/baskets/[id]/memory` but lacks identity genesis
- **Location**: Inline component within memory page
- **UX**: Dashboard-style completion interface (needs refactoring from current step-by-step)

## 🔄 Why Both Flows Are Essential

### Route-Level Flow Benefits:
1. **Clean first impression** - New users get guided welcome experience
2. **Complete capture** - Encourages full profile before workspace entry
3. **Marketing opportunity** - Can include product education/value prop

### Inline Memory Flow Benefits:
1. **Show completed work** - Display what was captured during welcome flow
2. **Progressive completion** - Allow partial users to finish incomplete sections
3. **Contextual relevance** - Profile completion happens where it's used (memory workspace)
4. **Substrate seeding** - Ensures important identity data jumpstarts basket substrate

## 📊 User Journey Scenarios

### Scenario A: Complete New User
1. Login → `resolveUserLanding()` → `/welcome`
2. Complete full onboarding → identity genesis created
3. Redirect to `/baskets` to pick or create a workspace basket
4. Enter `/baskets/[id]/memory` → full memory experience (no inline gate)

### Scenario B: Partial/Incomplete User  
1. Login → skipped welcome OR completed partial welcome → `/baskets`
2. Enter a basket (`/baskets/[id]/memory`) → `OnboardingGate` appears
3. Complete missing profile sections → enhanced memory experience

### Scenario C: Returning User
1. Login → has identity genesis → direct to `/baskets`
2. Choose any basket (or re-open the most recent)
3. No onboarding gates trigger once inside `/baskets/[id]/memory`

## 🎨 UX Design Intent

### Current State (Needs Refactoring):
- **Route flow**: Step-by-step wizard ✅ (appropriate)
- **Inline flow**: Step-by-step wizard ❌ (inappropriate - users already "landed")

### Target State:
- **Route flow**: Keep step-by-step wizard ✅
- **Inline flow**: Dashboard-style completion interface ✅
  - Show completed sections with checkmarks
  - Highlight incomplete sections for easy completion
  - Allow editing/updating completed sections
  - More compact, contextual design

## 🏗️ Technical Architecture

### Database Layer:
- **Identity Genesis Marker**: `context_items` with `context_type='yarnnn_system'`, `content_text='identity_genesis'`
- **Profile Document**: Optional structured document created from identity data
- **Dump Substrate**: Core identity data stored as immutable dumps with onboarding metadata

### API Layer:
- **`/api/onboarding/complete`**: Handles identity genesis creation for both flows
- **Detection Functions**: `isFirstEverUser()`, `hasIdentityGenesis()`, `isBlankBasket()`
- **Landing Logic**: `resolveUserLanding()` orchestrates route-level flow

### Component Layer:
```
/welcome/page.tsx (route-level)
├── resolveUserLanding() 
└── [redirect to appropriate destination]

/baskets/index (multi-basket hub)
├── CreateBasketDialog (modal)
└── Basket cards → `/baskets/[id]/memory`

/baskets/[id]/memory/page.tsx (inline)
├── OnboardingGate (dashboard-style) [NEEDS REFACTORING]
│   └── OnboardingForm (reused component)
└── MemoryClient (main workspace)
```

## ⚠️ Critical Design Rules

1. **Never eliminate either flow** - Both serve distinct UX purposes
2. **Maintain substrate equality** - Identity data follows Canon v1.3.1 substrate principles
3. **Profile document is optional** - Identity genesis can exist without profile document
4. **Idempotency guaranteed** - Multiple onboarding attempts are safe
5. **localStorage persistence** - Partial progress is preserved across sessions

## 🎯 Refactoring Priorities

### High Priority:
1. **Refactor inline OnboardingGate** from step-by-step to dashboard style
2. **Document this architecture** to prevent future elimination attempts
3. **Preserve all substrate seeding functionality**

### Medium Priority:
1. **Visual consistency** between flows while maintaining appropriate UX patterns
2. **Performance optimization** for identity detection queries
3. **Enhanced profile document integration**

## 📋 Success Metrics

- **Route flow**: High completion rate for new users
- **Inline flow**: High completion rate for partial users who reach memory
- **Data quality**: Rich identity substrate enables better memory workspace experience
- **User satisfaction**: Smooth progression from identity capture to productive memory work

---

**Version**: 1.0  
**Last Updated**: 2025-08-27  
**Status**: Architecture locked - do not eliminate flows without user approval

---

*This document exists because the dual onboarding system appears redundant but serves critical UX and technical purposes. Any cleanup must preserve both flows while improving their respective designs.*
