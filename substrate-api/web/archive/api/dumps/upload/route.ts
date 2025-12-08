export const dynamic = 'force-dynamic';
export const revalidate = 0;
export const runtime = 'nodejs';

import { NextRequest, NextResponse } from 'next/server';
import { createServerSupabaseClient } from '@/lib/supabase/server';
import { getAuthenticatedUser } from '@/lib/auth/getAuthenticatedUser';
import { ensureWorkspaceForUser } from '@/lib/workspaces/ensureWorkspaceForUser';
import { 
  CANONICAL_TEXT_MIME_TYPES, 
  CANONICAL_BINARY_MIME_TYPES, 
  SUPPORTED_FORMAT_DESCRIPTION,
  isCanonicalFile,
  getCanonicalMimeType,
  isCanonicalTextFormat,
  isCanonicalBinaryFormat
} from '@/shared/constants/canonical_file_types';

// Universal Work Initiation Helper for Canon v2.1 compliance
async function initiateUniversalWork(
  supabase: any,
  workType: string,
  payload: any,
  context: {
    user_id: string;
    workspace_id: string;
    basket_id?: string;
    dump_id?: string;
  },
  priority: number = 5
): Promise<string> {
  const work_id = crypto.randomUUID();
  
  const workEntry = {
    id: work_id,
    work_id: work_id,
    work_type: workType,
    user_id: context.user_id,
    workspace_id: context.workspace_id,
    basket_id: context.basket_id,
    dump_id: context.dump_id,
    processing_state: 'pending',
    priority: priority,
    work_payload: payload,
    cascade_metadata: {}
  };

  const { data, error } = await supabase
    .table('agent_processing_queue')
    .insert(workEntry);

  if (error) {
    throw new Error(`Failed to create work entry: ${error.message}`);
  }

  // Emit timeline event
  try {
    await supabase.table('timeline_events').insert({
      id: crypto.randomUUID(),
      workspace_id: context.workspace_id,
      basket_id: context.basket_id,
      kind: 'work.initiated',
      ref_id: work_id,
      preview: `${workType.replace('_', ' ')} work initiated`,
      payload: {
        work_id: work_id,
        work_type: workType,
        user_id: context.user_id
      }
    });
  } catch (e) {
    // Timeline event failure shouldn't break work creation
    console.warn('Failed to emit timeline event:', e);
  }

  return work_id;
}

