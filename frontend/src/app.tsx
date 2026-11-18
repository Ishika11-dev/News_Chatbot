import React, { useState, useEffect } from "react";
import { useChat } from "./hooks/useChat";
import { Sidebar } from "./components/layout/Sidebar";
import { MainLayout } from "./components/layout/MainLayout";
import { ChatPage } from "./pages/ChatPage";
import { TrendingPage } from "./pages/TrendingPage";

export function App() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [activeTab, setActiveTab] = useState<"chat" | "trending">("chat");

  const {
    messages,
    loading,
    currentSessionId,
    sessions,
    trendingNews,
    sendMessage,
    startNewChat,
    selectSession,
    deleteSession,
  } = useChat();

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
      />

      {/* Main Content Layout */}
      <MainLayout
        onToggleSidebar={() => setSidebarOpen((prev) => !prev)}
        onNewChat={() => {
          startNewChat();
          setActiveTab("chat");
        }}
        hasMessages={messages.length > 0}
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
