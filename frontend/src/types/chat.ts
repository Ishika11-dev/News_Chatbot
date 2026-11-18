export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: ArticleSource[];
  createdAt: Date;
}

export interface ArticleSource {
  title: string;
  publisher?: string;
  url: string;
  published_at?: string;
}