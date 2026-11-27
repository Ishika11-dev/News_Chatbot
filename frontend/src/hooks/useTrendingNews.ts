import { useState, useCallback, useEffect, useRef } from "react";
import axios from "axios";
import { fetchTrendingNewsPage } from "../services/newsService";
import type { TrendingArticle } from "../types/chat";

const PAGE_SIZE = 8;

export function useTrendingNews(isActive: boolean) {
  const [articles, setArticles] = useState<TrendingArticle[]>([]);
  const [page, setPage] = useState<number>(1);
  const [totalItems, setTotalItems] = useState<number>(0);
  const [totalPages, setTotalPages] = useState<number>(0);
  const [hasNext, setHasNext] = useState<boolean>(false);
  const [hasPrev, setHasPrev] = useState<boolean>(false);
  const [search, setSearchState] = useState<string>("");
  const [selectedCategory, setSelectedCategory] = useState<string>("All");
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const requestIdRef = useRef(0);
  const prevSearchRef = useRef(search);
  const prevCategoryRef = useRef(selectedCategory);

  const loadPage = useCallback(
    async (
      targetPage: number = 1,
      searchQuery: string = search,
      category: string = selectedCategory
    ) => {
      const requestId = ++requestIdRef.current;
      setLoading(true);
      setError(null);

      try {
        const data = await fetchTrendingNewsPage(
          targetPage,
          PAGE_SIZE,
          category,
          searchQuery
        );
        if (requestId !== requestIdRef.current) return;

        setArticles(data.articles || []);
        setPage(data.page);
        setTotalItems(data.total_items);
        setTotalPages(data.total_pages);
        setHasNext(data.has_next);
        setHasPrev(data.has_prev);
      } catch (err) {
        if (requestId !== requestIdRef.current) return;
        const message = axios.isAxiosError(err)
          ? err.response?.data?.detail || err.message
          : "Could not load trending news from backend.";
        setError(message);
      } finally {
        if (requestId === requestIdRef.current) {
          setLoading(false);
        }
      }
    },
    [search, selectedCategory]
  );

  // Fetch page 1 whenever the user opens the Trending tab
  useEffect(() => {
    if (isActive) {
      loadPage(1, search, selectedCategory);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isActive]);

  // Refetch from page 1 immediately when category filter changes
  useEffect(() => {
    if (prevCategoryRef.current === selectedCategory) return;
    prevCategoryRef.current = selectedCategory;
    if (!isActive) return;

    loadPage(1, search, selectedCategory);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedCategory]);

  // Debounce server-side search queries only when search actually changes
  useEffect(() => {
    if (prevSearchRef.current === search) return;
    prevSearchRef.current = search;
    if (!isActive) return;

    const timer = window.setTimeout(() => {
      loadPage(1, search, selectedCategory);
    }, 250);
    return () => window.clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [search]);

  const goToPage = useCallback(
    (targetPage: number) => {
      if (targetPage < 1 || (totalPages > 0 && targetPage > totalPages)) return;
      loadPage(targetPage, search, selectedCategory);
    },
    [loadPage, search, selectedCategory, totalPages]
  );

  const refreshTrending = useCallback(() => {
    loadPage(page, search, selectedCategory);
  }, [loadPage, page, search, selectedCategory]);

  return {
    articles,
    page,
    pageSize: PAGE_SIZE,
    totalItems,
    totalPages,
    hasNext,
    hasPrev,
    search,
    setSearch: setSearchState,
    selectedCategory,
    setSelectedCategory,
    loading,
    error,
    goToPage,
    refreshTrending,
  };
}
