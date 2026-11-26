import { useState, useEffect, useCallback } from "react";
import { sendChatMessage } from "../services/chatService";
import {
  fetchChatHistory,
  deleteChatHistory,
  getSavedSessions,
  persistSessions,
} from "../services/historyService";
import { fetchRecentNews } from "../services/newsService";
import type { ChatMessage, ChatSession, TrendingArticle } from "../types/chat";

// Bulletproof UUID generator that never fails in insecure origins or older web views
const generateUUID = (): string => {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    try {
      return crypto.randomUUID();
    } catch {
      // Fallback if randomUUID is restricted
    }
  }
  return `msg_${Date.now()}_${Math.random().toString(36).substring(2, 11)}`;
};

export function useChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [trendingNews, setTrendingNews] = useState<TrendingArticle[]>([]);

  // Load saved sessions on mount
  useEffect(() => {
    setSessions(getSavedSessions());
  }, []);

  // Load trending news on mount & provide refresh helper
  const refreshTrendingNews = useCallback(async () => {
    const articles = await fetchRecentNews(8);
    if (articles && articles.length > 0) {
      setTrendingNews(articles);
    }
  }, []);

  useEffect(() => {
    let mounted = true;
    fetchRecentNews(8).then((articles) => {
      if (mounted && articles && articles.length > 0) {
        setTrendingNews(articles);
      }
    });
    return () => {
      mounted = false;
    };
  }, []);

  // Start a new chat
  const startNewChat = useCallback(() => {
    setMessages([]);
    setCurrentSessionId(null);
  }, []);

  // Select an existing conversation session
  const selectSession = useCallback(
    async (sessionId: string) => {
      if (loading) return;
      setCurrentSessionId(sessionId);
      setLoading(true);

      try {
        const history = await fetchChatHistory(sessionId);
        setMessages(history);
      } catch (e) {
        console.error("Failed to load session history:", e);
      } finally {
        setLoading(false);
      }
    },
    [loading]
  );

  // Delete a session (both locally and in backend DB)
  const deleteSession = useCallback(
    async (sessionId: string, e?: React.MouseEvent) => {
      if (e) e.stopPropagation();

      setSessions((prev) => {
        const updated = prev.filter((s) => s.id !== sessionId);
        persistSessions(updated);
        return updated;
      });

      if (currentSessionId === sessionId) {
        startNewChat();
      }

      try {
        await deleteChatHistory(sessionId);
      } catch (err) {
        console.warn("Could not delete chat history from server:", err);
      }
    },
    [currentSessionId, startNewChat]
  );

  // Send a message (with optional forceNewSession parameter)
  const sendMessage = useCallback(
    async (text: string, forceNewSession: boolean = false) => {
      const cleanText = text.trim();
      if (!cleanText || loading) return;

      const userMessage: ChatMessage = {
        id: generateUUID(),
        role: "user",
        content: cleanText,
        createdAt: new Date(),
      };

      const activeSessionId = forceNewSession ? null : currentSessionId;
      if (forceNewSession) {
        setCurrentSessionId(null);
        setMessages([userMessage]);
      } else {
        setMessages((prev) => [...prev, userMessage]);
      }

      setLoading(true);

      try {
        const response = await sendChatMessage(cleanText, activeSessionId);
        const returnedSessionId = response.session_id || activeSessionId;

        if (returnedSessionId) {
          setCurrentSessionId(returnedSessionId);

          setSessions((prev) => {
            const exists = prev.find((s) => s.id === returnedSessionId);
            let updated: ChatSession[];
            if (!exists) {
              const newSession: ChatSession = {
                id: returnedSessionId,
                title: cleanText.slice(0, 36) + (cleanText.length > 36 ? "..." : ""),
                lastUpdated: Date.now(),
              };
              updated = [newSession, ...prev];
            } else {
              updated = prev.map((s) =>
                s.id === returnedSessionId ? { ...s, lastUpdated: Date.now() } : s
              );
            }
            persistSessions(updated);
            return updated;
          });
        }

        const assistantMessage: ChatMessage = {
          id: generateUUID(),
          role: "assistant",
          content: response.answer,
          sources: response.sources ?? [],
          createdAt: new Date(),
        };

        setMessages((prev) => [...prev, assistantMessage]);
      } catch (error) {
        console.error("Chat API error:", error);

        setMessages((prev) => [
          ...prev,
          {
            id: generateUUID(),
            role: "assistant",
            content:
              "I could not retrieve an answer from the backend. Please ensure the FastAPI server is running (`uvicorn main:app --reload --port 8000`).",
            createdAt: new Date(),
          },
        ]);
      } finally {
        setLoading(false);
      }
    },
    [currentSessionId, loading]
  );

  return {
    messages,
    loading,
    currentSessionId,
    sessions,
    trendingNews,
    refreshTrendingNews,
    sendMessage,
    startNewChat,
    selectSession,
    deleteSession,
  };
}
