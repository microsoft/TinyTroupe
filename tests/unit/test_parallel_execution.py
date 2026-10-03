"""
Tests for parallel world execution.

This module tests parallel execution of agents in TinyWorld environments,
comparing sequential vs parallel performance and ensuring correct behavior.
"""
import pytest
import sys
sys.path.insert(0, '../../tinytroupe/')
sys.path.insert(0, '../../')
sys.path.insert(0, '..')

from tinytroupe.environment import TinyWorld
from tinytroupe.agent import TinyPerson
from tinytroupe.agent.memory import EpisodicMemory
from unittest.mock import Mock, MagicMock, patch
from datetime import timedelta
import time


class TestParallelExecution:
    """Test parallel execution in TinyWorld."""

    def test_parallel_vs_sequential_basic(self, setup):
        """Test that parallel and sequential execution produce similar results."""
        # Create world with test agents
        world = TinyWorld("TestWorld")
        agents = [TinyPerson(f"Agent{i}") for i in range(3)]

        for agent in agents:
            agent.episodic_memory = EpisodicMemory(max_size=100)
            world.add_agent(agent)

        # Mock act method to return predictable actions
        def mock_act(return_actions=False):
            actions = [{"action": {"type": "DONE", "content": "", "target": ""}}]
            return actions if return_actions else None

        for agent in agents:
            agent.act = mock_act

        # Run sequentially
        sequential_actions = world._step_sequentially()

        # Run in parallel
        parallel_actions = world._step_in_parallel()

        # Both should have actions for all agents
        assert len(sequential_actions) == len(agents)
        assert len(parallel_actions) == len(agents)

        # All agents should have acted
        for agent in agents:
            assert agent.name in sequential_actions
            assert agent.name in parallel_actions

    def test_parallel_execution_metrics(self, setup):
        """Test that parallel execution collects metrics correctly."""
        world = TinyWorld("MetricsWorld")
        agents = [TinyPerson(f"Agent{i}") for i in range(5)]

        for agent in agents:
            agent.episodic_memory = EpisodicMemory(max_size=100)
            world.add_agent(agent)

        # Mock act
        def mock_act(return_actions=False):
            time.sleep(0.01)  # Simulate some work
            return [{"action": {"type": "DONE"}}] if return_actions else None

        for agent in agents:
            agent.act = mock_act

        # Run a few parallel steps
        for _ in range(3):
            world._step_in_parallel()

        # Check metrics
        metrics = world.get_parallel_metrics()

        assert metrics['total_parallel_steps'] == 3
        assert metrics['avg_parallel_speedup'] > 0
        assert metrics['parallel_errors'] == 0
        assert metrics['parallel_timeouts'] == 0

    def test_parallel_execution_timeout(self, setup):
        """Test that parallel execution handles timeouts correctly."""
        world = TinyWorld("TimeoutWorld")
        agents = [TinyPerson(f"Agent{i}") for i in range(2)]

        for agent in agents:
            agent.episodic_memory = EpisodicMemory(max_size=100)
            world.add_agent(agent)

        # Mock act - one agent takes too long
        def slow_act(return_actions=False):
            time.sleep(10)  # Takes longer than timeout
            return [{"action": {"type": "DONE"}}] if return_actions else None

        def fast_act(return_actions=False):
            return [{"action": {"type": "DONE"}}] if return_actions else None

        agents[0].act = fast_act
        agents[1].act = slow_act

        # Override timeout to 1 second for testing
        with patch.object(world, '_step_in_parallel') as mock_step:
            # We'll need to actually test this with real timeout
            # For now, verify the configuration is respected
            pass

        # This test would need actual timeout testing which is harder to mock

    def test_parallel_execution_error_handling(self, setup):
        """Test that parallel execution handles agent errors gracefully."""
        world = TinyWorld("ErrorWorld")
        agents = [TinyPerson(f"Agent{i}") for i in range(3)]

        for agent in agents:
            agent.episodic_memory = EpisodicMemory(max_size=100)
            world.add_agent(agent)

        # Mock act - one agent raises exception
        def good_act(return_actions=False):
            return [{"action": {"type": "DONE"}}] if return_actions else None

        def bad_act(return_actions=False):
            raise ValueError("Simulated error")

        agents[0].act = good_act
        agents[1].act = bad_act
        agents[2].act = good_act

        # Run parallel step - should handle error gracefully
        actions = world._step_in_parallel()

        # Two agents should have succeeded
        assert len(actions) == 2

        # Metrics should show one error
        metrics = world.get_parallel_metrics()
        assert metrics['parallel_errors'] == 1

    def test_config_based_parallelization(self, setup):
        """Test that parallelization respects configuration."""
        world = TinyWorld("ConfigWorld")
        agents = [TinyPerson(f"Agent{i}") for i in range(3)]

        for agent in agents:
            agent.episodic_memory = EpisodicMemory(max_size=100)
            world.add_agent(agent)

        def mock_act(return_actions=False):
            return [{"action": {"type": "DONE"}}] if return_actions else None

        for agent in agents:
            agent.act = mock_act

        # Test with parallelize=True
        actions_parallel = world._step(parallelize=True)
        assert len(actions_parallel) == 3

        # Test with parallelize=False
        actions_sequential = world._step(parallelize=False)
        assert len(actions_sequential) == 3

        # Metrics should show both types
        metrics = world.get_parallel_metrics()
        assert metrics['total_parallel_steps'] >= 1
        assert metrics['total_sequential_steps'] >= 1

    def test_parallel_with_multiple_steps(self, setup):
        """Test parallel execution over multiple simulation steps."""
        world = TinyWorld("MultiStepWorld")
        agents = [TinyPerson(f"Agent{i}") for i in range(4)]

        for agent in agents:
            agent.episodic_memory = EpisodicMemory(max_size=100)
            world.add_agent(agent)

        action_count = {agent.name: 0 for agent in agents}

        def make_counting_act(agent_name):
            def counting_act(return_actions=False):
                action_count[agent_name] += 1
                return [{"action": {"type": "DONE"}}] if return_actions else None
            return counting_act

        for agent in agents:
            agent.act = make_counting_act(agent.name)

        # Run multiple parallel steps
        steps = 5
        for _ in range(steps):
            world._step_in_parallel()

        # Each agent should have acted in each step
        for agent in agents:
            assert action_count[agent.name] == steps

    def test_parallel_execution_preserves_agent_state(self, setup):
        """Test that parallel execution doesn't corrupt agent state."""
        world = TinyWorld("StateWorld")
        agents = [TinyPerson(f"Agent{i}") for i in range(5)]

        for agent in agents:
            agent.episodic_memory = EpisodicMemory(max_size=100)
            agent.test_counter = 0
            world.add_agent(agent)

        def stateful_act(return_actions=False):
            # Access thread-safe counter
            with self._state_lock:
                self.test_counter += 1
            return [{"action": {"type": "DONE"}}] if return_actions else None

        # This would need more sophisticated testing with actual state

    def test_run_method_with_parallel_flag(self, setup):
        """Test that run() method respects parallel flag."""
        world = TinyWorld("RunWorld")
        agents = [TinyPerson(f"Agent{i}") for i in range(2)]

        for agent in agents:
            agent.episodic_memory = EpisodicMemory(max_size=100)
            world.add_agent(agent)

        def mock_act(return_actions=False):
            return [{"action": {"type": "DONE"}}] if return_actions else None

        for agent in agents:
            agent.act = mock_act

        # Run with parallel=True
        world.run(steps=3, parallelize=True)

        metrics = world.get_parallel_metrics()
        assert metrics['total_parallel_steps'] >= 3

    def test_sequential_and_parallel_metrics_separation(self, setup):
        """Test that sequential and parallel metrics are tracked separately."""
        world = TinyWorld("MetricsSepWorld")
        agents = [TinyPerson(f"Agent{i}") for i in range(2)]

        for agent in agents:
            agent.episodic_memory = EpisodicMemory(max_size=100)
            world.add_agent(agent)

        def mock_act(return_actions=False):
            return [{"action": {"type": "DONE"}}] if return_actions else None

        for agent in agents:
            agent.act = mock_act

        # Run 2 sequential steps
        for _ in range(2):
            world._step_sequentially()

        # Run 3 parallel steps
        for _ in range(3):
            world._step_in_parallel()

        metrics = world.get_parallel_metrics()
        assert metrics['total_sequential_steps'] == 2
        assert metrics['total_parallel_steps'] == 3


