import React from "react";
import type { TrendingArticle } from "../types/chat";
import { TrendingNews } from "../components/trending/TrendingNews";

interface TrendingPageProps {
  articles: TrendingArticle[];
  onAskAboutArticle: (title: string) => void;
}

export const TrendingPage: React.FC<TrendingPageProps> = ({
  articles,
  onAskAboutArticle,
}) => {
  return (
    <div className="flex-1 flex flex-col h-full overflow-hidden">
      <TrendingNews
        articles={articles}
        onAskAboutArticle={onAskAboutArticle}
      />
    </div>
  );
};

export default TrendingPage;

