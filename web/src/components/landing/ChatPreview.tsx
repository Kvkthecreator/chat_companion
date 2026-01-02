"use client";

import { cn } from "@/lib/utils";

interface MockMessage {
  role: "user" | "character";
  content: string;
}

const PREVIEW_MESSAGES: MockMessage[] = [
  {
    role: "character",
    content: "You're not supposed to be back here.",
  },
  {
    role: "user",
    content: "Neither are you.",
  },
  {
    role: "character",
    content: "...",
  },
  {
    role: "character",
    content: "Fair point. You're not going to post about this, are you?",
  },
];

interface ChatPreviewProps {
  characterName?: string;
  characterAvatar?: string;
  className?: string;
}

export function ChatPreview({
  characterName = "Min Soo",
  characterAvatar = "M",
  className,
}: ChatPreviewProps) {
  return (
    <div
      className={cn(
        "relative overflow-hidden rounded-2xl border bg-card/50 backdrop-blur-sm shadow-xl",
        className
      )}
    >
      {/* Header */}
      <div className="flex items-center gap-3 border-b bg-card/80 px-4 py-3">
        <div className="flex h-9 w-9 items-center justify-center rounded-full bg-gradient-to-br from-pink-400 to-purple-500 text-sm font-medium text-white shadow-lg ring-2 ring-white/20">
          {characterAvatar}
        </div>
        <div>
          <p className="text-sm font-medium text-foreground">{characterName}</p>
          <p className="text-xs text-muted-foreground">typing...</p>
        </div>
      </div>

      {/* Messages */}
      <div className="flex flex-col gap-3 p-4">
        {PREVIEW_MESSAGES.map((msg, i) => (
          <div
            key={i}
            className={cn(
              "flex",
              msg.role === "user" ? "justify-end" : "justify-start"
            )}
          >
            <div
              className={cn(
                "max-w-[80%] rounded-2xl px-4 py-2.5 text-sm",
                msg.role === "user"
                  ? "rounded-tr-md bg-primary text-primary-foreground"
                  : "rounded-tl-md bg-muted text-foreground"
              )}
            >
              {msg.content}
            </div>
          </div>
        ))}

        {/* Typing indicator */}
        <div className="flex justify-start">
          <div className="rounded-2xl rounded-tl-md bg-muted px-4 py-3">
            <div className="flex items-center gap-1">
              <span
                className="h-2 w-2 animate-bounce rounded-full bg-muted-foreground/50"
                style={{ animationDelay: "0ms" }}
              />
              <span
                className="h-2 w-2 animate-bounce rounded-full bg-muted-foreground/50"
                style={{ animationDelay: "150ms" }}
              />
              <span
                className="h-2 w-2 animate-bounce rounded-full bg-muted-foreground/50"
                style={{ animationDelay: "300ms" }}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Input mock */}
      <div className="border-t bg-card/80 px-4 py-3">
        <div className="flex items-center gap-2 rounded-full border bg-background px-4 py-2 text-sm text-muted-foreground">
          <span>What do you say?</span>
          <span className="ml-auto text-xs opacity-50">Press enter</span>
        </div>
      </div>
    </div>
  );
}