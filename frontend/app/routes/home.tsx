import { useState } from "react";
import { Link, useNavigate } from "react-router";
import type { Route } from "./+types/home";

export function meta({}: Route.MetaArgs) {
  return [
    { title: "arxgorithm — Personalized arXiv Paper Recommendations" },
    { name: "description", content: "Open-source personalized arXiv paper recommendation platform" },
  ];
}

const CATEGORIES = [
  { value: "", label: "All Categories" },
  { value: "cs.AI", label: "AI (cs.AI)" },
  { value: "cs.CL", label: "Computation & Language (cs.CL)" },
  { value: "cs.CV", label: "Computer Vision (cs.CV)" },
  { value: "cs.LG", label: "Machine Learning (cs.LG)" },
  { value: "cs.NE", label: "Neural & Evolutionary (cs.NE)" },
  { value: "stat.ML", label: "Statistics (stat.ML)" },
];

export default function Home() {
  const [query, setQuery] = useState("");
  const [category, setCategory] = useState("");
  const navigate = useNavigate();

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;
    navigate(`/search?q=${encodeURIComponent(query.trim())}${category ? `&cat=${category}` : ""}`);
  };

  return (
    <div className="min-h-screen">
      {/* Hero */}
      <section className="bg-gradient-to-b from-white to-gray-50 py-20">
        <div className="max-w-4xl mx-auto px-4 text-center">
          <h2 className="text-5xl font-bold mb-6 leading-tight">
            Find papers that
            <br />
            <span className="text-blue-600">actually matter</span> to you
          </h2>
          <p className="text-xl text-gray-600 mb-10 max-w-2xl mx-auto">
            Open-source arXiv recommendation engine powered by collaborative filtering
            embeddings and agentic AI.
          </p>

          {/* Hero search bar */}
          <form onSubmit={handleSearch} className="max-w-2xl mx-auto flex gap-2 mb-8">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search for papers..."
              className="flex-1 px-5 py-3.5 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none text-base"
            />
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className="px-3 py-3.5 border border-gray-300 rounded-xl bg-white text-sm text-gray-700 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
            >
              {CATEGORIES.map((cat) => (
                <option key={cat.value} value={cat.value}>
                  {cat.label}
                </option>
              ))}
            </select>
            <button
              type="submit"
              disabled={!query.trim()}
              className="px-8 py-3.5 bg-blue-600 text-white rounded-xl hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium text-base transition-colors"
            >
              Search
            </button>
          </form>

          <div className="flex gap-4 justify-center">
            <Link
              to="/search"
              className="text-blue-600 hover:text-blue-800 font-medium text-sm"
            >
              Advanced Search →
            </Link>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="max-w-6xl mx-auto px-4 py-20">
        <h2 className="text-2xl font-bold text-center mb-12">
          Why arxgorithm?
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div className="bg-white p-8 rounded-xl border border-gray-200 hover:shadow-lg transition-shadow">
            <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center text-2xl mb-4">
              🔍
            </div>
            <h3 className="text-lg font-semibold mb-2">Semantic Search</h3>
            <p className="text-gray-600 leading-relaxed">
              Go beyond keyword matching. Find papers based on meaning and context with
              embedding-powered semantic search across all of arXiv.
            </p>
          </div>

          <div className="bg-white p-8 rounded-xl border border-gray-200 hover:shadow-lg transition-shadow">
            <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center text-2xl mb-4">
              🎯
            </div>
            <h3 className="text-lg font-semibold mb-2">Personalized Feed</h3>
            <p className="text-gray-600 leading-relaxed">
              ML-powered recommendations based on your reading history and interests.
              Collaborative and content-based filtering combined.
            </p>
          </div>

          <div className="bg-white p-8 rounded-xl border border-gray-200 hover:shadow-lg transition-shadow">
            <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center text-2xl mb-4">
              🤖
            </div>
            <h3 className="text-lg font-semibold mb-2">Agentic Recommendations</h3>
            <p className="text-gray-600 leading-relaxed">
              LLM agents explain why each paper is recommended for your specific research
              context. Understand the reasoning behind every suggestion.
            </p>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="bg-blue-600 py-16">
        <div className="max-w-4xl mx-auto px-4 text-center">
          <h2 className="text-3xl font-bold text-white mb-4">
            Start discovering papers today
          </h2>
          <p className="text-blue-100 text-lg mb-8 max-w-xl mx-auto">
            Create a free account to get personalized recommendations and track your reading.
          </p>
          <div className="flex gap-4 justify-center">
            <Link
              to="/register"
              className="px-8 py-3.5 bg-white text-blue-600 rounded-xl hover:bg-blue-50 font-semibold text-lg transition-colors"
            >
              Get Started Free
            </Link>
            <a
              href="https://github.com/MisileLab/arxgorithm"
              target="_blank"
              rel="noopener noreferrer"
              className="px-8 py-3.5 border-2 border-white text-white rounded-xl hover:bg-blue-700 font-semibold text-lg transition-colors"
            >
              GitHub ⭐
            </a>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-gray-200 py-8 bg-white">
        <div className="max-w-6xl mx-auto px-4 flex flex-col md:flex-row items-center justify-between gap-4">
          <p className="text-sm text-gray-500">
            📚 arxgorithm — Open-source arXiv recommendations
          </p>
          <div className="flex gap-6">
            <a
              href="https://github.com/MisileLab/arxgorithm"
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm text-gray-500 hover:text-gray-700"
            >
              GitHub
            </a>
            <Link to="/search" className="text-sm text-gray-500 hover:text-gray-700">
              Search
            </Link>
            <Link to="/feed" className="text-sm text-gray-500 hover:text-gray-700">
              Feed
            </Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
