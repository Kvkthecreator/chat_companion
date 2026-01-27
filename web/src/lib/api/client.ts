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
export interface UserPreferences {
  daily_messages_paused?: boolean;
  email_notifications_enabled?: boolean;
  support?: {
    style?: string;
    feedback_type?: string;
    questions?: string;
  };
  communication?: {
    message_tone?: string;
  };
}

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
  preferences?: UserPreferences;
  telegram_user_id?: number;
  telegram_username?: string;
  telegram_linked_at?: string;
  whatsapp_number?: string;
  whatsapp_linked_at?: string;
  onboarding_completed_at?: string;
  location?: string;
  // Silence detection settings (Phase 2 - Companion Outreach System)
  allow_silence_checkins?: boolean;
  silence_threshold_days?: number;
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

export interface UnifiedHistoryMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  created_at: string;
  conversation_id: string;
}

export interface UnifiedHistory {
  messages: UnifiedHistoryMessage[];
  current_conversation_id: string;
  days_included: number;
  total_messages: number;
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
  domain?: string;
  phase?: string;
  priority_weight?: number;
  follow_up_date?: string;
  key_details: string[];
  updated_at?: string;
}

// Template types for domain layer
export interface TemplateListItem {
  template_key: string;
  display_name: string;
  domain: string;
  icon: string;
  has_phases: boolean;
}

export interface TemplateDetail {
  id: string;
  template_key: string;
  display_name: string;
  domain: string;
  description?: string;
  trigger_phrases: string[];
  has_phases: boolean;
  phases?: string[];
  follow_up_prompts: {
    initial: string;
    check_in: string;
    phase_specific?: Record<string, string>;
  };
  typical_duration?: string;
  default_follow_up_days: number;
}

export interface ClassifyResponse {
  template_key?: string;
  domain: string;
  confidence: number;
  summary: string;
  key_entities: string[];
  phase_hint?: string;
}

export interface DomainSelection {
  template_key: string;
  details: string;
  is_primary?: boolean;
}

export interface OnboardingV2Request {
  domain_selections: DomainSelection[];
  preferences: {
    display_name: string;
    companion_name?: string;
    preferred_message_time?: string;
    timezone?: string;
  };
}

