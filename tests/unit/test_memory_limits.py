"""
Tests for memory size limits and cleanup strategies.

This module tests the bounded memory functionality implemented in Task 1.1 of Phase 1.
"""
import pytest
import logging
logger = logging.getLogger("tinytroupe")

import sys
sys.path.insert(0, '../../tinytroupe/')
sys.path.insert(0, '../../')
sys.path.insert(0, '..')

from tinytroupe.agent.memory import EpisodicMemory
from collections import deque
from testing_utils import *


class TestMemorySizeLimits:
    """Test suite for memory size limits and bounded memory functionality."""

    def test_memory_respects_size_limit_with_fifo(self, setup):
        """Test that memory respects the max_size parameter with FIFO strategy."""
        max_size = 10
        memory = EpisodicMemory(max_size=max_size, cleanup_strategy="fifo")

        # Store more items than max_size
        for i in range(20):
            memory.store({'content': f'Memory {i}', 'type': 'action', 'simulation_timestamp': f'2024-01-{i:02d}'})

        # Commit the episode to move from buffer to main memory
        memory.commit_episode()

        # Memory should be bounded to max_size
        assert len(memory.memory) == max_size, f"Memory size should be {max_size}, but is {len(memory.memory)}"

        # Should contain the most recent memories (10-19)
        memory_list = list(memory.memory)
        assert memory_list[0]['content'] == 'Memory 10', "First memory should be 'Memory 10' (FIFO)"
        assert memory_list[-1]['content'] == 'Memory 19', "Last memory should be 'Memory 19'"

    def test_memory_with_unbounded_setting(self, setup):
        """Test that memory can be unbounded when max_size is 0 or None."""
        # Test with max_size=0
        memory = EpisodicMemory(max_size=0)
        for i in range(100):
            memory.store({'content': f'Memory {i}', 'type': 'action', 'simulation_timestamp': f'2024-01-{i:02d}'})
        memory.commit_episode()

        assert len(memory.memory) == 100, "Unbounded memory (max_size=0) should store all memories"

        # Test with max_size=None
        memory2 = EpisodicMemory(max_size=None)
        for i in range(100):
            memory2.store({'content': f'Memory {i}', 'type': 'action', 'simulation_timestamp': f'2024-01-{i:02d}'})
        memory2.commit_episode()

        assert len(memory2.memory) == 100, "Unbounded memory (max_size=None) should store all memories"

    def test_memory_uses_deque_for_fifo(self, setup):
        """Test that FIFO strategy uses deque for efficiency."""
        memory = EpisodicMemory(max_size=10, cleanup_strategy="fifo")
        assert isinstance(memory.memory, deque), "FIFO strategy should use deque"

    def test_memory_uses_list_for_other_strategies(self, setup):
        """Test that non-FIFO strategies use list."""
        memory_age = EpisodicMemory(max_size=10, cleanup_strategy="age")
        assert isinstance(memory_age.memory, list), "Age strategy should use list"

        memory_relevance = EpisodicMemory(max_size=10, cleanup_strategy="relevance")
        assert isinstance(memory_relevance.memory, list), "Relevance strategy should use list"

    def test_age_based_cleanup_strategy(self, setup):
        """Test that age-based cleanup removes oldest memories by timestamp."""
        memory = EpisodicMemory(max_size=5, cleanup_strategy="age")

        # Store memories with different timestamps
        for i in range(10):
            memory.store({
                'content': f'Memory {i}',
                'type': 'action',
                'simulation_timestamp': f'2024-01-{i+1:02d}'
            })

        memory.commit_episode()

        # Should have 5 most recent memories (by timestamp)
        assert len(memory.memory) == 5, "Memory should be limited to 5 items"

        # Verify that newest memories are kept
        memory_list = list(memory.memory)
        timestamps = [m['simulation_timestamp'] for m in memory_list]

        # After age-based cleanup, newest timestamps should remain
        assert '2024-01-10' in timestamps, "Most recent memory should be retained"
        assert '2024-01-09' in timestamps, "Recent memory should be retained"

    def test_memory_stats(self, setup):
        """Test that get_memory_stats returns accurate statistics."""
        max_size = 10
        memory = EpisodicMemory(max_size=max_size, cleanup_strategy="fifo")

        # Add some memories
        for i in range(5):
            memory.store({'content': f'Memory {i}', 'type': 'action', 'simulation_timestamp': f'2024-01-{i:02d}'})

        stats_before_commit = memory.get_memory_stats()
        assert stats_before_commit['current_size'] == 0, "Before commit, memory should be empty"
        assert stats_before_commit['buffer_size'] == 5, "Buffer should have 5 items"
        assert stats_before_commit['total_size'] == 5, "Total should be 5"
        assert stats_before_commit['max_size'] == max_size
        assert stats_before_commit['is_bounded'] is True

        memory.commit_episode()

        stats_after_commit = memory.get_memory_stats()
        assert stats_after_commit['current_size'] == 5, "After commit, memory should have 5 items"
        assert stats_after_commit['buffer_size'] == 0, "Buffer should be empty after commit"
        assert stats_after_commit['usage_ratio'] == 0.5, "Usage should be 50%"

    def test_memory_warning_threshold(self, setup, caplog):
        """Test that warnings are issued when approaching memory limits."""
        max_size = 10
        memory = EpisodicMemory(max_size=max_size, cleanup_strategy="fifo")

        # Store enough memories to trigger warning (80% of max_size = 8)
        for i in range(9):
            memory.store({'content': f'Memory {i}', 'type': 'action', 'simulation_timestamp': f'2024-01-{i:02d}'})

        memory.commit_episode()

        # Check memory stats
        stats = memory.get_memory_stats()
        assert stats['approaching_limit'] is True, "Memory should be approaching limit"

    def test_memory_clear_with_bounded_memory(self, setup):
        """Test that clearing memory works correctly with bounded memory."""
        memory = EpisodicMemory(max_size=10, cleanup_strategy="fifo")

        # Add memories
        for i in range(8):
            memory.store({'content': f'Memory {i}', 'type': 'action', 'simulation_timestamp': f'2024-01-{i:02d}'})
        memory.commit_episode()

        # Clear all memory
        memory.clear()

        assert len(memory.memory) == 0, "Memory should be empty after clear"
        assert isinstance(memory.memory, deque), "Should still be a deque after clear"

    def test_memory_overflow_scenario(self, setup):
        """Test memory behavior when continuously adding beyond max_size."""
        max_size = 100
        memory = EpisodicMemory(max_size=max_size, cleanup_strategy="fifo")

        # Simulate a long-running simulation
        for episode in range(5):
            # Add 50 memories per episode
            for i in range(50):
                memory.store({
                    'content': f'Episode {episode}, Memory {i}',
                    'type': 'action',
                    'simulation_timestamp': f'2024-{episode+1:02d}-{i:02d}'
                })
            memory.commit_episode()

        # Should never exceed max_size
        assert len(memory.memory) <= max_size, f"Memory should not exceed {max_size}"

        # Should have the most recent memories
        memory_list = list(memory.memory)
        # Last memory should be from episode 4, memory 49
        assert 'Episode 4' in memory_list[-1]['content'], "Should have most recent episode memories"

    def test_memory_with_current_buffer_handles_deque(self, setup):
        """Test that _memory_with_current_buffer correctly handles deque."""
        memory = EpisodicMemory(max_size=10, cleanup_strategy="fifo")

        for i in range(5):
            memory.store({'content': f'Committed {i}', 'type': 'action', 'simulation_timestamp': f'2024-01-{i:02d}'})
        memory.commit_episode()

        for i in range(3):
            memory.store({'content': f'Buffer {i}', 'type': 'action', 'simulation_timestamp': f'2024-02-{i:02d}'})

        combined = memory._memory_with_current_buffer()

        assert isinstance(combined, list), "Combined memory should be a list"
        assert len(combined) == 8, "Should have 5 committed + 3 buffered"
        assert combined[0]['content'] == 'Committed 0'
        assert combined[-1]['content'] == 'Buffer 2'

    def test_memory_cleanup_preserves_data_integrity(self, setup):
        """Test that cleanup doesn't corrupt memory data."""
        memory = EpisodicMemory(max_size=5, cleanup_strategy="fifo")

        # Store complex memory objects
        for i in range(10):
            memory.store({
                'content': f'Complex memory {i}',
                'type': 'action',
                'simulation_timestamp': f'2024-01-{i:02d}',
                'metadata': {'importance': i, 'tags': [f'tag{i}', f'tag{i+1}']}
            })
        memory.commit_episode()

        # Verify that remaining memories are intact
        memory_list = list(memory.memory)
        assert len(memory_list) == 5

        for mem in memory_list:
            assert 'content' in mem
            assert 'type' in mem
            assert 'simulation_timestamp' in mem
            assert 'metadata' in mem
            assert 'importance' in mem['metadata']
            assert 'tags' in mem['metadata']

    def test_retrieve_methods_work_with_bounded_memory(self, setup):
        """Test that retrieve methods work correctly with bounded memory."""
        memory = EpisodicMemory(max_size=10, cleanup_strategy="fifo")

        for i in range(15):
            memory.store({'content': f'Memory {i}', 'type': 'action', 'simulation_timestamp': f'2024-01-{i:02d}'})
        memory.commit_episode()

        # Test retrieve_all
        all_memories = memory.retrieve_all()
        assert len(all_memories) == 10, "retrieve_all should return all memories within limit"

        # Test retrieve_recent
        recent = memory.retrieve_recent()
        assert len(recent) > 0, "retrieve_recent should work with bounded memory"

        # Test retrieve with parameters
        first_5 = memory.retrieve(first_n=5, last_n=None)
        assert len(first_5) <= 6, "retrieve should respect bounded memory (5 + optional omission info)"


