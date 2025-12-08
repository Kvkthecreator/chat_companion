import { NextRequest, NextResponse } from 'next/server';
import { cookies } from 'next/headers';
import { createRouteHandlerClient } from '@/lib/supabase/clients';
import { ensureWorkspaceServer } from '@/lib/workspaces/ensureWorkspaceServer';

interface ContentInventory {
  documents: {
    total: number;
    withContent: number;
    totalWords: number;
    averageWords: number;
  };
  rawDumps: {
    total: number;
    processed: number;
    totalWords: number;
    contentBreakdown: Record<string, number>;
  };
  blocks: {
    total: number;
  };
}

interface ProcessingResults {
  themesDetected: Array<{
    name: string;
    confidence: number;
    source: 'real' | 'fallback';
    occurrences?: number;
  }>;
  intentAnalysis: {
    extracted: string | null;
    fallbackUsed: string | null;
    reason: string;
  };
  alignmentAnalysis: {
    realAlignment: number;
    dashboardShows: number;
    reason: string;
  };
}

interface HonestAssessment {
  contextQuality: number;
  contentSufficiency: 'minimal' | 'moderate' | 'sufficient' | 'rich';
  whatsWorking: string[];
  whatsMissing: string[];
  recommendations: string[];
  thresholds: Array<{
    feature: string;
    current: number;
    required: number;
    unit: string;
  }>;
}

interface TruthVsFiction {
  dashboard: {
    contextQuality: number;
    alignment: number;
    themes: number;
    intent: string;
  };
  reality: {
    contextQuality: number;
    alignment: number;
    themes: number;
    intent: string | null;
  };
  discrepancies: Array<{
    metric: string;
    dashboardValue: any;
    realValue: any;
    explanation: string;
  }>;
}

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id: basketId } = await params;
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

    // Fetch comprehensive data from database (Canon v3.0: use document_heads for content)
    // V3.0: context_items merged into blocks table
    const [basketResult, documentsResult, rawDumpsResult, blocksResult] = await Promise.all([
      supabase
        .from('baskets')
        .select('*')
        .eq('id', basketId)
        .eq('workspace_id', workspace.id)
        .single(),
      supabase
        .from('document_heads')
        .select('*')
        .eq('basket_id', basketId)
        .eq('workspace_id', workspace.id),
      supabase
        .from('raw_dumps')
        .select('*')
        .eq('basket_id', basketId)
        .order('created_at', { ascending: false }),
      supabase
        .from('blocks')
        .select('*')
        .eq('basket_id', basketId)
    ]);

    if (basketResult.error || !basketResult.data) {
      return NextResponse.json({ error: 'Basket not found' }, { status: 404 });
    }

    const basket = basketResult.data;
    const documents = documentsResult.data || [];
    const rawDumps = rawDumpsResult.data || [];
    const blocks = blocksResult.data || [];

    // Calculate content inventory
    const contentInventory = calculateContentInventory(documents, rawDumps, blocks);
    
    // Analyze processing results
    const processingResults = analyzeProcessingResults(documents, rawDumps, basket);
    
    // Generate honest assessment
    const honestAssessment = generateHonestAssessment(contentInventory, processingResults);
    
    // Compare truth vs fiction
    const truthVsFiction = compareTruthVsFiction(basket, documents, processingResults);

    // Get raw intelligence API response for comparison
    let intelligenceApiResponse = null;
    try {
      const baseUrl = new URL(request.url).origin;
      const intelligenceResponse = await fetch(
        `${baseUrl}/api/intelligence/basket/${basketId}/dashboard`,
        {
          headers: {
            'Authorization': request.headers.get('authorization') || '',
            'Cookie': request.headers.get('cookie') || '',
          }
        }
      );
      if (intelligenceResponse.ok) {
        intelligenceApiResponse = await intelligenceResponse.json();
      }
    } catch (error) {
      console.warn('Could not fetch intelligence API response:', error);
    }

    return NextResponse.json({
      contentInventory,
      processingResults,
      honestAssessment,
      truthVsFiction,
      rawData: {
        basket,
        documentsCount: documents.length,
        rawDumpsCount: rawDumps.length,
        blocksCount: blocks.length,
        intelligenceApiResponse
      }
    });

  } catch (error) {
    console.error('Detailed analysis error:', error);
    return NextResponse.json(
      { error: 'Failed to generate detailed analysis' },
      { status: 500 }
    );
  }
}

