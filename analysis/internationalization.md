# Internationalization (i18n) Analysis

> **Status**: Parked for future consideration
> **Date**: January 2026

## Overview

This document captures considerations for adding multi-language support to the Chat Companion app.

---

## Current State

- All UI and content is English-only
- Claude (the AI backend) natively supports 50+ languages
- User preferences schema exists and can be extended

---

## Two Layers of Localization

### 1. AI Response Language (Low Effort, High Impact)

The companion's responses can be localized with minimal work:

- Add `preferred_language` field to user preferences
- Inject language instruction into system prompt: `"Always respond in {language}"`
- Claude generates responses natively in the target language (no translation API needed)

**Why this matters most**: The emotional support content is the core product. Button labels are secondary.

### 2. UI/Static Text Localization (Moderate Effort)

Requires extracting all hardcoded strings into translation files.

**Recommended libraries:**
- **Web (Next.js)**: `next-intl` or `react-i18next`
- **Mobile (React Native)**: `react-i18next` or `i18n-js`

**Typical scope**: 500-2000 strings for an app of this size

---

## Technical Considerations

### Date/Time Formatting
- Already have timezone support
- Locale-aware formatting: `Intl.DateTimeFormat` (JS native)

### Right-to-Left (RTL) Languages
- Arabic, Hebrew, Farsi require layout mirroring
- Tailwind CSS has RTL utilities (`rtl:` prefix)
- React Native has RTL support built-in

### Text Length Variability
- German text is ~30% longer than English
- Chinese/Japanese are more compact
- UI needs to accommodate varying lengths

---

## How Other Apps Handle This

| App | Approach |
|-----|----------|
| WhatsApp/Telegram | UI translated, user messages stay as-is |
| ChatGPT | UI translated, AI responds based on user language or setting |
| Headspace | English first, then localized for top markets |
| Duolingo | Heavy localization, content in target language |

---

## Recommended Phased Approach

### Phase 1: AI Language Support (Quick Win)
1. Add `preferred_language` to user preferences schema
2. Add language selector in settings UI
3. Modify system prompt to include language preference
4. **Result**: Companion speaks user's language

### Phase 2: UI Localization (When Needed)
1. Set up i18n library infrastructure
2. Extract strings to JSON translation files
3. Start with top requested languages (Spanish, Portuguese, French)
4. Community translation option via platforms like Crowdin

### Phase 3: Full RTL Support (If Needed)
1. Implement RTL layout support
2. Test thoroughly with Arabic/Hebrew users

---

## Priority Languages (Suggested)

Based on global mental health app markets:
1. Spanish (Latin America + Spain)
2. Portuguese (Brazil)
3. French
4. German
5. Japanese
6. Hindi

---

## Implementation Estimate

| Component | Effort | Priority |
|-----------|--------|----------|
| AI response language | Trivial (1-2 hours) | High |
| Settings UI for language | Low | High |
| Web UI string extraction | Moderate | Medium |
| Mobile UI string extraction | Moderate | Medium |
| RTL support | High | Low (if needed) |

---

## Resources

- [next-intl documentation](https://next-intl-docs.vercel.app/)
- [react-i18next](https://react.i18next.com/)
- [Tailwind RTL plugin](https://tailwindcss.com/docs/hover-focus-and-other-states#rtl-support)
- [MDN Intl API](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Intl)

---

## Notes

- The AI-first approach is unique to LLM-powered apps - most traditional apps need full translation pipelines
- User-generated content (journal entries, chat messages) remains in the user's written language
- Consider language detection for auto-setting preference based on first interaction
