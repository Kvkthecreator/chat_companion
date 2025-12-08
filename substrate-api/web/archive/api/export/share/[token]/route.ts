import { NextResponse } from "next/server";
import { validateShareToken, generateSecureFilename } from "@/app/api/export_agent/security";
import { renderWithProvenance, wrapWithHtmlTemplate, addMarkdownMetadata } from "@/app/api/export_agent/renderers";

export async function GET(
  req: Request,
  { params }: { params: Promise<{ token: string }> }
) {
  try {
    const { token } = await params;
    
    if (!token) {
      return NextResponse.json({ error: "Share token required" }, { status: 400 });
    }

    // Validate the share token
    const validation = await validateShareToken(token);
    
    if (!validation.valid) {
      return NextResponse.json({ error: validation.error || "Invalid share token" }, { status: 403 });
    }

    const { basketId, docId, format } = validation;

    // Render the document with provenance
    const { result, manifest } = await renderWithProvenance(
      basketId!,
      format as 'markdown' | 'html',
      docId,
      true, // Always include provenance for shared exports
      token
    );

    if (!result.success) {
      return NextResponse.json({ error: result.error }, { status: 500 });
    }

    let finalContent = result.content || '';
    
    // Apply format-specific rendering
    if (format === 'html') {
      finalContent = wrapWithHtmlTemplate(finalContent, manifest);
    } else if (format === 'markdown') {
      finalContent = addMarkdownMetadata(finalContent, manifest);
    }

    const filename = generateSecureFilename(docId!, format!);
    
    // Return the content with appropriate headers
    const headers = new Headers({
      'Content-Type': format === 'html' ? 'text/html; charset=utf-8' : 'text/markdown; charset=utf-8',
      'Content-Disposition': `inline; filename="${filename}"`,
      'Cache-Control': 'no-cache, no-store, must-revalidate',
      'X-Export-Token': token,
      'X-Export-Format': format!
    });

    return new Response(finalContent, {
      status: 200,
      headers
    });
    
  } catch (error) {
    console.error('Share export error:', error);
    return NextResponse.json(
      { error: error instanceof Error ? error.message : 'Failed to access shared export' },
      { status: 500 }
    );
  }
}