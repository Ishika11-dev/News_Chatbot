import React from "react";
import type { ChatMessage as ChatMessageType } from "../types/chat";
import { ChatWindow } from "../components/chat/ChatWindow";
import { ChatInput } from "../components/chat/ChatInput";

interface ChatPageProps {
  messages: ChatMessageType[];
  loading: boolean;
  onSendMessage: (text: string) => void;
  onSelectPrompt: (prompt: string) => void;
}

export const ChatPage: React.FC<ChatPageProps> = ({
  messages,
  loading,
  onSendMessage,
  onSelectPrompt,
}) => {
  return (
    <div className="flex-1 flex flex-col h-full overflow-hidden relative bg-white dark:bg-slate-950 transition-colors">
      <ChatWindow
        messages={messages}
        loading={loading}
        onSelectPrompt={onSelectPrompt}
      />

      <div className="border-t border-slate-200 dark:border-slate-800 bg-white/95 dark:bg-slate-950/95 backdrop-blur-xs pt-2">
        <ChatInput onSendMessage={onSendMessage} disabled={loading} />
      </div>
    </div>
  );
};

export default ChatPage;
