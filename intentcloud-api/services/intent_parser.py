"""
Phase 3: Intent-Aware Query Understanding
Parses natural language queries using a local Ollama model.
Outputs structured intent: topics, keywords, filters.
"""

import logging
import json
import re
import requests
from typing import Dict, List

logger = logging.getLogger(__name__)

# Ollama configuration
OLLAMA_BASE_URL = "http://localhost:11434"
MODEL_NAME = "llama3.2:1b"
DEFAULT_TEMPERATURE = 0.1

VALID_INTENT_TYPES = {"find", "compare", "summarize", "list"}

STOP_WORDS = {
    "the", "a", "an", "is", "are", "be", "was", "were", "where", "what",
    "how", "can", "find", "show", "me", "my", "all", "any", "for", "and",
    "or", "in", "on", "at", "to", "of", "about", "with", "from", "this",
    "that", "these", "those", "please", "document", "documents", "doc",
    "file", "files", "report", "reports", "material", "notes", "guide",
    "guides", "paper", "papers", "compare", "summarize", "list",
}

# Boilerplate the small model sometimes copies from the prompt/schema.
PLACEHOLDER_PATTERNS = (
    r"keyword\d*",
    r"find\|compare\|summarize\|list",
    r"the main topic",
    r"subject the user is looking for",
    r"string,\s*brief",
    r"0\.5-1\.0",
    r"true\|false",
)


def parse_intent_with_phi3(query: str) -> Dict:
    """Parse natural language query intent via Ollama."""
    try:
        logger.info("[Intent] Parsing: %s", query)

        response = call_ollama(query)
        intent = parse_ollama_response(response, query)

        logger.info("[Intent] Parsed: %s", intent)
        return intent

    except Exception as exc:
        logger.error("[Intent] Parsing failed: %s", exc)
        return get_fallback_intent(query)


def build_intent_prompt(query: str) -> str:
    """Build a few-shot prompt with concrete examples (no schema placeholders)."""
    return f"""Extract search intent from the user query. Reply with JSON only.

Example 1
Query: Find documents about Kafka performance optimization
JSON: {{"topic":"Kafka performance optimization","keywords":["Kafka","performance","optimization"],"intent_type":"find","has_time_constraint":false,"confidence":0.9}}

Example 2
Query: Compare BM25 and dense retrieval approaches
JSON: {{"topic":"BM25 vs dense retrieval","keywords":["BM25","dense","retrieval"],"intent_type":"compare","has_time_constraint":false,"confidence":0.9}}

Example 3
Query: Where is the IntentCloud three-layer architecture design document?
JSON: {{"topic":"IntentCloud three-layer architecture","keywords":["IntentCloud","architecture","design"],"intent_type":"find","has_time_constraint":false,"confidence":0.9}}

Now parse this query.
Query: {query}
JSON:"""


def call_ollama(query: str) -> str:
    """Call Ollama with JSON mode and a low temperature for stable output."""
    prompt = build_intent_prompt(query)

    try:
        logger.info("[Ollama] Calling %s...", MODEL_NAME)

        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={
                "model": MODEL_NAME,
                "prompt": prompt,
                "stream": False,
                "format": "json",
                "temperature": DEFAULT_TEMPERATURE,
                "top_p": 0.9,
                "num_predict": 180,
            },
            timeout=30,
        )

        if response.status_code != 200:
            logger.error("[Ollama] HTTP %s: %s", response.status_code, response.text)
            raise RuntimeError(f"Ollama API error: {response.status_code}")

        response_text = response.json().get("response", "").strip()
        logger.info("[Ollama] Response: %s...", response_text[:120])
        return response_text

    except requests.exceptions.ConnectionError as exc:
        logger.error("[Ollama] Connection failed. Is Ollama running on localhost:11434?")
        raise RuntimeError("Ollama not available. Start with: ollama serve") from exc


def parse_ollama_response(response: str, original_query: str) -> Dict:
    """Parse and sanitize Ollama JSON, repairing template junk when needed."""
    try:
        json_start = response.find("{")
        json_end = response.rfind("}") + 1

        if json_start == -1 or json_end == 0:
            logger.warning("[Intent] No JSON found in response, using fallback")
            return get_fallback_intent(original_query)

        parsed = json.loads(response[json_start:json_end])

        intent = {
            "topic": str(parsed.get("topic", "")).strip()[:100],
            "keywords": _normalize_keywords(parsed.get("keywords", [])),
            "intent_type": str(parsed.get("intent_type", "find")).strip().lower(),
            "has_time_constraint": bool(parsed.get("has_time_constraint", False)),
            "confidence": float(parsed.get("confidence", 0.75)),
        }

        intent["confidence"] = max(0.0, min(1.0, intent["confidence"]))

        if intent["intent_type"] not in VALID_INTENT_TYPES:
            intent["intent_type"] = infer_intent_type(original_query)

        return sanitize_intent(intent, original_query, source="llm")

    except json.JSONDecodeError as exc:
        logger.warning("[Intent] JSON parse error: %s", exc)
        return get_fallback_intent(original_query)
    except Exception as exc:
        logger.warning("[Intent] Parse error: %s", exc)
        return get_fallback_intent(original_query)


