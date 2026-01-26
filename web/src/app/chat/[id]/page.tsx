"use client";

import { useState, useEffect, useRef } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { api, User, Message, ThreadSummary } from "@/lib/api/client";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Skeleton } from "@/components/ui/skeleton";
import { ThreadContextHeader } from "@/components/chat/ThreadContextHeader";

export default function ChatPage() {
  const params = useParams();
  const conversationId = params.id as string;

  const [user, setUser] = useState<User | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [threads, setThreads] = useState<ThreadSummary[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isSending, setIsSending] = useState(false);
  const [streamingContent, setStreamingContent] = useState("");
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Load user, threads, and conversation messages
  useEffect(() => {
    const init = async () => {
      try {
        const [userData, memoryData, msgs] = await Promise.all([
          api.users.me(),
          api.memory.getSummary(),
          api.conversations.getMessages(conversationId, { limit: 50 }),
        ]);

        setUser(userData);
        setThreads(memoryData.active_threads || []);
        setMessages(msgs.reverse()); // API returns newest first
      } catch (err) {
        console.error("Failed to load conversation:", err);
        setError("Conversation not found");
      }
      setIsLoading(false);
    };

    if (conversationId) {
      init();
    }
  }, [conversationId]);

  // Scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, streamingContent]);

  const sendMessage = async () => {
    if (!input.trim() || !conversationId || isSending) return;

    const content = input.trim();
    setInput("");
    setIsSending(true);

    // Add user message optimistically
    const tempUserMsg: Message = {
      id: `temp-${Date.now()}`,
      conversation_id: conversationId,
      role: "user",
      content,
      metadata: {},
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, tempUserMsg]);

    try {
      // Stream the response
      setStreamingContent("");
      let fullContent = "";

      for await (const chunk of api.conversations.sendMessageStream(conversationId, content)) {
        if (chunk.type === "chunk" && chunk.content) {
          fullContent += chunk.content;
          setStreamingContent(fullContent);
        } else if (chunk.type === "done") {
          fullContent = chunk.content || fullContent;
        }
      }

      // Add assistant message
      const assistantMsg: Message = {
        id: `assistant-${Date.now()}`,
        conversation_id: conversationId,
        role: "assistant",
        content: fullContent,
        metadata: {},
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, assistantMsg]);
      setStreamingContent("");
    } catch (err) {
      console.error("Failed to send message:", err);
      // Remove optimistic user message on error
      setMessages((prev) => prev.filter((m) => m.id !== tempUserMsg.id));
      setInput(content); // Restore input
    }

    setIsSending(false);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  if (isLoading) {
    return (
      <div className="flex h-full flex-col">
        <div className="flex items-center justify-between border-b px-6 py-4">
          <Skeleton className="h-6 w-32" />
          <Skeleton className="h-9 w-20" />
        </div>
        <div className="flex-1 space-y-4 p-6">
          <Skeleton className="h-16 w-3/4" />
          <Skeleton className="ml-auto h-12 w-1/2" />
          <Skeleton className="h-20 w-2/3" />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex h-full flex-col items-center justify-center gap-4">
        <p className="text-muted-foreground">{error}</p>
        <Link href="/dashboard">
          <Button>Back to Dashboard</Button>
        </Link>
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col bg-background">
      {/* Header */}
      <div className="flex items-center justify-between border-b px-6 py-4">
        <div className="flex items-center gap-3">
          <Link href="/dashboard">
            <Button variant="ghost" size="icon">
              <BackIcon className="h-5 w-5" />
            </Button>
          </Link>
          <div>
            <h1 className="font-semibold">{user?.companion_name || "Companion"}</h1>
            <p className="text-xs text-muted-foreground">Online</p>
          </div>
        </div>
        <Link href="/settings">
          <Button variant="ghost" size="sm">
            Settings
          </Button>
        </Link>
      </div>

      {/* Thread Context Header */}
      {threads.length > 0 && (
        <ThreadContextHeader
          threads={threads}
          maxVisible={3}
          onThreadClick={(threadId) => {
            // Could navigate to memory page or show thread details
            console.log("Thread clicked:", threadId);
          }}
        />
      )}

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-6">
        <div className="mx-auto max-w-2xl space-y-4">
          {messages.length === 0 && !streamingContent && (
            <div className="py-12 text-center">
              <div className="text-4xl">💬</div>
              <p className="mt-4 text-lg font-medium">
                Start chatting with {user?.companion_name || "your companion"}
              </p>
              <p className="text-sm text-muted-foreground">
                They're here to listen and support you.
              </p>
            </div>
          )}

          {messages.map((message) => (
            <MessageBubble
              key={message.id}
              role={message.role}
              content={message.content}
              timestamp={message.created_at}
            />
          ))}

          {streamingContent && (
            <MessageBubble
              role="assistant"
              content={streamingContent}
              isStreaming
            />
          )}

          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input */}
      <div className="border-t p-4 pb-20 md:pb-4">
        <div className="mx-auto flex max-w-2xl gap-3">
          <Textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={`Message ${user?.companion_name || "your companion"}...`}
            className="min-h-[44px] max-h-[200px] resize-none"
            rows={1}
            disabled={isSending}
          />
          <Button
            onClick={sendMessage}
            disabled={!input.trim() || isSending}
            className="shrink-0"
          >
            {isSending ? (
              <LoadingIcon className="h-4 w-4 animate-spin" />
            ) : (
              <SendIcon className="h-4 w-4" />
            )}
          </Button>
        </div>
      </div>
    </div>
  );
}

interface MessageBubbleProps {
  role: "user" | "assistant";
  content: string;
  timestamp?: string;
  isStreaming?: boolean;
}

function MessageBubble({ role, content, timestamp, isStreaming }: MessageBubbleProps) {
  const isUser = role === "user";

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[85%] rounded-2xl px-4 py-2.5 ${
          isUser
            ? "bg-primary text-primary-foreground"
            : "bg-muted text-foreground"
        }`}
      >
        <p className="whitespace-pre-wrap text-sm">{content}</p>
        {timestamp && !isStreaming && (
          <p
            className={`mt-1 text-xs ${
              isUser ? "text-primary-foreground/70" : "text-muted-foreground"
            }`}
          >
            {formatTime(timestamp)}
          </p>
        )}
        {isStreaming && (
          <span className="inline-block h-2 w-2 animate-pulse rounded-full bg-current" />
        )}
      </div>
    </div>
  );
}

function formatTime(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleTimeString("en-US", {
    hour: "numeric",
    minute: "2-digit",
    hour12: true,
  });
}

function BackIcon({ className }: { className?: string }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
    >
      <path d="M19 12H5M12 19l-7-7 7-7" />
    </svg>
  );
}

function SendIcon({ className }: { className?: string }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
    >
      <path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z" />
    </svg>
  );
}

function LoadingIcon({ className }: { className?: string }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
    >
      <path d="M21 12a9 9 0 1 1-6.219-8.56" />
    </svg>
  );
}
