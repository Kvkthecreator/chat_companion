/**
 * Chat Screen
 * Real-time messaging with streaming AI responses
 */

import { useEffect, useState, useRef } from "react";
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TextInput,
  TouchableOpacity,
  KeyboardAvoidingView,
  Platform,
  ActivityIndicator,
} from "react-native";
import { useLocalSearchParams, useNavigation } from "expo-router";
import { api, Message, Conversation, User } from "../../../lib/api/client";

interface DisplayMessage extends Message {
  isStreaming?: boolean;
  streamContent?: string;
}

export default function ChatScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const navigation = useNavigation();
  const flatListRef = useRef<FlatList>(null);

  const [user, setUser] = useState<User | null>(null);
  const [conversation, setConversation] = useState<Conversation | null>(null);
  const [messages, setMessages] = useState<DisplayMessage[]>([]);
  const [inputText, setInputText] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isSending, setIsSending] = useState(false);

  useEffect(() => {
    loadData();
  }, [id]);

  const loadData = async () => {
    try {
      const [userData, conversationData, messagesData] = await Promise.all([
        api.users.me(),
        api.conversations.get(id!),
        api.conversations.getMessages(id!, { limit: 50 }),
      ]);
      setUser(userData);
      setConversation(conversationData);
      setMessages(messagesData.reverse()); // Oldest first

      // Update header title
      const companionName = userData.companion_name || "Chat";
      navigation.setOptions({ title: companionName });
    } catch (error) {
      console.error("Failed to load chat:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSend = async () => {
    if (!inputText.trim() || isSending) return;

    const messageContent = inputText.trim();
    setInputText("");
    setIsSending(true);

    // Optimistically add user message
    const userMessage: DisplayMessage = {
      id: `temp-${Date.now()}`,
      conversation_id: id!,
      role: "user",
      content: messageContent,
      metadata: {},
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMessage]);

    // Add placeholder for AI response
    const aiPlaceholder: DisplayMessage = {
      id: `stream-${Date.now()}`,
      conversation_id: id!,
      role: "assistant",
      content: "",
      streamContent: "",
      isStreaming: true,
      metadata: {},
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, aiPlaceholder]);

    try {
      // Use streaming endpoint
      let fullContent = "";
      for await (const chunk of api.conversations.sendMessageStream(id!, messageContent)) {
        if (chunk.type === "content") {
          fullContent += chunk.content;
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === aiPlaceholder.id
                ? { ...msg, streamContent: fullContent }
                : msg
            )
          );
        } else if (chunk.type === "message_complete") {
          // Replace placeholder with actual message
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === aiPlaceholder.id
                ? {
                    ...chunk.message,
                    isStreaming: false,
                    streamContent: undefined,
                  }
                : msg
            )
          );
        }
      }
    } catch (error) {
      console.error("Failed to send message:", error);
      // Remove AI placeholder on error
      setMessages((prev) => prev.filter((msg) => msg.id !== aiPlaceholder.id));
    } finally {
      setIsSending(false);
    }
  };

  const renderMessage = ({ item }: { item: DisplayMessage }) => {
    const isUser = item.role === "user";
    const displayContent = item.isStreaming
      ? item.streamContent || "..."
      : item.content;

    return (
      <View
        style={[
          styles.messageContainer,
          isUser ? styles.userMessage : styles.assistantMessage,
        ]}
      >
        <Text
          style={[
            styles.messageText,
            isUser ? styles.userMessageText : styles.assistantMessageText,
          ]}
        >
          {displayContent}
        </Text>
        {item.isStreaming && (
          <View style={styles.typingIndicator}>
            <Text style={styles.typingDot}>●</Text>
          </View>
        )}
      </View>
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
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === "ios" ? "padding" : undefined}
      keyboardVerticalOffset={Platform.OS === "ios" ? 90 : 0}
    >
      {/* Messages */}
      <FlatList
        ref={flatListRef}
        data={messages}
        keyExtractor={(item) => item.id}
        renderItem={renderMessage}
        contentContainerStyle={styles.messagesList}
        onContentSizeChange={() =>
          flatListRef.current?.scrollToEnd({ animated: true })
        }
        onLayout={() =>
          flatListRef.current?.scrollToEnd({ animated: false })
        }
        ListEmptyComponent={
          <View style={styles.emptyContainer}>
            <Text style={styles.emptyText}>
              Say hello to {user?.companion_name || "your companion"}!
            </Text>
          </View>
        }
      />

      {/* Input */}
      <View style={styles.inputContainer}>
        <TextInput
          style={styles.textInput}
          value={inputText}
          onChangeText={setInputText}
          placeholder="Type a message..."
          placeholderTextColor="#999"
          multiline
          maxLength={2000}
          editable={!isSending}
        />
        <TouchableOpacity
          style={[
            styles.sendButton,
            (!inputText.trim() || isSending) && styles.sendButtonDisabled,
          ]}
          onPress={handleSend}
          disabled={!inputText.trim() || isSending}
        >
          {isSending ? (
            <ActivityIndicator size="small" color="#fff" />
          ) : (
            <Text style={styles.sendButtonText}>↑</Text>
          )}
        </TouchableOpacity>
      </View>
    </KeyboardAvoidingView>
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
  messagesList: {
    padding: 16,
    paddingBottom: 8,
  },
  messageContainer: {
    maxWidth: "80%",
    padding: 12,
    borderRadius: 16,
    marginBottom: 8,
  },
  userMessage: {
    alignSelf: "flex-end",
    backgroundColor: "#FF6B6B",
    borderBottomRightRadius: 4,
  },
  assistantMessage: {
    alignSelf: "flex-start",
    backgroundColor: "#fff",
    borderBottomLeftRadius: 4,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 1,
  },
  messageText: {
    fontSize: 16,
    lineHeight: 22,
  },
  userMessageText: {
    color: "#fff",
  },
  assistantMessageText: {
    color: "#333",
  },
  typingIndicator: {
    marginTop: 4,
  },
  typingDot: {
    fontSize: 8,
    color: "#FF6B6B",
  },
  emptyContainer: {
    padding: 48,
    alignItems: "center",
  },
  emptyText: {
    fontSize: 16,
    color: "#666",
    textAlign: "center",
  },
  inputContainer: {
    flexDirection: "row",
    padding: 12,
    paddingBottom: Platform.OS === "ios" ? 28 : 12,
    backgroundColor: "#fff",
    borderTopWidth: 1,
    borderTopColor: "#E5E5E5",
    alignItems: "flex-end",
  },
  textInput: {
    flex: 1,
    backgroundColor: "#F5F5F5",
    borderRadius: 20,
    paddingHorizontal: 16,
    paddingVertical: 10,
    fontSize: 16,
    maxHeight: 100,
    marginRight: 8,
  },
  sendButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: "#FF6B6B",
    alignItems: "center",
    justifyContent: "center",
  },
  sendButtonDisabled: {
    backgroundColor: "#CCC",
  },
  sendButtonText: {
    color: "#fff",
    fontSize: 20,
    fontWeight: "bold",
  },
});