def sanitize_intent(intent: Dict, query: str, source: str = "llm") -> Dict:
    """Reject prompt boilerplate and derive a usable topic/keywords set."""
    fallback = get_fallback_intent(query)
    repaired = dict(intent)

    if not repaired["keywords"] or _looks_like_placeholder(repaired["keywords"]):
        repaired["keywords"] = fallback["keywords"]

    if not repaired["topic"] or _looks_like_placeholder(repaired["topic"]):
        repaired["topic"] = derive_topic_from_keywords(repaired["keywords"], query)
        repaired["confidence"] = min(repaired.get("confidence", 0.7), 0.65)
        logger.warning("[Intent] Repaired invalid topic from keywords/query")

    if _topic_is_query_echo(repaired["topic"], query):
        repaired["topic"] = derive_topic_from_keywords(repaired["keywords"], query)

    inferred_type = infer_intent_type(query)
    if inferred_type != "find":
        repaired["intent_type"] = inferred_type

    if source == "llm" and repaired["topic"] == fallback["topic"]:
        repaired["confidence"] = min(repaired.get("confidence", 0.7), 0.6)

    return repaired


def _normalize_keywords(raw_keywords) -> List[str]:
    if not isinstance(raw_keywords, list):
        return []

    cleaned = []
    for keyword in raw_keywords:
        value = str(keyword).strip()
        if not value or _looks_like_placeholder(value):
            continue
        if value.lower() not in STOP_WORDS:
            cleaned.append(value)

    # Preserve order while deduplicating
    return list(dict.fromkeys(cleaned))[:5]


def _looks_like_placeholder(text) -> bool:
    if isinstance(text, list):
        return any(_looks_like_placeholder(item) for item in text)

    normalized = str(text).strip().lower()
    if not normalized:
        return True

    for pattern in PLACEHOLDER_PATTERNS:
        if re.search(pattern, normalized):
            return True

    return normalized in {"json", "query", "example", "string"}


def _topic_is_query_echo(topic: str, query: str) -> bool:
    return topic.strip().lower() == query.strip().lower()


def infer_intent_type(query: str) -> str:
    lowered = query.lower()
    if lowered.startswith("compare ") or " vs " in lowered or " versus " in lowered:
        return "compare"
    if lowered.startswith("summarize") or lowered.startswith("summary"):
        return "summarize"
    if lowered.startswith("list ") or "all " in lowered:
        return "list"
    return "find"


def extract_keywords(query: str) -> List[str]:
    tokens = re.findall(r"[A-Za-z0-9][A-Za-z0-9/+._-]*", query)
    keywords = []
    for token in tokens:
        lower = token.lower()
        if lower in STOP_WORDS or len(lower) <= 2:
            continue
        keywords.append(token)
    return list(dict.fromkeys(keywords))[:5]


def derive_topic_from_keywords(keywords: List[str], query: str) -> str:
    if keywords:
        return " ".join(keywords[:4])[:100]
    return query.strip()[:100]


def get_fallback_intent(query: str) -> Dict:
    """Keyword-based fallback when Ollama is unavailable or returns unusable JSON."""
    keywords = extract_keywords(query)
    topic = derive_topic_from_keywords(keywords, query)

    return {
        "topic": topic,
        "keywords": keywords,
        "intent_type": infer_intent_type(query),
        "has_time_constraint": bool(re.search(r"\b(19|20)\d{2}\b|q[1-4]\b", query.lower())),
        "confidence": 0.5,
    }


def check_ollama_available() -> bool:
    """Check if Ollama is running and the configured model is available."""
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        if response.status_code != 200:
            return False

        model_names = [m.get("name", "") for m in response.json().get("models", [])]
        logger.info("[Ollama] Available models: %s", model_names)
        configured = MODEL_NAME.split(":")[0]
        return any(
            name == MODEL_NAME or name.startswith(f"{configured}:")
            for name in model_names
        )
    except Exception as exc:
        logger.warning("[Ollama] Availability check failed: %s", exc)
        return False
