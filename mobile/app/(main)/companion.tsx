/**
 * Companion Screen - Memory + Personality tabs
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
  RefreshControl,
} from "react-native";
import { useFocusEffect } from "expo-router";
import * as Localization from "expo-localization";
import DateTimePicker from "@react-native-community/datetimepicker";
import {
  api,
  User,
  FullMemory,
  ThreadSummary,
  FollowUpSummary,
  FactItem,
} from "../../lib/api/client";

// Timezone regions (same as settings)
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
      { value: "America/Toronto", label: "Toronto (ET)", offset: -5 },
      { value: "America/Vancouver", label: "Vancouver (PT)", offset: -8 },
      { value: "America/Mexico_City", label: "Mexico City (CST)", offset: -6 },
      { value: "America/Sao_Paulo", label: "São Paulo (BRT)", offset: -3 },
    ],
  },
  {
    region: "Europe",
    timezones: [
      { value: "Europe/London", label: "London (GMT/BST)", offset: 0 },
      { value: "Europe/Paris", label: "Paris (CET)", offset: 1 },
      { value: "Europe/Berlin", label: "Berlin (CET)", offset: 1 },
      { value: "Europe/Amsterdam", label: "Amsterdam (CET)", offset: 1 },
      { value: "Europe/Moscow", label: "Moscow (MSK)", offset: 3 },
    ],
  },
  {
    region: "Asia",
    timezones: [
      { value: "Asia/Tokyo", label: "Tokyo (JST)", offset: 9 },
      { value: "Asia/Seoul", label: "Seoul (KST)", offset: 9 },
      { value: "Asia/Shanghai", label: "Shanghai (CST)", offset: 8 },
      { value: "Asia/Hong_Kong", label: "Hong Kong (HKT)", offset: 8 },
      { value: "Asia/Singapore", label: "Singapore (SGT)", offset: 8 },
      { value: "Asia/Bangkok", label: "Bangkok (ICT)", offset: 7 },
      { value: "Asia/Kolkata", label: "India (IST)", offset: 5.5 },
      { value: "Asia/Dubai", label: "Dubai (GST)", offset: 4 },
    ],
  },
  {
    region: "Pacific",
    timezones: [
      { value: "Australia/Sydney", label: "Sydney (AEST)", offset: 10 },
      { value: "Australia/Melbourne", label: "Melbourne (AEST)", offset: 10 },
      { value: "Pacific/Auckland", label: "Auckland (NZST)", offset: 12 },
    ],
  },
  {
    region: "Other",
    timezones: [
      { value: "UTC", label: "UTC (Coordinated Universal Time)", offset: 0 },
    ],
  },
];

const ALL_TIMEZONES = TIMEZONE_REGIONS.flatMap((r) => r.timezones);

const SUPPORT_STYLES = [
  { value: "motivational", label: "Motivational", description: "Encouraging and energizing" },
  { value: "friendly_checkin", label: "Friendly Check-in", description: "Warm and casual, like a close friend" },
  { value: "accountability", label: "Accountability", description: "Supportive but direct about goals" },
  { value: "listener", label: "Listener", description: "Gentle and present, space to share" },
];

type TabType = "memory" | "personality";

export default function CompanionScreen() {
  const [activeTab, setActiveTab] = useState<TabType>("memory");
  const [user, setUser] = useState<User | null>(null);
  const [memory, setMemory] = useState<FullMemory | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isSaving, setIsSaving] = useState(false);

  // Personality form state
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
  const [timezoneSearch, setTimezoneSearch] = useState("");

  // Memory states
  const [expandedThreads, setExpandedThreads] = useState<Set<string>>(new Set());
  const [deleteItemId, setDeleteItemId] = useState<string | null>(null);

  const deviceTimezone = useMemo(() => Localization.timezone || "UTC", []);

  const filteredTimezones = useMemo(() => {
    if (!timezoneSearch.trim()) return TIMEZONE_REGIONS;
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

  const getTimezoneLabel = (value: string): string => {
    const found = ALL_TIMEZONES.find((tz) => tz.value === value);
    if (found) return found.label;
    return value.replace(/_/g, " ").replace(/\//g, " / ");
  };

  const loadData = async () => {
    try {
      const [userData, memoryData] = await Promise.all([
        api.users.me(),
        api.memory.getFull(),
      ]);
      setUser(userData);
      setMemory(memoryData);

      // Populate form
      setCompanionName(userData.companion_name || "");
      setTimezone(userData.timezone || deviceTimezone);
      setPreferredTime(userData.preferred_message_time || "09:00");
      setTimeFlexibility(userData.message_time_flexibility || "exact");
      setTimeWindow(userData.message_time_window || "morning");
      setSupportStyle(userData.support_style || "friendly_checkin");
    } catch (error) {
      console.error("Failed to load data:", error);
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  };

  useFocusEffect(
    useCallback(() => {
      loadData();
    }, [])
  );

  const handleRefresh = () => {
    setIsRefreshing(true);
    loadData();
  };

  const handleSavePersonality = async () => {
    setIsSaving(true);
    try {
      await api.users.update({
        companion_name: companionName,
        timezone,
        preferred_message_time: preferredTime,
        support_style: supportStyle,
      });
      Alert.alert("Saved", "Your companion settings have been updated");
      loadData();
    } catch (error) {
      console.error("Failed to save:", error);
      Alert.alert("Error", "Failed to save changes");
    } finally {
      setIsSaving(false);
    }
  };

  const handleUseDeviceTimezone = async () => {
    setTimezone(deviceTimezone);
    setShowTimezoneModal(false);
    setIsSaving(true);
    try {
      await api.users.update({ timezone: deviceTimezone });
    } catch (error) {
      console.error("Failed to save timezone:", error);
    } finally {
      setIsSaving(false);
    }
  };

  const handleDeleteItem = (id: string, type: string) => {
    const companionDisplayName = user?.companion_name || "Your companion";
    Alert.alert(
      "Delete Memory",
      `${companionDisplayName} will no longer remember this. Are you sure?`,
      [
        { text: "Cancel", style: "cancel" },
        {
          text: "Delete",
          style: "destructive",
          onPress: async () => {
            try {
              await api.memory.deleteItem(id);
              loadData();
            } catch (error) {
              console.error("Failed to delete:", error);
            }
          },
        },
      ]
    );
  };

  const handleResolveThread = async (threadId: string) => {
    try {
      await api.memory.resolveThread(threadId);
      loadData();
    } catch (error) {
      console.error("Failed to resolve thread:", error);
    }
  };

  const toggleThread = (threadId: string) => {
    setExpandedThreads((prev) => {
      const next = new Set(prev);
      if (next.has(threadId)) {
        next.delete(threadId);
      } else {
        next.add(threadId);
      }
      return next;
    });
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

  const companionDisplayName = user?.companion_name || "Your Companion";

  const renderTabs = () => (
    <View style={styles.tabContainer}>
      <TouchableOpacity
        style={[styles.tab, activeTab === "memory" && styles.tabActive]}
        onPress={() => setActiveTab("memory")}
      >
        <Text style={[styles.tabText, activeTab === "memory" && styles.tabTextActive]}>
          🧠 Memory
        </Text>
      </TouchableOpacity>
      <TouchableOpacity
        style={[styles.tab, activeTab === "personality" && styles.tabActive]}
        onPress={() => setActiveTab("personality")}
      >
        <Text style={[styles.tabText, activeTab === "personality" && styles.tabTextActive]}>
          ✨ Personality
        </Text>
      </TouchableOpacity>
    </View>
  );

  const renderMemoryTab = () => (
    <ScrollView
      style={styles.tabContent}
      showsVerticalScrollIndicator={false}
      refreshControl={
        <RefreshControl
          refreshing={isRefreshing}
          onRefresh={handleRefresh}
          tintColor="#FF6B6B"
        />
      }
    >
      {/* Active Threads */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>🎯 Active Threads</Text>
        {memory?.threads.length === 0 ? (
          <Text style={styles.emptyText}>
            No active threads. As we chat about things happening in your life,
            I'll keep track of them here.
          </Text>
        ) : (
          memory?.threads.map((thread) => (
            <ThreadCard
              key={thread.id}
              thread={thread}
              isExpanded={expandedThreads.has(thread.id)}
              onToggle={() => toggleThread(thread.id)}
              onResolve={() => handleResolveThread(thread.id)}
              onDelete={() => handleDeleteItem(thread.id, "thread")}
            />
          ))
        )}
      </View>

      {/* Follow-ups */}
      {memory && memory.follow_ups.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>❓ Things to Follow Up On</Text>
          {memory.follow_ups.map((followUp) => (
            <FollowUpCard
              key={followUp.id}
              followUp={followUp}
              onDelete={() => handleDeleteItem(followUp.id, "follow_up")}
            />
          ))}
        </View>
      )}

      {/* Facts */}
      {memory && Object.keys(memory.facts).length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>👤 Things I Know About You</Text>
          {Object.entries(memory.facts).map(([category, facts]) => (
            <FactGroup
              key={category}
              category={category}
              facts={facts}
              onDelete={(id) => handleDeleteItem(id, "fact")}
            />
          ))}
        </View>
      )}

      {/* Patterns */}
      {memory && memory.patterns.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>💡 Patterns I've Noticed</Text>
          <Text style={styles.patternsNote}>
            These are observations, not facts. They help me know when to check
            in differently.
          </Text>
          {memory.patterns.map((pattern) => (
            <View key={pattern.id} style={styles.patternItem}>
              <Text style={styles.patternBullet}>•</Text>
              <Text style={styles.patternText}>{pattern.description}</Text>
            </View>
          ))}
        </View>
      )}

      <View style={{ height: 40 }} />
    </ScrollView>
  );

  const renderPersonalityTab = () => (
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
            onPress={handleSavePersonality}
            disabled={isSaving}
          >
            {isSaving ? (
              <ActivityIndicator size="small" color="#fff" />
            ) : (
              <Text style={styles.buttonText}>Save Changes</Text>
            )}
          </TouchableOpacity>
        </View>
      </View>

      <View style={{ height: 40 }} />
    </ScrollView>
  );

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>✨ {companionDisplayName}</Text>
        <Text style={styles.headerSubtitle}>Customize your companion</Text>
      </View>

      {renderTabs()}

      {activeTab === "memory" && renderMemoryTab()}
      {activeTab === "personality" && renderPersonalityTab()}

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

          <View style={styles.searchContainer}>
            <TextInput
              style={styles.searchInput}
              value={timezoneSearch}
              onChangeText={setTimezoneSearch}
              placeholder="Search cities or timezones..."
              placeholderTextColor="#999"
            />
          </View>

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
                    <Text style={[styles.modalOptionText, timezone === tz.value && styles.modalOptionTextSelected]}>
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
                  <Text style={[styles.modalOptionText, supportStyle === style.value && styles.modalOptionTextSelected]}>
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
                  if (date) setPreferredTime(formatTimeFromDate(date));
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
    </View>
  );
}