export async function POST(request: NextRequest) {
  try {
    const formData = await request.formData();
    const basketId = (formData.get('basket_id') as string | null)?.trim();
    const metaStr = formData.get('meta') as string | null;
    const textDumpRaw = formData.get('text_dump') as string | null;
    const dumpRequestValues = formData.getAll('dump_request_id').map((value) => String(value)).filter(Boolean);

    if (!basketId) {
      return NextResponse.json({ error: 'Missing required field: basket_id' }, { status: 400 });
    }

    let parsedMeta: Record<string, any> = {};
    if (metaStr) {
      try {
        parsedMeta = JSON.parse(metaStr);
      } catch (parseError) {
        return NextResponse.json({ error: 'Invalid meta payload', details: 'meta must be valid JSON' }, { status: 400 });
      }
    }

    const filesFromArray = formData.getAll('files').filter((value): value is File => value instanceof File);
    const singleFile = formData.get('file');
    if (singleFile instanceof File) {
      filesFromArray.push(singleFile);
    }

    const textDump = textDumpRaw?.trim() ?? '';

    if (!textDump && filesFromArray.length === 0) {
      return NextResponse.json({ error: 'No content provided', details: 'Attach text_dump and/or files[]' }, { status: 400 });
    }

    const supabase = createServerSupabaseClient();
    const { userId } = await getAuthenticatedUser(supabase);
    const workspace = await ensureWorkspaceForUser(userId, supabase);

    const { data: basket, error: basketError } = await supabase
      .from('baskets')
      .select('id, workspace_id')
      .eq('id', basketId)
      .eq('workspace_id', workspace.id)
      .single();

    if (basketError || !basket) {
      return NextResponse.json({ error: 'Basket access denied' }, { status: 403 });
    }

    const nextDumpRequestId = () => dumpRequestValues.shift() ?? crypto.randomUUID();

    type PendingDump = {
      payload: {
        dump_request_id: string;
        text_dump: string | null;
        file_url: string | null;
        source_meta: Record<string, any>;
      };
      processing: 'immediate_text' | 'storage_extraction';
      sourceType: 'text_content' | 'file_url';
      fileInfo?: {
        name: string;
        size: number;
        canonicalMime: string;
      };
    };

    const dumpsToIngest: PendingDump[] = [];

    if (textDump) {
      dumpsToIngest.push({
        payload: {
          dump_request_id: nextDumpRequestId(),
          text_dump: textDump,
          file_url: null,
          source_meta: {
            ...parsedMeta,
            upload_method: 'api_upload',
            content_origin: 'text'
          }
        },
        processing: 'immediate_text',
        sourceType: 'text_content'
      });
    }

    for (const file of filesFromArray) {
      if (!isCanonicalFile(file)) {
        return NextResponse.json({
          error: 'Unsupported file type',
          details: SUPPORTED_FORMAT_DESCRIPTION,
          received_type: file.type,
          file_name: file.name
        }, { status: 400 });
      }

      const canonicalMimeType = getCanonicalMimeType(file) || file.type;
      let textContent: string | null = null;
      let fileUrl: string | null = null;
      let processing: 'immediate_text' | 'storage_extraction';
      let sourceType: 'text_content' | 'file_url';

      if (canonicalMimeType && isCanonicalTextFormat(canonicalMimeType)) {
        textContent = (await file.text()).trim();
        processing = 'immediate_text';
        sourceType = 'text_content';
      } else {
        const fileBuffer = Buffer.from(await file.arrayBuffer());

        // Sanitize filename to ASCII-only for storage compatibility
        // Keep extension, replace non-ASCII with underscore
        const fileExt = file.name.split('.').pop() || '';
        const fileNameWithoutExt = file.name.substring(0, file.name.lastIndexOf('.')) || file.name;
        const sanitizedName = fileNameWithoutExt.replace(/[^a-zA-Z0-9_-]/g, '_') + (fileExt ? `.${fileExt}` : '');
        const storagePath = `dumps/${basketId}/${Date.now()}-${sanitizedName}`;

        const { error: uploadError } = await supabase.storage
          .from('basket-dumps')
          .upload(storagePath, fileBuffer, {
            contentType: canonicalMimeType || file.type,
            upsert: false
          });

        if (uploadError) {
          return NextResponse.json({
            error: 'Failed to upload file to storage',
            details: uploadError.message
          }, { status: 500 });
        }

        const { data: { publicUrl } } = supabase.storage
          .from('basket-dumps')
          .getPublicUrl(storagePath);

        fileUrl = publicUrl;
        processing = 'storage_extraction';
        sourceType = 'file_url';
      }

      dumpsToIngest.push({
        payload: {
          dump_request_id: nextDumpRequestId(),
          text_dump: textContent || null,
          file_url: fileUrl,
          source_meta: {
            ...parsedMeta,
            original_filename: file.name,
            file_size: file.size,
            file_type: canonicalMimeType || file.type,
            canonical_mime_type: canonicalMimeType || file.type,
            upload_method: 'api_upload'
          }
        },
        processing,
        sourceType,
        fileInfo: {
          name: file.name,
          size: file.size,
          canonicalMime: canonicalMimeType || file.type
        }
      });
    }

    const { data: dumpResult, error: dumpError } = await supabase
      .rpc('fn_ingest_dumps', {
        p_workspace_id: workspace.id,
        p_basket_id: basketId,
        p_dumps: dumpsToIngest.map((entry) => entry.payload)
      });

    if (dumpError) {
      console.error('Dump creation error:', dumpError);
      return NextResponse.json({
        error: 'Failed to create dumps',
        details: dumpError.message
      }, { status: 500 });
    }

    if (!Array.isArray(dumpResult) || dumpResult.length !== dumpsToIngest.length) {
      return NextResponse.json({
        error: 'Unexpected dump ingestion response'
      }, { status: 500 });
    }

    const responseItems: Array<{
      dump_id: string | null;
      dump_request_id: string;
      processing_method: 'immediate_text' | 'storage_extraction';
      work_id: string | null;
      status_url: string | null;
      source_type: 'text_content' | 'file_url';
      file?: PendingDump['fileInfo'];
    }> = [];

    for (let index = 0; index < dumpsToIngest.length; index += 1) {
      const dumpEntry = dumpsToIngest[index];
      const dumpId = dumpResult[index]?.dump_id ?? null;
      let workId: string | null = null;
      let statusUrl: string | null = null;

      if (dumpId) {
        try {
          workId = await initiateUniversalWork(
            supabase,
            'P0_CAPTURE',
            {
              dump_id: dumpId,
              source_type: dumpEntry.sourceType,
              file_meta: dumpEntry.fileInfo ? {
                original_filename: dumpEntry.fileInfo.name,
                file_size: dumpEntry.fileInfo.size,
                canonical_mime_type: dumpEntry.fileInfo.canonicalMime
              } : undefined,
              processing_method: dumpEntry.processing
            },
            {
              user_id: userId,
              workspace_id: workspace.id,
              basket_id: basketId,
              dump_id: dumpId
            },
            6
          );
          statusUrl = `/api/work/status/${workId}`;
        } catch (workError) {
          console.error('Failed to create P0_CAPTURE work:', workError);
        }
      }

      responseItems.push({
        dump_id: dumpId,
        dump_request_id: dumpEntry.payload.dump_request_id,
        processing_method: dumpEntry.processing,
        work_id: workId,
        status_url: statusUrl,
        source_type: dumpEntry.sourceType,
        file: dumpEntry.fileInfo
      });
    }

    return NextResponse.json({
      success: true,
      dump_ids: responseItems.map((item) => item.dump_id).filter(Boolean),
      primary_dump_id: responseItems[0]?.dump_id ?? null,
      dump_id: responseItems[0]?.dump_id ?? null,
      processing_method: responseItems[0]?.processing_method ?? null,
      status_url: responseItems[0]?.status_url ?? null,
      dumps: responseItems,
      message: 'Content captured and queued for processing'
    }, { status: 201 });

  } catch (error) {
    console.error('File upload error:', error);
    return NextResponse.json({
      error: 'Internal server error',
      details: error instanceof Error ? error.message : 'Unknown error'
    }, { status: 500 });
  }
}
