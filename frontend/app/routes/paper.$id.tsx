import { useState, useEffect } from "react";
import { useParams, Link } from "react-router";
import type { Route } from "./+types/paper.$id";
import { getPaper, getRelatedPapers, addBookmark, removeBookmark, recordHistory } from "~/lib/api";
import type { Paper } from "~/lib/api";
import { useAuth } from "~/lib/auth";
import PaperCard from "~/components/PaperCard";

export function meta({ params }: Route.MetaArgs) {
  return [{ title: "Paper — arxgorithm" }];
}

export default function PaperDetail() {
  const { id } = useParams();
  const { user } = useAuth();
  const [paper, setPaper] = useState<Paper | null>(null);
  const [related, setRelated] = useState<Paper[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isBookmarked, setIsBookmarked] = useState(false);
  const [bookmarking, setBookmarking] = useState(false);

  useEffect(() => {
    if (!id) return;

    async function load() {
      setLoading(true);
      setError(null);
      try {
        const [p, rel] = await Promise.all([
          getPaper(id),
          getRelatedPapers(id).catch(() => []),
        ]);
        setPaper(p);
        setRelated(rel);
        setIsBookmarked(p.bookmarked ?? false);

        if (user) {
          recordHistory(id).catch(() => {});
        }
      } catch (err: any) {
        setError(err.message || "Failed to load paper");
      } finally {
        setLoading(false);
      }
    }

    load();
  }, [id, user]);

  const handleBookmark = async () => {
    if (!user || !paper) return;
    setBookmarking(true);
    try {
      if (isBookmarked) {
        await removeBookmark(paper.arxiv_id);
        setIsBookmarked(false);
      } else {
        await addBookmark(paper.arxiv_id);
        setIsBookmarked(true);
      }
    } catch {} finally {
      setBookmarking(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 border-3 border-blue-600 border-t-transparent rounded-full animate-spin" />
          <p className="text-gray-500">Loading paper...</p>
        </div>
      </div>
    );
  }

  if (error || !paper) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="text-5xl mb-4">😕</div>
          <h2 className="text-2xl font-bold mb-2">Paper not found</h2>
          <p className="text-gray-500 mb-6">{error || "This paper could not be loaded."}</p>
          <Link
            to="/search"
            className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium transition-colors inline-block"
          >
            Back to Search
          </Link>
        </div>
      </div>
    );
  }

  const formattedDate = paper.published_date
    ? new Date(paper.published_date).toLocaleDateString("en-US", {
        year: "numeric",
        month: "long",
        day: "numeric",
      })
    : "Unknown date";

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto px-4 py-8">
        {/* Back link */}
        <Link
          to="/search"
          className="inline-flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700 mb-6"
        >
          ← Back to search
        </Link>

        {/* Paper header */}
        <div className="bg-white rounded-xl border border-gray-200 p-6 mb-6">
          <h1 className="text-2xl font-bold text-gray-900 mb-3">{paper.title}</h1>

          <p className="text-gray-600 mb-4">{paper.authors.join(", ")}</p>

          <div className="flex flex-wrap gap-2 mb-4">
            {paper.categories.map((cat) => (
              <span
                key={cat}
                className="text-xs font-medium bg-blue-50 text-blue-700 px-2.5 py-1 rounded-full"
              >
                {cat}
              </span>
            ))}
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <span className="text-sm text-gray-500">{formattedDate}</span>

            {paper.pdf_url && (
              <a
                href={paper.pdf_url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm text-blue-600 hover:text-blue-800 font-medium"
              >
                📄 PDF
              </a>
            )}

            {paper.abs_url && (
              <a
                href={paper.abs_url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm text-blue-600 hover:text-blue-800 font-medium"
              >
                🔗 arXiv Abstract
              </a>
            )}

            {!paper.abs_url && (
              <a
                href={`https://arxiv.org/abs/${paper.arxiv_id}`}
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm text-blue-600 hover:text-blue-800 font-medium"
              >
                🔗 arXiv Abstract
              </a>
            )}

            {!paper.pdf_url && (
              <a
                href={`https://arxiv.org/pdf/${paper.arxiv_id}`}
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm text-blue-600 hover:text-blue-800 font-medium"
              >
                📄 PDF
              </a>
            )}

            {user && (
              <button
                onClick={handleBookmark}
                disabled={bookmarking}
                className={`text-sm px-4 py-1.5 rounded-lg border transition-colors ${
                  isBookmarked
                    ? "bg-blue-50 border-blue-200 text-blue-600"
                    : "border-gray-200 text-gray-500 hover:bg-gray-50"
                }`}
              >
                {isBookmarked ? "★ Bookmarked" : "☆ Bookmark"}
              </button>
            )}
          </div>
        </div>

        {/* Abstract */}
        <div className="bg-white rounded-xl border border-gray-200 p-6 mb-6">
          <h2 className="text-lg font-semibold mb-3">Abstract</h2>
          <p className="text-gray-700 leading-relaxed whitespace-pre-wrap">{paper.abstract}</p>
        </div>

        {/* Related papers */}
        {related.length > 0 && (
          <div>
            <h2 className="text-xl font-bold mb-4">Related Papers</h2>
            <div className="space-y-4">
              {related.map((rp) => (
                <PaperCard key={rp.arxiv_id} paper={rp} />
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
