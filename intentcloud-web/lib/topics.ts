/**
 * Shared Topic Definitions, Dynamic Categories, and Classification Utilities for IntentCloud Web
 */

export interface TopicDefinition {
  title: string;
  color: string;
  iconColor: string;
  keywords: string[];
}

export const CODE_EXTENSIONS = new Set([
  "py", "js", "ts", "tsx", "jsx", "html", "htm", "css", "scss", "sass",
  "json", "java", "c", "cpp", "cc", "cxx", "h", "hpp", "cs", "go",
  "rs", "php", "rb", "swift", "kt", "kts", "sql", "sh", "bash", "zsh",
  "yaml", "yml", "xml", "toml", "ini", "env", "r", "lua"
]);

export const IMAGE_EXTENSIONS = new Set([
  "png", "jpg", "jpeg", "webp", "svg", "gif", "bmp", "tiff", "tif", "ico"
]);

export const DOCUMENT_EXTENSIONS = new Set([
  "pdf", "docx", "doc", "txt", "md", "markdown", "rtf", "csv", "tsv", "log", "tex"
]);

export function getFileCategory(name: string, ext?: string): "pdf" | "docx" | "txt" | "code" | "photo" | "document" {
  const extension = (ext || name.split(".").pop() || "").toLowerCase().replace(".", "");
  if (IMAGE_EXTENSIONS.has(extension)) return "photo";
  if (CODE_EXTENSIONS.has(extension)) return "code";
  if (extension === "pdf") return "pdf";
  if (extension === "docx" || extension === "doc") return "docx";
  if (extension === "txt") return "txt";
  return "document";
}

export const BASE_TOPIC_DEFINITIONS: TopicDefinition[] = [
  {
    title: "Kafka & Microservices",
    color: "bg-amber-500/10 border-amber-500/20 text-amber-400",
    iconColor: "text-amber-500",
    keywords: ["kafka", "microservice", "stream", "event", "broker", "mesh", "circuit"],
  },
  {
    title: "Thesis Drafts",
    color: "bg-blue-500/10 border-blue-500/20 text-blue-400",
    iconColor: "text-blue-500",
    keywords: ["thesis", "draft", "paper", "research", "dissertation", "review"],
  },
  {
    title: "ML Models & AI",
    color: "bg-purple-500/10 border-purple-500/20 text-purple-400",
    iconColor: "text-purple-500",
    keywords: ["machine learning", "deep learning", "neural", "transformer", "model", "ai", "embedding", "llm"],
  },
  {
    title: "Business Reports",
    color: "bg-emerald-500/10 border-emerald-500/20 text-emerald-400",
    iconColor: "text-emerald-500",
    keywords: ["report", "summary", "quarter", "q1", "q2", "q3", "q4", "market", "finance", "business"],
  },
  {
    title: "Cloud & DevOps",
    color: "bg-cyan-500/10 border-cyan-500/20 text-cyan-400",
    iconColor: "text-cyan-500",
    keywords: ["kubernetes", "docker", "ci/cd", "pipeline", "devops", "cloud", "deployment", "cluster"],
  },
];

// Fallback dynamic styling palette for newly discovered topics
const DYNAMIC_PALETTE = [
  { color: "bg-rose-500/10 border-rose-500/20 text-rose-400", iconColor: "text-rose-500" },
  { color: "bg-indigo-500/10 border-indigo-500/20 text-indigo-400", iconColor: "text-indigo-500" },
  { color: "bg-teal-500/10 border-teal-500/20 text-teal-400", iconColor: "text-teal-500" },
  { color: "bg-fuchsia-500/10 border-fuchsia-500/20 text-fuchsia-400", iconColor: "text-fuchsia-500" },
  { color: "bg-orange-500/10 border-orange-500/20 text-orange-400", iconColor: "text-orange-500" },
  { color: "bg-lime-500/10 border-lime-500/20 text-lime-400", iconColor: "text-lime-500" },
];

export function classifyFile(name: string, topicTags: string[] = [], ext?: string): string {
  const lowerName = name.toLowerCase();
  const lowerTags = topicTags.map((t) => t.toLowerCase());
  const category = getFileCategory(name, ext);

  // 1. Check if matches pre-configured domain topics
  for (const topic of BASE_TOPIC_DEFINITIONS) {
    if (topic.keywords.some((kw) => lowerName.includes(kw) || lowerTags.some((t) => t.includes(kw)))) {
      return topic.title;
    }
  }

  // 2. Check if topic_tags from backend model/Ollama contain meaningful custom labels
  for (const tag of topicTags) {
    const cleanTag = tag.trim();
    if (
      cleanTag.length > 2 &&
      !["document", "file", "text", "test", "txt", "pdf"].includes(cleanTag.toLowerCase())
    ) {
      // Return capitalized tag
      return cleanTag.charAt(0).toUpperCase() + cleanTag.slice(1);
    }
  }

  // 3. Fallback to format/media categories
  if (category === "code") {
    return "Source Code & Scripts";
  }
  if (category === "photo") {
    return "Photos & Media";
  }

  // 4. Filename semantic clues
  if (lowerName.includes("invoice") || lowerName.includes("receipt") || lowerName.includes("bill")) {
    return "Invoices & Billing";
  }
  if (lowerName.includes("resume") || lowerName.includes("cv")) {
    return "Resumes & Portfolios";
  }
  if (lowerName.includes("spec") || lowerName.includes("architecture") || lowerName.includes("design")) {
    return "System Architecture";
  }

  return "General Documents";
}

/**
 * Returns dynamic topic definitions, automatically adding any new categories
 * present in the uploaded files.
 */
export function getAllTopicDefinitions(
  files: Array<{ name: string; topic_tags?: string[]; extension?: string }>
): TopicDefinition[] {
  const customTopicsMap = new Map<string, TopicDefinition>();

  // Start with default base definitions
  for (const base of BASE_TOPIC_DEFINITIONS) {
    customTopicsMap.set(base.title, base);
  }

  // Discover topics from actual uploaded files
  let paletteIdx = 0;
  for (const file of files) {
    const topicTitle = classifyFile(file.name, file.topic_tags, file.extension);
    if (!customTopicsMap.has(topicTitle)) {
      const palette = DYNAMIC_PALETTE[paletteIdx % DYNAMIC_PALETTE.length];
      paletteIdx++;

      customTopicsMap.set(topicTitle, {
        title: topicTitle,
        color: palette.color,
        iconColor: palette.iconColor,
        keywords: [topicTitle.toLowerCase()],
      });
    }
  }

  return Array.from(customTopicsMap.values());
}

export function countFilesByTopic(
  files: Array<{ name: string; topic_tags?: string[]; extension?: string }>
): Record<string, number> {
  const counts: Record<string, number> = {};

  for (const file of files) {
    const topic = classifyFile(file.name, file.topic_tags, file.extension);
    counts[topic] = (counts[topic] || 0) + 1;
  }
  return counts;
}

export const TOPIC_DEFINITIONS = BASE_TOPIC_DEFINITIONS;
