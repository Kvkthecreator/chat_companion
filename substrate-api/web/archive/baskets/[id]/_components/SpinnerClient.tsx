"use client";

import dynamic from "next/dynamic";

const YarnSpinner = dynamic(
  () => import("@/components/ui/OrganicSpinner"),
  {
    ssr: false,
    loading: () => (
      <div className="h-10 w-10 animate-pulse rounded-full bg-muted" />
    ),
  }
);

export default function SpinnerClient({
  size = "md",
}: { size?: "sm" | "md" | "lg" | "xl" }) {
  return (
    <div className="absolute inset-0 flex items-center justify-center">
      {/* OrganicSpinner sets role="status" and aria-busy */}
      {/* @ts-ignore size is a runtime prop on lazy component */}
      <YarnSpinner size={size} />
    </div>
  );
}
