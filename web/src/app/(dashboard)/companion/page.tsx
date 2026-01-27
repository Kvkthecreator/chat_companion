"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { Skeleton } from "@/components/ui/skeleton";
import { useUser } from "@/hooks/useUser";
import {
  Sparkles,
  Clock,
  MessageCircle,
  Loader2,
  CheckCircle2,
  Bell,
} from "lucide-react";

// Timezone options
const TIMEZONES = [
  { value: "America/New_York", label: "Eastern Time (ET)" },
  { value: "America/Chicago", label: "Central Time (CT)" },
  { value: "America/Denver", label: "Mountain Time (MT)" },
  { value: "America/Los_Angeles", label: "Pacific Time (PT)" },
  { value: "America/Anchorage", label: "Alaska Time (AKT)" },
  { value: "Pacific/Honolulu", label: "Hawaii Time (HT)" },
  { value: "Europe/London", label: "London (GMT/BST)" },
  { value: "Europe/Paris", label: "Central European (CET)" },
  { value: "Europe/Berlin", label: "Berlin (CET)" },
  { value: "Asia/Tokyo", label: "Japan (JST)" },
  { value: "Asia/Seoul", label: "Korea (KST)" },
  { value: "Asia/Shanghai", label: "China (CST)" },
  { value: "Asia/Singapore", label: "Singapore (SGT)" },
  { value: "Australia/Sydney", label: "Sydney (AEST)" },
  { value: "UTC", label: "UTC" },
];

// Support style options
const SUPPORT_STYLES = [
  { value: "motivational", label: "Motivational", description: "Encouraging and energizing" },
  { value: "friendly_checkin", label: "Friendly Check-in", description: "Warm and casual, like a close friend" },
  { value: "accountability", label: "Accountability", description: "Supportive but direct about goals" },
  { value: "listener", label: "Listener", description: "Gentle and present, space to share" },
];

