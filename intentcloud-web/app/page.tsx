"use client";

import Link from "next/link";
import { useEffect, useState, useRef } from "react";
import { TOPIC_DEFINITIONS, classifyFile, countFilesByTopic } from "@/lib/topics";
import { API_URL } from "@/lib/api";

interface UploadedFile {
  file_id: string;
  name: string;
  size_bytes: number;
  modified: number;
  extension: string;
  topic_tags?: string[];
}

interface StatsResponse {
  total_vectors: number;
  total_files: number;
  collection: string;
  vector_dim: number;
  status: string;
}

interface SearchResult {
  file_id: string;
  filename: string;
  file_type?: string;
  sentence_text: string;
  matched_snippet?: string;
  relevance_score: number;
  rank: number;
  explanation: string;
  relevance_percentage: number;
}

interface SearchResponse {
  query: string;
  search_mode: string;
  is_confident_match: boolean;
  confidence_message: string;
  results: SearchResult[];
  count: number;
}

interface TopicCluster {
  title: string;
  filesCount: number;
  color: string;
  iconColor: string;
  keyword: string;
}

export default function Home() {
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [stats, setStats] = useState<StatsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeFilter, setActiveFilter] = useState<string>("All files");
  const [activeTopicFilter, setActiveTopicFilter] = useState<string | null>(null);
  const [menuOpen, setMenuOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<SearchResponse | null>(null);
  const [isSearching, setIsSearching] = useState(false);
  const [uploadModalOpen, setUploadModalOpen] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [toastMessage, setToastMessage] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const showToast = (msg: string) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 3500);
  };

  const fetchData = async () => {
    try {
      const [statsRes, filesRes] = await Promise.all([
        fetch(`${API_URL}/stats`).catch(() => null),
        fetch(`${API_URL}/files`).catch(() => null),
      ]);

      if (statsRes && statsRes.ok) {
        const statsData = await statsRes.json();
        setStats(statsData);
      }

      if (filesRes && filesRes.ok) {
        const filesData = await filesRes.json();
        setFiles(filesData.uploaded_files || []);
      } else {
        setFiles([]);
      }
    } catch {
      setFiles([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 8000);
    return () => clearInterval(interval);
  }, []);

  const handleSearch = async (e?: React.FormEvent, directQuery?: string) => {
    if (e) e.preventDefault();
    const q = directQuery !== undefined ? directQuery : searchQuery;

    if (!q.trim()) {
      setSearchResults(null);
      return;
    }

    setIsSearching(true);
    try {
      const res = await fetch(
        `${API_URL}/search?query=${encodeURIComponent(q)}&top_k=3&search_mode=hybrid`,
        { method: "POST" }
      );
      if (res.ok) {
        const data: SearchResponse = await res.json();
        setSearchResults(data);
      } else {
        setSearchResults(null);
      }
    } catch {
      setSearchResults(null);
    } finally {
      setIsSearching(false);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || e.target.files.length === 0) return;
    setIsUploading(true);

    let uploadedCount = 0;
    let failedCount = 0;
    for (const file of Array.from(e.target.files)) {
      try {
        const formData = new FormData();
        formData.append("file", file);
        const res = await fetch(`${API_URL}/upload`, {
          method: "POST",
          body: formData,
        });
        if (res.ok) {
          uploadedCount++;
        } else {
          failedCount++;
        }
      } catch (err) {
        failedCount++;
        console.error(err);
      }
    }

    setIsUploading(false);
    setUploadModalOpen(false);
    if (uploadedCount > 0) {
      showToast(`Uploaded ${uploadedCount} document${uploadedCount > 1 ? "s" : ""} successfully!`);
    } else {
      showToast("Upload failed. Make sure the backend is running on port 8000.");
    }
    fetchData();
  };

  const handleDeleteFile = async (fileId: string, fileName: string) => {
    if (!confirm(`Are you sure you want to delete "${fileName}" from memory?`)) {
      return;
    }

    setDeletingId(fileId);
    try {
      const res = await fetch(`${API_URL}/files/${fileId}`, {
        method: "DELETE",
      });
      if (res.ok) {
        setFiles((prev) => prev.filter((f) => f.file_id !== fileId));
        showToast(`Deleted "${fileName}" successfully`);
        fetchData();
      } else {
        showToast(`Failed to delete file (${res.status})`);
      }
    } catch (err) {
      showToast("Error deleting file from server");
    } finally {
      setDeletingId(null);
    }
  };

  const formatSize = (bytes: number) => {
    if (!bytes) return "0 B";
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const getRelativeTime = (timestamp: number) => {
    if (!timestamp) return "Uploaded recently";
    const diff = Math.max(0, Date.now() - timestamp * 1000);
    const mins = Math.floor(diff / 60000);
    if (mins < 1) return "Uploaded just now";
    if (mins < 60) return `Uploaded ${mins} mins ago`;
    const hours = Math.floor(mins / 60);
    if (hours < 24) return `Uploaded ${hours} hours ago`;
    return `Uploaded ${Math.floor(hours / 24)} days ago`;
  };

  const topicCounts = countFilesByTopic(files);

  const dynamicTopicCards: TopicCluster[] = TOPIC_DEFINITIONS.map((topic) => ({
    title: topic.title,
    filesCount: topicCounts[topic.title] ?? 0,
    color: topic.color,
    iconColor: topic.iconColor,
    keyword: topic.title,
  }));

  const totalIndexedTopics = dynamicTopicCards.filter((t) => t.filesCount > 0).length;

  const displayFiles = files.filter((f) => {
    const ext = f.extension?.toLowerCase() || "";

    if (activeTopicFilter) {
      const fileTopic = classifyFile(f.name, f.topic_tags ?? []);
      if (fileTopic !== activeTopicFilter) return false;
    }

    if (activeFilter === "All files") return true;
    if (activeFilter === "PDF") return ext === "pdf";
    if (activeFilter === "Photos" || activeFilter === "DOCX") return ext === "docx";
    if (activeFilter === "Vectors" || activeFilter === "TXT") return ext === "txt";
    return true;
  });

  return (
    <div className="min-h-screen bg-[var(--bg-base)] text-[var(--text-primary)] px-4 sm:px-6 lg:px-8 py-8">
      {/* Toast Notification */}
      {toastMessage && (
        <div className="fixed bottom-6 right-6 z-50 px-5 py-3 rounded-2xl bg-[var(--text-primary)] text-[var(--bg-surface)] font-medium text-sm shadow-floating animate-in fade-in slide-in-from-bottom-3">
          {toastMessage}
        </div>
      )}

      <div className="max-w-7xl mx-auto space-y-10">
        {/* HERO BANNER */}
        <section className="relative rounded-[32px] overflow-hidden p-8 sm:p-10 shadow-hero text-white bg-gradient-to-br from-[#2D1B22] via-[#6E433E] to-[#B87B56]">
          <div
            className="absolute inset-0 opacity-40 mix-blend-overlay pointer-events-none"
            style={{
              backgroundImage:
                "radial-gradient(circle at 70% 30%, rgba(255, 230, 200, 0.8) 0%, transparent 60%)",
            }}
          />

          <div className="relative z-10 flex items-start justify-between gap-4 mb-10">
            <div>
              <h1 className="font-fraunces text-3xl sm:text-4xl font-bold tracking-tight">
                Good morning, Researcher
              </h1>
              <p className="text-sm sm:text-base opacity-90 mt-1 font-light">
                {files.length > 0
                  ? `You have ${files.length} documents stored across ${totalIndexedTopics || 1} topics in your memory.`
                  : "No documents stored yet. Upload files below to start your cognitive memory."}
              </p>
            </div>

            {/* Floating Action Controls */}
            <div className="flex items-center gap-3 relative">
              <button
                onClick={() => setMenuOpen(!menuOpen)}
                type="button"
                className="w-11 h-11 rounded-full bg-white text-[#1C1917] flex items-center justify-center text-xl font-bold shadow-lg hover:scale-105 active:scale-95 transition"
                aria-label="New action"
              >
                {menuOpen ? "✕" : "+"}
              </button>

              <button
                onClick={() => setUploadModalOpen(true)}
                type="button"
                className="w-11 h-11 rounded-full bg-white text-[#1C1917] flex items-center justify-center text-base shadow-lg hover:scale-105 active:scale-95 transition"
                title="Upload files"
              >
                🔔
              </button>

              {menuOpen && (
                <div className="absolute right-0 top-14 w-56 rounded-2xl bg-[#2D2A26]/90 backdrop-blur-xl text-white shadow-floating border border-white/10 p-2 z-50 animate-in fade-in zoom-in-95">
                  <button
                    onClick={() => {
                      setUploadModalOpen(true);
                      setMenuOpen(false);
                    }}
                    className="w-full text-left px-4 py-2.5 rounded-xl hover:bg-white/10 text-sm font-medium transition flex items-center justify-between"
                  >
                    <span>Upload New File</span>
                    <span className="text-xs text-white/50">Browse</span>
                  </button>
                  <Link
                    href="/search"
                    onClick={() => setMenuOpen(false)}
                    className="w-full text-left px-4 py-2.5 rounded-xl hover:bg-white/10 text-sm font-medium transition flex items-center justify-between"
                  >
                    <span>Natural Intent Search</span>
                    <span className="text-xs text-white/50">↵</span>
                  </Link>
                  <div className="h-px bg-white/10 my-1" />
                  <Link
                    href="/dashboard"
                    onClick={() => setMenuOpen(false)}
                    className="w-full text-left px-4 py-2.5 rounded-xl hover:bg-white/10 text-sm font-medium transition"
                  >
                    System Stats ({stats?.total_vectors || 0} vectors)
                  </Link>
                </div>
              )}
            </div>
          </div>

          {/* Horizontal Folder Cards */}
          <div className="relative z-10">
            <div className="flex gap-4 overflow-x-auto pb-2 no-scrollbar snap-x">
              {dynamicTopicCards.map((topic) => (
                <div
                  key={topic.title}
                  onClick={() => {
                    setSearchResults(null);
                    setSearchQuery("");
                    setActiveTopicFilter((current) =>
                      current === topic.title ? null : topic.title
                    );
                  }}
                  className={`min-w-[210px] sm:min-w-[230px] p-5 rounded-2xl bg-white text-[#1C1917] shadow-card hover:shadow-card-hover hover:-translate-y-1 transition-all duration-200 cursor-pointer snap-start flex flex-col justify-between ${
                    activeTopicFilter === topic.title
                      ? "ring-2 ring-[#B87B56] ring-offset-2 ring-offset-transparent"
                      : ""
                  }`}
                >
                  <div className="flex items-center justify-between mb-6">
                    <div className="w-8 h-8 rounded-lg bg-neutral-100 flex items-center justify-center">
                      <svg
                        className="w-5 h-5"
                        fill={topic.iconColor}
                        viewBox="0 0 24 24"
                      >
                        <path d="M20 6h-8l-2-2H4c-1.1 0-1.99.9-1.99 2L2 18c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2zm0 12H4V8h16v10z" />
                      </svg>
                    </div>
                  </div>

                  <div>
                    <h3 className="font-semibold text-base text-[#1C1917] tracking-tight truncate">
                      {topic.title}
                    </h3>
                    <p className="text-xs text-[#78716C] mt-0.5">
                      {topic.filesCount} {topic.filesCount === 1 ? "File" : "Total Files"}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* MY FILES & SEARCH SECTION */}
        <section className="space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <h2 className="font-fraunces text-2xl sm:text-3xl font-bold text-[var(--text-primary)]">
              My files
            </h2>

            {/* Search Bar */}
            <form onSubmit={(e) => handleSearch(e)} className="w-full sm:max-w-xl">
              <div className="flex items-center gap-2 p-1.5 pl-3.5 pr-1.5 rounded-full bg-[var(--bg-surface)] border border-[var(--border-subtle)] focus-within:border-[var(--accent)] shadow-sm transition">
                <span className="shrink-0 text-sm text-[var(--text-secondary)]" aria-hidden>
                  🔍
                </span>
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Ask intent query (e.g. Kafka report)..."
                  className="flex-1 min-w-0 bg-transparent border-none py-2 text-sm text-[var(--text-primary)] placeholder-[var(--text-secondary)] focus:outline-none"
                />
                {searchQuery && (
                  <button
                    type="button"
                    onClick={() => {
                      setSearchQuery("");
                      setSearchResults(null);
                    }}
                    className="shrink-0 w-7 h-7 flex items-center justify-center rounded-full text-xs text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-base)] transition"
                    aria-label="Clear search"
                  >
                    ✕
                  </button>
                )}
                <button
                  type="submit"
                  disabled={isSearching}
                  className="shrink-0 px-4 py-2 bg-[var(--text-primary)] text-[var(--bg-surface)] rounded-full text-xs font-semibold hover:opacity-90 transition disabled:opacity-50"
                >
                  {isSearching ? "..." : "Find"}
                </button>
              </div>
            </form>
          </div>

          {/* Filter Pills */}
          <div className="flex items-center justify-between gap-4 flex-wrap">
            <div className="flex items-center gap-2">
              {["All files", "PDF", "Photos", "Vectors"].map((pill) => (
                <button
                  key={pill}
                  type="button"
                  onClick={() => {
                    setActiveFilter(pill);
                    setSearchResults(null);
                    setActiveTopicFilter(null);
                  }}
                  className={`px-4 py-2 rounded-full text-sm font-medium transition select-none ${
                    activeFilter === pill
                      ? "bg-[var(--text-primary)] text-[var(--bg-surface)] font-semibold shadow-sm"
                      : "bg-[var(--bg-surface)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] border border-[var(--border-subtle)]"
                  }`}
                >
                  {pill}
                </button>
              ))}
            </div>

            <div className="text-xs font-medium text-[var(--text-secondary)] flex items-center gap-1 bg-[var(--bg-surface)] border border-[var(--border-subtle)] px-3 py-2 rounded-full">
              <span>{files.length} items total</span>
            </div>
          </div>

          {/* Search Results View */}
          {searchResults ? (
            <div className="space-y-4">
              <div className="flex items-center justify-between flex-wrap gap-2">
                <span className="text-sm font-semibold text-[var(--text-secondary)]">
                  Hybrid results for "{searchResults.query}" ({searchResults.count})
                </span>
                <button
                  onClick={() => {
                    setSearchResults(null);
                    setSearchQuery("");
                  }}
                  className="text-xs text-[var(--accent)] hover:underline"
                >
                  Clear search
                </button>
              </div>

              {!searchResults.is_confident_match && (
                <div className="p-4 rounded-xl bg-[var(--warning)]/10 border border-[var(--warning)]/30 text-sm text-[var(--text-primary)]">
                  {searchResults.confidence_message || "No confident match found."}
                </div>
              )}

              {searchResults.results.length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {searchResults.results.map((res) => (
                    <div
                      key={res.file_id + res.rank}
                      className="p-5 rounded-2xl bg-[var(--bg-surface)] border border-[var(--border-subtle)] shadow-card hover:shadow-card-hover transition-all flex flex-col justify-between space-y-3"
                    >
                      <div className="flex items-start gap-4">
                        <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-amber-500/20 to-amber-600/30 text-amber-700 dark:text-amber-300 flex items-center justify-center text-xl shrink-0 p-3 shadow-inner">
                          📄
                        </div>
                        <div className="min-w-0 flex-1">
                          <h4 className="font-semibold text-[15px] text-[var(--text-primary)] truncate">
                            {res.filename}
                          </h4>
                          <div className="flex items-center gap-2 mt-0.5">
                            <span className="text-xs font-bold text-[var(--accent)]">
                              {res.relevance_percentage}% match
                            </span>
                          </div>
                        </div>
                      </div>

                      <div className="p-3 rounded-xl bg-[var(--bg-base)] text-xs text-[var(--text-primary)] italic line-clamp-2">
                        "{res.sentence_text}"
                      </div>

                      <div className="pt-2 border-t border-[var(--border-subtle)] flex items-center justify-between text-xs">
                        <span className="text-[var(--text-secondary)] truncate">
                          {res.explanation}
                        </span>
                        <a
                          href={`${API_URL}/download/${res.file_id}`}
                          target="_blank"
                          rel="noreferrer"
                          className="px-2.5 py-1 rounded-lg bg-[var(--bg-base)] border border-[var(--border-subtle)] font-medium hover:text-[var(--accent)]"
                        >
                          Download
                        </a>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-16 bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-3xl p-8">
                  <p className="text-[var(--text-secondary)] text-sm">
                    {searchResults.is_confident_match
                      ? `No matching documents found for "${searchResults.query}".`
                      : searchResults.confidence_message}
                  </p>
                </div>
              )}
            </div>
          ) : (
            /* Real Files Grid */
            <div>
              {activeTopicFilter && (
                <div className="flex items-center justify-between mb-4">
                  <span className="text-sm font-semibold text-[var(--text-secondary)]">
                    Showing {displayFiles.length} file{displayFiles.length === 1 ? "" : "s"} in{" "}
                    {activeTopicFilter}
                  </span>
                  <button
                    type="button"
                    onClick={() => setActiveTopicFilter(null)}
                    className="text-xs text-[var(--accent)] hover:underline"
                  >
                    Clear topic filter
                  </button>
                </div>
              )}
              {loading ? (
                <div className="text-center py-20 text-sm text-[var(--text-secondary)]">
                  Loading files from memory...
                </div>
              ) : displayFiles.length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {displayFiles.map((file) => {
                    const ext = file.extension?.toLowerCase() || "";
                    const isPdf = ext === "pdf";
                    const isDocx = ext === "docx";

                    return (
                      <div
                        key={file.file_id}
                        className="p-4 rounded-2xl bg-[var(--bg-surface)] border border-[var(--border-subtle)] shadow-card hover:shadow-card-hover hover:-translate-y-0.5 transition-all duration-200 flex items-center justify-between gap-4 group"
                      >
                        <div className="flex items-center gap-3.5 min-w-0">
                          {/* 3D Squircle Icon */}
                          <div
                            className={`w-12 h-12 rounded-2xl flex items-center justify-center shrink-0 p-3 shadow-sm ${
                              isPdf
                                ? "bg-gradient-to-br from-[#FFEDE5] to-[#FCD9C8] dark:from-[#3D251C] dark:to-[#2A1810] text-[#C96A45]"
                                : isDocx
                                ? "bg-gradient-to-br from-[#EBF3FF] to-[#D4E6FC] dark:from-[#1E293B] dark:to-[#0F172A] text-[#3B82F6]"
                                : "bg-gradient-to-br from-[#F5EEFB] to-[#E9D5F7] dark:from-[#2E1065] dark:to-[#1E0942] text-[#A855F7]"
                            }`}
                          >
                            {isPdf ? (
                              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                                <path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-9.5 8.5h-1v2H7V9h2.5c.83 0 1.5.67 1.5 1.5v1c0 .83-.67 1.5-1.5 1.5zm6 3h-2.5V9H15c.83 0 1.5.67 1.5 1.5v3c0 .83-.67 1.5-1.5 1.5zm-6-4.5h-1v1h1v-1zm4.5 1.5h-1v2h1v-2z" />
                              </svg>
                            ) : isDocx ? (
                              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                                <path d="M14 2H6c-1.1 0-1.99.9-1.99 2L4 20c0 1.1.89 2 1.99 2H18c1.1 0 2-.9 2-2V8l-6-6zm2 16H8v-2h8v2zm0-4H8v-2h8v2zm-3-5V3.5L18.5 9H13z" />
                              </svg>
                            ) : (
                              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                                <path d="M3 17.25V21h3.75L17.81 9.94l-3.75-3.75L3 17.25zM20.71 7.04c.39-.39.39-1.02 0-1.41l-2.34-2.34c-.39-.39-1.02-.39-1.41 0l-1.83 1.83 3.75 3.75 1.83-1.83z" />
                              </svg>
                            )}
                          </div>

                          {/* File Details */}
                          <div className="min-w-0">
                            <h4
                              className="font-medium text-[14px] text-[var(--text-primary)] truncate"
                              title={file.name}
                            >
                              {file.name}
                            </h4>
                            <p className="text-xs text-[var(--text-secondary)] mt-0.5">
                              {ext.toUpperCase()} · {formatSize(file.size_bytes)}
                            </p>
                            <p className="text-[11px] text-[var(--text-muted)]">
                              {getRelativeTime(file.modified)}
                            </p>
                          </div>
                        </div>

                        {/* Actions: Download + Delete */}
                        <div className="flex items-center gap-1.5 shrink-0">
                          <a
                            href={`${API_URL}/download/${file.file_id}`}
                            target="_blank"
                            rel="noreferrer"
                            className="w-8 h-8 rounded-full bg-[var(--bg-base)] border border-[var(--border-subtle)] text-[var(--text-secondary)] hover:text-[var(--accent)] hover:border-[var(--accent)]/50 flex items-center justify-center text-xs transition"
                            title={`Download ${file.name}`}
                          >
                            📥
                          </a>

                          <button
                            onClick={() => handleDeleteFile(file.file_id, file.name)}
                            disabled={deletingId === file.file_id}
                            type="button"
                            className="w-8 h-8 rounded-full bg-[var(--bg-base)] border border-[var(--border-subtle)] text-[var(--text-secondary)] hover:text-red-500 hover:border-red-500/50 flex items-center justify-center text-xs transition disabled:opacity-40"
                            title={`Delete ${file.name}`}
                          >
                            {deletingId === file.file_id ? "..." : "🗑️"}
                          </button>
                        </div>
                      </div>
                    );
                  })}
                </div>
              ) : (
                /* Empty State */
                <div className="text-center py-16 bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-3xl p-8 space-y-4">
                  <div className="w-14 h-14 rounded-2xl bg-[var(--accent)]/10 text-[var(--accent)] text-2xl flex items-center justify-center mx-auto">
                    📂
                  </div>
                  <div>
                    <h3 className="font-fraunces text-xl font-bold text-[var(--text-primary)]">
                      {activeTopicFilter
                        ? `No files in ${activeTopicFilter}`
                        : "No files in memory yet"}
                    </h3>
                    <p className="text-sm text-[var(--text-secondary)] mt-1 max-w-sm mx-auto">
                      {activeTopicFilter
                        ? "Try another topic card or clear the filter to see all documents."
                        : "Upload your PDF, DOCX, or TXT documents to begin semantic retrieval."}
                    </p>
                  </div>
                  {activeTopicFilter ? (
                    <button
                      onClick={() => setActiveTopicFilter(null)}
                      className="px-6 py-2.5 rounded-full font-semibold bg-[var(--text-primary)] text-[var(--bg-surface)] hover:opacity-90 transition text-sm shadow-sm"
                    >
                      Show All Files
                    </button>
                  ) : (
                    <div>
                      <button
                        onClick={() => setUploadModalOpen(true)}
                        className="px-6 py-2.5 rounded-full font-semibold bg-[var(--text-primary)] text-[var(--bg-surface)] hover:opacity-90 transition text-sm shadow-sm"
                      >
                        Upload First Document
                      </button>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </section>

        {/* UPLOAD MODAL */}
        {uploadModalOpen && (
          <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4 z-50 animate-in fade-in">
            <div className="w-full max-w-lg bg-[var(--bg-surface)] p-8 rounded-3xl border border-[var(--border-subtle)] shadow-floating space-y-6">
              <div className="flex items-center justify-between">
                <h3 className="font-fraunces text-2xl font-bold text-[var(--text-primary)]">
                  Upload Documents
                </h3>
                <button
                  onClick={() => setUploadModalOpen(false)}
                  className="w-8 h-8 rounded-full bg-[var(--bg-base)] flex items-center justify-center text-sm"
                >
                  ✕
                </button>
              </div>

              <div
                onClick={() => fileInputRef.current?.click()}
                className="p-8 border-2 border-dashed border-[var(--border-subtle)] hover:border-[var(--accent)] rounded-2xl text-center cursor-pointer transition bg-[var(--bg-base)]"
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  multiple
                  accept=".pdf,.docx,.txt"
                  onChange={handleFileUpload}
                  className="hidden"
                />
                <div className="text-3xl mb-2">📤</div>
                <p className="font-semibold text-sm text-[var(--text-primary)]">
                  Click to browse or drop PDF, DOCX, TXT files
                </p>
                <p className="text-xs text-[var(--text-secondary)] mt-1">
                  Original filenames are preserved and indexed
                </p>
              </div>

              {isUploading && (
                <div className="text-center text-xs text-[var(--accent)] font-semibold animate-pulse">
                  Uploading and extracting embeddings...
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
