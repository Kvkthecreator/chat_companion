/**
 * Daisy API Client for React Native
 * Mirrors the web client with mobile-specific handling
 */

import { supabase } from "../supabase/client";

const API_BASE_URL = process.env.EXPO_PUBLIC_API_URL || "http://localhost:10000";

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

  if (response.status === 204) {
    return null as T;
  }

  return response.json();
}

// =============================================================================
// Types
// =============================================================================

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

export interface SubscriptionStatus {
  status: string;
  expires_at?: string;
  is_active: boolean;
}

export interface DeviceInfo {
  device_id: string;
  platform: "ios" | "android";
  push_token?: string;
  app_version?: string;
  os_version?: string;
  device_model?: string;
}

export interface DeviceResponse {
  id: string;
  device_id: string;
  platform: string;
  has_push_token: boolean;
  app_version?: string;
  last_active_at: string;
}

export interface PushHistoryItem {
  id: string;
  title: string;
  body: string;
  status: string;
  sent_at?: string;
  delivered_at?: string;
  clicked_at?: string;
  created_at: string;
}

export interface PushStats {
  total_sent: number;
  total_delivered: number;
  total_clicked: number;
  total_failed: number;
  delivery_rate: number;
  click_rate: number;
}

// =============================================================================
// API Client
// =============================================================================

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
    create: (channel: string = "mobile") =>
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

  // Device endpoints (mobile-specific)
  devices: {
    register: (data: DeviceInfo) =>
      request<DeviceResponse>("/devices", {
        method: "POST",
        body: JSON.stringify(data),
      }),
    update: (deviceId: string, data: { push_token?: string; app_version?: string; is_active?: boolean }) =>
      request<{ status: string; device_id: string }>(`/devices/${deviceId}`, {
        method: "PATCH",
        body: JSON.stringify(data),
      }),
    unregister: (deviceId: string) =>
      request<null>(`/devices/${deviceId}`, { method: "DELETE" }),
    list: () => request<DeviceResponse[]>("/devices"),
    heartbeat: (deviceId: string) =>
      request<{ status: string }>(`/devices/${deviceId}/heartbeat`, {
        method: "POST",
      }),
  },

  // Push notification endpoints (mobile-specific)
  push: {
    test: (title?: string, body?: string) =>
      request<{ status: string; devices_targeted: number; successful: number; failed: number }>(
        "/push/test",
        {
          method: "POST",
          body: JSON.stringify({ title, body }),
        }
      ),
    history: (limit?: number, offset?: number) => {
      const searchParams = new URLSearchParams();
      if (limit) searchParams.set("limit", String(limit));
      if (offset) searchParams.set("offset", String(offset));
      const query = searchParams.toString();
      return request<PushHistoryItem[]>(`/push/history${query ? `?${query}` : ""}`);
    },
    markClicked: (notificationId: string) =>
      request<{ status: string }>(`/push/${notificationId}/clicked`, {
        method: "PATCH",
      }),
    stats: (days?: number) => {
      const query = days ? `?days=${days}` : "";
      return request<PushStats>(`/push/stats${query}`);
    },
  },
};

export default api;
