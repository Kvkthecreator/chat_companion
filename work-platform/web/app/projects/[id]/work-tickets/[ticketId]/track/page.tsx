/**
 * Live Work Ticket Tracking Page
 *
 * Shows real-time execution progress for a work ticket:
 * - Ticket metadata (recipe, parameters, agent)
 * - Real-time status updates (Supabase Realtime)
 * - TodoWrite task progress (SSE)
 * - Output preview when completed
 * - Actions (view output, retry, download)
 */

import { cookies } from "next/headers";
import { createServerComponentClient } from "@/lib/supabase/clients";
import { getAuthenticatedUser } from "@/lib/auth/getAuthenticatedUser";
import { notFound } from "next/navigation";
import TicketTrackingClient from "./TicketTrackingClient";

interface PageProps {
  params: Promise<{ id: string; ticketId: string }>;
}

export default async function TicketTrackingPage({ params }: PageProps) {
  const { id: projectId, ticketId } = await params;

  const supabase = createServerComponentClient({ cookies });

  // Try to get authenticated user, but don't block if it fails
  let userId: string | null = null;
  try {
    const auth = await getAuthenticatedUser(supabase);
    userId = auth.userId;
  } catch (error) {
    console.error('[Track Page] Auth failed:', error);
    // Continue without auth - ticket will be fetched without user check
  }

  // Fetch work ticket with outputs (don't require project for simpler query)
  const { data: ticket } = await supabase
    .from('work_tickets')
    .select(`
      id,
      status,
      agent_type,
      created_at,
      started_at,
      completed_at,
      error_message,
      metadata,
      basket_id,
      workspace_id,
      work_outputs (
        id,
        title,
        body,
        output_type,
        agent_type,
        file_id,
        file_format,
        generation_method,
        created_at
      )
    `)
    .eq('id', ticketId)
    .maybeSingle();

  if (!ticket) {
    notFound();
  }

  // Fetch project from ticket's basket
  const { data: project } = await supabase
    .from('projects')
    .select('id, name, basket_id')
    .eq('basket_id', ticket.basket_id)
    .maybeSingle();

  if (!project) {
    notFound();
  }

  // Extract recipe info from metadata
  const recipeName = ticket.metadata?.recipe_slug || 'Work Request';
  const recipeParams = ticket.metadata?.recipe_parameters || {};
  const taskDescription = ticket.metadata?.task_description || '';

  return (
    <TicketTrackingClient
      projectId={projectId}
      projectName={project.name}
      ticket={ticket}
      recipeName={recipeName}
      recipeParams={recipeParams}
      taskDescription={taskDescription}
    />
  );
}
