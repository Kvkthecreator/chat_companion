"use client";

import { useState, useCallback, useRef, useEffect } from "react";
import { api, APIError } from "@/lib/api/client";
import type { Message, Episode, Character, RateLimitError } from "@/types";

interface UseChatOptions {
  characterId: string;
  episodeTemplateId?: string;
  enabled?: boolean;
  onError?: (error: Error) => void;
  onRateLimitExceeded?: (error: RateLimitError) => void;
}

interface UseChatReturn {
  messages: Message[];
  isLoading: boolean;
  isSending: boolean;
  episode: Episode | null;
  streamingContent: string;
  suggestScene: boolean;
  sendMessage: (content: string) => Promise<void>;
  loadMessages: () => Promise<void>;
  startNewEpisode: () => Promise<void>;
  endEpisode: () => Promise<void>;
  clearSceneSuggestion: () => void;
}

export function useChat({ characterId, episodeTemplateId, enabled = true, onError, onRateLimitExceeded }: UseChatOptions): UseChatReturn {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSending, setIsSending] = useState(false);
  const [episode, setEpisode] = useState<Episode | null>(null);
  const [streamingContent, setStreamingContent] = useState("");
  const [suggestScene, setSuggestScene] = useState(false);

  const abortControllerRef = useRef<AbortController | null>(null);

  // Store callbacks in refs to avoid dependency issues causing infinite loops
  const onErrorRef = useRef(onError);
  onErrorRef.current = onError;
  const onRateLimitExceededRef = useRef(onRateLimitExceeded);
  onRateLimitExceededRef.current = onRateLimitExceeded;

  // Track if we've already loaded for this characterId + episodeTemplateId combo
  const loadedKeyRef = useRef<string | null>(null);

  // Load active episode and messages
  const loadMessages = useCallback(async () => {
    setIsLoading(true);
    try {
      // Get or create active episode
      let activeEpisode = await api.episodes.getActive(characterId);

      if (!activeEpisode) {
        // Start new episode with template if provided
        activeEpisode = await api.conversation.start(characterId, {
          episodeTemplateId,
        });
      }

      setEpisode(activeEpisode);

      // Load messages
      if (activeEpisode) {
        const msgs = await api.messages.list(activeEpisode.id);
        setMessages(msgs);
      }
    } catch (error) {
      onErrorRef.current?.(error as Error);
    } finally {
      setIsLoading(false);
    }
  }, [characterId, episodeTemplateId]);

  // Send message (non-streaming)
  const sendMessageSimple = useCallback(async (content: string) => {
    if (!episode || isSending) return;

    setIsSending(true);

    // Optimistically add user message
    const tempUserMessage: Message = {
      id: `temp-${Date.now()}`,
      episode_id: episode.id,
      role: "user",
      content,
      model_used: null,
      tokens_input: null,
      tokens_output: null,
      latency_ms: null,
      metadata: {},
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, tempUserMessage]);

    try {
      const response = await api.conversation.send(characterId, content);

      // Replace temp message and add response
      setMessages((prev) => {
        const filtered = prev.filter((m) => m.id !== tempUserMessage.id);
        // Add real user message (from response context) and assistant response
        return [
          ...filtered,
          { ...tempUserMessage, id: `user-${Date.now()}` },
          response,
        ];
      });
    } catch (error) {
      // Remove temp message on error
      setMessages((prev) => prev.filter((m) => m.id !== tempUserMessage.id));
      onErrorRef.current?.(error as Error);
    } finally {
      setIsSending(false);
    }
  }, [characterId, episode, isSending]);

  // Send message with streaming
  const sendMessage = useCallback(async (content: string) => {
    if (!episode || isSending) return;

    setIsSending(true);
    setStreamingContent("");

    // Add user message immediately
    const userMessage: Message = {
      id: `user-${Date.now()}`,
      episode_id: episode.id,
      role: "user",
      content,
      model_used: null,
      tokens_input: null,
      tokens_output: null,
      latency_ms: null,
      metadata: {},
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMessage]);

    try {
      let fullContent = "";
      let messageAdded = false;

      for await (const chunk of api.conversation.sendStream(characterId, content)) {
        if (chunk.type === "chunk") {
          fullContent += chunk.content;
          setStreamingContent(fullContent);
        } else if (chunk.type === "done") {
          // Add complete assistant message
          const assistantMessage: Message = {
            id: `assistant-${Date.now()}`,
            episode_id: episode.id,
            role: "assistant",
            content: chunk.content || fullContent,
            model_used: null,
            tokens_input: null,
            tokens_output: null,
            latency_ms: null,
            metadata: {},
            created_at: new Date().toISOString(),
          };
          setMessages((prev) => [...prev, assistantMessage]);
          setStreamingContent("");
          messageAdded = true;

          // Check if backend suggests generating a scene
          if (chunk.suggest_scene) {
            setSuggestScene(true);
          }
        }
      }

      // If stream ended without "done" event, add what we have
      if (fullContent && !messageAdded) {
        const assistantMessage: Message = {
          id: `assistant-${Date.now()}`,
          episode_id: episode.id,
          role: "assistant",
          content: fullContent,
          model_used: null,
          tokens_input: null,
          tokens_output: null,
          latency_ms: null,
          metadata: {},
          created_at: new Date().toISOString(),
        };
        setMessages((prev) => [...prev, assistantMessage]);
        setStreamingContent("");
      }
    } catch (error) {
      // Check if this is a rate limit error (429)
      if (error instanceof APIError && error.status === 429) {
        const rateLimitError = error.data as RateLimitError;
        onRateLimitExceededRef.current?.(rateLimitError);
        // Remove the optimistic user message on rate limit
        setMessages((prev) => prev.filter((m) => m.id !== userMessage.id));
      } else {
        onErrorRef.current?.(error as Error);
      }
      // Keep user message but show error for other errors
    } finally {
      setIsSending(false);
      setStreamingContent("");
    }
  }, [characterId, episode, isSending]);

  // Start new episode
  const startNewEpisode = useCallback(async () => {
    try {
      // End current episode if exists
      if (episode?.is_active) {
        await api.conversation.end(characterId);
      }

      // Start new episode
      const newEpisode = await api.conversation.start(characterId);
      setEpisode(newEpisode);
      setMessages([]);
    } catch (error) {
      onErrorRef.current?.(error as Error);
    }
  }, [characterId, episode]);

  // End current episode
  const endEpisode = useCallback(async () => {
    if (!episode?.is_active) return;

    try {
      const ended = await api.conversation.end(characterId);
      setEpisode(ended);
    } catch (error) {
      onErrorRef.current?.(error as Error);
    }
  }, [characterId, episode]);

  // Clear scene suggestion
  const clearSceneSuggestion = useCallback(() => {
    setSuggestScene(false);
  }, []);

  // Load on mount (only when enabled, and only once per characterId + episodeTemplateId combo)
  useEffect(() => {
    if (!enabled) {
      setIsLoading(false);
      return;
    }

    // Create a unique key for characterId + episodeTemplateId combo
    const loadKey = `${characterId}:${episodeTemplateId || "default"}`;

    // Prevent infinite loops - only load once per key
    if (loadedKeyRef.current === loadKey) {
      return;
    }
    loadedKeyRef.current = loadKey;

    loadMessages();

    return () => {
      abortControllerRef.current?.abort();
    };
  }, [loadMessages, enabled, characterId, episodeTemplateId]);

  return {
    messages,
    isLoading,
    isSending,
    episode,
    streamingContent,
    suggestScene,
    sendMessage,
    loadMessages,
    startNewEpisode,
    endEpisode,
    clearSceneSuggestion,
  };
}
