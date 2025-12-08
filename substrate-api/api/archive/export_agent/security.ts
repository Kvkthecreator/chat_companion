import { sql } from "@/lib/db";
import crypto from 'crypto';

export interface ShareTokenValidation {
  valid: boolean;
  basketId?: string;
  docId?: string;
  format?: string;
  error?: string;
}

export async function validateShareToken(token: string): Promise<ShareTokenValidation> {
  try {
    const res = await sql/* sql */`
      select valid, basket_id, doc_id, format
      from public.fn_share_token_validate(${token})
    `;
    
    const result = res.rows?.[0];
    
    if (!result || !result.valid) {
      return {
        valid: false,
        error: 'Invalid or expired share token'
      };
    }

    return {
      valid: true,
      basketId: result.basket_id,
      docId: result.doc_id,
      format: result.format
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
  // Generate cryptographically secure random token
  const token = crypto.randomBytes(32).toString('hex');
  const expiresAt = new Date(Date.now() + expiresInHours * 60 * 60 * 1000);
  
  await sql/* sql */`
    insert into public.share_tokens (token, basket_id, doc_id, format, expires_at)
    values (${token}, ${basketId}::uuid, ${docId}::uuid, ${format}, ${expiresAt.toISOString()}::timestamptz)
  `;

  // Emit metrics
  await sql/* sql */`
    insert into public.pipeline_metrics (pipeline, basket_id, doc_id, counts, dims)
    values ('p4', ${basketId}::uuid, ${docId}::uuid,
            ${JSON.stringify({ share_token_created: 1 })}::jsonb,
            ${JSON.stringify({ format, expires_hours: expiresInHours })}::jsonb);
  `;

  return {
    token,
    url: `/api/export/share/${token}`,
    expiresAt: expiresAt.toISOString()
  };
}

export async function revokeShareToken(token: string): Promise<boolean> {
  try {
    const res = await sql/* sql */`
      delete from public.share_tokens 
      where token = ${token}
      returning token
    `;
    
    return res.rows.length > 0;
  } catch (error) {
    return false;
  }
}

export async function cleanupExpiredTokens(): Promise<number> {
  try {
    const res = await sql/* sql */`
      select public.fn_share_tokens_cleanup() as deleted_count
    `;
    
    return res.rows?.[0]?.deleted_count || 0;
  } catch (error) {
    return 0;
  }
}

export function generateSecureFilename(docId: string, format: string): string {
  const timestamp = new Date().toISOString().slice(0, 19).replace(/:/g, '-');
  const shortId = docId.slice(0, 8);
  return `export-${shortId}-${timestamp}.${format === 'html' ? 'html' : 'md'}`;
}