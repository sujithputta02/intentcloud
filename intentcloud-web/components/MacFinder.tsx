"use client";

import React, { useState, useEffect, useRef } from "react";
import {
  ChevronLeft,
  Share2,
  Eye,
  Tag,
  Search,
  Folder,
  FolderPlus,
  Cloud,
  Monitor,
  FileText,
  Download,
  Play,
  Pause,
  UploadCloud,
  Trash2,
  ExternalLink,
  X,
  Plus,
  ArrowUpRight,
  Sparkles,
} from "lucide-react";
import { API_URL } from "@/lib/api";
import { PreviewableFile } from "./FilePreviewModal";

export interface FolderItem {
  id: string;
  name: string;
  parent_id: string | null;
  color?: string;
  created_at?: number;
  path: string;
  file_count: number;
  subfolder_count: number;
}

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
  // Navigation & Folder Hierarchy
  const [folders, setFolders] = useState<FolderItem[]>([]);
  const [currentFolderId, setCurrentFolderId] = useState<string | null>(null);
  const [folderHistory, setFolderHistory] = useState<(string | null)[]>([null]);
  const [activeCategory, setActiveCategory] = useState<SidebarCategory>("documents");

  // Search & Modal States
  const [searchOpen, setSearchOpen] = useState<boolean>(false);
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [newFolderModalOpen, setNewFolderModalOpen] = useState<boolean>(false);
  const [newFolderName, setNewFolderName] = useState<string>("");
  const [newFolderColor, setNewFolderColor] = useState<string>("blue");
  const [isCreatingFolder, setIsCreatingFolder] = useState<boolean>(false);
  const [isUploading, setIsUploading] = useState<boolean>(false);
  const [activeAudioPlayingId, setActiveAudioPlayingId] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [localFiles, setLocalFiles] = useState<FileItem[]>(files);

  // Sync with prop if it changes
  useEffect(() => {
    if (files && files.length > 0) {
      setLocalFiles(files);
    }
  }, [files]);

  // Fetch Folders and Files from API directly to guarantee fresh data
  const fetchFilesAndFolders = async () => {
    try {
      // Fetch Folders
      const foldersRes = await fetch(`${API_URL}/folders`);
      if (foldersRes.ok) {
        const data = await foldersRes.json();
        const folderArray = Array.isArray(data) ? data : data?.folders || [];
        setFolders(folderArray);
      }

      // Fetch Files
      const filesRes = await fetch(`${API_URL}/files`);
      if (filesRes.ok) {
        const filesData = await filesRes.json();
        if (filesData?.uploaded_files) {
          setLocalFiles(filesData.uploaded_files);
        }
      }
    } catch (err) {
      console.error("Failed to fetch fresh files/folders:", err);
    }
  };

  useEffect(() => {
    fetchFilesAndFolders();
  }, []);

  // Compute Current Folder & Breadcrumb
  const currentFolder = folders.find((f) => f.id === currentFolderId);

  const currentPathBreadcrumb = React.useMemo(() => {
    if (activeCategory === "all") return "Users > All My Files";
    if (activeCategory === "desktop") return "Users > Desktop";
    if (activeCategory === "downloads") return "Users > Downloads";
    if (activeCategory === "icloud") return "iCloud Drive";
    if (activeCategory === "applications") return "Applications";

    if (!currentFolderId) return "Users > Documents";
    const segments: string[] = ["Users", "Documents"];
    let curr: FolderItem | undefined = currentFolder;
    const lineage: string[] = [];
    while (curr) {
      lineage.unshift(curr.name);
      curr = folders.find((f) => f.id === curr?.parent_id);
    }
    return [...segments, ...lineage].join(" > ");
  }, [activeCategory, currentFolderId, currentFolder, folders]);

  // Navigate into a folder
  const handleOpenFolder = (folderId: string) => {
    setFolderHistory((prev) => [...prev, folderId]);
    setCurrentFolderId(folderId);
    setActiveCategory("documents");
  };

  // Back Navigation
  const handleNavigateBack = () => {
    if (folderHistory.length > 1) {
      const newHistory = [...folderHistory];
      newHistory.pop();
      const prevId = newHistory[newHistory.length - 1];
      setFolderHistory(newHistory);
      setCurrentFolderId(prevId);
    } else if (currentFolderId !== null) {
      setCurrentFolderId(null);
      setFolderHistory([null]);
    } else {
      onShowToast("Already at root directory");
    }
  };

  // Filter Subfolders for current view
  const displayedSubfolders = folders.filter((f) => {
    if (searchQuery.trim()) {
      return f.name.toLowerCase().includes(searchQuery.toLowerCase());
    }
    if (activeCategory === "all") {
      return !f.parent_id;
    }
    if (activeCategory === "documents") {
      return f.parent_id === currentFolderId;
    }
    return false;
  });

  // Filter Files for current view
  const activeFileList = localFiles.length > 0 ? localFiles : files;

  const displayedFiles = activeFileList.filter((f) => {
    if (searchQuery.trim()) {
      return f.name.toLowerCase().includes(searchQuery.toLowerCase());
    }
    if (activeCategory === "all") return true;
    if (activeCategory === "icloud") return true;
    if (activeCategory === "downloads") {
      return ["zip", "dmg", "tar", "gz"].includes((f.extension || "").toLowerCase());
    }
    if (activeCategory === "desktop") {
      return ["png", "jpg", "jpeg", "svg", "webp"].includes((f.extension || "").toLowerCase());
    }
    if (activeCategory === "applications") {
      return ["py", "sh", "ts", "js", "html", "css"].includes((f.extension || "").toLowerCase());
    }
    
    // In Documents view:
    if (currentFolderId) {
      return f.folder_id === currentFolderId;
    }
    // At root documents: show files not assigned to a subfolder
    return !f.folder_id;
  });

  // Create New Folder
  const handleCreateFolder = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newFolderName.trim()) return;

    setIsCreatingFolder(true);
    try {
      const res = await fetch(`${API_URL}/folders`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: newFolderName.trim(),
          parent_id: currentFolderId,
          color: newFolderColor,
        }),
      });

      if (res.ok) {
        onShowToast(`Folder "${newFolderName}" created`);
        setNewFolderName("");
        setNewFolderModalOpen(false);
        await fetchFilesAndFolders();
        onRefresh();
      } else {
        const err = await res.json().catch(() => ({}));
        onShowToast(err.detail || "Failed to create folder");
      }
    } catch (err) {
      console.error(err);
      onShowToast("Network error creating folder");
    } finally {
      setIsCreatingFolder(false);
    }
  };

  // Delete Folder
  const handleDeleteFolder = async (folderId: string, folderName: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm(`Are you sure you want to delete folder "${folderName}"?`)) return;

    try {
      const res = await fetch(`${API_URL}/folders/${folderId}`, {
        method: "DELETE",
      });
      if (res.ok) {
        onShowToast(`Deleted folder "${folderName}"`);
        await fetchFilesAndFolders();
        onRefresh();
      } else {
        onShowToast("Failed to delete folder");
      }
    } catch (err) {
      console.error(err);
      onShowToast("Error deleting folder");
    }
  };

  // Direct File Upload into Current Folder
  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const fileList = e.target.files;
    if (!fileList || fileList.length === 0) return;

    const file = fileList[0];
    const formData = new FormData();
    formData.append("file", file);
    if (currentFolderId) {
      formData.append("folder_id", currentFolderId);
    }

    setIsUploading(true);
    onShowToast(`Uploading "${file.name}"...`);
    try {
      const res = await fetch(`${API_URL}/upload`, {
        method: "POST",
        body: formData,
      });

      if (res.ok) {
        onShowToast(`Uploaded "${file.name}" successfully`);
        await fetchFilesAndFolders();
        onRefresh();
      } else {
        onShowToast(`Upload failed for "${file.name}"`);
      }
    } catch (err) {
      console.error(err);
      onShowToast("Upload network error");
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  // Color helper for folder badges
  const getFolderColorGradient = (color?: string) => {
    switch (color) {
      case "purple":
        return "from-[#4c1d95] via-[#581c87] to-[#3b0764]";
      case "amber":
        return "from-[#b45309] via-[#d97706] to-[#78350f]";
      case "emerald":
        return "from-[#065f46] via-[#047857] to-[#064e3b]";
      case "rose":
        return "from-[#9f1239] via-[#be123c] to-[#881337]";
      default:
        return "from-[#1e3a8a] via-[#1d4ed8] to-[#172554]";
    }
  };

  return (
    <div className="relative w-full rounded-[24px] sm:rounded-[28px] bg-[#f5f6f8] dark:bg-[#18191e] border border-black/[0.08] dark:border-white/[0.08] shadow-xl overflow-hidden flex flex-col min-h-[640px] font-sans">
      {/* Hidden File Input for Native macOS Finder Uploads */}
      <input
        type="file"
        ref={fileInputRef}
        onChange={handleFileUpload}
        className="hidden"
      />

      {/* TOP TOOLBAR */}
      <div className="h-14 px-5 border-b border-black/[0.05] dark:border-white/[0.06] flex items-center justify-between select-none">
          {/* Traffic Lights & Back Arrow */}
          <div className="flex items-center space-x-5">
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
              onClick={handleNavigateBack}
              className={`p-1 transition ${
                currentFolderId !== null || folderHistory.length > 1
                  ? "text-gray-700 dark:text-gray-200 hover:scale-110"
                  : "text-gray-400 dark:text-gray-600 cursor-default"
              }`}
              title="Back"
            >
              <ChevronLeft className="w-5 h-5 stroke-[1.75]" />
            </button>
          </div>

          {/* Center Search / Action Toolbar */}
          <div className="flex-1 max-w-sm mx-4 flex items-center justify-center">
            {searchOpen ? (
              <div className="w-full relative">
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search files & folders..."
                  autoFocus
                  className="w-full bg-white/80 dark:bg-black/40 border border-gray-300 dark:border-gray-700 rounded-full px-3 py-1.5 text-xs text-gray-800 dark:text-gray-200 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500/40"
                />
                {searchQuery && (
                  <button
                    type="button"
                    onClick={() => setSearchQuery("")}
                    className="absolute right-2.5 top-2 text-gray-400 hover:text-gray-600"
                  >
                    <X className="w-3.5 h-3.5" />
                  </button>
                )}
              </div>
            ) : (
              <div className="flex items-center space-x-2">
                {/* New Folder Button */}
                <button
                  type="button"
                  onClick={() => setNewFolderModalOpen(true)}
                  className="flex items-center space-x-1.5 px-3 py-1 rounded-xl bg-black/[0.04] dark:bg-white/[0.06] hover:bg-black/[0.08] dark:hover:bg-white/[0.12] text-xs font-semibold text-gray-700 dark:text-gray-200 transition shadow-xs"
                >
                  <FolderPlus className="w-3.5 h-3.5 text-blue-500" />
                  <span>New Folder</span>
                </button>

                {/* Upload File Button */}
                <button
                  type="button"
                  onClick={() => fileInputRef.current?.click()}
                  disabled={isUploading}
                  className="flex items-center space-x-1.5 px-3 py-1 rounded-xl bg-black/[0.04] dark:bg-white/[0.06] hover:bg-black/[0.08] dark:hover:bg-white/[0.12] text-xs font-semibold text-gray-700 dark:text-gray-200 transition shadow-xs disabled:opacity-50"
                >
                  <UploadCloud className="w-3.5 h-3.5 text-amber-500" />
                  <span>{isUploading ? "Uploading..." : "Upload File"}</span>
                </button>
              </div>
            )}
          </div>

          {/* Action Toolbar Icons (Share, Quick Look, Tag, Search) */}
          <div className="flex items-center space-x-3 text-gray-400 dark:text-gray-400">
            <button
              type="button"
              onClick={() => onShowToast("Shared directory link")}
              className="p-1 hover:text-gray-700 dark:hover:text-gray-200 transition"
              title="Share"
            >
              <Share2 className="w-4 h-4 stroke-[1.75]" />
            </button>
            <button
              type="button"
              onClick={() => {
                if (displayedFiles.length > 0) {
                  onPreview(displayedFiles[0] as unknown as PreviewableFile);
                } else {
                  onShowToast("Select a file to Quick Look");
                }
              }}
              className="p-1 hover:text-gray-700 dark:hover:text-gray-200 transition"
              title="Quick Look"
            >
              <Eye className="w-4 h-4 stroke-[1.75]" />
            </button>
            <button
              type="button"
              onClick={() => onShowToast("Filtered by topic tags")}
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
            <nav className="space-y-1 text-xs overflow-y-auto max-h-[460px]">
              <button
                type="button"
                onClick={() => {
                  setActiveCategory("all");
                  setCurrentFolderId(null);
                }}
                className={`w-full flex items-center space-x-3 px-3 py-2 rounded-xl transition ${
                  activeCategory === "all"
                    ? "bg-black/[0.08] dark:bg-white/[0.12] text-gray-900 dark:text-white font-semibold shadow-xs"
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
                  setCurrentFolderId(null);
                }}
                className={`w-full flex items-center space-x-3 px-3 py-2 rounded-xl transition ${
                  activeCategory === "icloud"
                    ? "bg-black/[0.08] dark:bg-white/[0.12] text-gray-900 dark:text-white font-semibold shadow-xs"
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
                  setCurrentFolderId(null);
                }}
                className={`w-full flex items-center space-x-3 px-3 py-2 rounded-xl transition ${
                  activeCategory === "applications"
                    ? "bg-black/[0.08] dark:bg-white/[0.12] text-gray-900 dark:text-white font-semibold shadow-xs"
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
                  setCurrentFolderId(null);
                }}
                className={`w-full flex items-center space-x-3 px-3 py-2 rounded-xl transition ${
                  activeCategory === "desktop"
                    ? "bg-black/[0.08] dark:bg-white/[0.12] text-gray-900 dark:text-white font-semibold shadow-xs"
                    : "text-gray-600 dark:text-gray-400 hover:bg-black/[0.03] dark:hover:bg-white/[0.05]"
                }`}
              >
                <Monitor className="w-4 h-4 text-gray-500" />
                <span>Desktop</span>
              </button>

              {/* DOCUMENTS (EXACT ACTIVE STATE PILL FROM SCREENSHOT) */}
              <button
                type="button"
                onClick={() => {
                  setActiveCategory("documents");
                  setCurrentFolderId(null);
                }}
                className={`w-full flex items-center space-x-3 px-3 py-2 rounded-xl transition ${
                  activeCategory === "documents" && currentFolderId === null
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
                  setCurrentFolderId(null);
                }}
                className={`w-full flex items-center space-x-3 px-3 py-2 rounded-xl transition ${
                  activeCategory === "downloads"
                    ? "bg-black/[0.08] dark:bg-white/[0.12] text-gray-900 dark:text-white font-semibold shadow-xs"
                    : "text-gray-600 dark:text-gray-400 hover:bg-black/[0.03] dark:hover:bg-white/[0.05]"
                }`}
              >
                <Download className="w-4 h-4 text-gray-500" />
                <span>Downloads</span>
              </button>

              {/* REAL USER FOLDERS LIST */}
              {folders.length > 0 && (
                <div className="pt-3">
                  <div className="px-3 py-1 text-[10px] font-bold tracking-wider uppercase text-gray-400 dark:text-gray-500">
                    My Folders
                  </div>
                  <div className="space-y-0.5 mt-1">
                    {folders
                      .filter((f) => !f.parent_id)
                      .map((folder) => (
                        <button
                          key={folder.id}
                          type="button"
                          onClick={() => handleOpenFolder(folder.id)}
                          className={`w-full flex items-center justify-between px-3 py-1.5 rounded-xl transition text-xs ${
                            currentFolderId === folder.id
                              ? "bg-black/[0.08] dark:bg-white/[0.12] text-gray-900 dark:text-white font-semibold shadow-xs"
                              : "text-gray-600 dark:text-gray-400 hover:bg-black/[0.03] dark:hover:bg-white/[0.05]"
                          }`}
                        >
                          <div className="flex items-center space-x-2.5 truncate">
                            <Folder className="w-3.5 h-3.5 text-blue-500 shrink-0" />
                            <span className="truncate">{folder.name}</span>
                          </div>
                          <span className="text-[10px] text-gray-400">
                            {folder.file_count || 0}
                          </span>
                        </button>
                      ))}
                  </div>
                </div>
              )}
            </nav>

            <div className="pt-4 border-t border-black/[0.04] dark:border-white/[0.06] text-[11px] text-gray-400 dark:text-gray-500 hidden md:block">
              IntentCloud Edge Node
            </div>
          </aside>

          {/* MAIN CONTENT AREA */}
          <main className="flex-1 p-6 sm:p-8 flex flex-col justify-between overflow-y-auto max-h-[640px]">
            <div>
              {/* LARGE BOLD HEADER */}
              <div className="flex items-center justify-between mb-7">
                <h1 className="text-3xl sm:text-4xl font-extrabold text-[#1d1d1f] dark:text-white tracking-tight capitalize truncate">
                  {currentFolder ? currentFolder.name : activeCategory}
                </h1>
                
                <div className="flex items-center space-x-2">
                  <button
                    type="button"
                    onClick={() => setNewFolderModalOpen(true)}
                    className="flex items-center space-x-1 px-3 py-1.5 rounded-xl bg-blue-500/10 hover:bg-blue-500/20 text-blue-600 dark:text-blue-400 text-xs font-semibold transition"
                  >
                    <Plus className="w-3.5 h-3.5" />
                    <span>New Folder</span>
                  </button>
                  <button
                    type="button"
                    onClick={() => fileInputRef.current?.click()}
                    className="flex items-center space-x-1 px-3 py-1.5 rounded-xl bg-amber-500/10 hover:bg-amber-500/20 text-amber-600 dark:text-amber-400 text-xs font-semibold transition"
                  >
                    <UploadCloud className="w-3.5 h-3.5" />
                    <span>Upload</span>
                  </button>
                </div>
              </div>

              {/* CARDS GRID: REAL SUBFOLDERS & REAL FILES STYLED EXACTLY LIKE SCREENSHOT */}
              {displayedSubfolders.length === 0 && displayedFiles.length === 0 ? (
                /* EMPTY STATE */
                <div className="py-20 text-center flex flex-col items-center justify-center">
                  <div className="w-16 h-16 rounded-3xl bg-black/[0.03] dark:bg-white/[0.05] border border-black/[0.06] dark:border-white/[0.08] flex items-center justify-center mb-4">
                    <Folder className="w-8 h-8 text-gray-400 opacity-60" />
                  </div>
                  <h3 className="text-sm font-bold text-gray-800 dark:text-gray-200">
                    This folder is empty
                  </h3>
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-1 max-w-xs">
                    Create a subfolder or upload documents to start organizing your cognitive memory.
                  </p>
                  <div className="flex items-center space-x-3 mt-5">
                    <button
                      type="button"
                      onClick={() => setNewFolderModalOpen(true)}
                      className="px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold shadow-sm transition"
                    >
                      + Create Folder
                    </button>
                    <button
                      type="button"
                      onClick={() => fileInputRef.current?.click()}
                      className="px-4 py-2 rounded-xl bg-black/[0.06] dark:bg-white/[0.08] hover:bg-black/[0.1] text-gray-800 dark:text-gray-200 text-xs font-semibold transition"
                    >
                      Upload File
                    </button>
                  </div>
                </div>
              ) : (
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 items-start">
                  
                  {/* 1. RENDER SUBFOLDERS (EXACT "PROJECT FILES" STACKED ALBUM CARD STYLE) */}
                  {displayedSubfolders.map((folder) => (
                    <div
                      key={folder.id}
                      onClick={() => handleOpenFolder(folder.id)}
                      className="group relative h-44 rounded-2xl bg-gradient-to-b from-[#f1f3f6] to-[#d8dde6] dark:from-[#2a2c35] dark:to-[#1c1e24] p-3 shadow-[0_14px_32px_rgba(0,0,0,0.18)] cursor-pointer transition-all duration-300 hover:scale-[1.03] flex flex-col justify-between"
                    >
                      {/* Stacked Thumbnails / Folder Previews */}
                      <div className="grid grid-cols-2 gap-2 h-26">
                        <div className={`rounded-xl overflow-hidden bg-gradient-to-br ${getFolderColorGradient(folder.color)} relative shadow-inner p-2.5 flex flex-col justify-between`}>
                          <Folder className="w-4 h-4 text-white/80" />
                          <span className="text-[10px] text-white/80 font-mono">
                            {folder.file_count || 0} files
                          </span>
                        </div>
                        <div className="rounded-xl overflow-hidden bg-gradient-to-br from-slate-900 to-sky-950 relative shadow-inner p-2.5 flex flex-col justify-between">
                          <div className="w-4 h-1 bg-white/40 rounded-full" />
                          <span className="text-[10px] text-white/60 font-mono">
                            Folder
                          </span>
                        </div>
                      </div>

                      {/* Bottom Label & Delete Trigger */}
                      <div className="flex items-center justify-between px-1">
                        <span className="text-gray-900 dark:text-white font-bold text-sm tracking-tight truncate">
                          {folder.name}
                        </span>
                        <button
                          type="button"
                          onClick={(e) => handleDeleteFolder(folder.id, folder.name, e)}
                          className="opacity-0 group-hover:opacity-100 p-1 text-gray-400 hover:text-red-500 transition"
                          title="Delete folder"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>
                  ))}

                  {/* 2. RENDER REAL FILES (STYLED ACCORDING TO FILE TYPE MATCHING SCREENSHOT) */}
                  {displayedFiles.map((file) => {
                    const ext = (file.extension || "").toLowerCase();
                    const isCode = ["py", "ts", "js", "html", "css", "json", "sh", "cpp", "java"].includes(ext);
                    const isAudio = ["mp3", "wav", "m4a", "ogg", "flac"].includes(ext);
                    const isImage = ["jpg", "jpeg", "png", "svg", "webp", "gif"].includes(ext);

                    // A. CODE FILE -> "index" DARK SYNTAX CARD STYLE
                    if (isCode) {
                      return (
                        <div
                          key={file.file_id}
                          onClick={() => onPreview(file as unknown as PreviewableFile)}
                          className="group cursor-pointer transition-all duration-300 hover:scale-[1.03]"
                        >
                          <div className="h-28 rounded-2xl bg-[#1e1e24] p-3.5 shadow-[0_12px_28px_rgba(0,0,0,0.25)] flex flex-col justify-between">
                            <div className="flex items-center space-x-2 text-xs">
                              <span className="text-cyan-400 font-mono font-semibold">&lt;&gt;</span>
                              <span className="text-amber-400 font-mono font-medium">.{ext}</span>
                            </div>
                            <div className="text-[11px] font-mono text-purple-400 truncate">
                              &lt;import {file.name.replace(/\.[^/.]+$/, "")}&gt;
                            </div>
                            <div className="text-[10px] text-gray-500 font-mono">
                              {(file.size_bytes / 1024).toFixed(1)} KB
                            </div>
                          </div>
                          <p className="text-xs text-center text-gray-700 dark:text-gray-300 font-medium mt-1.5 truncate px-1">
                            {file.name}
                          </p>
                        </div>
                      );
                    }

                    // B. AUDIO FILE -> "final soundtrack" FROSTED LILAC WAVEFORM CARD STYLE
                    if (isAudio) {
                      const isPlaying = activeAudioPlayingId === file.file_id;
                      return (
                        <div
                          key={file.file_id}
                          onClick={() => {
                            setActiveAudioPlayingId(isPlaying ? null : file.file_id);
                            onShowToast(isPlaying ? `Paused ${file.name}` : `Playing ${file.name}`);
                          }}
                          className="group cursor-pointer transition-all duration-300 hover:scale-[1.02]"
                        >
                          <div className="h-28 rounded-2xl bg-gradient-to-r from-[#d9cbe8] via-[#e2d4f0] to-[#ece1f7] dark:from-[#352c42] dark:to-[#4a3b5c] p-3.5 shadow-[0_12px_28px_rgba(147,112,219,0.2)] flex items-center space-x-3">
                            <div className="w-8 h-8 rounded-xl bg-white/60 dark:bg-white/20 backdrop-blur-md flex items-center justify-center text-purple-900 dark:text-purple-200 shrink-0 shadow-xs">
                              {isPlaying ? (
                                <Pause className="w-4 h-4 fill-purple-900 dark:fill-purple-200" />
                              ) : (
                                <Play className="w-4 h-4 fill-purple-900 dark:fill-purple-200 ml-0.5" />
                              )}
                            </div>
                            <div className="flex-1 flex items-center justify-between h-8 space-x-0.5">
                              {[4, 10, 18, 26, 14, 22, 28, 16, 24, 30, 20, 12, 18, 25, 15, 8].map((h, i) => (
                                <div
                                  key={i}
                                  className={`w-1 rounded-full transition-all duration-300 ${
                                    isPlaying ? "bg-purple-700 dark:bg-purple-300" : "bg-purple-700/50 dark:bg-purple-400/50"
                                  }`}
                                  style={{ height: `${h}px` }}
                                />
                              ))}
                            </div>
                          </div>
                          <p className="text-xs text-center text-gray-700 dark:text-gray-300 font-medium mt-1.5 truncate px-1">
                            {file.name}
                          </p>
                        </div>
                      );
                    }

                    // C. IMAGE FILE -> "canyon" / "jellyfish" PHOTO TILE STYLE
                    if (isImage) {
                      return (
                        <div
                          key={file.file_id}
                          onClick={() => onPreview(file as unknown as PreviewableFile)}
                          className="group cursor-pointer transition-all duration-300 hover:scale-[1.03]"
                        >
                          <div className="h-28 rounded-2xl overflow-hidden shadow-[0_12px_28px_rgba(15,23,42,0.25)] bg-gradient-to-br from-[#c2410c] via-[#ea580c] to-[#7c2d12] relative p-3 flex flex-col justify-between">
                            <div className="self-start px-1.5 py-0.5 rounded-md bg-black/40 text-white font-bold text-[10px] tracking-tight backdrop-blur-md">
                              {ext.toUpperCase()}
                            </div>
                            <div className="text-[10px] text-white/90 font-medium drop-shadow-sm">
                              {(file.size_bytes / 1024).toFixed(1)} KB
                            </div>
                          </div>
                          <p className="text-xs text-center text-gray-700 dark:text-gray-300 font-medium mt-1.5 truncate px-1">
                            {file.name}
                          </p>
                        </div>
                      );
                    }

                    // D. DOCUMENT / PDF / GENERAL -> "aerial-01" / "project" BLUE GRADIENT CARD STYLE
                    return (
                      <div
                        key={file.file_id}
                        onClick={() => onPreview(file as unknown as PreviewableFile)}
                        className="group relative h-44 rounded-2xl overflow-hidden shadow-[0_16px_36px_rgba(0,119,182,0.3)] cursor-pointer transition-all duration-300 hover:scale-[1.03] bg-gradient-to-br from-[#0077b6] via-[#0096c7] to-[#48cae4] p-3.5 flex flex-col justify-between"
                      >
                        <div className="flex items-center justify-between">
                          <div className="w-7 h-7 rounded-full bg-white/30 backdrop-blur-md flex items-center justify-center shadow-xs">
                            <FileText className="w-3.5 h-3.5 text-white" />
                          </div>
                          <span className="text-[10px] font-bold text-white/90 uppercase px-2 py-0.5 rounded-full bg-black/20 backdrop-blur-sm">
                            {ext || "doc"}
                          </span>
                        </div>

                        <div>
                          <span className="text-white font-bold text-sm tracking-wide drop-shadow-[0_2px_4px_rgba(0,0,0,0.4)] line-clamp-2">
                            {file.name}
                          </span>
                          <span className="text-[11px] text-white/80 mt-1 block">
                            {(file.size_bytes / 1024).toFixed(1)} KB • {file.file_type_category || "Document"}
                          </span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>

            {/* BOTTOM STATUS & BREADCRUMB BAR */}
            <div className="pt-6 mt-8 border-t border-black/[0.04] dark:border-white/[0.06] flex items-center justify-between select-none">
              {/* Subtle Scrollbar Indicator in Center */}
              <div className="flex-1 flex justify-center">
                <div className="h-1.5 w-32 bg-gray-300/80 dark:bg-gray-600/80 rounded-full" />
              </div>

              {/* Dynamic Breadcrumb Path on Bottom-Right */}
              <div className="text-[11px] text-gray-400 dark:text-gray-500 font-normal truncate max-w-xs">
                {currentPathBreadcrumb}
              </div>
            </div>
          </main>
        </div>

      {/* MODAL: NEW FOLDER CREATION */}
      {newFolderModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4 animate-in fade-in duration-200">
          <div className="w-full max-w-sm rounded-2xl bg-white dark:bg-[#202127] border border-gray-200 dark:border-gray-700 shadow-2xl p-5 text-gray-900 dark:text-white">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center space-x-2">
                <FolderPlus className="w-5 h-5 text-blue-500" />
                <h3 className="font-bold text-sm">New Folder</h3>
              </div>
              <button
                type="button"
                onClick={() => setNewFolderModalOpen(false)}
                className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleCreateFolder} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-gray-500 dark:text-gray-400 mb-1">
                  Folder Name
                </label>
                <input
                  type="text"
                  value={newFolderName}
                  onChange={(e) => setNewFolderName(e.target.value)}
                  placeholder="e.g. Distributed Systems"
                  autoFocus
                  required
                  className="w-full px-3 py-2 text-xs rounded-xl bg-gray-50 dark:bg-black/30 border border-gray-300 dark:border-gray-600 focus:outline-none focus:ring-2 focus:ring-blue-500/40"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-500 dark:text-gray-400 mb-1.5">
                  Folder Color Accent
                </label>
                <div className="flex items-center space-x-2">
                  {[
                    { name: "blue", bg: "bg-blue-500" },
                    { name: "purple", bg: "bg-purple-500" },
                    { name: "emerald", bg: "bg-emerald-500" },
                    { name: "amber", bg: "bg-amber-500" },
                    { name: "rose", bg: "bg-rose-500" },
                  ].map((c) => (
                    <button
                      key={c.name}
                      type="button"
                      onClick={() => setNewFolderColor(c.name)}
                      className={`w-6 h-6 rounded-full ${c.bg} transition ${
                        newFolderColor === c.name
                          ? "ring-2 ring-offset-2 ring-blue-500 scale-110"
                          : "opacity-70 hover:opacity-100"
                      }`}
                      aria-label={c.name}
                    />
                  ))}
                </div>
              </div>

              <div className="flex items-center justify-end space-x-2 pt-2">
                <button
                  type="button"
                  onClick={() => setNewFolderModalOpen(false)}
                  className="px-3 py-1.5 rounded-xl text-xs font-semibold text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-white/10 transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isCreatingFolder || !newFolderName.trim()}
                  className="px-4 py-1.5 rounded-xl text-xs font-semibold bg-blue-600 hover:bg-blue-700 text-white transition disabled:opacity-50 shadow-sm"
                >
                  {isCreatingFolder ? "Creating..." : "Create"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
