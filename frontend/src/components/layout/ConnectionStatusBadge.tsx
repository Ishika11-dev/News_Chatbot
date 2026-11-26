import React, { useEffect, useState, useCallback, useRef } from "react";
import { RefreshCw } from "lucide-react";
import { fetchHealthStatus } from "../../services/healthService";
import type { HealthResponse } from "../../types/health";

const POLL_INTERVAL_MS = 30_000;

export const ConnectionStatusBadge: React.FC = () => {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [backendReachable, setBackendReachable] = useState<boolean | null>(null);
  const [checking, setChecking] = useState<boolean>(true);
  const [open, setOpen] = useState<boolean>(false);
  const containerRef = useRef<HTMLDivElement | null>(null);

  const checkHealth = useCallback(async () => {
    setChecking(true);
    try {
      const data = await fetchHealthStatus();
      setHealth(data);
      setBackendReachable(true);
    } catch {
      setHealth(null);
      setBackendReachable(false);
    } finally {
      setChecking(false);
    }
  }, []);

  useEffect(() => {
    checkHealth();
    const timer = window.setInterval(checkHealth, POLL_INTERVAL_MS);
    return () => window.clearInterval(timer);
  }, [checkHealth]);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (
        containerRef.current &&
        !containerRef.current.contains(e.target as Node)
      ) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const postgresOk = Boolean(health?.checks?.postgres?.connected);
  const qdrantOk = Boolean(health?.checks?.qdrant?.connected);
  const isAllHealthy = Boolean(backendReachable && postgresOk && qdrantOk);
  const isPending = backendReachable === null && checking;

  const dotClass = isPending
    ? "bg-slate-400 animate-pulse"
    : isAllHealthy
    ? "bg-emerald-500"
    : "bg-rose-500";

  const label = isPending
    ? "Checking..."
    : isAllHealthy
    ? "Connected"
    : backendReachable
    ? "Degraded"
    : "Offline";

  return (
    <div ref={containerRef} className="relative">
      <button
        type="button"
        onClick={() => setOpen((prev) => !prev)}
        className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-slate-50 dark:bg-slate-900 hover:bg-slate-100 dark:hover:bg-slate-800 border border-slate-200 dark:border-slate-700 text-[11px] font-medium text-slate-700 dark:text-slate-200 transition-colors cursor-pointer"
        title="System connection status (Postgres & Qdrant)"
      >
        <span className={`w-2 h-2 rounded-full shrink-0 ${dotClass}`} />
        <span className="hidden sm:inline">{label}</span>
      </button>

      {open && (
        <div className="absolute right-0 mt-1.5 w-64 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 shadow-lg p-3 z-50 text-xs space-y-2.5">
          <div className="flex items-center justify-between border-b border-slate-100 dark:border-slate-800 pb-2">
            <span className="font-semibold text-slate-800 dark:text-slate-100">
              Connection Status
            </span>
            <button
              type="button"
              onClick={checkHealth}
              disabled={checking}
              className="inline-flex items-center gap-1 text-[11px] text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 disabled:opacity-50 cursor-pointer"
              title="Refresh connection status"
            >
              <RefreshCw
                className={`w-3 h-3 ${checking ? "animate-spin" : ""}`}
              />
              <span>Refresh</span>
            </button>
          </div>

          <div className="space-y-2">
            <StatusRow
              label="Backend API"
              ok={Boolean(backendReachable)}
              error={!backendReachable ? "Server unreachable" : null}
            />
            <StatusRow
              label="PostgreSQL"
              ok={postgresOk}
              error={
                backendReachable
                  ? health?.checks?.postgres?.error
                  : "Backend offline"
              }
            />
            <StatusRow
              label="Qdrant"
              ok={qdrantOk}
              error={
                backendReachable
                  ? health?.checks?.qdrant?.error
                  : "Backend offline"
              }
            />
          </div>

          {health?.timestamp && (
            <div className="pt-1.5 border-t border-slate-100 dark:border-slate-800 text-[10px] text-slate-400 dark:text-slate-500">
              Last checked: {new Date(health.timestamp).toLocaleTimeString()}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

interface StatusRowProps {
  label: string;
  ok: boolean;
  error?: string | null;
}

const StatusRow: React.FC<StatusRowProps> = ({ label, ok, error }) => (
  <div className="space-y-0.5">
    <div className="flex items-center justify-between">
      <span className="text-slate-700 dark:text-slate-200 font-medium">{label}</span>
      <span className="inline-flex items-center gap-1.5 text-[11px]">
        <span
          className={`w-2 h-2 rounded-full ${
            ok ? "bg-emerald-500" : "bg-rose-500"
          }`}
        />
        <span className={ok ? "text-emerald-700 dark:text-emerald-400" : "text-rose-600 dark:text-rose-400"}>
          {ok ? "Active" : "Inactive"}
        </span>
      </span>
    </div>
    {!ok && error && (
      <p className="text-[10px] text-rose-500 dark:text-rose-400 truncate" title={error}>
        {error}
      </p>
    )}
  </div>
);

