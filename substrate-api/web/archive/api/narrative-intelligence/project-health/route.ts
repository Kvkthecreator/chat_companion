import { NextRequest, NextResponse } from 'next/server';

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const basketId = searchParams.get('basket_id');
    const workspaceId = searchParams.get('workspace_id') || 'default';

    if (!basketId) {
      return NextResponse.json(
        { error: 'basket_id is required' },
        { status: 400 }
      );
    }

    // TODO: Call Python narrative agent for health assessment
    // const health = await agent_assess_project_health(basketId, workspaceId);

    // Fallback data for development
    const mockHealth = {
      overall_health: "developing",
      health_score: 0.75,
      strengths: [
        "Active engagement with content creation",
        "Clear project workspace organization",
        "Consistent documentation patterns"
      ],
      improvement_areas: [
        "Strategic documentation could be expanded",
        "Cross-document connections need development",
        "Long-term planning framework missing"
      ],
      recommendations: [
        {
          focus: "Documentation",
          suggestion: "Create comprehensive strategic overview document",
          impact: "high",
          effort: "medium",
          timeframe: "1-2 weeks"
        },
        {
          focus: "Organization",
          suggestion: "Establish consistent document templates and naming conventions",
          impact: "medium",
          effort: "low",
          timeframe: "few days"
        },
        {
          focus: "Planning",
          suggestion: "Develop milestone-based project timeline",
          impact: "high",
          effort: "high",
          timeframe: "2-3 weeks"
        }
      ],
      progress_trajectory: "positive",
      next_review_suggestion: "2 weeks",
      key_metrics: {
        content_volume: "moderate",
        organization_level: "good",
        strategic_clarity: "developing",
        collaboration_readiness: "high"
      }
    };

    return NextResponse.json({
      success: true,
      health: mockHealth
    });
  } catch (error) {
    console.error('Project health API error:', error);
    return NextResponse.json(
      { 
        success: false, 
        error: 'Failed to assess project health',
        health: { 
          overall_health: "unknown",
          health_score: 0.5,
          strengths: [],
          improvement_areas: [],
          recommendations: [],
          progress_trajectory: "stable"
        }
      },
      { status: 200 }
    );
  }
}

export async function POST(request: NextRequest) {
  return NextResponse.json(
    { error: 'POST method not supported for this endpoint' },
    { status: 405 }
  );
}