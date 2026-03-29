import { Link } from "react-router";
import type { Paper } from "~/lib/api";

interface PaperCardProps {
  paper: Paper;
  score?: number;
  reason?: string;
  onBookmark?: (arxivId: string) => void;
  isBookmarked?: boolean;
}

export default function PaperCard({
  paper,
  score,
  reason,
  onBookmark,
  isBookmarked,
}: PaperCardProps) {
  const authors =
    paper.authors.length > 3
      ? paper.authors.slice(0, 3).join(", ") + ` et al. (${paper.authors.length} authors)`
      : paper.authors.join(", ");

  const abstractPreview =
    paper.abstract.length > 250
      ? paper.abstract.slice(0, 250) + "..."
      : paper.abstract;

  const formattedDate = paper.published_date
    ? new Date(paper.published_date).toLocaleDateString("en-US", {
        year: "numeric",
        month: "short",
        day: "numeric",
      })
    : "";

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between gap-3">
        <Link
          to={`/paper/${paper.arxiv_id}`}
          className="flex-1 min-w-0"
        >
          <h3 className="text-base font-semibold text-gray-900 hover:text-blue-600 transition-colors line-clamp-2">
            {paper.title}
          </h3>
        </Link>
        {score !== undefined && (
          <span className="shrink-0 text-xs font-medium bg-blue-50 text-blue-700 px-2 py-1 rounded-full">
            {(score * 100).toFixed(1)}%
          </span>
        )}
      </div>

      <p className="mt-1.5 text-sm text-gray-500">{authors}</p>

      {formattedDate && (
        <p className="mt-1 text-xs text-gray-400">{formattedDate}</p>
      )}

      <div className="mt-3 flex flex-wrap gap-1.5">
        {paper.categories.map((cat) => (
          <span
            key={cat}
            className="text-xs font-medium bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full"
          >
            {cat}
          </span>
        ))}
      </div>

      <p className="mt-3 text-sm text-gray-600 leading-relaxed line-clamp-3">
        {abstractPreview}
      </p>

      {reason && (
        <div className="mt-3 text-xs text-blue-600 bg-blue-50 px-3 py-1.5 rounded-lg">
          {reason}
        </div>
      )}

      <div className="mt-4 flex items-center justify-between">
        <Link
          to={`/paper/${paper.arxiv_id}`}
          className="text-sm text-blue-600 hover:text-blue-800 font-medium"
        >
          Read more →
        </Link>
        {onBookmark && (
          <button
            onClick={(e) => {
              e.preventDefault();
              onBookmark(paper.arxiv_id);
            }}
            className={`text-sm px-3 py-1 rounded-lg border transition-colors ${
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
  );
}
