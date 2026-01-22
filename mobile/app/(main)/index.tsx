/**
 * Dashboard / Home Screen
 */

import { useEffect, useState } from "react";
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  RefreshControl,
  ActivityIndicator,
} from "react-native";
import { useRouter } from "expo-router";
import { api, User, MemorySummary, Conversation } from "../../lib/api/client";

export default function DashboardScreen() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [memory, setMemory] = useState<MemorySummary | null>(null);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const loadData = async () => {
    try {
      const [userData, memoryData, conversationsData] = await Promise.all([
        api.users.me(),
        api.memory.getSummary(),
        api.conversations.list({ limit: 3 }),
      ]);
      setUser(userData);
      setMemory(memoryData);
      setConversations(conversationsData);
    } catch (error) {
      console.error("Failed to load dashboard data:", error);
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleRefresh = () => {
    setIsRefreshing(true);
    loadData();
  };

  if (isLoading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#FF6B6B" />
      </View>
    );
  }

  const companionName = user?.companion_name || "Your companion";

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.content}
      refreshControl={
        <RefreshControl
          refreshing={isRefreshing}
          onRefresh={handleRefresh}
          tintColor="#FF6B6B"
        />
      }
    >
      {/* Welcome Card */}
      <View style={styles.card}>
        <Text style={styles.greeting}>
          Hey{user?.display_name ? `, ${user.display_name}` : ""}! 👋
        </Text>
        <Text style={styles.companionIntro}>
          {companionName} is here for you
        </Text>
        <TouchableOpacity
          style={styles.chatButton}
          onPress={() => router.push("/(main)/chat")}
        >
          <Text style={styles.chatButtonText}>Start Chat</Text>
        </TouchableOpacity>
      </View>

      {/* Memory Insight Card */}
      {memory && (memory.thread_count > 0 || memory.fact_count > 0) && (
        <TouchableOpacity
          style={styles.card}
          onPress={() => router.push("/(main)/memory")}
        >
          <Text style={styles.cardTitle}>
            What {companionName} Remembers
          </Text>

          {memory.active_threads.length > 0 && (
            <View style={styles.memorySection}>
              <Text style={styles.memoryLabel}>Active threads</Text>
              {memory.active_threads.slice(0, 2).map((thread) => (
                <View key={thread.id} style={styles.memoryItem}>
                  <Text style={styles.memoryBullet}>•</Text>
                  <Text style={styles.memoryText} numberOfLines={1}>
                    {thread.topic.replace(/_/g, " ")}
                  </Text>
                </View>
              ))}
            </View>
          )}

          {memory.pending_follow_ups.length > 0 && (
            <View style={styles.memorySection}>
              <Text style={styles.memoryLabel}>To follow up on</Text>
              {memory.pending_follow_ups.slice(0, 2).map((followUp) => (
                <View key={followUp.id} style={styles.memoryItem}>
                  <Text style={styles.memoryBullet}>•</Text>
                  <Text style={styles.memoryText} numberOfLines={1}>
                    {followUp.question}
                  </Text>
                </View>
              ))}
            </View>
          )}

          <Text style={styles.viewAll}>View all →</Text>
        </TouchableOpacity>
      )}

      {/* Recent Conversations */}
      {conversations.length > 0 && (
        <View style={styles.card}>
          <Text style={styles.cardTitle}>Recent Chats</Text>
          {conversations.map((conv) => (
            <TouchableOpacity
              key={conv.id}
              style={styles.conversationItem}
              onPress={() => router.push(`/(main)/chat/${conv.id}`)}
            >
              <View style={styles.conversationInfo}>
                <Text style={styles.conversationDate}>
                  {formatDate(conv.started_at)}
                </Text>
                <Text style={styles.conversationMessages}>
                  {conv.message_count} messages
                </Text>
              </View>
              {conv.mood_summary && (
                <Text style={styles.conversationMood} numberOfLines={1}>
                  {conv.mood_summary}
                </Text>
              )}
            </TouchableOpacity>
          ))}
        </View>
      )}

      {/* Daily Check-in Info */}
      <View style={styles.card}>
        <Text style={styles.cardTitle}>Daily Check-in</Text>
        <Text style={styles.scheduleText}>
          {formatSchedule(user)}
        </Text>
        <TouchableOpacity
          style={styles.settingsLink}
          onPress={() => router.push("/(main)/settings")}
        >
          <Text style={styles.settingsLinkText}>Change schedule →</Text>
        </TouchableOpacity>
      </View>
    </ScrollView>
  );
}

