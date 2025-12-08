import { createServerComponentClient } from "@supabase/auth-helpers-nextjs";
import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import type { Database } from "@/lib/dbTypes";
import Link from "next/link";
import { ensureWorkspaceServer } from "@/lib/workspaces/ensureWorkspaceServer";
import { formatDistanceToNow } from "date-fns";
import { Plug, ArrowLeft, Rocket } from "lucide-react";

import ClaudeTokenManager from "@/components/integrations/ClaudeTokenManager";

export default async function IntegrationsPage() {
  const supabase = createServerComponentClient<Database>({ cookies });
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    redirect("/login?redirect=/dashboard/integrations");
  }

  const workspace = await ensureWorkspaceServer(supabase);
  const workspaceId = workspace?.id ?? null;

  const { data: latestToken } = await supabase
    .from('integration_tokens')
    .select('last_used_at, created_at')
    .eq('workspace_id', workspaceId)
    .order('created_at', { ascending: false })
    .limit(1);

  const { data: openaiToken } = await supabase
    .from('openai_app_tokens')
    .select('updated_at')
    .eq('workspace_id', workspaceId)
    .maybeSingle();

  const claudeConnected = Boolean(latestToken?.length);
  const claudeLastTouch = latestToken?.[0]?.last_used_at
    ? formatDistanceToNow(new Date(latestToken[0].last_used_at), { addSuffix: true })
    : 'Never';

  const chatgptConnected = Boolean(openaiToken);
  const chatgptUpdated = openaiToken?.updated_at
    ? formatDistanceToNow(new Date(openaiToken.updated_at), { addSuffix: true })
    : 'Awaiting launch';

  return (
    <div className="mx-auto flex max-w-4xl flex-col gap-6 px-6 py-8">
      <div className="rounded-lg border border-border bg-white px-4 py-3">
        <div className="flex items-center gap-3">
          <Link
            href="/dashboard"
            className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground"
          >
            <ArrowLeft className="h-4 w-4" /> Back to dashboard
          </Link>
        </div>
        <div className="mt-4 flex flex-col gap-2">
          <h1 className="text-2xl font-semibold">Integrations</h1>
          <p className="text-sm text-muted-foreground">
            Connect external hosts to Yarnnn&apos;s ambient memory. Generate tokens, review activity, and keep your connections in sync.
          </p>
        </div>
      </div>

      <div className="space-y-6">
        <section className="rounded-lg border border-border bg-white p-6 shadow-sm">
          <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
            <div>
              <div className="flex items-center gap-2 text-sm font-medium uppercase tracking-wide text-muted-foreground">
                <Plug className="h-4 w-4" /> Claude
              </div>
              <h2 className="text-xl font-semibold">Claude MCP connector</h2>
              <p className="text-sm text-muted-foreground">
                Remote MCP server for Claude Desktop and claude.ai. Use the token below as the bearer key when you add Yarnnn inside Claude.
              </p>
            </div>
            <span
              className={
                claudeConnected
                  ? 'rounded-full bg-emerald-100 px-3 py-1 text-xs font-medium text-emerald-700'
                  : 'rounded-full bg-amber-100 px-3 py-1 text-xs font-medium text-amber-700'
              }
            >
              {claudeConnected ? `Active · last seen ${claudeLastTouch}` : 'Not connected yet'}
            </span>
          </div>

          <div className="mt-6">
            <ClaudeTokenManager />
          </div>

          <div className="mt-4 text-sm text-muted-foreground">
            Need help?{' '}
            <a
              href="https://yarnnn.gitbook.io/docs/integrations-3rd-party/integrations"
              target="_blank"
              rel="noopener noreferrer"
              className="underline hover:text-foreground"
            >
              View integration guide
            </a>
            .
          </div>
        </section>

        <section className="rounded-lg border border-dashed border-border bg-muted/10 p-6">
          <div className="flex items-start gap-3">
            <Rocket className="h-5 w-5 text-muted-foreground" />
            <div className="space-y-2">
              <h2 className="text-lg font-semibold">ChatGPT Apps (coming soon)</h2>
              <p className="text-sm text-muted-foreground">
                OpenAI&apos;s Apps SDK is still in developer preview. We&apos;ll publish the Yarnnn connector as soon as the public beta opens.
              </p>
              <div className="text-xs text-muted-foreground">
                Status:{' '}
                {chatgptConnected ? `Connected · last updated ${chatgptUpdated}` : 'Waiting for public Apps SDK'}
              </div>
              <a
                href="https://yarnnn.gitbook.io/docs/integrations-3rd-party/integrations"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex w-fit items-center text-sm font-medium text-primary hover:underline"
              >
                View integration guide
              </a>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
