"""
Performance Benchmarking Suite for TinyTroupe

This module provides comprehensive benchmarking tools for measuring TinyTroupe
performance across different scenarios, agent counts, and execution modes.
"""
import sys
sys.path.insert(0, '../../tinytroupe/')
sys.path.insert(0, '../../')
sys.path.insert(0, '..')

import time
import psutil
import os
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
import json

from tinytroupe.environment import TinyWorld
from tinytroupe.agent import TinyPerson
from tinytroupe.agent.memory import EpisodicMemory
from tinytroupe.monitoring import MemoryMonitor
from unittest.mock import Mock


@dataclass
class BenchmarkResult:
    """Container for benchmark results."""
    benchmark_name: str
    agent_count: int
    execution_mode: str  # "sequential" or "parallel"
    total_time: float
    avg_time_per_step: float
    steps_completed: int
    memory_usage_mb: float
    peak_memory_mb: float
    speedup: Optional[float] = None
    parallel_metrics: Optional[Dict] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'benchmark_name': self.benchmark_name,
            'agent_count': self.agent_count,
            'execution_mode': self.execution_mode,
            'total_time': self.total_time,
            'avg_time_per_step': self.avg_time_per_step,
            'steps_completed': self.steps_completed,
            'memory_usage_mb': self.memory_usage_mb,
            'peak_memory_mb': self.peak_memory_mb,
            'speedup': self.speedup,
            'parallel_metrics': self.parallel_metrics,
            'timestamp': self.timestamp
        }


