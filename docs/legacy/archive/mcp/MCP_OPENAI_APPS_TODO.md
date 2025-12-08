# OpenAI Apps Adapter – Pending Items

This document tracks the outstanding work required once OpenAI publishes the Apps
SDK for general availability. Revisit it before resuming ChatGPT integration.

## 1. Apps SDK Runtime Wiring
- Replace the current Express stubs with the official Apps SDK handler.
- Register all four tools via `registerTool()` and map schemas/component metadata.
- Implement structured responses (cards, forms) that comply with the SDK.

## 2. OAuth Productionisation
- Confirm the authorization/token endpoints and scopes once the SDK stabilises.
- Exchange refresh tokens for long-lived access and schedule automatic rotation.
- Harden error handling for revoked installs (handle 401/403 from token refresh).

## 3. UI Bundle Completion
- Replace the placeholder React shell with the final set of components (context
  cards, confirmation flows, basket pickers).
- Align the host ↔ iframe messaging with the official `window.openai` contract.
- Add telemetry hooks (load, component actions) to feed the observability stack.

## 4. Distribution & Review Prep
- Collect discovery copy (≤200 characters) and usage examples for OpenAI’s app
  directory submission.
- Prepare answers for the review questionnaire (data retention, support contact,
  incident response) and link to status page.
- Run private pilots using OpenAI’s developer preview before public submission.

## 5. Security Checklist
- Enforce HMAC or signed requests if OpenAI introduces webhook callbacks.
- Finalise rate limits per install and document expected usage caps.
- Ensure `/api/integrations/openai/tokens` metrics show token freshness and
  refresh success/failure rates.

Keep this file updated as OpenAI releases more guidance.
