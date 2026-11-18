import axios from "axios";

const API = import.meta.env.VITE_API_BASE_URL;

export const sendChatMessage = async (message: string) => {
  const response = await axios.post(`${API}/api/chat`, {
    message: message,
  });

  return response.data;
};