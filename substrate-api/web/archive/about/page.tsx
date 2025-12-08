"use client";

import React from 'react';
import Head from 'next/head';
import Link from 'next/link';
import LandingHeader from '@/components/landing/LandingHeader';
import LandingFooter from '@/components/landing/LandingFooter';
import SystemPillarsSection from '@/components/landing/SystemPillarsSection';
import SystemCapabilitiesSection from '@/components/landing/SystemCapabilitiesSection';

export default function AboutPage() {
  return (
    <>
      <Head>
        <title>About yarnnn — A Memory That Defends</title>
        <meta name="description" content="Learn how yarnnn's unique lock in mechanism and narrative-first design help you achieve contextual integrity in your work with AI." />
        <meta name="keywords" content="yarnnn, about yarnnn, context OS, memory OS, indie builder tools, creative tools" />
        <meta property="og:title" content="About yarnnn — memory OS for indie builders" />
        <meta property="og:description" content="Learn how yarnnn helps you preserve clarity in your evolving ideas and memory." />
        <meta property="og:type" content="website" />
        <meta property="og:url" content="https://yarnnn.com/about" />
        <meta property="og:image" content="https://yarnnn.com/og-image.png" />
      </Head>
      <LandingHeader />
      <main>
        <section className="w-full max-w-[1200px] mx-auto px-4 py-[120px] space-y-6">
          <h1 className="text-foreground text-4xl md:text-6xl font-bold tracking-tight leading-tight text-left">
            A memory that defends, not just remembers.
          </h1>
          <p className="text-lg leading-relaxed max-w-2xl">
            In the age of AI, our greatest challenge isn't generating ideas—it's maintaining clarity. LLM chats quickly become a sea of repetition and contradiction. You're forced to become a context janitor, constantly reminding the AI of what you've already decided.
          </p>
          <p className="text-lg leading-relaxed max-w-2xl">
            yarnnn ends that cycle. It’s an opinionated memory system built on a simple principle: <strong>your context should be defended.</strong> By allowing you to <strong>Lock In</strong> core decisions as canonical truth, Yarnnn gives you the power to evolve your ideas with confidence and integrity.
          </p>
        </section>
        <SystemPillarsSection />
        <SystemCapabilitiesSection />
        <footer className="px-4 py-12 text-center text-sm text-muted-foreground">
          Our mission: to empower thinkers with a tool that defends contextual integrity, turning chaotic conversations into a reliable source of truth.
        </footer>
      </main>
      <LandingFooter />
    </>
  );
}