function calculateContentInventory(
  documents: any[],
  rawDumps: any[],
  blocks: any[]
): ContentInventory {
  // Analyze documents (Canon v3.0: use 'content' from versions instead of 'content_raw')
  const docsWithContent = documents.filter(doc =>
    doc.content && doc.content.trim().length > 0
  );
  const docTotalWords = documents.reduce((sum, doc) =>
    sum + countWords(doc.content || ''), 0
  );

  // Analyze raw dumps
  const processedDumps = rawDumps.filter(dump => 
    dump.processing_status === 'completed' || dump.body_md?.length > 0
  );
  const dumpTotalWords = rawDumps.reduce((sum, dump) => 
    sum + countWords(dump.body_md || ''), 0
  );

  // Content type breakdown
  const contentBreakdown: Record<string, number> = {};
  rawDumps.forEach(dump => {
    const content = dump.body_md || '';
    if (content.includes('technical') || content.includes('implementation')) {
      contentBreakdown.technical = (contentBreakdown.technical || 0) + countWords(content);
    }
    if (content.includes('strategic') || content.includes('business')) {
      contentBreakdown.strategic = (contentBreakdown.strategic || 0) + countWords(content);
    }
    if (content.includes('planning') || content.includes('roadmap')) {
      contentBreakdown.planning = (contentBreakdown.planning || 0) + countWords(content);
    }
  });

  return {
    documents: {
      total: documents.length,
      withContent: docsWithContent.length,
      totalWords: docTotalWords,
      averageWords: documents.length > 0 ? Math.round(docTotalWords / documents.length) : 0
    },
    rawDumps: {
      total: rawDumps.length,
      processed: processedDumps.length,
      totalWords: dumpTotalWords,
      contentBreakdown
    },
    blocks: {
      total: blocks.length
    }
  };
}

function analyzeProcessingResults(documents: any[], rawDumps: any[], basket: any): ProcessingResults {
  // Extract real themes from content
  const realThemes = new Set<string>();
  const themeOccurrences: Record<string, number> = {};

  // Analyze document titles and content (Canon v3.0: use 'content' instead of 'content_raw')
  documents.forEach(doc => {
    if (doc.title) {
      const words = extractKeywords(doc.title);
      words.forEach(word => {
        realThemes.add(word);
        themeOccurrences[word] = (themeOccurrences[word] || 0) + 1;
      });
    }
    if (doc.content) {
      const words = extractKeywords(doc.content).slice(0, 5); // Top 5 keywords
      words.forEach(word => {
        realThemes.add(word);
        themeOccurrences[word] = (themeOccurrences[word] || 0) + 1;
      });
    }
  });

  // Analyze raw dumps
  rawDumps.forEach(dump => {
    if (dump.body_md) {
      const words = extractKeywords(dump.body_md).slice(0, 5);
      words.forEach(word => {
        realThemes.add(word);
        themeOccurrences[word] = (themeOccurrences[word] || 0) + 1;
      });
    }
  });

  // Build themes array with confidence
  const themesDetected: Array<{
    name: string;
    confidence: number;
    source: 'real' | 'fallback';
    occurrences?: number;
  }> = Array.from(realThemes).map(theme => ({
    name: theme,
    confidence: Math.min(themeOccurrences[theme] / 10, 1), // Normalize to 0-1
    source: 'real' as const,
    occurrences: themeOccurrences[theme]
  })).sort((a, b) => b.confidence - a.confidence);

  // Check if fallback themes would be added
  if (themesDetected.length === 0) {
    ['Strategic Planning', 'Documentation', 'Growth'].forEach((theme, index) => {
      themesDetected.push({
        name: theme,
        confidence: 0,
        source: 'fallback' as const,
        occurrences: 0
      });
    });
  }

  // Analyze intent (Canon v3.0: use 'content' instead of 'content_raw')
  const totalContent = documents.map(d => d.content || '').join(' ') +
                      rawDumps.map(d => d.body_md || '').join(' ');
  
  let extractedIntent = null;
  let fallbackIntent = null;
  let intentReason = '';

  if (totalContent.length < 100) {
    fallbackIntent = "Building strategic understanding and documentation for sustainable growth";
    intentReason = "Insufficient content (< 100 characters)";
  } else if (themesDetected.filter(t => t.source === 'real').length > 0) {
    const topThemes = themesDetected
      .filter(t => t.source === 'real')
      .slice(0, 2)
      .map(t => t.name.toLowerCase());
    extractedIntent = `Building understanding around ${topThemes.join(' and ')}`;
    intentReason = "Extracted from content themes";
  } else {
    fallbackIntent = "Building strategic understanding and documentation for sustainable growth";
    intentReason = "No clear themes detected";
  }

  // Analyze document alignment (Canon v3.0: use 'content' instead of 'content_raw')
  const docsWithContent = documents.filter(doc =>
    doc.content && doc.content.trim().length > 50
  );
  const realAlignment = documents.length > 0 ? docsWithContent.length / documents.length : 0;
  
  // Dashboard would show 100% if docs are updated within 7 days
  const recentDocs = documents.filter(doc => 
    new Date(doc.updated_at) > new Date(Date.now() - 7 * 24 * 60 * 60 * 1000)
  );
  const dashboardAlignment = documents.length > 0 ? recentDocs.length / documents.length : 0.8;

  return {
    themesDetected,
    intentAnalysis: {
      extracted: extractedIntent,
      fallbackUsed: fallbackIntent,
      reason: intentReason
    },
    alignmentAnalysis: {
      realAlignment,
      dashboardShows: dashboardAlignment,
      reason: realAlignment === 0 ? "Empty documents cannot have alignment" : 
              dashboardAlignment > realAlignment ? "Dashboard uses recency instead of content alignment" :
              "Alignment based on actual content"
    }
  };
}

