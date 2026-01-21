"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { createClient } from "@/lib/supabase/client";
import { api } from "@/lib/api/client";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { BackgroundBlob } from "@/components/ui/background-blob";
import { Progress } from "@/components/ui/progress";

// Onboarding steps
const STEPS = [
  "welcome",
  "name",
  "companion_name",
  "timezone",
  "time",
  "style",
  "channel",
  "complete",
] as const;

type Step = (typeof STEPS)[number];

// Support styles
const SUPPORT_STYLES = [
  {
    id: "motivational",
    name: "Motivational Coach",
    description: "Encouraging and energizing - focuses on goals and positive momentum",
    emoji: "🚀",
  },
  {
    id: "friendly_checkin",
    name: "Friendly Check-in",
    description: "Warm and casual like a close friend - focuses on how you're feeling",
    emoji: "☕",
  },
  {
    id: "accountability",
    name: "Accountability Partner",
    description: "Supportive but direct - focuses on progress and commitments",
    emoji: "📋",
  },
  {
    id: "listener",
    name: "Gentle Listener",
    description: "Calm and present - creates space to share and validates feelings",
    emoji: "🌱",
  },
];

// Common timezones
const TIMEZONES = [
  { value: "America/New_York", label: "Eastern Time (New York)" },
  { value: "America/Chicago", label: "Central Time (Chicago)" },
  { value: "America/Denver", label: "Mountain Time (Denver)" },
  { value: "America/Los_Angeles", label: "Pacific Time (Los Angeles)" },
  { value: "America/Anchorage", label: "Alaska Time" },
  { value: "Pacific/Honolulu", label: "Hawaii Time" },
  { value: "Europe/London", label: "London (GMT/BST)" },
  { value: "Europe/Paris", label: "Paris (CET/CEST)" },
  { value: "Europe/Berlin", label: "Berlin (CET/CEST)" },
  { value: "Asia/Tokyo", label: "Tokyo (JST)" },
  { value: "Asia/Shanghai", label: "Shanghai (CST)" },
  { value: "Asia/Singapore", label: "Singapore (SGT)" },
  { value: "Australia/Sydney", label: "Sydney (AEST/AEDT)" },
  { value: "UTC", label: "UTC" },
];

// Message times
const MESSAGE_TIMES = [
  { value: "06:00", label: "6:00 AM - Early Bird" },
  { value: "07:00", label: "7:00 AM" },
  { value: "08:00", label: "8:00 AM" },
  { value: "09:00", label: "9:00 AM - Most Popular" },
  { value: "10:00", label: "10:00 AM" },
  { value: "11:00", label: "11:00 AM" },
  { value: "12:00", label: "12:00 PM - Noon" },
  { value: "18:00", label: "6:00 PM - Evening" },
  { value: "20:00", label: "8:00 PM" },
  { value: "21:00", label: "9:00 PM - Night Owl" },
];

