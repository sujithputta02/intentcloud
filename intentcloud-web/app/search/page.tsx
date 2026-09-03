"use client";

import { useState } from "react";
import { API_URL } from "@/lib/api";

interface SearchResult {
  file_id: string;
  filename: string;
  file_type?: string;
  sentence_text: string;
  matched_snippet?: string;
  relevance_score: number;
  relevance_percentage: number;
  rank: number;
  rrf_score?: number;
  rerank_score?: number;
  explanation: string;
  keywords?: string[];
  upload_time?: string;
}

interface SearchResponse {
  query: string;
  search_mode: string;
  parsed_intent: {
    topic: string;
    keywords: string[];
    confidence: number;
    intent_type?: string;
    has_time_constraint?: boolean;
  };
  is_confident_match: boolean;
  confidence_message: string;
  results: SearchResult[];
  count: number;
  metrics?: {
    latency_ms: number;
    dense_candidates?: number;
    sparse_candidates?: number;
    fused_candidates?: number;
    reranked_count?: number;
    device?: string;
  };
}

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const [searchMode, setSearchMode] = useState<"hybrid" | "dense" | "sparse" | "rrf_only">("hybrid");
  const [topK, setTopK] = useState<number>(3);
  const [isSearching, setIsSearching] = useState(false);
  const [searchResults, setSearchResults] = useState<SearchResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const executeSearch = async (queryString: string, mode: string = searchMode, count: number = topK) => {
    if (!queryString.trim()) {
      setError("Please enter a natural language search query");
      return;
    }

    setIsSearching(true);
    setError(null);

    try {
      const response = await fetch(
        `${API_URL}/search?query=${encodeURIComponent(queryString)}&top_k=${count}&search_mode=${mode}`,
        { method: "POST" }
      );

      if (!response.ok) {
        throw new Error(`Search request failed (${response.status}: ${response.statusText})`);
      }

      const data: SearchResponse = await response.json();
      setSearchResults(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Search query failed");
    } finally {
      setIsSearching(false);
    }
  };

  const handleFormSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    executeSearch(query, searchMode, topK);
  };

  const handleExampleClick = (example: string) => {
    setQuery(example);
    executeSearch(example, searchMode, topK);
  };

  const handleModeChange = (mode: "hybrid" | "dense" | "sparse" | "rrf_only") => {
    setSearchMode(mode);
    if (query.trim()) {
      executeSearch(query, mode, topK);
    }
  };

  const getBadgeColor = (filename: string) => {
    const ext = filename.split(".").pop()?.toLowerCase() || "";
    switch (ext) {
      case "pdf":
        return "bg-[#C96A45]/15 text-[#C96A45] dark:text-[#E08556] border-[#C96A45]/30";
      case "docx":
        return "bg-[#3B6FA0]/15 text-[#3B6FA0] dark:text-[#5B8FDB] border-[#3B6FA0]/30";
      case "txt":
        return "bg-[#5C8A5C]/15 text-[#5C8A5C] dark:text-[#7DB37D] border-[#5C8A5C]/30";
      default:
        return "bg-[var(--border-subtle)] text-[var(--text-secondary)] border-transparent";
    }
  };

  const getScoreBadge = (score: number) => {
    if (score >= 80) {
      return "bg-[var(--success)]/15 text-[var(--success)] border border-[var(--success)]/30";
    }
    if (score >= 50) {
      return "bg-[var(--warning)]/15 text-[var(--warning)] border border-[var(--warning)]/30";
    }
    return "bg-[var(--danger)]/15 text-[var(--danger)] border border-[var(--danger)]/30";
  };

  const getRankStyle = (rank: number) => {
    if (rank === 1) {
      return "bg-gradient-to-r from-amber-500/20 to-yellow-500/20 text-amber-600 dark:text-amber-400 border border-amber-500/40 shadow-sm";
    }
    if (rank === 2) {
      return "bg-slate-500/15 text-slate-700 dark:text-slate-300 border border-slate-500/30";
    }
    return "bg-amber-800/15 text-amber-800 dark:text-amber-300 border border-amber-800/30";
  };

  return (
    <div className="min-h-screen bg-[var(--bg-base)] text-[var(--text-primary)] py-10 px-4 sm:px-6 lg:px-8">
      <div className="max-w-4xl mx-auto space-y-8">
        {/* Title Header */}
        <div className="text-center space-y-2">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-[var(--accent)]/10 text-[var(--accent)] border border-[var(--accent)]/20 mb-1">
            <span>✨ Phase 4</span>
            <span>•</span>
            <span>Hybrid Dense + Sparse Reranking</span>
          </div>
          <h1 className="font-fraunces text-3xl sm:text-4xl font-bold tracking-tight">
            Intent-Aware Cognitive Search
          </h1>
          <p className="text-[var(--text-secondary)] text-sm sm:text-base max-w-2xl mx-auto">
            Find documents by describing their meaning. Phi-3 parses your intent, Qdrant retrieves candidates via dense & sparse index with Reciprocal Rank Fusion, and Cross-Encoder surfaces the exact top matches.
          </p>
        </div>

        {/* Mode Selector Strip */}
        <div className="flex flex-wrap items-center justify-between gap-3 p-2 rounded-2xl bg-[var(--bg-surface)] border border-[var(--border-subtle)] text-xs font-medium">
          <div className="flex flex-wrap items-center gap-1.5">
            <span className="text-[var(--text-secondary)] px-2 font-semibold">Mode:</span>
            {[
              { id: "hybrid", label: "⚡ Hybrid + Rerank (Phase 4)", desc: "Dense + Sparse + RRF + Cross-Encoder" },
              { id: "dense", label: "🧠 Dense Semantic", desc: "all-MiniLM-L6-v2" },
              { id: "sparse", label: "🔤 Sparse Keyword", desc: "Feature Hash BM25" },
              { id: "rrf_only", label: "🔀 RRF Fusion", desc: "Dense + Sparse (No Rerank)" },
            ].map((mode) => (
              <button
                key={mode.id}
                type="button"
                onClick={() => handleModeChange(mode.id as any)}
                title={mode.desc}
                className={`px-3 py-1.5 rounded-xl transition ${
                  searchMode === mode.id
                    ? "bg-[var(--accent)] text-white font-semibold shadow-sm"
                    : "text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-base)]"
                }`}
              >
                {mode.label}
              </button>
            ))}
          </div>

          <div className="flex items-center gap-2 pr-2">
            <span className="text-[var(--text-secondary)]">Top:</span>
            {[3, 5, 10].map((k) => (
              <button
                key={k}
                type="button"
                onClick={() => {
                  setTopK(k);
                  if (query.trim()) executeSearch(query, searchMode, k);
                }}
                className={`px-2 py-1 rounded-lg text-xs font-bold transition ${
                  topK === k
                    ? "bg-[var(--bg-base)] border border-[var(--accent)] text-[var(--accent)]"
                    : "text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
                }`}
              >
                {k}
              </button>
            ))}
          </div>
        </div>

        {/* Hero Search Bar */}
        <form onSubmit={handleFormSubmit} className="relative w-full">
          <div className="flex items-center gap-2 p-2.5 rounded-2xl bg-[var(--bg-surface)] border-2 border-[var(--border-subtle)] focus-within:border-[var(--accent)] shadow-sm transition">
            <span className="pl-3 text-xl text-[var(--text-secondary)]">🔍</span>
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Describe the file you are looking for (e.g. 'Kafka stream processing real-time notes')..."
              className="flex-1 bg-transparent border-none text-[var(--text-primary)] placeholder-[var(--text-secondary)] focus:outline-none text-base px-2 py-2"
            />
            <button
              type="submit"
              disabled={isSearching}
              className="px-6 py-2.5 rounded-xl font-semibold bg-[var(--accent)] text-white hover:bg-[var(--accent-hover)] transition disabled:opacity-50 shrink-0 shadow-sm"
            >
              {isSearching ? (
                <span className="flex items-center gap-2">
                  <span className="inline-block w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  Searching...
                </span>
              ) : (
                "Search"
              )}
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
            {/* Confidence Warning Banner if confidence is low */}
            {!searchResults.is_confident_match && (
              <div className="p-4 rounded-2xl bg-amber-500/10 border-2 border-amber-500/40 text-amber-700 dark:text-amber-300 flex items-start gap-3 shadow-sm">
                <span className="text-2xl shrink-0">⚠️</span>
                <div className="space-y-1 text-sm">
                  <h4 className="font-bold font-fraunces">No Confident Match Found</h4>
                  <p className="text-xs opacity-90 leading-relaxed">
                    {searchResults.confidence_message || "The top search candidates scored below the confidence threshold. The results below are weak/partial semantic matches."}
                  </p>
                  <p className="text-xs font-semibold pt-1">
                    Tip: Try using specific technical terms, keywords, or checking uploaded documents.
                  </p>
                </div>
              </div>
            )}

            {/* Parsed Intent & Metrics breakdown */}
            <div className="p-5 rounded-2xl bg-[var(--bg-surface)] border border-[var(--border-subtle)] space-y-4">
              <div className="flex flex-wrap items-center justify-between gap-2 border-b border-[var(--border-subtle)] pb-3">
                <div className="flex items-center gap-2">
                  <span className="text-lg">🧠</span>
                  <h3 className="font-fraunces font-bold text-sm text-[var(--text-primary)]">
                    Cognitive Intent & Pipeline Metrics
                  </h3>
                </div>
                {searchResults.metrics && (
                  <div className="flex items-center gap-2 text-xs font-mono text-[var(--text-secondary)]">
                    <span className="px-2 py-0.5 rounded-md bg-[var(--bg-base)] border border-[var(--border-subtle)]">
                      ⏱️ {searchResults.metrics.latency_ms} ms
                    </span>
                    {searchResults.metrics.device && (
                      <span className="px-2 py-0.5 rounded-md bg-[var(--bg-base)] border border-[var(--border-subtle)] uppercase">
                        ⚙️ {searchResults.metrics.device}
                      </span>
                    )}
                  </div>
                )}
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
                <div className="p-3 rounded-xl bg-[var(--bg-base)] border border-[var(--border-subtle)]">
                  <span className="text-[var(--text-secondary)] font-semibold uppercase block text-[10px] tracking-wider mb-0.5">
                    Target Topic
                  </span>
                  <span className="font-medium text-[var(--text-primary)] truncate block">
                    {searchResults.parsed_intent?.topic || searchResults.query}
                  </span>
                </div>

                <div className="p-3 rounded-xl bg-[var(--bg-base)] border border-[var(--border-subtle)]">
                  <span className="text-[var(--text-secondary)] font-semibold uppercase block text-[10px] tracking-wider mb-0.5">
                    Intent Tokens
                  </span>
                  <div className="flex flex-wrap gap-1 mt-0.5">
                    {searchResults.parsed_intent?.keywords?.length > 0 ? (
                      searchResults.parsed_intent.keywords.map((kw) => (
                        <span
                          key={kw}
                          className="px-1.5 py-0.2 rounded bg-[var(--bg-surface)] border border-[var(--border-subtle)] text-[var(--text-primary)] font-medium text-[11px]"
                        >
                          {kw}
                        </span>
                      ))
                    ) : (
                      <span className="text-[var(--text-secondary)]">General query</span>
                    )}
                  </div>
                </div>

                <div className="p-3 rounded-xl bg-[var(--bg-base)] border border-[var(--border-subtle)]">
                  <span className="text-[var(--text-secondary)] font-semibold uppercase block text-[10px] tracking-wider mb-0.5">
                    Fusion & Candidates
                  </span>
                  <span className="font-medium text-[var(--text-primary)] block">
                    {searchResults.metrics?.fused_candidates ?? 0} candidates fused (RRF k=60)
                  </span>
                </div>
              </div>
            </div>

            {/* Results cards */}
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h2 className="font-fraunces text-xl font-bold text-[var(--text-primary)]">
                  {searchResults.search_mode === "hybrid" ? "Top-3 Reranked Matches" : `Search Results (${searchResults.count})`}
                </h2>
                <span className="text-xs text-[var(--text-secondary)]">
                  Mode: <strong className="text-[var(--text-primary)] uppercase">{searchResults.search_mode}</strong>
                </span>
              </div>

              {searchResults.results.length === 0 ? (
                <div className="text-center py-12 p-8 rounded-2xl bg-[var(--bg-surface)] border border-[var(--border-subtle)] space-y-2">
                  <p className="text-sm text-[var(--text-secondary)]">
                    No documents matched your query in the index.
                  </p>
                </div>
              ) : (
                <div className="space-y-4">
                  {searchResults.results.map((res) => {
                    const ext = (res.file_type || res.filename.split(".").pop() || "TXT").toUpperCase();
                    const snippet = res.matched_snippet || res.sentence_text;

                    return (
                      <div
                        key={res.file_id + res.rank}
                        className="p-6 rounded-2xl bg-[var(--bg-surface)] border border-[var(--border-subtle)] hover:border-[var(--accent)]/50 transition shadow-sm space-y-4"
                      >
                        {/* Header Row: Rank, Filename, Match Score Badge */}
                        <div className="flex items-start justify-between gap-4">
                          <div className="flex items-center gap-2.5 min-w-0 flex-1">
                            <span className={`text-xs font-bold px-2.5 py-1 rounded-lg ${getRankStyle(res.rank)}`}>
                              #{res.rank}
                            </span>
                            <span className={`text-[10px] font-bold px-2 py-0.5 rounded uppercase border ${getBadgeColor(res.filename)}`}>
                              {ext}
                            </span>
                            <h3 className="font-fraunces font-bold text-base sm:text-lg text-[var(--text-primary)] truncate" title={res.filename}>
                              {res.filename}
                            </h3>
                          </div>

                          <div className="flex items-center gap-2 shrink-0">
                            <span className={`px-3 py-1 rounded-full text-xs font-bold whitespace-nowrap ${getScoreBadge(res.relevance_percentage)}`}>
                              {res.relevance_percentage}% match
                            </span>
                          </div>
                        </div>

                        {/* Explainable Matched Snippet (Golden Citation Box) */}
                        {snippet && (
                          <div className="space-y-1">
                            <span className="text-[10px] font-bold uppercase tracking-wider text-[var(--text-secondary)]">
                              Matched Passage / Citation:
                            </span>
                            <div className="p-4 rounded-xl bg-[var(--bg-base)] border-l-4 border-[var(--accent)] text-sm italic text-[var(--text-primary)] leading-relaxed shadow-inner">
                              &ldquo;{snippet}&rdquo;
                            </div>
                          </div>
                        )}

                        {/* Load-bearing Explanation & Keywords */}
                        <div className="pt-2 border-t border-[var(--border-subtle)] flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
                          <div className="flex items-start gap-2 text-[var(--text-secondary)] flex-1">
                            <span className="text-[var(--accent)] text-sm">💡</span>
                            <p className="leading-relaxed">
                              <strong className="font-semibold text-[var(--text-primary)]">Why this matched:</strong> {res.explanation}
                            </p>
                          </div>

                          <div className="flex items-center gap-2 shrink-0">
                            {res.rrf_score && (
                              <span className="text-[11px] font-mono text-[var(--text-secondary)] px-2 py-0.5 rounded bg-[var(--bg-base)] border border-[var(--border-subtle)]">
                                RRF: {res.rrf_score.toFixed(4)}
                              </span>
                            )}
                            <a
                              href={`${API_URL}/download/${res.file_id}`}
                              target="_blank"
                              rel="noreferrer"
                              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl font-semibold bg-[var(--accent)] text-white hover:bg-[var(--accent-hover)] transition shadow-sm text-xs"
                            >
                              📥 Download Original File
                            </a>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Empty state example queries */}
        {!searchResults && (
          <div className="pt-6 border-t border-[var(--border-subtle)] space-y-4">
            <h3 className="font-fraunces text-base font-bold text-[var(--text-primary)] text-center">
              Sample queries to test Hybrid Retrieval & Reranking:
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-w-2xl mx-auto">
              {[
                "Where are the Kafka stream processing notes?",
                "Find documents about Kafka performance optimization",
                "Show me microservices design patterns",
                "Where is the thesis draft about neural networks?",
                "Compare BM25 and dense retrieval approaches",
                "Where is the IntentCloud three-layer architecture design document?",
              ].map((sample) => (
                <button
                  key={sample}
                  type="button"
                  onClick={() => handleExampleClick(sample)}
                  className="p-3.5 rounded-xl text-left text-xs sm:text-sm font-medium bg-[var(--bg-surface)] border border-[var(--border-subtle)] hover:border-[var(--accent)] hover:bg-[var(--accent)]/5 transition text-[var(--text-primary)] shadow-sm"
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
