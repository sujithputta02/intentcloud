"use client";

import React, { useState } from "react";
import {
  ChevronLeft,
  Share2,
  Eye,
  Tag,
  Search,
  Folder,
  Cloud,
  Layers,
  Monitor,
  FileText,
  Download,
  Play,
  Pause,
  Code,
  Sparkles,
  ExternalLink,
  X,
} from "lucide-react";
import { PreviewableFile } from "./FilePreviewModal";

export interface FileItem {
  file_id: string;
  name: string;
  size_bytes: number;
  modified: number;
  extension: string;
  file_type_category?: string;
  topic_tags?: string[];
  folder_id?: string | null;
  folder_path?: string;
}

interface MacFinderProps {
  files: FileItem[];
  onRefresh: () => void;
  onPreview: (file: PreviewableFile) => void;
  onShowToast: (msg: string) => void;
}

type SidebarCategory =
  | "all"
  | "icloud"
  | "applications"
  | "desktop"
  | "documents"
  | "downloads";

export default function MacFinder({
  files,
  onRefresh,
  onPreview,
  onShowToast,
}: MacFinderProps) {
  const [activeCategory, setActiveCategory] = useState<SidebarCategory>("documents");
  const [searchOpen, setSearchOpen] = useState<boolean>(false);
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [isPlayingAudio, setIsPlayingAudio] = useState<boolean>(true);
  const [activeViewTab, setActiveViewTab] = useState<"showcase" | "userfiles">("showcase");

  // Filter user files if viewing user files
  const filteredUserFiles = files.filter((f) =>
    f.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const handleShowcaseClick = (title: string, type: string) => {
    onShowToast(`Opened ${title} in Quick Look`);
    onPreview({
      file_id: `showcase-${title.toLowerCase().replace(/\s+/g, "-")}`,
      name: `${title}.${type}`,
      size_bytes: 2048500,
      modified: Date.now() / 1000,
      extension: type,
      topic_tags: ["Showcase", type.toUpperCase()],
    });
  };

  return (
    <div className="relative w-full rounded-[36px] p-2 sm:p-6 lg:p-8 bg-gradient-to-tr from-[#2d124d] via-[#a83279] to-[#f97316] shadow-2xl overflow-hidden font-sans">
      {/* Background Ambient Glows */}
      <div className="absolute -top-24 -left-24 w-96 h-96 bg-purple-500/40 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute -bottom-24 -right-24 w-96 h-96 bg-amber-500/30 rounded-full blur-3xl pointer-events-none" />

      {/* Main macOS Finder Window Container */}
      <div className="relative w-full max-w-5xl mx-auto rounded-[28px] sm:rounded-[32px] bg-[#f4f5f8]/95 dark:bg-[#18191e]/95 backdrop-blur-3xl shadow-[0_25px_70px_rgba(0,0,0,0.35)] border border-white/70 dark:border-white/10 overflow-hidden flex flex-col min-h-[580px]">
        
        {/* TOP TOOLBAR */}
        <div className="h-14 px-5 border-b border-black/[0.05] dark:border-white/[0.06] flex items-center justify-between select-none">
          {/* Traffic Lights & Back Arrow */}
          <div className="flex items-center space-x-6">
            <div className="flex items-center space-x-2">
              <button
                type="button"
                onClick={() => onShowToast("Closed window")}
                className="w-3 h-3 rounded-full bg-[#ff5f56] border border-[#e0443e]/40 shadow-xs hover:opacity-80 transition cursor-pointer"
                aria-label="Close"
              />
              <button
                type="button"
                onClick={() => onShowToast("Minimized window")}
                className="w-3 h-3 rounded-full bg-[#ffbd2e] border border-[#dea123]/40 shadow-xs hover:opacity-80 transition cursor-pointer"
                aria-label="Minimize"
              />
              <button
                type="button"
                onClick={() => onShowToast("Maximized Finder")}
                className="w-3 h-3 rounded-full bg-[#27c93f] border border-[#1aab29]/40 shadow-xs hover:opacity-80 transition cursor-pointer"
                aria-label="Zoom"
              />
            </div>

            {/* Navigation Chevron */}
            <button
              type="button"
              onClick={() => onShowToast("Navigated back")}
              className="text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 transition p-1"
              aria-label="Back"
            >
              <ChevronLeft className="w-5 h-5 stroke-[1.75]" />
            </button>
          </div>

          {/* Center Title or Search Field */}
          {searchOpen ? (
            <div className="flex-1 max-w-xs mx-4 relative">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search Documents..."
                autoFocus
                className="w-full bg-white/70 dark:bg-black/30 border border-gray-300 dark:border-gray-700 rounded-full px-3 py-1 text-xs text-gray-800 dark:text-gray-200 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500/40"
              />
              {searchQuery && (
                <button
                  type="button"
                  onClick={() => setSearchQuery("")}
                  className="absolute right-2.5 top-1.5 text-gray-400 hover:text-gray-600"
                >
                  <X className="w-3.5 h-3.5" />
                </button>
              )}
            </div>
          ) : (
            <div className="flex items-center space-x-2 bg-black/[0.04] dark:bg-white/[0.06] p-0.5 rounded-lg text-[11px] font-medium text-gray-600 dark:text-gray-300">
              <button
                type="button"
                onClick={() => setActiveViewTab("showcase")}
                className={`px-2.5 py-1 rounded-md transition ${
                  activeViewTab === "showcase"
                    ? "bg-white dark:bg-black/40 text-gray-900 dark:text-white shadow-xs font-semibold"
                    : "hover:text-gray-900"
                }`}
              >
                Exact Design Preview
              </button>
              <button
                type="button"
                onClick={() => setActiveViewTab("userfiles")}
                className={`px-2.5 py-1 rounded-md transition ${
                  activeViewTab === "userfiles"
                    ? "bg-white dark:bg-black/40 text-gray-900 dark:text-white shadow-xs font-semibold"
                    : "hover:text-gray-900"
                }`}
              >
                My Uploaded Files ({files.length})
              </button>
            </div>
          )}

          {/* Action Toolbar Icons (Share, Quick Look, Tag, Search) */}
          <div className="flex items-center space-x-3 text-gray-400 dark:text-gray-400">
            <button
              type="button"
              onClick={() => onShowToast("Shared document link")}
              className="p-1 hover:text-gray-700 dark:hover:text-gray-200 transition"
              title="Share"
            >
              <Share2 className="w-4 h-4 stroke-[1.75]" />
            </button>
            <button
              type="button"
              onClick={() => {
                if (files.length > 0) {
                  onPreview(files[0] as unknown as PreviewableFile);
                } else {
                  handleShowcaseClick("aerial-01", "mp4");
                }
              }}
              className="p-1 hover:text-gray-700 dark:hover:text-gray-200 transition"
              title="Quick Look"
            >
              <Eye className="w-4 h-4 stroke-[1.75]" />
            </button>
            <button
              type="button"
              onClick={() => onShowToast("Filter by tags")}
              className="p-1 hover:text-gray-700 dark:hover:text-gray-200 transition"
              title="Tags"
            >
              <Tag className="w-4 h-4 stroke-[1.75]" />
            </button>
            <button
              type="button"
              onClick={() => setSearchOpen(!searchOpen)}
              className={`p-1 transition ${
                searchOpen
                  ? "text-blue-600 dark:text-blue-400"
                  : "hover:text-gray-700 dark:hover:text-gray-200"
              }`}
              title="Search"
            >
              <Search className="w-4 h-4 stroke-[1.75]" />
            </button>
          </div>
        </div>

        {/* BODY (SIDEBAR + MAIN CANVAS) */}
        <div className="flex-1 flex flex-col md:flex-row overflow-hidden">
          
          {/* LEFT SIDEBAR */}
          <aside className="w-full md:w-56 shrink-0 border-b md:border-b-0 md:border-r border-black/[0.04] dark:border-white/[0.06] p-4 flex flex-col justify-between select-none bg-black/[0.015] dark:bg-white/[0.015]">
            <nav className="space-y-1 text-xs">
              <button
                type="button"
                onClick={() => {
                  setActiveCategory("all");
                  setActiveViewTab("userfiles");
                }}
                className={`w-full flex items-center space-x-3 px-3 py-2 rounded-xl transition ${
                  activeCategory === "all"
                    ? "bg-black/[0.08] dark:bg-white/[0.12] text-gray-900 dark:text-white font-medium"
                    : "text-gray-600 dark:text-gray-400 hover:bg-black/[0.03] dark:hover:bg-white/[0.05]"
                }`}
              >
                <Folder className="w-4 h-4 text-gray-500 fill-gray-500/20" />
                <span>All My Files</span>
              </button>

              <button
                type="button"
                onClick={() => {
                  setActiveCategory("icloud");
                  onShowToast("iCloud Drive Synced");
                }}
                className={`w-full flex items-center space-x-3 px-3 py-2 rounded-xl transition ${
                  activeCategory === "icloud"
                    ? "bg-black/[0.08] dark:bg-white/[0.12] text-gray-900 dark:text-white font-medium"
                    : "text-gray-600 dark:text-gray-400 hover:bg-black/[0.03] dark:hover:bg-white/[0.05]"
                }`}
              >
                <Cloud className="w-4 h-4 text-gray-500" />
                <span>iCloud Drive</span>
              </button>

              <button
                type="button"
                onClick={() => {
                  setActiveCategory("applications");
                  onShowToast("Applications Directory");
                }}
                className={`w-full flex items-center space-x-3 px-3 py-2 rounded-xl transition ${
                  activeCategory === "applications"
                    ? "bg-black/[0.08] dark:bg-white/[0.12] text-gray-900 dark:text-white font-medium"
                    : "text-gray-600 dark:text-gray-400 hover:bg-black/[0.03] dark:hover:bg-white/[0.05]"
                }`}
              >
                <div className="w-4 h-4 rounded-full border border-gray-500 flex items-center justify-center text-[9px] font-bold">
                  A
                </div>
                <span>Applications</span>
              </button>

              <button
                type="button"
                onClick={() => {
                  setActiveCategory("desktop");
                  onShowToast("Desktop Workspace");
                }}
                className={`w-full flex items-center space-x-3 px-3 py-2 rounded-xl transition ${
                  activeCategory === "desktop"
                    ? "bg-black/[0.08] dark:bg-white/[0.12] text-gray-900 dark:text-white font-medium"
                    : "text-gray-600 dark:text-gray-400 hover:bg-black/[0.03] dark:hover:bg-white/[0.05]"
                }`}
              >
                <Monitor className="w-4 h-4 text-gray-500" />
                <span>Desktop</span>
              </button>

              {/* DOCUMENTS (EXACT ACTIVE STATE FROM SCREENSHOT) */}
              <button
                type="button"
                onClick={() => {
                  setActiveCategory("documents");
                  setActiveViewTab("showcase");
                }}
                className={`w-full flex items-center space-x-3 px-3 py-2 rounded-xl transition ${
                  activeCategory === "documents"
                    ? "bg-black/[0.08] dark:bg-white/[0.12] text-gray-900 dark:text-white font-semibold shadow-xs"
                    : "text-gray-600 dark:text-gray-400 hover:bg-black/[0.03] dark:hover:bg-white/[0.05]"
                }`}
              >
                <FileText className="w-4 h-4 text-gray-700 dark:text-gray-300" />
                <span>Documents</span>
              </button>

              <button
                type="button"
                onClick={() => {
                  setActiveCategory("downloads");
                  onShowToast("Downloads Directory");
                }}
                className={`w-full flex items-center space-x-3 px-3 py-2 rounded-xl transition ${
                  activeCategory === "downloads"
                    ? "bg-black/[0.08] dark:bg-white/[0.12] text-gray-900 dark:text-white font-medium"
                    : "text-gray-600 dark:text-gray-400 hover:bg-black/[0.03] dark:hover:bg-white/[0.05]"
                }`}
              >
                <Download className="w-4 h-4 text-gray-500" />
                <span>Downloads</span>
              </button>
            </nav>

            <div className="pt-4 border-t border-black/[0.04] dark:border-white/[0.06] text-[11px] text-gray-400 dark:text-gray-500 hidden md:block">
              IntentCloud Edge Node
            </div>
          </aside>

          {/* MAIN CONTENT AREA */}
          <main className="flex-1 p-6 sm:p-8 flex flex-col justify-between overflow-y-auto max-h-[620px]">
            <div>
              {/* LARGE BOLD HEADER */}
              <h1 className="text-3xl sm:text-4xl font-extrabold text-[#1d1d1f] dark:text-white tracking-tight mb-7 capitalize">
                {activeCategory}
              </h1>

              {/* VIEW MODE 1: EXACT SCREENSHOT REPLICA SHOWCASE */}
              {activeViewTab === "showcase" ? (
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 items-start">
                  
                  {/* TILE 1: AERIAL-01 (OCEAN VIDEO CARD) */}
                  <div
                    onClick={() => handleShowcaseClick("aerial-01", "mp4")}
                    className="group relative h-48 rounded-2xl overflow-hidden shadow-[0_16px_36px_rgba(0,119,182,0.3)] cursor-pointer transition-all duration-300 hover:scale-[1.03] hover:shadow-[0_20px_44px_rgba(0,119,182,0.4)] bg-gradient-to-br from-[#0077b6] via-[#0096c7] to-[#48cae4]"
                  >
                    {/* Ocean Wave Surface Overlay */}
                    <div className="absolute inset-0 bg-[radial-gradient(circle_at_30%_30%,rgba(255,255,255,0.35),transparent_60%)]" />
                    <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,rgba(2,62,138,0.5),transparent_70%)]" />

                    {/* Top-left Play Icon */}
                    <div className="absolute top-3.5 left-3.5 w-7 h-7 rounded-full bg-white/30 backdrop-blur-md flex items-center justify-center shadow-xs">
                      <Play className="w-3.5 h-3.5 text-white fill-white ml-0.5" />
                    </div>

                    {/* Bottom-left Title */}
                    <div className="absolute bottom-3.5 left-3.5">
                      <span className="text-white font-bold text-base tracking-wide drop-shadow-[0_2px_4px_rgba(0,0,0,0.4)]">
                        aerial-01
                      </span>
                    </div>
                  </div>

                  {/* TILE 2: CODE INDEX & CANYON COLUMN */}
                  <div className="flex flex-col space-y-5">
                    {/* Index Code Snippet Card */}
                    <div
                      onClick={() => handleShowcaseClick("index", "html")}
                      className="group cursor-pointer transition-all duration-300 hover:scale-[1.03]"
                    >
                      <div className="h-20 rounded-2xl bg-[#1e1e24] p-3 shadow-[0_12px_28px_rgba(0,0,0,0.25)] flex flex-col justify-center space-y-1">
                        <div className="flex items-center space-x-1.5 text-xs">
                          <span className="text-cyan-400 font-mono font-semibold">&lt;&gt;</span>
                          <span className="text-amber-400 font-mono font-medium">&lt;html&gt;</span>
                        </div>
                        <div className="text-[11px] font-mono text-purple-400 pl-4 truncate">
                          &lt;meta charset=&quot;utf-8&quot;&gt;
                        </div>
                      </div>
                      <p className="text-xs text-center text-gray-700 dark:text-gray-300 font-medium mt-1.5">
                        index
                      </p>
                    </div>

                    {/* Canyon Photo Card */}
                    <div
                      onClick={() => handleShowcaseClick("canyon", "jpg")}
                      className="group cursor-pointer transition-all duration-300 hover:scale-[1.03]"
                    >
                      <div className="h-28 rounded-2xl overflow-hidden shadow-[0_12px_28px_rgba(202,103,2,0.25)] bg-gradient-to-br from-[#c2410c] via-[#ea580c] to-[#7c2d12] relative">
                        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_bottom_left,rgba(251,191,36,0.5),transparent_70%)]" />
                        <div className="absolute inset-0 bg-[linear-gradient(45deg,transparent_40%,rgba(0,0,0,0.3)_100%)]" />
                      </div>
                      <p className="text-xs text-center text-gray-700 dark:text-gray-300 font-medium mt-1.5">
                        canyon
                      </p>
                    </div>
                  </div>

                  {/* TILE 3: SOUNDTRACK & JELLYFISH COLUMN */}
                  <div className="flex flex-col space-y-5">
                    {/* Final Soundtrack Waveform Card */}
                    <div
                      onClick={() => {
                        setIsPlayingAudio(!isPlayingAudio);
                        onShowToast(isPlayingAudio ? "Soundtrack paused" : "Soundtrack playing");
                      }}
                      className="group cursor-pointer transition-all duration-300 hover:scale-[1.02]"
                    >
                      <div className="h-20 rounded-2xl bg-gradient-to-r from-[#d9cbe8] via-[#e2d4f0] to-[#ece1f7] dark:from-[#352c42] dark:to-[#4a3b5c] p-3.5 shadow-[0_12px_28px_rgba(147,112,219,0.2)] flex items-center space-x-3">
                        {/* Pause / Play Icon */}
                        <div className="w-8 h-8 rounded-xl bg-white/60 dark:bg-white/20 backdrop-blur-md flex items-center justify-center text-purple-900 dark:text-purple-200 shrink-0 shadow-xs">
                          {isPlayingAudio ? (
                            <Pause className="w-4 h-4 fill-purple-900 dark:fill-purple-200" />
                          ) : (
                            <Play className="w-4 h-4 fill-purple-900 dark:fill-purple-200 ml-0.5" />
                          )}
                        </div>

                        {/* Waveform Bars */}
                        <div className="flex-1 flex items-center justify-between h-8 space-x-0.5">
                          {[
                            4, 8, 14, 20, 26, 18, 12, 22, 28, 16, 24, 30, 22, 14, 19, 25, 20,
                            12, 15, 22, 26, 18, 10, 16, 24, 18, 12, 8, 5,
                          ].map((height, i) => (
                            <div
                              key={i}
                              className={`w-1 rounded-full transition-all duration-300 ${
                                i < 18
                                  ? "bg-purple-700/80 dark:bg-purple-400"
                                  : "bg-white/80 dark:bg-white/40"
                              }`}
                              style={{ height: `${height}px` }}
                            />
                          ))}
                        </div>
                      </div>
                      <p className="text-xs text-center text-gray-700 dark:text-gray-300 font-medium mt-1.5">
                        final soundtrack
                      </p>
                    </div>

                    {/* Jellyfish Photoshop Card */}
                    <div
                      onClick={() => handleShowcaseClick("jellyfish", "psd")}
                      className="group cursor-pointer transition-all duration-300 hover:scale-[1.03]"
                    >
                      <div className="h-28 rounded-2xl overflow-hidden shadow-[0_12px_28px_rgba(15,23,42,0.3)] bg-gradient-to-b from-[#020617] via-[#0f172a] to-[#1e1b4b] relative p-3 flex flex-col justify-between">
                        {/* Photoshop Badge */}
                        <div className="self-start px-1.5 py-0.5 rounded-md bg-[#001e36] border border-[#31a8ff]/40 text-[#31a8ff] font-bold text-[10px] tracking-tight shadow-xs">
                          Ps
                        </div>
                        {/* Bioluminescent Jellyfish Light Effect */}
                        <div className="absolute right-4 top-4 w-14 h-14 rounded-full bg-cyan-400/20 blur-lg" />
                        <div className="absolute right-6 bottom-4 w-8 h-8 rounded-full bg-blue-500/30 blur-md" />
                      </div>
                      <p className="text-xs text-center text-gray-700 dark:text-gray-300 font-medium mt-1.5">
                        jellyfish
                      </p>
                    </div>
                  </div>

                  {/* TILE 4: PROJECT FILES (STACKED ALBUM CARD) */}
                  <div
                    onClick={() => handleShowcaseClick("project-files", "zip")}
                    className="group relative h-48 rounded-2xl bg-gradient-to-b from-[#f1f3f6] to-[#d8dde6] dark:from-[#2a2c35] dark:to-[#1c1e24] p-3 shadow-[0_16px_36px_rgba(0,0,0,0.18)] cursor-pointer transition-all duration-300 hover:scale-[1.03] flex flex-col justify-between"
                  >
                    {/* Stacked Thumbnails */}
                    <div className="grid grid-cols-2 gap-2 h-28">
                      <div className="rounded-xl overflow-hidden bg-gradient-to-br from-indigo-900 to-purple-800 relative shadow-inner">
                        <div className="absolute inset-0 bg-[radial-gradient(circle_at_bottom,rgba(244,114,182,0.4),transparent)]" />
                      </div>
                      <div className="rounded-xl overflow-hidden bg-gradient-to-br from-slate-900 to-sky-950 relative shadow-inner">
                        <div className="absolute inset-0 bg-[linear-gradient(45deg,rgba(239,68,68,0.4),transparent)]" />
                      </div>
                    </div>

                    {/* Bottom Label on the Card */}
                    <div className="px-1">
                      <span className="text-gray-900 dark:text-white font-bold text-sm tracking-tight drop-shadow-xs">
                        project files
                      </span>
                    </div>
                  </div>

                  {/* TILE 5: PROJECT (SKETCH / MOBILE DESIGN CARD) */}
                  <div
                    onClick={() => handleShowcaseClick("project", "sketch")}
                    className="group cursor-pointer transition-all duration-300 hover:scale-[1.03]"
                  >
                    <div className="h-40 rounded-2xl overflow-hidden shadow-[0_14px_32px_rgba(19,78,74,0.25)] bg-gradient-to-br from-[#134e4a] via-[#115e59] to-[#042f2e] p-3 relative flex items-center justify-center">
                      {/* Diamond / Sketch Badge in Top Left */}
                      <div className="absolute top-3 left-3 text-cyan-300 text-xs">
                        💎
                      </div>

                      {/* Mini Smartphone Wireframe */}
                      <div className="w-20 h-28 rounded-xl bg-black/40 backdrop-blur-md border border-white/20 p-1.5 flex flex-col justify-between shadow-lg">
                        <div className="w-6 h-1 bg-white/30 rounded-full mx-auto" />
                        <div className="flex justify-center -space-x-1">
                          <div className="w-3.5 h-3.5 rounded-full bg-amber-400" />
                          <div className="w-3.5 h-3.5 rounded-full bg-rose-400" />
                          <div className="w-3.5 h-3.5 rounded-full bg-sky-400" />
                        </div>
                        <div className="w-full h-7 rounded-lg bg-teal-500/40" />
                      </div>
                    </div>
                    <p className="text-xs text-center text-gray-700 dark:text-gray-300 font-medium mt-1.5">
                      project
                    </p>
                  </div>
                </div>
              ) : (
                /* VIEW MODE 2: USER'S REAL UPLOADED CLOUD FILES */
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
                  {filteredUserFiles.length === 0 ? (
                    <div className="col-span-full py-16 text-center text-gray-400 dark:text-gray-500">
                      <Folder className="w-10 h-10 mx-auto mb-2 opacity-40" />
                      <p className="text-sm">No uploaded documents found matching query.</p>
                    </div>
                  ) : (
                    filteredUserFiles.map((file) => (
                      <div
                        key={file.file_id}
                        onClick={() => onPreview(file as unknown as PreviewableFile)}
                        className="group relative rounded-2xl p-4 bg-white/70 dark:bg-black/30 border border-black/[0.06] dark:border-white/[0.08] hover:border-blue-500/50 shadow-sm hover:shadow-md cursor-pointer transition-all duration-200 flex flex-col justify-between h-36"
                      >
                        <div className="flex items-start justify-between">
                          <div className="w-10 h-10 rounded-xl bg-blue-500/10 text-blue-600 dark:text-blue-400 flex items-center justify-center font-bold text-xs uppercase">
                            {file.extension || "doc"}
                          </div>
                          <button
                            type="button"
                            onClick={(e) => {
                              e.stopPropagation();
                              onPreview(file as unknown as PreviewableFile);
                            }}
                            className="text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 p-1"
                          >
                            <ExternalLink className="w-4 h-4" />
                          </button>
                        </div>
                        <div>
                          <p className="text-xs font-semibold text-gray-900 dark:text-white truncate">
                            {file.name}
                          </p>
                          <p className="text-[11px] text-gray-500 dark:text-gray-400 mt-0.5">
                            {(file.size_bytes / 1024).toFixed(1)} KB • {file.file_type_category || "Document"}
                          </p>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              )}
            </div>

            {/* BOTTOM STATUS & BREADCRUMB BAR */}
            <div className="pt-6 mt-8 border-t border-black/[0.04] dark:border-white/[0.06] flex items-center justify-between">
              {/* Subtle Scrollbar Indicator in Center */}
              <div className="flex-1 flex justify-center">
                <div className="h-1.5 w-32 bg-gray-300/80 dark:bg-gray-600/80 rounded-full" />
              </div>

              {/* Breadcrumb Path on Bottom-Right */}
              <div className="text-[11px] text-gray-400 dark:text-gray-500 font-normal select-none">
                Users &gt; Documents
              </div>
            </div>
          </main>
        </div>
      </div>
    </div>
  );
}
