import { useState } from "react";
import { useNavigate } from "react-router";

const CATEGORIES = [
  { value: "", label: "All Categories" },
  { value: "cs.AI", label: "AI (cs.AI)" },
  { value: "cs.CL", label: "Computation & Language (cs.CL)" },
  { value: "cs.CV", label: "Computer Vision (cs.CV)" },
  { value: "cs.LG", label: "Machine Learning (cs.LG)" },
  { value: "cs.NE", label: "Neural & Evolutionary (cs.NE)" },
  { value: "stat.ML", label: "Statistics (stat.ML)" },
];

interface SearchBarProps {
  initialQuery?: string;
  initialCategory?: string;
  onSearch: (query: string, category: string) => void;
  loading?: boolean;
}

export default function SearchBar({
  initialQuery = "",
  initialCategory = "",
  onSearch,
  loading = false,
}: SearchBarProps) {
  const [query, setQuery] = useState(initialQuery);
  const [category, setCategory] = useState(initialCategory);
  const navigate = useNavigate();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;
    navigate(`/search?q=${encodeURIComponent(query.trim())}${category ? `&cat=${category}` : ""}`);
    onSearch(query.trim(), category);
  };

  return (
    <form onSubmit={handleSubmit} className="flex gap-2 w-full">
      <div className="flex-1 relative">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search papers by topic, title, or abstract..."
          className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none text-base"
          disabled={loading}
        />
        {loading && (
          <div className="absolute right-3 top-1/2 -translate-y-1/2">
            <div className="w-5 h-5 border-2 border-blue-600 border-t-transparent rounded-full animate-spin" />
          </div>
        )}
      </div>
      <select
        value={category}
        onChange={(e) => setCategory(e.target.value)}
        className="px-3 py-3 border border-gray-300 rounded-lg bg-white text-sm text-gray-700 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
        disabled={loading}
      >
        {CATEGORIES.map((cat) => (
          <option key={cat.value} value={cat.value}>
            {cat.label}
          </option>
        ))}
      </select>
      <button
        type="submit"
        disabled={loading || !query.trim()}
        className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium transition-colors"
      >
        Search
      </button>
    </form>
  );
}
