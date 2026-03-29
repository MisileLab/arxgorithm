import { useState, useEffect } from "react";
import { Link } from "react-router";
import type { Route } from "./+types/bookmarks";
import { getBookmarks, removeBookmark } from "~/lib/api";
import type { BookmarkItem } from "~/lib/api";
import { useAuth } from "~/lib/auth";
import PaperCard from "~/components/PaperCard";

export function meta({}: Route.MetaArgs) {
  return [{ title: "Bookmarks — arxgorithm" }];
}

export default function Bookmarks() {
  const { user, loading: authLoading } = useAuth();
  const [bookmarks, setBookmarks] = useState<BookmarkItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!user) {
      setLoading(false);
      return;
    }

    async function load() {
      setLoading(true);
      setError(null);
      try {
        const data = await getBookmarks();
        setBookmarks(data);
      } catch (err: any) {
        setError(err.message || "Failed to load bookmarks");
      } finally {
        setLoading(false);
      }
    }

    load();
  }, [user]);

  const handleRemove = async (arxivId: string) => {
    try {
      await removeBookmark(arxivId);
      setBookmarks((prev) => prev.filter((b) => b.paper.arxiv_id !== arxivId));
    } catch {}
  };

  if (authLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="w-8 h-8 border-3 border-blue-600 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (!user) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center max-w-md">
          <div className="text-6xl mb-4">🔒</div>
          <h2 className="text-2xl font-bold mb-3">Sign in to view bookmarks</h2>
          <p className="text-gray-500 mb-6">
            Save papers to read later by bookmarking them.
          </p>
          <Link
            to="/login"
            className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium transition-colors inline-block"
          >
            Sign In
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto px-4 py-8">
        <h1 className="text-3xl font-bold mb-2">Bookmarks</h1>
        <p className="text-gray-500 mb-6">Papers you've saved for later</p>

        {loading && (
          <div className="flex justify-center py-16">
            <div className="flex flex-col items-center gap-3">
              <div className="w-8 h-8 border-3 border-blue-600 border-t-transparent rounded-full animate-spin" />
              <p className="text-gray-500">Loading bookmarks...</p>
            </div>
          </div>
        )}

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
            {error}
          </div>
        )}

        {!loading && !error && bookmarks.length === 0 && (
          <div className="text-center py-16">
            <div className="text-5xl mb-4">📑</div>
            <h2 className="text-xl font-semibold text-gray-700 mb-2">No bookmarks yet</h2>
            <p className="text-gray-500 mb-6">
              Start bookmarking papers while browsing to save them here.
            </p>
            <Link
              to="/search"
              className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium transition-colors inline-block"
            >
              Browse Papers
            </Link>
          </div>
        )}

        {!loading && bookmarks.length > 0 && (
          <div className="space-y-4">
            {bookmarks.map((bookmark) => (
              <div key={bookmark.paper.arxiv_id} className="relative">
                <PaperCard
                  paper={bookmark.paper}
                  onBookmark={handleRemove}
                  isBookmarked={true}
                />
                <p className="text-xs text-gray-400 mt-1 ml-5">
                  Saved {new Date(bookmark.created_at).toLocaleDateString()}
                </p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
