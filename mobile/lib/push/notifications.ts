/**
 * Push Notification Service for Expo
 * Handles registration, permissions, and notification listeners
 */

import * as Notifications from "expo-notifications";
import * as Device from "expo-device";
import Constants from "expo-constants";
import { Platform } from "react-native";
import { api } from "../api/client";

// Configure how notifications are handled when app is in foreground
Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowAlert: true,
    shouldPlaySound: true,
    shouldSetBadge: true,
  }),
});

/**
 * Register for push notifications and save token to backend
 * @returns The Expo push token, or null if registration failed
 */
export async function registerForPushNotifications(): Promise<string | null> {
  // Must be a physical device
  if (!Device.isDevice) {
    console.log("Push notifications require a physical device");
    return null;
  }

  // Check existing permissions
  const { status: existingStatus } = await Notifications.getPermissionsAsync();
  let finalStatus = existingStatus;

  // Request permissions if not granted
  if (existingStatus !== "granted") {
    const { status } = await Notifications.requestPermissionsAsync();
    finalStatus = status;
  }

  if (finalStatus !== "granted") {
    console.log("Push notification permission denied");
    return null;
  }

  try {
    // Get Expo push token
    const projectId = Constants.expoConfig?.extra?.eas?.projectId;
    const tokenData = await Notifications.getExpoPushTokenAsync({
      projectId,
    });
    const pushToken = tokenData.data;

    // Get device info
    const deviceId = Constants.installationId || Device.modelId || "unknown";
    const platform = Platform.OS as "ios" | "android";

    // Register device with backend
    await api.devices.register({
      device_id: deviceId,
      platform,
      push_token: pushToken,
      app_version: Constants.expoConfig?.version,
      os_version: Device.osVersion || undefined,
      device_model: Device.modelName || undefined,
    });

    console.log("Push token registered:", pushToken);

    // Set up Android notification channel
    if (Platform.OS === "android") {
      await setupAndroidChannels();
    }

    return pushToken;
  } catch (error) {
    console.error("Failed to register for push notifications:", error);
    return null;
  }
}

/**
 * Set up Android notification channels
 */
async function setupAndroidChannels(): Promise<void> {
  await Notifications.setNotificationChannelAsync("daily-checkin", {
    name: "Daily Check-ins",
    description: "Daily messages from your companion",
    importance: Notifications.AndroidImportance.HIGH,
    vibrationPattern: [0, 250, 250, 250],
    lightColor: "#FF6B6B",
    sound: "default",
  });

  await Notifications.setNotificationChannelAsync("chat", {
    name: "Chat Messages",
    description: "Real-time chat notifications",
    importance: Notifications.AndroidImportance.DEFAULT,
    sound: "default",
  });
}

/**
 * Update the push token on the backend
 * Call this when the token might have changed
 */
export async function updatePushToken(): Promise<void> {
  try {
    const { status } = await Notifications.getPermissionsAsync();
    if (status !== "granted") return;

    const projectId = Constants.expoConfig?.extra?.eas?.projectId;
    const tokenData = await Notifications.getExpoPushTokenAsync({ projectId });
    const deviceId = Constants.installationId || Device.modelId || "unknown";

    await api.devices.update(deviceId, {
      push_token: tokenData.data,
    });
  } catch (error) {
    console.error("Failed to update push token:", error);
  }
}

/**
 * Unregister device from push notifications
 */
export async function unregisterFromPushNotifications(): Promise<void> {
  try {
    const deviceId = Constants.installationId || Device.modelId || "unknown";
    await api.devices.unregister(deviceId);
  } catch (error) {
    console.error("Failed to unregister from push notifications:", error);
  }
}

/**
 * Set up notification event listeners
 * @param onReceived - Called when notification is received while app is open
 * @param onResponse - Called when user interacts with a notification
 * @returns Cleanup function to remove listeners
 */
export function setupNotificationListeners(
  onReceived: (notification: Notifications.Notification) => void,
  onResponse: (response: Notifications.NotificationResponse) => void
): () => void {
  // Listener for notifications received while app is in foreground
  const receivedSubscription = Notifications.addNotificationReceivedListener(
    onReceived
  );

  // Listener for when user taps on a notification
  const responseSubscription = Notifications.addNotificationResponseReceivedListener(
    async (response) => {
      // Track notification click for analytics
      const notificationId = response.notification.request.content.data?.notification_id;
      if (notificationId) {
        try {
          await api.push.markClicked(notificationId as string);
        } catch (error) {
          console.error("Failed to mark notification as clicked:", error);
        }
      }

      onResponse(response);
    }
  );

  // Return cleanup function
  return () => {
    receivedSubscription.remove();
    responseSubscription.remove();
  };
}

/**
 * Get the last notification response that opened the app
 * Useful for handling deep links from notifications
 */
export async function getLastNotificationResponse(): Promise<Notifications.NotificationResponse | null> {
  return await Notifications.getLastNotificationResponseAsync();
}

/**
 * Clear all delivered notifications
 */
export async function clearAllNotifications(): Promise<void> {
  await Notifications.dismissAllNotificationsAsync();
}

/**
 * Set the app badge count (iOS only)
 */
export async function setBadgeCount(count: number): Promise<void> {
  await Notifications.setBadgeCountAsync(count);
}

/**
 * Get current notification permissions status
 */
export async function getNotificationPermissions(): Promise<Notifications.PermissionStatus> {
  const { status } = await Notifications.getPermissionsAsync();
  return status;
}
