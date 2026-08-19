"use client";

import { useState } from "react";

interface SearchResult {
  file_id: string;
  filename: string;
  sentence_text: string;
  relevance_score: number;
  rank: number;
  explanation: string;
  relevance_percentage: number;
}

interface SearchResponse {
  query: string;
  parsed_intent: {
    topic: string;
    keywords: string[];
    confidence: number;
  };
  results: SearchResult[];
  count: number;
}

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const [isSearching, setIsSearching] = useState(false);
  const [searchResults, setSearchResults] = useState<SearchResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  const executeSearch = async (queryString: string) => {
    if (!queryString.trim()) {
      setError("Please enter a search prompt");
      return;
    }

    setIsSearching(true);
    setError(null);
    setSearchResults(null);

    try {
      const response = await fetch(
        `${API_URL}/search?query=${encodeURIComponent(queryString)}&top_k=5`,
        { method: "POST" }
      );

      if (!response.ok) {
        throw new Error(`Search request failed (${response.status})`);
      }

      const data: SearchResponse = await response.json();
      setSearchResults(data);

      if (data.count === 0) {
        setError("No semantic matches found. Try asking in different terms.");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Search query failed");
    } finally {
      setIsSearching(false);
    }
  };

  const handleFormSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    executeSearch(query);
  };

  const handleExampleClick = (example: string) => {
    setQuery(example);
    executeSearch(example);
  };

  const getBadgeColor = (filename: string) => {
    const ext = filename.split(".").pop()?.toLowerCase() || "";
    switch (ext) {
      case "pdf":
        return "bg-[#C96A45]/15 text-[#C96A45] dark:text-[#E08556]";
      case "docx":
        return "bg-[#3B6FA0]/15 text-[#3B6FA0] dark:text-[#5B8FDB]";
      case "txt":
        return "bg-[#5C8A5C]/15 text-[#5C8A5C] dark:text-[#7DB37D]";
      default:
        return "bg-[var(--border-subtle)] text-[var(--text-secondary)]";
    }
  };

  const getScoreBadge = (score: number) => {
    if (score >= 70) {
      return "bg-[var(--success)]/15 text-[var(--success)] border border-[var(--success)]/30";
    }
    if (score >= 40) {
      return "bg-[var(--warning)]/15 text-[var(--warning)] border border-[var(--warning)]/30";
    }
    return "bg-[var(--danger)]/15 text-[var(--danger)] border border-[var(--danger)]/30";
  };

  return (
    <div className="min-h-screen bg-[var(--bg-base)] text-[var(--text-primary)] py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-4xl mx-auto space-y-10">
        {/* Title */}
        <div className="text-center space-y-2">
          <h1 className="font-fraunces text-3xl sm:text-4xl font-bold tracking-tight">
            Intent Search
          </h1>
          <p className="text-[var(--text-secondary)] text-base max-w-xl mx-auto">
            Search your document corpus using natural language queries.
          </p>
        </div>

        {/* Hero Search Bar */}
        <form onSubmit={handleFormSubmit} className="relative w-full">
          <div className="flex items-center gap-2 p-2 rounded-2xl bg-[var(--bg-surface)] border-2 border-[var(--border-subtle)] focus-within:border-[var(--accent)] shadow-sm transition">
            <span className="pl-3 text-lg text-[var(--text-secondary)]">🔍</span>
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Find the report where I discussed Kafka and microservices..."
              className="flex-1 bg-transparent border-none text-[var(--text-primary)] placeholder-[var(--text-secondary)] focus:outline-none text-base px-2 py-2"
            />
            <button
              type="submit"
              disabled={isSearching}
              className="px-6 py-2.5 rounded-xl font-semibold bg-[var(--accent)] text-white hover:bg-[var(--accent-hover)] transition disabled:opacity-50 shrink-0"
            >
              {isSearching ? "Searching..." : "Search"}
            </button>
          </div>
        </form>

        {/* Error message */}
        {error && (
          <div className="p-4 rounded-xl bg-[var(--danger)]/10 border border-[var(--danger)]/30 text-[var(--danger)] text-sm font-medium text-center">
            {error}
          </div>
        )}

        {/* Search Results & Intent Area */}
        {searchResults && (
          <div className="space-y-6">
            {/* Parsed Intent breakdown */}
            {searchResults.parsed_intent && (
              <div className="p-5 rounded-2xl bg-[var(--bg-surface)] border border-[var(--border-subtle)] space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span>🧠</span>
                    <h3 className="font-fraunces font-bold text-sm text-[var(--text-primary)]">
                      Understood Intent
                    </h3>
                  </div>
                  <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-[var(--accent)]/10 text-[var(--accent)]">
                    Confidence: {(searchResults.parsed_intent.confidence * 100).toFixed(0)}%
                  </span>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                  <div className="p-3 rounded-lg bg-[var(--bg-base)] border border-[var(--border-subtle)]">
                    <span className="text-[var(--text-secondary)] font-semibold uppercase block text-[10px] tracking-wider mb-0.5">
                      Target Topic
                    </span>
                    <span className="font-medium text-[var(--text-primary)]">
                      {searchResults.parsed_intent.topic || "General Retrieval"}
                    </span>
                  </div>

                  {searchResults.parsed_intent.keywords.length > 0 && (
                    <div className="p-3 rounded-lg bg-[var(--bg-base)] border border-[var(--border-subtle)]">
                      <span className="text-[var(--text-secondary)] font-semibold uppercase block text-[10px] tracking-wider mb-0.5">
                        Key Search Tokens
                      </span>
                      <div className="flex flex-wrap gap-1 mt-1">
                        {searchResults.parsed_intent.keywords.map((kw) => (
                          <span
                            key={kw}
                            className="px-2 py-0.5 rounded bg-[var(--bg-surface)] border border-[var(--border-subtle)] text-[var(--text-primary)] font-medium"
                          >
                            {kw}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Results cards */}
            <div className="space-y-4">
              <h2 className="font-fraunces text-xl font-bold text-[var(--text-primary)]">
                Ranked Results ({searchResults.count})
              </h2>

              <div className="space-y-4">
                {searchResults.results.map((res) => {
                  const ext = res.filename.split(".").pop()?.toUpperCase() || "TXT";
                  return (
                    <div
                      key={res.file_id + res.rank}
                      className="p-6 rounded-2xl bg-[var(--bg-surface)] border border-[var(--border-subtle)] hover:border-[var(--accent)]/40 transition space-y-3"
                    >
                      <div className="flex items-start justify-between gap-4">
                        <div className="flex items-center gap-2 min-w-0">
                          <span
                            className={`text-xs font-bold px-2 py-0.5 rounded uppercase ${getBadgeColor(
                              res.filename
                            )}`}
                          >
                            {ext}
                          </span>
                          <h3 className="font-fraunces font-bold text-base text-[var(--text-primary)] truncate">
                            {res.filename}
                          </h3>
                        </div>

                        <span
                          className={`px-3 py-1 rounded-full text-xs font-bold whitespace-nowrap ${getScoreBadge(
                            res.relevance_percentage
                          )}`}
                        >
                          {res.relevance_percentage}% match
                        </span>
                      </div>

                      {/* Excerpt */}
                      <div className="p-4 rounded-xl bg-[var(--bg-base)] border-l-4 border-[var(--accent)] text-sm italic text-[var(--text-primary)] leading-relaxed">
                        "{res.sentence_text}"
                      </div>

                      {/* Load-bearing Explanation */}
                      <div className="pt-1 flex items-start gap-2 text-xs text-[var(--text-secondary)]">
                        <span className="text-[var(--accent)] text-sm">💡</span>
                        <p className="leading-relaxed">
                          <strong className="font-semibold text-[var(--text-primary)]">
                            Why this matched:
                          </strong>{" "}
                          {res.explanation}
                        </p>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        )}

        {/* Empty state example queries */}
        {!searchResults && (
          <div className="pt-6 border-t border-[var(--border-subtle)] space-y-4">
            <h3 className="font-fraunces text-base font-bold text-[var(--text-primary)] text-center">
              Sample queries to try:
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-w-2xl mx-auto">
              {[
                "Find the report where I discussed Kafka and microservices",
                "Where is the thesis draft about neural networks?",
                "Show me all project documentation",
                "Find files related to machine learning and embeddings",
              ].map((sample) => (
                <button
                  key={sample}
                  type="button"
                  onClick={() => handleExampleClick(sample)}
                  className="p-3.5 rounded-xl text-left text-xs sm:text-sm font-medium bg-[var(--bg-surface)] border border-[var(--border-subtle)] hover:border-[var(--accent)] hover:bg-[var(--accent)]/5 transition text-[var(--text-primary)]"
                >
                  {sample}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
