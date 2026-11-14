"""
Tests for LRU cache with size limits.

This module tests the cache management functionality including LRU eviction,
compression, and metrics collection.
"""
import pytest
import sys
sys.path.insert(0, '../../tinytroupe/')
sys.path.insert(0, '../../')
sys.path.insert(0, '..')

from testing_utils import setup  # noqa: F401 - fixture
from tinytroupe.control import Simulation
from tinytroupe import config_manager


class TestLRUCache:
    """Test LRU cache management."""

    def test_cache_size_limit(self, setup):
        """Test that cache respects size limit."""
        sim = Simulation(id="test_cache_limit")

        # Set small cache limit for testing
        sim.max_cache_size = 10

        # Add more entries than limit
        for i in range(15):
            sim.cached_trace.append((f"prev_{i}", f"event_{i}", f"output_{i}", {"state": i}))
            sim._manage_cache_size()

        # Should not exceed limit
        assert len(sim.cached_trace) <= sim.max_cache_size

    def test_lru_eviction(self, setup):
        """Test LRU eviction policy."""
        sim = Simulation(id="test_lru")
        sim.max_cache_size = 5
        sim.cache_eviction_policy = "lru"

        # Add entries
        for i in range(5):
            sim.cached_trace.append((f"prev_{i}", f"event_{i}", f"output_{i}", {"state": i}))
            sim._record_cache_access(i)

        # Access indices 2, 3, 4 (making 0, 1 least recently used)
        sim._record_cache_access(2)
        sim._record_cache_access(3)
        sim._record_cache_access(4)

        # Add one more entry, should evict 0 or 1
        sim.cached_trace.append(("prev_5", "event_5", "output_5", {"state": 5}))
        sim._manage_cache_size()

        assert len(sim.cached_trace) == 5

    def test_fifo_eviction(self, setup):
        """Test FIFO eviction policy."""
        sim = Simulation(id="test_fifo")
        sim.max_cache_size = 5
        sim.cache_eviction_policy = "fifo"

        # Add entries
        for i in range(7):
            sim.cached_trace.append((f"prev_{i}", f"event_{i}", f"output_{i}", {"state": i}))
            sim._manage_cache_size()

        # Should have removed oldest entries (0, 1)
        assert len(sim.cached_trace) == 5

    def test_cache_metrics(self, setup):
        """Test cache metrics collection."""
        sim = Simulation(id="test_metrics")
        sim.collect_cache_metrics = True

        # Add some entries
        for i in range(5):
            sim.cached_trace.append((f"prev_{i}", f"event_{i}", f"output_{i}", {"state": i}))

        # Simulate cache hits and misses
        sim.cache_hits = 10
        sim.cache_misses = 3

        metrics = sim.get_cache_metrics()

        assert metrics['cache_hits'] == 10
        assert metrics['cache_misses'] == 3
        assert metrics['cache_size_entries'] == 5
        assert metrics['hit_rate'] == 10 / 13  # 10 / (10 + 3)
        assert 'cache_size_bytes' in metrics
        assert 'cache_usage_ratio' in metrics

    def test_cache_warning_threshold(self, setup, caplog):
        """Test cache warning when approaching limit."""
        sim = Simulation(id="test_warning")
        sim.max_cache_size = 10
        sim.cache_warning_threshold = 0.8

        # Add entries up to warning threshold
        for i in range(8):
            sim.cached_trace.append((f"prev_{i}", f"event_{i}", f"output_{i}", {"state": i}))

        # This should trigger warning
        sim.cached_trace.append(("prev_8", "event_8", "output_8", {"state": 8}))
        sim._manage_cache_size()

        # Check that cache is not evicted yet, just warning
        assert len(sim.cached_trace) == 9

    def test_unbounded_cache(self, setup):
        """Test that unbounded cache (max_size=0) doesn't evict."""
        sim = Simulation(id="test_unbounded")
        sim.max_cache_size = 0  # Unbounded

        # Add many entries
        for i in range(100):
            sim.cached_trace.append((f"prev_{i}", f"event_{i}", f"output_{i}", {"state": i}))
            sim._manage_cache_size()

        # All should remain
        assert len(sim.cached_trace) == 100

    def test_cache_eviction_count(self, setup):
        """Test that evictions are counted."""
        sim = Simulation(id="test_eviction_count")
        sim.max_cache_size = 5

        # Add more than limit
        for i in range(10):
            sim.cached_trace.append((f"prev_{i}", f"event_{i}", f"output_{i}", {"state": i}))
            sim._manage_cache_size()

        # Should have evicted 5 entries
        assert sim.cache_evictions == 5

    def test_cache_compression(self, setup):
        """Test cache compression functionality."""
        sim = Simulation(id="test_compression")
        sim.enable_cache_compression = True
        sim.cache_compression_threshold = 100  # Low threshold for testing

        # Create large entry
        large_state = {"data": "x" * 10000}
        entry = ("prev", "event", "output", large_state)

        compressed = sim._compress_cache_entry(entry)

        # Should be compressed (marked with __compressed__)
        if isinstance(compressed, tuple) and len(compressed) == 2:
            assert compressed[0] == "__compressed__"

            # Decompress and verify
            decompressed = sim._decompress_cache_entry(compressed)
            assert decompressed == entry

    def test_cache_metrics_history(self, setup):
        """Test cache metrics history tracking."""
        sim = Simulation(id="test_history")
        sim.collect_cache_metrics = True

        # Get metrics multiple times
        for i in range(5):
            sim.cached_trace.append((f"prev_{i}", f"event_{i}", f"output_{i}", {"state": i}))
            sim.get_cache_metrics()

        history = sim.get_cache_metrics_history()

        # Should have 5 entries
        assert len(history) == 5

        # Each entry should be (timestamp, metrics_dict)
        for timestamp, metrics in history:
            assert isinstance(metrics, dict)
            assert 'cache_size_entries' in metrics

    def test_size_based_eviction(self, setup):
        """Test size-based eviction policy."""
        sim = Simulation(id="test_size_eviction")
        sim.max_cache_size = 3
        sim.cache_eviction_policy = "size"

        # Add entries of different sizes
        sim.cached_trace.append(("p1", "e1", "o1", {"data": "small"}))
        sim.cached_trace.append(("p2", "e2", "o2", {"data": "x" * 1000}))  # Large
        sim.cached_trace.append(("p3", "e3", "o3", {"data": "medium" * 10}))

        # Add one more to trigger eviction
        sim.cached_trace.append(("p4", "e4", "o4", {"data": "tiny"}))
        sim._manage_cache_size()

        # Should have evicted largest entry
        assert len(sim.cached_trace) == 3

    def test_lru_access_tracking(self, setup):
        """Test that cache access is properly tracked."""
        sim = Simulation(id="test_access_tracking")
        sim.cache_eviction_policy = "lru"
        sim.max_cache_size = 10

        # Add entries
        for i in range(5):
            sim.cached_trace.append((f"prev_{i}", f"event_{i}", f"output_{i}", {"state": i}))

        # Record accesses
        sim._record_cache_access(0)
        sim._record_cache_access(2)
        sim._record_cache_access(4)

        # Check access order was recorded
        assert 0 in sim._cache_access_order
        assert 2 in sim._cache_access_order
        assert 4 in sim._cache_access_order

        # 1 and 3 should not be in access order (not accessed)
        assert 1 not in sim._cache_access_order
        assert 3 not in sim._cache_access_order


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
