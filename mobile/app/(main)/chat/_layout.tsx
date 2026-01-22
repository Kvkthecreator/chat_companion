/**
 * Chat Stack Layout
 */

import { Stack } from "expo-router";

export default function ChatLayout() {
  return (
    <Stack
      screenOptions={{
        headerStyle: {
          backgroundColor: "#fff",
        },
        headerTitleStyle: {
          fontWeight: "600",
        },
        headerBackTitleVisible: false,
      }}
    >
      <Stack.Screen
        name="index"
        options={{
          title: "Conversations",
        }}
      />
      <Stack.Screen
        name="[id]"
        options={{
          title: "Chat",
        }}
      />
    </Stack>
  );
}
