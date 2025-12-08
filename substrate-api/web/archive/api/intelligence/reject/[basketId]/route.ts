import { NextRequest, NextResponse } from "next/server";

// ============================================================================
// MIGRATED TO UNIVERSAL CHANGE SYSTEM
// ============================================================================
// This endpoint has been replaced by the Universal Change System.
// All intelligence rejections now go through /api/work (universal governance)

export async function POST(request: NextRequest) {
  return NextResponse.json(
    {
      error: "This endpoint has been migrated to the Universal Change System",
      migration: {
        newEndpoint: "/api/work",
        method: "POST",
        changeType: "intelligence_reject",
        description: "All intelligence operations now use the unified change pipeline for consistency, real-time updates, and conflict resolution."
      },
      documentation: "See Universal Change Architecture documentation for migration details"
    },
    { status: 410 } // Gone - permanently moved
  );
}

export async function GET() {
  return NextResponse.json(
    { error: "Endpoint migrated to Universal Work. Use /api/work." },
    { status: 410 }
  );
}

export async function PUT() {
  return NextResponse.json(
    { error: "Endpoint migrated to Universal Work. Use /api/work." },
    { status: 410 }
  );
}

export async function PATCH() {
  return NextResponse.json(
    { error: "Endpoint migrated to Universal Work. Use /api/work." },
    { status: 410 }
  );
}

export async function DELETE() {
  return NextResponse.json(
    { error: "Endpoint migrated to Universal Work. Use /api/work." },
    { status: 410 }
  );
}
