"use client";

import { useEffect, useState } from "react";

interface StatsResponse {
  total_vectors: number;
  total_files: number;
  collection: string;
  vector_dim: number;
  status: string;
  topic_counts?: Record<string, number>;
}

interface UploadedFile {
  file_id: string;
  name: string;
  size_bytes: number;
  modified: number;
  extension: string;
}

interface FileResponse {
  uploaded_files: UploadedFile[];
}

export default function DashboardPage() {
  const [stats, setStats] = useState<StatsResponse | null>(null);
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [activeFilter, setActiveFilter] = useState<string>("All");
  const [loading, setLoading] = useState(true);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  const fetchStatsAndFiles = async () => {
    try {
      const [statsRes, filesRes] = await Promise.all([
        fetch(`${API_URL}/stats`).catch(() => null),
        fetch(`${API_URL}/files`).catch(() => null),
      ]);

      if (statsRes && statsRes.ok) {
        const statsData: StatsResponse = await statsRes.json();
        setStats(statsData);
      }

      if (filesRes && filesRes.ok) {
        const filesData: FileResponse = await filesRes.json();
        setFiles(filesData.uploaded_files || []);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load dashboard data");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatsAndFiles();
    const interval = setInterval(fetchStatsAndFiles, 10000);
    return () => clearInterval(interval);
  }, []);

  const handleDeleteFile = async (fileId: string, fileName: string) => {
    if (!confirm(`Are you sure you want to delete "${fileName}"?`)) return;
    setDeletingId(fileId);
    try {
      const res = await fetch(`${API_URL}/files/${fileId}`, { method: "DELETE" });
      if (res.ok) {
        setFiles((prev) => prev.filter((f) => f.file_id !== fileId));
        fetchStatsAndFiles();
      }
    } catch (err) {
      console.error(err);
    } finally {
      setDeletingId(null);
    }
  };

  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return "Good morning";
    if (hour < 18) return "Good afternoon";
    return "Good evening";
  };

  const formatSize = (bytes: number): string => {
    if (!bytes) return "0 B";
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const getRelativeTime = (timestamp: number): string => {
    if (!timestamp) return "Recently";
    const diff = Math.max(0, Date.now() - timestamp * 1000);
    const mins = Math.floor(diff / 60000);
    if (mins < 1) return "Just now";
    if (mins < 60) return `${mins}m ago`;
    const hours = Math.floor(mins / 60);
    if (hours < 24) return `${hours}h ago`;
    const days = Math.floor(hours / 24);
    return `${days}d ago`;
  };

  const getBadgeColor = (ext: string) => {
    switch (ext.toLowerCase()) {
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

  // Topic icon map — only cosmetic; counts come from the backend /stats
  // endpoint (topic_counts), which is sourced from real Qdrant topic_tags
  // metadata (PRD §7.7 Week-3), not client-side filename substring matching.
  const TOPIC_ICONS: Record<string, string> = {
    Kafka: "⚡",
    Microservices: "⚡",
    "Thesis & Research": "🎓",
    "Machine Learning": "🤖",
    "Information Retrieval": "🔎",
    "Business Reports": "📊",
    "Project Docs": "📁",
    "Cloud & DevOps": "☁️",
    "General Research": "📚",
  };

  // Build the topic cloud from the backend topic_counts if present; fall back
  // to an empty list when no files are indexed yet (states are still loading
  // or no uploads have been processed).
  const topicsWithCounts = stats?.topic_counts
    ? Object.entries(stats.topic_counts).map(([name, count]) => ({
        name,
        icon: TOPIC_ICONS[name] ?? "📎",
        count,
      }))
    : [];

  const filteredFiles = files.filter((f) => {
    if (activeFilter === "All") return true;
    return f.extension.toLowerCase() === activeFilter.toLowerCase();
  });

  return (
    <div className="min-h-screen bg-[var(--bg-base)] text-[var(--text-primary)] py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto space-y-12">
        {/* Greeting Hero Section */}
        <div
          className="w-full p-8 sm:p-12 rounded-[32px] text-white shadow-hero"
          style={{ background: "var(--bg-hero)" }}
        >
          <div className="max-w-2xl space-y-3">
            <h1 className="font-fraunces text-3xl sm:text-4xl md:text-5xl font-bold tracking-tight">
              {getGreeting()}, Researcher
            </h1>
            <p className="text-base sm:text-lg opacity-90 font-normal">
              You have <span className="font-semibold">{files.length} documents</span> stored across{" "}
              <span className="font-semibold">{stats?.total_vectors || 0} vector embeddings</span>.
            </p>
          </div>
        </div>

        {error && (
          <div className="p-4 rounded-xl bg-[var(--danger)]/10 border border-[var(--danger)]/30 text-[var(--danger)] text-sm">
            {error}
          </div>
        )}

        {/* Horizontally Scrollable Topic Cards Strip */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="font-fraunces text-2xl font-bold text-[var(--text-primary)]">
              Topics & Clusters
            </h2>
            <span className="text-xs text-[var(--text-secondary)]">
              ← Scroll horizontally →
            </span>
          </div>

          <div className="flex gap-4 overflow-x-auto pb-3 snap-x scrollbar-none">
            {topicsWithCounts.length === 0 ? (
              <div className="w-full text-sm text-[var(--text-secondary)] py-4">
                No topics yet — upload documents to populate the topic cloud.
              </div>
            ) : (topicsWithCounts.map((t) => (
              <div
                key={t.name}
                className="w-64 p-5 rounded-2xl bg-[var(--bg-surface)] border border-[var(--border-subtle)] snap-start shrink-0 flex flex-col justify-between space-y-3 shadow-card"
              >
                <div className="flex items-center justify-between">
                  <span className="text-2xl">{t.icon}</span>
                  <span className="text-xs px-2.5 py-0.5 rounded-full font-semibold bg-[var(--bg-base)] border border-[var(--border-subtle)] text-[var(--text-secondary)]">
                    {t.count} files
                  </span>
                </div>
                <div>
                  <h3 className="font-semibold text-base text-[var(--text-primary)] truncate">
                    {t.name}
                  </h3>
                  <p className="text-xs text-[var(--text-secondary)] mt-0.5">
                    Semantic cluster
                  </p>
                </div>
              </div>
              ))
            )}
          </div>
        </div>

        {/* My Files Section */}
        <div className="space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-[var(--border-subtle)]">
            <div className="flex items-center gap-3">
              <h2 className="font-fraunces text-2xl font-bold text-[var(--text-primary)]">
                Stored Documents
              </h2>
              <span className="text-xs px-2.5 py-1 rounded-full bg-[var(--bg-surface)] border border-[var(--border-subtle)] text-[var(--text-secondary)] font-semibold">
                {files.length} total
              </span>
            </div>

            {/* Filter Pills */}
            <div className="flex items-center gap-1.5 p-1 rounded-xl bg-[var(--bg-surface)] border border-[var(--border-subtle)] text-xs font-semibold">
              {["All", "PDF", "DOCX", "TXT"].map((pill) => (
                <button
                  key={pill}
                  type="button"
                  onClick={() => setActiveFilter(pill)}
                  className={`px-3.5 py-1.5 rounded-lg transition ${
                    activeFilter === pill
                      ? "bg-[var(--accent)] text-white shadow-sm"
                      : "text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
                  }`}
                >
                  {pill}
                </button>
              ))}
            </div>
          </div>

          {/* Files Grid */}
          {loading ? (
            <div className="text-center py-16 text-[var(--text-secondary)] text-sm">
              Loading files...
            </div>
          ) : filteredFiles.length > 0 ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
              {filteredFiles.map((file) => (
                <div
                  key={file.file_id}
                  className="p-5 rounded-2xl bg-[var(--bg-surface)] border border-[var(--border-subtle)] shadow-card hover:shadow-card-hover transition flex flex-col justify-between space-y-4"
                >
                  <div className="space-y-2">
                    <div className="flex items-center justify-between gap-2">
                      <span
                        className={`text-[10px] font-bold uppercase px-2 py-0.5 rounded ${getBadgeColor(
                          file.extension
                        )}`}
                      >
                        {file.extension}
                      </span>
                      <span className="text-xs text-[var(--text-secondary)]">
                        {getRelativeTime(file.modified)}
                      </span>
                    </div>

                    <h4
                      className="font-medium text-base text-[var(--text-primary)] truncate"
                      title={file.name}
                    >
                      {file.name}
                    </h4>
                  </div>

                  <div className="pt-3 border-t border-[var(--border-subtle)] flex items-center justify-between text-xs">
                    <span className="text-[var(--text-secondary)] font-medium">
                      {formatSize(file.size_bytes)}
                    </span>
                    <div className="flex items-center gap-2">
                      <a
                        href={`${API_URL}/download/${file.file_id}`}
                        target="_blank"
                        rel="noreferrer"
                        className="px-2.5 py-1 rounded-lg bg-[var(--bg-base)] border border-[var(--border-subtle)] text-[var(--text-primary)] hover:text-[var(--accent)] transition"
                      >
                        📥 Download
                      </a>
                      <button
                        onClick={() => handleDeleteFile(file.file_id, file.name)}
                        disabled={deletingId === file.file_id}
                        type="button"
                        className="px-2 py-1 rounded-lg bg-[var(--bg-base)] border border-[var(--border-subtle)] text-red-500 hover:bg-red-500/10 transition"
                        title="Delete file"
                      >
                        🗑️
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-16 p-8 rounded-2xl bg-[var(--bg-surface)] border border-[var(--border-subtle)] space-y-3">
              <p className="text-[var(--text-secondary)] text-sm">
                No documents found for the <strong className="font-semibold text-[var(--text-primary)]">{activeFilter}</strong> filter.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
