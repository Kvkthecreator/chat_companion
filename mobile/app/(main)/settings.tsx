/**
 * Settings Screen
 * Full-featured settings with tabs matching web experience
 */

import { useEffect, useState, useCallback, useMemo } from "react";
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TextInput,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
  Modal,
  Platform,
} from "react-native";
import { useFocusEffect, useRouter } from "expo-router";
import * as WebBrowser from "expo-web-browser";
import * as Localization from "expo-localization";
import DateTimePicker from "@react-native-community/datetimepicker";
import { api, User, SubscriptionStatus } from "../../lib/api/client";
import { supabase } from "../../lib/supabase/client";
import { unregisterFromPushNotifications } from "../../lib/push/notifications";

// Comprehensive timezone list organized by region
const TIMEZONE_REGIONS = [
  {
    region: "Americas",
    timezones: [
      { value: "America/New_York", label: "New York (ET)", offset: -5 },
      { value: "America/Chicago", label: "Chicago (CT)", offset: -6 },
      { value: "America/Denver", label: "Denver (MT)", offset: -7 },
      { value: "America/Los_Angeles", label: "Los Angeles (PT)", offset: -8 },
      { value: "America/Anchorage", label: "Anchorage (AKT)", offset: -9 },
      { value: "Pacific/Honolulu", label: "Honolulu (HT)", offset: -10 },
      { value: "America/Phoenix", label: "Phoenix (MST)", offset: -7 },
      { value: "America/Toronto", label: "Toronto (ET)", offset: -5 },
      { value: "America/Vancouver", label: "Vancouver (PT)", offset: -8 },
      { value: "America/Mexico_City", label: "Mexico City (CST)", offset: -6 },
      { value: "America/Sao_Paulo", label: "São Paulo (BRT)", offset: -3 },
      { value: "America/Buenos_Aires", label: "Buenos Aires (ART)", offset: -3 },
      { value: "America/Lima", label: "Lima (PET)", offset: -5 },
      { value: "America/Bogota", label: "Bogotá (COT)", offset: -5 },
      { value: "America/Santiago", label: "Santiago (CLT)", offset: -3 },
    ],
  },
  {
    region: "Europe",
    timezones: [
      { value: "Europe/London", label: "London (GMT/BST)", offset: 0 },
      { value: "Europe/Paris", label: "Paris (CET)", offset: 1 },
      { value: "Europe/Berlin", label: "Berlin (CET)", offset: 1 },
      { value: "Europe/Madrid", label: "Madrid (CET)", offset: 1 },
      { value: "Europe/Rome", label: "Rome (CET)", offset: 1 },
      { value: "Europe/Amsterdam", label: "Amsterdam (CET)", offset: 1 },
      { value: "Europe/Brussels", label: "Brussels (CET)", offset: 1 },
      { value: "Europe/Vienna", label: "Vienna (CET)", offset: 1 },
      { value: "Europe/Stockholm", label: "Stockholm (CET)", offset: 1 },
      { value: "Europe/Warsaw", label: "Warsaw (CET)", offset: 1 },
      { value: "Europe/Prague", label: "Prague (CET)", offset: 1 },
      { value: "Europe/Zurich", label: "Zurich (CET)", offset: 1 },
      { value: "Europe/Athens", label: "Athens (EET)", offset: 2 },
      { value: "Europe/Helsinki", label: "Helsinki (EET)", offset: 2 },
      { value: "Europe/Istanbul", label: "Istanbul (TRT)", offset: 3 },
      { value: "Europe/Moscow", label: "Moscow (MSK)", offset: 3 },
      { value: "Europe/Kiev", label: "Kyiv (EET)", offset: 2 },
      { value: "Europe/Dublin", label: "Dublin (GMT/IST)", offset: 0 },
      { value: "Europe/Lisbon", label: "Lisbon (WET)", offset: 0 },
    ],
  },
  {
    region: "Asia",
    timezones: [
      { value: "Asia/Tokyo", label: "Tokyo (JST)", offset: 9 },
      { value: "Asia/Seoul", label: "Seoul (KST)", offset: 9 },
      { value: "Asia/Shanghai", label: "Shanghai (CST)", offset: 8 },
      { value: "Asia/Hong_Kong", label: "Hong Kong (HKT)", offset: 8 },
      { value: "Asia/Taipei", label: "Taipei (CST)", offset: 8 },
      { value: "Asia/Singapore", label: "Singapore (SGT)", offset: 8 },
      { value: "Asia/Kuala_Lumpur", label: "Kuala Lumpur (MYT)", offset: 8 },
      { value: "Asia/Bangkok", label: "Bangkok (ICT)", offset: 7 },
      { value: "Asia/Ho_Chi_Minh", label: "Ho Chi Minh (ICT)", offset: 7 },
      { value: "Asia/Jakarta", label: "Jakarta (WIB)", offset: 7 },
      { value: "Asia/Manila", label: "Manila (PHT)", offset: 8 },
      { value: "Asia/Kolkata", label: "India (IST)", offset: 5.5 },
      { value: "Asia/Mumbai", label: "Mumbai (IST)", offset: 5.5 },
      { value: "Asia/Dubai", label: "Dubai (GST)", offset: 4 },
      { value: "Asia/Riyadh", label: "Riyadh (AST)", offset: 3 },
      { value: "Asia/Tel_Aviv", label: "Tel Aviv (IST)", offset: 2 },
      { value: "Asia/Karachi", label: "Karachi (PKT)", offset: 5 },
      { value: "Asia/Dhaka", label: "Dhaka (BST)", offset: 6 },
      { value: "Asia/Yangon", label: "Yangon (MMT)", offset: 6.5 },
    ],
  },
  {
    region: "Pacific",
    timezones: [
      { value: "Australia/Sydney", label: "Sydney (AEST)", offset: 10 },
      { value: "Australia/Melbourne", label: "Melbourne (AEST)", offset: 10 },
      { value: "Australia/Brisbane", label: "Brisbane (AEST)", offset: 10 },
      { value: "Australia/Perth", label: "Perth (AWST)", offset: 8 },
      { value: "Australia/Adelaide", label: "Adelaide (ACST)", offset: 9.5 },
      { value: "Pacific/Auckland", label: "Auckland (NZST)", offset: 12 },
      { value: "Pacific/Fiji", label: "Fiji (FJT)", offset: 12 },
      { value: "Pacific/Guam", label: "Guam (ChST)", offset: 10 },
    ],
  },
  {
    region: "Africa & Middle East",
    timezones: [
      { value: "Africa/Cairo", label: "Cairo (EET)", offset: 2 },
      { value: "Africa/Johannesburg", label: "Johannesburg (SAST)", offset: 2 },
      { value: "Africa/Lagos", label: "Lagos (WAT)", offset: 1 },
      { value: "Africa/Nairobi", label: "Nairobi (EAT)", offset: 3 },
      { value: "Africa/Casablanca", label: "Casablanca (WET)", offset: 1 },
    ],
  },
  {
    region: "Other",
    timezones: [
      { value: "UTC", label: "UTC (Coordinated Universal Time)", offset: 0 },
    ],
  },
];

