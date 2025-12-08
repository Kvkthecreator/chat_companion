import type { ExportResult, ExportFormat } from "./interface";
import { execute } from "./agent";

export interface RenderManifest {
  version: string;
  pipeline: 'p4';
  generatedAt: string;
  format: ExportFormat;
  docId: string;
  basketId: string;
  provenance: {
    sourceDoc: string;
    reflectionId?: string;
    includesProvenance: boolean;
  };
  security: {
    shareToken?: string;
    expiresAt?: string;
  };
}

export async function renderWithProvenance(
  basketId: string, 
  format: ExportFormat, 
  docId?: string,
  includeProvenance = true,
  shareToken?: string
): Promise<{ result: ExportResult; manifest: RenderManifest }> {
  
  const result = await execute({
    basketId,
    format,
    docId,
    includeProvenance,
    shareToken
  });

  const manifest: RenderManifest = {
    version: '1.0',
    pipeline: 'p4',
    generatedAt: new Date().toISOString(),
    format,
    docId: result.provenance?.docId || docId || '',
    basketId,
    provenance: {
      sourceDoc: result.provenance?.docId || docId || '',
      reflectionId: result.provenance?.reflectionId,
      includesProvenance: includeProvenance
    },
    security: {
      shareToken,
      expiresAt: shareToken ? new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString() : undefined
    }
  };

  return { result, manifest };
}

export function wrapWithHtmlTemplate(content: string, manifest: RenderManifest): string {
  const title = `Export - ${manifest.docId}`;
  
  return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>${title}</title>
    <style>
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
            max-width: 800px; 
            margin: 0 auto; 
            padding: 2rem;
            line-height: 1.6;
        }
        h1, h2, h3 { color: #2d3748; }
        .export-meta {
            background: #f7fafc;
            border-left: 4px solid #4299e1;
            padding: 1rem;
            margin: 2rem 0;
            font-size: 0.875rem;
            color: #4a5568;
        }
        .export-meta h4 { margin: 0 0 0.5rem 0; }
        pre { background: #f7fafc; padding: 1rem; border-radius: 4px; overflow-x: auto; }
        code { background: #edf2f7; padding: 0.125rem 0.25rem; border-radius: 2px; }
    </style>
</head>
<body>
    ${content}
    
    ${manifest.provenance.includesProvenance ? `
    <div class="export-meta">
        <h4>Export Information</h4>
        <p><strong>Generated:</strong> ${manifest.generatedAt}</p>
        <p><strong>Document ID:</strong> ${manifest.docId}</p>
        <p><strong>Pipeline:</strong> ${manifest.pipeline}</p>
        ${manifest.provenance.reflectionId ? `<p><strong>Reflection ID:</strong> ${manifest.provenance.reflectionId}</p>` : ''}
        ${manifest.security.shareToken ? `<p><strong>Share Token:</strong> ${manifest.security.shareToken}</p>` : ''}
    </div>
    ` : ''}
</body>
</html>`;
}

export function addMarkdownMetadata(content: string, manifest: RenderManifest): string {
  if (!manifest.provenance.includesProvenance) {
    return content;
  }

  const metadata = `---
export_version: ${manifest.version}
pipeline: ${manifest.pipeline}
generated_at: ${manifest.generatedAt}
doc_id: ${manifest.docId}
basket_id: ${manifest.basketId}
reflection_id: ${manifest.provenance.reflectionId || 'none'}
share_token: ${manifest.security.shareToken || 'none'}
---

`;

  return metadata + content;
}