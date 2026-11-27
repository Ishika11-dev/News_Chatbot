import React from "react";
import type { TrendingArticle } from "../types/chat";
import { TrendingNews } from "../components/trending/TrendingNews";

interface TrendingPageProps {
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

export const TrendingPage: React.FC<TrendingPageProps> = ({
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
  return (
    <div className="flex-1 flex flex-col h-full overflow-hidden">
      <TrendingNews
        articles={articles}
        page={page}
        pageSize={pageSize}
        totalItems={totalItems}
        totalPages={totalPages}
        hasNext={hasNext}
        hasPrev={hasPrev}
        search={search}
        loading={loading}
        error={error}
        onSearchChange={onSearchChange}
        onPageChange={onPageChange}
        onRefresh={onRefresh}
        onAskAboutArticle={onAskAboutArticle}
      />
    </div>
  );
};

export default TrendingPage;

