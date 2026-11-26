import React, { useState, useEffect, useCallback } from "react";
import axios from "axios";
import { useChat } from "./hooks/useChat";
import { Sidebar } from "./components/layout/Sidebar";
import { MainLayout } from "./components/layout/MainLayout";
import { ChatPage } from "./pages/ChatPage";
import { TrendingPage } from "./pages/TrendingPage";
import {
  triggerManualIngestion,
  triggerManualCleanup,
} from "./services/adminService";
import type { AdminActionFeedback } from "./types/admin";

export function App() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [activeTab, setActiveTab] = useState<"chat" | "trending">("chat");
  const [adminFeedback, setAdminFeedback] =
    useState<AdminActionFeedback | null>(null);

  const {
    messages,
    loading,
    currentSessionId,
    sessions,
    trendingNews,
    refreshTrendingNews,
    sendMessage,
    startNewChat,
    selectSession,
    deleteSession,
  } = useChat();

  const handleRunAdminAction = useCallback(
    async (action: "ingest" | "cleanup") => {
      if (adminFeedback?.loading) return;

      setAdminFeedback({
        action,
        loading: true,
        timestamp: new Date().toLocaleTimeString(),
      });

      try {
        if (action === "ingest") {
          const ingestResponse = await triggerManualIngestion();
          setAdminFeedback({
            action,
            loading: false,
            ingestResponse,
            timestamp: new Date().toLocaleTimeString(),
          });
        } else {
          const cleanupResponse = await triggerManualCleanup();
          setAdminFeedback({
            action,
            loading: false,
            cleanupResponse,
            timestamp: new Date().toLocaleTimeString(),
          });
        }
        await refreshTrendingNews();
      } catch (err) {
        const errorMessage = axios.isAxiosError(err)
          ? err.response?.data?.detail || err.message
          : err instanceof Error
          ? err.message
          : "Request failed. Ensure the backend server is running.";

        setAdminFeedback({
          action,
          loading: false,
          error: errorMessage,
          timestamp: new Date().toLocaleTimeString(),
        });
      }
    },
    [adminFeedback?.loading, refreshTrendingNews]
  );

  // Keyboard shortcut Ctrl+K or Cmd+K to start a new chat
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === "k") {
        e.preventDefault();
        startNewChat();
        setActiveTab("chat");
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [startNewChat]);

  const handleAskAboutNews = (prompt: string) => {
    setActiveTab("chat");
    sendMessage(prompt, true);
  };

  return (
    <div className="flex h-screen bg-white text-slate-800 font-sans overflow-hidden">
      {/* Clean Minimalist Sidebar */}
      <Sidebar
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        activeTab={activeTab}
        onSelectTab={setActiveTab}
        sessions={sessions}
        currentSessionId={currentSessionId}
        onNewChat={() => {
          startNewChat();
          setActiveTab("chat");
        }}
        onSelectSession={(id) => {
          selectSession(id);
          setActiveTab("chat");
        }}
        onDeleteSession={deleteSession}
        adminRunningAction={
          adminFeedback?.loading ? adminFeedback.action : null
        }
        onTriggerIngest={() => handleRunAdminAction("ingest")}
        onTriggerCleanup={() => handleRunAdminAction("cleanup")}
      />

      {/* Main Content Layout */}
      <MainLayout
        onToggleSidebar={() => setSidebarOpen((prev) => !prev)}
        onNewChat={() => {
          startNewChat();
          setActiveTab("chat");
        }}
        hasMessages={messages.length > 0}
        adminFeedback={adminFeedback}
        onDismissAdminFeedback={() => setAdminFeedback(null)}
      >
        {activeTab === "chat" ? (
          <ChatPage
            messages={messages}
            loading={loading}
            onSendMessage={(text) => sendMessage(text, false)}
            onSelectPrompt={(prompt) => sendMessage(prompt, true)}
          />
        ) : (
          <TrendingPage
            articles={trendingNews}
            onAskAboutArticle={handleAskAboutNews}
          />
        )}
      </MainLayout>
    </div>
  );
}

export default App;
