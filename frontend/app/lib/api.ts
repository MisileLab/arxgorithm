const API_BASE = "http://localhost:8000";

export interface Paper {
  id: string;
  arxiv_id: string;
  title: string;
  authors: string[];
  abstract: string;
  categories: string[];
  published_date: string;
  updated_date?: string;
  pdf_url?: string;
  abs_url?: string;
  bookmarked?: boolean;
}

export interface SearchResult {
  paper: Paper;
  score: number;
}

export interface FeedResponse {
  paper_ids: string[];
  reasons: string[];
  strategy: string;
}

export interface BookmarkItem {
  paper: Paper;
  created_at: string;
}

export interface HistoryItem {
  paper: Paper;
  read_at: string;
}

export interface User {
  id: string;
  email: string;
  username: string;
}

function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("token");
}

export function getAuthHeaders(): Record<string, string> {
  const token = getToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export async function searchPapers(
  query: string,
  options?: {
    limit?: number;
    categories?: string[];
  }
): Promise<SearchResult[]> {
  const res = await fetch(`${API_BASE}/papers/search`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...getAuthHeaders() },
    body: JSON.stringify({
      query,
      limit: options?.limit ?? 20,
      categories: options?.categories,
    }),
  });
  if (!res.ok) throw new Error("Search failed");
  return res.json();
}

export async function getFeed(
  userId?: string,
  limit = 20,
  categories?: string[]
): Promise<FeedResponse> {
  const res = await fetch(`${API_BASE}/papers/recommend`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...getAuthHeaders() },
    body: JSON.stringify({
      user_id: userId,
      limit,
      categories,
    }),
  });
  if (!res.ok) throw new Error("Failed to load feed");
  return res.json();
}

export async function getPaper(arxivId: string): Promise<Paper> {
  const res = await fetch(`${API_BASE}/papers/${arxivId}`, {
    headers: { ...getAuthHeaders() },
  });
  if (!res.ok) throw new Error("Paper not found");
  return res.json();
}

export async function getRelatedPapers(arxivId: string): Promise<Paper[]> {
  const res = await fetch(`${API_BASE}/papers/${arxivId}/related`, {
    headers: { ...getAuthHeaders() },
  });
  if (!res.ok) return [];
  return res.json();
}

export async function getBookmarks(): Promise<BookmarkItem[]> {
  const res = await fetch(`${API_BASE}/users/me/bookmarks`, {
    headers: { ...getAuthHeaders() },
  });
  if (!res.ok) throw new Error("Failed to load bookmarks");
  return res.json();
}

export async function addBookmark(arxivId: string): Promise<void> {
  const res = await fetch(`${API_BASE}/users/me/bookmarks/${arxivId}`, {
    method: "POST",
    headers: { ...getAuthHeaders() },
  });
  if (!res.ok) throw new Error("Failed to bookmark");
}

export async function removeBookmark(arxivId: string): Promise<void> {
  const res = await fetch(`${API_BASE}/users/me/bookmarks/${arxivId}`, {
    method: "DELETE",
    headers: { ...getAuthHeaders() },
  });
  if (!res.ok) throw new Error("Failed to remove bookmark");
}

export async function getHistory(): Promise<HistoryItem[]> {
  const res = await fetch(`${API_BASE}/users/me/history`, {
    headers: { ...getAuthHeaders() },
  });
  if (!res.ok) throw new Error("Failed to load history");
  return res.json();
}

export async function recordHistory(arxivId: string): Promise<void> {
  const res = await fetch(`${API_BASE}/users/me/history/${arxivId}`, {
    method: "POST",
    headers: { ...getAuthHeaders() },
  });
  if (!res.ok) {
    // Silently fail - history recording is non-critical
  }
}

export async function login(
  username: string,
  password: string
): Promise<{ access_token: string; token_type: string }> {
  const res = await fetch(`${API_BASE}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || "Login failed");
  }
  return res.json();
}

export async function register(
  email: string,
  username: string,
  password: string
): Promise<{ access_token: string; token_type: string }> {
  const res = await fetch(`${API_BASE}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, username, password }),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || "Registration failed");
  }
  return res.json();
}

export async function getMe(): Promise<User | null> {
  const token = getToken();
  if (!token) return null;
  try {
    const res = await fetch(`${API_BASE}/auth/me`, {
      headers: { ...getAuthHeaders() },
    });
    if (!res.ok) return null;
    return res.json();
  } catch {
    return null;
  }
}

export function logout(): void {
  localStorage.removeItem("token");
}
