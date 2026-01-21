/**
 * OG Image Configuration
 *
 * Shared constants and utilities for Open Graph image generation.
 */

// =============================================================================
// TYPES
// =============================================================================

export type OGTheme = "default" | "play" | "dark";

export interface OGThemeConfig {
  background: string;
  text: string;
  accent: string;
  muted: string;
}

// =============================================================================
// BRAND CONFIGURATION
// =============================================================================

export const BRAND = {
  name: "Chat Companion",
  shortName: "companion",
  tagline: "Your AI friend that reaches out to you",
  url: process.env.NEXT_PUBLIC_SITE_URL || "https://chat-companion-ep-0.vercel.app",
  features: ["Daily check-ins", "Remembers you", "Always there"],
};

// =============================================================================
// OG IMAGE DIMENSIONS
// =============================================================================

export const OG_SIZE = {
  width: 1200,
  height: 630,
};

// =============================================================================
// THEME CONFIGURATIONS
// =============================================================================

export const OG_THEMES: Record<OGTheme, OGThemeConfig> = {
  default: {
    background: "#09090b",
    text: "#ffffff",
    accent: "#a855f7",
    muted: "#a1a1aa",
  },
  play: {
    background: "#09090b",
    text: "#ffffff",
    accent: "#22c55e",
    muted: "#a1a1aa",
  },
  dark: {
    background: "#09090b",
    text: "#ffffff",
    accent: "#3b82f6",
    muted: "#71717a",
  },
};

// =============================================================================
// GRADIENT BACKGROUNDS
// =============================================================================

export function getGradientBackground(theme: OGTheme): string {
  const gradients: Record<OGTheme, string> = {
    default: "radial-gradient(ellipse 80% 50% at 50% -20%, rgba(168, 85, 247, 0.3), transparent)",
    play: "radial-gradient(ellipse 80% 50% at 50% -20%, rgba(34, 197, 94, 0.3), transparent)",
    dark: "radial-gradient(ellipse 80% 50% at 50% -20%, rgba(59, 130, 246, 0.3), transparent)",
  };
  return gradients[theme];
}

// =============================================================================
// METADATA HELPERS
// =============================================================================

import type { Metadata } from "next";

export function getBaseMetadata(): Metadata {
  return {
    title: {
      default: `${BRAND.name} — ${BRAND.tagline}`,
      template: `%s | ${BRAND.name}`,
    },
    description: BRAND.tagline,
    metadataBase: new URL(BRAND.url),
    openGraph: {
      title: BRAND.name,
      description: BRAND.tagline,
      url: BRAND.url,
      siteName: BRAND.name,
      locale: "en_US",
      type: "website",
    },
    twitter: {
      card: "summary_large_image",
      title: BRAND.name,
      description: BRAND.tagline,
    },
    robots: {
      index: true,
      follow: true,
    },
  };
}
