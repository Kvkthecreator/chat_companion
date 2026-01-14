import { useState, useEffect } from 'react';

const GUEST_SESSION_KEY = 'ep0_guest_session_id';

interface GuestSessionData {
  guest_session_id: string;
  session_id: string;
  messages_remaining: number;
}

export function useGuestSession() {
  const [guestSessionId, setGuestSessionId] = useState<string | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [messagesRemaining, setMessagesRemaining] = useState<number | null>(null);
  const [isGuest, setIsGuest] = useState(false);

  useEffect(() => {
    // Load guest session ID from localStorage on mount
    const stored = localStorage.getItem(GUEST_SESSION_KEY);
    if (stored) {
      try {
        const data: GuestSessionData = JSON.parse(stored);
        setGuestSessionId(data.guest_session_id);
        setSessionId(data.session_id);
        setMessagesRemaining(data.messages_remaining);
        setIsGuest(true);
      } catch {
        // Invalid data, clear it
        localStorage.removeItem(GUEST_SESSION_KEY);
      }
    }
  }, []);

  const createGuestSession = (data: GuestSessionData) => {
    localStorage.setItem(GUEST_SESSION_KEY, JSON.stringify(data));
    setGuestSessionId(data.guest_session_id);
    setSessionId(data.session_id);
    setMessagesRemaining(data.messages_remaining);
    setIsGuest(true);
  };

  const updateMessagesRemaining = (remaining: number) => {
    setMessagesRemaining(remaining);
    const stored = localStorage.getItem(GUEST_SESSION_KEY);
    if (stored) {
      try {
        const data: GuestSessionData = JSON.parse(stored);
        data.messages_remaining = remaining;
        localStorage.setItem(GUEST_SESSION_KEY, JSON.stringify(data));
      } catch {
        // Ignore errors
      }
    }
  };

  const clearGuestSession = () => {
    localStorage.removeItem(GUEST_SESSION_KEY);
    setGuestSessionId(null);
    setSessionId(null);
    setMessagesRemaining(null);
    setIsGuest(false);
  };

  return {
    guestSessionId,
    sessionId,
    messagesRemaining,
    isGuest,
    createGuestSession,
    updateMessagesRemaining,
    clearGuestSession,
  };
}
