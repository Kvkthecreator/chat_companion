/**
 * Memory Management Screen
 */

import { useEffect, useState, useCallback } from "react";
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  RefreshControl,
  ActivityIndicator,
  Alert,
} from "react-native";
import { useFocusEffect } from "expo-router";
import {
  api,
  User,
  FullMemory,
  ThreadSummary,
  FollowUpSummary,
  FactItem,
  PatternItem,
} from "../../lib/api/client";

export default function MemoryScreen() {
  const [user, setUser] = useState<User | null>(null);
  const [memory, setMemory] = useState<FullMemory | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [expandedThreads, setExpandedThreads] = useState<Set<string>>(new Set());

  const loadData = async () => {
    try {
      const [userData, memoryData] = await Promise.all([
        api.users.me(),
        api.memory.getFull(),
      ]);
      setUser(userData);
      setMemory(memoryData);
    } catch (error) {
      console.error("Failed to load memory:", error);
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

  const handleDeleteItem = (id: string, type: string) => {
    const companionName = user?.companion_name || "Your companion";
    Alert.alert(
      "Delete Memory",
      `${companionName} will no longer remember this. Are you sure?`,
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
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.title}>What {companionName} Remembers</Text>
        <Text style={styles.subtitle}>
          Everything {companionName} is paying attention to
        </Text>
      </View>

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
    </ScrollView>
  );
}

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
    <View style={styles.card}>
      <TouchableOpacity onPress={onToggle} style={styles.cardHeader}>
        <Text style={styles.expandIcon}>{isExpanded ? "▼" : "▶"}</Text>
        <View style={styles.cardContent}>
          <Text style={styles.cardTitle}>
            {thread.topic.replace(/_/g, " ")}
          </Text>
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
        <TouchableOpacity onPress={onDelete} style={styles.deleteButton}>
          <Text style={styles.deleteButtonText}>Delete</Text>
        </TouchableOpacity>
      </View>

      {isResolved && (
        <Text style={styles.resolvedBadge}>Resolved</Text>
      )}
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
    <View style={styles.card}>
      <View style={styles.cardContent}>
        <Text style={styles.cardTitle}>{followUp.question}</Text>
        <Text style={styles.cardSubtitle}>{followUp.context}</Text>
      </View>
      <TouchableOpacity onPress={onDelete} style={styles.deleteButton}>
        <Text style={styles.deleteButtonText}>Delete</Text>
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
          <TouchableOpacity
            onPress={() => onDelete(fact.id)}
            style={styles.factDeleteButton}
          >
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
  content: {
    padding: 16,
  },
  loadingContainer: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
  },
  header: {
    marginBottom: 24,
  },
  title: {
    fontSize: 24,
    fontWeight: "bold",
    color: "#333",
    marginBottom: 4,
  },
  subtitle: {
    fontSize: 14,
    color: "#666",
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
  deleteButton: {},
  deleteButtonText: {
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
});
