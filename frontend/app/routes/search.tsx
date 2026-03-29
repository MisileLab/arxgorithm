import { useState, useEffect } from "react";
import { useSearchParams } from "react-router";
import type { Route } from "./+types/search";
import { searchPapers, addBookmark, removeBookmark, getPaper } from "~/lib/api";
import type { Paper, SearchResult } from "~/lib/api";
import { useAuth } from "~/lib/auth";
import PaperCard from "~/components/PaperCard";
import SearchBar from "~/components/SearchBar";

export function meta({}: Route.MetaArgs) {
  return [{ title: "Search — arxgorithm" }];
}

export default function Search() {
  const [searchParams] = useSearchParams();
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searched, setSearched] = useState(false);
  const [bookmarkedIds, setBookmarkedIds] = useState<Set<string>>(new Set());
  const { user } = useAuth();

  const initialQuery = searchParams.get("q") || "";
  const initialCategory = searchParams.get("cat") || "";

  const doSearch = async (query: string, category: string) => {
    setLoading(true);
    setError(null);
    setSearched(true);
    try {
      const cats = category ? [category] : undefined;
      const data = await searchPapers(query, { limit: 20, categories: cats });
      setResults(data);
    } catch (err: any) {
      setError(err.message || "Search failed. Please try again.");
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (initialQuery) {
      doSearch(initialQuery, initialCategory);
    }
  }, []);

  const handleBookmark = async (arxivId: string) => {
    if (!user) return;
    try {
      if (bookmarkedIds.has(arxivId)) {
        await removeBookmark(arxivId);
        setBookmarkedIds((prev) => {
          const next = new Set(prev);
          next.delete(arxivId);
          return next;
        });
      } else {
        await addBookmark(arxivId);
        setBookmarkedIds((prev) => new Set(prev).add(arxivId));
      }
    } catch {}
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto px-4 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-6">Search Papers</h1>
          <SearchBar
            initialQuery={initialQuery}
            initialCategory={initialCategory}
            onSearch={doSearch}
            loading={loading}
          />
        </div>

        {loading && (
          <div className="flex justify-center py-16">
            <div className="flex flex-col items-center gap-3">
              <div className="w-8 h-8 border-3 border-blue-600 border-t-transparent rounded-full animate-spin" />
              <p className="text-gray-500">Searching papers...</p>
            </div>
          </div>
        )}

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
            {error}
          </div>
        )}

        {!loading && searched && results.length === 0 && !error && (
          <div className="text-center py-16">
            <div className="text-5xl mb-4">🔍</div>
            <h2 className="text-xl font-semibold text-gray-700 mb-2">No papers found</h2>
            <p className="text-gray-500">Try a different search query or remove category filters.</p>
          </div>
        )}

        {!loading && !searched && (
          <div className="text-center py-16">
            <div className="text-5xl mb-4">📚</div>
            <h2 className="text-xl font-semibold text-gray-700 mb-2">Search for papers</h2>
            <p className="text-gray-500">Enter a topic, title, or keyword to find relevant arXiv papers.</p>
          </div>
        )}

        {results.length > 0 && (
          <div>
            <p className="text-sm text-gray-500 mb-4">
              Found {results.length} result{results.length !== 1 ? "s" : ""}
            </p>
            <div className="space-y-4">
              {results.map((result, i) => (
                <PaperCard
                  key={result.paper?.arxiv_id || i}
                  paper={result.paper}
                  score={result.score}
                  onBookmark={user ? handleBookmark : undefined}
                  isBookmarked={bookmarkedIds.has(result.paper?.arxiv_id)}
                />
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
