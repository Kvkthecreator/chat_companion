import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "My Characters",
};

export default function MyCharactersLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
