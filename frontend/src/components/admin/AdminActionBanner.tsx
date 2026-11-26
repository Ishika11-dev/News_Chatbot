import React, { useState } from "react";
import {
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Loader2,
  X,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import type { AdminActionFeedback } from "../../types/admin";

interface AdminActionBannerProps {
  feedback: AdminActionFeedback | null;
  onDismiss: () => void;
}

export const AdminActionBanner: React.FC<AdminActionBannerProps> = ({
  feedback,
  onDismiss,
}) => {
  const [showRawJson, setShowRawJson] = useState(false);

  if (!feedback) return null;

  const isIngest = feedback.action === "ingest";
  const actionLabel = isIngest ? "Manual Ingestion" : "30-Day Retention Cleanup";
  const ingestStats = feedback.ingestResponse?.stats;
  const cleanupResult = feedback.cleanupResponse?.result;

  const isFailed =
    Boolean(feedback.error) || ingestStats?.status === "FAILED";
  const isWarning =
    !isFailed &&
    (ingestStats?.status === "PARTIAL_FAILURE" ||
      Boolean(
        cleanupResult?.qdrant_status &&
          cleanupResult.qdrant_status !== "PURGED"
      ));

  const containerStyle = feedback.loading
    ? "bg-blue-50/90 dark:bg-blue-950/60 border-blue-200 dark:border-blue-800 text-blue-900 dark:text-blue-100"
    : isFailed
    ? "bg-rose-50/90 dark:bg-rose-950/60 border-rose-200 dark:border-rose-800 text-rose-900 dark:text-rose-100"
    : isWarning
    ? "bg-amber-50/90 dark:bg-amber-950/60 border-amber-200 dark:border-amber-800 text-amber-900 dark:text-amber-100"
    : "bg-emerald-50/90 dark:bg-emerald-950/60 border-emerald-200 dark:border-emerald-800 text-emerald-900 dark:text-emerald-100";

  const rawPayload = feedback.ingestResponse ?? feedback.cleanupResponse ?? null;

  return (
    <div className="px-3 sm:px-4 pt-3 shrink-0">
      <div
        className={`rounded-xl border px-3.5 py-3 shadow-xs transition-colors ${containerStyle}`}
      >
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-start gap-2.5 min-w-0">
            {feedback.loading ? (
              <Loader2 className="w-4 h-4 mt-0.5 shrink-0 animate-spin text-blue-600" />
            ) : isFailed ? (
              <XCircle className="w-4 h-4 mt-0.5 shrink-0 text-rose-600" />
            ) : isWarning ? (
              <AlertTriangle className="w-4 h-4 mt-0.5 shrink-0 text-amber-600" />
            ) : (
              <CheckCircle2 className="w-4 h-4 mt-0.5 shrink-0 text-emerald-600" />
            )}

            <div className="min-w-0 space-y-1">
              <div className="flex flex-wrap items-center gap-2">
                <span className="text-xs font-semibold">{actionLabel}</span>
                {!feedback.loading && (
                  <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-white/70 dark:bg-slate-900/70 border border-black/10 dark:border-white/10">
                    {feedback.error
                      ? "ERROR"
                      : ingestStats?.status ??
                        feedback.cleanupResponse?.status ??
                        "COMPLETED"}
                  </span>
                )}
                <span className="text-[10px] opacity-70">{feedback.timestamp}</span>
              </div>

              {feedback.loading && (
                <p className="text-xs opacity-85">
                  {isIngest
                    ? "Fetching RSS feeds, chunking articles, and storing vectors..."
                    : "Purging expired articles older than 30 days from Qdrant and database..."}
                </p>
              )}

              {feedback.error && (
                <p className="text-xs break-words">{feedback.error}</p>
              )}

              {feedback.ingestResponse && ingestStats && (
                <div className="space-y-1.5">
                  <p className="text-xs opacity-90">
                    {feedback.ingestResponse.message}
                  </p>
                  <div className="flex flex-wrap gap-2 text-[11px]">
                    <span className="px-2 py-0.5 rounded-md bg-white/75 dark:bg-slate-900/70 border border-black/5 dark:border-white/10">
                      Feeds: <strong>{ingestStats.total_feeds}</strong>
                    </span>
                    <span className="px-2 py-0.5 rounded-md bg-white/75 dark:bg-slate-900/70 border border-black/5 dark:border-white/10">
                      Fetched: <strong>{ingestStats.total_fetched}</strong>
                    </span>
                    <span className="px-2 py-0.5 rounded-md bg-white/75 dark:bg-slate-900/70 border border-black/5 dark:border-white/10">
                      New Articles:{" "}
                      <strong>{ingestStats.new_articles_ingested}</strong>
                    </span>
                    <span className="px-2 py-0.5 rounded-md bg-white/75 dark:bg-slate-900/70 border border-black/5 dark:border-white/10">
                      Duplicates Skipped:{" "}
                      <strong>{ingestStats.duplicates_skipped}</strong>
                    </span>
                    <span className="px-2 py-0.5 rounded-md bg-white/75 dark:bg-slate-900/70 border border-black/5 dark:border-white/10">
                      Chunks Stored:{" "}
                      <strong>
                        {ingestStats.total_chunks_stored}/
                        {ingestStats.total_chunks_created}
                      </strong>
                    </span>
                    <span className="px-2 py-0.5 rounded-md bg-white/75 dark:bg-slate-900/70 border border-black/5 dark:border-white/10">
                      Tokens: <strong>{ingestStats.total_tokens_used}</strong>
                    </span>
                    <span className="px-2 py-0.5 rounded-md bg-white/75 dark:bg-slate-900/70 border border-black/5 dark:border-white/10">
                      Duration: <strong>{ingestStats.duration_seconds}s</strong>
                    </span>
                  </div>
                  {ingestStats.error_message && (
                    <p className="text-[11px] font-medium">
                      Reason: {ingestStats.error_message}
                    </p>
                  )}
                  {ingestStats.failed_feeds.length > 0 && (
                    <p className="text-[11px] opacity-85">
                      Failed feeds: {ingestStats.failed_feeds.join(", ")}
                    </p>
                  )}
                </div>
              )}

              {feedback.cleanupResponse && cleanupResult && (
                <div className="space-y-1.5">
                  <p className="text-xs opacity-90">
                    {feedback.cleanupResponse.message}
                  </p>
                  <div className="flex flex-wrap gap-2 text-[11px]">
                    <span className="px-2 py-0.5 rounded-md bg-white/75 dark:bg-slate-900/70 border border-black/5 dark:border-white/10">
                      Deleted DB Articles:{" "}
                      <strong>{cleanupResult.deleted_db_articles}</strong>
                    </span>
                    <span className="px-2 py-0.5 rounded-md bg-white/75 dark:bg-slate-900/70 border border-black/5 dark:border-white/10">
                      Qdrant Status:{" "}
                      <strong>{cleanupResult.qdrant_status}</strong>
                    </span>
                    <span className="px-2 py-0.5 rounded-md bg-white/75 dark:bg-slate-900/70 border border-black/5 dark:border-white/10">
                      Cutoff Date:{" "}
                      <strong>
                        {new Date(cleanupResult.cutoff_date).toLocaleString()}
                      </strong>
                    </span>
                  </div>
                </div>
              )}

              {rawPayload && (
                <div className="pt-1">
                  <button
                    type="button"
                    onClick={() => setShowRawJson((prev) => !prev)}
                    className="inline-flex items-center gap-1 text-[11px] font-medium underline underline-offset-2 opacity-80 hover:opacity-100 cursor-pointer"
                  >
                    {showRawJson ? (
                      <>
                        <ChevronUp className="w-3 h-3" />
                        Hide raw response
                      </>
                    ) : (
                      <>
                        <ChevronDown className="w-3 h-3" />
                        View raw response
                      </>
                    )}
                  </button>
                  {showRawJson && (
                    <pre className="mt-1.5 p-2 rounded-lg bg-slate-900 text-slate-100 text-[11px] overflow-x-auto max-h-48">
                      {JSON.stringify(rawPayload, null, 2)}
                    </pre>
                  )}
                </div>
              )}
            </div>
          </div>

          {!feedback.loading && (
            <button
              type="button"
              onClick={onDismiss}
              className="p-1 rounded-md hover:bg-black/5 transition-colors cursor-pointer shrink-0"
              title="Dismiss response"
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