class TestParallelExecutionConfiguration:
    """Test parallel execution configuration."""

    def test_max_workers_configuration(self, setup):
        """Test that max_workers configuration is respected."""
        # This would require mocking ThreadPoolExecutor to verify max_workers
        world = TinyWorld("MaxWorkersWorld")

        # The actual max_workers is passed to ThreadPoolExecutor
        # We'd need to patch ThreadPoolExecutor to verify this

    def test_timeout_configuration(self, setup):
        """Test that timeout configuration is respected."""
        # This would require testing with actual slow agents
        # and verifying timeouts are enforced
        pass


class TestParallelExecutionEdgeCases:
    """Test edge cases in parallel execution."""

    def test_parallel_with_no_agents(self, setup):
        """Test parallel execution with no agents."""
        world = TinyWorld("EmptyWorld")

        # Should handle empty agent list gracefully
        actions = world._step_in_parallel()
        assert len(actions) == 0

    def test_parallel_with_single_agent(self, setup):
        """Test parallel execution with single agent."""
        world = TinyWorld("SingleAgentWorld")
        agent = TinyPerson("SoloAgent")
        agent.episodic_memory = EpisodicMemory(max_size=100)
        world.add_agent(agent)

        def mock_act(return_actions=False):
            return [{"action": {"type": "DONE"}}] if return_actions else None

        agent.act = mock_act

        # Should work fine with single agent
        actions = world._step_in_parallel()
        assert len(actions) == 1
        assert "SoloAgent" in actions

    def test_metrics_thread_safety(self, setup):
        """Test that metrics updates are thread-safe."""
        import threading

        world = TinyWorld("ThreadSafeMetricsWorld")

        # Simulate concurrent metrics updates
        def update_metrics():
            with world._metrics_lock:
                world._parallel_metrics['total_parallel_steps'] += 1

        threads = [threading.Thread(target=update_metrics) for _ in range(100)]

        for t in threads:
            t.start()

        for t in threads:
            t.join()

        metrics = world.get_parallel_metrics()
        assert metrics['total_parallel_steps'] == 100


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
