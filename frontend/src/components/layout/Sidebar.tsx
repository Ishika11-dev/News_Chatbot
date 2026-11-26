import React from "react";
import {
  Plus,
  MessageSquare,
  Flame,
  Trash2,
  Newspaper,
  X,
  RefreshCw,
  DatabaseZap,
  Loader2,
} from "lucide-react";
import type { ChatSession } from "../../types/chat";
import type { AdminActionType } from "../../types/admin";

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
  activeTab: "chat" | "trending";
  onSelectTab: (tab: "chat" | "trending") => void;
  sessions: ChatSession[];
  currentSessionId: string | null;
  onNewChat: () => void;
  onSelectSession: (id: string) => void;
  onDeleteSession: (id: string, e: React.MouseEvent) => void;
  adminRunningAction: AdminActionType | null;
  onTriggerIngest: () => void;
  onTriggerCleanup: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  isOpen,
  onClose,
  activeTab,
  onSelectTab,
  sessions,
  currentSessionId,
  onNewChat,
  onSelectSession,
  onDeleteSession,
  adminRunningAction,
  onTriggerIngest,
  onTriggerCleanup,
}) => {
  const closeOnMobile = () => {
    if (typeof window !== "undefined" && window.innerWidth < 768) {
      onClose();
    }
  };

  return (
    <>
      {/* Mobile Backdrop */}
      {isOpen && (
        <div
          onClick={onClose}
          className="fixed inset-0 bg-slate-900/30 dark:bg-black/60 z-40 md:hidden transition-opacity"
        />
      )}

      {/* Sidebar Container */}
      <aside
        className={`fixed md:static inset-y-0 left-0 z-50 shrink-0 overflow-hidden bg-slate-50 dark:bg-slate-900 transition-all duration-200 ease-in-out ${
          isOpen
            ? "w-64 translate-x-0 border-r border-slate-200 dark:border-slate-800"
            : "w-64 -translate-x-full md:w-0 md:translate-x-0 border-r-0 pointer-events-none md:pointer-events-none"
        }`}
      >
        <div className="flex flex-col w-64 h-full">
        {/* Top Header & New Chat Button */}
        <div className="p-3 border-b border-slate-200 dark:border-slate-800 space-y-2.5">
          <div className="flex items-center justify-between px-1">
            <div className="flex items-center gap-2">
              <div className="w-6 h-6 rounded-md bg-blue-600 flex items-center justify-center text-white font-bold text-xs shadow-xs">
                <Newspaper className="w-3.5 h-3.5" />
              </div>
              <span className="font-semibold text-xs text-slate-800 dark:text-slate-100 tracking-tight">
                News Intelligence
              </span>
            </div>
            <button
              onClick={onClose}
              className="p-1 rounded-md text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-100 md:hidden hover:bg-slate-200/60 dark:hover:bg-slate-800 cursor-pointer"
              title="Close sidebar"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          {/* New Chat Button */}
          <button
            onClick={() => {
              onNewChat();
              onSelectTab("chat");
              closeOnMobile();
            }}
            className="w-full flex items-center justify-between px-3 py-2 rounded-lg bg-white dark:bg-slate-800 hover:bg-slate-100 dark:hover:bg-slate-700/80 text-slate-800 dark:text-slate-100 font-medium text-xs border border-slate-200 dark:border-slate-700 shadow-xs transition-colors cursor-pointer"
          >
            <div className="flex items-center gap-2">
              <Plus className="w-3.5 h-3.5 text-blue-600 dark:text-blue-400" />
              <span>New Chat</span>
            </div>
            <span className="text-[10px] text-slate-400 font-mono">
              Ctrl+K
            </span>
          </button>

          {/* View Switcher: Chat vs Trending */}
          <div className="grid grid-cols-2 gap-1 p-0.5 bg-slate-200/70 dark:bg-slate-800 rounded-lg text-xs">
            <button
              onClick={() => {
                onSelectTab("chat");
                closeOnMobile();
              }}
              className={`flex items-center justify-center gap-1.5 py-1.5 rounded-md font-medium transition-colors cursor-pointer ${
                activeTab === "chat"
                  ? "bg-white dark:bg-slate-700 text-blue-600 dark:text-blue-400 shadow-xs"
                  : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100"
              }`}
            >
              <MessageSquare className="w-3.5 h-3.5" />
              <span>Chat</span>
            </button>
            <button
              onClick={() => {
                onSelectTab("trending");
                closeOnMobile();
              }}
              className={`flex items-center justify-center gap-1.5 py-1.5 rounded-md font-medium transition-colors cursor-pointer ${
                activeTab === "trending"
                  ? "bg-white dark:bg-slate-700 text-blue-600 dark:text-blue-400 shadow-xs"
                  : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100"
              }`}
            >
              <Flame className="w-3.5 h-3.5" />
              <span>Trending</span>
            </button>
          </div>
        </div>

        {/* Scrollable Chat History */}
        <div className="flex-1 overflow-y-auto px-2 py-3">
          <div className="px-2 pb-1.5 flex items-center justify-between text-[10px] font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wider">
            <span>Recent Chats</span>
            <span className="text-slate-400 dark:text-slate-500">{sessions.length}</span>
          </div>

          {sessions.length === 0 ? (
            <p className="px-2 py-3 text-xs text-slate-400 dark:text-slate-500 italic text-left">
              No saved chats yet.
            </p>
          ) : (
            <div className="space-y-0.5">
              {sessions.map((s) => {
                const isActive = s.id === currentSessionId && activeTab === "chat";
                return (
                  <div
                    key={s.id}
                    onClick={() => {
                      onSelectSession(s.id);
                      onSelectTab("chat");
                      closeOnMobile();
                    }}
                    className={`group flex items-center justify-between px-2.5 py-2 rounded-lg text-xs cursor-pointer transition-colors ${
                      isActive
                        ? "bg-blue-50 dark:bg-blue-950/60 text-blue-700 dark:text-blue-300 font-medium border border-blue-200 dark:border-blue-800"
                        : "text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800"
                    }`}
                  >
                    <div className="flex items-center gap-2 overflow-hidden">
                      <MessageSquare
                        className={`w-3.5 h-3.5 shrink-0 ${
                          isActive ? "text-blue-600 dark:text-blue-400" : "text-slate-400 dark:text-slate-500"
                        }`}
                      />
                      <span className="truncate">{s.title || "Conversation"}</span>
                    </div>

                    <button
                      onClick={(e) => onDeleteSession(s.id, e)}
                      className="opacity-0 group-hover:opacity-100 p-1 hover:text-rose-600 dark:hover:text-rose-400 text-slate-400 transition-opacity cursor-pointer"
                      title="Delete chat"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Pipeline Admin Controls */}
        <div className="p-3 border-t border-slate-200 dark:border-slate-800 bg-slate-100/60 dark:bg-slate-900/80 space-y-1.5">
          <div className="px-0.5 text-[10px] font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wider">
            Pipeline Controls
          </div>
          <button
            type="button"
            disabled={adminRunningAction !== null}
            onClick={() => {
              onTriggerIngest();
              closeOnMobile();
            }}
            className="w-full flex items-center justify-between px-2.5 py-2 rounded-lg bg-white dark:bg-slate-800 hover:bg-blue-50/70 dark:hover:bg-slate-700/80 text-slate-700 dark:text-slate-200 hover:text-blue-700 dark:hover:text-blue-400 text-xs font-medium border border-slate-200 dark:border-slate-700 shadow-xs transition-colors cursor-pointer disabled:opacity-60 disabled:cursor-not-allowed"
          >
            <span className="flex items-center gap-2">
              {adminRunningAction === "ingest" ? (
                <Loader2 className="w-3.5 h-3.5 animate-spin text-blue-600 dark:text-blue-400" />
              ) : (
                <RefreshCw className="w-3.5 h-3.5 text-blue-600 dark:text-blue-400" />
              )}
              <span>Manual Ingestion</span>
            </span>
          </button>

          <button
            type="button"
            disabled={adminRunningAction !== null}
            onClick={() => {
              onTriggerCleanup();
              closeOnMobile();
            }}
            className="w-full flex items-center justify-between px-2.5 py-2 rounded-lg bg-white dark:bg-slate-800 hover:bg-amber-50/70 dark:hover:bg-slate-700/80 text-slate-700 dark:text-slate-200 hover:text-amber-700 dark:hover:text-amber-400 text-xs font-medium border border-slate-200 dark:border-slate-700 shadow-xs transition-colors cursor-pointer disabled:opacity-60 disabled:cursor-not-allowed"
          >
            <span className="flex items-center gap-2">
              {adminRunningAction === "cleanup" ? (
                <Loader2 className="w-3.5 h-3.5 animate-spin text-amber-600 dark:text-amber-400" />
              ) : (
                <DatabaseZap className="w-3.5 h-3.5 text-amber-600 dark:text-amber-400" />
              )}
              <span>30d Retention Cleanup</span>
            </span>
          </button>
        </div>
        </div>
      </aside>
    </>
  );
};
