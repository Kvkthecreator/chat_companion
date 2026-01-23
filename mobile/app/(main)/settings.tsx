/**
 * Settings Screen - Account, Channels, Billing
 */

import { useEffect, useState, useCallback } from "react";
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
import { api, User, SubscriptionStatus } from "../../lib/api/client";
import { supabase } from "../../lib/supabase/client";
import { unregisterFromPushNotifications } from "../../lib/push/notifications";

// Delete reasons
const DELETE_REASONS = [
  { value: "not_using", label: "Not using the app anymore" },
  { value: "found_alternative", label: "Found an alternative" },
  { value: "privacy", label: "Privacy concerns" },
  { value: "too_expensive", label: "Too expensive" },
  { value: "not_satisfied", label: "Not satisfied" },
  { value: "other", label: "Other" },
];

type TabType = "channels" | "billing" | "account";

export default function SettingsScreen() {
  const router = useRouter();
  const [activeTab, setActiveTab] = useState<TabType>("channels");
  const [user, setUser] = useState<User | null>(null);
  const [subscription, setSubscription] = useState<SubscriptionStatus | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);

  // Form state
  const [displayName, setDisplayName] = useState("");

  // Modal states
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [showDeleteReasonModal, setShowDeleteReasonModal] = useState(false);

  // Delete account state
  const [deleteConfirmation, setDeleteConfirmation] = useState("");
  const [deleteReason, setDeleteReason] = useState("");
  const [isDeleting, setIsDeleting] = useState(false);

  const loadData = async () => {
    try {
      const [userData, subscriptionData] = await Promise.all([
        api.users.me(),
        api.subscription.getStatus().catch(() => null),
      ]);
      setUser(userData);
      setSubscription(subscriptionData);
      setDisplayName(userData.display_name || "");
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

  if (isLoading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#FF6B6B" />
      </View>
    );
  }

  const renderTabs = () => (
    <View style={styles.tabContainer}>
      {(["channels", "billing", "account"] as TabType[]).map((tab) => (
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

  const renderChannelsTab = () => (
    <ScrollView style={styles.tabContent} showsVerticalScrollIndicator={false}>
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Notifications</Text>
        <Text style={styles.sectionDescription}>
          Your companion will send you daily check-ins via push notifications.
        </Text>

        <View style={styles.card}>
          {/* Mobile Push */}
          <View style={[styles.channelRow, { borderBottomWidth: 0 }]}>
            <View style={[styles.channelIcon, { backgroundColor: "#FF6B6B" }]}>
              <Text style={styles.channelIconText}>📱</Text>
            </View>
            <View style={styles.channelInfo}>
              <Text style={styles.channelName}>Push Notifications</Text>
              <Text style={styles.channelDescription}>Daily check-ins on this device</Text>
            </View>
            <View style={styles.channelStatus}>
              <Text style={styles.channelStatusActive}>✓ Active</Text>
            </View>
          </View>
        </View>

        <Text style={styles.channelHelpText}>
          You can also chat with your companion anytime by opening the app. Push notifications are just a gentle reminder for your daily check-in.
        </Text>
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

      {activeTab === "channels" && renderChannelsTab()}
      {activeTab === "billing" && renderBillingTab()}
      {activeTab === "account" && renderAccountTab()}

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
    fontSize: 14,
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
  channelHelpText: {
    fontSize: 13,
    color: "#666",
    lineHeight: 18,
    paddingHorizontal: 4,
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
  modalOptionText: {
    fontSize: 16,
    color: "#333",
  },
  modalOptionTextSelected: {
    color: "#FF6B6B",
    fontWeight: "600",
  },
  checkmark: {
    fontSize: 18,
    color: "#FF6B6B",
    fontWeight: "600",
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
