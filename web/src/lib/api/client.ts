/**
 * Chat Companion API Client
 */

import { createClient } from "@/lib/supabase/client";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:10000";

export class APIError extends Error {
  constructor(
    public status: number,
    public statusText: string,
    public data?: unknown
  ) {
    super(`API Error: ${status} ${statusText}`);
    this.name = "APIError";
  }
}

async function getAuthHeaders(): Promise<HeadersInit> {
  const supabase = createClient();
  const {
    data: { session },
  } = await supabase.auth.getSession();

  const headers: HeadersInit = {
    "Content-Type": "application/json",
  };

  if (session?.access_token) {
    headers["Authorization"] = `Bearer ${session.access_token}`;
  }

  return headers;
}

async function request<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const headers = await getAuthHeaders();

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers: {
      ...headers,
      ...options.headers,
    },
  });

  if (!response.ok) {
    let data;
    try {
      data = await response.json();
    } catch {
      data = null;
    }
    throw new APIError(response.status, response.statusText, data);
  }

  // Handle 204 No Content
  if (response.status === 204) {
    return null as T;
  }

  return response.json();
}

// Types for the companion app
export interface User {
  id: string;
  email: string;
  display_name?: string;
  companion_name?: string;
  timezone?: string;
  preferred_message_time?: string;
  message_time_flexibility?: "exact" | "around" | "window";
  message_time_window?: "morning" | "midday" | "evening" | "night";
  support_style?: string;
  preferred_channel?: "push" | "telegram" | "whatsapp" | "none";
  telegram_user_id?: number;
  telegram_username?: string;
  telegram_linked_at?: string;
  whatsapp_number?: string;
  whatsapp_linked_at?: string;
  onboarding_completed_at?: string;
  location?: string;
  created_at: string;
  updated_at: string;
}

export interface OnboardingState {
  user_id: string;
  current_step: string;
  completed_at?: string;
  data: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface ChatOnboardingState {
  message?: string;
  step: string;
  expects?: string;
  options?: string[];
  is_complete: boolean;
}

export interface ChatResponseResult {
  success: boolean;
  is_complete: boolean;
  step?: string;
  next_message?: string;
  expects?: string;
  options?: string[];
  error?: string;
  retry_message?: string;
}

export interface Conversation {
  id: string;
  user_id: string;
  channel: string;
  started_at: string;
  ended_at?: string;
  message_count: number;
  initiated_by: string;
  mood_summary?: string;
  topics: string[];
  created_at: string;
}

export interface Message {
  id: string;
  conversation_id: string;
  role: "user" | "assistant";
  content: string;
  telegram_message_id?: number;
  metadata: Record<string, unknown>;
  created_at: string;
}

export interface UserContext {
  id: string;
  user_id: string;
  category: string;
  key: string;
  value: string;
  importance_score: number;
  emotional_valence: number;
  source: string;
  created_at: string;
  updated_at: string;
  last_referenced_at?: string;
  expires_at?: string;
}

export interface DailyUsage {
  messages_sent: number;
  messages_received: number;
  usage_date: string;
}

export interface SubscriptionStatus {
  status: string;
  expires_at?: string;
  is_active: boolean;
}

export interface TelegramDeepLink {
  deep_link_url: string;
  expires_in_minutes: number;
}

// Memory types
export interface ThreadSummary {
  id: string;
  topic: string;
  summary: string;
  status: string;
  follow_up_date?: string;
  key_details: string[];
  updated_at?: string;
}

export interface FollowUpSummary {
  id: string;
  question: string;
  context: string;
  follow_up_date: string;
  source_thread?: string;
}

export interface MemorySummary {
  active_threads: ThreadSummary[];
  pending_follow_ups: FollowUpSummary[];
  thread_count: number;
  fact_count: number;
}

export interface FactItem {
  id: string;
  category: string;
  key: string;
  value: string;
  importance_score: number;
  created_at?: string;
}

export interface PatternItem {
  id: string;
  pattern_type: string;
  description: string;
  confidence: number;
  message_hint?: string;
}

export interface FullMemory {
  threads: ThreadSummary[];
  follow_ups: FollowUpSummary[];
  facts: Record<string, FactItem[]>;
  patterns: PatternItem[];
}

export const api = {
  // User endpoints
  users: {
    me: () => request<User>("/users/me"),
    update: (data: Partial<User>) =>
      request<User>("/users/me", {
        method: "PATCH",
        body: JSON.stringify(data),
      }),
    deleteAccount: (confirmation: string, reason?: string) =>
      request<{ status: string; message: string }>("/users/me", {
        method: "DELETE",
        body: JSON.stringify({ confirmation, reason }),
      }),
  },

  // Onboarding endpoints
  onboarding: {
    get: () => request<OnboardingState>("/onboarding"),
    update: (data: { step?: string; data?: Record<string, unknown> }) =>
      request<OnboardingState>("/onboarding", {
        method: "PATCH",
        body: JSON.stringify(data),
      }),
    complete: () =>
      request<OnboardingState>("/onboarding/complete", {
        method: "POST",
      }),
    // Chat-based onboarding (ADR-003)
    chat: {
      getState: () => request<ChatOnboardingState>("/onboarding/chat"),
      respond: (response: string) =>
        request<ChatResponseResult>("/onboarding/chat/respond", {
          method: "POST",
          body: JSON.stringify({ response }),
        }),
      reset: () =>
        request<ChatOnboardingState>("/onboarding/chat/reset", {
          method: "POST",
        }),
    },
  },

  // Conversation endpoints
  conversations: {
    list: (params?: { limit?: number; offset?: number }) => {
      const searchParams = new URLSearchParams();
      if (params?.limit) searchParams.set("limit", String(params.limit));
      if (params?.offset) searchParams.set("offset", String(params.offset));
      const query = searchParams.toString();
      return request<Conversation[]>(
        `/conversations${query ? `?${query}` : ""}`
      );
    },
    get: (id: string) => request<Conversation>(`/conversations/${id}`),
    create: (channel: string = "web") =>
      request<Conversation>("/conversations", {
        method: "POST",
        body: JSON.stringify({ channel }),
      }),
    getMessages: (id: string, params?: { limit?: number; before_id?: string }) => {
      const searchParams = new URLSearchParams();
      if (params?.limit) searchParams.set("limit", String(params.limit));
      if (params?.before_id) searchParams.set("before_id", params.before_id);
      const query = searchParams.toString();
      return request<Message[]>(
        `/conversations/${id}/messages${query ? `?${query}` : ""}`
      );
    },
    sendMessage: (id: string, content: string) =>
      request<Message>(`/conversations/${id}/messages`, {
        method: "POST",
        body: JSON.stringify({ content }),
      }),
    sendMessageStream: async function* (id: string, content: string) {
      const headers = await getAuthHeaders();

      const response = await fetch(
        `${API_BASE_URL}/conversations/${id}/messages/stream`,
        {
          method: "POST",
          headers,
          body: JSON.stringify({ content }),
        }
      );

      if (!response.ok) {
        let data;
        try {
          data = await response.json();
        } catch {
          data = null;
        }
        throw new APIError(response.status, response.statusText, data);
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (!reader) {
        throw new Error("No response body");
      }

      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          const trimmedLine = line.trim();
          if (trimmedLine.startsWith("data: ")) {
            const data = trimmedLine.slice(6);
            if (data === "[DONE]") return;
            if (data.startsWith("[ERROR]")) throw new Error(data.slice(8));
            try {
              const parsed = JSON.parse(data);
              yield parsed;
            } catch {
              console.warn("[SSE] Failed to parse:", data.substring(0, 100));
            }
          }
        }
      }
    },
  },