function formatDate(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diff = now.getTime() - date.getTime();
  const days = Math.floor(diff / (1000 * 60 * 60 * 24));

  if (days === 0) return "Today";
  if (days === 1) return "Yesterday";
  if (days < 7) return `${days} days ago`;

  return date.toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

function formatSchedule(user: User | null): string {
  if (!user) return "Not set";

  const flexibility = user.message_time_flexibility || "exact";
  const time = user.preferred_message_time || "09:00";
  const window = user.message_time_window;

  if (flexibility === "exact") {
    return `Messages arrive at ${formatTime(time)}`;
  } else if (flexibility === "around") {
    return `Messages arrive around ${formatTime(time)}`;
  } else if (flexibility === "window" && window) {
    const windows: Record<string, string> = {
      morning: "morning (6-10am)",
      midday: "midday (11am-2pm)",
      evening: "evening (5-8pm)",
      night: "night (8-11pm)",
    };
    return `Messages arrive in the ${windows[window]}`;
  }

  return "Not set";
}

function formatTime(time: string): string {
  const [hours, minutes] = time.split(":");
  const hour = parseInt(hours, 10);
  const ampm = hour >= 12 ? "PM" : "AM";
  const displayHour = hour % 12 || 12;
  return `${displayHour}:${minutes} ${ampm}`;
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#F5F5F5",
  },
  content: {
    padding: 16,
  },
  loadingContainer: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
  },
  card: {
    backgroundColor: "#fff",
    borderRadius: 16,
    padding: 20,
    marginBottom: 16,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 8,
    elevation: 2,
  },
  greeting: {
    fontSize: 24,
    fontWeight: "bold",
    color: "#333",
    marginBottom: 4,
  },
  companionIntro: {
    fontSize: 16,
    color: "#666",
    marginBottom: 16,
  },
  chatButton: {
    backgroundColor: "#FF6B6B",
    borderRadius: 12,
    paddingVertical: 14,
    alignItems: "center",
  },
  chatButtonText: {
    color: "#fff",
    fontSize: 16,
    fontWeight: "600",
  },
  cardTitle: {
    fontSize: 18,
    fontWeight: "600",
    color: "#333",
    marginBottom: 12,
  },
  memorySection: {
    marginBottom: 12,
  },
  memoryLabel: {
    fontSize: 12,
    fontWeight: "600",
    color: "#999",
    textTransform: "uppercase",
    marginBottom: 6,
  },
  memoryItem: {
    flexDirection: "row",
    alignItems: "center",
    marginBottom: 4,
  },
  memoryBullet: {
    color: "#FF6B6B",
    marginRight: 8,
    fontSize: 16,
  },
  memoryText: {
    flex: 1,
    fontSize: 14,
    color: "#333",
  },
  viewAll: {
    fontSize: 14,
    color: "#FF6B6B",
    fontWeight: "500",
    marginTop: 8,
  },
  conversationItem: {
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: "#F0F0F0",
  },
  conversationInfo: {
    flexDirection: "row",
    justifyContent: "space-between",
    marginBottom: 4,
  },
  conversationDate: {
    fontSize: 14,
    fontWeight: "500",
    color: "#333",
  },
  conversationMessages: {
    fontSize: 12,
    color: "#999",
  },
  conversationMood: {
    fontSize: 13,
    color: "#666",
  },
  scheduleText: {
    fontSize: 14,
    color: "#666",
    marginBottom: 8,
  },
  settingsLink: {
    paddingTop: 8,
  },
  settingsLinkText: {
    fontSize: 14,
    color: "#FF6B6B",
    fontWeight: "500",
  },
});
