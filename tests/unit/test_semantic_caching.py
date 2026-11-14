"""
Tests for semantic similarity caching.

This module tests the semantic cache functionality including embedding-based
lookups and hybrid exact + semantic matching.
"""
import pytest
import numpy as np
import sys
sys.path.insert(0, '../../tinytroupe/')
sys.path.insert(0, '../../')
sys.path.insert(0, '..')

from tinytroupe.caching import SemanticCache, create_text_representation


class TestSemanticCache:
    """Test semantic cache functionality."""

    def test_create_text_representation(self, setup):
        """Test text representation creation."""
        text = create_text_representation("my_function", 1, 2, x=3, y=4)

        assert "my_function" in text
        assert "1" in text
        assert "2" in text
        assert "x=3" in text or "x = 3" in text
        assert "y=4" in text or "y = 4" in text

    def test_semantic_cache_initialization(self, setup):
        """Test semantic cache initialization."""
        cache = SemanticCache(similarity_threshold=0.9)

        assert cache.similarity_threshold == 0.9
        assert cache.semantic_hits == 0
        assert cache.semantic_misses == 0

    def test_add_entry_without_embedding_function(self, setup):
        """Test adding entry without embedding function (should not crash)."""
        cache = SemanticCache()

        # Should not raise error
        cache.add_entry("hash1", 0, "test text")

        # Should have no embeddings
        assert len(cache._embeddings) == 0

    def test_add_entry_with_embedding_function(self, setup):
        """Test adding entry with embedding function."""
        def mock_embedding(text):
            # Simple mock: return hash as embedding
            return np.random.rand(384)

        cache = SemanticCache(embedding_function=mock_embedding)
        cache.add_entry("hash1", 0, "test text 1")

        assert len(cache._embeddings) == 1
        assert "hash1" in cache._embeddings

    def test_find_similar_exact_threshold(self, setup):
        """Test finding similar entries."""
        def mock_embedding(text):
            # Return same embedding for similar text
            if "hello" in text:
                return np.array([1.0, 0.0, 0.0])
            else:
                return np.array([0.0, 1.0, 0.0])

        cache = SemanticCache(
            similarity_threshold=0.9,
            embedding_function=mock_embedding
        )

        # Add entries
        cache.add_entry("hash1", 0, "hello world")
        cache.add_entry("hash2", 1, "goodbye world")

        # Find similar (should match hash1)
        result = cache.find_similar("query_hash", "hello there")

        # Should find hash1 as similar
        assert result is not None
        assert result[0] == "hash1"
        assert result[1] == 0  # cache index

    def test_find_similar_no_match(self, setup):
        """Test finding similar when no match exists."""
        def mock_embedding(text):
            # Different embeddings for different text
            if "hello" in text:
                return np.array([1.0, 0.0, 0.0])
            else:
                return np.array([0.0, 1.0, 0.0])

        cache = SemanticCache(
            similarity_threshold=0.99,  # Very high threshold
            embedding_function=mock_embedding
        )

        cache.add_entry("hash1", 0, "hello world")

        # Query with different text
        result = cache.find_similar("query_hash", "goodbye world")

        # Should not find match (similarity too low)
        assert result is None

    def test_remove_entry(self, setup):
        """Test removing entry."""
        def mock_embedding(text):
            return np.random.rand(384)

        cache = SemanticCache(embedding_function=mock_embedding)

        cache.add_entry("hash1", 0, "test 1")
        cache.add_entry("hash2", 1, "test 2")

        assert len(cache._embeddings) == 2

        cache.remove_entry("hash1")

        assert len(cache._embeddings) == 1
        assert "hash1" not in cache._embeddings

    def test_clear_cache(self, setup):
        """Test clearing cache."""
        def mock_embedding(text):
            return np.random.rand(384)

        cache = SemanticCache(embedding_function=mock_embedding)

        cache.add_entry("hash1", 0, "test 1")
        cache.add_entry("hash2", 1, "test 2")

        assert len(cache._embeddings) == 2

        cache.clear()

        assert len(cache._embeddings) == 0
        assert len(cache._hash_to_index) == 0

    def test_get_metrics(self, setup):
        """Test metrics collection."""
        cache = SemanticCache()

        cache.semantic_hits = 5
        cache.semantic_misses = 3

        metrics = cache.get_metrics()

        assert metrics['semantic_hits'] == 5
        assert metrics['semantic_misses'] == 3
        assert metrics['semantic_hit_rate'] == 5 / 8

    def test_eviction_on_size_limit(self, setup):
        """Test that cache evicts when size limit is reached."""
        def mock_embedding(text):
            return np.random.rand(384)

        cache = SemanticCache(
            embedding_function=mock_embedding,
            max_semantic_entries=5
        )

        # Add more than limit
        for i in range(10):
            cache.add_entry(f"hash{i}", i, f"text {i}")

        # Should not exceed limit
        assert len(cache._embeddings) <= 5

    def test_cosine_similarity(self, setup):
        """Test cosine similarity calculation."""
        cache = SemanticCache()

        vec1 = np.array([1.0, 0.0, 0.0])
        vec2 = np.array([1.0, 0.0, 0.0])

        similarity = cache._cosine_similarity(vec1, vec2)

        # Same vectors should have similarity 1.0
        assert abs(similarity - 1.0) < 0.001

    def test_embedding_normalization(self, setup):
        """Test that embeddings are normalized."""
        def mock_embedding(text):
            return np.array([3.0, 4.0, 0.0])  # Not normalized

        cache = SemanticCache(embedding_function=mock_embedding)

        embedding = cache._get_embedding("test")

        # Should be normalized (length = 1)
        norm = np.linalg.norm(embedding)
        assert abs(norm - 1.0) < 0.001


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
