"""
Phase 3: Intent-Aware Query Understanding
Parses natural language queries using Phi-3 Mini via Ollama.
Outputs structured intent: topics, keywords, filters.
"""

import logging
import json
import requests
from typing import Dict, Optional

logger = logging.getLogger(__name__)

# Ollama configuration
OLLAMA_BASE_URL = "http://localhost:11434"
MODEL_NAME = "phi:3"  # or phi3:mini - Q4_K_M quantized version
DEFAULT_TEMPERATURE = 0.7


def parse_intent_with_phi3(query: str) -> Dict:
    """
    Parse natural language query intent using Phi-3 Mini via Ollama.
    
    Structured intent output:
    {
        "topic": "what the user is looking for",
        "keywords": ["keyword1", "keyword2"],
        "filters": {...},
        "confidence": 0.0-1.0
    }
    
    Args:
        query: Natural language search query
    
    Returns:
        Parsed intent dict
    """
    try:
        logger.info(f"[Intent] Parsing: {query}")
        
        # Build prompt for Phi-3
        prompt = build_intent_prompt(query)
        
        # Call Ollama
        response = call_ollama_phi3(prompt)
        
        # Parse response
        intent = parse_ollama_response(response, query)
        
        logger.info(f"[Intent] Parsed: {intent}")
        return intent
    
    except Exception as e:
        logger.error(f"[Intent] Parsing failed: {str(e)}")
        # Return fallback intent
        return get_fallback_intent(query)


def build_intent_prompt(query: str) -> str:
    """
    Build prompt for Phi-3 to parse query intent.
    
    Args:
        query: User's natural language query
    
    Returns:
        Formatted prompt
    """
    return f"""You are an intelligent search assistant. Parse the user's query intent and output ONLY valid JSON (no markdown, no explanation).

User query: "{query}"

Output a JSON object with exactly these fields:
{{
  "topic": "the main topic or subject the user is looking for (string, brief)",
  "keywords": ["keyword1", "keyword2", "keyword3"],
  "intent_type": "find|compare|summarize|list",
  "has_time_constraint": true|false,
  "confidence": 0.5-1.0
}}

Respond ONLY with the JSON object, no other text."""


def call_ollama_phi3(prompt: str) -> str:
    """
    Call Ollama API with Phi-3 Mini model.
    
    Args:
        prompt: Input prompt
    
    Returns:
        Model response text
    """
    try:
        logger.info(f"[Ollama] Calling Phi-3 Mini...")
        
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={
                "model": MODEL_NAME,
                "prompt": prompt,
                "stream": False,
                "temperature": DEFAULT_TEMPERATURE,
                "top_p": 0.9,
                "num_predict": 200
            },
            timeout=30
        )
        
        if response.status_code != 200:
            logger.error(f"[Ollama] HTTP {response.status_code}: {response.text}")
            raise Exception(f"Ollama API error: {response.status_code}")
        
        result = response.json()
        response_text = result.get("response", "").strip()
        
        logger.info(f"[Ollama] Response: {response_text[:100]}...")
        return response_text
    
    except requests.exceptions.ConnectionError:
        logger.error("[Ollama] Connection failed. Is Ollama running on localhost:11434?")
        raise Exception("Ollama not available. Start with: ollama serve")
    except Exception as e:
        logger.error(f"[Ollama] Error: {str(e)}")
        raise


def parse_ollama_response(response: str, original_query: str) -> Dict:
    """
    Parse Ollama's JSON response into intent structure.
    
    Args:
        response: Raw text response from Ollama
        original_query: Original user query
    
    Returns:
        Parsed intent dict
    """
    try:
        # Try to extract JSON from response (may contain explanation text)
        json_start = response.find("{")
        json_end = response.rfind("}") + 1
        
        if json_start == -1 or json_end == 0:
            logger.warning("[Intent] No JSON found in response, using fallback")
            return get_fallback_intent(original_query)
        
        json_str = response[json_start:json_end]
        parsed = json.loads(json_str)
        
        # Validate and normalize
        intent = {
            "topic": str(parsed.get("topic", "")).strip()[:100],
            "keywords": list(set(
                [k.strip() for k in parsed.get("keywords", []) if k.strip()]
            ))[:5],  # Limit to 5 keywords
            "intent_type": parsed.get("intent_type", "find"),
            "has_time_constraint": bool(parsed.get("has_time_constraint", False)),
            "confidence": float(parsed.get("confidence", 0.7))
        }
        
        # Validate confidence
        intent["confidence"] = max(0.0, min(1.0, intent["confidence"]))
        
        return intent
    
    except json.JSONDecodeError as e:
        logger.warning(f"[Intent] JSON parse error: {str(e)}")
        return get_fallback_intent(original_query)
    except Exception as e:
        logger.warning(f"[Intent] Parse error: {str(e)}")
        return get_fallback_intent(original_query)


def get_fallback_intent(query: str) -> Dict:
    """
    Generate fallback intent using simple keyword extraction.
    Used when Ollama/Phi-3 is unavailable.
    
    Args:
        query: User query
    
    Returns:
        Fallback intent dict
    """
    # Simple keyword extraction (split on spaces, remove stop words)
    stop_words = {"the", "a", "an", "is", "are", "be", "where", "what", "how", "can", "find"}
    keywords = [w for w in query.lower().split() if w not in stop_words and len(w) > 2]
    
    return {
        "topic": query[:100],
        "keywords": keywords[:5],
        "intent_type": "find",
        "has_time_constraint": False,
        "confidence": 0.5  # Lower confidence for fallback
    }


def check_ollama_available() -> bool:
    """
    Check if Ollama is running and Phi-3 model is available.
    
    Returns:
        True if available, False otherwise
    """
    try:
        response = requests.get(
            f"{OLLAMA_BASE_URL}/api/tags",
            timeout=5
        )
        if response.status_code == 200:
            models = response.json().get("models", [])
            model_names = [m.get("name", "") for m in models]
            logger.info(f"[Ollama] Available models: {model_names}")
            return any("phi" in name for name in model_names)
        return False
    except Exception as e:
        logger.warning(f"[Ollama] Availability check failed: {str(e)}")
        return False
