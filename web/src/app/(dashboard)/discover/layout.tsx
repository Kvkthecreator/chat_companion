import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Discover",
};

export default function DiscoverLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