// Sub-components
function ThreadCard({
  thread,
  isExpanded,
  onToggle,
  onResolve,
  onDelete,
}: {
  thread: ThreadSummary;
  isExpanded: boolean;
  onToggle: () => void;
  onResolve: () => void;
  onDelete: () => void;
}) {
  const isResolved = thread.status === "resolved";

  return (
    <View style={styles.memoryCard}>
      <TouchableOpacity onPress={onToggle} style={styles.cardHeader}>
        <Text style={styles.expandIcon}>{isExpanded ? "▼" : "▶"}</Text>
        <View style={styles.cardContent}>
          <Text style={styles.cardTitle}>{thread.topic.replace(/_/g, " ")}</Text>
          <Text style={styles.cardSubtitle}>{thread.summary}</Text>
        </View>
      </TouchableOpacity>

      {isExpanded && thread.key_details.length > 0 && (
        <View style={styles.detailsContainer}>
          <Text style={styles.detailsLabel}>Details:</Text>
          {thread.key_details.map((detail, i) => (
            <Text key={i} style={styles.detailItem}>• {detail}</Text>
          ))}
        </View>
      )}

      <View style={styles.cardActions}>
        {!isResolved && (
          <TouchableOpacity onPress={onResolve} style={styles.actionButton}>
            <Text style={styles.actionButtonText}>✓ Resolve</Text>
          </TouchableOpacity>
        )}
        <TouchableOpacity onPress={onDelete} style={styles.deleteActionButton}>
          <Text style={styles.deleteActionText}>Delete</Text>
        </TouchableOpacity>
      </View>

      {isResolved && <Text style={styles.resolvedBadge}>Resolved</Text>}
    </View>
  );
}

