// TRUE CONTEXT OS - The ONLY API Endpoint for Substrate
// Handles ALL substrate operations

import { NextRequest, NextResponse } from 'next/server';
import { UnifiedSubstrateComposer } from '@/lib/substrate/UnifiedSubstrateComposer';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const composer = UnifiedSubstrateComposer.getInstance();
    
    const { operation, data, basketId, workspaceId } = body;

    if (!operation || !basketId || !workspaceId) {
      return NextResponse.json(
        { success: false, error: 'Missing required fields: operation, basketId, workspaceId' },
        { status: 400 }
      );
    }

    let response;

    switch (operation) {
      case 'add_raw_dump':
        if (!data.content) {
          return NextResponse.json(
            { success: false, error: 'Content is required for raw dump' },
            { status: 400 }
          );
        }
        response = await composer.addRawDump(data.content, basketId, workspaceId);
        break;

      case 'propose_blocks':
        if (!data.rawDumpId) {
          return NextResponse.json(
            { success: false, error: 'rawDumpId is required for block proposal' },
            { status: 400 }
          );
        }
        response = await composer.proposeBlocks(data.rawDumpId);
        break;

      case 'create_context_item':
        if (!data.title || !data.semanticType) {
          return NextResponse.json(
            { success: false, error: 'Title and semanticType are required for context item' },
            { status: 400 }
          );
        }
        response = await composer.createContextItem(
          data.title,
          data.semanticType,
          data.references || [],
          basketId,
          workspaceId,
          data.description
        );
        break;

      case 'compose_document':
        if (!data.title || !data.composition) {
          return NextResponse.json(
            { success: false, error: 'Title and composition are required for document' },
            { status: 400 }
          );
        }
        response = await composer.composeDocument(data.title, data.composition, basketId, workspaceId);
        break;

      case 'link_substrate':
        if (!data.from || !data.to || !data.type) {
          return NextResponse.json(
            { success: false, error: 'From, to, and type are required for linking' },
            { status: 400 }
          );
        }
        response = await composer.linkSubstrate(data.from, data.to, data.type);
        break;

      case 'process_with_agent':
        if (!data.agentType || !data.agentOperation) {
          return NextResponse.json(
            { success: false, error: 'agentType and agentOperation are required' },
            { status: 400 }
          );
        }
        response = await composer.processWithAgent(data.agentType, data.agentOperation, {
          ...data.agentData,
          basketId,
          workspaceId
        });
        break;

      case 'get_substrate':
        const substrateType = data.type;
        if (!substrateType) {
          return NextResponse.json(
            { success: false, error: 'Substrate type is required' },
            { status: 400 }
          );
        }
        const elements = composer.getSubstrateByType(substrateType, basketId);
        response = { success: true, data: elements };
        break;

      case 'get_relationships':
        if (!data.substrateId) {
          return NextResponse.json(
            { success: false, error: 'substrateId is required for relationships' },
            { status: 400 }
          );
        }
        const relationships = composer.getRelationships(data.substrateId);
        response = { success: true, data: relationships };
        break;

      case 'find_connections':
        if (!data.elementId) {
          return NextResponse.json(
            { success: false, error: 'elementId is required for finding connections' },
            { status: 400 }
          );
        }
        const connections = composer.findConnections(data.elementId);
        response = { success: true, data: connections };
        break;

      default:
        return NextResponse.json(
          { success: false, error: `Unknown operation: ${operation}` },
          { status: 400 }
        );
    }

    return NextResponse.json(response);
    
  } catch (error) {
    console.error('Substrate API Error:', error);
    return NextResponse.json(
      { 
        success: false, 
        error: error instanceof Error ? error.message : 'Internal server error' 
      },
      { status: 500 }
    );
  }
}

// GET endpoint for querying substrate
export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const basketId = searchParams.get('basketId');
    const workspaceId = searchParams.get('workspaceId');
    const type = searchParams.get('type');
    const elementId = searchParams.get('elementId');
    const operation = searchParams.get('operation') || 'get_all';

    if (!basketId || !workspaceId) {
      return NextResponse.json(
        { success: false, error: 'basketId and workspaceId are required' },
        { status: 400 }
      );
    }

    const composer = UnifiedSubstrateComposer.getInstance();
    let response;

    switch (operation) {
      case 'get_all':
        const substrate = {
          rawDumps: composer.getSubstrateByType('dump', basketId),  // v2.0 substrate type
          blocks: composer.getSubstrateByType('block', basketId),
          contextItems: composer.getSubstrateByType('context_item', basketId),
          timelineEvents: composer.getSubstrateByType('timeline_event', basketId),  // v2.0 substrate type
          // Note: narrative and documents are artifacts, not substrate
        };
        response = { success: true, data: substrate };
        break;

      case 'get_by_type':
        if (!type) {
          return NextResponse.json(
            { success: false, error: 'Type parameter is required' },
            { status: 400 }
          );
        }
        const elements = composer.getSubstrateByType(type as any, basketId);
        response = { success: true, data: elements };
        break;

      case 'get_relationships':
        if (!elementId) {
          return NextResponse.json(
            { success: false, error: 'elementId parameter is required' },
            { status: 400 }
          );
        }
        const relationships = composer.getRelationships(elementId);
        response = { success: true, data: relationships };
        break;

      case 'find_connections':
        if (!elementId) {
          return NextResponse.json(
            { success: false, error: 'elementId parameter is required' },
            { status: 400 }
          );
        }
        const connections = composer.findConnections(elementId);
        response = { success: true, data: connections };
        break;

      default:
        return NextResponse.json(
          { success: false, error: `Unknown operation: ${operation}` },
          { status: 400 }
        );
    }

    return NextResponse.json(response);

  } catch (error) {
    console.error('Substrate GET Error:', error);
    return NextResponse.json(
      { 
        success: false, 
        error: error instanceof Error ? error.message : 'Internal server error' 
      },
      { status: 500 }
    );
  }
}