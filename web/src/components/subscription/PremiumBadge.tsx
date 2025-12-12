"use client";

import { Badge } from "@/components/ui/badge";
import { Crown } from "lucide-react";
import { cn } from "@/lib/utils";

interface PremiumBadgeProps {
  className?: string;
  showIcon?: boolean;
  size?: "sm" | "default";
}

export function PremiumBadge({
  className,
  showIcon = true,
  size = "default",
}: PremiumBadgeProps) {
  return (
    <Badge
      className={cn(
        "bg-gradient-to-r from-yellow-400 to-amber-500 text-amber-950 border-0",
        size === "sm" && "text-xs px-1.5 py-0",
        className
      )}
    >
      {showIcon && (
        <Crown
          className={cn("mr-1", size === "sm" ? "h-2.5 w-2.5" : "h-3 w-3")}
        />
      )}
      Premium
    </Badge>
  );
}
