import axios from "axios";
import type { ChatResponse } from "../types/chat";

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

