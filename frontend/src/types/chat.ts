export interface SourceCitation {
  citation_id: number;
  title: string;
  publisher: string;
  published_at: string;
  url: string;
  category?: string;
  score?: number | null;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: SourceCitation[];
  createdAt: Date;
}

export interface ChatResponse {
  answer: string;
  sources: SourceCitation[];
  session_id: string;
  timestamp: string;
}

export interface ChatSession {
  id: string;
  title: string;
  lastUpdated: number;
}

export interface TrendingArticle {
  article_id: string;
  title: string;
  summary?: string;
  publisher?: string;
  category?: string;
  published_at?: string;
  article_url?: string;
  image_url?: string;
}

export interface PaginatedTrendingResponse {
  page: number;
  page_size: number;
  total_items: number;
  total_pages: number;
  has_next: boolean;
  has_prev: boolean;
  articles: TrendingArticle[];
}
