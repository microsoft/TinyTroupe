"""
Semantic similarity caching for TinyTroupe.

This module provides embedding-based cache lookup alongside exact matching,
enabling fuzzy cache hits for semantically similar function calls.
"""
import numpy as np
from typing import Optional, List, Tuple, Dict, Any
import hashlib
import logging

logger = logging.getLogger("tinytroupe")


class SemanticCache:
    """
    Semantic cache using embeddings for similarity-based lookup.

    Enables fuzzy cache hits when exact match fails but semantically similar
    entry exists. Uses hybrid approach: exact match first, then semantic.
    """

    def __init__(
        self,
        similarity_threshold: float = 0.85,
        embedding_function: Optional[callable] = None,
        max_semantic_entries: int = 1000
    ):
        """
        Initialize semantic cache.

        Args:
            similarity_threshold: Minimum cosine similarity for cache hit (0.0-1.0)
            embedding_function: Function to generate embeddings from text
            max_semantic_entries: Maximum entries to track for semantic lookup
        """
        self.similarity_threshold = similarity_threshold
        self.embedding_function = embedding_function
        self.max_semantic_entries = max_semantic_entries

        # Maps hash -> embedding vector
        self._embeddings: Dict[str, np.ndarray] = {}

        # Maps hash -> cache index
        self._hash_to_index: Dict[str, int] = {}

        # Semantic cache statistics
        self.semantic_hits = 0
        self.semantic_misses = 0
        self.semantic_lookups = 0

    def set_embedding_function(self, func: callable):
        """
        Set the embedding function to use.

        Args:
            func: Callable that takes text and returns embedding vector
        """
        self.embedding_function = func

    def add_entry(self, event_hash: str, cache_index: int, text_representation: str):
        """
        Add an entry to the semantic cache.

        Args:
            event_hash: Hash of the event (cache key)
            cache_index: Index in the main cache
            text_representation: Text to generate embedding from
        """
        if not self.embedding_function:
            return  # Semantic caching disabled

        try:
            # Generate embedding
            embedding = self._get_embedding(text_representation)

            # Store mapping
            self._embeddings[event_hash] = embedding
            self._hash_to_index[event_hash] = cache_index

            # Manage size
            if len(self._embeddings) > self.max_semantic_entries:
                self._evict_oldest_entries()

        except Exception as e:
            logger.warning(f"Failed to add semantic cache entry: {e}")

    def find_similar(
        self,
        event_hash: str,
        text_representation: str
    ) -> Optional[Tuple[str, int, float]]:
        """
        Find semantically similar cache entry.

        Args:
            event_hash: Hash of the query event
            text_representation: Text representation of the query

        Returns:
            Tuple of (matching_hash, cache_index, similarity_score) or None
        """
        if not self.embedding_function or not self._embeddings:
            return None

        self.semantic_lookups += 1

        try:
            # Get query embedding
            query_embedding = self._get_embedding(text_representation)

            # Find most similar entry
            best_match = None
            best_similarity = self.similarity_threshold

            for cached_hash, cached_embedding in self._embeddings.items():
                similarity = self._cosine_similarity(query_embedding, cached_embedding)

                if similarity > best_similarity:
                    best_similarity = similarity
                    best_match = cached_hash

            if best_match:
                self.semantic_hits += 1
                cache_index = self._hash_to_index[best_match]
                logger.debug(f"Semantic cache hit: {event_hash[:16]}... -> {best_match[:16]}... "
                           f"(similarity: {best_similarity:.3f})")
                return (best_match, cache_index, best_similarity)
            else:
                self.semantic_misses += 1
                return None

        except Exception as e:
            logger.warning(f"Semantic cache lookup failed: {e}")
            self.semantic_misses += 1
            return None

    def remove_entry(self, event_hash: str):
        """
        Remove an entry from semantic cache.

        Args:
            event_hash: Hash to remove
        """
        if event_hash in self._embeddings:
            del self._embeddings[event_hash]
        if event_hash in self._hash_to_index:
            del self._hash_to_index[event_hash]

    def clear(self):
        """Clear all semantic cache entries."""
        self._embeddings.clear()
        self._hash_to_index.clear()

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get semantic cache metrics.

        Returns:
            Dictionary with statistics
        """
        total_lookups = self.semantic_hits + self.semantic_misses
        hit_rate = self.semantic_hits / total_lookups if total_lookups > 0 else 0.0

        return {
            'semantic_hits': self.semantic_hits,
            'semantic_misses': self.semantic_misses,
            'semantic_lookups': self.semantic_lookups,
            'semantic_hit_rate': hit_rate,
            'semantic_entries': len(self._embeddings),
            'similarity_threshold': self.similarity_threshold,
            'max_entries': self.max_semantic_entries
        }

    def _get_embedding(self, text: str) -> np.ndarray:
        """
        Get embedding vector for text.

        Args:
            text: Text to embed

        Returns:
            Embedding vector as numpy array
        """
        if not self.embedding_function:
            raise RuntimeError("Embedding function not set")

        embedding = self.embedding_function(text)

        # Convert to numpy array if needed
        if not isinstance(embedding, np.ndarray):
            embedding = np.array(embedding)

        # Normalize
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm

        return embedding

    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """
        Compute cosine similarity between two vectors.

        Args:
            vec1, vec2: Embedding vectors (assumed normalized)

        Returns:
            Cosine similarity (0.0 to 1.0)
        """
        return float(np.dot(vec1, vec2))

    def _evict_oldest_entries(self):
        """Evict oldest semantic cache entries to maintain size limit."""
        num_to_evict = len(self._embeddings) - self.max_semantic_entries

        if num_to_evict > 0:
            # Remove first N entries (FIFO)
            hashes_to_remove = list(self._embeddings.keys())[:num_to_evict]

            for hash_val in hashes_to_remove:
                self.remove_entry(hash_val)

            logger.debug(f"Evicted {num_to_evict} semantic cache entries")


def create_compact_text_representation(
    function_name: str,
    *args,
    template_ref: str = None,
    **kwargs,
) -> str:
    """
    Create a compact text representation for cache keys, using optional template reference
    to reduce redundancy when the same prompt template is repeated across many entries.

    Use template_ref when the call uses a well-known template (e.g. persona base);
    this reduces cache bloat from repeated full prompt text.
    """
    parts = [f"Function: {function_name}"]
    if template_ref:
        parts.append(f"TemplateRef: {template_ref}")
    if args:
        parts.append(f"Args: {len(args)} items")
    if kwargs:
        kw_items = sorted(kwargs.items())
        parts.append(f"Kwargs: {', '.join(f'{k}={repr(v)[:50]}' for k, v in kw_items)}")
    return " | ".join(parts)


def create_text_representation(function_name: str, *args, **kwargs) -> str:
    """
    Create text representation of a function call for embedding.

    Args:
        function_name: Name of the function
        *args: Positional arguments
        **kwargs: Keyword arguments

    Returns:
        Text representation suitable for embedding
    """
    parts = [f"Function: {function_name}"]

    # Add positional arguments
    if args:
        args_str = ", ".join(str(arg) for arg in args)
        parts.append(f"Args: {args_str}")

    # Add keyword arguments (sorted for consistency)
    if kwargs:
        kwargs_items = sorted(kwargs.items())
        kwargs_str = ", ".join(f"{k}={v}" for k, v in kwargs_items)
        parts.append(f"Kwargs: {kwargs_str}")

    return " | ".join(parts)


# Singleton instance (optional)
_default_semantic_cache: Optional[SemanticCache] = None


def get_default_semantic_cache() -> SemanticCache:
    """Get or create the default semantic cache instance."""
    global _default_semantic_cache

    if _default_semantic_cache is None:
        _default_semantic_cache = SemanticCache()

    return _default_semantic_cache


def reset_default_semantic_cache():
    """Reset the default semantic cache."""
    global _default_semantic_cache
    _default_semantic_cache = None
