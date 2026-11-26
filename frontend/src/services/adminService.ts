import axios from "axios";
import type {
  TriggerIngestResponse,
  TriggerCleanupResponse,
} from "../types/admin";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

export const triggerManualIngestion = async (): Promise<TriggerIngestResponse> => {
  const response = await axios.post<TriggerIngestResponse>(
    `${API_BASE_URL}/api/admin/trigger-ingest`
  );
  return response.data;
};

export const triggerManualCleanup = async (): Promise<TriggerCleanupResponse> => {
  const response = await axios.post<TriggerCleanupResponse>(
    `${API_BASE_URL}/api/admin/trigger-cleanup`
  );
  return response.data;
};