class TestMemoryConfiguration:
    """Test suite for memory configuration from config file."""

    def test_memory_reads_config_values(self, setup):
        """Test that memory reads configuration from config manager."""
        # Create memory without explicit parameters (should use config)
        memory = EpisodicMemory()

        # Should have loaded from config
        assert memory.max_size is not None, "max_size should be loaded from config"
        assert memory.cleanup_strategy is not None, "cleanup_strategy should be loaded from config"
        assert memory.warning_threshold is not None, "warning_threshold should be loaded from config"

    def test_explicit_parameters_override_config(self, setup):
        """Test that explicit parameters override config values."""
        memory = EpisodicMemory(max_size=50, cleanup_strategy="age")

        assert memory.max_size == 50, "Explicit max_size should override config"
        assert memory.cleanup_strategy == "age", "Explicit cleanup_strategy should override config"


class TestEdgeCases:
    """Test suite for edge cases and error conditions."""

    def test_memory_with_empty_memories(self, setup):
        """Test memory behavior with empty or None values."""
        memory = EpisodicMemory(max_size=10, cleanup_strategy="fifo")

        # Store empty content
        memory.store({'content': '', 'type': 'action', 'simulation_timestamp': '2024-01-01'})
        memory.commit_episode()

        assert len(memory.memory) == 1, "Should store empty content"

    def test_memory_with_max_size_one(self, setup):
        """Test memory with max_size of 1 (edge case)."""
        memory = EpisodicMemory(max_size=1, cleanup_strategy="fifo")

        for i in range(5):
            memory.store({'content': f'Memory {i}', 'type': 'action', 'simulation_timestamp': f'2024-01-{i:02d}'})
        memory.commit_episode()

        assert len(memory.memory) == 1, "Memory should only have 1 item"
        memory_list = list(memory.memory)
        assert memory_list[0]['content'] == 'Memory 4', "Should have the most recent memory"

    def test_memory_stats_with_unbounded_memory(self, setup):
        """Test that get_memory_stats handles unbounded memory correctly."""
        memory = EpisodicMemory(max_size=None)

        stats = memory.get_memory_stats()
        assert stats['max_size'] is None
        assert stats['usage_ratio'] is None
        assert stats['is_bounded'] is False
        assert stats['approaching_limit'] is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
