import type { Route } from "./+types/home";

export function meta({}: Route.MetaArgs) {
  return [
    { title: "arxgorithm — Personalized arXiv Paper Recommendations" },
    { name: "description", content: "Open-source personalized arXiv paper recommendation platform" },
  ];
}

export default function Home() {
  return (
    <div className="min-h-screen">
      {/* Hero */}
      <header className="bg-white border-b">
        <nav className="max-w-6xl mx-auto px-4 py-4 flex items-center justify-between">
          <h1 className="text-xl font-bold">
            📚 arxgorithm
          </h1>
          <div className="flex gap-4">
            <a href="/search" className="text-gray-600 hover:text-gray-900">Search</a>
            <a href="/feed" className="text-gray-600 hover:text-gray-900">Feed</a>
            <a href="/login" className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700">
              Sign In
            </a>
          </div>
        </nav>
      </header>

      {/* Landing */}
      <main className="max-w-4xl mx-auto px-4 py-20 text-center">
        <h2 className="text-5xl font-bold mb-6">
          Find papers that<br />
          <span className="text-blue-600">actually matter</span> to you
        </h2>
        <p className="text-xl text-gray-600 mb-10 max-w-2xl mx-auto">
          Open-source arXiv recommendation engine powered by collaborative filtering
          embeddings and agentic AI.
        </p>
        <div className="flex gap-4 justify-center">
          <a href="/search" className="bg-blue-600 text-white px-6 py-3 rounded-lg text-lg hover:bg-blue-700">
            Start Searching
          </a>
          <a href="https://github.com/MisileLab/arxgorithm" target="_blank" className="border border-gray-300 px-6 py-3 rounded-lg text-lg hover:bg-gray-50">
            GitHub ⭐
          </a>
        </div>
      </main>

      {/* Features */}
      <section className="max-w-6xl mx-auto px-4 py-16 grid grid-cols-1 md:grid-cols-3 gap-8">
        <div className="bg-white p-6 rounded-xl border">
          <div className="text-3xl mb-3">🎯</div>
          <h3 className="text-lg font-semibold mb-2">Personalized Feed</h3>
          <p className="text-gray-600">
            ML-powered recommendations based on your reading history and interests.
          </p>
        </div>
        <div className="bg-white p-6 rounded-xl border">
          <div className="text-3xl mb-3">🤖</div>
          <h3 className="text-lg font-semibold mb-2">Agentic Explanations</h3>
          <p className="text-gray-600">
            LLM agents explain why each paper is recommended for your research context.
          </p>
        </div>
        <div className="bg-white p-6 rounded-xl border">
          <div className="text-3xl mb-3">🔓</div>
          <h3 className="text-lg font-semibold mb-2">Open Source</h3>
          <p className="text-gray-600">
            AGPL-3.0 licensed. Self-host, customize, and contribute.
          </p>
        </div>
      </section>
    </div>
  );
}
