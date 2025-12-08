import { cookies } from "next/headers";
import { createRouteHandlerClient } from "@/lib/supabase/clients";
import * as crypto from 'crypto';

export interface ShareTokenValidation {
  valid: boolean;
  basketId?: string;
  docId?: string;
  format?: string;
  error?: string;
}

export async function validateShareToken(token: string): Promise<ShareTokenValidation> {
  try {
    const supabase = createRouteHandlerClient({ cookies });
    
    // Get token info and update access count
    const { data, error } = await supabase
      .from('share_tokens')
      .select('basket_id, doc_id, format, expires_at')
      .eq('token', token)
      .gt('expires_at', new Date().toISOString())
      .single();
      
    if (error || !data) {
      return {
        valid: false,
        error: 'Invalid or expired share token'
      };
    }

    // Update access count (simplified for Supabase client)
    await supabase
      .from('share_tokens')
      .update({ 
        last_accessed_at: new Date().toISOString()
      })
      .eq('token', token);

    return {
      valid: true,
      basketId: data.basket_id,
      docId: data.doc_id,
      format: data.format
    };
  } catch (error) {
    return {
      valid: false,
      error: error instanceof Error ? error.message : 'Token validation failed'
    };
  }
}

export async function createSecureShareToken(
  basketId: string, 
  docId: string, 
  format: string,
  expiresInHours = 24
): Promise<{ token: string; url: string; expiresAt: string }> {
  const supabase = createRouteHandlerClient({ cookies });
  
  // Generate cryptographically secure random token
  const token = crypto.randomBytes(32).toString('hex');
  const expiresAt = new Date(Date.now() + expiresInHours * 60 * 60 * 1000);
  
  await supabase.from('share_tokens').insert({
    token,
    basket_id: basketId,
    doc_id: docId,
    format,
    expires_at: expiresAt.toISOString()
  });

  // Emit metrics
  await supabase.from('pipeline_metrics').insert({
    pipeline: 'p4',
    basket_id: basketId,
    doc_id: docId,
    counts: { share_token_created: 1 },
    dims: { format, expires_hours: expiresInHours }
  });

  return {
    token,
    url: `/api/export/share/${token}`,
    expiresAt: expiresAt.toISOString()
  };
}

export async function revokeShareToken(token: string): Promise<boolean> {
  try {
    const supabase = createRouteHandlerClient({ cookies });
    const { error } = await supabase
      .from('share_tokens')
      .delete()
      .eq('token', token);
    
    return !error;
  } catch (error) {
    return false;
  }
}

export async function cleanupExpiredTokens(): Promise<number> {
  try {
    const supabase = createRouteHandlerClient({ cookies });
    const cutoff = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString();
    
    const { error } = await supabase
      .from('share_tokens')
      .delete()
      .lt('expires_at', cutoff);
    
    return error ? 0 : 1; // Simplified return for now
  } catch (error) {
    return 0;
  }
}

export function generateSecureFilename(docId: string, format: string): string {
  const timestamp = new Date().toISOString().slice(0, 19).replace(/:/g, '-');
  const shortId = docId.slice(0, 8);
  return `export-${shortId}-${timestamp}.${format === 'html' ? 'html' : 'md'}`;
}