"""
Tests for thread-safe agent actions.

This module tests thread safety of TinyPerson operations when multiple
threads are acting on the same agent or multiple agents concurrently.
"""
import pytest
import sys
sys.path.insert(0, '../../tinytroupe/')
sys.path.insert(0, '../../')
sys.path.insert(0, '..')

from tinytroupe.agent.tiny_person import TinyPerson
from tinytroupe.agent.memory import EpisodicMemory
from unittest.mock import Mock, MagicMock
import threading
import time


class TestThreadSafetyBasics:
    """Test basic thread safety of agent operations."""

    def test_concurrent_counter_increments(self, setup):
        """Test that concurrent counter increments are thread-safe."""
        agent = TinyPerson("TestAgent")
        agent.episodic_memory = EpisodicMemory(max_size=1000)
        agent.actions_count = 0
        agent.stimuli_count = 0

        def increment_actions(iterations):
            for _ in range(iterations):
                with agent._state_lock:
                    agent.actions_count += 1

        def increment_stimuli(iterations):
            for _ in range(iterations):
                with agent._state_lock:
                    agent.stimuli_count += 1

        iterations = 100
        threads = []

        # Create 10 threads incrementing actions
        for _ in range(10):
            t = threading.Thread(target=increment_actions, args=(iterations,))
            threads.append(t)
            t.start()

        # Create 10 threads incrementing stimuli
        for _ in range(10):
            t = threading.Thread(target=increment_stimuli, args=(iterations,))
            threads.append(t)
            t.start()

        # Wait for all threads to complete
        for t in threads:
            t.join()

        # Verify counts are correct
        assert agent.actions_count == iterations * 10, f"Expected {iterations * 10}, got {agent.actions_count}"
        assert agent.stimuli_count == iterations * 10, f"Expected {iterations * 10}, got {agent.stimuli_count}"

    def test_concurrent_memory_stores(self, setup):
        """Test that concurrent memory stores are thread-safe."""
        agent = TinyPerson("TestAgent")
        agent.episodic_memory = EpisodicMemory(max_size=1000)

        def store_memories(thread_id, count):
            for i in range(count):
                agent.store_in_memory({
                    'content': f'Thread {thread_id}, Memory {i}',
                    'type': 'action',
                    'simulation_timestamp': f'2024-{thread_id:02d}-{i:03d}'
                })

        count_per_thread = 50
        thread_count = 5
        threads = []

        for thread_id in range(thread_count):
            t = threading.Thread(target=store_memories, args=(thread_id, count_per_thread))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # Verify total memory count
        total_expected = count_per_thread * thread_count
        actual_total = len(agent.episodic_memory.episodic_buffer) + len(agent.episodic_memory.memory)

        assert actual_total == total_expected, f"Expected {total_expected} memories, got {actual_total}"

    def test_concurrent_mental_state_updates(self, setup):
        """Test that concurrent mental state updates are thread-safe."""
        agent = TinyPerson("TestAgent")

        def update_goals(thread_id):
            for i in range(10):
                agent._update_cognitive_state(goals=[f"Thread {thread_id} Goal {i}"])
                time.sleep(0.001)  # Small delay to increase contention

        threads = []
        for thread_id in range(5):
            t = threading.Thread(target=update_goals, args=(thread_id,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # Verify mental state still has a valid goals structure
        assert "goals" in agent._mental_state
        assert isinstance(agent._mental_state["goals"], list)

    def test_concurrent_accessible_agents_modifications(self, setup):
        """Test that concurrent accessible agents modifications are thread-safe."""
        agent = TinyPerson("MainAgent")
        test_agents = [TinyPerson(f"Agent{i}") for i in range(10)]

        def make_accessible(agents_subset):
            for a in agents_subset:
                agent.make_agent_accessible(a)

        def make_inaccessible(agents_subset):
            time.sleep(0.01)  # Let some additions happen first
            for a in agents_subset:
                agent.make_agent_inaccessible(a)

        threads = []

        # Thread 1: Make first 5 accessible
        t1 = threading.Thread(target=make_accessible, args=(test_agents[:5],))
        threads.append(t1)

        # Thread 2: Make last 5 accessible
        t2 = threading.Thread(target=make_accessible, args=(test_agents[5:],))
        threads.append(t2)

        # Thread 3: Remove first 3
        t3 = threading.Thread(target=make_inaccessible, args=(test_agents[:3],))
        threads.append(t3)

        for t in threads:
            t.start()

        for t in threads:
            t.join()

        # Verify consistency between lists
        accessible_count = len(agent._accessible_agents)
        mental_state_count = len(agent._mental_state["accessible_agents"])

        assert accessible_count == mental_state_count, \
            f"Inconsistency: {accessible_count} agents vs {mental_state_count} in mental state"


class TestThreadSafetyConsolidation:
    """Test thread safety of memory consolidation."""

    def test_concurrent_consolidation_attempts(self, setup):
        """Test that concurrent consolidation attempts don't corrupt state."""
        agent = TinyPerson("TestAgent")
        agent.episodic_memory = EpisodicMemory(max_size=1000)

        # Add enough memories to trigger consolidation
        for i in range(100):
            agent.store_in_memory({
                'content': f'Memory {i}',
                'type': 'action',
                'simulation_timestamp': f'2024-01-{i:03d}'
            })

        consolidation_results = []

        def try_consolidate():
            result = agent.consolidate_episode_memories(force=True)
            consolidation_results.append(result)

        threads = []
        for _ in range(3):
            t = threading.Thread(target=try_consolidate)
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # At least one should succeed, others might fail due to lock
        assert any(consolidation_results), "At least one consolidation should succeed"

        # Verify memory state is valid
        assert hasattr(agent, 'consolidation_metrics')
        assert agent.consolidation_metrics['total_consolidations'] >= 1

    def test_memory_consolidation_during_storage(self, setup):
        """Test that memory storage works correctly even during consolidation."""
        agent = TinyPerson("TestAgent")
        agent.episodic_memory = EpisodicMemory(max_size=1000)

        # Pre-fill some memories
        for i in range(50):
            agent.store_in_memory({
                'content': f'Initial Memory {i}',
                'type': 'action',
                'simulation_timestamp': f'2024-01-{i:03d}'
            })

        def continuous_storage():
            for i in range(50):
                agent.store_in_memory({
                    'content': f'During Consolidation {i}',
                    'type': 'action',
                    'simulation_timestamp': f'2024-02-{i:03d}'
                })
                time.sleep(0.001)

        def try_consolidate():
            time.sleep(0.01)  # Let some storage happen
            agent.consolidate_episode_memories(force=True)

        t1 = threading.Thread(target=continuous_storage)
        t2 = threading.Thread(target=try_consolidate)

        t1.start()
        t2.start()

        t1.join()
        t2.join()

        # Verify no memories were lost
        total_memories = len(agent.episodic_memory.memory) + len(agent.episodic_memory.episodic_buffer)
        assert total_memories >= 50, f"Expected at least 50 memories, got {total_memories}"


class TestThreadSafetyMultipleAgents:
    """Test thread safety with multiple agents acting concurrently."""

    def test_multiple_agents_acting_concurrently(self, setup):
        """Test that multiple agents can act concurrently without interference."""
        agents = [TinyPerson(f"Agent{i}") for i in range(5)]

        for agent in agents:
            agent.episodic_memory = EpisodicMemory(max_size=1000)

        def agent_activity(agent, activity_count):
            for i in range(activity_count):
                agent.store_in_memory({
                    'content': f'{agent.name} Activity {i}',
                    'type': 'action',
                    'simulation_timestamp': f'2024-01-{i:03d}'
                })

                with agent._state_lock:
                    agent.actions_count += 1

        threads = []
        activity_count = 30

        for agent in agents:
            t = threading.Thread(target=agent_activity, args=(agent, activity_count))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # Verify each agent has correct counts
        for agent in agents:
            assert agent.actions_count == activity_count, \
                f"{agent.name} expected {activity_count} actions, got {agent.actions_count}"

            total_memories = len(agent.episodic_memory.memory) + len(agent.episodic_memory.episodic_buffer)
            assert total_memories == activity_count, \
                f"{agent.name} expected {activity_count} memories, got {total_memories}"

    def test_agents_with_shared_interactions(self, setup):
        """Test agents that interact with each other concurrently."""
        agent1 = TinyPerson("Alice")
        agent2 = TinyPerson("Bob")

        agent1.episodic_memory = EpisodicMemory(max_size=1000)
        agent2.episodic_memory = EpisodicMemory(max_size=1000)

        def alice_activity():
            for i in range(20):
                agent1.make_agent_accessible(agent2, "Friend")
                time.sleep(0.001)
                if i % 5 == 0:
                    agent1.make_agent_inaccessible(agent2)

        def bob_activity():
            for i in range(20):
                agent2.make_agent_accessible(agent1, "Friend")
                time.sleep(0.001)
                if i % 5 == 0:
                    agent2.make_agent_inaccessible(agent1)

        t1 = threading.Thread(target=alice_activity)
        t2 = threading.Thread(target=bob_activity)

        t1.start()
        t2.start()

        t1.join()
        t2.join()

        # Verify consistency of accessible agents for both
        for agent in [agent1, agent2]:
            accessible_count = len(agent._accessible_agents)
            mental_state_count = len(agent._mental_state["accessible_agents"])
            assert accessible_count == mental_state_count


class TestThreadSafetyStressTest:
    """Stress tests for thread safety."""

    def test_high_concurrency_stress(self, setup):
        """Stress test with high concurrency."""
        agent = TinyPerson("StressAgent")
        agent.episodic_memory = EpisodicMemory(max_size=2000)

        results = {'actions': 0, 'memories': 0, 'errors': 0}
        lock = threading.Lock()

        def mixed_operations(op_count):
            try:
                for i in range(op_count):
                    # Mix of operations
                    operation = i % 4

                    if operation == 0:
                        # Store memory
                        agent.store_in_memory({
                            'content': f'Stress test {i}',
                            'type': 'action',
                            'simulation_timestamp': f'2024-01-{i:03d}'
                        })
                        with lock:
                            results['memories'] += 1

                    elif operation == 1:
                        # Increment action count
                        with agent._state_lock:
                            agent.actions_count += 1
                        with lock:
                            results['actions'] += 1

                    elif operation == 2:
                        # Update mental state
                        agent._update_cognitive_state(goals=[f"Goal {i}"])

                    elif operation == 3:
                        # Get memory stats (read operation)
                        stats = agent.episodic_memory.get_memory_stats()
                        assert stats is not None

            except Exception as e:
                with lock:
                    results['errors'] += 1
                raise

        threads = []
        op_count = 25
        thread_count = 10

        for _ in range(thread_count):
            t = threading.Thread(target=mixed_operations, args=(op_count,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # Verify no errors occurred
        assert results['errors'] == 0, f"{results['errors']} errors occurred during stress test"

        # Verify counts are reasonable
        assert results['actions'] > 0
        assert results['memories'] > 0

        # Verify agent state is still valid
        assert hasattr(agent, '_mental_state')
        assert hasattr(agent, 'episodic_memory')


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
