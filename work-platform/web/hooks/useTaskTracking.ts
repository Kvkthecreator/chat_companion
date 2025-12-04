"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { createBrowserClient } from "@/lib/supabase/clients";

/**
 * @deprecated This hook uses SSE which is being replaced by Supabase Realtime.
 *
 * MIGRATION NOTICE (2024-12):
 * Task progress is now delivered via Supabase Realtime subscription on work_tickets table.
 * The metadata.current_todos field is updated in real-time during agent execution.
 *
 * Instead of using this hook, subscribe to work_tickets updates:
 *
 * ```tsx
 * const supabase = createBrowserClient();
 * const channel = supabase
 *   .channel(`work_ticket_${ticketId}`)
 *   .on('postgres_changes', {
 *     event: 'UPDATE',
 *     schema: 'public',
 *     table: 'work_tickets',
 *     filter: `id=eq.${ticketId}`,
 *   }, (payload) => {
 *     const currentTodos = payload.new.metadata?.current_todos;
 *     // Use currentTodos for progress display
 *   })
 *   .subscribe();
 * ```
 *
 * See: TicketTrackingClient.tsx for the new implementation.
 */

/**
 * Task progress update from TodoWrite tool
 */
export interface TaskUpdate {
  content: string;
  status: "pending" | "in_progress" | "completed";
  activeForm: string;
}

/**
 * SSE event from task streaming endpoint
 * @deprecated Use Supabase Realtime instead
 */
export interface TaskStreamEvent {
  type: "connected" | "todo_update" | "completed" | "timeout" | "task_started" | "task_update" | "task_completed" | "task_failed";
  ticket_id?: string;
  todos?: TaskUpdate[];
  status?: string;
  timestamp?: string;
  source?: string;
  // New fields for task streaming
  current_step?: string;
  activeForm?: string;
  output_count?: number;
  error?: string;
}

/**
 * Hook return value
 */
export interface UseTaskTrackingResult {
  tasks: TaskUpdate[];
  isConnected: boolean;
  error: string | null;
  completionStatus: string | null;
}

/**
 * @deprecated This hook uses SSE which is being replaced by Supabase Realtime.
 * See file header for migration instructions.
 *
 * Real-time Task Tracking Hook (Legacy SSE)
 *
 * Subscribes to SSE stream for agent task progress updates (TodoWrite tool).
 * Displays real-time visibility into what the agent is doing during execution.
 *
 * @param workTicketId - Work ticket UUID to track
 * @param enabled - Whether to enable the SSE connection (default: true)
 */
export function useTaskTracking(
  workTicketId: string | null | undefined,
  enabled: boolean = true
): UseTaskTrackingResult {
  const [tasks, setTasks] = useState<TaskUpdate[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [completionStatus, setCompletionStatus] = useState<string | null>(null);
  const eventSourceRef = useRef<EventSource | null>(null);

  const disconnect = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
      setIsConnected(false);
    }
  }, []);

  useEffect(() => {
    // Skip if not enabled or no ticket ID
    if (!enabled || !workTicketId) {
      disconnect();
      return;
    }

    // Get token and create SSE connection
    const connectWithToken = async () => {
      try {
        // Get JWT token from Supabase session
        const supabase = createBrowserClient();
        const { data: { session } } = await supabase.auth.getSession();

        if (!session?.access_token) {
          setError("No authentication token available");
          return;
        }

        // Create SSE connection with token as query param (EventSource can't send headers)
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || "https://yarnnn-app-fullstack.onrender.com";
        const eventSource = new EventSource(
          `${apiUrl}/api/work/tickets/${workTicketId}/stream?token=${encodeURIComponent(session.access_token)}`
        );

        eventSourceRef.current = eventSource;

        // Handle incoming messages
        eventSource.onmessage = (event) => {
          try {
            const data: TaskStreamEvent = JSON.parse(event.data);

            if (data.type === "connected") {
              setIsConnected(true);
              setError(null);
            } else if (data.type === "todo_update" && data.todos) {
              // Legacy format - array of todos
              setTasks(data.todos);
            } else if (data.type === "task_started" || data.type === "task_update") {
              // New format - individual task update
              const taskUpdate: TaskUpdate = {
                content: data.current_step || "",
                status: data.status === "in_progress" ? "in_progress" : "pending",
                activeForm: data.activeForm || data.current_step || "Working...",
              };
              // Append to tasks list (showing progress history)
              setTasks(prev => {
                // Replace last task if it's in_progress, otherwise append
                const newTasks = [...prev];
                const lastIndex = newTasks.findIndex(t => t.status === "in_progress");
                if (lastIndex >= 0) {
                  newTasks[lastIndex] = { ...newTasks[lastIndex], status: "completed" };
                }
                newTasks.push(taskUpdate);
                return newTasks;
              });
            } else if (data.type === "task_completed") {
              // Mark all tasks as completed
              setTasks(prev => prev.map(t => ({ ...t, status: "completed" as const })));
              setCompletionStatus("completed");
              disconnect();
            } else if (data.type === "task_failed") {
              setError(data.error || "Task execution failed");
              setCompletionStatus("failed");
              disconnect();
            } else if (data.type === "completed") {
              setCompletionStatus(data.status || "completed");
              disconnect();
            } else if (data.type === "timeout") {
              setError("Stream timeout - task may still be running");
              disconnect();
            }
          } catch (err) {
            console.error("[useTaskTracking] Failed to parse SSE event:", err);
            setError("Failed to parse task update");
          }
        };

        // Handle errors
        eventSource.onerror = (err) => {
          console.error("[useTaskTracking] SSE error:", err);
          setError("Connection error - retrying...");
          setIsConnected(false);
          // EventSource will automatically retry connection
        };
      } catch (err) {
        console.error("[useTaskTracking] Failed to connect:", err);
        setError("Failed to establish connection");
      }
    };

    connectWithToken();

    // Cleanup on unmount
    return () => {
      disconnect();
    };
  }, [workTicketId, enabled, disconnect]);

  return {
    tasks,
    isConnected,
    error,
    completionStatus,
  };
}
