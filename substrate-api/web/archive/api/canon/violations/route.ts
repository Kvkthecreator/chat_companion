/**
 * Canon Violations Monitoring Endpoint
 * 
 * Provides visibility into pipeline boundary violations
 * Used for compliance monitoring and debugging
 */

import { NextResponse } from 'next/server';
import { createRouteHandlerClient } from '@/lib/supabase/clients';
import { getAuthenticatedUser } from '@/lib/auth/getAuthenticatedUser';
import { cookies } from 'next/headers';
import { getViolationMonitoringData } from '@/lib/canon/PipelineViolationLogger';

export const dynamic = 'force-dynamic';

export async function GET(req: Request) {
  try {
    // Only allow authenticated users to view violations
    const supabase = createRouteHandlerClient({ cookies });
    const { userId } = await getAuthenticatedUser(supabase);
    
    if (!userId) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }
    
    // In production, might want to restrict to admin users
    // For now, any authenticated user can view violations
    
    const monitoringData = getViolationMonitoringData();
    
    return NextResponse.json({
      success: true,
      data: monitoringData
    });
  } catch (error) {
    return NextResponse.json(
      { error: 'Failed to fetch violation data' },
      { status: 500 }
    );
  }
}