function FollowUpCard({
  followUp,
  onDelete,
}: {
  followUp: FollowUpSummary;
  onDelete: () => void;
}) {
  return (
    <View style={styles.memoryCard}>
      <View style={styles.cardContent}>
        <Text style={styles.cardTitle}>{followUp.question}</Text>
        <Text style={styles.cardSubtitle}>{followUp.context}</Text>
      </View>
      <TouchableOpacity onPress={onDelete} style={styles.deleteActionButton}>
        <Text style={styles.deleteActionText}>Delete</Text>
      </TouchableOpacity>
    </View>
  );
}

function FactGroup({
  category,
  facts,
  onDelete,
}: {
  category: string;
  facts: FactItem[];
  onDelete: (id: string) => void;
}) {
  return (
    <View style={styles.factGroup}>
      <Text style={styles.factCategory}>{category}</Text>
      {facts.map((fact) => (
        <View key={fact.id} style={styles.factItem}>
          <Text style={styles.factValue}>{fact.value}</Text>
          <TouchableOpacity onPress={() => onDelete(fact.id)} style={styles.factDeleteButton}>
            <Text style={styles.factDeleteText}>×</Text>
          </TouchableOpacity>
        </View>
      ))}
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
  header: {
    backgroundColor: "#fff",
    padding: 16,
    paddingTop: 8,
    borderBottomWidth: 1,
    borderBottomColor: "#E5E5E5",
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: "bold",
    color: "#333",
  },
  headerSubtitle: {
    fontSize: 14,
    color: "#666",
    marginTop: 2,
  },
  tabContainer: {
    flexDirection: "row",
    backgroundColor: "#fff",
    paddingHorizontal: 16,
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
    padding: 16,
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
  emptyText: {
    fontSize: 14,
    color: "#666",
    fontStyle: "italic",
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
  // Memory cards
  memoryCard: {
    backgroundColor: "#fff",
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 1,
  },
  cardHeader: {
    flexDirection: "row",
    alignItems: "flex-start",
  },
  expandIcon: {
    fontSize: 12,
    color: "#999",
    marginRight: 8,
    marginTop: 4,
  },
  cardContent: {
    flex: 1,
  },
  cardTitle: {
    fontSize: 16,
    fontWeight: "600",
    color: "#333",
    marginBottom: 4,
    textTransform: "capitalize",
  },
  cardSubtitle: {
    fontSize: 14,
    color: "#666",
  },
  detailsContainer: {
    marginTop: 12,
    paddingLeft: 20,
  },
  detailsLabel: {
    fontSize: 12,
    fontWeight: "600",
    color: "#999",
    marginBottom: 4,
  },
  detailItem: {
    fontSize: 14,
    color: "#666",
    marginBottom: 2,
  },
  cardActions: {
    flexDirection: "row",
    marginTop: 12,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: "#F0F0F0",
  },
  actionButton: {
    marginRight: 16,
  },
  actionButtonText: {
    fontSize: 14,
    color: "#4CAF50",
    fontWeight: "500",
  },
  deleteActionButton: {},
  deleteActionText: {
    fontSize: 14,
    color: "#FF6B6B",
    fontWeight: "500",
  },
  resolvedBadge: {
    fontSize: 12,
    color: "#999",
    marginTop: 8,
  },
  factGroup: {
    marginBottom: 16,
  },
  factCategory: {
    fontSize: 14,
    fontWeight: "600",
    color: "#333",
    marginBottom: 8,
    textTransform: "capitalize",
  },
  factItem: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: "#fff",
    borderRadius: 8,
    padding: 12,
    marginBottom: 6,
  },
  factValue: {
    flex: 1,
    fontSize: 14,
    color: "#666",
  },
  factDeleteButton: {
    paddingHorizontal: 8,
  },
  factDeleteText: {
    fontSize: 18,
    color: "#999",
  },
  patternsNote: {
    fontSize: 13,
    color: "#666",
    marginBottom: 12,
    fontStyle: "italic",
  },
  patternItem: {
    flexDirection: "row",
    alignItems: "flex-start",
    marginBottom: 8,
  },
  patternBullet: {
    color: "#FF6B6B",
    marginRight: 8,
  },
  patternText: {
    flex: 1,
    fontSize: 14,
    color: "#333",
  },
  // Form styles
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
  // Modal styles
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
});
