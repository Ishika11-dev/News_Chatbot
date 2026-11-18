import axios from "axios";
import type { ChatMessage, ChatSession } from "../types/chat";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";
const SESSIONS_STORAGE_KEY = "news_intelligence_chat_sessions";

export const fetchChatHistory = async (sessionId: string): Promise<ChatMessage[]> => {
  try {
    const response = await axios.get<any[]>(`${API_BASE_URL}/api/chat/history/${sessionId}`);
    return (response.data || []).map((msg) => ({
      id: String(msg.id),
      role: msg.role === "assistant" ? "assistant" : "user",
      content: msg.content,
      sources: msg.sources || [],
      createdAt: msg.created_at ? new Date(msg.created_at) : new Date(),
    }));
  } catch (error) {
    console.warn("Could not fetch chat history from server:", error);
    return [];
  }
};

export const getSavedSessions = (): ChatSession[] => {
  try {
    const data = localStorage.getItem(SESSIONS_STORAGE_KEY);
    return data ? JSON.parse(data) : [];
  } catch (e) {
    console.warn("Error reading sessions from localStorage:", e);
    return [];
  }
};

export const persistSessions = (sessions: ChatSession[]): void => {
  try {
    localStorage.setItem(SESSIONS_STORAGE_KEY, JSON.stringify(sessions));
  } catch (e) {
    console.warn("Error persisting sessions to localStorage:", e);
  }
};

