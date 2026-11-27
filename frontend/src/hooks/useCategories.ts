import { useState, useEffect } from "react";
import {
  DEFAULT_NEWS_CATEGORIES,
  fetchNewsCategories,
} from "../services/newsService";

export function useCategories() {
  const [categories, setCategories] = useState<string[]>(
    DEFAULT_NEWS_CATEGORIES
  );

  useEffect(() => {
    let mounted = true;
    fetchNewsCategories().then((list) => {
      if (mounted && list.length > 0) {
        setCategories(list);
      }
    });
    return () => {
      mounted = false;
    };
  }, []);

  return categories;
}

