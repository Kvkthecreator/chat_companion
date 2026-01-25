/**
 * Chat Companion API Types
 */

// User types
export interface User {
  id: string;
  email: string;
  display_name?: string;
  companion_name?: string;
  timezone?: string;
  preferred_message_time?: string;
  support_style?: string;
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

export interface UserUpdate {
  display_name?: string;
  companion_name?: string;
  timezone?: string;
  preferred_message_time?: string;
  support_style?: string;
  location?: string;
}

// Onboarding types
export interface OnboardingState {
  user_id: string;
  current_step: string;
  completed_at?: string;
  data: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

// Chat onboarding types (ADR-003)
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

// Conversation types
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

// Message types
export interface Message {
  id: string;
  conversation_id: string;
  role: "user" | "assistant";
  content: string;
  telegram_message_id?: number;
  metadata: Record<string, unknown>;
  created_at: string;
}

// User context types
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

// Usage types
export interface DailyUsage {
  messages_sent: number;
  messages_received: number;
  usage_date: string;
}

export interface UsageResponse {
  today: DailyUsage;
  this_week: DailyUsage[];
}

// Subscription types
export interface SubscriptionStatus {
  status: string;
  expires_at?: string;
  is_active: boolean;
  plan?: string;
}

export interface CheckoutResponse {
  checkout_url: string;
}

export interface PortalResponse {
  portal_url: string;
}

// Telegram types
export interface TelegramDeepLink {
  deep_link_url: string;
  expires_in_minutes: number;
}

// Re-export admin types from API client
export type {
  AdminStatsResponse,
  AdminSignupDay,
  AdminUserEngagement,
  AdminPurchase,
  AdminGuestSession,
  ActivationFunnelResponse,
  FunnelStep,
  MessageDistribution,
  DropoffPoint,
  SourcePerformance,
  CohortRetention,
  MessagePriorityMetrics,
  PriorityDistribution,
  DailyPriorityStats,
  ExtractionStatsResponse,
  ExtractionDayStats,
  RecentFailure,
} from "@/lib/api/client";
