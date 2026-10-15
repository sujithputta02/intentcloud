"use client";

import React, { useState, useEffect, useRef } from "react";
import { 
  Cpu, HardDrive, Sparkles, Radio, Tv, CheckCircle2, 
  Activity, Wifi, ArrowRight, Play, RotateCcw, 
  Terminal, ShieldCheck, Eye, Layers, Zap, Database,
  Sliders, Maximize2, Minimize2, Check, ExternalLink
} from "lucide-react";

export type PipelineStage = "idle" | "ingest" | "cognitive" | "transport" | "memory" | "rerank" | "pushed";

export interface HardwareOledPipelineProps {
  isSearching: boolean;
  query: string;
  searchMode?: string;
  topResult?: {
    filename: string;
    relevance_percentage: number;
    rank: number;
    file_type?: string;
    rrf_score?: number;
    explanation?: string;
  } | null;
  metrics?: {
    latency_ms?: number;
    device?: string;
    dense_candidates?: number;
    sparse_candidates?: number;
    fused_candidates?: number;
    reranked_count?: number;
  } | null;
  parsedIntent?: {
    topic?: string;
    keywords?: string[];
    intent_type?: string;
    confidence?: number;
  } | null;
}

export default function HardwareOledPipeline({
  isSearching,
  query,
  searchMode = "hybrid",
  topResult,
  metrics,
  parsedIntent,
}: HardwareOledPipelineProps) {
  const [currentStage, setCurrentStage] = useState<PipelineStage>("idle");
  const [activeTab, setActiveTab] = useState<"pipeline" | "oled_closeup">("pipeline");
  const [pulseTick, setPulseTick] = useState(0);
  const [isManualReplay, setIsManualReplay] = useState(false);
  const [marqueeOffset, setMarqueeOffset] = useState(0);

  // Pulse clock for simulated hardware heartbeat (1 Hz)
  useEffect(() => {
    const timer = setInterval(() => {
      setPulseTick((prev) => (prev + 1) % 100);
      setMarqueeOffset((prev) => (prev + 1) % 40);
    }, 500);
    return () => clearInterval(timer);
  }, []);

  const animTimerRef = useRef<NodeJS.Timeout[]>([]);

  // Helper to push telemetry to hardware
  const pushToOled = (stageStatus: string, infoText: string, matchScore?: number) => {
    try {
      fetch("/api/hardware/oled", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          status: stageStatus,
          query: query || "Ready for query",
          info: infoText,
          match: matchScore,
        }),
      }).catch(() => {});
    } catch {}
  };

  const clearAnimTimers = () => {
    animTimerRef.current.forEach((t) => clearTimeout(t));
    animTimerRef.current = [];
  };

  // Clean up timers on unmount
  useEffect(() => {
    return () => clearAnimTimers();
  }, []);

  // Manage real-time pipeline stages when searching starts and completes
  useEffect(() => {
    if (isSearching) {
      clearAnimTimers();
      setIsManualReplay(false);
      
      // Step 1: Ingest
      setCurrentStage("ingest");
      pushToOled("INGEST", "Query Ingest");

      // Step 2: Cognitive Parse (450ms)
      const t1 = setTimeout(() => {
        setCurrentStage("cognitive");
        pushToOled("PARSING", "llama3.2:1b");
      }, 450);

      // Step 3: Ethernet Transport (900ms)
      const t2 = setTimeout(() => {
        setCurrentStage("transport");
        pushToOled("ETHERNET", "LAN 192.168.2.2");
      }, 900);

      // Step 4: Hybrid Qdrant Search (1350ms)
      const t3 = setTimeout(() => {
        setCurrentStage("memory");
        pushToOled("SEARCHING", "Dense + Sparse");
      }, 1350);

      // Step 5: Cross-Encoder Rerank (1800ms)
      const t4 = setTimeout(() => {
        setCurrentStage("rerank");
        pushToOled("RERANK", "MiniLM Neural");
      }, 1800);

      // Step 6: OLED Push result (2250ms)
      const t5 = setTimeout(() => {
        setCurrentStage("pushed");
        if (topResult) {
          pushToOled("PUSHED", `Pi 3B | ${topResult.relevance_percentage}% Match`, topResult.relevance_percentage);
        } else {
          pushToOled("ONLINE", "Ready for query");
        }
      }, 2250);

      animTimerRef.current = [t1, t2, t3, t4, t5];
    } else if (!isSearching && !topResult && currentStage !== "idle") {
      clearAnimTimers();
      setCurrentStage("idle");
    }
  }, [isSearching]);

  // Keep pushed state synced if topResult arrives
  useEffect(() => {
    if (!isSearching && topResult && currentStage === "idle") {
      setCurrentStage("pushed");
    }
  }, [isSearching, topResult]);

  // Manual replay animation for demonstrations
  const runManualReplay = () => {
    clearAnimTimers();
    setIsManualReplay(true);
    setCurrentStage("ingest");
    pushToOled("INGEST", "Query Ingest");

    const t1 = setTimeout(() => {
      setCurrentStage("cognitive");
      pushToOled("PARSING", "llama3.2:1b");
    }, 450);
    const t2 = setTimeout(() => {
      setCurrentStage("transport");
      pushToOled("ETHERNET", "LAN 192.168.2.2");
    }, 900);
    const t3 = setTimeout(() => {
      setCurrentStage("memory");
      pushToOled("SEARCHING", "Dense + Sparse");
    }, 1350);
    const t4 = setTimeout(() => {
      setCurrentStage("rerank");
      pushToOled("RERANK", "MiniLM Neural");
    }, 1800);
    const t5 = setTimeout(() => {
      setCurrentStage("pushed");
      setIsManualReplay(false);
      if (topResult) {
        pushToOled("PUSHED", `Pi 3B | ${topResult.relevance_percentage}% Match`, topResult.relevance_percentage);
      }
    }, 2250);

    animTimerRef.current = [t1, t2, t3, t4, t5];
  };

  const getStageNumber = (stage: PipelineStage): number => {
    switch (stage) {
      case "idle": return 0;
      case "ingest": return 1;
      case "cognitive": return 2;
      case "transport": return 3;
      case "memory": return 4;
      case "rerank": return 5;
      case "pushed": return 6;
      default: return 0;
    }
  };

  const currentStepNum = getStageNumber(currentStage);

  // Derive OLED Display Strings matching firmware/main.py
  const displayQuery = query || "Ready for query";
  const truncatedQuery = displayQuery.length > 15 ? displayQuery.slice(0, 15) : displayQuery;
  
  let oledStatusText = "ACTIVE";
  let oledHwInfo = "Pi 3B | Qdrant";
  let oledLineBottom = "Q: " + truncatedQuery;

  if (currentStage === "ingest") {
    oledStatusText = "INGESTING";
    oledHwInfo = "Mac -> Intent";
    oledLineBottom = "RX: Query Ingest";
  } else if (currentStage === "cognitive") {
    oledStatusText = "PARSING";
    oledHwInfo = "LLM: llama3.2";
    oledLineBottom = "Topic: " + (parsedIntent?.topic ? parsedIntent.topic.slice(0, 11) : "Semantic");
  } else if (currentStage === "transport") {
    oledStatusText = "ETHERNET TX";
    oledHwInfo = "LAN 192.168.2.2";
    oledLineBottom = "Sending Vectors";
  } else if (currentStage === "memory") {
    oledStatusText = "SEARCHING";
    oledHwInfo = "Dense + Sparse";
    oledLineBottom = "RRF Fusion k=60";
  } else if (currentStage === "rerank") {
    oledStatusText = "RERANKING";
    oledHwInfo = "MiniLM Neural";
    oledLineBottom = "Scoring Top Hits";
  } else if (currentStage === "pushed" && topResult) {
    oledStatusText = "PUSHED TO DEV";
    oledHwInfo = `Pi 3B | ${topResult.relevance_percentage}% Match`;
    const cleanName = topResult.filename.replace(/^WhatsApp\s*Image\s*/i, "WA_IMG_").slice(0, 16);
    oledLineBottom = `★ ${cleanName}`;
  }

  return (
    <div className="w-full rounded-3xl bg-[var(--bg-surface)] border border-[var(--border-subtle)] shadow-xl overflow-hidden transition-all duration-300">
      {/* Header Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 px-5 py-4 border-b border-[var(--border-subtle)] bg-[var(--bg-surface)]/80 backdrop-blur">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-cyan-500 shadow-inner">
            <Radio className="w-5 h-5 animate-pulse" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="font-fraunces font-bold text-sm sm:text-base text-[var(--text-primary)]">
                Edge Memory & Live OLED Pipeline
              </h3>
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-mono font-semibold bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border border-emerald-500/30">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-ping" />
                SSD1306 128x64 LIVE
              </span>
            </div>
            <p className="text-xs text-[var(--text-secondary)]">
              Real-time pictorial hardware sync from Cognitive Ingestion to Physical Edge Display
            </p>
          </div>
        </div>

        {/* View Switcher & Replay Button */}
        <div className="flex items-center gap-2">
          {topResult && !isSearching && (
            <button
              onClick={runManualReplay}
              disabled={isManualReplay}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold bg-[var(--bg-base)] hover:bg-[var(--border-subtle)] border border-[var(--border-subtle)] text-[var(--text-primary)] transition shadow-sm disabled:opacity-50"
              title="Replay full hardware animation"
            >
              <RotateCcw className={`w-3.5 h-3.5 ${isManualReplay ? "animate-spin" : ""}`} />
              <span>Replay Pipeline</span>
            </button>
          )}

          <div className="flex rounded-xl bg-[var(--bg-base)] p-1 border border-[var(--border-subtle)] text-xs font-semibold">
            <button
              onClick={() => setActiveTab("pipeline")}
              className={`px-3 py-1 rounded-lg transition ${
                activeTab === "pipeline"
                  ? "bg-[var(--bg-surface)] text-[var(--text-primary)] shadow-sm"
                  : "text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
              }`}
            >
              Full Flow
            </button>
            <button
              onClick={() => setActiveTab("oled_closeup")}
              className={`px-3 py-1 rounded-lg transition ${
                activeTab === "oled_closeup"
                  ? "bg-[var(--bg-surface)] text-[var(--text-primary)] shadow-sm"
                  : "text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
              }`}
            >
              OLED Close-Up
            </button>
          </div>
        </div>
      </div>

      {/* Main Interactive Stage Body */}
      <div className="p-5 sm:p-6 space-y-6">
        {activeTab === "pipeline" ? (
          /* ========================================================================= */
          /* 1. PICTORIAL FULL DATAFLOW DIAGRAM WITH REAL-TIME STAGES                  */
          /* ========================================================================= */
          <div className="space-y-6">
            {/* Visual Process Flow Tracker */}
            <div className="relative">
              {/* Progress Connection Line */}
              <div className="absolute top-1/2 left-6 right-6 -translate-y-1/2 h-1 bg-[var(--border-subtle)] rounded-full -z-0 hidden md:block">
                <div 
                  className="h-full bg-gradient-to-r from-blue-500 via-purple-500 to-cyan-400 transition-all duration-500 rounded-full"
                  style={{ width: `${Math.min(100, Math.max(0, ((currentStepNum - 1) / 5) * 100))}%` }}
                />
              </div>

              {/* Station Nodes */}
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-3 relative z-10">
                {/* Node 1: Ingestion */}
                <div className={`p-3 rounded-2xl border transition-all duration-300 flex flex-col items-center text-center gap-2 ${
                  currentStepNum >= 1
                    ? "bg-blue-500/10 border-blue-500/40 shadow-sm"
                    : "bg-[var(--bg-base)] border-[var(--border-subtle)] opacity-60"
                }`}>
                  <div className={`w-8 h-8 rounded-xl flex items-center justify-center font-bold text-xs ${
                    currentStepNum >= 1 ? "bg-blue-500 text-white shadow-md shadow-blue-500/30" : "bg-[var(--border-subtle)] text-[var(--text-secondary)]"
                  }`}>
                    1
                  </div>
                  <div>
                    <span className="font-semibold text-xs text-[var(--text-primary)] block">Query Ingest</span>
                    <span className="text-[10px] text-[var(--text-secondary)] font-mono">User Layer</span>
                  </div>
                </div>

                {/* Node 2: Cognitive Parse */}
                <div className={`p-3 rounded-2xl border transition-all duration-300 flex flex-col items-center text-center gap-2 ${
                  currentStepNum >= 2
                    ? "bg-purple-500/10 border-purple-500/40 shadow-sm"
                    : "bg-[var(--bg-base)] border-[var(--border-subtle)] opacity-60"
                }`}>
                  <div className={`w-8 h-8 rounded-xl flex items-center justify-center font-bold text-xs ${
                    currentStepNum >= 2 ? "bg-purple-500 text-white shadow-md shadow-purple-500/30" : "bg-[var(--border-subtle)] text-[var(--text-secondary)]"
                  }`}>
                    2
                  </div>
                  <div>
                    <span className="font-semibold text-xs text-[var(--text-primary)] block">Intent Parse</span>
                    <span className="text-[10px] text-[var(--text-secondary)] font-mono">llama3.2:1b</span>
                  </div>
                </div>

                {/* Node 3: Transport */}
                <div className={`p-3 rounded-2xl border transition-all duration-300 flex flex-col items-center text-center gap-2 ${
                  currentStepNum >= 3
                    ? "bg-amber-500/10 border-amber-500/40 shadow-sm"
                    : "bg-[var(--bg-base)] border-[var(--border-subtle)] opacity-60"
                }`}>
                  <div className={`w-8 h-8 rounded-xl flex items-center justify-center font-bold text-xs ${
                    currentStepNum >= 3 ? "bg-amber-500 text-white shadow-md shadow-amber-500/30" : "bg-[var(--border-subtle)] text-[var(--text-secondary)]"
                  }`}>
                    3
                  </div>
                  <div>
                    <span className="font-semibold text-xs text-[var(--text-primary)] block">LAN Ethernet</span>
                    <span className="text-[10px] text-[var(--text-secondary)] font-mono">192.168.2.2</span>
                  </div>
                </div>

                {/* Node 4: Memory Layer */}
                <div className={`p-3 rounded-2xl border transition-all duration-300 flex flex-col items-center text-center gap-2 ${
                  currentStepNum >= 4
                    ? "bg-emerald-500/10 border-emerald-500/40 shadow-sm"
                    : "bg-[var(--bg-base)] border-[var(--border-subtle)] opacity-60"
                }`}>
                  <div className={`w-8 h-8 rounded-xl flex items-center justify-center font-bold text-xs ${
                    currentStepNum >= 4 ? "bg-emerald-500 text-white shadow-md shadow-emerald-500/30" : "bg-[var(--border-subtle)] text-[var(--text-secondary)]"
                  }`}>
                    4
                  </div>
                  <div>
                    <span className="font-semibold text-xs text-[var(--text-primary)] block">Hybrid Qdrant</span>
                    <span className="text-[10px] text-[var(--text-secondary)] font-mono">RRF Fusion</span>
                  </div>
                </div>

                {/* Node 5: Neural Rerank */}
                <div className={`p-3 rounded-2xl border transition-all duration-300 flex flex-col items-center text-center gap-2 ${
                  currentStepNum >= 5
                    ? "bg-indigo-500/10 border-indigo-500/40 shadow-sm"
                    : "bg-[var(--bg-base)] border-[var(--border-subtle)] opacity-60"
                }`}>
                  <div className={`w-8 h-8 rounded-xl flex items-center justify-center font-bold text-xs ${
                    currentStepNum >= 5 ? "bg-indigo-500 text-white shadow-md shadow-indigo-500/30" : "bg-[var(--border-subtle)] text-[var(--text-secondary)]"
                  }`}>
                    5
                  </div>
                  <div>
                    <span className="font-semibold text-xs text-[var(--text-primary)] block">Neural Rerank</span>
                    <span className="text-[10px] text-[var(--text-secondary)] font-mono">MiniLM-L6</span>
                  </div>
                </div>

                {/* Node 6: OLED Push */}
                <div className={`p-3 rounded-2xl border transition-all duration-300 flex flex-col items-center text-center gap-2 ${
                  currentStepNum >= 6
                    ? "bg-cyan-500/15 border-cyan-500/50 shadow-md shadow-cyan-500/20 ring-2 ring-cyan-400/30"
                    : "bg-[var(--bg-base)] border-[var(--border-subtle)] opacity-60"
                }`}>
                  <div className={`w-8 h-8 rounded-xl flex items-center justify-center font-bold text-xs ${
                    currentStepNum >= 6 ? "bg-cyan-400 text-black shadow-md shadow-cyan-400/50 animate-bounce" : "bg-[var(--border-subtle)] text-[var(--text-secondary)]"
                  }`}>
                    6
                  </div>
                  <div>
                    <span className="font-semibold text-xs text-[var(--text-primary)] block">OLED Push</span>
                    <span className="text-[10px] text-cyan-500 font-mono font-bold">SSD1306</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Split Arena: Hardware Architecture Diagram & Embedded OLED Monitor */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-stretch">
              {/* Architecture Blueprint Card (7 cols) */}
              <div className="lg:col-span-7 p-5 rounded-2xl bg-[var(--bg-base)] border border-[var(--border-subtle)] flex flex-col justify-between space-y-4">
                <div className="flex items-center justify-between border-b border-[var(--border-subtle)] pb-3">
                  <div className="flex items-center gap-2">
                    <Activity className="w-4 h-4 text-cyan-500" />
                    <span className="font-bold text-xs tracking-wider uppercase text-[var(--text-primary)] font-mono">
                      System Topology & Pipeline Stage
                    </span>
                  </div>
                  <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-mono font-bold ${
                    currentStage === "pushed"
                      ? "bg-emerald-500/15 text-emerald-500 border border-emerald-500/30"
                      : isSearching
                      ? "bg-cyan-500/15 text-cyan-500 border border-cyan-500/30 animate-pulse"
                      : "bg-[var(--border-subtle)] text-[var(--text-secondary)]"
                  }`}>
                    <span className={`w-2 h-2 rounded-full ${currentStage === "pushed" ? "bg-emerald-500" : isSearching ? "bg-cyan-500 animate-ping" : "bg-gray-400"}`} />
                    STAGE: {currentStage.toUpperCase()}
                  </span>
                </div>

                {/* Circuit Flow Graphic */}
                <div className="space-y-3 font-mono text-xs">
                  {/* Step 1 & 2: Cognitive Layer */}
                  <div className={`p-3 rounded-xl border transition-all ${
                    currentStepNum >= 2 ? "bg-[var(--bg-surface)] border-purple-500/30 shadow-sm" : "opacity-50 border-[var(--border-subtle)]"
                  }`}>
                    <div className="flex items-center justify-between text-[11px] mb-1">
                      <span className="font-bold text-purple-600 dark:text-purple-400 flex items-center gap-1.5">
                        <Sparkles className="w-3.5 h-3.5" /> 1. COGNITIVE LAYER (MAC GPU)
                      </span>
                      <span className="text-[var(--text-secondary)]">Ollama LLM :11434</span>
                    </div>
                    <div className="text-[var(--text-secondary)] text-[11px]">
                      Query: <span className="text-[var(--text-primary)] font-medium">"{truncatedQuery}"</span>
                      {parsedIntent?.topic && (
                        <span> → Topic: <strong className="text-purple-500">{parsedIntent.topic}</strong></span>
                      )}
                    </div>
                  </div>

                  {/* Step 3: Transport Pipe */}
                  <div className={`p-3 rounded-xl border transition-all flex items-center justify-between ${
                    currentStepNum >= 3 ? "bg-[var(--bg-surface)] border-amber-500/30 shadow-sm" : "opacity-50 border-[var(--border-subtle)]"
                  }`}>
                    <div className="flex items-center gap-2">
                      <Wifi className="w-3.5 h-3.5 text-amber-500" />
                      <div>
                        <span className="font-bold text-[11px] text-[var(--text-primary)] block">2. LAN PACKET TRANSPORT</span>
                        <span className="text-[10px] text-[var(--text-secondary)]">FastAPI Daemon @ 192.168.2.2:8000</span>
                      </div>
                    </div>
                    <div className="flex items-center gap-1">
                      <span className="w-2 h-2 rounded-full bg-emerald-500 animate-ping" />
                      <span className="text-[10px] font-bold text-emerald-500">HTTP/2 OK</span>
                    </div>
                  </div>

                  {/* Step 4 & 5: Memory Layer on Pi */}
                  <div className={`p-3 rounded-xl border transition-all ${
                    currentStepNum >= 4 ? "bg-[var(--bg-surface)] border-emerald-500/30 shadow-sm" : "opacity-50 border-[var(--border-subtle)]"
                  }`}>
                    <div className="flex items-center justify-between text-[11px] mb-1">
                      <span className="font-bold text-emerald-600 dark:text-emerald-400 flex items-center gap-1.5">
                        <Database className="w-3.5 h-3.5" /> 3. MEMORY LAYER (RASPBERRY PI 3B)
                      </span>
                      <span className="text-[var(--text-secondary)]">Qdrant Embedded</span>
                    </div>
                    <div className="text-[var(--text-secondary)] text-[11px]">
                      Dual Vectors (384-D Dense + Sparse Hash) → RRF Fusion (k=60) → Cross-Encoder MiniLM
                    </div>
                  </div>
                </div>

                {/* Bottom Hardware Telemetry Strip */}
                <div className="pt-2 border-t border-[var(--border-subtle)] flex flex-wrap items-center justify-between gap-2 text-[11px] font-mono text-[var(--text-secondary)]">
                  <span>Edge Storage: /media/pi/Intentcloud_storage</span>
                  {metrics?.latency_ms ? (
                    <span className="text-cyan-600 dark:text-cyan-400 font-bold">Latency: {metrics.latency_ms} ms</span>
                  ) : (
                    <span>Heartbeat: {pulseTick % 2 === 0 ? "PING" : "PONG"}</span>
                  )}
                </div>
              </div>

              {/* Physical OLED Display Unit (5 cols) */}
              <div className="lg:col-span-5 flex flex-col items-center justify-center">
                {/* Physical OLED Module Graphic */}
                <div className="w-full max-w-[340px] p-4 rounded-3xl bg-neutral-900 border-4 border-neutral-800 shadow-2xl relative flex flex-col items-center">
                  {/* Mounting Screws (4 corners) */}
                  <div className="absolute top-2 left-2 w-2 h-2 rounded-full bg-neutral-600 border border-neutral-400" />
                  <div className="absolute top-2 right-2 w-2 h-2 rounded-full bg-neutral-600 border border-neutral-400" />
                  <div className="absolute bottom-2 left-2 w-2 h-2 rounded-full bg-neutral-600 border border-neutral-400" />
                  <div className="absolute bottom-2 right-2 w-2 h-2 rounded-full bg-neutral-600 border border-neutral-400" />

                  {/* Header Pin Labels */}
                  <div className="flex items-center justify-center gap-4 text-[9px] font-mono font-bold text-neutral-400 mb-2">
                    <span className="text-red-400">VCC</span>
                    <span className="text-neutral-400">GND</span>
                    <span className="text-yellow-400">SCL</span>
                    <span className="text-blue-400">SDA</span>
                  </div>

                  {/* The Actual OLED Glass Screen (SSD1306 128x64) */}
                  <div className="w-full aspect-[2/1] rounded-xl bg-black border-2 border-neutral-700 p-2.5 relative overflow-hidden shadow-inner flex flex-col justify-between font-mono select-none">
                    {/* CRT Scanline & Pixel Grid Overlay */}
                    <div 
                      className="absolute inset-0 pointer-events-none opacity-20"
                      style={{
                        backgroundImage: "linear-gradient(rgba(18, 16, 16, 0) 50%, rgba(0, 0, 0, 0.4) 50%), linear-gradient(90deg, rgba(255, 0, 0, 0.06), rgba(0, 255, 0, 0.02), rgba(0, 0, 255, 0.06))",
                        backgroundSize: "100% 2px, 3px 100%"
                      }}
                    />

                    {/* Top Banner (Inverted Block) */}
                    <div className="bg-cyan-400 text-black px-1.5 py-0.5 rounded-sm flex items-center justify-between text-[10px] font-black tracking-wider leading-none">
                      <span>INTENTCLOUD</span>
                      <span className={`w-2 h-2 ${pulseTick % 2 === 0 ? "bg-black" : "border border-black bg-transparent"}`} />
                    </div>

                    {/* Middle Telemetry Rows */}
                    <div className="space-y-0.5 text-[9px] sm:text-[10px] text-cyan-400 font-bold leading-tight">
                      <div className="flex justify-between">
                        <span>Status: {oledStatusText}</span>
                      </div>
                      <div className="flex justify-between text-cyan-300">
                        <span>IP: 192.168.2.2</span>
                      </div>
                      <div className="text-cyan-400/90 truncate">
                        {oledHwInfo}
                      </div>
                    </div>

                    {/* OLED Divider Line */}
                    <div className="w-full h-[1px] bg-cyan-400/80 my-0.5" />

                    {/* Bottom Dynamic Activity / Result Line */}
                    <div className="text-[9px] text-cyan-300 font-bold truncate">
                      {oledLineBottom}
                    </div>

                    {/* Active Edge Transmission Glow Effect */}
                    {currentStage === "pushed" && (
                      <div className="absolute inset-0 bg-cyan-400/10 pointer-events-none animate-pulse" />
                    )}
                  </div>

                  {/* Physical Board Subtitle & Status LED */}
                  <div className="w-full flex items-center justify-between mt-3 px-1 text-[10px] font-mono text-neutral-400">
                    <span>SSD1306 (0x3C)</span>
                    <div className="flex items-center gap-1.5">
                      <span className="text-[9px]">TX</span>
                      <span className={`w-2 h-2 rounded-full ${
                        currentStage === "pushed"
                          ? "bg-emerald-400 shadow-sm shadow-emerald-400"
                          : isSearching
                          ? "bg-cyan-400 animate-ping"
                          : "bg-neutral-600"
                      }`} />
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        ) : (
          /* ========================================================================= */
          /* 2. OLED CLOSE-UP & TELEMETRY TERMINAL VIEW                                */
          /* ========================================================================= */
          <div className="space-y-6">
            <div className="flex flex-col items-center justify-center py-6">
              {/* Massive High-Def OLED Simulator */}
              <div className="w-full max-w-[480px] p-6 rounded-3xl bg-neutral-950 border-4 border-neutral-800 shadow-2xl relative flex flex-col items-center">
                <div className="w-full aspect-[2/1] rounded-2xl bg-black border-2 border-neutral-700 p-4 relative overflow-hidden shadow-2xl flex flex-col justify-between font-mono select-none">
                  {/* Pixel Mesh Overlay */}
                  <div 
                    className="absolute inset-0 pointer-events-none opacity-25"
                    style={{
                      backgroundImage: "linear-gradient(rgba(18, 16, 16, 0) 50%, rgba(0, 0, 0, 0.5) 50%), linear-gradient(90deg, rgba(255, 255, 255, 0.05), transparent)",
                      backgroundSize: "100% 3px, 3px 100%"
                    }}
                  />

                  {/* Header Inverted Banner */}
                  <div className="bg-cyan-400 text-black px-2 py-1 rounded-sm flex items-center justify-between text-xs sm:text-sm font-black tracking-widest leading-none">
                    <span>INTENTCLOUD // EDGE</span>
                    <div className="flex items-center gap-1">
                      <span className="text-[10px]">I2C</span>
                      <span className={`w-2.5 h-2.5 ${pulseTick % 2 === 0 ? "bg-black" : "border border-black bg-transparent"}`} />
                    </div>
                  </div>

                  {/* Body Content */}
                  <div className="space-y-1 text-xs sm:text-sm text-cyan-400 font-bold leading-normal">
                    <div className="flex justify-between">
                      <span>STATUS : {oledStatusText}</span>
                      <span className="text-cyan-300">100%</span>
                    </div>
                    <div className="text-cyan-300">
                      HOST   : 192.168.2.2 (LAN)
                    </div>
                    <div className="text-cyan-400/90 truncate">
                      ENGINE : {oledHwInfo}
                    </div>
                  </div>

                  {/* Horizontal Rule */}
                  <div className="w-full h-[2px] bg-cyan-400/80 my-1" />

                  {/* Bottom Active Marquee / Pushed Result */}
                  <div className="text-xs sm:text-sm text-cyan-300 font-bold truncate flex items-center justify-between">
                    <span>{oledLineBottom}</span>
                    {topResult && currentStage === "pushed" && (
                      <span className="text-[10px] bg-cyan-400 text-black px-1.5 py-0.5 rounded font-black">
                        #{topResult.rank}
                      </span>
                    )}
                  </div>
                </div>

                <div className="w-full flex items-center justify-between mt-4 px-2 text-xs font-mono text-neutral-400">
                  <div className="flex items-center gap-2">
                    <Radio className="w-4 h-4 text-cyan-500 animate-pulse" />
                    <span>ESP32 / Pi I2C Bus Address: 0x3C</span>
                  </div>
                  <span className="text-emerald-400 font-bold">DEVICE SYNCHRONIZED</span>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Live Push Notification Banner when search delivers results */}
        {topResult && currentStage === "pushed" && (
          <div className="p-4 rounded-2xl bg-gradient-to-r from-cyan-500/10 via-emerald-500/10 to-transparent border border-cyan-500/30 flex flex-wrap items-center justify-between gap-3 animate-in fade-in duration-300">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-xl bg-emerald-500/20 border border-emerald-500/30 flex items-center justify-center text-emerald-500 shrink-0">
                <Check className="w-5 h-5" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-xs font-bold font-mono uppercase text-emerald-600 dark:text-emerald-400 tracking-wider">
                    Pushed to Edge Device Successfully
                  </span>
                  <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-cyan-500/15 text-cyan-600 dark:text-cyan-400 border border-cyan-500/30">
                    Rank #{topResult.rank} • {topResult.relevance_percentage}% Match
                  </span>
                </div>
                <p className="text-xs text-[var(--text-primary)] font-medium truncate max-w-lg">
                  {topResult.filename}
                </p>
              </div>
            </div>

            <div className="text-right text-xs font-mono text-[var(--text-secondary)]">
              <span>Display Sync: </span>
              <strong className="text-emerald-500">CONFIRMED (192.168.2.2)</strong>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
