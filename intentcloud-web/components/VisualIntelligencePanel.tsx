"use client";

import React, { useState, useMemo } from "react";
import { 
  Sparkles, Palette, Layers, Cpu, Search, Type, 
  Terminal, Copy, Check, Info, Hash, ExternalLink 
} from "lucide-react";

export interface ColorSwatch {
  name: string;
  hex: string;
}

export interface VisualConcept {
  title: string;
  body: string;
  type: "palette" | "presentation" | "architecture" | "general";
}

export interface ParsedVisualMetadata {
  format: string;
  resolution: string;
  colorMode: string;
  keywords: string;
  swatches: ColorSwatch[];
  concepts: VisualConcept[];
  ocrLines: string[];
  vlmCaption: string;
  rawText: string;
}

/**
 * Robust parser for IntentCloud visual semantic text
 */
export function parseVisualMetadata(raw: string): ParsedVisualMetadata {
  const result: ParsedVisualMetadata = {
    format: "",
    resolution: "",
    colorMode: "",
    keywords: "",
    swatches: [],
    concepts: [],
    ocrLines: [],
    vlmCaption: "",
    rawText: raw || ""
  };

  if (!raw) return result;

  // 1. Technical Specs
  const resMatch = raw.match(/Resolution:\s*([0-9xX]+(?:\s*pixels)?)/i);
  if (resMatch) result.resolution = resMatch[1].replace(/pixels/i, "").trim();

  const formatMatch = raw.match(/Format:\s*([^,\n]+)/i);
  if (formatMatch) result.format = formatMatch[1].trim();

  const colorMatch = raw.match(/Color Mode:\s*([^\n,]+)/i);
  if (colorMatch) result.colorMode = colorMatch[1].trim();

  const kwMatch = raw.match(/Subject \/ Filename Keywords:\s*([^\n]+)/i);
  if (kwMatch) result.keywords = kwMatch[1].trim();

  // 2. Swatches (from Swatches: line or OCR)
  const swatchesLineMatch = raw.match(/Swatches:\s*([^\n]+)/i);
  const foundHexes = new Set<string>();

  if (swatchesLineMatch) {
    const swatchStr = swatchesLineMatch[1];
    const swatchRegex = /(?:([A-Za-z0-9\s_-]+)\s*)?\((#[0-9a-fA-F]{6})\)|(#[0-9a-fA-F]{6})/g;
    let match;
    while ((match = swatchRegex.exec(swatchStr)) !== null) {
      const hex = (match[2] || match[3]).toUpperCase();
      if (!foundHexes.has(hex)) {
        foundHexes.add(hex);
        let name = (match[1] || "").trim();
        if (name) {
          name = name.toLowerCase().replace(/\b\w/g, (c) => c.toUpperCase());
        } else {
          name = hex;
        }
        result.swatches.push({ name, hex });
      }
    }
  }

  // 3. Concepts
  const conceptRegex = /\[Visual Concept:\s*([^\]]+)\]\s*\n([\s\S]*?)(?=(?:\n\[Visual Concept:|\n---\s*VISUAL|\n$))/g;
  let cmatch;
  while ((cmatch = conceptRegex.exec(raw)) !== null) {
    const title = cmatch[1].trim();
    const rawBody = cmatch[2].replace(/Swatches:\s*[^\n]+/i, "").trim();
    
    let type: "palette" | "presentation" | "architecture" | "general" = "general";
    const lowerTitle = title.toLowerCase();
    if (lowerTitle.includes("palette") || lowerTitle.includes("color") || lowerTitle.includes("branding")) {
      type = "palette";
    } else if (lowerTitle.includes("slide") || lowerTitle.includes("presentation") || lowerTitle.includes("deck")) {
      type = "presentation";
    } else if (lowerTitle.includes("architecture") || lowerTitle.includes("topology") || lowerTitle.includes("system")) {
      type = "architecture";
    }

    result.concepts.push({ title, body: rawBody, type });
  }

  // 4. OCR text
  const ocrMatch = raw.match(/---\s*VISUAL TEXT & LABELS EXTRACTED FROM IMAGE[^\n]*---\n([\s\S]*?)(?=(?:\n---\s*VISUAL SCENE|\n$))/i);
  if (ocrMatch) {
    result.ocrLines = ocrMatch[1]
      .split("\n")
      .map((l) => l.trim())
      .filter((l) => l.length > 0);

    // Fallback: If no swatches parsed yet, check OCR lines for hex codes
    if (result.swatches.length === 0) {
      for (let i = 0; i < result.ocrLines.length; i++) {
        const line = result.ocrLines[i];
        const hex = line.match(/^#[0-9a-fA-F]{6}$/);
        if (hex) {
          const hexVal = hex[0].toUpperCase();
          if (!foundHexes.has(hexVal)) {
            foundHexes.add(hexVal);
            const prevLine = i > 0 ? result.ocrLines[i - 1] : "";
            const name = prevLine && prevLine.length <= 25 && !prevLine.startsWith("#")
              ? prevLine.toLowerCase().replace(/\b\w/g, (c) => c.toUpperCase())
              : hexVal;
            result.swatches.push({ name, hex: hexVal });
          }
        }
      }
    }
  }

  // 5. VLM Caption
  const vlmMatch = raw.match(/---\s*VISUAL SCENE & DIAGRAM DESCRIPTION[^\n]*---\n([\s\S]*)$/i);
  if (vlmMatch) {
    result.vlmCaption = vlmMatch[1].trim();
  }

  return result;
}

// Determines whether a color is light so we can render an outline
function isLightColor(hex: string): boolean {
  const clean = hex.replace("#", "");
  if (clean.length !== 6) return false;
  const r = parseInt(clean.slice(0, 2), 16);
  const g = parseInt(clean.slice(2, 4), 16);
  const b = parseInt(clean.slice(4, 6), 16);
  const lum = (0.299 * r + 0.587 * g + 0.114 * b) / 255;
  return lum > 0.72;
}

interface VisualIntelligencePanelProps {
  rawMetadata: string;
  filename?: string;
}

export default function VisualIntelligencePanel({ rawMetadata, filename }: VisualIntelligencePanelProps) {
  const [activeTab, setActiveTab] = useState<"insights" | "text" | "raw">("insights");
  const [copiedHex, setCopiedHex] = useState<string | null>(null);
  const [copiedAllOcr, setCopiedAllOcr] = useState(false);
  const [copiedRaw, setCopiedRaw] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");

  const data = useMemo(() => parseVisualMetadata(rawMetadata), [rawMetadata]);

  const handleCopyHex = (hex: string, e?: React.MouseEvent) => {
    e?.stopPropagation();
    navigator.clipboard.writeText(hex);
    setCopiedHex(hex);
    setTimeout(() => setCopiedHex(null), 1800);
  };

  const handleCopyAllOcr = () => {
    if (!data.ocrLines.length) return;
    navigator.clipboard.writeText(data.ocrLines.join("\n"));
    setCopiedAllOcr(true);
    setTimeout(() => setCopiedAllOcr(false), 2000);
  };

  const handleCopyRaw = () => {
    navigator.clipboard.writeText(rawMetadata);
    setCopiedRaw(true);
    setTimeout(() => setCopiedRaw(false), 2000);
  };

  const filteredOcrLines = useMemo(() => {
    if (!searchQuery.trim()) return data.ocrLines;
    const q = searchQuery.toLowerCase();
    return data.ocrLines.filter((line) => line.toLowerCase().includes(q));
  }, [data.ocrLines, searchQuery]);

  return (
    <div className="flex flex-col h-full bg-[var(--bg-surface)] text-[var(--text-primary)]">
      {/* Top Header */}
      <div className="px-4 py-3 border-b border-[var(--border-subtle)] bg-[var(--bg-surface)]/95 backdrop-blur shrink-0 space-y-2.5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-lg bg-gradient-to-tr from-[#B45F3C]/20 to-purple-500/20 border border-[#B45F3C]/30 flex items-center justify-center text-[#B45F3C] dark:text-[#E08556]">
              <Sparkles className="w-4 h-4" />
            </div>
            <div>
              <div className="text-xs font-bold uppercase tracking-wider text-[var(--text-primary)] flex items-center gap-1.5 font-fraunces">
                Visual Intelligence
              </div>
              <p className="text-[10px] text-[var(--text-secondary)]">
                Apple Neural Engine OCR • Semantic Perception
              </p>
            </div>
          </div>

          <div className="flex items-center gap-1 text-[10px] font-semibold">
            {data.swatches.length > 0 && (
              <span className="px-2 py-0.5 rounded-full bg-rose-500/10 text-rose-500 border border-rose-500/20 flex items-center gap-1">
                <Palette className="w-2.5 h-2.5" /> {data.swatches.length} Swatches
              </span>
            )}
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="flex p-0.5 rounded-xl bg-[var(--bg-base)] border border-[var(--border-subtle)] text-xs font-medium">
          <button
            onClick={() => setActiveTab("insights")}
            type="button"
            className={`flex-1 flex items-center justify-center gap-1.5 py-1.5 rounded-lg transition text-xs font-semibold ${
              activeTab === "insights"
                ? "bg-[var(--bg-surface)] text-[var(--text-primary)] shadow-sm border border-[var(--border-subtle)]"
                : "text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
            }`}
          >
            <Sparkles className="w-3.5 h-3.5 text-[#B45F3C] dark:text-[#E08556]" />
            <span>Insights</span>
          </button>

          <button
            onClick={() => setActiveTab("text")}
            type="button"
            className={`flex-1 flex items-center justify-center gap-1.5 py-1.5 rounded-lg transition text-xs font-semibold ${
              activeTab === "text"
                ? "bg-[var(--bg-surface)] text-[var(--text-primary)] shadow-sm border border-[var(--border-subtle)]"
                : "text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
            }`}
          >
            <Type className="w-3.5 h-3.5 text-blue-500" />
            <span>Extracted Text</span>
            {data.ocrLines.length > 0 && (
              <span className="text-[10px] font-mono px-1.5 py-0.2 rounded-full bg-[var(--border-subtle)] text-[var(--text-secondary)]">
                {data.ocrLines.length}
              </span>
            )}
          </button>

          <button
            onClick={() => setActiveTab("raw")}
            type="button"
            className={`flex-1 flex items-center justify-center gap-1.5 py-1.5 rounded-lg transition text-xs font-semibold ${
              activeTab === "raw"
                ? "bg-[var(--bg-surface)] text-[var(--text-primary)] shadow-sm border border-[var(--border-subtle)]"
                : "text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
            }`}
          >
            <Terminal className="w-3.5 h-3.5 text-emerald-500" />
            <span>Raw</span>
          </button>
        </div>
      </div>

      {/* Main Tab Content */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 text-xs scrollbar-thin">
        {activeTab === "insights" && (
          <div className="space-y-4 animate-in fade-in duration-150">
            {/* 1. Color Palette / Swatches */}
            {data.swatches.length > 0 && (
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-[11px] font-bold tracking-wider uppercase text-[var(--text-secondary)] flex items-center gap-1.5">
                    <Palette className="w-3.5 h-3.5 text-[#B45F3C] dark:text-[#E08556]" />
                    Detected Brand Swatches ({data.swatches.length})
                  </span>
                  <span className="text-[10px] text-[var(--text-muted)]">Click swatch to copy hex</span>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                  {data.swatches.map((swatch, idx) => {
                    const isCopied = copiedHex === swatch.hex;
                    const light = isLightColor(swatch.hex);

                    return (
                      <div
                        key={idx}
                        onClick={() => handleCopyHex(swatch.hex)}
                        className="group relative flex items-center gap-2.5 p-2 rounded-xl bg-[var(--bg-base)] border border-[var(--border-subtle)] hover:border-[#B45F3C]/50 hover:shadow-md transition cursor-pointer select-none"
                        title={`Click to copy ${swatch.hex}`}
                      >
                        {/* Swatch preview */}
                        <div
                          className={`w-9 h-9 rounded-lg shrink-0 shadow-inner flex items-center justify-center relative transition-transform group-hover:scale-105 ${
                            light ? "border border-black/15 dark:border-white/20" : "border border-black/10"
                          }`}
                          style={{ backgroundColor: swatch.hex }}
                        >
                          {isCopied && (
                            <div className="absolute inset-0 rounded-lg bg-black/40 backdrop-blur-xs flex items-center justify-center">
                              <Check className="w-4 h-4 text-white drop-shadow" />
                            </div>
                          )}
                        </div>

                        {/* Swatch details */}
                        <div className="min-w-0 flex-1">
                          <div className="text-xs font-semibold text-[var(--text-primary)] truncate" title={swatch.name}>
                            {swatch.name}
                          </div>
                          <div className="text-[11px] font-mono text-[var(--text-secondary)] flex items-center gap-1 mt-0.5">
                            <span className="opacity-75">#</span>
                            <span className="font-semibold">{swatch.hex.replace("#", "")}</span>
                          </div>
                        </div>

                        {/* Copy button */}
                        <button
                          onClick={(e) => handleCopyHex(swatch.hex, e)}
                          type="button"
                          className="p-1 rounded-md text-[var(--text-muted)] group-hover:text-[var(--text-primary)] hover:bg-[var(--bg-surface)] transition shrink-0"
                          title="Copy Hex"
                        >
                          {isCopied ? (
                            <Check className="w-3.5 h-3.5 text-emerald-500" />
                          ) : (
                            <Copy className="w-3.5 h-3.5" />
                          )}
                        </button>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* 2. Visual Concepts */}
            {data.concepts.length > 0 && (
              <div className="space-y-2">
                <span className="text-[11px] font-bold tracking-wider uppercase text-[var(--text-secondary)] flex items-center gap-1.5">
                  <Layers className="w-3.5 h-3.5 text-blue-500" />
                  Visual Concepts & Classification
                </span>

                <div className="space-y-2">
                  {data.concepts.map((concept, idx) => {
                    const isPalette = concept.type === "palette";
                    const isPresentation = concept.type === "presentation";
                    const isArch = concept.type === "architecture";

                    const badgeClass = isPalette
                      ? "bg-rose-500/10 text-rose-500 border-rose-500/20"
                      : isPresentation
                      ? "bg-blue-500/10 text-blue-500 border-blue-500/20"
                      : isArch
                      ? "bg-emerald-500/10 text-emerald-500 border-emerald-500/20"
                      : "bg-amber-500/10 text-amber-500 border-amber-500/20";

                    const IconComponent = isPalette
                      ? Palette
                      : isPresentation
                      ? Layers
                      : isArch
                      ? Cpu
                      : Sparkles;

                    return (
                      <div
                        key={idx}
                        className="p-3 rounded-xl bg-[var(--bg-base)] border border-[var(--border-subtle)] space-y-1.5 transition hover:border-[#B45F3C]/40"
                      >
                        <div className="flex items-center gap-2">
                          <span className={`px-2 py-0.5 rounded-md text-[10px] font-bold uppercase tracking-wider border flex items-center gap-1 ${badgeClass}`}>
                            <IconComponent className="w-2.5 h-2.5" />
                            {isPalette ? "Brand System" : isPresentation ? "Slide Deck" : isArch ? "System Topology" : "Visual Concept"}
                          </span>
                          <span className="text-xs font-bold text-[var(--text-primary)] font-fraunces truncate">
                            {concept.title}
                          </span>
                        </div>

                        {concept.body && (
                          <div className="text-[11px] text-[var(--text-secondary)] leading-relaxed space-y-1">
                            {concept.body.split("\n").map((line, lidx) => (
                              <p key={lidx}>{line}</p>
                            ))}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* 3. VLM Scene Understanding (Ollama / Moondream) */}
            {data.vlmCaption && (
              <div className="p-3.5 rounded-xl bg-gradient-to-br from-[var(--bg-base)] to-purple-500/5 border border-purple-500/20 space-y-2">
                <div className="flex items-center gap-1.5 text-xs font-bold text-purple-400 font-fraunces">
                  <Sparkles className="w-3.5 h-3.5" />
                  <span>AI Scene Understanding</span>
                </div>
                <p className="text-xs text-[var(--text-primary)] leading-relaxed italic opacity-95">
                  &ldquo;{data.vlmCaption}&rdquo;
                </p>
              </div>
            )}

            {/* 4. Technical Specs & Document Profile */}
            <div className="space-y-2">
              <span className="text-[11px] font-bold tracking-wider uppercase text-[var(--text-secondary)] flex items-center gap-1.5">
                <Info className="w-3.5 h-3.5 text-neutral-400" />
                Technical Specifications
              </span>

              <div className="grid grid-cols-2 gap-2">
                {data.resolution && (
                  <div className="p-2.5 rounded-xl bg-[var(--bg-base)] border border-[var(--border-subtle)]">
                    <span className="text-[10px] uppercase font-semibold text-[var(--text-muted)] block">
                      Resolution
                    </span>
                    <span className="text-xs font-bold font-mono text-[var(--text-primary)] mt-0.5 block">
                      {data.resolution}
                    </span>
                  </div>
                )}

                {data.format && (
                  <div className="p-2.5 rounded-xl bg-[var(--bg-base)] border border-[var(--border-subtle)]">
                    <span className="text-[10px] uppercase font-semibold text-[var(--text-muted)] block">
                      Format & Encoding
                    </span>
                    <span className="text-xs font-bold font-mono text-[var(--text-primary)] mt-0.5 block">
                      {data.format}
                    </span>
                  </div>
                )}

                {data.colorMode && (
                  <div className="p-2.5 rounded-xl bg-[var(--bg-base)] border border-[var(--border-subtle)]">
                    <span className="text-[10px] uppercase font-semibold text-[var(--text-muted)] block">
                      Color Space
                    </span>
                    <span className="text-xs font-bold font-mono text-[var(--text-primary)] mt-0.5 block">
                      {data.colorMode}
                    </span>
                  </div>
                )}

                <div className="p-2.5 rounded-xl bg-[var(--bg-base)] border border-[var(--border-subtle)]">
                  <span className="text-[10px] uppercase font-semibold text-[var(--text-muted)] block">
                    OCR Engine
                  </span>
                  <span className="text-xs font-bold text-purple-400 mt-0.5 block truncate">
                    Apple Neural Engine
                  </span>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Tab 2: Extracted Text (OCR) */}
        {activeTab === "text" && (
          <div className="space-y-3 animate-in fade-in duration-150">
            {/* Search & Actions Bar */}
            <div className="flex items-center gap-2">
              <div className="relative flex-1">
                <Search className="w-3.5 h-3.5 absolute left-2.5 top-1/2 -translate-y-1/2 text-[var(--text-muted)]" />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Filter extracted words..."
                  className="w-full pl-8 pr-3 py-1.5 rounded-lg bg-[var(--bg-base)] border border-[var(--border-subtle)] text-xs text-[var(--text-primary)] placeholder-[var(--text-muted)] focus:outline-hidden focus:border-[#B45F3C]"
                />
              </div>

              <button
                onClick={handleCopyAllOcr}
                type="button"
                className="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-lg bg-[var(--bg-base)] border border-[var(--border-subtle)] hover:border-[#B45F3C] text-[var(--text-primary)] text-xs font-semibold transition shrink-0 shadow-xs"
                title="Copy all OCR lines"
              >
                {copiedAllOcr ? (
                  <>
                    <Check className="w-3.5 h-3.5 text-emerald-500" />
                    <span>Copied!</span>
                  </>
                ) : (
                  <>
                    <Copy className="w-3.5 h-3.5" />
                    <span>Copy All</span>
                  </>
                )}
              </button>
            </div>

            {/* List of text items */}
            {filteredOcrLines.length === 0 ? (
              <div className="p-6 text-center text-[var(--text-secondary)] space-y-1">
                <p className="font-semibold">No matching text found</p>
                <p className="text-[11px]">Try clearing the search query.</p>
              </div>
            ) : (
              <div className="space-y-1 rounded-xl bg-[var(--bg-base)] border border-[var(--border-subtle)] p-2 max-h-[60vh] overflow-y-auto">
                {filteredOcrLines.map((line, idx) => {
                  const isHeading =
                    line.length < 60 &&
                    (line.includes("SYSTEM") ||
                      line.includes("structure") ||
                      line.includes("personality") ||
                      line.match(/^[0-9]+(\s*[-–]\s*)?[A-Z\s]+$/));

                  const isHex = line.match(/^#[0-9a-fA-F]{6}$/);

                  return (
                    <div
                      key={idx}
                      className={`group flex items-start justify-between gap-2 px-2.5 py-1.5 rounded-lg hover:bg-[var(--bg-surface)] transition text-xs select-text ${
                        isHeading ? "font-bold text-[var(--text-primary)] bg-[var(--bg-surface)]/60" : "text-[var(--text-primary)] font-mono text-[11px]"
                      }`}
                    >
                      <div className="flex items-center gap-2 min-w-0">
                        <span className="text-[10px] font-mono text-[var(--text-muted)] select-none w-5 text-right shrink-0">
                          {idx + 1}
                        </span>
                        <span className="break-all">{line}</span>
                      </div>

                      {isHex && (
                        <div
                          className="w-3.5 h-3.5 rounded-full shrink-0 border border-black/10 mt-0.5"
                          style={{ backgroundColor: line }}
                        />
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        )}

        {/* Tab 3: Raw Output */}
        {activeTab === "raw" && (
          <div className="space-y-2 animate-in fade-in duration-150">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-bold uppercase tracking-wider text-[var(--text-secondary)]">
                Raw Metadata Feed
              </span>
              <button
                onClick={handleCopyRaw}
                type="button"
                className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-[11px] font-medium bg-[var(--bg-base)] border border-[var(--border-subtle)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:border-[#B45F3C] transition"
              >
                {copiedRaw ? <Check className="w-3 h-3 text-emerald-500" /> : <Copy className="w-3 h-3" />}
                <span>{copiedRaw ? "Copied" : "Copy Raw"}</span>
              </button>
            </div>

            <div className="p-3 rounded-xl bg-[#0d1117] text-[#c9d1d9] font-mono text-[11px] leading-relaxed overflow-x-auto max-h-[62vh] select-text">
              <pre className="whitespace-pre-wrap">{rawMetadata}</pre>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
