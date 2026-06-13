"""
Memory optimization utilities for TinyTroupe agents.
"""

from typing import List, Dict, Any
import time


def optimize_episodic_memory(episodes: List[Dict[str, Any]], max_episodes: int = 100) -> List[Dict[str, Any]]:
    """
    Optimizes episodic memory by keeping only the most recent and important episodes.

    Args:
        episodes: List of episodic memories to optimize
        max_episodes: Maximum number of episodes to retain

    Returns:
        Optimized list of episodes
    """
    if len(episodes) <= max_episodes:
        return episodes

    # Keep most recent episodes (simple FIFO strategy)
    # More sophisticated strategies could involve importance scoring
    return episodes[-max_episodes:]


def consolidate_semantic_memory(semantic_entries: List[Dict[str, Any]],
                                deduplicate: bool = True) -> List[Dict[str, Any]]:
    """
    Consolidates semantic memory by removing duplicates and merging related entries.

    Args:
        semantic_entries: List of semantic memory entries
        deduplicate: Whether to remove exact duplicates

    Returns:
        Consolidated list of semantic entries
    """
    if deduplicate:
        # Remove exact duplicates based on content hash
        seen = set()
        unique_entries = []
        for entry in semantic_entries:
            content_str = str(entry)
            content_hash = hash(content_str)
            if content_hash not in seen:
                seen.add(content_hash)
                unique_entries.append(entry)
        return unique_entries

    return semantic_entries


def calculate_memory_stats(memory: Any) -> Dict[str, Any]:
    """
    Calculates statistics about memory usage.

    Args:
        memory: Memory object to analyze

    Returns:
        Dictionary with memory statistics
    """
    stats = {
        "timestamp": time.time(),
        "episodic_count": 0,
        "semantic_count": 0,
        "total_size_estimate": 0
    }

    if hasattr(memory, "episodic_memory") and memory.episodic_memory:
        if hasattr(memory.episodic_memory, "_episodes"):
            stats["episodic_count"] = len(memory.episodic_memory._episodes)

    if hasattr(memory, "semantic_memory") and memory.semantic_memory:
        if hasattr(memory.semantic_memory, "_facts"):
            stats["semantic_count"] = len(memory.semantic_memory._facts)

    # Rough size estimation (each entry ~1KB on average)
    stats["total_size_estimate"] = (stats["episodic_count"] + stats["semantic_count"]) * 1024

    return stats