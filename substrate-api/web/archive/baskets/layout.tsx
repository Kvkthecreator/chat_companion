"use client";

interface LayoutProps {
  children: React.ReactNode;
}

export default function BasketsLayout({ children }: LayoutProps) {
  return <div className="max-w-5xl mx-auto px-6 py-8 w-full">{children}</div>;
}
