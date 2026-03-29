import { useState, useEffect } from "react";
import { Link } from "react-router";
import type { Route } from "./+types/feed";
import { getFeed, getPaper, addBookmark, removeBookmark } from "~/lib/api";
import type { Paper } from "~/lib/api";
import { useAuth } from "~/lib/auth";
import PaperCard from "~/components/PaperCard";

export function meta({}: Route.MetaArgs) {
  return [{ title: "Feed — arxgorithm" }];
}

const STRATEGY_LABELS: Record<string, { label: string; color: string }> = {
  collaborative_filtering: { label: "Collaborative Filtering", color: "bg-purple-100 text-purple-700" },
  content_based: { label: "Content-Based", color: "bg-green-100 text-green-700" },
  agentic: { label: "Agentic AI", color: "bg-amber-100 text-amber-700" },
};

export default function Feed() {
  const { user, loading: authLoading } = useAuth();
  const [papers, setPapers] = useState<Paper[]>([]);
  const [reasons, setReasons] = useState<string[]>([]);
  const [strategy, setStrategy] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [bookmarkedIds, setBookmarkedIds] = useState<Set<string>>(new Set());

  useEffect(() => {
    if (!user) {
      setLoading(false);
      return;
    }

    async function loadFeed() {
      setLoading(true);
      setError(null);
      try {
        const feed = await getFeed(user.id, 20);
        setStrategy(feed.strategy);
        setReasons(feed.reasons);

        const paperPromises = feed.paper_ids.map((id: string) =>
          getPaper(id).catch(() => null)
        );
        const results = await Promise.all(paperPromises);
        setPapers(results.filter((p): p is Paper => p !== null));
      } catch (err: any) {
        setError(err.message || "Failed to load feed");
      } finally {
        setLoading(false);
      }
    }

    loadFeed();
  }, [user]);

  const handleBookmark = async (arxivId: string) => {
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
          <h2 className="text-2xl font-bold mb-3">Sign in to see your feed</h2>
          <p className="text-gray-500 mb-6">
            Get personalized paper recommendations based on your reading history and interests.
          </p>
          <div className="flex gap-3 justify-center">
            <Link
              to="/login"
              className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium transition-colors"
            >
              Sign In
            </Link>
            <Link
              to="/register"
              className="px-6 py-3 border border-gray-300 rounded-lg hover:bg-gray-50 font-medium transition-colors"
            >
              Create Account
            </Link>
          </div>
        </div>
      </div>
    );
  }

  const strategyInfo = STRATEGY_LABELS[strategy] || { label: strategy, color: "bg-gray-100 text-gray-600" };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto px-4 py-8">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-3xl font-bold">Your Feed</h1>
            <p className="text-gray-500 mt-1">Personalized recommendations for you</p>
          </div>
          {strategy && (
            <span className={`text-xs font-medium px-3 py-1.5 rounded-full ${strategyInfo.color}`}>
              {strategyInfo.label}
            </span>
          )}
        </div>

        {loading && (
          <div className="flex justify-center py-16">
            <div className="flex flex-col items-center gap-3">
              <div className="w-8 h-8 border-3 border-blue-600 border-t-transparent rounded-full animate-spin" />
              <p className="text-gray-500">Loading your feed...</p>
            </div>
          </div>
        )}

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
            {error}
          </div>
        )}

        {!loading && !error && papers.length === 0 && (
          <div className="text-center py-16">
            <div className="text-5xl mb-4">📭</div>
            <h2 className="text-xl font-semibold text-gray-700 mb-2">No recommendations yet</h2>
            <p className="text-gray-500 mb-6">
              Start by searching and reading papers to get personalized recommendations.
            </p>
            <Link
              to="/search"
              className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium transition-colors inline-block"
            >
              Browse Papers
            </Link>
          </div>
        )}

        {!loading && papers.length > 0 && (
          <div className="space-y-4">
            {papers.map((paper, i) => (
              <PaperCard
                key={paper.arxiv_id}
                paper={paper}
                reason={reasons[i]}
                onBookmark={handleBookmark}
                isBookmarked={bookmarkedIds.has(paper.arxiv_id)}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
