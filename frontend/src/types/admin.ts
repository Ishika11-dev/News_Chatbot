export interface IngestionStats {
  total_feeds: number;
  total_fetched: number;
  new_articles_ingested: number;
  duplicates_skipped: number;
  total_chunks_created: number;
  total_chunks_stored: number;
  total_tokens_used: number;
  status: string;
  error_message?: string | null;
  failed_feeds: string[];
  duration_seconds: number;
}

export interface TriggerIngestResponse {
  status: string;
  message: string;
  stats: IngestionStats;
}

export interface CleanupResult {
  cutoff_timestamp: number;
  cutoff_date: string;
  deleted_db_articles: number;
  qdrant_status: string;
}

export interface TriggerCleanupResponse {
  status: string;
  message: string;
  result: CleanupResult;
}

export type AdminActionType = "ingest" | "cleanup";

export interface AdminActionFeedback {
  action: AdminActionType;
  loading: boolean;
  error?: string | null;
  ingestResponse?: TriggerIngestResponse | null;
  cleanupResponse?: TriggerCleanupResponse | null;
  timestamp: string;
}