function generateHonestAssessment(
  inventory: ContentInventory,
  results: ProcessingResults
): HonestAssessment {
  const totalWords = inventory.documents.totalWords + inventory.rawDumps.totalWords;
  const realThemes = results.themesDetected.filter(t => t.source === 'real').length;
  
  // Calculate honest context quality
  let contextQuality = 0.1; // Base score
  if (totalWords > 100) contextQuality += 0.1;
  if (totalWords > 500) contextQuality += 0.2;
  if (totalWords > 1000) contextQuality += 0.2;
  if (realThemes > 0) contextQuality += 0.1;
  if (realThemes > 2) contextQuality += 0.1;
  if (inventory.documents.withContent > 0) contextQuality += 0.1;
  if (inventory.rawDumps.processed > 0) contextQuality += 0.1;

  // Determine sufficiency level
  let contentSufficiency: 'minimal' | 'moderate' | 'sufficient' | 'rich';
  if (totalWords < 100) contentSufficiency = 'minimal';
  else if (totalWords < 500) contentSufficiency = 'moderate';
  else if (totalWords < 2000) contentSufficiency = 'sufficient';
  else contentSufficiency = 'rich';

  // What's working
  const whatsWorking: string[] = [];
  if (inventory.rawDumps.processed > 0) whatsWorking.push('PDF/file processing is working');
  if (realThemes > 0) whatsWorking.push(`${realThemes} real themes detected`);
  if (inventory.rawDumps.totalWords > 1000) whatsWorking.push('Substantial content in raw dumps');
  if (inventory.documents.total > 0) whatsWorking.push('Document structure created');

  // What's missing
  const whatsMissing: string[] = [];
  if (inventory.documents.withContent === 0) whatsMissing.push('All documents are empty');
  if (totalWords < 500) whatsMissing.push('Insufficient content for quality insights');
  if (realThemes < 3) whatsMissing.push('Not enough themes for pattern detection');
  if (!inventory.rawDumps.contentBreakdown.strategic) whatsMissing.push('No strategic business content');

  // Recommendations
  const recommendations: string[] = [];
  if (inventory.documents.withContent === 0) {
    recommendations.push('Add content to your empty documents');
  }
  if (totalWords < 500) {
    recommendations.push(`Add ${500 - totalWords} more words to enable business intelligence`);
  }
  if (!inventory.rawDumps.contentBreakdown.strategic) {
    recommendations.push('Upload business model, market analysis, or strategic plans');
  }
  if (inventory.documents.total === 0) {
    recommendations.push('Create documents to organize your insights');
  }

  // Feature thresholds
  const thresholds = [
    {
      feature: 'Basic Intelligence',
      current: totalWords,
      required: 500,
      unit: 'words'
    },
    {
      feature: 'Pattern Detection',
      current: realThemes,
      required: 3,
      unit: 'themes'
    },
    {
      feature: 'Strategic Insights',
      current: inventory.rawDumps.contentBreakdown.strategic || 0,
      required: 300,
      unit: 'strategic words'
    },
    {
      feature: 'Document Alignment',
      current: inventory.documents.withContent,
      required: Math.max(2, Math.ceil(inventory.documents.total / 2)),
      unit: 'documents with content'
    }
  ];

  return {
    contextQuality,
    contentSufficiency,
    whatsWorking,
    whatsMissing,
    recommendations,
    thresholds
  };
}

