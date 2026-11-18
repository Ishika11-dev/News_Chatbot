import React, { useEffect, useRef } from "react";
import type { ChatMessage as ChatMessageType } from "../../types/chat";
import { ChatMessage } from "./ChatMessage";
import { TypingIndicator } from "./TypingIndicator";
import { WelcomeScreen } from "./WelcomeScreen";

interface ChatWindowProps {
  messages: ChatMessageType[];
  loading: boolean;
  onSelectPrompt: (prompt: string) => void;
}

export const ChatWindow: React.FC<ChatWindowProps> = ({
  messages,
  loading,
  onSelectPrompt,
}) => {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  if (messages.length === 0) {
    return <WelcomeScreen onSelectPrompt={onSelectPrompt} />;
  }

  return (
    <div className="flex-1 overflow-y-auto px-4 py-6 space-y-6 max-w-3xl w-full mx-auto">
      {messages.map((message) => (
        <ChatMessage key={message.id} message={message} />
      ))}

      {loading && <TypingIndicator />}

      <div ref={bottomRef} className="h-4" />
    </div>
  );
};
