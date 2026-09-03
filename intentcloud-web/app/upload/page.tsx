"use client";

import { useState, useRef } from "react";
import { API_URL } from "@/lib/api";

interface UploadResponse {
  status: string;
  file_id: string;
  filename: string;
  size_bytes: number;
  message: string;
}

interface IngestingItem {
  id: string;
  filename: string;
  sizeBytes: number;
  extension: string;
  progress: number;
  stage: "uploading" | "extracting" | "indexing" | "ready" | "error";
  topicTag?: string;
  errorMessage?: string;
}

export default function UploadPage() {
  const [isDragging, setIsDragging] = useState(false);
  const [items, setItems] = useState<IngestingItem[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files) {
      processFiles(Array.from(e.dataTransfer.files));
    }
  };

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      processFiles(Array.from(e.target.files));
    }
  };

  const detectTopic = (name: string): string => {
    const lower = name.toLowerCase();
    if (lower.includes("kafka") || lower.includes("microservice") || lower.includes("stream")) {
      return "Kafka & Microservices";
    }
    if (lower.includes("thesis") || lower.includes("draft") || lower.includes("paper") || lower.includes("neural")) {
      return "Thesis Drafts";
    }
    if (lower.includes("report") || lower.includes("finance") || lower.includes("annual") || lower.includes("quarter")) {
      return "Business Reports";
    }
    if (lower.includes("doc") || lower.includes("api") || lower.includes("guide") || lower.includes("spec")) {
      return "Project Docs";
    }
    return "Cognitive Memory";
  };

  const formatSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const processFiles = async (fileList: File[]) => {
    for (const file of fileList) {
      const ext = file.name.split(".").pop()?.toLowerCase() || "";
      const itemId = Math.random().toString(36).substring(2, 9);

      if (!["pdf", "docx", "txt"].includes(ext)) {
        setItems((prev) => [
          {
            id: itemId,
            filename: file.name,
            sizeBytes: file.size,
            extension: ext,
            progress: 100,
            stage: "error",
            errorMessage: `Unsupported file format (.${ext}). Only PDF, DOCX, and TXT are accepted.`,
          },
          ...prev,
        ]);
        continue;
      }

      const newItem: IngestingItem = {
        id: itemId,
        filename: file.name,
        sizeBytes: file.size,
        extension: ext,
        progress: 20,
        stage: "uploading",
      };

      setItems((prev) => [newItem, ...prev]);

      try {
        const formData = new FormData();
        formData.append("file", file);

        const response = await fetch(`${API_URL}/upload`, {
          method: "POST",
          body: formData,
        });

        if (!response.ok) {
          throw new Error(`Upload failed with status ${response.status}`);
        }

        const data: UploadResponse = await response.json();

        // Simulate extraction stage
        setItems((prev) =>
          prev.map((item) =>
            item.id === itemId
              ? { ...item, progress: 60, stage: "extracting" }
              : item
          )
        );

        await new Promise((r) => setTimeout(r, 800));

        // Simulate embedding/indexing stage
        setItems((prev) =>
          prev.map((item) =>
            item.id === itemId
              ? { ...item, progress: 90, stage: "indexing" }
              : item
          )
        );

        await new Promise((r) => setTimeout(r, 700));

        // Ready stage with topic tag
        setItems((prev) =>
          prev.map((item) =>
            item.id === itemId
              ? {
                  ...item,
                  progress: 100,
                  stage: "ready",
                  topicTag: detectTopic(data.filename || file.name),
                }
              : item
          )
        );
      } catch (err) {
        setItems((prev) =>
          prev.map((item) =>
            item.id === itemId
              ? {
                  ...item,
                  stage: "error",
                  errorMessage: err instanceof Error ? err.message : "Failed to upload",
                }
              : item
          )
        );
      }
    }
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

  return (
    <div className="min-h-screen bg-[var(--bg-base)] text-[var(--text-primary)] py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-4xl mx-auto space-y-10">
        {/* Header */}
        <div className="text-center sm:text-left space-y-2">
          <h1 className="font-fraunces text-3xl sm:text-4xl font-bold tracking-tight">
            Upload Documents
          </h1>
          <p className="text-[var(--text-secondary)] text-base">
            Upload your files into IntentCloud. Text will be extracted, chunked, and embedded into local Qdrant vectors automatically.
          </p>
        </div>

        {/* Full-width Drop Zone */}
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          className={`w-full p-12 rounded-2xl border-2 border-dashed text-center cursor-pointer transition-all duration-200 ${
            isDragging
              ? "border-[var(--accent)] bg-[var(--accent)]/5 scale-[1.005]"
              : "border-[var(--border-subtle)] bg-[var(--bg-surface)] hover:border-[var(--accent)]/70"
          }`}
        >
          <input
            ref={fileInputRef}
            type="file"
            multiple
            accept=".pdf,.docx,.txt"
            onChange={handleFileInput}
            className="hidden"
          />

          <div className="flex flex-col items-center justify-center space-y-4">
            <div className="w-16 h-16 rounded-full bg-[var(--accent)]/10 text-[var(--accent)] flex items-center justify-center text-3xl">
              📂
            </div>

            <div className="space-y-1">
              <h3 className="font-fraunces text-xl font-bold text-[var(--text-primary)]">
                Drag and drop your files here
              </h3>
              <p className="text-sm text-[var(--text-secondary)]">
                or click anywhere in this zone to browse your device
              </p>
            </div>

            <div className="pt-2">
              <span className="inline-flex items-center px-4 py-2 rounded-lg text-sm font-semibold bg-[var(--accent)] text-white hover:bg-[var(--accent-hover)] transition">
                Browse Files
              </span>
            </div>

            <p className="text-xs text-[var(--text-secondary)] pt-2">
              Accepted file formats: <strong className="font-semibold">PDF, DOCX, TXT</strong> (up to 50MB)
            </p>
          </div>
        </div>

        {/* Ingested Items / Progress Feed */}
        {items.length > 0 && (
          <div className="p-6 rounded-2xl bg-[var(--bg-surface)] border border-[var(--border-subtle)] space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-[var(--border-subtle)]">
              <h3 className="font-fraunces text-lg font-bold text-[var(--text-primary)]">
                Ingestion Queue ({items.length})
              </h3>
              <button
                onClick={() => setItems([])}
                className="text-xs text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition"
              >
                Clear list
              </button>
            </div>

            <div className="space-y-3">
              {items.map((item) => (
                <div
                  key={item.id}
                  className="p-4 rounded-xl bg-[var(--bg-base)] border border-[var(--border-subtle)] flex flex-col sm:flex-row sm:items-center justify-between gap-4"
                >
                  <div className="space-y-1.5 flex-1 min-w-0">
                    <div className="flex items-center gap-2.5">
                      <span
                        className={`text-[10px] font-bold uppercase px-2 py-0.5 rounded ${getBadgeColor(
                          item.extension
                        )}`}
                      >
                        {item.extension}
                      </span>
                      <span className="font-medium text-sm text-[var(--text-primary)] truncate max-w-sm">
                        {item.filename}
                      </span>
                      <span className="text-xs text-[var(--text-secondary)] shrink-0">
                        ({formatSize(item.sizeBytes)})
                      </span>
                    </div>

                    {/* Progress indicator */}
                    <div className="flex items-center gap-3">
                      <div className="flex-1 h-1.5 rounded-full bg-[var(--border-subtle)] overflow-hidden">
                        <div
                          className={`h-full rounded-full transition-all duration-300 ${
                            item.stage === "error"
                              ? "bg-[var(--danger)]"
                              : item.stage === "ready"
                              ? "bg-[var(--success)]"
                              : "bg-[var(--accent)]"
                          }`}
                          style={{ width: `${item.progress}%` }}
                        />
                      </div>
                      <span className="text-xs text-[var(--text-secondary)] whitespace-nowrap min-w-[100px] text-right font-medium">
                        {item.stage === "uploading" && "Uploading..."}
                        {item.stage === "extracting" && "Extracting text..."}
                        {item.stage === "indexing" && "Embedding vectors..."}
                        {item.stage === "ready" && (
                          <span className="text-[var(--success)] font-semibold">
                            ✓ Ingested
                          </span>
                        )}
                        {item.stage === "error" && (
                          <span className="text-[var(--danger)] font-semibold">
                            Failed
                          </span>
                        )}
                      </span>
                    </div>

                    {item.errorMessage && (
                      <p className="text-xs text-[var(--danger)] font-medium">
                        {item.errorMessage}
                      </p>
                    )}
                  </div>

                  {/* Auto-detected topic badge */}
                  {item.stage === "ready" && item.topicTag && (
                    <div className="sm:text-right shrink-0">
                      <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-semibold bg-[var(--success)]/10 text-[var(--success)] border border-[var(--success)]/20">
                        🏷️ {item.topicTag}
                      </span>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
