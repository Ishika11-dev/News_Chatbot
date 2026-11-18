import React from "react";
import { Newspaper, ShieldCheck, Zap, ArrowRight, TrendingUp } from "lucide-react";

interface WelcomeScreenProps {
  onSelectPrompt: (prompt: string) => void;
}

const SAMPLE_PROMPTS = [
  {
    title: "AI & Tech News",
    query: "What is the latest news regarding Nvidia and AI chips?",
    icon: Zap,
  },
  {
    title: "Electric Vehicles",
    query: "Summarize recent developments in the electric vehicle industry.",
    icon: TrendingUp,
  },
  {
    title: "Market Inquiries",
    query: "What major technology or financial investigations were announced recently?",
    icon: ShieldCheck,
  },
];

export const WelcomeScreen: React.FC<WelcomeScreenProps> = ({ onSelectPrompt }) => {
  return (
    <div className="flex-1 flex flex-col items-center justify-center p-6 text-center max-w-2xl mx-auto space-y-6">
      {/* Icon Badge */}
      <div className="w-12 h-12 rounded-xl bg-blue-50 border border-blue-200 flex items-center justify-center text-blue-600 shadow-xs">
        <Newspaper className="w-6 h-6" />
      </div>

      {/* Headings */}
      <div className="space-y-1.5">
        <h2 className="text-xl sm:text-2xl font-semibold text-slate-900 tracking-tight">
          News Intelligence Assistant
        </h2>
        <p className="text-sm text-slate-500 max-w-md mx-auto leading-relaxed">
          Grounded strictly in verified news from the past 30 days.
          Answers include inline numerical citations linked directly to verified publishers.
        </p>
      </div>

      {/* Suggested Prompts */}
      <div className="w-full space-y-2 pt-3">
        <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider text-left">
          Suggested Queries
        </p>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
          {SAMPLE_PROMPTS.map((sample, idx) => {
            const Icon = sample.icon;
            return (
              <button
                key={idx}
                type="button"
                onClick={(e) => {
                  e.preventDefault();
                  onSelectPrompt(sample.query);
                }}
                className="group p-3.5 rounded-xl border border-slate-200 bg-white hover:bg-slate-50 hover:border-blue-400 text-left transition-colors shadow-xs flex flex-col justify-between cursor-pointer"
              >
                <div>
                  <Icon className="w-4 h-4 text-blue-600 mb-2" />
                  <span className="text-xs font-semibold text-slate-800 block mb-1">
                    {sample.title}
                  </span>
                  <span className="text-[11px] text-slate-500 line-clamp-2 leading-snug">
                    {sample.query}
                  </span>
                </div>
                <div className="mt-3 flex items-center gap-1 text-[11px] font-medium text-blue-600">
                  <span>Ask</span>
                  <ArrowRight className="w-3 h-3 group-hover:translate-x-0.5 transition-transform" />
                </div>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
};
