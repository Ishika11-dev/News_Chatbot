import React from "react";
import { Menu, Plus, Moon, Sun } from "lucide-react";
import type { AdminActionFeedback } from "../../types/admin";
import { AdminActionBanner } from "../admin/AdminActionBanner";
import { ConnectionStatusBadge } from "./ConnectionStatusBadge";

interface MainLayoutProps {
  onToggleSidebar: () => void;
  onNewChat: () => void;
  hasMessages: boolean;
  darkMode: boolean;
  onToggleDarkMode: () => void;
  adminFeedback: AdminActionFeedback | null;
  onDismissAdminFeedback: () => void;
  children: React.ReactNode;
}

export const MainLayout: React.FC<MainLayoutProps> = ({
  onToggleSidebar,
  onNewChat,
  hasMessages,
  darkMode,
  onToggleDarkMode,
  adminFeedback,
  onDismissAdminFeedback,
  children,
}) => {
  return (
    <div className="flex-1 flex flex-col h-full overflow-hidden min-w-0 bg-white dark:bg-slate-950 transition-colors">
      {/* Minimal Top Header */}
      <header className="h-12 border-b border-slate-200 dark:border-slate-800 bg-white/95 dark:bg-slate-950/95 backdrop-blur-xs sticky top-0 z-20 flex items-center justify-between px-3 sm:px-4">
        {/* Left: Sidebar Toggle & Clean Title */}
        <div className="flex items-center gap-2.5">
          <button
            onClick={onToggleSidebar}
            className="p-1.5 rounded-lg text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-100 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors cursor-pointer"
            title="Toggle sidebar"
          >
            <Menu className="w-5 h-5" />
          </button>
          <span className="text-sm font-semibold text-slate-800 dark:text-slate-100 tracking-tight">
            News Intelligence
          </span>
        </div>

        {/* Right: Connection Status, Theme Toggle & New Chat Shortcut */}
        <div className="flex items-center gap-2">
          <ConnectionStatusBadge />
          <button
            type="button"
            onClick={onToggleDarkMode}
            className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-slate-50 dark:bg-slate-900 hover:bg-slate-100 dark:hover:bg-slate-800 border border-slate-200 dark:border-slate-700 text-[11px] font-medium text-slate-700 dark:text-slate-200 transition-colors cursor-pointer"
            title={darkMode ? "Switch to light mode" : "Switch to dark mode"}
            aria-label={darkMode ? "Switch to light mode" : "Switch to dark mode"}
          >
            {darkMode ? (
              <>
                <Sun className="w-3.5 h-3.5 text-amber-400" />
                <span className="hidden sm:inline">Light</span>
              </>
            ) : (
              <>
                <Moon className="w-3.5 h-3.5 text-slate-600" />
                <span className="hidden sm:inline">Dark</span>
              </>
            )}
          </button>
          {hasMessages && (
            <button
              onClick={onNewChat}
              className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-white dark:bg-slate-900 hover:bg-slate-100 dark:hover:bg-slate-800 text-xs font-medium text-slate-700 dark:text-slate-200 border border-slate-200 dark:border-slate-700 shadow-xs transition-colors cursor-pointer"
              title="Start new chat"
            >
              <Plus className="w-3.5 h-3.5 text-blue-600 dark:text-blue-400" />
              <span className="hidden sm:inline">New Chat</span>
            </button>
          )}
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col overflow-hidden relative bg-white dark:bg-slate-950 transition-colors">
        <AdminActionBanner
          feedback={adminFeedback}
          onDismiss={onDismissAdminFeedback}
        />
        {children}
      </main>
    </div>
  );
};