export default function CompanionPage() {
  const { user, updateUser, isLoading: userLoading } = useUser();

  // Form state
  const [companionName, setCompanionName] = useState("");
  const [timezone, setTimezone] = useState("America/New_York");
  const [preferredTime, setPreferredTime] = useState("09:00");
  const [timeFlexibility, setTimeFlexibility] = useState<"exact" | "around" | "window">("exact");
  const [timeWindow, setTimeWindow] = useState<"morning" | "midday" | "evening" | "night">("morning");
  const [supportStyle, setSupportStyle] = useState("friendly_checkin");
  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  // Silence detection settings
  const [allowSilenceCheckins, setAllowSilenceCheckins] = useState(true);
  const [silenceThresholdDays, setSilenceThresholdDays] = useState(3);

  // Sync form state from user data
  useEffect(() => {
    if (user) {
      setCompanionName(user.companion_name || "");
      setTimezone(user.timezone || "America/New_York");
      setPreferredTime(user.preferred_message_time || "09:00");
      setSupportStyle(user.support_style || "friendly_checkin");
      setAllowSilenceCheckins(user.allow_silence_checkins ?? true);
      setSilenceThresholdDays(user.silence_threshold_days ?? 3);
    }
  }, [user]);

  const handleSave = async () => {
    setIsSaving(true);
    setSaveSuccess(false);
    try {
      await updateUser({
        companion_name: companionName || undefined,
        timezone,
        preferred_message_time: preferredTime,
        support_style: supportStyle,
        allow_silence_checkins: allowSilenceCheckins,
        silence_threshold_days: silenceThresholdDays,
      });
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (err) {
      console.error("Failed to save:", err);
    } finally {
      setIsSaving(false);
    }
  };

  const companionDisplayName = user?.companion_name || "Your Companion";

  if (userLoading) {
    return <CompanionSkeleton />;
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6 pb-20 md:pb-0">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
          <Sparkles className="h-8 w-8 text-primary" />
          {companionDisplayName}
        </h1>
        <p className="text-muted-foreground">
          Customize how your companion communicates with you
        </p>
      </div>

      {/* Companion Settings */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <MessageCircle className="h-5 w-5 text-muted-foreground" />
            Companion Settings
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="companionName">Companion Name</Label>
            <Input
              id="companionName"
              type="text"
              placeholder="Give your companion a name"
              value={companionName}
              onChange={(e) => setCompanionName(e.target.value)}
            />
            <p className="text-xs text-muted-foreground">
              Your companion will use this name when talking to you.
            </p>
          </div>

          <div className="space-y-2">
            <Label htmlFor="supportStyle">Support Style</Label>
            <Select value={supportStyle} onValueChange={setSupportStyle}>
              <SelectTrigger id="supportStyle">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {SUPPORT_STYLES.map((style) => (
                  <SelectItem key={style.value} value={style.value}>
                    <div className="flex flex-col">
                      <span className="font-medium">{style.label}</span>
                      <span className="text-xs text-muted-foreground">{style.description}</span>
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Message Schedule */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Clock className="h-5 w-5 text-muted-foreground" />
            Message Schedule
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="timezone">Timezone</Label>
            <Select value={timezone} onValueChange={setTimezone}>
              <SelectTrigger id="timezone">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {TIMEZONES.map((tz) => (
                  <SelectItem key={tz.value} value={tz.value}>
                    {tz.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-3">
            <Label>Message Timing</Label>
            <div className="space-y-2">
              <label className="flex items-center gap-3 p-3 rounded-lg border cursor-pointer hover:bg-muted/50 transition-colors">
                <input
                  type="radio"
                  name="timeFlexibility"
                  value="exact"
                  checked={timeFlexibility === "exact"}
                  onChange={() => setTimeFlexibility("exact")}
                  className="h-4 w-4"
                />
                <div className="flex-1">
                  <p className="font-medium text-sm">At a specific time</p>
                  <p className="text-xs text-muted-foreground">Message arrives at the exact time you choose</p>
                </div>
                {timeFlexibility === "exact" && (
                  <Input
                    type="time"
                    value={preferredTime}
                    onChange={(e) => setPreferredTime(e.target.value)}
                    className="w-28"
                  />
                )}
              </label>

              <label className="flex items-center gap-3 p-3 rounded-lg border cursor-pointer hover:bg-muted/50 transition-colors">
                <input
                  type="radio"
                  name="timeFlexibility"
                  value="around"
                  checked={timeFlexibility === "around"}
                  onChange={() => setTimeFlexibility("around")}
                  className="h-4 w-4"
                />
                <div className="flex-1">
                  <p className="font-medium text-sm">Around a specific time</p>
                  <p className="text-xs text-muted-foreground">Message arrives within ~30 minutes of your preferred time</p>
                </div>
                {timeFlexibility === "around" && (
                  <Input
                    type="time"
                    value={preferredTime}
                    onChange={(e) => setPreferredTime(e.target.value)}
                    className="w-28"
                  />
                )}
              </label>

              <label className="flex items-start gap-3 p-3 rounded-lg border cursor-pointer hover:bg-muted/50 transition-colors">
                <input
                  type="radio"
                  name="timeFlexibility"
                  value="window"
                  checked={timeFlexibility === "window"}
                  onChange={() => setTimeFlexibility("window")}
                  className="h-4 w-4 mt-1"
                />
                <div className="flex-1 space-y-2">
                  <div>
                    <p className="font-medium text-sm">Sometime during a time window</p>
                    <p className="text-xs text-muted-foreground">Message arrives sometime within your chosen window</p>
                  </div>
                  {timeFlexibility === "window" && (
                    <Select value={timeWindow} onValueChange={(v) => setTimeWindow(v as typeof timeWindow)}>
                      <SelectTrigger className="w-full">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="morning">Morning (6am - 10am)</SelectItem>
                        <SelectItem value="midday">Midday (11am - 2pm)</SelectItem>
                        <SelectItem value="evening">Evening (5pm - 8pm)</SelectItem>
                        <SelectItem value="night">Night (8pm - 11pm)</SelectItem>
                      </SelectContent>
                    </Select>
                  )}
                </div>
              </label>
            </div>
          </div>

        </CardContent>
      </Card>

      {/* When to Reach Out */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Bell className="h-5 w-5 text-muted-foreground" />
            When to Reach Out
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label htmlFor="silenceCheckins">Check in when I've been quiet</Label>
              <p className="text-xs text-muted-foreground">
                {companionDisplayName} will reach out if you haven't messaged in a while
              </p>
            </div>
            <Switch
              id="silenceCheckins"
              checked={allowSilenceCheckins}
              onCheckedChange={setAllowSilenceCheckins}
            />
          </div>

          {allowSilenceCheckins && (
            <div className="space-y-2 pl-0 pt-2 border-t">
              <Label htmlFor="silenceThreshold">After how many days?</Label>
              <Select
                value={silenceThresholdDays.toString()}
                onValueChange={(v) => setSilenceThresholdDays(parseInt(v))}
              >
                <SelectTrigger id="silenceThreshold" className="w-48">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="2">2 days</SelectItem>
                  <SelectItem value="3">3 days</SelectItem>
                  <SelectItem value="5">5 days</SelectItem>
                  <SelectItem value="7">1 week</SelectItem>
                  <SelectItem value="14">2 weeks</SelectItem>
                </SelectContent>
              </Select>
              <p className="text-xs text-muted-foreground">
                A gentle check-in, no pressure to respond
              </p>
            </div>
          )}

          <div className="flex items-center gap-3 pt-2">
            <Button onClick={handleSave} disabled={isSaving}>
              {isSaving && <Loader2 className="h-4 w-4 animate-spin mr-2" />}
              Save Changes
            </Button>
            {saveSuccess && (
              <span className="text-sm text-green-500 flex items-center gap-1">
                <CheckCircle2 className="h-4 w-4" />
                Saved
              </span>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function CompanionSkeleton() {
  return (
    <div className="mx-auto max-w-3xl space-y-6 pb-20 md:pb-0">
      <div className="space-y-2">
        <Skeleton className="h-9 w-64" />
        <Skeleton className="h-5 w-48" />
      </div>
      <Skeleton className="h-40 rounded-xl" />
      <Skeleton className="h-64 rounded-xl" />
      <Skeleton className="h-40 rounded-xl" />
    </div>
  );
}
