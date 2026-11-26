import React from "react";
import { Menu, Plus } from "lucide-react";
import type { AdminActionFeedback } from "../../types/admin";
import { AdminActionBanner } from "../admin/AdminActionBanner";
import { ConnectionStatusBadge } from "./ConnectionStatusBadge";

interface MainLayoutProps {
  onToggleSidebar: () => void;
  onNewChat: () => void;
  hasMessages: boolean;
  adminFeedback: AdminActionFeedback | null;
  onDismissAdminFeedback: () => void;
  children: React.ReactNode;
}

export const MainLayout: React.FC<MainLayoutProps> = ({
  onToggleSidebar,
  onNewChat,
  hasMessages,
  adminFeedback,
  onDismissAdminFeedback,
  children,
}) => {
  return (
    <div className="flex-1 flex flex-col h-full overflow-hidden min-w-0 bg-white">
      {/* Minimal Top Header */}
      <header className="h-12 border-b border-slate-200 bg-white/95 backdrop-blur-xs sticky top-0 z-20 flex items-center justify-between px-3 sm:px-4">
        {/* Left: Sidebar Toggle & Clean Title */}
        <div className="flex items-center gap-2.5">
          <button
            onClick={onToggleSidebar}
            className="p-1.5 rounded-lg text-slate-500 hover:text-slate-800 hover:bg-slate-100 transition-colors cursor-pointer"
            title="Toggle sidebar"
          >
            <Menu className="w-5 h-5" />
          </button>
          <span className="text-sm font-semibold text-slate-800 tracking-tight">
            News Intelligence
          </span>
        </div>

        {/* Right: Connection Status & New Chat Shortcut */}
        <div className="flex items-center gap-2">
          <ConnectionStatusBadge />
          {hasMessages && (
            <button
              onClick={onNewChat}
              className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-white hover:bg-slate-100 text-xs font-medium text-slate-700 border border-slate-200 shadow-xs transition-colors cursor-pointer"
              title="Start new chat"
            >
              <Plus className="w-3.5 h-3.5 text-blue-600" />
              <span className="hidden sm:inline">New Chat</span>
            </button>
          )}
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col overflow-hidden relative bg-white">
        <AdminActionBanner
          feedback={adminFeedback}
          onDismiss={onDismissAdminFeedback}
        />
        {children}
      </main>
    </div>
  );
};
