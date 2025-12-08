'use client';

/**
 * MCP OAuth Authorization Page
 *
 * Shows consent screen for Claude.ai MCP connection.
 * If not logged in, shows Google login button.
 * If logged in, shows user info and Authorize button.
 */

import { useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { createBrowserClient } from '@/lib/supabase/clients';
import { Button } from '@/components/ui/Button';
import Brand from '@/components/Brand';

export default function MCPAuthorizePage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [user, setUser] = useState<any>(null);
  const [isAuthorizing, setIsAuthorizing] = useState(false);

  const redirectUri = searchParams.get('redirect_uri');
  const state = searchParams.get('state');
  const mcpCallback = searchParams.get('mcp_callback');

  useEffect(() => {
    checkAuth();
  }, []);

  async function checkAuth() {
    try {
      const supabase = createBrowserClient();

      console.log('[MCP Auth] Checking authentication...');
      const { data, error } = await supabase.auth.getUser();

      if (error || !data?.user) {
        // Not authenticated - redirect to login with full return path
        console.log('[MCP Auth] Not authenticated, redirecting to login');
        const returnUrl = `/mcp/authorize?${searchParams.toString()}`;
        localStorage.setItem('redirectPath', returnUrl);
        router.push(`/login?returnUrl=${encodeURIComponent(returnUrl)}`);
        return;
      }

      // User is authenticated - show consent screen
      console.log('[MCP Auth] User authenticated:', data.user.email);
      setUser(data.user);
      setLoading(false);
    } catch (err) {
      console.error('[MCP Auth] Auth check failed:', err);
      setError('Failed to check authentication status');
      setLoading(false);
    }
  }

  async function handleAuthorize() {
    if (!redirectUri || !state || !mcpCallback) {
      setError('Missing required OAuth parameters');
      return;
    }

    setIsAuthorizing(true);

    try {
      const supabase = createBrowserClient();

      // Get fresh session token
      const { data: sessionData } = await supabase.auth.getSession();
      const token = sessionData.session?.access_token;

      if (!token) {
        setError('No active session found');
        setIsAuthorizing(false);
        return;
      }

      // Get workspace ID (assumes user has exactly one workspace per YARNNN canon)
      const { data: workspace } = await supabase
        .from('workspace_memberships')
        .select('workspace_id')
        .eq('user_id', user.id)
        .single();

      if (!workspace) {
        setError('No workspace found. Please create a workspace first.');
        setIsAuthorizing(false);
        return;
      }

      // Redirect back to MCP server callback with auth info
      const callbackUrl = new URL(mcpCallback);
      callbackUrl.searchParams.set('token', token);
      callbackUrl.searchParams.set('user_id', user.id);
      callbackUrl.searchParams.set('workspace_id', workspace.workspace_id);
      callbackUrl.searchParams.set('redirect_uri', redirectUri);
      callbackUrl.searchParams.set('state', state);

      console.log('[MCP Auth] Redirecting to callback:', callbackUrl.toString());
      window.location.href = callbackUrl.toString();
    } catch (err) {
      console.error('[MCP Auth] Authorization failed:', err);
      setError('Failed to authorize. Please try again.');
      setIsAuthorizing(false);
    }
  }


  // Loading state
  if (loading) {
    return (
      <div className="min-h-screen w-full flex flex-col justify-center items-center px-4">
        <div className="w-full max-w-sm bg-card border rounded-xl shadow-sm px-6 py-8">
          <div className="flex flex-col items-center space-y-4">
            <Brand width={120} height={34} />
            <p className="text-sm text-muted-foreground">Loading...</p>
          </div>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="min-h-screen w-full flex flex-col justify-center items-center px-4">
        <div className="w-full max-w-sm bg-card border rounded-xl shadow-sm px-6 py-8 space-y-6">
          <div className="flex flex-col items-center space-y-4">
            <Brand width={120} height={34} />
            <div className="text-center space-y-2">
              <h2 className="text-xl font-semibold text-destructive">Connection Error</h2>
              <p className="text-sm text-muted-foreground">{error}</p>
            </div>
            <Button
              onClick={() => router.push('/baskets')}
              variant="outline"
              className="w-full"
            >
              Return to YARNNN
            </Button>
          </div>
        </div>
      </div>
    );
  }

  // User is logged in - show consent screen
  if (user) {
    return (
      <div className="min-h-screen w-full flex flex-col justify-center items-center px-4">
        <div className="w-full max-w-sm bg-card border rounded-xl shadow-sm px-6 py-8 space-y-6">
          {/* Header */}
          <div className="flex flex-col items-center space-y-3">
            <Brand width={120} height={34} />
            <div className="text-center space-y-1.5">
              <h2 className="text-2xl font-semibold tracking-tight">Connect to Claude</h2>
              <p className="text-sm text-muted-foreground">
                Authorize <span className="font-medium">Claude.ai</span> to access your YARNNN workspace
              </p>
            </div>
          </div>

          {/* User info */}
          <div className="bg-muted/50 border rounded-lg p-4">
            <p className="text-xs text-muted-foreground mb-1">Logged in as</p>
            <p className="text-sm font-medium">{user.email}</p>
          </div>

          {/* Permissions info */}
          <div className="bg-muted/50 border rounded-lg p-4 space-y-2">
            <p className="text-xs font-medium text-foreground">Claude will be able to:</p>
            <ul className="text-xs text-muted-foreground space-y-1.5 ml-4 list-disc">
              <li>Create memories from chat conversations</li>
              <li>Read substrate from your baskets</li>
              <li>Add context to existing baskets</li>
              <li>Validate substrate structure</li>
            </ul>
          </div>

          {/* Action buttons */}
          <div className="flex gap-3">
            <Button
              onClick={() => router.push('/baskets')}
              variant="outline"
              className="flex-1"
            >
              Cancel
            </Button>
            <Button
              onClick={handleAuthorize}
              disabled={isAuthorizing}
              className="flex-1"
            >
              {isAuthorizing ? 'Authorizing...' : 'Authorize'}
            </Button>
          </div>

          {/* Footer */}
          <p className="text-xs text-center text-muted-foreground leading-relaxed">
            You can revoke this connection anytime from your YARNNN settings.
          </p>
        </div>
      </div>
    );
  }

  // Should never reach here - redirected to login if not authenticated
  return null;
}
