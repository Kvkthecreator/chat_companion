// TRUE CONTEXT OS - Substrate Persistence to Database
// Handles saving substrate to database

import { NextRequest, NextResponse } from 'next/server';
import type { SubstrateElement } from '@/lib/substrate/SubstrateTypes';
import { getAuthenticatedUser } from '@/lib/server/auth';
import { createUserClient } from '@/lib/supabase/user';

export async function POST(request: NextRequest) {
  try {
    const { token } = await getAuthenticatedUser(request);
    const supabase = createUserClient(token);
    const substrate: SubstrateElement = await request.json();

    // Route to appropriate table based on substrate type
    let tableName: string;
    let data: any;

    switch (substrate.type) {
      case 'dump':
        tableName = 'raw_dumps';
        data = {
          id: substrate.id,
          basket_id: substrate.basketId,
          workspace_id: substrate.workspaceId,
          content: (substrate as any).content,
          source: (substrate as any).source,
          metadata: (substrate as any).metadata,
          created_at: substrate.createdAt,
          updated_at: substrate.updatedAt
        };
        break;

      case 'block':
        tableName = 'blocks';
        data = {
          id: substrate.id,
          basket_id: substrate.basketId,
          workspace_id: substrate.workspaceId,
          title: (substrate as any).title,
          content: (substrate as any).content,
          status: (substrate as any).status,
          raw_dump_id: (substrate as any).rawDumpId,
          metadata: (substrate as any).metadata,
          created_at: substrate.createdAt,
          updated_at: substrate.updatedAt
        };
        break;

      case 'context_item':
        tableName = 'context_items';
        data = {
          id: substrate.id,
          basket_id: substrate.basketId,
          workspace_id: substrate.workspaceId,
          title: (substrate as any).title,
          description: (substrate as any).description,
          semantic_type: (substrate as any).semanticType,
          references: (substrate as any).references,
          metadata: (substrate as any).metadata,
          created_at: substrate.createdAt,
          updated_at: substrate.updatedAt
        };
        break;

      // Note: narrative and document are artifacts in v2.0, not substrates
      case 'timeline_event':
        tableName = 'timeline_events';
        data = {
          id: substrate.id,
          basket_id: substrate.basketId,
          workspace_id: substrate.workspaceId,
          event_kind: (substrate as any).event_kind,
          event_data: (substrate as any).event_data,
          metadata: (substrate as any).metadata,
          created_at: substrate.createdAt,
          updated_at: substrate.updatedAt
        };
        break;

      default:
        return NextResponse.json(
          { success: false, error: `Unknown substrate type: ${substrate.type}` },
          { status: 400 }
        );
    }

    // Upsert to database
    const { data: result, error } = await supabase
      .from(tableName)
      .upsert(data, { onConflict: 'id' })
      .select()
      .single();

    if (error) {
      console.error('Database error:', error);
      return NextResponse.json(
        { success: false, error: error.message },
        { status: 500 }
      );
    }

    return NextResponse.json({
      success: true,
      data: result
    });

  } catch (error) {
    console.error('Persist API Error:', error);
    return NextResponse.json(
      {
        success: false,
        error: error instanceof Error ? error.message : 'Internal server error'
      },
      { status: 500 }
    );
  }
}
