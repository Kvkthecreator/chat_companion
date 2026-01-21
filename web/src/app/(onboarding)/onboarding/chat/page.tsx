"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { useRouter } from "next/navigation";
import { createClient } from "@/lib/supabase/client";
import { api } from "@/lib/api/client";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { BackgroundBlob } from "@/components/ui/background-blob";
import { Loader2, Send, ArrowLeft } from "lucide-react";

interface ChatMessage {
  id: string;
  role: "assistant" | "user";
  content: string;
  options?: string[];
  expects?: string;
}

export default function ChatOnboardingPage() {
  const router = useRouter();
  const supabase = createClient();
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isSending, setIsSending] = useState(false);
  const [currentStep, setCurrentStep] = useState("");
  const [currentOptions, setCurrentOptions] = useState<string[]>([]);
  const [currentExpects, setCurrentExpects] = useState<string | undefined>();
  const [isComplete, setIsComplete] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Scroll to bottom of messages
  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  // Check auth and load initial state
  useEffect(() => {
    const init = async () => {
      const {
        data: { user },
      } = await supabase.auth.getUser();

      if (!user) {
        router.push("/login?next=/onboarding/chat");
        return;
      }

      try {
        // Check if user has completed onboarding
        const userData = await api.users.me();
        if (userData.onboarding_completed_at) {
          router.push("/dashboard");
          return;
        }

        // Get current chat onboarding state
        const state = await api.onboarding.chat.getState();

        if (state.is_complete) {
          router.push("/dashboard");
          return;
        }

        // Initialize with first message
        if (state.message) {
          setMessages([
            {
              id: "initial",
              role: "assistant",
              content: state.message,
              options: state.options,
              expects: state.expects,
            },
          ]);
          setCurrentOptions(state.options || []);
          setCurrentExpects(state.expects);
        }
        setCurrentStep(state.step);
        setIsLoading(false);
      } catch (err) {
        console.error("Failed to init chat onboarding:", err);
        setError("Failed to load. Please refresh the page.");
        setIsLoading(false);
      }
    };

    init();
  }, [router, supabase]);

  // Handle sending a message
  const sendMessage = async (content: string) => {
    if (!content.trim() || isSending) return;

    // Add user message
    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      role: "user",
      content: content.trim(),
    };
    setMessages((prev) => [...prev, userMessage]);
    setInputValue("");
    setCurrentOptions([]);
    setIsSending(true);
    setError(null);

    try {
      const result = await api.onboarding.chat.respond(content.trim());

      if (result.success) {
        if (result.is_complete) {
          // Add final message and redirect
          if (result.next_message) {
            setMessages((prev) => [
              ...prev,
              {
                id: `assistant-${Date.now()}`,
                role: "assistant",
                content: result.next_message,
              },
            ]);
          }
          setIsComplete(true);
          // Wait a bit for user to see the message, then redirect
          setTimeout(() => {
            router.push("/dashboard");
          }, 2000);
        } else {
          // Add assistant response
          if (result.next_message) {
            setMessages((prev) => [
              ...prev,
              {
                id: `assistant-${Date.now()}`,
                role: "assistant",
                content: result.next_message,
                options: result.options,
                expects: result.expects,
              },
            ]);
            setCurrentOptions(result.options || []);
            setCurrentExpects(result.expects);
          }
          if (result.step) {
            setCurrentStep(result.step);
          }
        }
      } else {
        // Show error or retry message
        if (result.retry_message) {
          setMessages((prev) => [
            ...prev,
            {
              id: `assistant-${Date.now()}`,
              role: "assistant",
              content: result.retry_message,
              options: result.options,
              expects: result.expects,
            },
          ]);
          setCurrentOptions(result.options || []);
          setCurrentExpects(result.expects);
        } else if (result.error) {
          setError(result.error);
        }
      }
    } catch (err) {
      console.error("Failed to send message:", err);
      setError("Failed to send message. Please try again.");
    } finally {
      setIsSending(false);
      inputRef.current?.focus();
    }
  };

  // Handle option click
  const handleOptionClick = (option: string) => {
    sendMessage(option);
  };

  // Handle form submit
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    sendMessage(inputValue);
  };

  // Handle key press
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage(inputValue);
    }
  };

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <div className="flex items-center gap-2 text-muted-foreground">
          <Loader2 className="h-5 w-5 animate-spin" />
          <span>Loading...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="relative min-h-screen bg-background text-foreground">
      <BackgroundBlob className="mx-auto max-w-5xl" />

      {/* Header */}
      <header className="fixed top-0 left-0 right-0 z-10 bg-background/80 backdrop-blur-sm border-b border-border">
        <div className="mx-auto max-w-2xl px-4 py-3 flex items-center gap-3">
          <button
            onClick={() => router.push("/onboarding")}
            className="p-2 rounded-lg hover:bg-muted transition-colors"
            title="Switch to form onboarding"
          >
            <ArrowLeft className="h-5 w-5" />
          </button>
          <div>
            <h1 className="font-semibold">Chat with your companion</h1>
            <p className="text-xs text-muted-foreground">
              Getting to know you
            </p>
          </div>
        </div>
      </header>

      {/* Messages */}
      <div className="mx-auto max-w-2xl px-4 pt-20 pb-32">
        <div className="space-y-4">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${
                message.role === "user" ? "justify-end" : "justify-start"
              }`}
            >
              <div
                className={`max-w-[80%] rounded-2xl px-4 py-3 ${
                  message.role === "user"
                    ? "bg-primary text-primary-foreground"
                    : "bg-muted"
                }`}
              >
                <p className="whitespace-pre-wrap">{message.content}</p>
              </div>
            </div>
          ))}

          {/* Typing indicator */}
          {isSending && (
            <div className="flex justify-start">
              <div className="bg-muted rounded-2xl px-4 py-3">
                <div className="flex gap-1">
                  <span className="w-2 h-2 bg-muted-foreground/50 rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
                  <span className="w-2 h-2 bg-muted-foreground/50 rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
                  <span className="w-2 h-2 bg-muted-foreground/50 rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input area */}
      <div className="fixed bottom-0 left-0 right-0 bg-background/80 backdrop-blur-sm border-t border-border">
        <div className="mx-auto max-w-2xl px-4 py-4">
          {/* Error message */}
          {error && (
            <div className="mb-3 rounded-lg bg-destructive/10 border border-destructive/30 px-3 py-2 text-sm text-destructive">
              {error}
            </div>
          )}

          {/* Complete message */}
          {isComplete && (
            <div className="mb-3 rounded-lg bg-green-500/10 border border-green-500/30 px-3 py-2 text-sm text-green-600 dark:text-green-400 text-center">
              Setup complete! Redirecting to your dashboard...
            </div>
          )}

          {/* Quick options */}
          {currentOptions.length > 0 && !isSending && !isComplete && (
            <div className="mb-3 flex flex-wrap gap-2">
              {currentOptions.map((option, index) => (
                <button
                  key={index}
                  onClick={() => handleOptionClick(option)}
                  className="px-4 py-2 rounded-full border border-border bg-background hover:bg-muted transition-colors text-sm"
                >
                  {option}
                </button>
              ))}
            </div>
          )}

          {/* Input form */}
          {!isComplete && (
            <form onSubmit={handleSubmit} className="flex gap-2">
              <Input
                ref={inputRef}
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyDown={handleKeyPress}
                placeholder={
                  currentExpects === "time"
                    ? "e.g., 9am, 8:30, around noon..."
                    : currentExpects === "acknowledgment"
                    ? "Say hi or tap an option above..."
                    : currentExpects === "choice"
                    ? "Type or tap an option above..."
                    : "Type a message..."
                }
                disabled={isSending}
                className="flex-1"
              />
              <Button
                type="submit"
                size="icon"
                disabled={!inputValue.trim() || isSending}
              >
                {isSending ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Send className="h-4 w-4" />
                )}
              </Button>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}
