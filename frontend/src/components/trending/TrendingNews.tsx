import React, { useRef } from "react";
import {
  Flame,
  ExternalLink,
  Calendar,
  Search,
  ArrowRight,
  Newspaper,
  ChevronLeft,
  ChevronRight,
  Loader2,
  RefreshCw,
} from "lucide-react";
import type { TrendingArticle } from "../../types/chat";
import { formatDate } from "../../utils/formatdate";

interface TrendingNewsProps {
  articles: TrendingArticle[];
  page: number;
  pageSize: number;
  totalItems: number;
  totalPages: number;
  hasNext: boolean;
  hasPrev: boolean;
  search: string;
  loading: boolean;
  error: string | null;
  onSearchChange: (value: string) => void;
  onPageChange: (page: number) => void;
  onRefresh: () => void;
  onAskAboutArticle: (title: string) => void;
}

const getPageNumbers = (current: number, total: number): (number | "ellipsis")[] => {
  if (total <= 7) {
    return Array.from({ length: total }, (_, idx) => idx + 1);
  }
  const pages: (number | "ellipsis")[] = [1];
  const start = Math.max(2, current - 1);
  const end = Math.min(total - 1, current + 1);

  if (start > 2) pages.push("ellipsis");
  for (let p = start; p <= end; p++) pages.push(p);
  if (end < total - 1) pages.push("ellipsis");
  pages.push(total);

  return pages;
};

export const TrendingNews: React.FC<TrendingNewsProps> = ({
  articles,
  page,
  pageSize,
  totalItems,
  totalPages,
  hasNext,
  hasPrev,
  search,
  loading,
  error,
  onSearchChange,
  onPageChange,
  onRefresh,
  onAskAboutArticle,
}) => {
  const scrollContainerRef = useRef<HTMLDivElement>(null);

  const handlePageChange = (targetPage: number) => {
    onPageChange(targetPage);
    scrollContainerRef.current?.scrollTo({ top: 0, behavior: "smooth" });
  };

  const startItem = totalItems === 0 ? 0 : (page - 1) * pageSize + 1;
  const endItem = Math.min(page * pageSize, totalItems);
  const pageNumbers = getPageNumbers(page, totalPages);

  return (
    <div
      ref={scrollContainerRef}
      className="flex-1 overflow-y-auto p-4 sm:p-6 max-w-4xl w-full mx-auto space-y-6"
    >
      {/* Top Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-200 dark:border-slate-800">
        <div>
          <div className="flex items-center gap-2 text-slate-900 dark:text-slate-100 font-semibold text-sm">
            <Flame className="w-4 h-4 text-amber-500" />
            <span>Recent & Trending News (Past 30 Days)</span>
            {totalItems > 0 && (
              <span className="text-[11px] font-normal px-2 py-0.5 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300">
                {totalItems} total
              </span>
            )}
          </div>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
            All verified articles stored in your knowledge base ({pageSize} per page). Click "Ask AI" to query any article.
          </p>
        </div>

        {/* Search Filter & Refresh */}
        <div className="flex items-center gap-2 w-full sm:w-auto">
          <div className="relative flex-1 sm:w-64">
            <Search className="w-4 h-4 text-slate-400 dark:text-slate-500 absolute left-3 top-2" />
            <input
              type="text"
              value={search}
              onChange={(e) => onSearchChange(e.target.value)}
              placeholder="Search all recent news..."
              className="w-full pl-9 pr-3 py-1.5 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg text-xs text-slate-800 dark:text-slate-100 placeholder-slate-400 dark:placeholder-slate-500 focus:outline-none focus:border-blue-500"
            />
          </div>
          <button
            type="button"
            onClick={onRefresh}
            disabled={loading}
            className="p-2 rounded-lg bg-slate-50 dark:bg-slate-900 hover:bg-slate-100 dark:hover:bg-slate-800 border border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-300 transition-colors cursor-pointer disabled:opacity-50"
            title="Refresh news list"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
          </button>
        </div>
      </div>

      {/* Error State */}
      {error && (
        <div className="rounded-xl border border-rose-200 dark:border-rose-800 bg-rose-50 dark:bg-rose-950/60 px-4 py-3 text-xs text-rose-800 dark:text-rose-200 flex items-center justify-between gap-3">
          <span>{error}</span>
          <button
            type="button"
            onClick={onRefresh}
            className="px-2.5 py-1 rounded-md bg-white dark:bg-slate-900 border border-rose-200 dark:border-rose-700 font-medium hover:bg-rose-100 dark:hover:bg-rose-900/50 cursor-pointer shrink-0"
          >
            Retry
          </button>
        </div>
      )}

      {/* Loading / Empty / Grid of Articles */}
      {loading && articles.length === 0 ? (
        <div className="p-12 text-center text-slate-400 dark:text-slate-500 space-y-2">
          <Loader2 className="w-7 h-7 mx-auto animate-spin text-blue-600 dark:text-blue-400" />
          <p className="text-xs">Loading recent news...</p>
        </div>
      ) : articles.length === 0 ? (
        <div className="p-12 text-center text-slate-400 dark:text-slate-500 space-y-2">
          <Newspaper className="w-8 h-8 mx-auto text-slate-300 dark:text-slate-700" />
          <p className="text-sm">
            {search.trim()
              ? "No recent articles match your search."
              : "No recent articles found in the database."}
          </p>
        </div>
      ) : (
        <div className={`space-y-5 transition-opacity ${loading ? "opacity-60" : "opacity-100"}`}>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
            {articles.map((article) => (
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

          {/* Pagination Controls */}
          {totalPages > 0 && (
            <div className="pt-4 border-t border-slate-200 dark:border-slate-800 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs">
              <span className="text-slate-500 dark:text-slate-400">
                Showing <strong className="text-slate-800 dark:text-slate-200">{startItem}–{endItem}</strong> of{" "}
                <strong className="text-slate-800 dark:text-slate-200">{totalItems}</strong> articles
              </span>

              <div className="flex items-center gap-1">
                <button
                  type="button"
                  disabled={!hasPrev || loading}
                  onClick={() => handlePageChange(page - 1)}
                  className="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer transition-colors"
                >
                  <ChevronLeft className="w-3.5 h-3.5" />
                  <span>Prev</span>
                </button>

                {pageNumbers.map((item, idx) =>
                  item === "ellipsis" ? (
                    <span
                      key={`ellipsis-${idx}`}
                      className="px-2 text-slate-400 dark:text-slate-500 select-none"
                    >
                      …
                    </span>
                  ) : (
                    <button
                      key={item}
                      type="button"
                      disabled={loading}
                      onClick={() => handlePageChange(item)}
                      className={`min-w-8 px-2.5 py-1.5 rounded-lg border text-xs font-medium transition-colors cursor-pointer ${
                        item === page
                          ? "bg-blue-600 border-blue-600 text-white"
                          : "border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800"
                      }`}
                    >
                      {item}
                    </button>
                  )
                )}

                <button
                  type="button"
                  disabled={!hasNext || loading}
                  onClick={() => handlePageChange(page + 1)}
                  className="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer transition-colors"
                >
                  <span>Next</span>
                  <ChevronRight className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