// Flatten for search
const ALL_TIMEZONES = TIMEZONE_REGIONS.flatMap((r) => r.timezones);

// Support style options
const SUPPORT_STYLES = [
  { value: "motivational", label: "Motivational", description: "Encouraging and energizing" },
  { value: "friendly_checkin", label: "Friendly Check-in", description: "Warm and casual, like a close friend" },
  { value: "accountability", label: "Accountability", description: "Supportive but direct about goals" },
  { value: "listener", label: "Listener", description: "Gentle and present, space to share" },
];

// Delete reasons
const DELETE_REASONS = [
  { value: "not_using", label: "Not using the app anymore" },
  { value: "found_alternative", label: "Found an alternative" },
  { value: "privacy", label: "Privacy concerns" },
  { value: "too_expensive", label: "Too expensive" },
  { value: "not_satisfied", label: "Not satisfied" },
  { value: "other", label: "Other" },
];

type TabType = "preferences" | "channels" | "billing" | "account";

export default function SettingsScreen() {
  const router = useRouter();
  const [activeTab, setActiveTab] = useState<TabType>("preferences");
  const [user, setUser] = useState<User | null>(null);
  const [subscription, setSubscription] = useState<SubscriptionStatus | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);

  // Form state
  const [displayName, setDisplayName] = useState("");
  const [companionName, setCompanionName] = useState("");
  const [timezone, setTimezone] = useState("America/New_York");
  const [preferredTime, setPreferredTime] = useState("09:00");
  const [timeFlexibility, setTimeFlexibility] = useState<"exact" | "around" | "window">("exact");
  const [timeWindow, setTimeWindow] = useState<"morning" | "midday" | "evening" | "night">("morning");
  const [supportStyle, setSupportStyle] = useState("friendly_checkin");

  // Modal states
  const [showTimezoneModal, setShowTimezoneModal] = useState(false);
  const [showSupportStyleModal, setShowSupportStyleModal] = useState(false);
  const [showTimePicker, setShowTimePicker] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [showDeleteReasonModal, setShowDeleteReasonModal] = useState(false);

  // Timezone search
  const [timezoneSearch, setTimezoneSearch] = useState("");

  // Delete account state
  const [deleteConfirmation, setDeleteConfirmation] = useState("");
  const [deleteReason, setDeleteReason] = useState("");
  const [isDeleting, setIsDeleting] = useState(false);

  // Detected device timezone
  const deviceTimezone = useMemo(() => {
    return Localization.timezone || "UTC";
  }, []);

  // Filter timezones based on search
  const filteredTimezones = useMemo(() => {
    if (!timezoneSearch.trim()) {
      return TIMEZONE_REGIONS;
    }
    const search = timezoneSearch.toLowerCase();
    return TIMEZONE_REGIONS.map((region) => ({
      ...region,
      timezones: region.timezones.filter(
        (tz) =>
          tz.label.toLowerCase().includes(search) ||
          tz.value.toLowerCase().includes(search)
      ),
    })).filter((region) => region.timezones.length > 0);
  }, [timezoneSearch]);

  // Get display label for current timezone
  const getTimezoneLabel = (value: string): string => {
    const found = ALL_TIMEZONES.find((tz) => tz.value === value);
    if (found) return found.label;
    // If not in our list, show the raw value
    return value.replace(/_/g, " ").replace(/\//g, " / ");
  };

  const loadData = async () => {
    try {
      const [userData, subscriptionData] = await Promise.all([
        api.users.me(),
        api.subscription.getStatus().catch(() => null),
      ]);
      setUser(userData);
      setSubscription(subscriptionData);

      // Populate form
      setDisplayName(userData.display_name || "");
      setCompanionName(userData.companion_name || "");
      setTimezone(userData.timezone || deviceTimezone);
      setPreferredTime(userData.preferred_message_time || "09:00");
      setTimeFlexibility(userData.message_time_flexibility || "exact");
      setTimeWindow(userData.message_time_window || "morning");
      setSupportStyle(userData.support_style || "friendly_checkin");
    } catch (error) {
      console.error("Failed to load settings:", error);
    } finally {
      setIsLoading(false);
    }
  };

  useFocusEffect(
    useCallback(() => {
      loadData();
    }, [])
  );

  const handleUseDeviceTimezone = async () => {
    setTimezone(deviceTimezone);
    setShowTimezoneModal(false);
    // Auto-save when using device timezone
    setIsSaving(true);
    try {
      await api.users.update({ timezone: deviceTimezone });
    } catch (error) {
      console.error("Failed to save timezone:", error);
    } finally {
      setIsSaving(false);
    }
  };

  const handleSaveProfile = async () => {
    setIsSaving(true);
    try {
      await api.users.update({
        display_name: displayName,
        companion_name: companionName,
      });
      Alert.alert("Saved", "Your profile has been updated");
      loadData();
    } catch (error) {
      console.error("Failed to save:", error);
      Alert.alert("Error", "Failed to save changes");
    } finally {
      setIsSaving(false);
    }
  };

  const handleSavePreferences = async () => {
    setIsSaving(true);
    try {
      await api.users.update({
        timezone,
        preferred_message_time: preferredTime,
        message_time_flexibility: timeFlexibility,
        message_time_window: timeFlexibility === "window" ? timeWindow : undefined,
        support_style: supportStyle,
      });
      Alert.alert("Saved", "Your preferences have been updated");
      loadData();
    } catch (error) {
      console.error("Failed to save:", error);
      Alert.alert("Error", "Failed to save changes");
    } finally {
      setIsSaving(false);
    }
  };

  const handleManageSubscription = async () => {
    try {
      const { portal_url } = await api.subscription.getPortal();
      await WebBrowser.openBrowserAsync(portal_url);
    } catch (error) {
      console.error("Failed to open portal:", error);
      Alert.alert("Error", "Failed to open subscription portal");
    }
  };

  const handleLogout = async () => {
    Alert.alert(
      "Log Out",
      "Are you sure you want to log out?",
      [
        { text: "Cancel", style: "cancel" },
        {
          text: "Log Out",
          style: "destructive",
          onPress: async () => {
            await unregisterFromPushNotifications();
            await supabase.auth.signOut();
          },
        },
      ]
    );
  };

  const handleDeleteAccount = async () => {
    if (deleteConfirmation !== "DELETE") {
      Alert.alert("Error", "Please type DELETE to confirm");
      return;
    }

    setIsDeleting(true);
    try {
      await api.users.deleteAccount("DELETE", deleteReason || undefined);
      await supabase.auth.signOut();
    } catch (error) {
      console.error("Failed to delete:", error);
      Alert.alert("Error", "Failed to delete account");
      setIsDeleting(false);
    }
  };

  const parseTimeToDate = (timeStr: string): Date => {
    const [hours, minutes] = timeStr.split(":").map(Number);
    const date = new Date();
    date.setHours(hours, minutes, 0, 0);
    return date;
  };

  const formatTimeFromDate = (date: Date): string => {
    const hours = date.getHours().toString().padStart(2, "0");
    const minutes = date.getMinutes().toString().padStart(2, "0");
    return `${hours}:${minutes}`;
  };

  if (isLoading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#FF6B6B" />
      </View>
    );
  }

  const renderTabs = () => (
    <View style={styles.tabContainer}>
      {(["preferences", "channels", "billing", "account"] as TabType[]).map((tab) => (
        <TouchableOpacity
          key={tab}
          style={[styles.tab, activeTab === tab && styles.tabActive]}
          onPress={() => setActiveTab(tab)}
        >
          <Text style={[styles.tabText, activeTab === tab && styles.tabTextActive]}>
            {tab.charAt(0).toUpperCase() + tab.slice(1)}
          </Text>
        </TouchableOpacity>
      ))}
    </View>
  );

  const renderPreferencesTab = () => (
    <ScrollView style={styles.tabContent} showsVerticalScrollIndicator={false}>
      {/* Companion Settings */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Companion Settings</Text>
        <View style={styles.card}>
          <View style={styles.field}>
            <Text style={styles.label}>Companion Name</Text>
            <TextInput
              style={styles.input}
              value={companionName}
              onChangeText={setCompanionName}
              placeholder="Give your companion a name"
            />
            <Text style={styles.hint}>Your companion will use this name when talking to you.</Text>
          </View>

          <View style={styles.field}>
            <Text style={styles.label}>Support Style</Text>
            <TouchableOpacity
              style={styles.selector}
              onPress={() => setShowSupportStyleModal(true)}
            >
              <Text style={styles.selectorText}>
                {SUPPORT_STYLES.find((s) => s.value === supportStyle)?.label || "Select style"}
              </Text>
              <Text style={styles.selectorArrow}>›</Text>
            </TouchableOpacity>
          </View>
        </View>
      </View>

      {/* Message Schedule */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Message Schedule</Text>
        <View style={styles.card}>
          <View style={styles.field}>
            <Text style={styles.label}>Timezone</Text>
            <TouchableOpacity
              style={styles.selector}
              onPress={() => setShowTimezoneModal(true)}
            >
              <Text style={styles.selectorText} numberOfLines={1}>
                {getTimezoneLabel(timezone)}
              </Text>
              <Text style={styles.selectorArrow}>›</Text>
            </TouchableOpacity>
            {timezone !== deviceTimezone && (
              <TouchableOpacity onPress={handleUseDeviceTimezone}>
                <Text style={styles.detectLink}>
                  Use device timezone ({getTimezoneLabel(deviceTimezone)})
                </Text>
              </TouchableOpacity>
            )}
          </View>

          <Text style={styles.label}>Message Timing</Text>

          {/* Exact Time Option */}
          <TouchableOpacity
            style={[styles.optionCard, timeFlexibility === "exact" && styles.optionCardSelected]}
            onPress={() => setTimeFlexibility("exact")}
          >
            <View style={styles.optionRadio}>
              {timeFlexibility === "exact" && <View style={styles.optionRadioSelected} />}
            </View>
            <View style={styles.optionContent}>
              <Text style={styles.optionTitle}>At a specific time</Text>
              <Text style={styles.optionDescription}>Message arrives at the exact time you choose</Text>
              {timeFlexibility === "exact" && (
                <TouchableOpacity
                  style={styles.timeButton}
                  onPress={() => setShowTimePicker(true)}
                >
                  <Text style={styles.timeButtonText}>{preferredTime}</Text>
                </TouchableOpacity>
              )}
            </View>
          </TouchableOpacity>

          {/* Around Time Option */}
          <TouchableOpacity
            style={[styles.optionCard, timeFlexibility === "around" && styles.optionCardSelected]}
            onPress={() => setTimeFlexibility("around")}
          >
            <View style={styles.optionRadio}>
              {timeFlexibility === "around" && <View style={styles.optionRadioSelected} />}
            </View>
            <View style={styles.optionContent}>
              <Text style={styles.optionTitle}>Around a specific time</Text>
              <Text style={styles.optionDescription}>Message arrives within ~30 minutes</Text>
              {timeFlexibility === "around" && (
                <TouchableOpacity
                  style={styles.timeButton}
                  onPress={() => setShowTimePicker(true)}
                >
                  <Text style={styles.timeButtonText}>{preferredTime}</Text>
                </TouchableOpacity>
              )}
            </View>
          </TouchableOpacity>

          {/* Window Option */}
          <TouchableOpacity
            style={[styles.optionCard, timeFlexibility === "window" && styles.optionCardSelected]}
            onPress={() => setTimeFlexibility("window")}
          >
            <View style={styles.optionRadio}>
              {timeFlexibility === "window" && <View style={styles.optionRadioSelected} />}
            </View>
            <View style={styles.optionContent}>
              <Text style={styles.optionTitle}>During a time window</Text>
              <Text style={styles.optionDescription}>Message arrives sometime within your chosen window</Text>
            </View>
          </TouchableOpacity>

          {timeFlexibility === "window" && (
            <View style={styles.windowOptions}>
              {([
                { value: "morning", label: "Morning", time: "6am - 10am" },
                { value: "midday", label: "Midday", time: "11am - 2pm" },
                { value: "evening", label: "Evening", time: "5pm - 8pm" },
                { value: "night", label: "Night", time: "8pm - 11pm" },
              ] as const).map((w) => (
                <TouchableOpacity
                  key={w.value}
                  style={[styles.windowOption, timeWindow === w.value && styles.windowOptionSelected]}
                  onPress={() => setTimeWindow(w.value)}
                >
                  <Text style={[styles.windowOptionLabel, timeWindow === w.value && styles.windowOptionTextSelected]}>
                    {w.label}
                  </Text>
                  <Text style={[styles.windowOptionTime, timeWindow === w.value && styles.windowOptionTextSelected]}>
                    {w.time}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>
          )}

          <TouchableOpacity
            style={[styles.button, isSaving && styles.buttonDisabled]}
            onPress={handleSavePreferences}
            disabled={isSaving}
          >
            {isSaving ? (
              <ActivityIndicator size="small" color="#fff" />
            ) : (
              <Text style={styles.buttonText}>Save Preferences</Text>
            )}
          </TouchableOpacity>
        </View>
      </View>
    </ScrollView>
  );

  const renderChannelsTab = () => (
    <ScrollView style={styles.tabContent} showsVerticalScrollIndicator={false}>
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Message Channels</Text>
        <Text style={styles.sectionDescription}>
          How do you want to receive messages from your companion?
        </Text>

        <View style={styles.card}>
          {/* Mobile Push */}
          <View style={styles.channelRow}>
            <View style={[styles.channelIcon, { backgroundColor: "#FF6B6B" }]}>
              <Text style={styles.channelIconText}>📱</Text>
            </View>
            <View style={styles.channelInfo}>
              <Text style={styles.channelName}>Mobile Push</Text>
              <Text style={styles.channelDescription}>Notifications on this device</Text>
            </View>
            <View style={styles.channelStatus}>
              <Text style={styles.channelStatusActive}>✓ Active</Text>
            </View>
          </View>

          {/* Telegram */}
          <View style={styles.channelRow}>
            <View style={[styles.channelIcon, { backgroundColor: "#0088cc" }]}>
              <Text style={styles.channelIconText}>✈️</Text>
            </View>
            <View style={styles.channelInfo}>
              <Text style={styles.channelName}>Telegram</Text>
              <Text style={styles.channelDescription}>Primary messaging channel</Text>
            </View>
            <TouchableOpacity style={styles.channelConnectButton}>
              <Text style={styles.channelConnectText}>Connect</Text>
            </TouchableOpacity>
          </View>

          {/* Web Chat */}
          <View style={styles.channelRow}>
            <View style={[styles.channelIcon, { backgroundColor: "#FF6B6B" }]}>
              <Text style={styles.channelIconText}>💬</Text>
            </View>
            <View style={styles.channelInfo}>
              <Text style={styles.channelName}>Web Chat</Text>
              <Text style={styles.channelDescription}>Chat directly on the website</Text>
            </View>
            <View style={styles.channelStatus}>
              <Text style={styles.channelStatusAvailable}>Available</Text>
            </View>
          </View>

          {/* WhatsApp */}
          <View style={[styles.channelRow, styles.channelDisabled]}>
            <View style={[styles.channelIcon, { backgroundColor: "#25D366" }]}>
              <Text style={styles.channelIconText}>📞</Text>
            </View>
            <View style={styles.channelInfo}>
              <Text style={styles.channelName}>WhatsApp</Text>
              <Text style={styles.channelDescription}>Coming soon</Text>
            </View>
            <Text style={styles.channelComingSoon}>Coming Soon</Text>
          </View>
        </View>
      </View>
    </ScrollView>
  );

  const renderBillingTab = () => (
    <ScrollView style={styles.tabContent} showsVerticalScrollIndicator={false}>
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Your Plan</Text>
        <View style={styles.card}>
          <View style={styles.subscriptionInfo}>
            <Text style={styles.subscriptionLabel}>Status</Text>
            <Text
              style={[
                styles.subscriptionStatus,
                subscription?.is_active ? styles.subscriptionActive : styles.subscriptionInactive,
              ]}
            >
              {subscription?.is_active ? "Premium" : "Free"}
            </Text>
          </View>

          {subscription?.current_period_end && (
            <View style={styles.subscriptionInfo}>
              <Text style={styles.subscriptionLabel}>Renews</Text>
              <Text style={styles.subscriptionDate}>
                {new Date(subscription.current_period_end).toLocaleDateString()}
              </Text>
            </View>
          )}

          <TouchableOpacity style={styles.linkButton} onPress={handleManageSubscription}>
            <Text style={styles.linkButtonText}>Manage Subscription →</Text>
          </TouchableOpacity>
        </View>
      </View>
    </ScrollView>
  );

  const renderAccountTab = () => (
    <ScrollView style={styles.tabContent} showsVerticalScrollIndicator={false}>
      {/* Profile */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Profile</Text>
        <View style={styles.card}>
          <View style={styles.field}>
            <Text style={styles.label}>Email</Text>
            <View style={styles.inputDisabled}>
              <Text style={styles.inputDisabledText}>{user?.email}</Text>
            </View>
          </View>

          <View style={styles.field}>
            <Text style={styles.label}>Display Name</Text>
            <TextInput
              style={styles.input}
              value={displayName}
              onChangeText={setDisplayName}
              placeholder="How should we address you?"
            />
          </View>

          <TouchableOpacity
            style={[styles.button, isSaving && styles.buttonDisabled]}
            onPress={handleSaveProfile}
            disabled={isSaving}
          >
            {isSaving ? (
              <ActivityIndicator size="small" color="#fff" />
            ) : (
              <Text style={styles.buttonText}>Save Profile</Text>
            )}
          </TouchableOpacity>
        </View>
      </View>

      {/* Log Out */}
      <View style={styles.section}>
        <View style={styles.card}>
          <TouchableOpacity style={styles.logoutButton} onPress={handleLogout}>
            <Text style={styles.logoutButtonText}>Log Out</Text>
          </TouchableOpacity>
        </View>
      </View>

      {/* Danger Zone */}
      <View style={styles.section}>
        <Text style={[styles.sectionTitle, styles.dangerTitle]}>Danger Zone</Text>
        <View style={[styles.card, styles.dangerCard]}>
          <Text style={styles.dangerText}>Permanently delete your account and all data.</Text>
          <TouchableOpacity style={styles.deleteButton} onPress={() => setShowDeleteModal(true)}>
            <Text style={styles.deleteButtonText}>Delete Account</Text>
          </TouchableOpacity>
        </View>
      </View>
    </ScrollView>
  );

  return (
    <View style={styles.container}>
      {renderTabs()}

      {activeTab === "preferences" && renderPreferencesTab()}
      {activeTab === "channels" && renderChannelsTab()}
      {activeTab === "billing" && renderBillingTab()}
      {activeTab === "account" && renderAccountTab()}

      {/* Timezone Modal */}
      <Modal visible={showTimezoneModal} animationType="slide" presentationStyle="pageSheet">
        <View style={styles.modalContainer}>
          <View style={styles.modalHeader}>
            <TouchableOpacity onPress={() => setShowTimezoneModal(false)}>
              <Text style={styles.modalCancel}>Cancel</Text>
            </TouchableOpacity>
            <Text style={styles.modalTitle}>Select Timezone</Text>
            <View style={{ width: 60 }} />
          </View>

          {/* Search */}
          <View style={styles.searchContainer}>
            <TextInput
              style={styles.searchInput}
              value={timezoneSearch}
              onChangeText={setTimezoneSearch}
              placeholder="Search cities or timezones..."
              placeholderTextColor="#999"
              autoCapitalize="none"
              autoCorrect={false}
            />
          </View>

          {/* Device Timezone Option */}
          <TouchableOpacity style={styles.deviceTimezoneButton} onPress={handleUseDeviceTimezone}>
            <View style={styles.deviceTimezoneContent}>
              <Text style={styles.deviceTimezoneLabel}>📍 Use Device Timezone</Text>
              <Text style={styles.deviceTimezoneValue}>{getTimezoneLabel(deviceTimezone)}</Text>
            </View>
            {timezone === deviceTimezone && <Text style={styles.checkmark}>✓</Text>}
          </TouchableOpacity>

          <ScrollView style={styles.modalContent}>
            {filteredTimezones.map((region) => (
              <View key={region.region}>
                <Text style={styles.regionHeader}>{region.region}</Text>
                {region.timezones.map((tz) => (
                  <TouchableOpacity
                    key={tz.value}
                    style={[styles.modalOption, timezone === tz.value && styles.modalOptionSelected]}
                    onPress={() => {
                      setTimezone(tz.value);
                      setShowTimezoneModal(false);
                      setTimezoneSearch("");
                    }}
                  >
                    <Text
                      style={[styles.modalOptionText, timezone === tz.value && styles.modalOptionTextSelected]}
                    >
                      {tz.label}
                    </Text>
                    {timezone === tz.value && <Text style={styles.checkmark}>✓</Text>}
                  </TouchableOpacity>
                ))}
              </View>
            ))}
          </ScrollView>
        </View>
      </Modal>

      {/* Support Style Modal */}
      <Modal visible={showSupportStyleModal} animationType="slide" presentationStyle="pageSheet">
        <View style={styles.modalContainer}>
          <View style={styles.modalHeader}>
            <Text style={styles.modalTitle}>Select Support Style</Text>
            <TouchableOpacity onPress={() => setShowSupportStyleModal(false)}>
              <Text style={styles.modalDone}>Done</Text>
            </TouchableOpacity>
          </View>
          <ScrollView style={styles.modalContent}>
            {SUPPORT_STYLES.map((style) => (
              <TouchableOpacity
                key={style.value}
                style={[styles.modalOption, supportStyle === style.value && styles.modalOptionSelected]}
                onPress={() => {
                  setSupportStyle(style.value);
                  setShowSupportStyleModal(false);
                }}
              >
                <View style={styles.modalOptionContent}>
                  <Text
                    style={[styles.modalOptionText, supportStyle === style.value && styles.modalOptionTextSelected]}
                  >
                    {style.label}
                  </Text>
                  <Text style={styles.modalOptionDescription}>{style.description}</Text>
                </View>
                {supportStyle === style.value && <Text style={styles.checkmark}>✓</Text>}
              </TouchableOpacity>
            ))}
          </ScrollView>
        </View>
      </Modal>

      {/* Time Picker */}
      {showTimePicker && Platform.OS === "ios" && (
        <Modal visible={showTimePicker} animationType="slide" presentationStyle="pageSheet">
          <View style={styles.modalContainer}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>Select Time</Text>
              <TouchableOpacity onPress={() => setShowTimePicker(false)}>
                <Text style={styles.modalDone}>Done</Text>
              </TouchableOpacity>
            </View>
            <View style={styles.timePickerContainer}>
              <DateTimePicker
                value={parseTimeToDate(preferredTime)}
                mode="time"
                display="spinner"
                onChange={(event, date) => {
                  if (date) {
                    setPreferredTime(formatTimeFromDate(date));
                  }
                }}
                style={styles.timePicker}
              />
            </View>
          </View>
        </Modal>
      )}

      {Platform.OS === "android" && showTimePicker && (
        <DateTimePicker
          value={parseTimeToDate(preferredTime)}
          mode="time"
          display="default"
          onChange={(event, date) => {
            setShowTimePicker(false);
            if (date && event.type !== "dismissed") {
              setPreferredTime(formatTimeFromDate(date));
            }
          }}
        />
      )}

      {/* Delete Account Modal */}
      <Modal visible={showDeleteModal} animationType="slide" presentationStyle="pageSheet">
        <View style={styles.modalContainer}>
          <View style={styles.modalHeader}>
            <TouchableOpacity
              onPress={() => {
                setShowDeleteModal(false);
                setDeleteConfirmation("");
                setDeleteReason("");
              }}
            >
              <Text style={styles.modalCancel}>Cancel</Text>
            </TouchableOpacity>
            <Text style={styles.modalTitle}>Delete Account</Text>
            <View style={{ width: 60 }} />
          </View>

          <ScrollView style={styles.modalContent}>
            <View style={styles.deleteWarning}>
              <Text style={styles.deleteWarningTitle}>This will permanently delete:</Text>
              <Text style={styles.deleteWarningItem}>• Your account and profile</Text>
              <Text style={styles.deleteWarningItem}>• All chat history and messages</Text>
              <Text style={styles.deleteWarningItem}>• All memories and context</Text>
              <Text style={styles.deleteWarningItem}>• Your subscription (will be cancelled)</Text>
            </View>

            <View style={styles.field}>
              <Text style={styles.label}>Why are you leaving? (optional)</Text>
              <TouchableOpacity style={styles.selector} onPress={() => setShowDeleteReasonModal(true)}>
                <Text style={[styles.selectorText, !deleteReason && styles.selectorPlaceholder]}>
                  {DELETE_REASONS.find((r) => r.value === deleteReason)?.label || "Select a reason..."}
                </Text>
                <Text style={styles.selectorArrow}>›</Text>
              </TouchableOpacity>
            </View>

            <View style={styles.field}>
              <Text style={styles.label}>
                Type <Text style={styles.deleteKeyword}>DELETE</Text> to confirm
              </Text>
              <TextInput
                style={styles.input}
                value={deleteConfirmation}
                onChangeText={setDeleteConfirmation}
                placeholder="Type DELETE"
                autoCapitalize="characters"
              />
            </View>

            <TouchableOpacity
              style={[
                styles.deleteConfirmButton,
                deleteConfirmation !== "DELETE" && styles.deleteConfirmButtonDisabled,
              ]}
              onPress={handleDeleteAccount}
              disabled={deleteConfirmation !== "DELETE" || isDeleting}
            >
              {isDeleting ? (
                <ActivityIndicator size="small" color="#fff" />
              ) : (
                <Text style={styles.deleteConfirmButtonText}>Delete My Account</Text>
              )}
            </TouchableOpacity>
          </ScrollView>
        </View>
      </Modal>

      {/* Delete Reason Modal */}
      <Modal visible={showDeleteReasonModal} animationType="slide" presentationStyle="pageSheet">
        <View style={styles.modalContainer}>
          <View style={styles.modalHeader}>
            <Text style={styles.modalTitle}>Select Reason</Text>
            <TouchableOpacity onPress={() => setShowDeleteReasonModal(false)}>
              <Text style={styles.modalDone}>Done</Text>
            </TouchableOpacity>
          </View>
          <ScrollView style={styles.modalContent}>
            {DELETE_REASONS.map((reason) => (
              <TouchableOpacity
                key={reason.value}
                style={[styles.modalOption, deleteReason === reason.value && styles.modalOptionSelected]}
                onPress={() => {
                  setDeleteReason(reason.value);
                  setShowDeleteReasonModal(false);
                }}
              >
                <Text
                  style={[styles.modalOptionText, deleteReason === reason.value && styles.modalOptionTextSelected]}
                >
                  {reason.label}
                </Text>
                {deleteReason === reason.value && <Text style={styles.checkmark}>✓</Text>}
              </TouchableOpacity>
            ))}
          </ScrollView>
        </View>
      </Modal>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#F5F5F5",
  },
  loadingContainer: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
  },
  tabContainer: {
    flexDirection: "row",
    backgroundColor: "#fff",
    paddingHorizontal: 16,
    paddingTop: 8,
    borderBottomWidth: 1,
    borderBottomColor: "#E5E5E5",
  },
  tab: {
    flex: 1,
    paddingVertical: 12,
    alignItems: "center",
    borderBottomWidth: 2,
    borderBottomColor: "transparent",
  },
  tabActive: {
    borderBottomColor: "#FF6B6B",
  },
  tabText: {
    fontSize: 13,
    fontWeight: "500",
    color: "#666",
  },
  tabTextActive: {
    color: "#FF6B6B",
  },
  tabContent: {
    flex: 1,
  },
  section: {
    padding: 16,
    paddingBottom: 0,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: "600",
    color: "#333",
    marginBottom: 8,
  },
  sectionDescription: {
    fontSize: 14,
    color: "#666",
    marginBottom: 12,
  },
  card: {
    backgroundColor: "#fff",
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 1,
  },
  field: {
    marginBottom: 16,
  },
  label: {
    fontSize: 14,
    fontWeight: "500",
    color: "#333",
    marginBottom: 8,
  },
  hint: {
    fontSize: 12,
    color: "#888",
    marginTop: 4,
  },
  input: {
    height: 48,
    borderWidth: 1,
    borderColor: "#E5E5E5",
    borderRadius: 8,
    paddingHorizontal: 12,
    fontSize: 16,
    backgroundColor: "#F9F9F9",
  },
  inputDisabled: {
    height: 48,
    borderWidth: 1,
    borderColor: "#E5E5E5",
    borderRadius: 8,
    paddingHorizontal: 12,
    justifyContent: "center",
    backgroundColor: "#F0F0F0",
  },
  inputDisabledText: {
    fontSize: 16,
    color: "#666",
  },
  selector: {
    height: 48,
    borderWidth: 1,
    borderColor: "#E5E5E5",
    borderRadius: 8,
    paddingHorizontal: 12,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    backgroundColor: "#F9F9F9",
  },
  selectorText: {
    fontSize: 16,
    color: "#333",
    flex: 1,
  },
  selectorPlaceholder: {
    color: "#999",
  },
  selectorArrow: {
    fontSize: 20,
    color: "#999",
  },
  detectLink: {
    fontSize: 13,
    color: "#FF6B6B",
    marginTop: 6,
  },
  button: {
    backgroundColor: "#FF6B6B",
    borderRadius: 8,
    paddingVertical: 14,
    alignItems: "center",
    marginTop: 8,
  },
  buttonDisabled: {
    opacity: 0.7,
  },
  buttonText: {
    color: "#fff",
    fontSize: 16,
    fontWeight: "600",
  },
  optionCard: {
    flexDirection: "row",
    padding: 12,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "#E5E5E5",
    marginBottom: 8,
  },
  optionCardSelected: {
    borderColor: "#FF6B6B",
    backgroundColor: "#FFF5F5",
  },
  optionRadio: {
    width: 20,
    height: 20,
    borderRadius: 10,
    borderWidth: 2,
    borderColor: "#E5E5E5",
    alignItems: "center",
    justifyContent: "center",
    marginRight: 12,
    marginTop: 2,
  },
  optionRadioSelected: {
    width: 10,
    height: 10,
    borderRadius: 5,
    backgroundColor: "#FF6B6B",
  },
  optionContent: {
    flex: 1,
  },
  optionTitle: {
    fontSize: 14,
    fontWeight: "600",
    color: "#333",
    marginBottom: 2,
  },
  optionDescription: {
    fontSize: 12,
    color: "#666",
  },
  timeButton: {
    marginTop: 8,
    backgroundColor: "#fff",
    borderWidth: 1,
    borderColor: "#FF6B6B",
    borderRadius: 6,
    paddingVertical: 8,
    paddingHorizontal: 16,
    alignSelf: "flex-start",
  },
  timeButtonText: {
    fontSize: 16,
    fontWeight: "600",
    color: "#FF6B6B",
  },
  windowOptions: {
    marginTop: 8,
    marginBottom: 8,
  },
  windowOption: {
    padding: 12,
    borderRadius: 8,
    backgroundColor: "#F0F0F0",
    marginBottom: 8,
  },
  windowOptionSelected: {
    backgroundColor: "#FF6B6B",
  },
  windowOptionLabel: {
    fontSize: 14,
    fontWeight: "600",
    color: "#333",
  },
  windowOptionTime: {
    fontSize: 12,
    color: "#666",
    marginTop: 2,
  },
  windowOptionTextSelected: {
    color: "#fff",
  },
  // Channels
  channelRow: {
    flexDirection: "row",
    alignItems: "center",
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: "#F0F0F0",
  },
  channelDisabled: {
    opacity: 0.5,
  },
  channelIcon: {
    width: 40,
    height: 40,
    borderRadius: 20,
    alignItems: "center",
    justifyContent: "center",
    marginRight: 12,
  },
  channelIconText: {
    fontSize: 18,
  },
  channelInfo: {
    flex: 1,
  },
  channelName: {
    fontSize: 16,
    fontWeight: "500",
    color: "#333",
  },
  channelDescription: {
    fontSize: 12,
    color: "#666",
  },
  channelStatus: {},
  channelStatusActive: {
    fontSize: 12,
    color: "#4CAF50",
    fontWeight: "500",
  },
  channelStatusAvailable: {
    fontSize: 12,
    color: "#666",
  },
  channelConnectButton: {
    backgroundColor: "#FFF5F5",
    borderWidth: 1,
    borderColor: "#FF6B6B",
    borderRadius: 6,
    paddingVertical: 6,
    paddingHorizontal: 12,
  },
  channelConnectText: {
    fontSize: 14,
    color: "#FF6B6B",
    fontWeight: "500",
  },
  channelComingSoon: {
    fontSize: 12,
    color: "#999",
  },
  // Billing
  subscriptionInfo: {
    flexDirection: "row",
    justifyContent: "space-between",
    marginBottom: 12,
  },
  subscriptionLabel: {
    fontSize: 14,
    color: "#666",
  },
  subscriptionStatus: {
    fontSize: 14,
    fontWeight: "600",
  },
  subscriptionActive: {
    color: "#4CAF50",
  },
  subscriptionInactive: {
    color: "#666",
  },
  subscriptionDate: {
    fontSize: 14,
    color: "#333",
  },
  linkButton: {
    paddingVertical: 8,
  },
  linkButtonText: {
    fontSize: 14,
    color: "#FF6B6B",
    fontWeight: "500",
  },
  // Account
  logoutButton: {
    paddingVertical: 14,
    alignItems: "center",
    borderWidth: 1,
    borderColor: "#E5E5E5",
    borderRadius: 8,
  },
  logoutButtonText: {
    fontSize: 16,
    color: "#333",
  },
  dangerTitle: {
    color: "#FF6B6B",
  },
  dangerCard: {
    borderWidth: 1,
    borderColor: "#FFE0E0",
  },
  dangerText: {
    fontSize: 14,
    color: "#666",
    marginBottom: 12,
  },
  deleteButton: {
    paddingVertical: 12,
    alignItems: "center",
    backgroundColor: "#FF6B6B",
    borderRadius: 8,
  },
  deleteButtonText: {
    fontSize: 16,
    color: "#fff",
    fontWeight: "600",
  },
  // Modal
  modalContainer: {
    flex: 1,
    backgroundColor: "#fff",
  },
  modalHeader: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: "#E5E5E5",
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: "600",
    color: "#333",
  },
  modalDone: {
    fontSize: 16,
    color: "#FF6B6B",
    fontWeight: "600",
  },
  modalCancel: {
    fontSize: 16,
    color: "#666",
  },
  modalContent: {
    flex: 1,
    padding: 16,
  },
  modalOption: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    padding: 16,
    borderRadius: 8,
    marginBottom: 8,
    backgroundColor: "#F9F9F9",
  },
  modalOptionSelected: {
    backgroundColor: "#FFF5F5",
  },
  modalOptionContent: {
    flex: 1,
  },
  modalOptionText: {
    fontSize: 16,
    color: "#333",
  },
  modalOptionTextSelected: {
    color: "#FF6B6B",
    fontWeight: "600",
  },
  modalOptionDescription: {
    fontSize: 12,
    color: "#666",
    marginTop: 2,
  },
  checkmark: {
    fontSize: 18,
    color: "#FF6B6B",
    fontWeight: "600",
  },
  // Timezone search
  searchContainer: {
    padding: 16,
    paddingBottom: 8,
    borderBottomWidth: 1,
    borderBottomColor: "#E5E5E5",
  },
  searchInput: {
    height: 44,
    borderWidth: 1,
    borderColor: "#E5E5E5",
    borderRadius: 8,
    paddingHorizontal: 12,
    fontSize: 16,
    backgroundColor: "#F9F9F9",
  },
  deviceTimezoneButton: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    marginHorizontal: 16,
    marginTop: 12,
    padding: 14,
    backgroundColor: "#FFF5F5",
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "#FF6B6B",
  },
  deviceTimezoneContent: {
    flex: 1,
  },
  deviceTimezoneLabel: {
    fontSize: 14,
    fontWeight: "600",
    color: "#FF6B6B",
  },
  deviceTimezoneValue: {
    fontSize: 12,
    color: "#666",
    marginTop: 2,
  },
  regionHeader: {
    fontSize: 13,
    fontWeight: "600",
    color: "#888",
    textTransform: "uppercase",
    marginTop: 16,
    marginBottom: 8,
    paddingHorizontal: 4,
  },
  timePickerContainer: {
    padding: 16,
  },
  timePicker: {
    height: 200,
  },
  // Delete modal
  deleteWarning: {
    backgroundColor: "#FFF5F5",
    borderWidth: 1,
    borderColor: "#FFE0E0",
    borderRadius: 8,
    padding: 16,
    marginBottom: 24,
  },
  deleteWarningTitle: {
    fontSize: 14,
    fontWeight: "600",
    color: "#FF6B6B",
    marginBottom: 8,
  },
  deleteWarningItem: {
    fontSize: 14,
    color: "#666",
    marginBottom: 4,
  },
  deleteKeyword: {
    fontWeight: "bold",
    color: "#FF6B6B",
    fontFamily: Platform.OS === "ios" ? "Menlo" : "monospace",
  },
  deleteConfirmButton: {
    backgroundColor: "#FF6B6B",
    borderRadius: 8,
    paddingVertical: 14,
    alignItems: "center",
    marginTop: 16,
  },
  deleteConfirmButtonDisabled: {
    backgroundColor: "#CCC",
  },
  deleteConfirmButtonText: {
    color: "#fff",
    fontSize: 16,
    fontWeight: "600",
  },
});
