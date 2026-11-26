import axios from "axios";
import type { HealthResponse } from "../types/health";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

export const fetchHealthStatus = async (): Promise<HealthResponse> => {
  const response = await axios.get<HealthResponse>(
    `${API_BASE_URL}/api/health`,
    { timeout: 5000 }
  );
  return response.data;
};

