"""Simple cache module for MQTT topic values."""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Tuple, Any


# Global cache dictionary
CACHE: Dict[str, Dict[str, Any]] = {}

# Cache file path
CACHE_FILE = Path.home() / ".mqtt-mcp-cache.json"


def load_cache() -> Dict[str, Dict[str, Any]]:
    """Load cache from file. Returns empty dict if file missing."""
    global CACHE

    if CACHE_FILE.exists():
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                CACHE = json.load(f)
                sys.stderr.write(f"Loaded cache with {len(CACHE)} topics\n")
        except Exception as e:
            sys.stderr.write(f"Warning: Could not load cache: {e}\n")
            CACHE = {}
    else:
        CACHE = {}

    return CACHE


def save_cache() -> None:
    """Save cache to file with proper error handling."""
    try:
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(CACHE, f, indent=2, ensure_ascii=False)
        sys.stderr.write(f"Saved cache with {len(CACHE)} topics\n")
    except Exception as e:
        sys.stderr.write(f"Warning: Could not save cache: {e}\n")


def get_cached_value(topic: str) -> Optional[Tuple[str, float]]:
    """
    Get cached value for topic.
    Returns tuple of (value, age_seconds) or None if not cached.
    """
    if topic not in CACHE:
        return None

    cached = CACHE[topic]

    # Calculate age if timestamp exists
    if "timestamp" in cached:
        try:
            cached_time = datetime.fromisoformat(cached["timestamp"].replace('Z', '+00:00'))
            now = datetime.utcnow()
            # Make both timezone-aware or both naive
            if cached_time.tzinfo is not None:
                from datetime import timezone
                now = now.replace(tzinfo=timezone.utc)
            age = (now - cached_time).total_seconds()
            age = max(0.0, age)
        except Exception:
            age = 0.0
    else:
        age = 0.0

    return cached.get("value", ""), age


def set_cached_value(topic: str, value: str) -> None:
    """Set cached value for topic with current timestamp."""
    CACHE[topic] = {
        "value": value,
        "timestamp": datetime.utcnow().isoformat() + 'Z'
    }


def update_cache(topics_dict: Dict[str, str]) -> None:
    """Update cache with multiple topic-value pairs."""
    timestamp = datetime.utcnow().isoformat() + 'Z'
    for topic, value in topics_dict.items():
        CACHE[topic] = {
            "value": value,
            "timestamp": timestamp
        }


def get_cache() -> Dict[str, Dict[str, Any]]:
    """Get the entire cache dictionary."""
    return CACHE