"use client";

import React, { useEffect, useState } from "react";
import { 
  X, Download, ExternalLink, Copy, Check, Eye, 
  FileCode, ImageIcon, FileText, Code2, Sparkles, 
  ZoomIn, ZoomOut, RotateCcw 
} from "lucide-react";
import { API_URL } from "@/lib/api";
import { getFileCategory } from "@/lib/topics";
import VisualIntelligencePanel from "./VisualIntelligencePanel";

export interface PreviewableFile {
  file_id: string;
  name: string;
  size_bytes: number;
  extension: string;
  topic_tags?: string[];
  modified?: number;
}

interface FileContentResponse {
  file_id: string;
  filename: string;
  category: string;
  extension: string;
  is_binary: boolean;
  content: string;
  visual_metadata?: string;
  preview_url: string;
  size_bytes: number;
}

interface FilePreviewModalProps {
  file: PreviewableFile | null;
  onClose: () => void;
}

export default function FilePreviewModal({ file, onClose }: FilePreviewModalProps) {
  const [contentData, setContentData] = useState<FileContentResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [zoomLevel, setZoomLevel] = useState(1);
  const [showVisualDetails, setShowVisualDetails] = useState(true);

  useEffect(() => {
    if (!file) return;

    setLoading(true);
    setError(null);
    setZoomLevel(1);
    setContentData(null);

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handleKeyDown);

    fetch(`${API_URL}/files/${file.file_id}/content`)
      .then(async (res) => {
        if (!res.ok) throw new Error(`Could not load preview (${res.status})`);
        return res.json();
      })
      .then((data: FileContentResponse) => {
        setContentData(data);
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : "Failed to load preview");
      })
      .finally(() => {
        setLoading(false);
      });

    return () => {
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [file, onClose]);

  if (!file) return null;

  const category = getFileCategory(file.name, file.extension);
  const previewUrl = `${API_URL}/preview/${file.file_id}`;
  const downloadUrl = `${API_URL}/download/${file.file_id}`;

  const copyToClipboard = () => {
    if (!contentData?.content) return;
    navigator.clipboard.writeText(contentData.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const formatSize = (bytes: number): string => {
    if (!bytes) return "0 B";
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const getCategoryIcon = () => {
    if (category === "code") return <Code2 className="w-5 h-5 text-emerald-500" />;
    if (category === "photo") return <ImageIcon className="w-5 h-5 text-purple-500" />;
    if (category === "pdf") return <FileText className="w-5 h-5 text-[#C96A45]" />;
    return <FileText className="w-5 h-5 text-[var(--accent)]" />;
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-6 bg-black/75 backdrop-blur-md animate-in fade-in duration-200">
      {/* Click-away backdrop */}
      <div className="fixed inset-0" onClick={onClose} />

      {/* Modal Container */}
      <div className="relative w-full max-w-6xl xl:max-w-7xl h-[90vh] max-h-[920px] rounded-2xl sm:rounded-3xl bg-[var(--bg-surface)] border border-[var(--border-subtle)] shadow-2xl flex flex-col overflow-hidden z-10">
        
        {/* Header Bar */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-[var(--border-subtle)] bg-[var(--bg-surface)]/90 backdrop-blur shrink-0">
          <div className="flex items-center gap-3 min-w-0 pr-4">
            <div className="w-10 h-10 rounded-xl bg-[var(--bg-base)] border border-[var(--border-subtle)] flex items-center justify-center shrink-0 shadow-inner">
              {getCategoryIcon()}
            </div>
            <div className="min-w-0">
              <h2 className="text-base sm:text-lg font-bold text-[var(--text-primary)] font-fraunces truncate max-w-md sm:max-w-lg" title={file.name}>
                {file.name}
              </h2>
              <div className="flex items-center gap-2 text-xs text-[var(--text-secondary)] mt-0.5">
                <span className="font-semibold uppercase tracking-wider px-1.5 py-0.5 rounded bg-[var(--bg-base)] border border-[var(--border-subtle)]">
                  {file.extension}
                </span>
                <span>•</span>
                <span>{formatSize(contentData?.size_bytes || file.size_bytes)}</span>
                {category === "photo" && (
                  <>
                    <span>•</span>
                    <span className="text-purple-400 font-medium flex items-center gap-1">
                      <Sparkles className="w-3 h-3" /> Visual AI Indexed
                    </span>
                  </>
                )}
              </div>
            </div>
          </div>

          {/* Action buttons */}
          <div className="flex items-center gap-2 shrink-0">
            {contentData?.content && !contentData.is_binary && (
              <button
                onClick={copyToClipboard}
                type="button"
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-[var(--bg-base)] border border-[var(--border-subtle)] text-[var(--text-primary)] hover:border-[var(--accent)] transition shadow-sm"
                title="Copy contents"
              >
                {copied ? <Check className="w-3.5 h-3.5 text-emerald-500" /> : <Copy className="w-3.5 h-3.5" />}
                <span className="hidden sm:inline">{copied ? "Copied!" : "Copy"}</span>
              </button>
            )}

            <a
              href={previewUrl}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-[var(--bg-base)] border border-[var(--border-subtle)] text-[var(--text-primary)] hover:border-[var(--accent)] transition shadow-sm"
              title="Open raw file in new tab"
            >
              <ExternalLink className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Open tab</span>
            </a>

            <a
              href={downloadUrl}
              download={file.name}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-[var(--accent)] text-white hover:bg-[var(--accent-hover)] transition shadow-sm"
              title="Download file"
            >
              <Download className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Download</span>
            </a>

            <button
              onClick={onClose}
              type="button"
              className="p-1.5 rounded-lg text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-base)] transition ml-1"
              title="Close preview (Esc)"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Content Viewer Body */}
        <div className="flex-1 overflow-hidden relative bg-[var(--bg-base)] flex flex-col">
          {loading ? (
            <div className="h-full flex flex-col items-center justify-center space-y-3 text-[var(--text-secondary)]">
              <div className="w-8 h-8 rounded-full border-2 border-[var(--accent)] border-t-transparent animate-spin" />
              <p className="text-sm font-medium">Loading document preview...</p>
            </div>
          ) : error ? (
            <div className="h-full flex flex-col items-center justify-center p-6 text-center space-y-4">
              <div className="w-12 h-12 rounded-full bg-red-500/10 text-red-500 flex items-center justify-center">
                <X className="w-6 h-6" />
              </div>
              <div>
                <h3 className="font-fraunces text-lg font-bold text-[var(--text-primary)]">Preview Unavailable</h3>
                <p className="text-sm text-[var(--text-secondary)] mt-1 max-w-sm">{error}</p>
              </div>
              <a
                href={downloadUrl}
                download={file.name}
                className="px-4 py-2 rounded-xl text-xs font-semibold bg-[var(--accent)] text-white hover:bg-[var(--accent-hover)] transition"
              >
                Download File Instead
              </a>
            </div>
          ) : category === "photo" ? (
            /* IMAGE PREVIEWER WITH ZOOM & VISUAL AI DRAWER */
            <div className="relative h-full flex flex-col sm:flex-row overflow-hidden">
              <div className="flex-1 relative flex items-center justify-center overflow-auto p-4 bg-[#090d16]/90 pattern-dots">
                {/* Image display */}
                <div 
                  className="transition-transform duration-150 ease-out origin-center flex items-center justify-center max-w-full max-h-full"
                  style={{ transform: `scale(${zoomLevel})` }}
                >
                  <img
                    src={previewUrl}
                    alt={file.name}
                    className="max-h-[65vh] max-w-full rounded-lg shadow-2xl object-contain border border-white/10"
                  />
                </div>

                {/* Floating zoom controls */}
                <div className="absolute bottom-4 left-4 flex items-center gap-1.5 p-1.5 rounded-xl bg-black/60 backdrop-blur-md border border-white/15 text-white shadow-lg text-xs z-10">
                  <button
                    onClick={() => setZoomLevel((z) => Math.max(0.5, z - 0.25))}
                    type="button"
                    className="p-1 rounded-md hover:bg-white/15 transition"
                    title="Zoom Out"
                  >
                    <ZoomOut className="w-4 h-4" />
                  </button>
                  <span className="px-2 font-mono text-[11px] min-w-[40px] text-center font-semibold">
                    {Math.round(zoomLevel * 100)}%
                  </span>
                  <button
                    onClick={() => setZoomLevel((z) => Math.min(3, z + 0.25))}
                    type="button"
                    className="p-1 rounded-md hover:bg-white/15 transition"
                    title="Zoom In"
                  >
                    <ZoomIn className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => setZoomLevel(1)}
                    type="button"
                    className="p-1 rounded-md hover:bg-white/15 transition ml-0.5"
                    title="Reset Zoom"
                  >
                    <RotateCcw className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>

              {/* Side Drawer: Visual AI Insights (OCR & VLM) */}
              {contentData?.visual_metadata && (
                <div className={`w-full sm:w-96 md:w-[420px] lg:w-[460px] xl:w-[480px] border-t sm:border-t-0 sm:border-l border-[var(--border-subtle)] bg-[var(--bg-surface)] flex flex-col shrink-0 overflow-hidden ${showVisualDetails ? 'h-64 sm:h-full' : 'h-11 sm:h-full'}`}>
                  <VisualIntelligencePanel
                    rawMetadata={contentData.visual_metadata}
                    filename={file.name}
                  />
                </div>
              )}
            </div>
          ) : category === "pdf" ? (
            /* PDF EMBEDDED VIEWER */
            <div className="w-full h-full relative">
              <iframe
                src={`${previewUrl}#toolbar=1&navpanes=1`}
                title={file.name}
                className="w-full h-full border-0"
              />
            </div>
          ) : (
            /* CODE OR TEXT DOCUMENT VIEWER */
            <div className="h-full flex flex-col overflow-hidden">
              {/* Toolbar */}
              <div className="flex items-center justify-between px-5 py-2 border-b border-[var(--border-subtle)] bg-[var(--bg-surface)]/60 text-xs text-[var(--text-secondary)] shrink-0">
                <div className="flex items-center gap-2">
                  <span className="font-semibold text-[var(--text-primary)]">
                    {category === "code" ? "Source Code Viewer" : "Text Document Viewer"}
                  </span>
                  <span>•</span>
                  <span>{contentData?.content.split("\n").length ?? 0} lines</span>
                </div>
                <span className="font-mono text-[11px]">UTF-8</span>
              </div>

              {/* Code lines container */}
              <div className="flex-1 overflow-auto p-4 font-mono text-xs leading-6 select-text bg-[#0d1117] text-[#c9d1d9] scrollbar-thin">
                <table className="w-full border-collapse">
                  <tbody>
                    {(contentData?.content || "No content").split("\n").map((line, idx) => (
                      <tr key={idx} className="hover:bg-white/[0.04]">
                        <td className="w-10 pr-4 text-right select-none text-neutral-500 text-[11px] align-top">
                          {idx + 1}
                        </td>
                        <td className="whitespace-pre break-all font-mono">
                          {line || " "}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
