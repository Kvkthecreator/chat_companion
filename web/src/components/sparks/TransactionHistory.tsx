"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api/client";
import type { SparkTransaction } from "@/types";
import { Sparkles, TrendingUp, TrendingDown, Gift, CreditCard, RefreshCw, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

const TRANSACTION_ICONS: Record<string, typeof Sparkles> = {
  subscription_grant: Gift,
  topup_purchase: CreditCard,
  generation_spend: TrendingDown,
  refund: RefreshCw,
  bonus: Gift,
  admin_adjustment: Sparkles,
};

const TRANSACTION_LABELS: Record<string, string> = {
  subscription_grant: "Subscription Sparks",
  topup_purchase: "Spark Pack Purchase",
  generation_spend: "Image Generation",
  refund: "Refund",
  bonus: "Bonus",
  admin_adjustment: "Adjustment",
  expiry: "Expired",
};

export function TransactionHistory() {
  const [transactions, setTransactions] = useState<SparkTransaction[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    async function fetchHistory() {
      try {
        const data = await api.credits.getHistory(20, 0);
        setTransactions(data.transactions);
      } catch (err) {
        setError(err as Error);
      } finally {
        setIsLoading(false);
      }
    }
    fetchHistory();
  }, []);

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
      hour: "numeric",
      minute: "2-digit",
    });
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-8">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-8 text-muted-foreground">
        Failed to load transaction history
      </div>
    );
  }

  if (transactions.length === 0) {
    return (
      <div className="text-center py-8 text-muted-foreground">
        <Sparkles className="h-8 w-8 mx-auto mb-2 opacity-50" />
        <p>No transactions yet</p>
        <p className="text-sm">Your spark activity will appear here</p>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {transactions.map((tx) => {
        const Icon = TRANSACTION_ICONS[tx.transaction_type] || Sparkles;
        const label = TRANSACTION_LABELS[tx.transaction_type] || tx.transaction_type;
        const isPositive = tx.amount > 0;

        return (
          <div
            key={tx.id}
            className="flex items-center justify-between p-3 rounded-lg bg-muted/50 hover:bg-muted/70 transition-colors"
          >
            <div className="flex items-center gap-3">
              <div className={cn(
                "p-2 rounded-full",
                isPositive ? "bg-green-500/10" : "bg-red-500/10"
              )}>
                <Icon className={cn(
                  "h-4 w-4",
                  isPositive ? "text-green-500" : "text-red-400"
                )} />
              </div>
              <div>
                <p className="font-medium text-sm">{tx.description || label}</p>
                <p className="text-xs text-muted-foreground">{formatDate(tx.created_at)}</p>
              </div>
            </div>
            <div className="text-right">
              <p className={cn(
                "font-semibold",
                isPositive ? "text-green-500" : "text-red-400"
              )}>
                {isPositive ? "+" : ""}{tx.amount} Sparks
              </p>
              <p className="text-xs text-muted-foreground">
                Balance: {tx.balance_after}
              </p>
            </div>
          </div>
        );
      })}
    </div>
  );
}
