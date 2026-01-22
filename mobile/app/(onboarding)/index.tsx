/**
 * Chat-based Onboarding Screen
 * Mirrors the web onboarding experience
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
  SafeAreaView,
} from "react-native";
import { useRouter } from "expo-router";
import * as Localization from "expo-localization";
import { api, ChatOnboardingState } from "../../lib/api/client";
import { registerForPushNotifications } from "../../lib/push/notifications";

interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  options?: string[];
}

export default function OnboardingScreen() {
  const router = useRouter();
  const flatListRef = useRef<FlatList>(null);

  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputText, setInputText] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isSending, setIsSending] = useState(false);
  const [currentOptions, setCurrentOptions] = useState<string[]>([]);
  const [isComplete, setIsComplete] = useState(false);

  useEffect(() => {
    initOnboarding();
  }, []);

  const initOnboarding = async () => {
    try {
      // Try to detect timezone and set it
      const timezone = Localization.timezone;
      if (timezone) {
        await api.users.update({ timezone }).catch(() => {});
      }

      // Get current onboarding state
      const state = await api.onboarding.chat.getState();

      if (state.is_complete) {
        // Already completed, go to main app
        router.replace("/(main)");
        return;
      }

      if (state.message) {
        setMessages([
          {
            id: "welcome",
            role: "assistant",
            content: state.message,
            options: state.options,
          },
        ]);
        setCurrentOptions(state.options || []);
      }
    } catch (error) {
      console.error("Failed to init onboarding:", error);
      // Show a default welcome message
      setMessages([
        {
          id: "welcome",
          role: "assistant",
          content: "Hi there! I'm so glad you're here. I'm going to be your daily companion - someone who checks in on you and remembers what matters to you. Let's get to know each other a bit. What should I call you?",
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSend = async (text?: string) => {
    const messageText = text || inputText.trim();
    if (!messageText || isSending) return;

    setInputText("");
    setCurrentOptions([]);
    setIsSending(true);

    // Add user message
    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      role: "user",
      content: messageText,
    };
    setMessages((prev) => [...prev, userMessage]);

    try {
      const result = await api.onboarding.chat.respond(messageText);

      if (result.success) {
        if (result.next_message) {
          const assistantMessage: ChatMessage = {
            id: `assistant-${Date.now()}`,
            role: "assistant",
            content: result.next_message,
            options: result.options,
          };
          setMessages((prev) => [...prev, assistantMessage]);
          setCurrentOptions(result.options || []);
        }

        if (result.is_complete) {
          setIsComplete(true);
          // Request push notification permission
          await registerForPushNotifications();
          // Navigate to main app after a short delay
          setTimeout(() => {
            router.replace("/(main)");
          }, 2000);
        }
      } else if (result.retry_message) {
        // Validation failed, show retry message
        const retryMessage: ChatMessage = {
          id: `retry-${Date.now()}`,
          role: "assistant",
          content: result.retry_message,
          options: result.options,
        };
        setMessages((prev) => [...prev, retryMessage]);
        setCurrentOptions(result.options || []);
      }
    } catch (error) {
      console.error("Failed to send response:", error);
      const errorMessage: ChatMessage = {
        id: `error-${Date.now()}`,
        role: "assistant",
        content: "Sorry, something went wrong. Could you try that again?",
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsSending(false);
    }
  };

  const handleOptionSelect = (option: string) => {
    handleSend(option);
  };

  const renderMessage = ({ item }: { item: ChatMessage }) => {
    const isUser = item.role === "user";

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
          {item.content}
        </Text>
      </View>
    );
  };

  if (isLoading) {
    return (
      <SafeAreaView style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#FF6B6B" />
        <Text style={styles.loadingText}>Setting things up...</Text>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <KeyboardAvoidingView
        style={styles.keyboardView}
        behavior={Platform.OS === "ios" ? "padding" : undefined}
        keyboardVerticalOffset={Platform.OS === "ios" ? 0 : 0}
      >
        {/* Header */}
        <View style={styles.header}>
          <Text style={styles.headerTitle}>Welcome to Daisy</Text>
          <Text style={styles.headerSubtitle}>Let's get to know each other</Text>
        </View>

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
        />

        {/* Quick Options */}
        {currentOptions.length > 0 && !isSending && (
          <View style={styles.optionsContainer}>
            {currentOptions.map((option, index) => (
              <TouchableOpacity
                key={index}
                style={styles.optionButton}
                onPress={() => handleOptionSelect(option)}
              >
                <Text style={styles.optionButtonText}>{option}</Text>
              </TouchableOpacity>
            ))}
          </View>
        )}

        {/* Completion Message */}
        {isComplete && (
          <View style={styles.completionContainer}>
            <Text style={styles.completionText}>
              ✨ All set! Taking you to your dashboard...
            </Text>
          </View>
        )}

        {/* Input */}
        {!isComplete && (
          <View style={styles.inputContainer}>
            <TextInput
              style={styles.textInput}
              value={inputText}
              onChangeText={setInputText}
              placeholder="Type your response..."
              placeholderTextColor="#999"
              multiline
              maxLength={500}
              editable={!isSending}
              onSubmitEditing={() => handleSend()}
              returnKeyType="send"
            />
            <TouchableOpacity
              style={[
                styles.sendButton,
                (!inputText.trim() || isSending) && styles.sendButtonDisabled,
              ]}
              onPress={() => handleSend()}
              disabled={!inputText.trim() || isSending}
            >
              {isSending ? (
                <ActivityIndicator size="small" color="#fff" />
              ) : (
                <Text style={styles.sendButtonText}>↑</Text>
              )}
            </TouchableOpacity>
          </View>
        )}
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#fff",
  },
  loadingContainer: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "#fff",
  },
  loadingText: {
    marginTop: 16,
    fontSize: 16,
    color: "#666",
  },
  keyboardView: {
    flex: 1,
  },
  header: {
    paddingHorizontal: 20,
    paddingTop: 20,
    paddingBottom: 16,
    borderBottomWidth: 1,
    borderBottomColor: "#F0F0F0",
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: "bold",
    color: "#FF6B6B",
    marginBottom: 4,
  },
  headerSubtitle: {
    fontSize: 14,
    color: "#666",
  },
  messagesList: {
    padding: 16,
    paddingBottom: 8,
  },
  messageContainer: {
    maxWidth: "85%",
    padding: 14,
    borderRadius: 18,
    marginBottom: 10,
  },
  userMessage: {
    alignSelf: "flex-end",
    backgroundColor: "#FF6B6B",
    borderBottomRightRadius: 4,
  },
  assistantMessage: {
    alignSelf: "flex-start",
    backgroundColor: "#F5F5F5",
    borderBottomLeftRadius: 4,
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
  optionsContainer: {
    flexDirection: "row",
    flexWrap: "wrap",
    paddingHorizontal: 16,
    paddingBottom: 8,
  },
  optionButton: {
    backgroundColor: "#FFF0F0",
    borderWidth: 1,
    borderColor: "#FF6B6B",
    borderRadius: 20,
    paddingHorizontal: 16,
    paddingVertical: 10,
    marginRight: 8,
    marginBottom: 8,
  },
  optionButtonText: {
    color: "#FF6B6B",
    fontSize: 14,
    fontWeight: "500",
  },
  completionContainer: {
    padding: 20,
    alignItems: "center",
  },
  completionText: {
    fontSize: 16,
    color: "#4CAF50",
    fontWeight: "500",
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
