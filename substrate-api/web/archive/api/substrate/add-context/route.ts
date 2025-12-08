import { NextRequest, NextResponse } from 'next/server';
import { cookies } from 'next/headers';
import { createRouteHandlerClient } from '@/lib/supabase/clients';
import { ensureWorkspaceServer } from '@/lib/workspaces/ensureWorkspaceServer';
import { createDump } from '@/lib/api/dumps';
import type { SubstrateContentInput, AddContextResult } from '@/lib/substrate/types';

// Note: Universal processor removed - using basic text processing only

export async function POST(request: NextRequest) {
  try {
    const supabase = createRouteHandlerClient({ cookies });
    
    // Get authenticated user
    const {
      data: { user },
      error: authError,
    } = await supabase.auth.getUser();

    if (authError || !user) {
      return NextResponse.json({ error: 'Authentication required' }, { status: 401 });
    }

    // Ensure workspace access
    const workspace = await ensureWorkspaceServer(supabase);
    if (!workspace) {
      return NextResponse.json({ error: 'Workspace access required' }, { status: 403 });
    }

    const { basketId, content, triggerIntelligenceRefresh } = await request.json();
    
    if (!basketId || !content) {
      return NextResponse.json(
        { error: 'basketId and content are required' },
        { status: 400 }
      );
    }

    // Validate basket exists and user has access
    const { data: basket, error: basketError } = await supabase
      .from('baskets')
      .select('id')
      .eq('id', basketId)
      .eq('workspace_id', workspace.id)
      .single();

    if (basketError || !basket) {
      return NextResponse.json({ error: 'Basket not found' }, { status: 404 });
    }

    // Basic processing only - no universal processor

    // Create consolidated text content for raw_dump
    const consolidatedContent = content.map((item: SubstrateContentInput) => {
      if (item.type === 'text') return item.content;
      if (item.type === 'file') return `[File: ${item.metadata?.filename}]\n${item.content}`;
      if (item.type === 'pdf') return `[PDF: ${item.metadata?.filename}]\n${item.content}`;
      if (item.type === 'image') return `[Image: ${item.metadata?.filename}]\n${item.content}`;
      return `[${item.type}]: ${item.content}`;
    }).join('\n\n');
    
    // Extract file URLs if any
    const fileUrls = content
      .filter((item: SubstrateContentInput) => item.metadata?.fileObject)
      .map((item: SubstrateContentInput) => item.metadata!.filename)
      .filter(Boolean);

    // Create raw_dump(s) using existing function
    const { dump_id } = await createDump({ basket_id: basketId, dump_request_id: crypto.randomUUID(), text_dump: consolidatedContent });
    for (const url of fileUrls) {
      await createDump({ basket_id: basketId, dump_request_id: crypto.randomUUID(), file_url: url });
    }
    
    // Trigger immediate background intelligence generation for raw dumps
    try {
      const { triggerBackgroundIntelligenceGeneration } = await import('@/lib/intelligence/backgroundGeneration');
      
      triggerBackgroundIntelligenceGeneration({
        basketId,
        origin: 'raw_dump_added',
        rawDumpId: dump_id,
      });
      
      console.log(`Background intelligence generation triggered for raw dump in basket ${basketId}`);
    } catch (error) {
      console.warn('Failed to trigger background intelligence generation:', error);
    }
    
    // Build response
    // Since this simplified route only consolidates content and creates a dump
    // (without running the original universal processor), return defaults for
    // the processing statistics. This avoids referencing the removed
    // `processingResults` variable which caused the build to fail.
    const result: AddContextResult = {
      success: true,
      rawDumpId: dump_id,
      processingResults: {
        contentProcessed: content.length,
        insights: 'None',
        filesProcessed: fileUrls.length,
        processingQuality: 'N/A',
      },
    };

    return NextResponse.json(result);

  } catch (error) {
    console.error('Add context error:', error);
    return NextResponse.json(
      { error: 'Failed to add context to substrate' },
      { status: 500 }
    );
  }
}