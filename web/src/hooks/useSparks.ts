"use client";

import { useUsage } from "./useUsage";

/**
 * Hook for spark balance (simplified wrapper around useUsage)
 */
export function useSparks() {
  const { fluxRemaining, isLowFlux, isOutOfFlux, isLoading } = useUsage();

  return {
    sparkBalance: fluxRemaining,
    isLow: isLowFlux,
    isEmpty: isOutOfFlux,
    isLoading,
  };
}
