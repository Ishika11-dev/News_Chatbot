import React from "react";
import { ExternalLink, Sparkles, Calendar } from "lucide-react";
import type { SourceCitation } from "../../types/chat";
import { formatDate } from "../../utils/formatdate";

interface SourceListProps {
  sources: SourceCitation[];
}

export const SourceList: React.FC<SourceListProps> = ({ sources }) => {
  if (!sources || sources.length === 0) return null;

  return (
    <div className="space-y-2 pt-1">
      <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-600">
        <Sparkles className="w-3.5 h-3.5 text-blue-600" />
        <span>Verified Sources ({sources.length})</span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
        {sources.map((source) => (
          <a
            key={source.citation_id || source.url}
            href={source.url}
            target="_blank"
            rel="noopener noreferrer"
            className="group block p-3 rounded-xl border border-slate-200 bg-white hover:bg-slate-50/70 hover:border-blue-400 transition-colors text-left shadow-xs"
          >
            <div className="flex items-start justify-between gap-2">
              <div className="flex items-center gap-1.5 text-xs font-semibold text-blue-600">
                <span className="w-5 h-5 rounded-full bg-blue-50 border border-blue-200 flex items-center justify-center text-[10px]">
                  {source.citation_id}
                </span>
                <span className="truncate">{source.publisher || "News Source"}</span>
              </div>
              <ExternalLink className="w-3.5 h-3.5 text-slate-400 group-hover:text-blue-600 transition-colors shrink-0" />
            </div>

            <h4 className="mt-1.5 text-xs font-medium text-slate-800 line-clamp-2 group-hover:text-slate-900 transition-colors">
              {source.title}
            </h4>

            <div className="mt-2 flex items-center gap-2 text-[11px] text-slate-400">
              {source.published_at && (
                <span className="flex items-center gap-1">
                  <Calendar className="w-3 h-3 text-slate-400" />
                  {formatDate(source.published_at)}
                </span>
              )}
              {source.category && (
                <span className="px-1.5 py-0.2 rounded bg-slate-100 text-slate-600 text-[10px] border border-slate-200">
                  {source.category}
                </span>
              )}
            </div>
          </a>
        ))}
      </div>
    </div>
  );
};
