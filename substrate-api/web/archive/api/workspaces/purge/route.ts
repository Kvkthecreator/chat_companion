import { NextResponse } from 'next/server';
import { cookies } from 'next/headers';
import { createServerComponentClient } from '@/lib/supabase/clients';
import { getAuthenticatedUser } from '@/lib/auth/getAuthenticatedUser';

/**
 * DELETE /api/workspaces/purge
 *
 * Purges ALL data for the authenticated user's workspace.
 * This is a destructive operation with no undo.
 *
 * Safety:
 * - Only deletes data belonging to the authenticated user's workspace
 * - Requires email confirmation from frontend
 * - Transaction-wrapped (all-or-nothing)
 * - No CASCADE - explicit scoped deletes only
 */
export async function DELETE(request: Request) {
  const supabase = createServerComponentClient({ cookies });

  // Authentication check
  const { userId } = await getAuthenticatedUser(supabase);

  // Get user email for verification
  const { data: userData, error: userError } = await supabase.auth.getUser();
  if (userError || !userData?.user?.email) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  const userEmail = userData.user.email;

  // Parse and validate request
  const body = await request.json();
  const { email_confirmation } = body;

  if (!email_confirmation) {
    return NextResponse.json({
      error: 'Email confirmation required'
    }, { status: 400 });
  }

  // Verify email matches (case-insensitive)
  if (email_confirmation.toLowerCase() !== userEmail.toLowerCase()) {
    return NextResponse.json({
      error: 'Email does not match your account email'
    }, { status: 403 });
  }

  // Get user's workspace_id from workspace_memberships
  const { data: membership } = await supabase
    .from('workspace_memberships')
    .select('workspace_id')
    .eq('user_id', userId)
    .maybeSingle();

  if (!membership?.workspace_id) {
    return NextResponse.json({
      error: 'No workspace found for user'
    }, { status: 404 });
  }

  const workspaceId = membership.workspace_id;

  try {
    // Execute workspace-scoped purge in transaction
    // Note: Supabase client doesn't support transactions directly,
    // so we use RPC call to a database function for atomicity

    const { error: purgeError } = await supabase.rpc('purge_workspace_data', {
      target_workspace_id: workspaceId
    });

    if (purgeError) {
      console.error('Workspace purge failed:', purgeError);
      return NextResponse.json({
        error: 'Purge failed. Your data is unchanged. Please try again or contact support.',
        details: purgeError.message
      }, { status: 500 });
    }

    // Log the purge action for audit trail (ignore errors - purge already succeeded)
    try {
      await supabase
        .from('app_events')
        .insert({
          event_type: 'workspace.purged',
          workspace_id: workspaceId,
          user_id: userId,
          metadata: {
            purged_at: new Date().toISOString(),
            confirmed_email: email_confirmation.toLowerCase(),
          }
        });
    } catch (err) {
      console.warn('Failed to log purge event:', err);
    }

    return NextResponse.json({
      success: true,
      message: 'Workspace data purged successfully'
    });

  } catch (error) {
    console.error('Unexpected error during workspace purge:', error);
    return NextResponse.json({
      error: 'An unexpected error occurred. Your data may be unchanged.',
      details: error instanceof Error ? error.message : 'Unknown error'
    }, { status: 500 });
  }
}
