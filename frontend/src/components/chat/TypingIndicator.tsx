import React from "react";
import { Bot } from "lucide-react";

export const TypingIndicator: React.FC = () => {
  return (
    <div className="flex items-start gap-3 text-left">
      <div className="w-8 h-8 rounded-full bg-blue-50 dark:bg-blue-950/60 border border-blue-200 dark:border-blue-800 flex items-center justify-center shrink-0 text-blue-600 dark:text-blue-400 shadow-xs">
        <Bot className="w-4 h-4" />
      </div>

      <div className="px-3.5 py-3 rounded-2xl bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-tl-xs flex items-center gap-1.5 shadow-xs">
        <span className="w-2 h-2 rounded-full bg-blue-600 dark:bg-blue-400 animate-bounce [animation-delay:-0.3s]"></span>
        <span className="w-2 h-2 rounded-full bg-blue-600 dark:bg-blue-400 animate-bounce [animation-delay:-0.15s]"></span>
        <span className="w-2 h-2 rounded-full bg-blue-600 dark:bg-blue-400 animate-bounce"></span>
        <span className="ml-2 text-xs text-slate-500 dark:text-slate-400 font-medium">Searching verified news...</span>
      </div>
    </div>
  );
};
