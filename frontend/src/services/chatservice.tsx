import axios from "axios";
import type { ChatResponse, ChatMessage, TrendingArticle } from "../types/chat";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

export const sendChatMessage = async (
  message: string,
  sessionId: string | null = null,
  topK: number = 5
): Promise<ChatResponse> => {
  const response = await axios.post<ChatResponse>(`${API_BASE_URL}/api/chat`, {
    message,
    session_id: sessionId,
    top_k: topK,
    category: null,
  });

  return response.data;
};

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
    console.warn("Could not fetch chat history:", error);
    return [];
  }
};

export const fetchTrendingNews = async (limit: number = 6): Promise<TrendingArticle[]> => {
  try {
    const response = await axios.get<{ articles: TrendingArticle[] }>(
      `${API_BASE_URL}/api/news?limit=${limit}`
    );
    return response.data?.articles || [];
  } catch (error) {
    console.warn("Could not fetch trending news:", error);
    return [];
  }
};