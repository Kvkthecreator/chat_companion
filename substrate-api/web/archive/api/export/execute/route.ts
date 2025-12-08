import { NextResponse } from "next/server";
import { cookies } from "next/headers";
import { createRouteHandlerClient } from "@/lib/supabase/clients";
import { renderWithProvenance, wrapWithHtmlTemplate, addMarkdownMetadata } from "@/app/api/export_agent/renderers";
import { createSecureShareToken, generateSecureFilename } from "@/app/api/export_agent/security";

export async function POST(req: Request) {
  const supabase = createRouteHandlerClient({ cookies });
  
  try {
    const body = await req.json();
    const { 
      basketId, 
      format = 'markdown', 
      docId, 
      includeProvenance = false,
      createShare = false,
      shareExpiresHours = 24
    } = body;

    if (!basketId) {
      return NextResponse.json({ error: "basketId required" }, { status: 400 });
    }

    if (!['markdown', 'html'].includes(format)) {
      return NextResponse.json({ error: "format must be 'markdown' or 'html'" }, { status: 400 });
    }

    const { result, manifest } = await renderWithProvenance(
      basketId,
      format,
      docId,
      includeProvenance
    );

    if (!result.success) {
      return NextResponse.json({ error: result.error }, { status: 500 });
    }

    let finalContent = result.content || '';
    
    // Apply format-specific rendering
    if (format === 'html') {
      finalContent = wrapWithHtmlTemplate(finalContent, manifest);
    } else if (format === 'markdown' && includeProvenance) {
      finalContent = addMarkdownMetadata(finalContent, manifest);
    }

    // Create share link if requested
    let shareInfo;
    if (createShare) {
      shareInfo = await createSecureShareToken(
        basketId,
        manifest.docId,
        format,
        shareExpiresHours
      );
    }

    const response = {
      success: true,
      content: finalContent,
      contentType: result.contentType,
      size: finalContent.length,
      filename: generateSecureFilename(manifest.docId, format),
      manifest,
      shareLink: shareInfo
    };

    return NextResponse.json(response);
  } catch (error) {
    console.error('Export execute error:', error);
    return NextResponse.json(
      { error: error instanceof Error ? error.message : 'Failed to execute export' },
      { status: 500 }
    );
  }
}