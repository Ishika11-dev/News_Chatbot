import axios from "axios";
import type {
  PaginatedTrendingResponse,
  TrendingArticle,
} from "../types/chat";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

export const DEFAULT_NEWS_CATEGORIES: string[] = [
  "All",
  "Technology",
  "Business",
  "World News",
  "Politics",
  "Science",
  "Sports",
  "Entertainment",
];

const FALLBACK_ARTICLES: TrendingArticle[] = [
  {
    article_id: "preview-1",
    title: "Nvidia Unveils Next-Gen Blackwell Ultra AI GPUs for Data Centers",
    summary:
      "Nvidia announced its latest enterprise GPU computing architecture, designed for ultra-scale training and low-latency inference workloads.",
    publisher: "TechCrunch",
    published_at: new Date(Date.now() - 3600 * 1000 * 12).toISOString(),
    article_url: "https://techcrunch.com",
    category: "Technology",
  },
  {
    article_id: "preview-2",
    title: "Global Automakers Accelerate Commercial Solid-State Battery Deployment for EVs",
    summary:
      "Automotive leaders revealed new roadmaps and commercial range testing results for next-generation solid-state battery technology.",
    publisher: "Reuters",
    published_at: new Date(Date.now() - 3600 * 1000 * 24).toISOString(),
    article_url: "https://reuters.com",
    category: "Technology",
  },
  {
    article_id: "preview-3",
    title: "Financial Regulators Announce Comprehensive Review of Cloud AI Computing Partnerships",
    summary:
      "Global competition watchdogs launched a detailed joint study into infrastructure dependencies and long-term cloud service agreements.",
    publisher: "Bloomberg",
    published_at: new Date(Date.now() - 3600 * 1000 * 48).toISOString(),
    article_url: "https://bloomberg.com",
    category: "Business",
  },
];

export const fetchRecentNews = async (
  limit: number = 8,
  category: string | null = null
): Promise<TrendingArticle[]> => {
  try {
    const params: Record<string, any> = { limit };
    if (category && category !== "All") {
      params.category = category;
    }

    const response = await axios.get<{ articles: TrendingArticle[] }>(
      `${API_BASE_URL}/api/news`,
      { params }
    );

    const backendArticles = response.data?.articles || [];
    if (backendArticles.length > 0) {
      return backendArticles;
    }
    return FALLBACK_ARTICLES;
  } catch (error) {
    console.warn("Could not fetch recent news from backend, using preview items:", error);
    return FALLBACK_ARTICLES;
  }
};

export const fetchTrendingNewsPage = async (
  page: number = 1,
  pageSize: number = 8,
  category: string | null = null,
  search: string = ""
): Promise<PaginatedTrendingResponse> => {
  const params: Record<string, string | number> = {
    page,
    page_size: pageSize,
  };
  if (category && category !== "All") {
    params.category = category;
  }
  if (search.trim()) {
    params.search = search.trim();
  }

  const response = await axios.get<PaginatedTrendingResponse>(
    `${API_BASE_URL}/api/news/trending`,
    { params }
  );
  return response.data;
};

export const fetchNewsCategories = async (): Promise<string[]> => {
  try {
    const response = await axios.get<string[]>(
      `${API_BASE_URL}/api/news/categories`
    );
    if (Array.isArray(response.data) && response.data.length > 0) {
      return response.data;
    }
    return DEFAULT_NEWS_CATEGORIES;
  } catch (error) {
    console.warn("Could not fetch news categories, using defaults:", error);
    return DEFAULT_NEWS_CATEGORIES;
  }
};

