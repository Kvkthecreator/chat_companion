import { cookies } from "next/headers";
import { createRouteHandlerClient } from "@/lib/supabase/clients";
import type { ExportRequest, ExportPlan, ExportResult, ExportFormat, ShareLink } from "./interface";
import * as crypto from 'crypto';

export async function fetchDoc(basketId: string, docId?: string): Promise<any> {
  const supabase = createRouteHandlerClient({ cookies });
  
  let query = supabase
    .from('documents')
    .select('id, title, body, doc_type, metadata, created_at, updated_at')
    .eq('basket_id', basketId)
    .order('created_at', { ascending: false })
    .limit(1);
    
  if (docId) {
    query = query.eq('id', docId);
  }
  
  const { data, error } = await query;
  if (error) throw new Error(error.message);
  return data?.[0] || null;
}

export async function fetchLatestReflection(basketId: string): Promise<any> {
  const supabase = createRouteHandlerClient({ cookies });
  
  const { data, error } = await supabase
    .from('cached_reflections')
    .select('pattern, tension, question, meta_derived_from, created_at')
    .eq('basket_id', basketId)
    .order('created_at', { ascending: false })
    .limit(1);
    
  if (error) throw new Error(error.message);
  return data?.[0] || null;
}

export async function plan(request: ExportRequest): Promise<ExportPlan> {
  const doc = await fetchDoc(request.basketId, request.docId);
  
  if (!doc) {
    throw new Error(`No document found for basket ${request.basketId}`);
  }

  const contentLength = (doc.body || '').length;
  const estimatedSize = request.format === 'html' 
    ? Math.ceil(contentLength * 1.5) // HTML markup overhead
    : contentLength;

  return {
    format: request.format,
    docId: doc.id,
    title: doc.title,
    estimatedSize,
    requiresReflection: doc.doc_type === 'narrative',
    metadata: {
      basketId: request.basketId,
      createdAt: doc.created_at,
      lastModified: doc.updated_at
    }
  };
}

export async function dryRun(request: ExportRequest): Promise<ExportResult> {
  try {
    const exportPlan = await plan(request);
    
    return {
      success: true,
      contentType: request.format === 'html' ? 'text/html' : 'text/markdown',
      size: exportPlan.estimatedSize,
      provenance: {
        docId: exportPlan.docId,
        generatedAt: new Date().toISOString(),
        pipeline: 'p4'
      }
    };
  } catch (error) {
    return {
      success: false,
      contentType: request.format === 'html' ? 'text/html' : 'text/markdown',
      size: 0,
      error: error instanceof Error ? error.message : 'Unknown error'
    };
  }
}

export async function execute(request: ExportRequest): Promise<ExportResult> {
  try {
    const doc = await fetchDoc(request.basketId, request.docId);
    
    if (!doc) {
      throw new Error(`No document found for basket ${request.basketId}`);
    }

    let content = doc.body || '';
    let reflectionId;

    // For narrative docs, optionally include reflection context
    if (doc.doc_type === 'narrative' && request.includeProvenance) {
      const reflection = await fetchLatestReflection(request.basketId);
      if (reflection) {
        reflectionId = reflection.meta_derived_from;
        content += `\n\n---\n*Generated from reflection: ${reflection.pattern}*`;
      }
    }

    // Convert to HTML if requested
    if (request.format === 'html') {
      content = markdownToHtml(content);
    }

    const result: ExportResult = {
      success: true,
      content,
      contentType: request.format === 'html' ? 'text/html' : 'text/markdown',
      size: content.length,
      provenance: {
        docId: doc.id,
        reflectionId,
        generatedAt: new Date().toISOString(),
        pipeline: 'p4'
      }
    };

    // Emit metrics
    const supabase = createRouteHandlerClient({ cookies });
    await supabase.from('pipeline_metrics').insert({
      pipeline: 'p4',
      basket_id: request.basketId,
      doc_id: doc.id,
      counts: { export_success: 1 },
      dims: { format: request.format, has_provenance: !!request.includeProvenance }
    });

    return result;
  } catch (error) {
    // Emit error metrics
    const supabase = createRouteHandlerClient({ cookies });
    await supabase.from('pipeline_metrics').insert({
      pipeline: 'p4',
      basket_id: request.basketId,
      counts: { export_error: 1 },
      dims: { format: request.format, error: error instanceof Error ? error.message : 'unknown' }
    });

    return {
      success: false,
      contentType: request.format === 'html' ? 'text/html' : 'text/markdown',
      size: 0,
      error: error instanceof Error ? error.message : 'Unknown error'
    };
  }
}

export async function createShareLink(basketId: string, docId: string, format: ExportFormat, expiresInHours = 24): Promise<ShareLink> {
  const token = crypto.randomBytes(32).toString('hex');
  const expiresAt = new Date(Date.now() + expiresInHours * 60 * 60 * 1000).toISOString();
  
  // Store the share token
  const supabase = createRouteHandlerClient({ cookies });
  await supabase.from('share_tokens').insert({
    token,
    basket_id: basketId,
    doc_id: docId,
    format,
    expires_at: expiresAt
  });

  return {
    token,
    url: `/api/export/share/${token}`,
    expiresAt,
    format,
    docId
  };
}

function markdownToHtml(markdown: string): string {
  // Basic markdown to HTML conversion
  return markdown
    .replace(/^# (.+)$/gm, '<h1>$1</h1>')
    .replace(/^## (.+)$/gm, '<h2>$1</h2>')
    .replace(/^### (.+)$/gm, '<h3>$1</h3>')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/\n\n/g, '</p><p>')
    .replace(/^(.+)$/gm, '<p>$1</p>')
    .replace(/<p><\/p>/g, '')
    .replace(/<p><h([1-6])>/g, '<h$1>')
    .replace(/<\/h([1-6])><\/p>/g, '</h$1>');
}