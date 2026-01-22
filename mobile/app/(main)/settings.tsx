/**
 * Settings Screen
 */

import { useEffect, useState, useCallback } from "react";
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TextInput,
  TouchableOpacity,
  RefreshControl,
  ActivityIndicator,
  Alert,
  Switch,
} from "react-native";
import { useFocusEffect, useRouter } from "expo-router";
import * as WebBrowser from "expo-web-browser";
import { api, User, SubscriptionStatus } from "../../lib/api/client";
import { supabase } from "../../lib/supabase/client";
import { unregisterFromPushNotifications } from "../../lib/push/notifications";

export default function SettingsScreen() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [subscription, setSubscription] = useState<SubscriptionStatus | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);

  // Form state
  const [displayName, setDisplayName] = useState("");
  const [companionName, setCompanionName] = useState("");
  const [timeFlexibility, setTimeFlexibility] = useState<"exact" | "around" | "window">("exact");
  const [timeWindow, setTimeWindow] = useState<"morning" | "midday" | "evening" | "night">("morning");

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
      setTimeFlexibility(userData.message_time_flexibility || "exact");
      setTimeWindow(userData.message_time_window || "morning");
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
        message_time_flexibility: timeFlexibility,
        message_time_window: timeFlexibility === "window" ? timeWindow : undefined,
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

  const handleDeleteAccount = () => {
    Alert.alert(
      "Delete Account",
      "This will permanently delete your account and all data. This cannot be undone.",
      [
        { text: "Cancel", style: "cancel" },
        {
          text: "Delete",
          style: "destructive",
          onPress: () => {
            Alert.prompt(
              "Confirm Deletion",
              'Type "DELETE" to confirm',
              async (text) => {
                if (text === "DELETE") {
                  try {
                    await api.users.deleteAccount("DELETE");
                    await supabase.auth.signOut();
                  } catch (error) {
                    console.error("Failed to delete:", error);
                    Alert.alert("Error", "Failed to delete account");
                  }
                } else {
                  Alert.alert("Error", "Confirmation text did not match");
                }
              }
            );
          },
        },
      ]
    );
  };

  if (isLoading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#FF6B6B" />
      </View>
    );
  }

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      {/* Profile Section */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Profile</Text>
        <View style={styles.card}>
          <View style={styles.field}>
            <Text style={styles.label}>Your Name</Text>
            <TextInput
              style={styles.input}
              value={displayName}
              onChangeText={setDisplayName}
              placeholder="How should we address you?"
            />
          </View>
          <View style={styles.field}>
            <Text style={styles.label}>Companion Name</Text>
            <TextInput
              style={styles.input}
              value={companionName}
              onChangeText={setCompanionName}
              placeholder="Name your AI companion"
            />
          </View>
          <TouchableOpacity
            style={[styles.button, isSaving && styles.buttonDisabled]}
            onPress={handleSaveProfile}
            disabled={isSaving}
          >
            <Text style={styles.buttonText}>Save Profile</Text>
          </TouchableOpacity>
        </View>
      </View>

      {/* Message Timing Section */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Message Timing</Text>
        <View style={styles.card}>
          <TouchableOpacity
            style={[
              styles.optionCard,
              timeFlexibility === "exact" && styles.optionCardSelected,
            ]}
            onPress={() => setTimeFlexibility("exact")}
          >
            <View style={styles.optionRadio}>
              {timeFlexibility === "exact" && <View style={styles.optionRadioSelected} />}
            </View>
            <View style={styles.optionContent}>
              <Text style={styles.optionTitle}>At a specific time</Text>
              <Text style={styles.optionDescription}>
                Message arrives at the exact time you choose
              </Text>
            </View>
          </TouchableOpacity>

          <TouchableOpacity
            style={[
              styles.optionCard,
              timeFlexibility === "around" && styles.optionCardSelected,
            ]}
            onPress={() => setTimeFlexibility("around")}
          >
            <View style={styles.optionRadio}>
              {timeFlexibility === "around" && <View style={styles.optionRadioSelected} />}
            </View>
            <View style={styles.optionContent}>
              <Text style={styles.optionTitle}>Around a specific time</Text>
              <Text style={styles.optionDescription}>
                Message arrives within ~30 minutes
              </Text>
            </View>
          </TouchableOpacity>

          <TouchableOpacity
            style={[
              styles.optionCard,
              timeFlexibility === "window" && styles.optionCardSelected,
            ]}
            onPress={() => setTimeFlexibility("window")}
          >
            <View style={styles.optionRadio}>
              {timeFlexibility === "window" && <View style={styles.optionRadioSelected} />}
            </View>
            <View style={styles.optionContent}>
              <Text style={styles.optionTitle}>During a time window</Text>
              <Text style={styles.optionDescription}>
                Message arrives sometime within your chosen window
              </Text>
            </View>
          </TouchableOpacity>

          {timeFlexibility === "window" && (
            <View style={styles.windowOptions}>
              {(["morning", "midday", "evening", "night"] as const).map((w) => (
                <TouchableOpacity
                  key={w}
                  style={[
                    styles.windowOption,
                    timeWindow === w && styles.windowOptionSelected,
                  ]}
                  onPress={() => setTimeWindow(w)}
                >
                  <Text
                    style={[
                      styles.windowOptionText,
                      timeWindow === w && styles.windowOptionTextSelected,
                    ]}
                  >
                    {w.charAt(0).toUpperCase() + w.slice(1)}
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
            <Text style={styles.buttonText}>Save Preferences</Text>
          </TouchableOpacity>
        </View>
      </View>

      {/* Subscription Section */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Subscription</Text>
        <View style={styles.card}>
          <Text style={styles.subscriptionStatus}>
            Status: {subscription?.is_active ? "Active" : "Free"}
          </Text>
          <TouchableOpacity
            style={styles.linkButton}
            onPress={handleManageSubscription}
          >
            <Text style={styles.linkButtonText}>Manage Subscription →</Text>
          </TouchableOpacity>
        </View>
      </View>

      {/* Account Section */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Account</Text>
        <View style={styles.card}>
          <Text style={styles.email}>{user?.email}</Text>
          <TouchableOpacity style={styles.logoutButton} onPress={handleLogout}>
            <Text style={styles.logoutButtonText}>Log Out</Text>
          </TouchableOpacity>
        </View>
      </View>

      {/* Danger Zone */}
      <View style={styles.section}>
        <Text style={[styles.sectionTitle, styles.dangerTitle]}>Danger Zone</Text>
        <View style={[styles.card, styles.dangerCard]}>
          <Text style={styles.dangerText}>
            Once you delete your account, there is no going back.
          </Text>
          <TouchableOpacity
            style={styles.deleteButton}
            onPress={handleDeleteAccount}
          >
            <Text style={styles.deleteButtonText}>Delete Account</Text>
          </TouchableOpacity>
        </View>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#F5F5F5",
  },
  content: {
    padding: 16,
    paddingBottom: 48,
  },
  loadingContainer: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
  },
  section: {
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: "600",
    color: "#333",
    marginBottom: 12,
  },
  card: {
    backgroundColor: "#fff",
    borderRadius: 12,
    padding: 16,
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
  input: {
    height: 48,
    borderWidth: 1,
    borderColor: "#E5E5E5",
    borderRadius: 8,
    paddingHorizontal: 12,
    fontSize: 16,
    backgroundColor: "#F9F9F9",
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
  windowOptions: {
    flexDirection: "row",
    flexWrap: "wrap",
    marginVertical: 8,
  },
  windowOption: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    backgroundColor: "#F0F0F0",
    marginRight: 8,
    marginBottom: 8,
  },
  windowOptionSelected: {
    backgroundColor: "#FF6B6B",
  },
  windowOptionText: {
    fontSize: 14,
    color: "#666",
  },
  windowOptionTextSelected: {
    color: "#fff",
  },
  subscriptionStatus: {
    fontSize: 16,
    color: "#333",
    marginBottom: 12,
  },
  linkButton: {
    paddingVertical: 8,
  },
  linkButtonText: {
    fontSize: 14,
    color: "#FF6B6B",
    fontWeight: "500",
  },
  email: {
    fontSize: 16,
    color: "#666",
    marginBottom: 12,
  },
  logoutButton: {
    paddingVertical: 12,
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
});
