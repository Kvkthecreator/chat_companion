# ChatGPT Apps Integration (Preview)

The ChatGPT Apps SDK is still in developer preview. This guide explains how to
prepare for the Yarnnn connector when OpenAI opens public submissions.

## Current Status
- Yarnnn hosts an OpenAI Apps adapter at `https://chatgpt.yarnnn.com`.
- OAuth and token storage are wired, but the official Apps UI/runtime is not yet
  public. You can join our waitlist to be notified when the integration goes
  live.

## What You Can Do Now
1. **Generate an integration token** in Yarnnn (Settings → Integrations). This
   token will be required when the ChatGPT connector launches.
2. **Sign up for early access updates** at support@yarnnn.com.
3. **Review the Claude integration flow** to understand how Yarnnn handles
   basket inference, governance, and unassigned captures.

## Launch Checklist (Preview)
When OpenAI opens submissions we will:
- Publish the connector in the ChatGPT Apps directory.
- Provide a simple “Connect Yarnnn” button inside ChatGPT that walks you through
  OAuth and token linking.
- Ensure the same four tools (`create_memory_from_chat`, `get_substrate`,
  `add_to_substrate`, `validate_against_substrate`) are available with identical
  behavior to Claude.

## Stay in the Loop
We’ll announce availability via the Yarnnn changelog and email list. In the
meantime, feel free to send questions or integration requests to
support@yarnnn.com.
