# YARNNN AI Integration Architecture

```
           Claude / Anthropic                OpenAI (ChatGPT)
                   |                                  |
                   v                                  v
        +-------------------+            +-----------------------+
        | @yarnnn/anthropic |            |   @yarnnn/openai-apps |
        |      (adapter)    |            |        (adapter)      |
        +---------+---------+            +-----------+-----------+
                  \                        /
                   \                      /
                    v                    v
            +-------------------------------+
            |   @yarnnn/integration-core     |
            |  (tool schemas + HTTP client)  |
            +-------------------------------+
                            |
                            v
                    YARNNN Backend API

**Management Principle:** The YARNNN web application remains the source of
truth for basket management (anchors, naming, governance). MCP adapters are
ambient extensions—they may offer convenience actions (confirm basket, switch,
create new) but should redirect to the web UI for any deeper intervention.
```

- The **core** package owns protocol-neutral logic: tool schemas, input validation, 
  backend request helpers, and shared types.
- Each **adapter** wires that core into a specific host:
- `@yarnnn/anthropic-mcp` exposes the tools over the Model Context Protocol (stdio or HTTP/SSE).
- `@yarnnn/openai-apps` (scaffold) will wrap the same tools with the OpenAI Apps SDK once OAuth and UI wiring are complete.
- The OpenAI adapter now ships an embedded UI bundle (`ui/`) that ChatGPT can render once the Apps SDK contract is final; build it via `npm --prefix mcp-server/adapters/openai-apps/ui run build`.
- Both adapters call the same backend endpoints (`/api/mcp/...`), keeping the service contract identical regardless of AI platform. Basket inference is served via `/api/mcp/baskets/infer`, which returns scored candidates derived from canonical basket signatures.
- ChatGPT installs persist their OAuth tokens via `/api/integrations/openai/tokens`, secured with the shared `MCP_SHARED_SECRET` between adapter and backend.
