"use client";

import { useState } from "react";
import { 
  Sparkles, Zap, Brain, Binary, Shuffle, Search, AlertTriangle, 
  Clock, Cpu, Lightbulb, Download, Image as ImageIcon, ZoomIn, 
  X, Maximize2, Layers, Check, Palette, Copy 
} from "lucide-react";
import { API_URL } from "@/lib/api";
import { getFileCategory } from "@/lib/topics";
import HardwareOledPipeline from "@/components/HardwareOledPipeline";

export interface FigureEvidence {
  figure_id: string;
  figure_label: string;
  page: number;
  caption: string;
  ocr_text?: string;
  visual_description?: string;
  scene_description?: string;
  swatches?: Array<{ name: string; hex: string; rgb?: number[] }>;
  dominant_colors?: string[];
  visual_tags?: string[];
  image_url: string;
  thumbnail_url?: string;
  provenance: string;
  relevance_score?: number;
  bbox?: number[];
  color_mode?: string;
  mime_type?: string;
  width?: number;
  height?: number;
  extraction_method?: string;
}

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
  parent_section?: string;
  section_path?: string[];
  evidence_count?: number;
  matched_sections?: string[];
  expanded_context?: string;
  figures?: FigureEvidence[];
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
  const [searchMode, setSearchMode] = useState<"hybrid" | "visual" | "dense" | "sparse" | "rrf_only">("hybrid");
  const [topK, setTopK] = useState<number>(3);
  const [isSearching, setIsSearching] = useState(false);
  const [searchResults, setSearchResults] = useState<SearchResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [activeFigureModal, setActiveFigureModal] = useState<{
    figure: FigureEvidence;
    filename: string;
    file_id: string;
  } | null>(null);
  const [modalGrayscale, setModalGrayscale] = useState<boolean>(false);
  const [showOcrText, setShowOcrText] = useState<boolean>(false);
  const [copiedHex, setCopiedHex] = useState<string | null>(null);


  const syncHardwareOled = async (payload: { status?: string; query?: string; info?: string; match?: number }) => {
    try {
      await fetch("/api/hardware/oled", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
    } catch {
      // Non-blocking hardware sync
    }
  };

  const executeSearch = async (queryString: string, mode: string = searchMode, count: number = topK) => {
    if (!queryString.trim()) {
      setError("Please enter a natural language search query");
      return;
    }

    setIsSearching(true);
    setError(null);

    // Stream real-time stages to physical ESP32 OLED display
    syncHardwareOled({ status: "SEARCHING", query: queryString, info: "Cognitive Ingest" });
    const stageTimers: NodeJS.Timeout[] = [
      setTimeout(() => syncHardwareOled({ status: "PARSING", query: queryString, info: "llama3.2:1b" }), 1200),
      setTimeout(() => syncHardwareOled({ status: "ETHERNET", query: queryString, info: "LAN 192.168.2.2" }), 2800),
      setTimeout(() => syncHardwareOled({ status: "HYBRID", query: queryString, info: "Dense + Sparse" }), 4500),
      setTimeout(() => syncHardwareOled({ status: "RERANK", query: queryString, info: "MiniLM Neural" }), 7500),
    ];

    try {
      const response = await fetch(
        `${API_URL}/search?query=${encodeURIComponent(queryString)}&top_k=${count}&search_mode=${mode}`,
        { method: "POST" }
      );

      stageTimers.forEach(clearTimeout);

      if (!response.ok) {
        throw new Error(`Search request failed (${response.status}: ${response.statusText})`);
      }

      const data: SearchResponse = await response.json();
      setSearchResults(data);

      // Push final result to physical OLED screen
      const topMatch = data.results?.[0];
      const matchScore = topMatch ? topMatch.relevance_percentage : 0;
      syncHardwareOled({
        status: "PUSHED",
        query: queryString,
        info: `Pi 3B | ${matchScore}% Match`,
        match: matchScore,
      });
    } catch (err) {
      stageTimers.forEach(clearTimeout);
      syncHardwareOled({
        status: "ERROR",
        query: queryString,
        info: "Pi Search Error",
      });
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

  const handleModeChange = (mode: "hybrid" | "dense" | "sparse" | "rrf_only" | "visual") => {
    setSearchMode(mode);
    if (query.trim()) {
      executeSearch(query, mode, topK);
    }
  };

  const getBadgeColor = (filename: string) => {
    const ext = filename.split(".").pop()?.toLowerCase() || "";
    const category = getFileCategory(filename, ext);
    switch (category) {
      case "pdf":
        return "bg-[#C96A45]/15 text-[#C96A45] dark:text-[#E08556] border-[#C96A45]/30";
      case "docx":
        return "bg-[#3B6FA0]/15 text-[#3B6FA0] dark:text-[#5B8FDB] border-[#3B6FA0]/30";
      case "txt":
        return "bg-[#5C8A5C]/15 text-[#5C8A5C] dark:text-[#7DB37D] border-[#5C8A5C]/30";
      case "code":
        return "bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border-emerald-500/30";
      case "photo":
        return "bg-purple-500/15 text-purple-600 dark:text-purple-400 border-purple-500/30";
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
            <span className="inline-flex items-center gap-1"><Sparkles className="w-3.5 h-3.5" /> Phase 4</span>
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
              { id: "hybrid", label: "Hybrid + Rerank", icon: Zap, desc: "Dense + Sparse + RRF + Cross-Encoder" },
              { id: "visual", label: "Visual Evidence", icon: ImageIcon, desc: "Diagrams, Charts & Multimodal Figures" },
              { id: "dense", label: "Dense Semantic", icon: Brain, desc: "all-MiniLM-L6-v2" },
              { id: "sparse", label: "Sparse Keyword", icon: Binary, desc: "Feature Hash BM25" },
              { id: "rrf_only", label: "RRF Fusion", icon: Shuffle, desc: "Dense + Sparse (No Rerank)" },
            ].map((mode) => {
              const ModeIcon = mode.icon;
              return (
                <button
                  key={mode.id}
                  type="button"
                  onClick={() => handleModeChange(mode.id as any)}
                  title={mode.desc}
                  className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl transition ${
                    searchMode === mode.id
                      ? "bg-[var(--accent)] text-white font-semibold shadow-sm"
                      : "text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-base)]"
                  }`}
                >
                  <ModeIcon className="w-3.5 h-3.5" />
                  <span>{mode.label}</span>
                </button>
              );
            })}
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
            <Search className="w-5 h-5 text-[var(--text-secondary)] ml-3 shrink-0" />
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

        {/* Real-Time Pictorial Edge Memory & OLED Pipeline Animation */}
        <HardwareOledPipeline
          isSearching={isSearching}
          query={query}
          searchMode={searchMode}
          topResult={searchResults?.results?.[0] || null}
          metrics={searchResults?.metrics || null}
          parsedIntent={searchResults?.parsed_intent || null}
        />

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
                <AlertTriangle className="w-6 h-6 text-amber-500 shrink-0 mt-0.5" />
                <div className="space-y-1 text-sm">
                  <h4 className="font-bold font-fraunces">No Confident Match Found</h4>
                  <p className="text-xs opacity-90 leading-relaxed">
                    {searchResults.confidence_message || "No matching document in your library met the confidence threshold for this query."}
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
                  <Brain className="w-4 h-4 text-[var(--accent)]" />
                  <h3 className="font-fraunces font-bold text-sm text-[var(--text-primary)]">
                    Cognitive Intent & Pipeline Metrics
                  </h3>
                </div>
                {searchResults.metrics && (
                  <div className="flex items-center gap-2 text-xs font-mono text-[var(--text-secondary)]">
                    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-[var(--bg-base)] border border-[var(--border-subtle)]">
                      <Clock className="w-3 h-3 text-[var(--text-secondary)]" /> {searchResults.metrics.latency_ms} ms
                    </span>
                    {searchResults.metrics.device && (
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-[var(--bg-base)] border border-[var(--border-subtle)] uppercase">
                        <Cpu className="w-3 h-3 text-[var(--text-secondary)]" /> {searchResults.metrics.device}
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

            {/* Results cards — hidden when confidence gate abstains */}
            {searchResults.is_confident_match && (
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

                        {/* Document Memory Hierarchy & Evidence Badges */}
                        {(res.parent_section || (res.evidence_count && res.evidence_count > 1)) && (
                          <div className="flex flex-wrap items-center gap-2 pt-0.5">
                            {res.parent_section && (
                              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-[var(--accent)]/10 text-[var(--accent)] text-xs font-medium border border-[var(--accent)]/20">
                                <span className="opacity-70 text-[10px] font-mono uppercase">Section:</span>
                                <span className="font-semibold">{res.parent_section}</span>
                              </span>
                            )}
                            {res.evidence_count && res.evidence_count > 1 && (
                              <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 text-xs font-medium border border-emerald-500/20">
                                <span className="font-semibold">{res.evidence_count} evidence nodes</span>
                              </span>
                            )}
                          </div>
                        )}

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

                        {/* IEEE Figure Evidence Inline Cards */}
                        {res.figures && res.figures.length > 0 && (
                          <div className="space-y-2 pt-2 border-t border-[var(--border-subtle)]">
                            <div className="flex items-center justify-between">
                              <div className="flex items-center gap-1.5 text-xs font-semibold text-[var(--text-secondary)]">
                                <ImageIcon className="w-3.5 h-3.5 text-[var(--accent)]" />
                                <span className="uppercase tracking-wider text-[11px] font-bold">
                                  Figure Evidence (IEEE Citation Format)
                                </span>
                              </div>
                              <span className="text-[11px] text-[var(--text-secondary)] font-mono">
                                {res.figures.length} {res.figures.length === 1 ? "figure" : "figures"} extracted
                              </span>
                            </div>

                            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
                              {res.figures.map((fig, fIdx) => {
                                const fullImgUrl = fig.image_url.startsWith("http") ? fig.image_url : `${API_URL}${fig.image_url}`;
                                const thumbUrl = fig.thumbnail_url
                                  ? (fig.thumbnail_url.startsWith("http") ? fig.thumbnail_url : `${API_URL}${fig.thumbnail_url}`)
                                  : fullImgUrl;

                                const scorePct = fig.relevance_score
                                  ? Math.round(fig.relevance_score <= 1.0 ? fig.relevance_score * 100 : fig.relevance_score)
                                  : res.relevance_percentage;

                                return (
                                  <div
                                    key={fig.figure_id || fIdx}
                                    className="group relative flex flex-col rounded-xl bg-[var(--bg-base)] border border-[var(--border-subtle)] hover:border-[var(--accent)]/60 transition p-2.5 shadow-sm space-y-2"
                                  >
                                    {/* Grayscale-friendly Thumbnail Box */}
                                    <div
                                      onClick={() => {
                                        setActiveFigureModal({
                                          figure: fig,
                                          filename: res.filename,
                                          file_id: res.file_id,
                                        });
                                        setModalGrayscale(false);
                                        setShowOcrText(false);
                                      }}
                                      className="relative w-full h-36 rounded-lg overflow-hidden bg-black/5 dark:bg-white/5 border border-[var(--border-subtle)] flex items-center justify-center cursor-pointer group-hover:shadow-md transition"
                                      title={`Click to inspect ${fig.figure_label}: ${fig.caption}`}
                                    >
                                      <img
                                        src={thumbUrl}
                                        alt={fig.caption || fig.figure_label}
                                        className="w-full h-full object-contain transition-all duration-300 group-hover:scale-105"
                                        loading="lazy"
                                        onError={(e) => {
                                          const target = e.target as HTMLImageElement;
                                          if (target.src !== fullImgUrl) {
                                            target.src = fullImgUrl;
                                          } else {
                                            target.style.display = "none";
                                          }
                                        }}
                                      />

                                      {/* Sequential Figure Label & Score Badge */}
                                      <div className="absolute top-1.5 left-1.5 flex items-center gap-1">
                                        <span className="px-2 py-0.5 rounded-md text-[10px] font-bold font-mono bg-black/75 text-white shadow-sm border border-white/20">
                                          {fig.figure_label}
                                        </span>
                                        <span className="px-1.5 py-0.5 rounded-md text-[9px] font-semibold bg-emerald-600/90 text-white shadow-sm">
                                          {scorePct}% match
                                        </span>
                                      </div>

                                      {/* Click to Enlarge Hover Icon */}
                                      <div className="absolute inset-0 bg-black/30 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                                        <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-white text-black dark:bg-zinc-900 dark:text-white shadow flex items-center gap-1">
                                          <ZoomIn className="w-3 h-3" /> Inspect Details
                                        </span>
                                      </div>
                                    </div>

                                    {/* IEEE Caption immediately below thumbnail */}
                                    <div className="space-y-1.5">
                                      <p className="text-[11px] font-medium text-[var(--text-primary)] line-clamp-2 leading-snug">
                                        <strong className="font-bold text-[var(--accent)] mr-1">
                                          {fig.figure_label}:
                                        </strong>
                                        {fig.caption || "Embedded diagram evidence"}
                                      </p>

                                      {/* Detailed Scene Description */}
                                      {(fig.scene_description || fig.visual_description) && (
                                        <p className="text-[10px] text-[var(--text-secondary)] line-clamp-2 leading-relaxed bg-[var(--bg-surface)] p-1.5 rounded-md border border-[var(--border-subtle)]">
                                          <Sparkles className="w-2.5 h-2.5 text-[var(--accent)] inline mr-1" />
                                          {fig.scene_description || fig.visual_description}
                                        </p>
                                      )}

                                      {/* Swatches preview */}
                                      {fig.swatches && fig.swatches.length > 0 && (
                                        <div className="flex items-center gap-1 flex-wrap pt-0.5">
                                          {fig.swatches.slice(0, 6).map((swatch, sIdx) => (
                                            <span
                                              key={sIdx}
                                              className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[9px] font-mono bg-[var(--bg-surface)] border border-[var(--border-subtle)]"
                                              title={`${swatch.name}: ${swatch.hex}`}
                                            >
                                              <span
                                                className="w-2 h-2 rounded-full border border-black/10 shrink-0"
                                                style={{ backgroundColor: swatch.hex }}
                                              />
                                              <span>{swatch.hex}</span>
                                            </span>
                                          ))}
                                        </div>
                                      )}

                                      <div className="flex items-center justify-between text-[10px] text-[var(--text-secondary)] font-mono pt-1">
                                        <span>p. {fig.page}</span>
                                        <span className="truncate max-w-[120px]" title={fig.provenance}>
                                          {fig.provenance}
                                        </span>
                                      </div>
                                    </div>
                                  </div>
                                );
                              })}
                            </div>
                          </div>
                        )}


                        {/* Load-bearing Explanation & Keywords */}
                        <div className="pt-2 border-t border-[var(--border-subtle)] flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
                          <div className="flex items-start gap-2 text-[var(--text-secondary)] flex-1">
                            <Lightbulb className="w-4 h-4 text-[var(--accent)] shrink-0 mt-0.5" />
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
                              <Download className="w-3.5 h-3.5" />
                              <span>Download Original File</span>
                            </a>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
            )}
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

        {/* Interactive Figure Evidence Lightbox Modal */}
        {activeFigureModal && (
          <div
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4 animate-in fade-in duration-200"
            onClick={() => setActiveFigureModal(null)}
          >
            <div
              className="relative max-w-4xl w-full max-h-[90vh] bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-2xl shadow-2xl overflow-hidden flex flex-col"
              onClick={(e) => e.stopPropagation()}
            >
              {/* Modal Header */}
              <div className="flex items-center justify-between p-4 border-b border-[var(--border-subtle)] bg-[var(--bg-base)]">
                <div className="flex items-center gap-2.5 min-w-0">
                  <span className="px-2.5 py-1 rounded-lg text-xs font-bold font-mono bg-[var(--accent)] text-white shadow-sm">
                    {activeFigureModal.figure.figure_label}
                  </span>
                  <div className="min-w-0">
                    <h3 className="text-sm font-bold text-[var(--text-primary)] truncate">
                      {activeFigureModal.filename}
                    </h3>
                    <p className="text-xs text-[var(--text-secondary)] font-mono">
                      Provenance: {activeFigureModal.figure.provenance}
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-2 shrink-0">
                  {/* Toggle Grayscale / Full Color */}
                  <button
                    type="button"
                    onClick={() => setModalGrayscale(!modalGrayscale)}
                    className="px-3 py-1.5 rounded-xl text-xs font-semibold bg-[var(--bg-surface)] border border-[var(--border-subtle)] hover:border-[var(--accent)] text-[var(--text-primary)] transition"
                  >
                    {modalGrayscale ? "Show Color (RGB)" : "Grayscale (IEEE Print)"}
                  </button>

                  {/* Download Original Document */}
                  <a
                    href={`${API_URL}/download/${activeFigureModal.file_id}`}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-center gap-1 px-3 py-1.5 rounded-xl text-xs font-semibold bg-[var(--accent)] text-white hover:bg-[var(--accent-hover)] transition"
                  >
                    <Download className="w-3.5 h-3.5" /> Source PDF
                  </a>

                  <button
                    type="button"
                    onClick={() => setActiveFigureModal(null)}
                    className="p-1.5 rounded-xl text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-base)] transition"
                    aria-label="Close modal"
                  >
                    <X className="w-5 h-5" />
                  </button>
                </div>
              </div>

              {/* Modal Image Body */}
              <div className="flex-1 overflow-auto p-6 flex flex-col items-center justify-center bg-zinc-950/40 min-h-[300px]">
                <img
                  src={
                    activeFigureModal.figure.image_url.startsWith("http")
                      ? activeFigureModal.figure.image_url
                      : `${API_URL}${activeFigureModal.figure.image_url}`
                  }
                  alt={activeFigureModal.figure.caption || activeFigureModal.figure.figure_label}
                  className={`max-h-[55vh] max-w-full object-contain rounded-lg shadow-lg border border-white/10 transition-all ${
                    modalGrayscale ? "filter grayscale contrast-125" : ""
                  }`}
                />
              </div>

              {/* Modal Footer: Caption, Scene Understanding, Color Swatches & OCR */}
              <div className="p-4 border-t border-[var(--border-subtle)] bg-[var(--bg-surface)] space-y-3 text-xs max-h-[35vh] overflow-y-auto scrollbar-thin">
                <div className="p-3 rounded-xl bg-[var(--bg-base)] border border-[var(--border-subtle)]">
                  <p className="font-serif italic text-sm text-[var(--text-primary)] leading-relaxed">
                    <strong className="font-sans not-italic font-bold text-[var(--accent)] mr-1.5">
                      {activeFigureModal.figure.figure_label}:
                    </strong>
                    {activeFigureModal.figure.caption}
                  </p>
                  {activeFigureModal.figure.bbox && (
                    <p className="text-[10px] text-[var(--text-secondary)] font-mono mt-1">
                      Coordinates (Bounding Box): [{activeFigureModal.figure.bbox.join(", ")}]
                    </p>
                  )}
                </div>

                {/* Detailed Scene Understanding */}
                {activeFigureModal.figure.scene_description && (
                  <div className="p-3 rounded-xl bg-[var(--bg-base)] border border-[var(--border-subtle)] space-y-1">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-[var(--accent)] flex items-center gap-1.5">
                      <Sparkles className="w-3.5 h-3.5" />
                      Visual Scene Breakdown & VLM Analysis
                    </span>
                    <p className="text-xs text-[var(--text-primary)] leading-relaxed">
                      {activeFigureModal.figure.scene_description}
                    </p>
                  </div>
                )}

                {/* Extracted Brand Swatches Grid */}
                {activeFigureModal.figure.swatches && activeFigureModal.figure.swatches.length > 0 && (
                  <div className="p-3 rounded-xl bg-[var(--bg-base)] border border-[var(--border-subtle)] space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-[10px] font-bold uppercase tracking-wider text-[var(--text-secondary)] flex items-center gap-1.5">
                        <Palette className="w-3.5 h-3.5 text-[var(--accent)]" />
                        Extracted Color Swatches & Palette ({activeFigureModal.figure.swatches.length})
                      </span>
                      <span className="text-[10px] text-[var(--text-muted)]">Click swatch to copy hex</span>
                    </div>

                    <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-2">
                      {activeFigureModal.figure.swatches.map((swatch, sIdx) => {
                        const isCopied = copiedHex === swatch.hex;
                        return (
                          <div
                            key={sIdx}
                            onClick={() => {
                              navigator.clipboard.writeText(swatch.hex);
                              setCopiedHex(swatch.hex);
                              setTimeout(() => setCopiedHex(null), 1800);
                            }}
                            className="flex flex-col items-center p-2 rounded-xl bg-[var(--bg-surface)] border border-[var(--border-subtle)] hover:border-[var(--accent)] transition cursor-pointer group text-center space-y-1.5 shadow-xs"
                            title={`Click to copy ${swatch.hex}`}
                          >
                            <div
                              className="w-10 h-10 rounded-lg shadow-inner border border-black/15 dark:border-white/20 group-hover:scale-105 transition flex items-center justify-center relative"
                              style={{ backgroundColor: swatch.hex }}
                            >
                              {isCopied && (
                                <span className="absolute inset-0 bg-black/40 rounded-lg flex items-center justify-center text-white text-[10px] font-bold">
                                  ✓
                                </span>
                              )}
                            </div>
                            <span className="text-[11px] font-semibold text-[var(--text-primary)] truncate max-w-full">
                              {swatch.name}
                            </span>
                            <span className="text-[10px] font-mono text-[var(--text-secondary)] font-medium">
                              {swatch.hex}
                            </span>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}

                {/* Optional OCR / Diagram Labels Accordion */}
                {(activeFigureModal.figure.ocr_text || activeFigureModal.figure.visual_description) && (
                  <div>
                    <button
                      type="button"
                      onClick={() => setShowOcrText(!showOcrText)}
                      className="text-xs font-semibold text-[var(--accent)] hover:underline inline-flex items-center gap-1"
                    >
                      {showOcrText ? "Hide Diagram Labels & Text" : "View Extracted Diagram Labels & Text (OCR)"}
                    </button>
                    {showOcrText && (
                      <div className="mt-2 p-3 rounded-xl bg-[var(--bg-base)] border border-[var(--border-subtle)] text-[11px] font-mono text-[var(--text-secondary)] whitespace-pre-wrap max-h-32 overflow-y-auto">
                        {activeFigureModal.figure.ocr_text || activeFigureModal.figure.visual_description}
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