  // User context endpoints
  context: {
    list: (params?: { category?: string; limit?: number }) => {
      const searchParams = new URLSearchParams();
      if (params?.category) searchParams.set("category", params.category);
      if (params?.limit) searchParams.set("limit", String(params.limit));
      const query = searchParams.toString();
      return request<UserContext[]>(`/context${query ? `?${query}` : ""}`);
    },
    create: (data: {
      category: string;
      key: string;
      value: string;
      importance_score?: number;
      emotional_valence?: number;
    }) =>
      request<UserContext>("/context", {
        method: "POST",
        body: JSON.stringify(data),
      }),
    delete: (id: string) =>
      request<null>(`/context/${id}`, { method: "DELETE" }),
  },

  // Usage endpoints
  usage: {
    today: () => request<DailyUsage>("/usage/today"),
    history: (days?: number) => {
      const query = days ? `?days=${days}` : "";
      return request<DailyUsage[]>(`/usage/history${query}`);
    },
  },

  // Telegram endpoints
  telegram: {
    getDeepLink: () => request<TelegramDeepLink>("/telegram/deep-link"),
    unlink: () =>
      request<{ status: string }>("/telegram/unlink", { method: "POST" }),
  },

  // Subscription endpoints
  subscription: {
    getStatus: () => request<SubscriptionStatus>("/subscription/status"),
    createCheckout: (variantId?: string) =>
      request<{ checkout_url: string }>("/subscription/checkout", {
        method: "POST",
        body: JSON.stringify({ variant_id: variantId }),
      }),
    getPortal: () => request<{ portal_url: string }>("/subscription/portal"),
  },

  // Memory endpoints
  memory: {
    getSummary: () => request<MemorySummary>("/memory/summary"),
    getFull: () => request<FullMemory>("/memory/full"),
    deleteItem: (id: string) =>
      request<null>(`/memory/context/${id}`, { method: "DELETE" }),
    updateItem: (id: string, data: { value?: string; importance_score?: number }) =>
      request<Record<string, unknown>>(`/memory/context/${id}`, {
        method: "PATCH",
        body: JSON.stringify(data),
      }),
    resolveThread: (threadId: string) =>
      request<{ status: string }>(`/memory/threads/${threadId}/resolve`, {
        method: "POST",
      }),
  },
};

export default api;
