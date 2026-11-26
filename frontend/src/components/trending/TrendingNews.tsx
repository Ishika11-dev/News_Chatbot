import React, { useState } from "react";
import { Flame, ExternalLink, Calendar, Search, ArrowRight, Newspaper } from "lucide-react";
import type { TrendingArticle } from "../../types/chat";
import { formatDate } from "../../utils/formatdate";

interface TrendingNewsProps {
  articles: TrendingArticle[];
  onAskAboutArticle: (title: string) => void;
}

export const TrendingNews: React.FC<TrendingNewsProps> = ({
  articles,
  onAskAboutArticle,
}) => {
  const [searchTerm, setSearchTerm] = useState("");

  const filtered = articles.filter(
    (a) =>
      a.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (a.publisher && a.publisher.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  return (
    <div className="flex-1 overflow-y-auto p-4 sm:p-6 max-w-4xl w-full mx-auto space-y-6">
      {/* Top Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-200 dark:border-slate-800">
        <div>
          <div className="flex items-center gap-2 text-slate-900 dark:text-slate-100 font-semibold text-sm">
            <Flame className="w-4 h-4 text-amber-500" />
            <span>Trending News (Past 30 Days)</span>
          </div>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
            Verified articles stored in your local knowledge base. Click "Ask AI" to query any news item.
          </p>
        </div>

        {/* Search Filter */}
        <div className="relative w-full sm:w-64">
          <Search className="w-4 h-4 text-slate-400 dark:text-slate-500 absolute left-3 top-2.5" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search recent news..."
            className="w-full pl-9 pr-3 py-1.5 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg text-xs text-slate-800 dark:text-slate-100 placeholder-slate-400 dark:placeholder-slate-500 focus:outline-none focus:border-blue-500"
          />
        </div>
      </div>

      {/* Grid of Articles */}
      {filtered.length === 0 ? (
        <div className="p-12 text-center text-slate-400 dark:text-slate-500 space-y-2">
          <Newspaper className="w-8 h-8 mx-auto text-slate-300 dark:text-slate-700" />
          <p className="text-sm">No trending articles match your search.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
          {filtered.map((article) => (
            <div
              key={article.article_id}
              onClick={() => onAskAboutArticle(`Tell me about: ${article.title}`)}
              className="p-4 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 hover:border-blue-400 dark:hover:border-blue-500 hover:shadow-xs transition-all flex flex-col justify-between shadow-xs cursor-pointer group"
            >
              <div className="space-y-1.5">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-semibold text-blue-600 dark:text-blue-400">
                    {article.publisher || "News"}
                  </span>
                  {article.published_at && (
                    <span className="flex items-center gap-1 text-[11px] text-slate-400 dark:text-slate-500">
                      <Calendar className="w-3 h-3 text-slate-400 dark:text-slate-500" />
                      {formatDate(article.published_at)}
                    </span>
                  )}
                </div>

                <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-100 group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors line-clamp-2 leading-snug">
                  {article.title}
                </h3>

                {article.summary && (
                  <p className="text-xs text-slate-500 dark:text-slate-400 line-clamp-2 leading-relaxed">
                    {article.summary}
                  </p>
                )}
              </div>

              <div className="pt-3 mt-3 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between">
                {article.article_url ? (
                  <a
                    href={article.article_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    onClick={(e) => e.stopPropagation()}
                    className="text-xs text-slate-400 dark:text-slate-500 hover:text-slate-700 dark:hover:text-slate-300 flex items-center gap-1 transition-colors"
                  >
                    <span>Read source</span>
                    <ExternalLink className="w-3 h-3" />
                  </a>
                ) : (
                  <div />
                )}

                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    onAskAboutArticle(`Tell me about: ${article.title}`);
                  }}
                  className="px-2.5 py-1 rounded-md bg-blue-50 dark:bg-blue-950/60 group-hover:bg-blue-600 group-hover:text-white hover:bg-blue-600 hover:text-white text-blue-600 dark:text-blue-400 border border-blue-200 dark:border-blue-800 text-xs font-medium flex items-center gap-1.5 transition-colors cursor-pointer"
                >
                  <span>Ask AI</span>
                  <ArrowRight className="w-3 h-3" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
