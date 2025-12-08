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

    // TODO: Call Python narrative agent
    // const understanding = await agent_get_project_understanding(basketId, workspaceId);

    // Fallback data for development
    const mockUnderstanding = {
      personalized_greeting: "I'm ready to understand your project and help you build something meaningful",
      current_understanding: "Building understanding of your work through our collaboration...",
      intelligence_level: { 
        stage: "emerging",
        description: "I'm learning the foundations of your project" 
      },
      confidence: { 
        level: "building_understanding", 
        explanation: "Learning from your content and interactions" 
      },
      discovered_themes: [
        "Strategic planning and documentation",
        "Project organization and workflow",
        "Collaboration and knowledge sharing"
      ],
      next_steps: [
        "Continue sharing your ideas and documents",
        "Explore strategic planning templates",
        "Build comprehensive project documentation"
      ],
      recommended_actions: [
        {
          type: "create_document",
          title: "Strategic Overview",
          description: "Create a central strategy document"
        },
        {
          type: "organize_content",
          title: "Structure Your Ideas",
          description: "Organize existing content into coherent themes"
        }
      ]
    };

    return NextResponse.json({
      success: true,
      understanding: mockUnderstanding
    });
  } catch (error) {
    console.error('Project understanding API error:', error);
    return NextResponse.json(
      { 
        success: false, 
        error: 'Failed to get project understanding',
        // Always provide fallback data instead of failing
        understanding: {
          personalized_greeting: "I'm ready to understand your project",
          current_understanding: "Building understanding of your work...",
          intelligence_level: { stage: "emerging" },
          confidence: { level: "building_understanding", explanation: "Learning from your content" },
          discovered_themes: [],
          next_steps: [],
          recommended_actions: []
        }
      },
      { status: 200 } // Return 200 with fallback data instead of 500
    );
  }
}

export async function POST(request: NextRequest) {
  return NextResponse.json(
    { error: 'POST method not supported for this endpoint' },
    { status: 405 }
  );
}