export const dynamic = 'force-dynamic';
export const revalidate = 0;
export const runtime = 'nodejs';

import { NextRequest, NextResponse } from 'next/server';
import { createServerSupabaseClient } from '@/lib/supabase/server';
import { getAuthenticatedUser } from '@/lib/auth/getAuthenticatedUser';

interface EnhanceRequest {
  current_content: string;
  enhancement_intent: string;
  context: {
    basket_id: string;
    window_days: number;
  };
}

export async function POST(
  req: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id: documentId } = await params;
    const body: EnhanceRequest = await req.json();
    
    // Get auth token from request headers
    const accessToken = 
      req.headers.get("sb-access-token") || req.headers.get("authorization")?.replace("Bearer ", "");
      
    if (!accessToken) {
      return NextResponse.json(
        { error: 'Missing authentication token' },
        { status: 401 }
      );
    }
    
    const supabase = createServerSupabaseClient();
    const { userId } = await getAuthenticatedUser(supabase);
    
    // Verify document access
    const { data: document, error: docError } = await supabase
      .from('documents')
      .select('id, basket_id, title, workspace_id')
      .eq('id', documentId)
      .single();
      
    if (docError || !document) {
      return NextResponse.json({ error: 'Document not found' }, { status: 404 });
    }
    
    // Verify basket access
    const { data: basket, error: basketError } = await supabase
      .from('baskets')
      .select('workspace_id')
      .eq('id', document.basket_id)
      .single();
      
    if (basketError || !basket) {
      return NextResponse.json({ error: 'Basket not found' }, { status: 404 });
    }
    
    // For now, return a simple enhanced version
    // This could be replaced with actual AI enhancement logic
    const enhanced_content = await enhanceDocumentContent(
      body.current_content,
      body.enhancement_intent,
      document.basket_id,
      accessToken
    );
    
    return NextResponse.json({
      enhanced_content,
      enhancement_applied: true,
      original_length: body.current_content.length,
      enhanced_length: enhanced_content.length
    });
    
  } catch (error) {
    console.error('Document enhancement error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}

async function enhanceDocumentContent(
  currentContent: string,
  intent: string,
  basketId: string,
  accessToken: string
): Promise<string> {
  // Use backend presentation agent for actual AI enhancement
  try {
    const { getApiBaseUrl } = await import('@/lib/config/api');
    const backend = getApiBaseUrl();
    
    if (!backend) {
      throw new Error('Backend URL not configured');
    }
    
    // Call backend composition service for document enhancement
    const response = await fetch(`${backend}/api/documents/enhance-existing`, {
      method: 'POST',
      headers: { 
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${accessToken}`,
        'sb-access-token': accessToken
      },
      body: JSON.stringify({
        current_content: currentContent,
        enhancement_intent: intent,
        basket_id: basketId,
        composition_type: 'enhancement'
      })
    });
    
    if (!response.ok) {
      // Fallback to simple enhancement if backend fails
      console.warn('Backend enhancement failed, using fallback');
      return currentContent + '\n\n---\n\n*AI enhancement temporarily unavailable. Backend service error.*';
    }
    
    const data = await response.json();
    return data.enhanced_content || currentContent;
    
  } catch (error) {
    console.error('Enhancement service error:', error);
    // Fallback for any network/service issues
    if (!currentContent.trim()) {
      return "This document has been enhanced with AI insights.\n\nPlease add some initial content to get meaningful enhancements.";
    }
    
    return currentContent + '\n\n---\n\n*AI enhancement temporarily unavailable. Please try again later.*';
  }
}