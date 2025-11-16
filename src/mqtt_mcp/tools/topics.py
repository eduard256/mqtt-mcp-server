"""MQTT topic discovery tool."""

import asyncio
import json
import sys
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

from ..mqtt_client import MQTTClient
from ..cache import update_cache, get_cache


class TopicsParams(BaseModel):
    """Parameters for topics tool."""
    scan_timeout: int = Field(default=10, ge=1, le=60, description="How long to scan for topics")
    keywords: Optional[List[str]] = Field(default=None, description="Keywords to filter topics (OR logic)")
    limit: int = Field(default=50, ge=1, le=200, description="Maximum results to return")
    offset: int = Field(default=0, ge=0, description="Pagination offset")


async def topics(params: TopicsParams) -> Dict[str, Any]:
    """
    Discover and search MQTT topics.

    Args:
        params: Discovery parameters

    Returns:
        Dict with paginated topics list and metadata
    """
    mqtt = MQTTClient()
    discovered_topics: Dict[str, str] = {}

    def matches_keywords(topic: str) -> bool:
        """Check if topic matches any keyword (OR logic)."""
        if not params.keywords:
            return True
        return any(keyword.lower() in topic.lower() for keyword in params.keywords)

    try:
        sys.stderr.write(f"Scanning for topics (timeout: {params.scan_timeout}s)\n")
        if params.keywords:
            sys.stderr.write(f"Keywords filter: {', '.join(params.keywords)}\n")

        async with await mqtt.create_client(timeout=params.scan_timeout) as client:
            # Subscribe to all topics
            await client.subscribe("#")
            sys.stderr.write("Discovering MQTT topics...\n")

            # Collect topics
            async def collect_topics():
                async for message in client.messages:
                    topic = str(message.topic)

                    # Decode payload
                    try:
                        payload = message.payload.decode('utf-8')
                    except (UnicodeDecodeError, AttributeError):
                        payload = str(message.payload)

                    # Store topic and payload
                    discovered_topics[topic] = payload

                    # Progress feedback
                    if len(discovered_topics) % 100 == 0:
                        sys.stderr.write(f"Discovered {len(discovered_topics)} topics...\n")

            # Scan for specified duration
            try:
                await asyncio.wait_for(collect_topics(), timeout=params.scan_timeout)
            except asyncio.TimeoutError:
                pass  # Normal timeout

        # Update global cache
        update_cache(discovered_topics)

        # Get all topics (discovered + cached)
        all_cache = get_cache()
        all_topics = sorted(set(list(discovered_topics.keys()) + list(all_cache.keys())))

        # Apply keyword filter
        if params.keywords:
            filtered_topics = [t for t in all_topics if matches_keywords(t)]
        else:
            filtered_topics = all_topics

        total = len(filtered_topics)

        # Apply pagination
        start_idx = params.offset
        end_idx = min(start_idx + params.limit, total)
        paginated_topics = filtered_topics[start_idx:end_idx]

        # Build hierarchical grouping
        grouped_topics = {}
        for topic in paginated_topics:
            parts = topic.split('/')
            if parts[0] not in grouped_topics:
                grouped_topics[parts[0]] = []
            grouped_topics[parts[0]].append(topic)

        sys.stderr.write(f"Found {total} topics, showing {len(paginated_topics)}\n")

        return {
            "topics": paginated_topics,
            "grouped": grouped_topics,
            "total": total,
            "showing": f"{start_idx}-{end_idx}",
            "has_more": end_idx < total,
            "scan_duration": float(params.scan_timeout)
        }

    except Exception as e:
        error_msg = f"Topic discovery failed: {str(e)}"
        sys.stderr.write(f"Error: {error_msg}\n")
        raise RuntimeError(error_msg)