class PerformanceBenchmark:
    """
    Performance benchmarking suite for TinyTroupe.

    Measures execution time, memory usage, and parallel speedup
    across different scenarios and agent counts.
    """

    def __init__(self):
        """Initialize the benchmark suite."""
        self.results: List[BenchmarkResult] = []
        self.process = psutil.Process(os.getpid())

    def get_memory_usage(self) -> float:
        """Get current memory usage in MB."""
        return self.process.memory_info().rss / 1024 / 1024

    def create_mock_agents(self, count: int) -> List[TinyPerson]:
        """
        Create mock agents for benchmarking.

        Args:
            count: Number of agents to create

        Returns:
            List of TinyPerson agents with mock act methods
        """
        agents = []

        for i in range(count):
            agent = TinyPerson(f"BenchAgent{i}")
            agent.episodic_memory = EpisodicMemory(max_size=1000)

            # Mock act method with controllable delay
            def mock_act(return_actions=False, delay=0.01):
                # Simulate some work
                time.sleep(delay)

                # Simulate memory storage
                return [{"action": {"type": "DONE", "content": "Benchmark action"}}] if return_actions else None

            agent.act = mock_act
            agents.append(agent)

        return agents

    def benchmark_sequential_vs_parallel(
        self,
        agent_counts: List[int] = [1, 5, 10, 20],
        steps: int = 10,
        action_delay: float = 0.01
    ) -> None:
        """
        Benchmark sequential vs parallel execution across different agent counts.

        Args:
            agent_counts: List of agent counts to test
            steps: Number of steps to run
            action_delay: Simulated delay per agent action (seconds)
        """
        print("\n=== Sequential vs Parallel Benchmark ===\n")

        for agent_count in agent_counts:
            # Benchmark sequential execution
            sequential_result = self._run_benchmark(
                benchmark_name="sequential_vs_parallel",
                agent_count=agent_count,
                steps=steps,
                parallelize=False,
                action_delay=action_delay
            )

            # Benchmark parallel execution
            parallel_result = self._run_benchmark(
                benchmark_name="sequential_vs_parallel",
                agent_count=agent_count,
                steps=steps,
                parallelize=True,
                action_delay=action_delay
            )

            # Calculate speedup
            speedup = sequential_result.total_time / parallel_result.total_time
            parallel_result.speedup = speedup

            # Print results
            print(f"\nAgent Count: {agent_count}")
            print(f"  Sequential: {sequential_result.total_time:.2f}s ({sequential_result.avg_time_per_step:.3f}s/step)")
            print(f"  Parallel:   {parallel_result.total_time:.2f}s ({parallel_result.avg_time_per_step:.3f}s/step)")
            print(f"  Speedup:    {speedup:.2f}x")
            print(f"  Memory:     {parallel_result.memory_usage_mb:.1f} MB (peak: {parallel_result.peak_memory_mb:.1f} MB)")

    def benchmark_memory_usage(
        self,
        agent_count: int = 10,
        steps: int = 100,
        memory_size: int = 1000
    ) -> BenchmarkResult:
        """
        Benchmark memory usage during extended execution.

        Args:
            agent_count: Number of agents
            steps: Number of steps to run
            memory_size: Memory size per agent

        Returns:
            BenchmarkResult with memory statistics
        """
        print(f"\n=== Memory Usage Benchmark (agents={agent_count}, steps={steps}) ===\n")

        # Create world with agents
        world = TinyWorld(f"MemoryBenchWorld_{agent_count}")
        agents = self.create_mock_agents(agent_count)

        for agent in agents:
            agent.episodic_memory = EpisodicMemory(max_size=memory_size)
            world.add_agent(agent)

        # Track memory over time
        memory_samples = []
        start_memory = self.get_memory_usage()
        peak_memory = start_memory

        # Run simulation with memory tracking
        start_time = time.time()

        for step in range(steps):
            world._step_in_parallel()

            # Sample memory every 10 steps
            if step % 10 == 0:
                current_memory = self.get_memory_usage()
                memory_samples.append(current_memory)
                peak_memory = max(peak_memory, current_memory)

                print(f"  Step {step}: {current_memory:.1f} MB")

        end_time = time.time()
        final_memory = self.get_memory_usage()

        # Create result
        result = BenchmarkResult(
            benchmark_name="memory_usage",
            agent_count=agent_count,
            execution_mode="parallel",
            total_time=end_time - start_time,
            avg_time_per_step=(end_time - start_time) / steps,
            steps_completed=steps,
            memory_usage_mb=final_memory,
            peak_memory_mb=peak_memory,
            parallel_metrics={
                'start_memory_mb': start_memory,
                'memory_growth_mb': final_memory - start_memory,
                'memory_samples': memory_samples
            }
        )

        self.results.append(result)

        print(f"\n  Start:  {start_memory:.1f} MB")
        print(f"  Final:  {final_memory:.1f} MB")
        print(f"  Peak:   {peak_memory:.1f} MB")
        print(f"  Growth: {final_memory - start_memory:.1f} MB")

        return result

    def benchmark_llm_call_patterns(
        self,
        agent_count: int = 5,
        steps: int = 20
    ) -> BenchmarkResult:
        """
        Profile LLM call patterns and timing.

        Args:
            agent_count: Number of agents
            steps: Number of steps

        Returns:
            BenchmarkResult with LLM call statistics
        """
        print(f"\n=== LLM Call Pattern Benchmark (agents={agent_count}, steps={steps}) ===\n")

        # Track call timing
        call_times = []

        def timed_mock_act(return_actions=False):
            start = time.time()
            # Simulate variable LLM latency (50-200ms)
            import random
            latency = random.uniform(0.05, 0.2)
            time.sleep(latency)
            duration = time.time() - start
            call_times.append(duration)
            return [{"action": {"type": "DONE"}}] if return_actions else None

        # Create world
        world = TinyWorld(f"LLMBenchWorld_{agent_count}")
        agents = self.create_mock_agents(agent_count)

        for agent in agents:
            agent.act = timed_mock_act
            world.add_agent(agent)

        # Run simulation
        start_time = time.time()

        for step in range(steps):
            world._step_in_parallel()

        end_time = time.time()

        # Analyze call patterns
        total_calls = len(call_times)
        avg_call_time = sum(call_times) / total_calls if total_calls > 0 else 0
        min_call_time = min(call_times) if call_times else 0
        max_call_time = max(call_times) if call_times else 0

        result = BenchmarkResult(
            benchmark_name="llm_call_patterns",
            agent_count=agent_count,
            execution_mode="parallel",
            total_time=end_time - start_time,
            avg_time_per_step=(end_time - start_time) / steps,
            steps_completed=steps,
            memory_usage_mb=self.get_memory_usage(),
            peak_memory_mb=self.get_memory_usage(),
            parallel_metrics={
                'total_calls': total_calls,
                'avg_call_time': avg_call_time,
                'min_call_time': min_call_time,
                'max_call_time': max_call_time,
                'calls_per_step': total_calls / steps if steps > 0 else 0
            }
        )

        self.results.append(result)

        print(f"  Total calls: {total_calls}")
        print(f"  Avg time:    {avg_call_time*1000:.1f} ms")
        print(f"  Min time:    {min_call_time*1000:.1f} ms")
        print(f"  Max time:    {max_call_time*1000:.1f} ms")
        print(f"  Calls/step:  {total_calls/steps:.1f}")

        return result

    def benchmark_scalability(
        self,
        min_agents: int = 1,
        max_agents: int = 50,
        step_size: int = 5,
        steps: int = 10
    ) -> List[BenchmarkResult]:
        """
        Benchmark scalability across increasing agent counts.

        Args:
            min_agents: Minimum number of agents
            max_agents: Maximum number of agents
            step_size: Increment between tests
            steps: Number of steps per test

        Returns:
            List of BenchmarkResults
        """
        print(f"\n=== Scalability Benchmark ({min_agents}-{max_agents} agents) ===\n")

        results = []
        agent_counts = range(min_agents, max_agents + 1, step_size)

        for agent_count in agent_counts:
            result = self._run_benchmark(
                benchmark_name="scalability",
                agent_count=agent_count,
                steps=steps,
                parallelize=True,
                action_delay=0.01
            )

            results.append(result)

            print(f"  Agents: {agent_count:3d} | Time: {result.total_time:6.2f}s | "
                  f"Avg: {result.avg_time_per_step:6.3f}s/step | "
                  f"Memory: {result.memory_usage_mb:6.1f} MB")

        return results

    def _run_benchmark(
        self,
        benchmark_name: str,
        agent_count: int,
        steps: int,
        parallelize: bool,
        action_delay: float = 0.01
    ) -> BenchmarkResult:
        """
        Run a single benchmark scenario.

        Args:
            benchmark_name: Name of the benchmark
            agent_count: Number of agents
            steps: Number of steps
            parallelize: Whether to use parallel execution
            action_delay: Simulated action delay

        Returns:
            BenchmarkResult
        """
        # Create world
        world = TinyWorld(f"BenchWorld_{agent_count}_{parallelize}")
        agents = self.create_mock_agents(agent_count)

        for agent in agents:
            # Create mock with delay
            def make_mock_act(delay):
                def mock_act(return_actions=False):
                    time.sleep(delay)
                    return [{"action": {"type": "DONE"}}] if return_actions else None
                return mock_act

            agent.act = make_mock_act(action_delay)
            world.add_agent(agent)

        # Track memory
        start_memory = self.get_memory_usage()
        peak_memory = start_memory

        # Run simulation
        start_time = time.time()

        for step in range(steps):
            if parallelize:
                world._step_in_parallel()
            else:
                world._step_sequentially()

            # Track peak memory
            current_memory = self.get_memory_usage()
            peak_memory = max(peak_memory, current_memory)

        end_time = time.time()
        final_memory = self.get_memory_usage()

        # Get parallel metrics if applicable
        parallel_metrics = None
        if parallelize:
            parallel_metrics = world.get_parallel_metrics()

        # Create result
        result = BenchmarkResult(
            benchmark_name=benchmark_name,
            agent_count=agent_count,
            execution_mode="parallel" if parallelize else "sequential",
            total_time=end_time - start_time,
            avg_time_per_step=(end_time - start_time) / steps,
            steps_completed=steps,
            memory_usage_mb=final_memory,
            peak_memory_mb=peak_memory,
            parallel_metrics=parallel_metrics
        )

        self.results.append(result)
        return result

    def export_results(self, filename: str = "benchmark_results.json") -> None:
        """
        Export benchmark results to JSON file.

        Args:
            filename: Output filename
        """
        with open(filename, 'w') as f:
            json.dump([r.to_dict() for r in self.results], f, indent=2)

        print(f"\n✅ Results exported to {filename}")

    def print_summary(self) -> None:
        """Print summary of all benchmark results."""
        if not self.results:
            print("No benchmark results to summarize.")
            return

        print("\n" + "=" * 80)
        print("BENCHMARK SUMMARY")
        print("=" * 80)

        # Group by benchmark name
        by_benchmark = {}
        for result in self.results:
            if result.benchmark_name not in by_benchmark:
                by_benchmark[result.benchmark_name] = []
            by_benchmark[result.benchmark_name].append(result)

        for benchmark_name, results in by_benchmark.items():
            print(f"\n{benchmark_name.upper()}")
            print("-" * 80)

            for result in results:
                print(f"  Agents: {result.agent_count:3d} | "
                      f"Mode: {result.execution_mode:10s} | "
                      f"Time: {result.total_time:6.2f}s | "
                      f"Memory: {result.memory_usage_mb:6.1f} MB")

                if result.speedup:
                    print(f"    Speedup: {result.speedup:.2f}x")

        print("\n" + "=" * 80)


def run_all_benchmarks():
    """Run all benchmarks in the suite."""
    benchmark = PerformanceBenchmark()

    print("\n" + "=" * 80)
    print("TINYTROUPE PERFORMANCE BENCHMARK SUITE")
    print("=" * 80)

    # Run benchmarks
    benchmark.benchmark_sequential_vs_parallel(
        agent_counts=[1, 5, 10, 20],
        steps=10,
        action_delay=0.01
    )

    benchmark.benchmark_memory_usage(
        agent_count=10,
        steps=100,
        memory_size=1000
    )

    benchmark.benchmark_llm_call_patterns(
        agent_count=5,
        steps=20
    )

    benchmark.benchmark_scalability(
        min_agents=1,
        max_agents=25,
        step_size=5,
        steps=10
    )

    # Print summary
    benchmark.print_summary()

    # Export results
    benchmark.export_results("benchmark_results.json")

    return benchmark


if __name__ == "__main__":
    run_all_benchmarks()
