"use client";

import { Button, type ButtonProps } from "@/components/ui/button";
import { useSubscription } from "@/hooks/useSubscription";
import { Loader2, Sparkles } from "lucide-react";
import { cn } from "@/lib/utils";

interface UpgradeButtonProps extends Omit<ButtonProps, "onClick"> {
  showIcon?: boolean;
  children?: React.ReactNode;
}

export function UpgradeButton({
  showIcon = true,
  children,
  className,
  variant = "default",
  size = "default",
  ...props
}: UpgradeButtonProps) {
  const { isPremium, upgrade, isLoading } = useSubscription();

  // Don't render if already premium
  if (isPremium) {
    return null;
  }

  return (
    <Button
      variant={variant}
      size={size}
      className={cn(
        variant === "default" &&
          "bg-gradient-to-r from-pink-500 to-purple-500 hover:from-pink-600 hover:to-purple-600",
        className
      )}
      onClick={upgrade}
      disabled={isLoading}
      {...props}
    >
      {isLoading ? (
        <Loader2 className="h-4 w-4 animate-spin mr-2" />
      ) : showIcon ? (
        <Sparkles className="h-4 w-4 mr-2" />
      ) : null}
      {children || "Upgrade to Premium"}
    </Button>
  );
}
