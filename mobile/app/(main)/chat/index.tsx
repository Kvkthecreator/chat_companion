/**
 * Conversation List / New Chat Screen
 */

import { useEffect, useState, useCallback } from "react";
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  RefreshControl,
  ActivityIndicator,
} from "react-native";
import { useRouter, useFocusEffect } from "expo-router";
import { api, Conversation } from "../../../lib/api/client";

export default function ConversationListScreen() {
  const router = useRouter();
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isCreating, setIsCreating] = useState(false);

  const loadConversations = async () => {
    try {
      const data = await api.conversations.list({ limit: 20 });
      setConversations(data);
    } catch (error) {
      console.error("Failed to load conversations:", error);
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  };

  // Reload when screen comes into focus
  useFocusEffect(
    useCallback(() => {
      loadConversations();
    }, [])
  );

  const handleRefresh = () => {
    setIsRefreshing(true);
    loadConversations();
  };

  const handleNewChat = async () => {
    setIsCreating(true);
    try {
      const conversation = await api.conversations.create("mobile");
      router.push(`/(main)/chat/${conversation.id}`);
    } catch (error) {
      console.error("Failed to create conversation:", error);
    } finally {
      setIsCreating(false);
    }
  };

  const renderConversation = ({ item }: { item: Conversation }) => (
    <TouchableOpacity
      style={styles.conversationItem}
      onPress={() => router.push(`/(main)/chat/${item.id}`)}
    >
      <View style={styles.conversationHeader}>
        <Text style={styles.conversationDate}>
          {formatDate(item.started_at)}
        </Text>
        <Text style={styles.messageCount}>
          {item.message_count} messages
        </Text>
      </View>
      {item.mood_summary && (
        <Text style={styles.moodSummary} numberOfLines={2}>
          {item.mood_summary}
        </Text>
      )}
      {item.topics.length > 0 && (
        <View style={styles.topicsContainer}>
          {item.topics.slice(0, 3).map((topic, index) => (
            <View key={index} style={styles.topicTag}>
              <Text style={styles.topicText}>{topic}</Text>
            </View>
          ))}
        </View>
      )}
    </TouchableOpacity>
  );

  if (isLoading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#FF6B6B" />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {/* New Chat Button */}
      <TouchableOpacity
        style={[styles.newChatButton, isCreating && styles.buttonDisabled]}
        onPress={handleNewChat}
        disabled={isCreating}
      >
        {isCreating ? (
          <ActivityIndicator color="#fff" />
        ) : (
          <Text style={styles.newChatButtonText}>+ New Conversation</Text>
        )}
      </TouchableOpacity>

      {/* Conversation List */}
      <FlatList
        data={conversations}
        keyExtractor={(item) => item.id}
        renderItem={renderConversation}
        contentContainerStyle={styles.listContent}
        refreshControl={
          <RefreshControl
            refreshing={isRefreshing}
            onRefresh={handleRefresh}
            tintColor="#FF6B6B"
          />
        }
        ListEmptyComponent={
          <View style={styles.emptyContainer}>
            <Text style={styles.emptyText}>No conversations yet</Text>
            <Text style={styles.emptySubtext}>
              Start a new chat to talk with your companion
            </Text>
          </View>
        }
      />
    </View>
  );
}

function formatDate(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diff = now.getTime() - date.getTime();
  const days = Math.floor(diff / (1000 * 60 * 60 * 24));

  if (days === 0) {
    return date.toLocaleTimeString("en-US", {
      hour: "numeric",
      minute: "2-digit",
    });
  }
  if (days === 1) return "Yesterday";
  if (days < 7) {
    return date.toLocaleDateString("en-US", { weekday: "long" });
  }

  return date.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
  });
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
  newChatButton: {
    backgroundColor: "#FF6B6B",
    margin: 16,
    borderRadius: 12,
    paddingVertical: 16,
    alignItems: "center",
  },
  buttonDisabled: {
    opacity: 0.7,
  },
  newChatButtonText: {
    color: "#fff",
    fontSize: 16,
    fontWeight: "600",
  },
  listContent: {
    paddingHorizontal: 16,
    paddingBottom: 16,
  },
  conversationItem: {
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
  conversationHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 8,
  },
  conversationDate: {
    fontSize: 14,
    fontWeight: "600",
    color: "#333",
  },
  messageCount: {
    fontSize: 12,
    color: "#999",
  },
  moodSummary: {
    fontSize: 14,
    color: "#666",
    lineHeight: 20,
  },
  topicsContainer: {
    flexDirection: "row",
    flexWrap: "wrap",
    marginTop: 8,
  },
  topicTag: {
    backgroundColor: "#F0F0F0",
    borderRadius: 12,
    paddingHorizontal: 10,
    paddingVertical: 4,
    marginRight: 6,
    marginBottom: 4,
  },
  topicText: {
    fontSize: 12,
    color: "#666",
  },
  emptyContainer: {
    padding: 48,
    alignItems: "center",
  },
  emptyText: {
    fontSize: 18,
    fontWeight: "600",
    color: "#333",
    marginBottom: 8,
  },
  emptySubtext: {
    fontSize: 14,
    color: "#666",
    textAlign: "center",
  },
});
