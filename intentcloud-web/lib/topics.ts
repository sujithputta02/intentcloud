/**
 * Shared Topic Definitions and Classification Utilities for IntentCloud Web
 */

export interface TopicDefinition {
  title: string;
  color: string;
  iconColor: string;
  keywords: string[];
}

export const TOPIC_DEFINITIONS: TopicDefinition[] = [
  {
    title: "Kafka & Microservices",
    color: "bg-amber-500/10 border-amber-500/20 text-amber-400",
    iconColor: "text-amber-400",
    keywords: ["kafka", "microservice", "stream", "event", "broker", "mesh", "circuit"],
  },
  {
    title: "Thesis Drafts",
    color: "bg-blue-500/10 border-blue-500/20 text-blue-400",
    iconColor: "text-blue-400",
    keywords: ["thesis", "draft", "paper", "research", "dissertation", "review"],
  },
  {
    title: "ML Models & AI",
    color: "bg-purple-500/10 border-purple-500/20 text-purple-400",
    iconColor: "text-purple-400",
    keywords: ["machine learning", "deep learning", "neural", "transformer", "model", "ai", "embedding", "llm"],
  },
  {
    title: "Business Reports",
    color: "bg-emerald-500/10 border-emerald-500/20 text-emerald-400",
    iconColor: "text-emerald-400",
    keywords: ["report", "summary", "quarter", "q1", "q2", "q3", "q4", "market", "finance", "business"],
  },
  {
    title: "Cloud & DevOps",
    color: "bg-cyan-500/10 border-cyan-500/20 text-cyan-400",
    iconColor: "text-cyan-400",
    keywords: ["kubernetes", "docker", "ci/cd", "pipeline", "devops", "cloud", "deployment", "cluster"],
  },
];

export function classifyFile(name: string, topicTags: string[] = []): string {
  const lowerName = name.toLowerCase();
  const lowerTags = topicTags.map((t) => t.toLowerCase());

  for (const topic of TOPIC_DEFINITIONS) {
    if (topic.keywords.some((kw) => lowerName.includes(kw) || lowerTags.some((t) => t.includes(kw)))) {
      return topic.title;
    }
  }
  return "General Documents";
}

export function countFilesByTopic(
  files: Array<{ name: string; topic_tags?: string[] }>
): Record<string, number> {
  const counts: Record<string, number> = {};
  for (const topic of TOPIC_DEFINITIONS) {
    counts[topic.title] = 0;
  }
  counts["General Documents"] = 0;

  for (const file of files) {
    const topic = classifyFile(file.name, file.topic_tags);
    counts[topic] = (counts[topic] || 0) + 1;
  }
  return counts;
}