export interface OnboardingV2Response {
  success: boolean;
  acknowledgment_message: string;
  conversation_id: string;
  threads_created: string[];
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

// Artifact types
export type ArtifactType = "thread_journey" | "domain_health" | "communication" | "relationship";

export interface ArtifactSection {
  type: string;
  content: unknown;
}

export interface Artifact {
  id?: string;
  artifact_type: ArtifactType;
  title: string;
  sections: ArtifactSection[];
  companion_voice?: string;
  data_sources: string[];
  is_meaningful: boolean;
  min_data_reason?: string;
  thread_id?: string;
  domain?: string;
  generated_at?: string;
}

export interface ArtifactListItem {
  id: string;
  artifact_type: ArtifactType;
  title: string;
  is_meaningful: boolean;
  thread_id?: string;
  domain?: string;
  generated_at: string;
}

export interface ArtifactAvailability {
  thread_journey: {
    available: boolean;
    threads?: Array<{
      thread_id: string;
      topic: string;
      domain?: string;
      days_active: number;
    }>;
  };
  domain_health: {
    available: boolean;
    domains?: Array<{
      domain: string;
      thread_count: number;
    }>;
  };
  communication: {
    available: boolean;
    message_count?: number;
    conversation_count?: number;
  };
  relationship: {
    available: boolean;
    days_together?: number;
    conversation_count?: number;
  };
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
    complete: (data?: { situation?: string }) =>
      request<OnboardingState>("/onboarding/complete", {
        method: "POST",
        body: data ? JSON.stringify(data) : undefined,
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
    // Domain-first onboarding v2
    completeV2: (data: OnboardingV2Request) =>
      request<OnboardingV2Response>("/onboarding/complete-v2", {
        method: "POST",
        body: JSON.stringify(data),
      }),
  },

  // Template endpoints for domain layer
  templates: {
    list: () => request<TemplateListItem[]>("/templates"),
    get: (key: string) => request<TemplateDetail>(`/templates/${key}`),
    classify: (text: string) =>
      request<ClassifyResponse>("/templates/classify", {
        method: "POST",
        body: JSON.stringify({ text }),
      }),
    getFollowUpPrompt: (key: string, phase?: string, promptType: string = "check_in") => {
      const params = new URLSearchParams();
      if (phase) params.set("phase", phase);
      params.set("prompt_type", promptType);
      return request<{ prompt: string; template_key: string; phase?: string }>(
        `/templates/${key}/follow-up?${params.toString()}`
      );
    },
  },

  // Artifact endpoints
  artifacts: {
    // Check which artifacts are available
    checkAvailability: () => request<ArtifactAvailability>("/artifacts/available"),

    // List all stored artifacts
    list: (meaningfulOnly: boolean = true) => {
      const params = new URLSearchParams();
      params.set("meaningful_only", String(meaningfulOnly));
      return request<ArtifactListItem[]>(`/artifacts?${params.toString()}`);
    },

    // Get Thread Journey artifact
    getThreadJourney: (threadId: string, regenerate: boolean = false) => {
      const params = regenerate ? "?regenerate=true" : "";
      return request<Artifact>(`/artifacts/thread-journey/${threadId}${params}`);
    },

    // Get Domain Health artifact
    getDomainHealth: (domain: string, regenerate: boolean = false) => {
      const params = regenerate ? "?regenerate=true" : "";
      return request<Artifact>(`/artifacts/domain-health/${domain}${params}`);
    },

    // Get Communication Profile artifact
    getCommunicationProfile: (regenerate: boolean = false) => {
      const params = regenerate ? "?regenerate=true" : "";
      return request<Artifact>(`/artifacts/communication-profile${params}`);
    },

    // Get Relationship Summary artifact
    getRelationshipSummary: (regenerate: boolean = false) => {
      const params = regenerate ? "?regenerate=true" : "";
      return request<Artifact>(`/artifacts/relationship-summary${params}`);
    },

    // Log a thread event (for timeline building)
    logEvent: (data: {
      thread_id: string;
      event_type: string;
      description: string;
      event_date?: string;
    }) =>
      request<{ success: boolean; event_id: string; thread_id: string }>("/artifacts/events", {
        method: "POST",
        body: JSON.stringify(data),
      }),
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
    // Get unified history across multiple conversations (for continuous chat UX)
    getUnifiedHistory: (params?: { days?: number; max_messages?: number }) => {
      const searchParams = new URLSearchParams();
      if (params?.days) searchParams.set("days", String(params.days));
      if (params?.max_messages) searchParams.set("max_messages", String(params.max_messages));
      const query = searchParams.toString();
      return request<UnifiedHistory>(
        `/conversations/history${query ? `?${query}` : ""}`
      );
    },
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

  // Admin endpoints (restricted by email allowlist on backend)
  admin: {
    stats: () => request<AdminStatsResponse>("/admin/stats"),
    funnel: (days: number = 30) => request<ActivationFunnelResponse>(`/admin/activation-funnel?days=${days}`),
    messagePriority: (days: number = 30) => request<MessagePriorityMetrics>(`/admin/message-priority?days=${days}`),
    extractionStats: () => request<ExtractionStatsResponse>("/admin/extraction-stats"),
  },
};

// Admin types (matches backend response models)
export interface AdminStatsResponse {
  overview: {
    total_users: number;
    users_7d: number;
    users_30d: number;
    premium_users: number;
    total_revenue_cents: number;
    total_messages: number;
    total_sessions: number;
    guest_sessions_total: number;
    guest_sessions_24h: number;
    guest_sessions_converted: number;
  };
  signups_by_day: AdminSignupDay[];
  users: AdminUserEngagement[];
  purchases: AdminPurchase[];
  guest_sessions: AdminGuestSession[];
}

export interface AdminSignupDay {
  date: string;
  count: number;
}

export interface AdminUserEngagement {
  id: string;
  display_name: string;
  email?: string;
  subscription_status: string;
  spark_balance: number;
  messages_sent_count: number;
  flux_generations_used: number;
  session_count: number;
  engagement_count: number;
  created_at: string;
  last_active?: string;
  signup_source?: string;
  signup_campaign?: string;
}

export interface AdminPurchase {
  id: string;
  user_id: string;
  user_name?: string;
  pack_name: string;
  sparks_amount: number;
  price_cents: number;
  status: string;
  created_at: string;
}

export interface AdminGuestSession {
  id: string;
  guest_session_id: string;
  character_name: string;
  message_count: number;
  ip_hash?: string;
  converted: boolean;
  created_at: string;
}

export interface ActivationFunnelResponse {
  funnel: FunnelStep[];
  message_distribution: MessageDistribution[];
  dropoff_analysis: DropoffPoint[];
  source_performance: SourcePerformance[];
  cohort_retention: CohortRetention[];
  insights: string[];
}

export interface FunnelStep {
  step: string;
  count: number;
  percentage: number;
}

export interface MessageDistribution {
  bucket: string;
  count: number;
  percentage: number;
}

export interface DropoffPoint {
  description: string;
  user_count: number;
  example_users: string[];
}

export interface SourcePerformance {
  source: string;
  campaign?: string;
  signups: number;
  activation_rate: number;
  engagement_rate: number;
}

export interface CohortRetention {
  cohort_date: string;
  cohort_size: number;
  day_1: number;
  day_7: number;
  day_14: number;
  day_30: number;
}

export interface MessagePriorityMetrics {
  total_messages: number;
  distribution: PriorityDistribution[];
  generic_rate: number;
  personal_rate: number;
  daily_stats: DailyPriorityStats[];
  insights: string[];
}

export interface PriorityDistribution {
  priority: string;
  count: number;
  percentage: number;
}

export interface DailyPriorityStats {
  date: string;
  total: number;
  priority_1: number;
  priority_2: number;
  priority_3: number;
  priority_4: number;
  priority_5: number;
  generic_rate: number;
}

export interface ExtractionStatsResponse {
  total_24h: number;
  failed_24h: number;
  failure_rate_24h: number;
  total_7d: number;
  failed_7d: number;
  failure_rate_7d: number;
  avg_duration_ms: number;
  daily_stats: ExtractionDayStats[];
  recent_failures: RecentFailure[];
  insights: string[];
}

export interface ExtractionDayStats {
  date: string;
  total: number;
  success: number;
  failed: number;
  failure_rate: number;
  avg_duration_ms: number;
  avg_items: number;
}

export interface RecentFailure {
  created_at: string;
  extraction_type: string;
  error_message?: string;
  duration_ms?: number;
  user_display_name?: string;
}

export default api;
