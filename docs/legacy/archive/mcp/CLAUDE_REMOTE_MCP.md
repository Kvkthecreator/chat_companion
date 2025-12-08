# Claude Remote MCP Launch Notes

This note captures the Anthropic guidance for publishing Yarnnn as a remote MCP
connector for Claude (chatanthropic.com + Claude Desktop).

## Availability & Plans
- Remote MCP custom connectors are available to Claude Pro, Max, Team, and
  Enterprise plans (currently beta).
- Team/Enterprise: only Primary Owners/Owners can register a connector; each
  user must connect & enable it individually.
- Pro/Max: users add the connector via **Settings → Connectors**.

## Registration Flow (Org Admins)
1. Navigate to **Admin settings → Connectors** (Team/Enterprise) or
   **Settings → Connectors** (Pro/Max).
2. Click **Add custom connector**.
3. Provide the Yarnnn MCP HTTPS endpoint.
4. (Optional) Supply OAuth Client ID/Secret if the server requires it (Yarnnn
   uses integration tokens rather than OAuth for Claude today).
5. Save to make the connector available to users.

## User Enablement
- Open Claude chat, click the **Search & tools** icon (bottom-right).
- Under the **Custom** section, toggle Yarnnn → Claude prompts for the bearer
  token. Paste the integration token created in Yarnnn and save.
- After the toggle succeeds, Settings → Connectors shows Yarnnn as Connected.

## Troubleshooting
- **Connector stays disconnected:** Claude fetches `https://<server>/.well-known/mcp.json`. The endpoint must exist and advertise the available transport (Yarnnn returns the SSE URL).
- **Bearer prompt missing:** Claude must reach Yarnnn from inside a chat. Open a new chat, click **Search & tools**, open Yarnnn under Custom. The prompt appears there (Settings → Connectors does not show the token field).
- **Token rejected:** the MCP server logs `401` errors if the integration token is invalid or revoked; confirm the exact token matches the one in Yarnnn.

## Security Reminders (Anthropic guidance)
- Remote MCP servers are unverified; remind users to only connect to Yarnnn’s
  official endpoint and to review tool invocation prompts before approving.
- Write-capable tools should remain disabled unless the user intends to use
  them; Yarnnn surfaces confirmation copy for writes to help with this.
- Research mode can auto-invoke tools; document recommended settings (e.g.
  disable write actions during Research sessions).

## Removal / Editing
- Remove or edit the connector from **Settings → Connectors** via the menu
  next to Yarnnn.

## Support Playbook
- Publish an “Add Yarnnn to Claude” guide linking to the production MCP URL and
  showing where to locate the token prompt (Search & tools → Yarnnn toggle).
- Provide contact details for suspicious-activity reports; Anthropic recommends
  filing through their VDP if something malicious is detected.

Refer back to this note when finalising Claude launch messaging and admin docs.
