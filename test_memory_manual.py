#!/usr/bin/env python
"""
Manual test script for memory limits functionality.
"""

import sys
sys.path.insert(0, 'tinytroupe/')

from tinytroupe.agent.memory import EpisodicMemory
from collections import deque

def test_basic_memory_limits():
    """Test basic memory limit functionality."""
    print("=" * 60)
    print("Test 1: Basic Memory Limits with FIFO")
    print("=" * 60)

    max_size = 10
    memory = EpisodicMemory(max_size=max_size, cleanup_strategy="fifo")

    print(f"Created memory with max_size={max_size}, strategy=fifo")
    print(f"Memory is using: {type(memory.memory).__name__}")

    # Store more items than max_size
    for i in range(20):
        memory.store({'content': f'Memory {i}', 'type': 'action', 'simulation_timestamp': f'2024-01-{i:02d}'})

    print(f"Stored 20 memories in buffer")
    print(f"Buffer size: {len(memory.episodic_buffer)}")

    # Commit the episode
    memory.commit_episode()

    print(f"Committed episode")
    print(f"Memory size: {len(memory.memory)}")
    print(f"Expected: {max_size}")

    # Verify
    if len(memory.memory) == max_size:
        print("✓ PASS: Memory size is correct")
    else:
        print(f"✗ FAIL: Memory size is {len(memory.memory)}, expected {max_size}")
        return False

    # Check contents
    memory_list = list(memory.memory)
    print(f"First memory: {memory_list[0]['content']}")
    print(f"Last memory: {memory_list[-1]['content']}")

    if memory_list[0]['content'] == 'Memory 10' and memory_list[-1]['content'] == 'Memory 19':
        print("✓ PASS: Memory contains correct items (FIFO)")
    else:
        print("✗ FAIL: Memory contents are incorrect")
        return False

    print()
    return True


def test_memory_stats():
    """Test memory statistics."""
    print("=" * 60)
    print("Test 2: Memory Statistics")
    print("=" * 60)

    memory = EpisodicMemory(max_size=10, cleanup_strategy="fifo")

    # Add some memories
    for i in range(5):
        memory.store({'content': f'Memory {i}', 'type': 'action', 'simulation_timestamp': f'2024-01-{i:02d}'})

    stats_before = memory.get_memory_stats()
    print(f"Stats before commit:")
    print(f"  Current size: {stats_before['current_size']}")
    print(f"  Buffer size: {stats_before['buffer_size']}")
    print(f"  Total size: {stats_before['total_size']}")
    print(f"  Max size: {stats_before['max_size']}")
    print(f"  Is bounded: {stats_before['is_bounded']}")

    memory.commit_episode()

    stats_after = memory.get_memory_stats()
    print(f"\nStats after commit:")
    print(f"  Current size: {stats_after['current_size']}")
    print(f"  Buffer size: {stats_after['buffer_size']}")
    print(f"  Total size: {stats_after['total_size']}")
    print(f"  Usage ratio: {stats_after['usage_ratio']}")

    if (stats_before['buffer_size'] == 5 and
        stats_after['current_size'] == 5 and
        stats_after['usage_ratio'] == 0.5):
        print("\n✓ PASS: Memory statistics are correct")
        return True
    else:
        print("\n✗ FAIL: Memory statistics are incorrect")
        return False


def test_unbounded_memory():
    """Test unbounded memory."""
    print("=" * 60)
    print("Test 3: Unbounded Memory")
    print("=" * 60)

    memory = EpisodicMemory(max_size=0)

    for i in range(100):
        memory.store({'content': f'Memory {i}', 'type': 'action', 'simulation_timestamp': f'2024-01-{i:02d}'})

    memory.commit_episode()

    print(f"Stored 100 memories with max_size=0")
    print(f"Memory size: {len(memory.memory)}")

    if len(memory.memory) == 100:
        print("✓ PASS: Unbounded memory works correctly")
        return True
    else:
        print(f"✗ FAIL: Expected 100 memories, got {len(memory.memory)}")
        return False


def test_age_based_cleanup():
    """Test age-based cleanup strategy."""
    print("=" * 60)
    print("Test 4: Age-Based Cleanup")
    print("=" * 60)

    memory = EpisodicMemory(max_size=5, cleanup_strategy="age")

    print(f"Memory is using: {type(memory.memory).__name__}")

    # Store memories with different timestamps
    for i in range(10):
        memory.store({
            'content': f'Memory {i}',
            'type': 'action',
            'simulation_timestamp': f'2024-01-{i+1:02d}'
        })

    memory.commit_episode()

    print(f"Stored 10 memories, max_size=5")
    print(f"Memory size: {len(memory.memory)}")

    if len(memory.memory) == 5:
        print("✓ PASS: Memory size limited correctly")
    else:
        print(f"✗ FAIL: Expected 5 memories, got {len(memory.memory)}")
        return False

    # Check timestamps
    timestamps = [m['simulation_timestamp'] for m in memory.memory]
    print(f"Timestamps in memory: {timestamps}")

    # Should keep newest by timestamp
    if '2024-01-10' in timestamps:
        print("✓ PASS: Newest memories retained (age-based cleanup)")
        return True
    else:
        print("✗ FAIL: Newest memories not retained")
        return False


def test_memory_with_current_buffer():
    """Test _memory_with_current_buffer with deque."""
    print("=" * 60)
    print("Test 5: Memory with Current Buffer (deque handling)")
    print("=" * 60)

    memory = EpisodicMemory(max_size=10, cleanup_strategy="fifo")

    for i in range(5):
        memory.store({'content': f'Committed {i}', 'type': 'action', 'simulation_timestamp': f'2024-01-{i:02d}'})
    memory.commit_episode()

    for i in range(3):
        memory.store({'content': f'Buffer {i}', 'type': 'action', 'simulation_timestamp': f'2024-02-{i:02d}'})

    combined = memory._memory_with_current_buffer()

    print(f"Combined type: {type(combined).__name__}")
    print(f"Combined length: {len(combined)}")
    print(f"First item: {combined[0]['content']}")
    print(f"Last item: {combined[-1]['content']}")

    if (isinstance(combined, list) and
        len(combined) == 8 and
        combined[0]['content'] == 'Committed 0' and
        combined[-1]['content'] == 'Buffer 2'):
        print("✓ PASS: _memory_with_current_buffer works correctly")
        return True
    else:
        print("✗ FAIL: _memory_with_current_buffer has issues")
        return False


if __name__ == "__main__":
    print("\nRunning Manual Memory Limits Tests\n")

    tests = [
        test_basic_memory_limits,
        test_memory_stats,
        test_unbounded_memory,
        test_age_based_cleanup,
        test_memory_with_current_buffer,
    ]

    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
            print()
        except Exception as e:
            print(f"✗ EXCEPTION: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)
            print()

    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")

    if passed == total:
        print("✓ ALL TESTS PASSED")
        sys.exit(0)
    else:
        print("✗ SOME TESTS FAILED")
        sys.exit(1)