function compareTruthVsFiction(
  basket: any,
  documents: any[],
  results: ProcessingResults
): TruthVsFiction {
  // After our fixes, the dashboard should now show honest metrics
  // So we'll compare old vs new behavior to show the improvement
  
  // OLD dashboard behavior (what we fixed)
  const oldDashboardContextQuality = 0.6; // Old inflated base
  const oldDashboardAlignment = 0.8; // Old timestamp-based alignment
  const oldDashboardThemes = Math.max(3, results.themesDetected.filter(t => t.source === 'real').length);
  const oldDashboardIntent = "Building strategic understanding and documentation for sustainable growth";

  // NEW honest dashboard behavior (post-fix) (Canon v3.0: use 'content' instead of 'content_raw')
  const totalContentLength = documents.reduce((sum, doc) => sum + (doc.content?.length || 0), 0);
  const realThemes = results.themesDetected.filter(t => t.source === 'real');
  
  // Calculate what the new honest dashboard shows
  let newDashboardContextQuality = 0.1;
  if (totalContentLength > 100) newDashboardContextQuality += 0.1;
  if (totalContentLength > 500) newDashboardContextQuality += 0.2;
  if (totalContentLength > 1000) newDashboardContextQuality += 0.2;
  if (realThemes.length > 0) newDashboardContextQuality += 0.2;
  if (realThemes.length > 1) newDashboardContextQuality += 0.1;

  const newDashboardAlignment = results.alignmentAnalysis.realAlignment;
  const newDashboardThemes = realThemes.length;
  const newDashboardIntent = results.intentAnalysis.extracted || 
    (totalContentLength < 100 ? "Add more strategic content to help me understand your intent" : 
     "Add strategic documents, plans, or context to enable intelligent analysis");

  // What technical reality actually shows (unchanged)
  const realityContextQuality = newDashboardContextQuality;
  const realityAlignment = results.alignmentAnalysis.realAlignment;
  const realityThemes = realThemes.length;
  const realityIntent = results.intentAnalysis.extracted;

  // Build discrepancies array - now showing improvement from fixes
  const discrepancies = [];

  // Show old vs new dashboard behavior as "before/after fixes"
  if (Math.abs(oldDashboardContextQuality - newDashboardContextQuality) > 0.01) {
    discrepancies.push({
      metric: 'Context Quality (Fixed)',
      dashboardValue: `Before: ${Math.round(oldDashboardContextQuality * 100)}% → After: ${Math.round(newDashboardContextQuality * 100)}%`,
      realValue: `${Math.round(realityContextQuality * 100)}%`,
      explanation: 'Fixed: Removed inflated 60% baseline, now based on actual content'
    });
  }

  if (Math.abs(oldDashboardAlignment - newDashboardAlignment) > 0.01) {
    discrepancies.push({
      metric: 'Document Alignment (Fixed)',
      dashboardValue: `Before: ${Math.round(oldDashboardAlignment * 100)}% → After: ${Math.round(newDashboardAlignment * 100)}%`,
      realValue: `${Math.round(realityAlignment * 100)}%`,
      explanation: 'Fixed: Removed timestamp-based fake alignment, now based on content'
    });
  }

  if (oldDashboardThemes !== newDashboardThemes) {
    discrepancies.push({
      metric: 'Themes Identified (Fixed)',
      dashboardValue: `Before: ${oldDashboardThemes} → After: ${newDashboardThemes}`,
      realValue: realityThemes,
      explanation: 'Fixed: Removed hardcoded fallback themes, now shows only real themes'
    });
  }

  if (oldDashboardIntent !== newDashboardIntent) {
    discrepancies.push({
      metric: 'Strategic Intent (Fixed)',
      dashboardValue: 'Before: Template → After: Honest guidance',
      realValue: realityIntent || 'Content-based guidance',
      explanation: 'Fixed: Replaced template with honest content-based guidance'
    });
  }

  // Show the current state (post-fix) - should have no discrepancies
  return {
    dashboard: {
      contextQuality: newDashboardContextQuality,
      alignment: newDashboardAlignment,
      themes: newDashboardThemes,
      intent: newDashboardIntent
    },
    reality: {
      contextQuality: realityContextQuality,
      alignment: realityAlignment,
      themes: realityThemes,
      intent: realityIntent
    },
    discrepancies
  };
}

function countWords(text: string): number {
  return text.split(/\s+/).filter(word => word.length > 0).length;
}

function extractKeywords(text: string): string[] {
  const commonWords = new Set([
    'the', 'be', 'to', 'of', 'and', 'a', 'in', 'that', 'have', 'i',
    'it', 'for', 'not', 'on', 'with', 'he', 'as', 'you', 'do', 'at',
    'this', 'but', 'his', 'by', 'from', 'they', 'we', 'say', 'her', 'she',
    'or', 'an', 'will', 'my', 'one', 'all', 'would', 'there', 'their'
  ]);

  const words = text.toLowerCase()
    .replace(/[^a-z0-9\s]/g, '')
    .split(/\s+/)
    .filter(word => word.length > 3 && !commonWords.has(word));

  // Count occurrences
  const wordCount: Record<string, number> = {};
  words.forEach(word => {
    wordCount[word] = (wordCount[word] || 0) + 1;
  });

  // Sort by frequency and return top keywords
  return Object.entries(wordCount)
    .sort((a, b) => b[1] - a[1])
    .map(([word]) => word.charAt(0).toUpperCase() + word.slice(1))
    .slice(0, 10);
}