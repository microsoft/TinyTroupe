"""
Parallel Execution Benchmarks for TinyTroupe

This module provides specialized benchmarks for parallel execution performance,
including thread pool sizing, timeout behavior, and concurrent agent interactions.
"""
import sys
sys.path.insert(0, '../../tinytroupe/')
sys.path.insert(0, '../../')
sys.path.insert(0, '..')

import time
import threading
from typing import List, Dict, Tuple
from dataclasses import dataclass

from tinytroupe.environment import TinyWorld
from tinytroupe.agent import TinyPerson
from tinytroupe.agent.memory import EpisodicMemory
from tinytroupe import config_manager


@dataclass
class ParallelBenchmarkResult:
    """Results from parallel execution benchmark."""
    scenario: str
    agent_count: int
    max_workers: int
    total_time: float
    parallel_steps: int
    avg_speedup: float
    errors: int
    timeouts: int
    efficiency: float  # speedup / agent_count


class ParallelBenchmark:
    """
    Specialized benchmarks for parallel execution.

    Focuses on parallel-specific metrics like thread pool efficiency,
    speedup, and concurrent execution behavior.
    """

    def __init__(self):
        """Initialize parallel benchmark suite."""
        self.results: List[ParallelBenchmarkResult] = []

    def benchmark_thread_pool_sizes(
        self,
        agent_count: int = 10,
        max_workers_options: List[int] = [1, 2, 4, 8, None],
        steps: int = 20
    ) -> None:
        """
        Benchmark different thread pool sizes.

        Args:
            agent_count: Number of agents to test with
            max_workers_options: List of max_workers values to test
            steps: Number of steps per test
        """
        print("\n=== Thread Pool Size Benchmark ===\n")
        print(f"Agent Count: {agent_count}, Steps: {steps}")
        print("-" * 80)

        for max_workers in max_workers_options:
            # Configure max_workers
            config_manager.set("max_workers", max_workers)

            # Create world with agents
            world = TinyWorld(f"ThreadPoolBench_{max_workers}")
            agents = self._create_mock_agents(agent_count)

            for agent in agents:
                world.add_agent(agent)

            # Run benchmark
            start_time = time.time()

            for _ in range(steps):
                world._step_in_parallel()

            end_time = time.time()
            total_time = end_time - start_time

            # Get metrics
            metrics = world.get_parallel_metrics()

            # Calculate efficiency
            avg_speedup = metrics.get('avg_parallel_speedup', 1.0)
            efficiency = (avg_speedup / agent_count) * 100  # Percentage

            workers_str = str(max_workers) if max_workers else "auto"
            print(f"  Workers: {workers_str:6s} | "
                  f"Time: {total_time:6.2f}s | "
                  f"Speedup: {avg_speedup:5.2f}x | "
                  f"Efficiency: {efficiency:5.1f}%")

            # Store result
            result = ParallelBenchmarkResult(
                scenario="thread_pool_size",
                agent_count=agent_count,
                max_workers=max_workers if max_workers else -1,
                total_time=total_time,
                parallel_steps=metrics.get('total_parallel_steps', 0),
                avg_speedup=avg_speedup,
                errors=metrics.get('parallel_errors', 0),
                timeouts=metrics.get('parallel_timeouts', 0),
                efficiency=efficiency
            )

            self.results.append(result)

    def benchmark_timeout_behavior(
        self,
        agent_count: int = 5,
        timeout_values: List[int] = [1, 5, 10, 60],
        slow_agent_delay: float = 3.0
    ) -> None:
        """
        Benchmark timeout handling with slow agents.

        Args:
            agent_count: Number of agents
            timeout_values: List of timeout values to test
            slow_agent_delay: Delay for slow agent (seconds)
        """
        print("\n=== Timeout Behavior Benchmark ===\n")
        print(f"Agent Count: {agent_count}, Slow Agent Delay: {slow_agent_delay}s")
        print("-" * 80)

        for timeout in timeout_values:
            # Configure timeout
            config_manager.set("parallel_execution_timeout", timeout)

            # Create world
            world = TinyWorld(f"TimeoutBench_{timeout}")
            agents = []

            # Create normal agents
            for i in range(agent_count - 1):
                agent = TinyPerson(f"FastAgent{i}")
                agent.episodic_memory = EpisodicMemory(max_size=100)

                def make_fast_act():
                    def fast_act(return_actions=False):
                        time.sleep(0.01)  # Fast
                        return [{"action": {"type": "DONE"}}] if return_actions else None
                    return fast_act

                agent.act = make_fast_act()
                agents.append(agent)

            # Create one slow agent
            slow_agent = TinyPerson("SlowAgent")
            slow_agent.episodic_memory = EpisodicMemory(max_size=100)

            def make_slow_act(delay):
                def slow_act(return_actions=False):
                    time.sleep(delay)
                    return [{"action": {"type": "DONE"}}] if return_actions else None
                return slow_act

            slow_agent.act = make_slow_act(slow_agent_delay)
            agents.append(slow_agent)

            for agent in agents:
                world.add_agent(agent)

            # Run one step
            start_time = time.time()
            world._step_in_parallel()
            end_time = time.time()

            # Get metrics
            metrics = world.get_parallel_metrics()

            print(f"  Timeout: {timeout:3d}s | "
                  f"Time: {end_time - start_time:6.2f}s | "
                  f"Timeouts: {metrics.get('parallel_timeouts', 0)} | "
                  f"Errors: {metrics.get('parallel_errors', 0)}")

    def benchmark_concurrent_interactions(
        self,
        agent_count: int = 10,
        steps: int = 20,
        interaction_frequency: float = 0.3
    ) -> None:
        """
        Benchmark agents with concurrent interactions.

        Args:
            agent_count: Number of agents
            steps: Number of steps
            interaction_frequency: Probability of interaction per step
        """
        print("\n=== Concurrent Interactions Benchmark ===\n")
        print(f"Agent Count: {agent_count}, Steps: {steps}")
        print("-" * 80)

        # Create world
        world = TinyWorld(f"InteractionBench_{agent_count}")
        agents = []

        for i in range(agent_count):
            agent = TinyPerson(f"Agent{i}")
            agent.episodic_memory = EpisodicMemory(max_size=1000)

            # Mock act that may interact with other agents
            def make_interactive_act(agent_ref, all_agents, freq):
                def interactive_act(return_actions=False):
                    import random

                    # Simulate some work
                    time.sleep(0.01)

                    # Randomly interact with other agents
                    if random.random() < freq and len(all_agents) > 1:
                        other_agent = random.choice([a for a in all_agents if a != agent_ref])

                        # Thread-safe interaction
                        agent_ref.make_agent_accessible(other_agent, "Colleague")

                    return [{"action": {"type": "DONE"}}] if return_actions else None

                return interactive_act

            agents.append(agent)

        # Set up interactions after all agents created
        for agent in agents:
            agent.act = make_interactive_act(agent, agents, interaction_frequency)
            world.add_agent(agent)

        # Run benchmark
        start_time = time.time()

        for _ in range(steps):
            world._step_in_parallel()

        end_time = time.time()
        total_time = end_time - start_time

        # Get metrics
        metrics = world.get_parallel_metrics()

        print(f"  Total Time: {total_time:.2f}s")
        print(f"  Avg Speedup: {metrics.get('avg_parallel_speedup', 1.0):.2f}x")
        print(f"  Errors: {metrics.get('parallel_errors', 0)}")
        print(f"  Timeouts: {metrics.get('parallel_timeouts', 0)}")

        # Count accessible agents
        total_accessible = sum(len(agent._accessible_agents) for agent in agents)
        print(f"  Total Interactions: {total_accessible}")

    def benchmark_memory_consolidation_parallel(
        self,
        agent_count: int = 10,
        steps: int = 50,
        memories_per_step: int = 10
    ) -> None:
        """
        Benchmark memory consolidation under parallel execution.

        Args:
            agent_count: Number of agents
            steps: Number of steps
            memories_per_step: Memories to add per step per agent
        """
        print("\n=== Memory Consolidation Parallel Benchmark ===\n")
        print(f"Agent Count: {agent_count}, Steps: {steps}, Memories/Step: {memories_per_step}")
        print("-" * 80)

        # Create world
        world = TinyWorld(f"ConsolidationBench_{agent_count}")
        agents = []

        for i in range(agent_count):
            agent = TinyPerson(f"Agent{i}")
            agent.episodic_memory = EpisodicMemory(max_size=1000)

            # Mock act that stores many memories
            def make_memory_act(agent_ref, count):
                def memory_act(return_actions=False):
                    for j in range(count):
                        agent_ref.store_in_memory({
                            'content': f'Memory {j}',
                            'type': 'action',
                            'simulation_timestamp': f'2024-01-{j:03d}'
                        })

                    return [{"action": {"type": "DONE"}}] if return_actions else None

                return memory_act

            agent.act = make_memory_act(agent, memories_per_step)
            agents.append(agent)
            world.add_agent(agent)

        # Run benchmark
        start_time = time.time()
        consolidation_times = []

        for step in range(steps):
            step_start = time.time()
            world._step_in_parallel()
            step_end = time.time()

            # Check for consolidations
            for agent in agents:
                if hasattr(agent, 'consolidation_metrics'):
                    metrics = agent.get_consolidation_metrics()
                    if metrics['total_consolidations'] > 0:
                        consolidation_times.append(step_end - step_start)

        end_time = time.time()
        total_time = end_time - start_time

        # Collect consolidation metrics
        total_consolidations = sum(
            agent.get_consolidation_metrics()['total_consolidations']
            for agent in agents
            if hasattr(agent, 'consolidation_metrics')
        )

        print(f"  Total Time: {total_time:.2f}s")
        print(f"  Total Consolidations: {total_consolidations}")
        print(f"  Avg Time/Step: {total_time/steps:.3f}s")

        if consolidation_times:
            print(f"  Avg Consolidation Step Time: {sum(consolidation_times)/len(consolidation_times):.3f}s")

    def benchmark_error_recovery(
        self,
        agent_count: int = 10,
        error_rate: float = 0.1,
        steps: int = 20
    ) -> None:
        """
        Benchmark error recovery in parallel execution.

        Args:
            agent_count: Number of agents
            error_rate: Probability of agent error
            steps: Number of steps
        """
        print("\n=== Error Recovery Benchmark ===\n")
        print(f"Agent Count: {agent_count}, Error Rate: {error_rate}, Steps: {steps}")
        print("-" * 80)

        # Create world
        world = TinyWorld(f"ErrorBench_{agent_count}")
        agents = []

        for i in range(agent_count):
            agent = TinyPerson(f"Agent{i}")
            agent.episodic_memory = EpisodicMemory(max_size=100)

            # Mock act that may raise errors
            def make_error_act(rate):
                def error_act(return_actions=False):
                    import random

                    if random.random() < rate:
                        raise RuntimeError("Simulated agent error")

                    return [{"action": {"type": "DONE"}}] if return_actions else None

                return error_act

            agent.act = make_error_act(error_rate)
            agents.append(agent)
            world.add_agent(agent)

        # Run benchmark
        start_time = time.time()
        successful_steps = 0

        for _ in range(steps):
            try:
                world._step_in_parallel()
                successful_steps += 1
            except Exception as e:
                pass  # Continue despite errors

        end_time = time.time()

        # Get metrics
        metrics = world.get_parallel_metrics()

        print(f"  Total Time: {end_time - start_time:.2f}s")
        print(f"  Successful Steps: {successful_steps}/{steps}")
        print(f"  Total Errors: {metrics.get('parallel_errors', 0)}")
        print(f"  Error Rate: {metrics.get('parallel_errors', 0) / (agent_count * steps) * 100:.1f}%")

    def _create_mock_agents(self, count: int) -> List[TinyPerson]:
        """Create mock agents for benchmarking."""
        agents = []

        for i in range(count):
            agent = TinyPerson(f"Agent{i}")
            agent.episodic_memory = EpisodicMemory(max_size=100)

            def mock_act(return_actions=False):
                time.sleep(0.01)
                return [{"action": {"type": "DONE"}}] if return_actions else None

            agent.act = mock_act
            agents.append(agent)

        return agents

    def print_summary(self) -> None:
        """Print summary of parallel benchmark results."""
        if not self.results:
            print("\nNo parallel benchmark results.")
            return

        print("\n" + "=" * 80)
        print("PARALLEL EXECUTION BENCHMARK SUMMARY")
        print("=" * 80)

        for result in self.results:
            print(f"\n{result.scenario.upper()}")
            print(f"  Agents: {result.agent_count}, Workers: {result.max_workers}")
            print(f"  Time: {result.total_time:.2f}s, Speedup: {result.avg_speedup:.2f}x")
            print(f"  Efficiency: {result.efficiency:.1f}%, Errors: {result.errors}, Timeouts: {result.timeouts}")


def run_parallel_benchmarks():
    """Run all parallel execution benchmarks."""
    benchmark = ParallelBenchmark()

    print("\n" + "=" * 80)
    print("TINYTROUPE PARALLEL EXECUTION BENCHMARKS")
    print("=" * 80)

    # Run benchmarks
    benchmark.benchmark_thread_pool_sizes(
        agent_count=10,
        max_workers_options=[1, 2, 4, 8, None],
        steps=20
    )

    benchmark.benchmark_timeout_behavior(
        agent_count=5,
        timeout_values=[1, 5, 10],
        slow_agent_delay=3.0
    )

    benchmark.benchmark_concurrent_interactions(
        agent_count=10,
        steps=20,
        interaction_frequency=0.3
    )

    benchmark.benchmark_memory_consolidation_parallel(
        agent_count=10,
        steps=50,
        memories_per_step=10
    )

    benchmark.benchmark_error_recovery(
        agent_count=10,
        error_rate=0.1,
        steps=20
    )

    # Print summary
    benchmark.print_summary()

    return benchmark


if __name__ == "__main__":
    run_parallel_benchmarks()
