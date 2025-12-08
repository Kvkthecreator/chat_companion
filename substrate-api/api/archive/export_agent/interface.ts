export type ExportFormat = 'markdown' | 'html';

export interface ExportRequest {
  basketId: string;
  format: ExportFormat;
  docId?: string;
  includeProvenance?: boolean;
  shareToken?: string;
}

export interface ExportPlan {
  format: ExportFormat;
  docId: string;
  title: string;
  estimatedSize: number;
  requiresReflection: boolean;
  metadata: {
    basketId: string;
    createdAt: string;
    lastModified: string;
  };
}

export interface ExportResult {
  success: boolean;
  content?: string;
  contentType: string;
  size: number;
  provenance?: {
    docId: string;
    reflectionId?: string;
    generatedAt: string;
    pipeline: 'p4';
  };
  error?: string;
}

export interface ShareLink {
  token: string;
  url: string;
  expiresAt: string;
  format: ExportFormat;
  docId: string;
}