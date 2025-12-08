import { NextRequest, NextResponse } from 'next/server';

// ============================================================================
// UNIVERSAL CHANGE API ENDPOINT
// ============================================================================

/**
 * Universal Change API - Single endpoint for ALL substrate modifications
 * 
 * This endpoint replaces all individual change APIs:
 * - /api/baskets/[id] (PATCH)
 * - /api/documents (POST/PATCH)
 * - /api/intelligence/approve/[basketId]
 * - /api/intelligence/reject/[basketId]  
 * - /api/substrate/add-context
 * - And more...
 */

export async function POST(_request: NextRequest) {
  return NextResponse.json({
    error: 'Deprecated endpoint. Use /api/work with { work_type, work_payload }.'
  }, { status: 410 });
}

// ============================================================================
// ADDITIONAL ENDPOINTS FOR CHANGE MANAGEMENT
// ============================================================================

/**
 * GET /api/changes - Governance status and capabilities
 */
export async function GET(_request: NextRequest) {
  return NextResponse.json({
    endpoint: '/api/changes',
    status: 'deprecated',
    replacement: '/api/work'
  }, { status: 410 });
}

// ============================================================================
// LEGACY API COMPATIBILITY (TEMPORARY)
// ============================================================================

/**
 * During migration, this endpoint can also handle requests from legacy APIs
 * by transforming them to the universal format
 */
export async function PUT(_request: NextRequest) {
  return NextResponse.json({ error: 'Deprecated. Use /api/work.' }, { status: 410 });
}

export async function PATCH(_request: NextRequest) {
  return NextResponse.json({ error: 'Deprecated. Use /api/work.' }, { status: 410 });
}

export async function DELETE(_request: NextRequest) {
  return NextResponse.json({ error: 'Deprecated. Use /api/work.' }, { status: 410 });
}