export default function OnboardingPage() {
  const router = useRouter();
  const supabase = createClient();

  const [currentStep, setCurrentStep] = useState<Step>("welcome");
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Form data
  const [displayName, setDisplayName] = useState("");
  const [companionName, setCompanionName] = useState("");
  const [timezone, setTimezone] = useState("America/New_York");
  const [messageTime, setMessageTime] = useState("09:00");
  const [supportStyle, setSupportStyle] = useState("friendly_checkin");
  const [telegramLinked, setTelegramLinked] = useState(false);
  const [telegramDeepLink, setTelegramDeepLink] = useState<string | null>(null);

  // Check auth and load existing onboarding state
  useEffect(() => {
    const init = async () => {
      const {
        data: { user },
      } = await supabase.auth.getUser();

      if (!user) {
        router.push("/login?next=/onboarding");
        return;
      }

      try {
        // Check if user has completed onboarding
        const userData = await api.users.me();
        if (userData.onboarding_completed_at) {
          router.push("/dashboard");
          return;
        }

        // Pre-fill display name from auth provider
        if (user.user_metadata?.full_name) {
          setDisplayName(user.user_metadata.full_name);
        }

        // Try to detect timezone
        const detectedTimezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
        if (TIMEZONES.some((tz) => tz.value === detectedTimezone)) {
          setTimezone(detectedTimezone);
        }

        // Load existing onboarding state if any
        try {
          const onboardingState = await api.onboarding.get();
          if (onboardingState.current_step) {
            setCurrentStep(onboardingState.current_step as Step);
          }
          if (onboardingState.data) {
            if (onboardingState.data.display_name) setDisplayName(onboardingState.data.display_name as string);
            if (onboardingState.data.companion_name) setCompanionName(onboardingState.data.companion_name as string);
            if (onboardingState.data.timezone) setTimezone(onboardingState.data.timezone as string);
            if (onboardingState.data.message_time) setMessageTime(onboardingState.data.message_time as string);
            if (onboardingState.data.support_style) setSupportStyle(onboardingState.data.support_style as string);
          }
        } catch {
          // No existing onboarding state, that's fine
        }

        setIsLoading(false);
      } catch (err) {
        console.error("Failed to init onboarding:", err);
        setError("Failed to load. Please refresh the page.");
        setIsLoading(false);
      }
    };

    init();
  }, [router, supabase]);

  // Progress calculation
  const stepIndex = STEPS.indexOf(currentStep);
  const progress = Math.round((stepIndex / (STEPS.length - 1)) * 100);

  // Navigation
  const goToStep = async (step: Step) => {
    setCurrentStep(step);
    try {
      await api.onboarding.update({ step });
    } catch (err) {
      console.error("Failed to save step:", err);
    }
  };

  const nextStep = () => {
    const currentIndex = STEPS.indexOf(currentStep);
    if (currentIndex < STEPS.length - 1) {
      goToStep(STEPS[currentIndex + 1]);
    }
  };

  const prevStep = () => {
    const currentIndex = STEPS.indexOf(currentStep);
    if (currentIndex > 0) {
      goToStep(STEPS[currentIndex - 1]);
    }
  };

  // Save step data
  const saveStepData = async (data: Record<string, unknown>) => {
    setIsSaving(true);
    try {
      await api.onboarding.update({ data });
    } catch (err) {
      console.error("Failed to save data:", err);
    }
    setIsSaving(false);
  };

  // Complete onboarding
  const completeOnboarding = async () => {
    setIsSaving(true);
    setError(null);
    try {
      // Save all data to user profile
      await api.users.update({
        display_name: displayName,
        companion_name: companionName,
        timezone,
        preferred_message_time: messageTime,
        support_style: supportStyle,
      });

      // Mark onboarding as complete
      await api.onboarding.complete();

      // Redirect to dashboard
      router.push("/dashboard");
    } catch (err) {
      console.error("Failed to complete onboarding:", err);
      setError("Failed to complete setup. Please try again.");
      setIsSaving(false);
    }
  };

  // Get Telegram deep link
  const getTelegramDeepLink = async () => {
    try {
      const result = await api.telegram.getDeepLink();
      setTelegramDeepLink(result.deep_link_url);
    } catch (err) {
      console.error("Failed to get Telegram link:", err);
    }
  };

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="text-muted-foreground">Loading...</div>
      </div>
    );
  }

  return (
    <div className="relative min-h-screen bg-background text-foreground">
      <BackgroundBlob className="mx-auto max-w-5xl" />
      <div className="relative mx-auto flex min-h-screen max-w-2xl flex-col px-6 py-8">
        {/* Progress bar */}
        {currentStep !== "welcome" && currentStep !== "complete" && (
          <div className="mb-8">
            <Progress value={progress} className="h-2" />
            <div className="mt-2 text-center text-sm text-muted-foreground">
              Step {stepIndex} of {STEPS.length - 2}
            </div>
          </div>
        )}

        {/* Step content */}
        <div className="flex flex-1 items-center justify-center">
          <Card className="w-full max-w-md border border-border/70 shadow-sm">
            <CardContent className="p-8">
              {error && (
                <div className="mb-4 rounded-lg border border-destructive/30 bg-destructive/10 px-3 py-2 text-sm text-destructive">
                  {error}
                </div>
              )}

              {/* Welcome */}
              {currentStep === "welcome" && (
                <div className="space-y-6 text-center">
                  <div className="text-5xl">👋</div>
                  <div>
                    <h1 className="text-2xl font-semibold">Welcome to Chat Companion</h1>
                    <p className="mt-2 text-muted-foreground">
                      Your AI friend that reaches out to you daily.
                    </p>
                  </div>
                  <div className="space-y-2 text-left text-sm text-muted-foreground">
                    <p>✨ Receive personalized daily check-ins</p>
                    <p>💭 Chat when you need someone to talk to</p>
                    <p>🧠 Your companion remembers your conversations</p>
                  </div>
                  <Button onClick={nextStep} className="w-full">
                    Get Started
                  </Button>
                </div>
              )}

              {/* Name */}
              {currentStep === "name" && (
                <div className="space-y-6">
                  <div className="text-center">
                    <h2 className="text-xl font-semibold">What should I call you?</h2>
                    <p className="mt-1 text-sm text-muted-foreground">
                      Your companion will use this name when talking to you.
                    </p>
                  </div>
                  <Input
                    value={displayName}
                    onChange={(e) => setDisplayName(e.target.value)}
                    placeholder="Enter your name"
                    className="text-center text-lg"
                  />
                  <div className="flex gap-3">
                    <Button variant="outline" onClick={prevStep} className="flex-1">
                      Back
                    </Button>
                    <Button
                      onClick={() => {
                        saveStepData({ display_name: displayName });
                        nextStep();
                      }}
                      disabled={!displayName.trim()}
                      className="flex-1"
                    >
                      Continue
                    </Button>
                  </div>
                </div>
              )}

              {/* Companion Name */}
              {currentStep === "companion_name" && (
                <div className="space-y-6">
                  <div className="text-center">
                    <h2 className="text-xl font-semibold">Name your companion</h2>
                    <p className="mt-1 text-sm text-muted-foreground">
                      Give your AI companion a name. Make it personal!
                    </p>
                  </div>
                  <Input
                    value={companionName}
                    onChange={(e) => setCompanionName(e.target.value)}
                    placeholder="e.g., Luna, Max, Sage, Echo..."
                    className="text-center text-lg"
                  />
                  <div className="flex gap-3">
                    <Button variant="outline" onClick={prevStep} className="flex-1">
                      Back
                    </Button>
                    <Button
                      onClick={() => {
                        saveStepData({ companion_name: companionName });
                        nextStep();
                      }}
                      disabled={!companionName.trim()}
                      className="flex-1"
                    >
                      Continue
                    </Button>
                  </div>
                </div>
              )}

              {/* Timezone */}
              {currentStep === "timezone" && (
                <div className="space-y-6">
                  <div className="text-center">
                    <h2 className="text-xl font-semibold">Where are you located?</h2>
                    <p className="mt-1 text-sm text-muted-foreground">
                      This helps {companionName || "your companion"} message you at the right time.
                    </p>
                  </div>
                  <select
                    value={timezone}
                    onChange={(e) => setTimezone(e.target.value)}
                    className="w-full rounded-lg border border-border bg-background px-4 py-3 text-foreground"
                  >
                    {TIMEZONES.map((tz) => (
                      <option key={tz.value} value={tz.value}>
                        {tz.label}
                      </option>
                    ))}
                  </select>
                  <div className="flex gap-3">
                    <Button variant="outline" onClick={prevStep} className="flex-1">
                      Back
                    </Button>
                    <Button
                      onClick={() => {
                        saveStepData({ timezone });
                        nextStep();
                      }}
                      className="flex-1"
                    >
                      Continue
                    </Button>
                  </div>
                </div>
              )}

              {/* Message Time */}
              {currentStep === "time" && (
                <div className="space-y-6">
                  <div className="text-center">
                    <h2 className="text-xl font-semibold">When should I check in?</h2>
                    <p className="mt-1 text-sm text-muted-foreground">
                      {companionName || "Your companion"} will send you a message at this time each day.
                    </p>
                  </div>
                  <div className="grid grid-cols-2 gap-2">
                    {MESSAGE_TIMES.map((time) => (
                      <button
                        key={time.value}
                        onClick={() => setMessageTime(time.value)}
                        className={`rounded-lg border px-3 py-3 text-sm transition-colors ${
                          messageTime === time.value
                            ? "border-primary bg-primary/10 text-primary"
                            : "border-border hover:border-primary/50"
                        }`}
                      >
                        {time.label}
                      </button>
                    ))}
                  </div>
                  <div className="flex gap-3">
                    <Button variant="outline" onClick={prevStep} className="flex-1">
                      Back
                    </Button>
                    <Button
                      onClick={() => {
                        saveStepData({ message_time: messageTime });
                        nextStep();
                      }}
                      className="flex-1"
                    >
                      Continue
                    </Button>
                  </div>
                </div>
              )}

              {/* Support Style */}
              {currentStep === "style" && (
                <div className="space-y-6">
                  <div className="text-center">
                    <h2 className="text-xl font-semibold">How should {companionName || "I"} support you?</h2>
                    <p className="mt-1 text-sm text-muted-foreground">
                      Choose the style that feels right for you.
                    </p>
                  </div>
                  <div className="space-y-3">
                    {SUPPORT_STYLES.map((style) => (
                      <button
                        key={style.id}
                        onClick={() => setSupportStyle(style.id)}
                        className={`w-full rounded-lg border p-4 text-left transition-colors ${
                          supportStyle === style.id
                            ? "border-primary bg-primary/10"
                            : "border-border hover:border-primary/50"
                        }`}
                      >
                        <div className="flex items-center gap-3">
                          <span className="text-2xl">{style.emoji}</span>
                          <div>
                            <div className="font-medium">{style.name}</div>
                            <div className="text-sm text-muted-foreground">{style.description}</div>
                          </div>
                        </div>
                      </button>
                    ))}
                  </div>
                  <div className="flex gap-3">
                    <Button variant="outline" onClick={prevStep} className="flex-1">
                      Back
                    </Button>
                    <Button
                      onClick={() => {
                        saveStepData({ support_style: supportStyle });
                        nextStep();
                      }}
                      className="flex-1"
                    >
                      Continue
                    </Button>
                  </div>
                </div>
              )}

              {/* Channel Selection */}
              {currentStep === "channel" && (
                <div className="space-y-6">
                  <div className="text-center">
                    <h2 className="text-xl font-semibold">How do you want to chat?</h2>
                    <p className="mt-1 text-sm text-muted-foreground">
                      Connect Telegram for messages, or use web chat.
                    </p>
                  </div>

                  {/* Telegram Option */}
                  <div className="rounded-lg border border-border p-4">
                    <div className="flex items-center gap-3">
                      <span className="text-2xl">📱</span>
                      <div className="flex-1">
                        <div className="font-medium">Telegram</div>
                        <div className="text-sm text-muted-foreground">
                          Get messages directly in Telegram
                        </div>
                      </div>
                      {telegramLinked ? (
                        <span className="text-sm text-green-600">Connected</span>
                      ) : telegramDeepLink ? (
                        <a
                          href={telegramDeepLink}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="rounded-lg bg-[#0088cc] px-4 py-2 text-sm font-medium text-white hover:bg-[#0088cc]/90"
                        >
                          Connect
                        </a>
                      ) : (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={getTelegramDeepLink}
                        >
                          Get Link
                        </Button>
                      )}
                    </div>
                  </div>

                  {/* Web Chat Option */}
                  <div className="rounded-lg border border-border p-4">
                    <div className="flex items-center gap-3">
                      <span className="text-2xl">💬</span>
                      <div className="flex-1">
                        <div className="font-medium">Web Chat</div>
                        <div className="text-sm text-muted-foreground">
                          Chat right here on the website
                        </div>
                      </div>
                      <span className="text-sm text-green-600">Always available</span>
                    </div>
                  </div>

                  <p className="text-center text-xs text-muted-foreground">
                    You can connect more channels later in settings.
                  </p>

                  <div className="flex gap-3">
                    <Button variant="outline" onClick={prevStep} className="flex-1">
                      Back
                    </Button>
                    <Button onClick={nextStep} className="flex-1">
                      Continue
                    </Button>
                  </div>
                </div>
              )}

              {/* Complete */}
              {currentStep === "complete" && (
                <div className="space-y-6 text-center">
                  <div className="text-5xl">🎉</div>
                  <div>
                    <h2 className="text-xl font-semibold">You're all set, {displayName}!</h2>
                    <p className="mt-2 text-muted-foreground">
                      {companionName} will reach out to you daily at{" "}
                      {MESSAGE_TIMES.find((t) => t.value === messageTime)?.label.split(" - ")[0] || messageTime}.
                    </p>
                  </div>
                  <div className="rounded-lg bg-muted p-4 text-sm text-muted-foreground">
                    <p>
                      <strong className="text-foreground">{companionName}</strong> is ready to be your{" "}
                      {SUPPORT_STYLES.find((s) => s.id === supportStyle)?.name.toLowerCase() || "companion"}.
                    </p>
                  </div>
                  <Button
                    onClick={completeOnboarding}
                    disabled={isSaving}
                    className="w-full"
                  >
                    {isSaving ? "Setting up..." : "Start Chatting"}
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
