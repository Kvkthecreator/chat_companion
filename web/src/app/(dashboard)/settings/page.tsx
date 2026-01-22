"use client";

import { useEffect, useState } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { SubscriptionCard } from "@/components/subscription";
import { useUser } from "@/hooks/useUser";
import { createClient } from "@/lib/supabase/client";
import { api } from "@/lib/api/client";
import {
  CheckCircle2,
  CreditCard,
  User,
  Mail,
  Clock,
  Loader2,
  Settings2,
  AlertCircle,
  HelpCircle,
  ExternalLink,
  Trash2,
  Bell,
  MessageCircle,
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

export default function SettingsPage() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const { user, reload, updateUser, isLoading: userLoading } = useUser();
  const [showSuccess, setShowSuccess] = useState(false);
  const [email, setEmail] = useState<string | null>(null);
  const [displayName, setDisplayName] = useState("");
  const [companionName, setCompanionName] = useState("");
  const [timezone, setTimezone] = useState("America/New_York");
  const [preferredTime, setPreferredTime] = useState("09:00");
  const [supportStyle, setSupportStyle] = useState("friendly_checkin");
  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  // Delete account state
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [deleteConfirmation, setDeleteConfirmation] = useState("");
  const [deleteReason, setDeleteReason] = useState("");
  const [isDeleting, setIsDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  // Get email from Supabase auth
  useEffect(() => {
    async function getEmail() {
      const supabase = createClient();
      const { data: { user: authUser } } = await supabase.auth.getUser();
      setEmail(authUser?.email || null);
    }
    getEmail();
  }, []);

  // Sync form state from user data
  useEffect(() => {
    if (user) {
      setDisplayName(user.display_name || "");
      setCompanionName(user.companion_name || "");
      setTimezone(user.timezone || "America/New_York");
      setPreferredTime(user.preferred_message_time || "09:00");
      setSupportStyle(user.support_style || "friendly_checkin");
    }
  }, [user]);

  const handleSaveProfile = async () => {
    setIsSaving(true);
    setSaveSuccess(false);
    try {
      await updateUser({
        display_name: displayName || undefined,
        companion_name: companionName || undefined,
      });
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (err) {
      console.error("Failed to save profile:", err);
    } finally {
      setIsSaving(false);
    }
  };

  const handleSavePreferences = async () => {
    setIsSaving(true);
    setSaveSuccess(false);
    try {
      await updateUser({
        timezone,
        preferred_message_time: preferredTime,
        support_style: supportStyle,
      });
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (err) {
      console.error("Failed to save preferences:", err);
    } finally {
      setIsSaving(false);
    }
  };

  const handleDeleteAccount = async () => {
    if (deleteConfirmation !== "DELETE") {
      setDeleteError("Please type DELETE to confirm");
      return;
    }

    setIsDeleting(true);
    setDeleteError(null);

    try {
      await api.users.deleteAccount("DELETE", deleteReason || undefined);
      const supabase = createClient();
      await supabase.auth.signOut();
      router.push("/");
    } catch (err) {
      console.error("Failed to delete account:", err);
      setDeleteError("Failed to delete account. Please try again or contact support.");
      setIsDeleting(false);
    }
  };

  // Tab management
  const urlTab = searchParams.get("tab");
  const initialTab = urlTab || "preferences";
  const [activeTab, setActiveTab] = useState(initialTab);

  useEffect(() => {
    const tab = searchParams.get("tab");
    if (tab && tab !== activeTab) {
      setActiveTab(tab);
    }
  }, [searchParams, activeTab]);

  const handleTabChange = (value: string) => {
    setActiveTab(value);
    router.replace(`/settings?tab=${value}`, { scroll: false });
  };

  // Handle success redirect from Lemon Squeezy
  useEffect(() => {
    const subscription = searchParams.get("subscription");
    if (subscription === "success") {
      setShowSuccess(true);
      reload();
      window.history.replaceState({}, "", "/settings?tab=billing");
      const timer = setTimeout(() => setShowSuccess(false), 5000);
      return () => clearTimeout(timer);
    }
  }, [searchParams, reload]);

  return (
    <div className="space-y-8 pb-20 md:pb-0">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Settings</h1>
        <p className="text-muted-foreground">Manage your companion and account</p>
      </div>

      {/* Success Banner */}
      {showSuccess && (
        <Card className="border-green-500/50 bg-green-500/10">
          <CardContent className="p-4 flex items-center gap-3">
            <CheckCircle2 className="h-5 w-5 text-green-500 shrink-0" />
            <div>
              <p className="font-medium text-green-700 dark:text-green-400">
                Welcome to Premium!
              </p>
              <p className="text-sm text-green-600 dark:text-green-500">
                Your subscription is now active.
              </p>
            </div>
          </CardContent>
        </Card>
      )}

      <Tabs value={activeTab} onValueChange={handleTabChange}>
        <TabsList className="grid w-full grid-cols-4 max-w-lg">
          <TabsTrigger value="preferences" className="gap-2">
            <Settings2 className="h-4 w-4" />
            Preferences
          </TabsTrigger>
          <TabsTrigger value="notifications" className="gap-2">
            <Bell className="h-4 w-4" />
            Channels
          </TabsTrigger>
          <TabsTrigger value="billing" className="gap-2">
            <CreditCard className="h-4 w-4" />
            Billing
          </TabsTrigger>
          <TabsTrigger value="account" className="gap-2">
            <User className="h-4 w-4" />
            Account
          </TabsTrigger>
        </TabsList>

        {/* Preferences Tab */}
        <TabsContent value="preferences" className="space-y-6">
          {/* Companion Settings */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <MessageCircle className="h-5 w-5 text-muted-foreground" />
                Companion Settings
              </CardTitle>
              <CardDescription>
                Personalize your companion experience
              </CardDescription>
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
              <CardDescription>
                When should your companion reach out?
              </CardDescription>
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

              <div className="space-y-2">
                <Label htmlFor="preferredTime">Preferred Message Time</Label>
                <Input
                  id="preferredTime"
                  type="time"
                  value={preferredTime}
                  onChange={(e) => setPreferredTime(e.target.value)}
                />
                <p className="text-xs text-muted-foreground">
                  Your companion will send a daily message around this time.
                </p>
              </div>

              <div className="flex items-center gap-3">
                <Button onClick={handleSavePreferences} disabled={isSaving}>
                  {isSaving && <Loader2 className="h-4 w-4 animate-spin mr-2" />}
                  Save Preferences
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
        </TabsContent>

        {/* Notifications/Channels Tab */}
        <TabsContent value="notifications" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Bell className="h-5 w-5 text-muted-foreground" />
                Message Channels
              </CardTitle>
              <CardDescription>
                How do you want to receive messages from your companion?
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Telegram */}
              <div className="flex items-center justify-between p-4 rounded-lg border">
                <div className="flex items-center gap-3">
                  <div className="h-10 w-10 rounded-full bg-blue-500 flex items-center justify-center">
                    <svg className="h-5 w-5 text-white" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm4.64 6.8c-.15 1.58-.8 5.42-1.13 7.19-.14.75-.42 1-.68 1.03-.58.05-1.02-.38-1.58-.75-.88-.58-1.38-.94-2.23-1.5-.99-.65-.35-1.01.22-1.59.15-.15 2.71-2.48 2.76-2.69a.2.2 0 00-.05-.18c-.06-.05-.14-.03-.21-.02-.09.02-1.49.95-4.22 2.79-.4.27-.76.41-1.08.4-.36-.01-1.04-.2-1.55-.37-.63-.2-1.12-.31-1.08-.66.02-.18.27-.36.74-.55 2.92-1.27 4.86-2.11 5.83-2.51 2.78-1.16 3.35-1.36 3.73-1.36.08 0 .27.02.39.12.1.08.13.19.14.27-.01.06.01.24 0 .38z"/>
                    </svg>
                  </div>
                  <div>
                    <p className="font-medium">Telegram</p>
                    <p className="text-sm text-muted-foreground">Primary messaging channel</p>
                  </div>
                </div>
                <Button variant="outline">
                  Connect
                </Button>
              </div>

              {/* Web Chat */}
              <div className="flex items-center justify-between p-4 rounded-lg border">
                <div className="flex items-center gap-3">
                  <div className="h-10 w-10 rounded-full bg-primary flex items-center justify-center">
                    <MessageCircle className="h-5 w-5 text-primary-foreground" />
                  </div>
                  <div>
                    <p className="font-medium">Web Chat</p>
                    <p className="text-sm text-muted-foreground">Chat directly on the website</p>
                  </div>
                </div>
                <span className="text-sm text-green-500 flex items-center gap-1">
                  <CheckCircle2 className="h-4 w-4" />
                  Available
                </span>
              </div>

              {/* WhatsApp (Coming Soon) */}
              <div className="flex items-center justify-between p-4 rounded-lg border opacity-50">
                <div className="flex items-center gap-3">
                  <div className="h-10 w-10 rounded-full bg-green-500 flex items-center justify-center">
                    <svg className="h-5 w-5 text-white" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/>
                    </svg>
                  </div>
                  <div>
                    <p className="font-medium">WhatsApp</p>
                    <p className="text-sm text-muted-foreground">Coming soon</p>
                  </div>
                </div>
                <span className="text-sm text-muted-foreground">Coming Soon</span>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Billing Tab */}
        <TabsContent value="billing" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Your Plan</CardTitle>
              <CardDescription>
                Manage your subscription
              </CardDescription>
            </CardHeader>
            <CardContent>
              <SubscriptionCard />
            </CardContent>
          </Card>
        </TabsContent>

        {/* Account Tab */}
        <TabsContent value="account" className="space-y-6">
          {/* Profile Settings */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <User className="h-5 w-5 text-muted-foreground" />
                Profile
              </CardTitle>
              <CardDescription>
                Your account information
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="email" className="flex items-center gap-2">
                  <Mail className="h-4 w-4 text-muted-foreground" />
                  Email
                </Label>
                <Input
                  id="email"
                  type="email"
                  value={email || ""}
                  disabled
                  className="bg-muted"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="displayName">Display Name</Label>
                <Input
                  id="displayName"
                  type="text"
                  placeholder="Enter your display name"
                  value={displayName}
                  onChange={(e) => setDisplayName(e.target.value)}
                />
              </div>

              <div className="flex items-center gap-3">
                <Button onClick={handleSaveProfile} disabled={isSaving}>
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

          {/* Danger Zone */}
          <Card className="border-red-500/30">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-red-600 dark:text-red-400">
                <AlertCircle className="h-5 w-5" />
                Danger Zone
              </CardTitle>
              <CardDescription>
                Irreversible actions
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="rounded-lg border border-red-500/30 bg-red-500/5 p-4">
                <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                  <div className="space-y-1">
                    <p className="font-medium text-red-700 dark:text-red-400">
                      Delete Account
                    </p>
                    <p className="text-sm text-muted-foreground">
                      Permanently delete your account and all data.
                    </p>
                  </div>
                  <Button
                    variant="destructive"
                    onClick={() => setShowDeleteModal(true)}
                    className="shrink-0"
                  >
                    <Trash2 className="h-4 w-4 mr-2" />
                    Delete Account
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Delete Account Modal */}
      <Dialog open={showDeleteModal} onOpenChange={setShowDeleteModal}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-red-600 dark:text-red-400">
              <AlertCircle className="h-5 w-5" />
              Delete Account
            </DialogTitle>
            <DialogDescription>
              This action is permanent and cannot be undone.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-4">
            <div className="rounded-lg bg-red-500/10 border border-red-500/20 p-4 text-sm space-y-2">
              <p className="font-medium text-red-700 dark:text-red-400">
                This will permanently delete:
              </p>
              <ul className="list-disc list-inside text-red-600 dark:text-red-500 space-y-1">
                <li>Your account and profile</li>
                <li>All chat history and messages</li>
                <li>All memories and context</li>
                <li>Your subscription (will be cancelled)</li>
              </ul>
            </div>

            <div className="space-y-2">
              <Label htmlFor="delete-reason" className="text-muted-foreground">
                Why are you leaving? (optional)
              </Label>
              <Select value={deleteReason} onValueChange={setDeleteReason}>
                <SelectTrigger id="delete-reason">
                  <SelectValue placeholder="Select a reason..." />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="not_using">Not using the app anymore</SelectItem>
                  <SelectItem value="found_alternative">Found an alternative</SelectItem>
                  <SelectItem value="privacy">Privacy concerns</SelectItem>
                  <SelectItem value="too_expensive">Too expensive</SelectItem>
                  <SelectItem value="not_satisfied">Not satisfied</SelectItem>
                  <SelectItem value="other">Other</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="delete-confirmation">
                Type <span className="font-mono font-bold text-red-600">DELETE</span> to confirm
              </Label>
              <Input
                id="delete-confirmation"
                type="text"
                placeholder="Type DELETE"
                value={deleteConfirmation}
                onChange={(e) => setDeleteConfirmation(e.target.value)}
                className="font-mono"
              />
            </div>

            {deleteError && (
              <p className="text-sm text-red-600 dark:text-red-400">{deleteError}</p>
            )}
          </div>

          <DialogFooter className="gap-2 sm:gap-0">
            <Button
              variant="outline"
              onClick={() => {
                setShowDeleteModal(false);
                setDeleteConfirmation("");
                setDeleteReason("");
                setDeleteError(null);
              }}
              disabled={isDeleting}
            >
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={handleDeleteAccount}
              disabled={deleteConfirmation !== "DELETE" || isDeleting}
            >
              {isDeleting && <Loader2 className="h-4 w-4 animate-spin mr-2" />}
              Delete My Account
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
