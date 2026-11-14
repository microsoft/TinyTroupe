"""
Memory monitoring and alerting utilities for TinyTroupe agents.

This module provides tools to monitor memory usage, detect abnormal growth,
and generate alerts when memory thresholds are exceeded.
"""

import logging
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from datetime import datetime
import time
import functools

logger = logging.getLogger("tinytroupe")


@dataclass
class MemoryAlert:
    """
    Represents a memory usage alert.

    Attributes:
        timestamp: When the alert was triggered
        agent_name: Name of the agent that triggered the alert
        alert_type: Type of alert (e.g., 'threshold_exceeded', 'abnormal_growth', 'consolidation_needed')
        severity: Alert severity ('info', 'warning', 'critical')
        message: Human-readable alert message
        memory_stats: Memory statistics at time of alert
    """
    timestamp: datetime
    agent_name: str
    alert_type: str
    severity: str  # 'info', 'warning', 'critical'
    message: str
    memory_stats: Dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        return f"[{self.severity.upper()}] {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')} - {self.agent_name}: {self.message}"


class MemoryMonitor:
    """
    Monitors memory usage for TinyPerson agents and generates alerts.

    Can track:
    - Memory size over time
    - Consolidation frequency and effectiveness
    - Abnormal memory growth patterns
    - Memory usage trends

    Example:
        >>> monitor = MemoryMonitor()
        >>> monitor.track_agent(agent)
        >>> stats = monitor.get_agent_stats(agent.name)
        >>> alerts = monitor.get_alerts()
    """

    def __init__(self,
                 alert_threshold: float = 0.8,
                 growth_rate_threshold: float = 2.0,
                 consolidation_frequency_threshold: int = 100):
        """
        Initialize the memory monitor.

        Args:
            alert_threshold: Memory usage ratio that triggers alerts (default: 0.8 = 80%)
            growth_rate_threshold: Memory growth rate that triggers alerts (default: 2.0 = 200%)
            consolidation_frequency_threshold: Minimum memories between consolidations before alert
        """
        self.alert_threshold = alert_threshold
        self.growth_rate_threshold = growth_rate_threshold
        self.consolidation_frequency_threshold = consolidation_frequency_threshold

        # Tracking data
        self.agent_history: Dict[str, List[Dict]] = {}  # agent_name -> list of snapshots
        self.alerts: List[MemoryAlert] = []
        self.alert_callbacks: List[Callable[[MemoryAlert], None]] = []

    def track_agent(self, agent) -> None:
        """
        Start tracking an agent's memory usage.

        Args:
            agent: TinyPerson agent to track
        """
        if agent.name not in self.agent_history:
            self.agent_history[agent.name] = []
            logger.info(f"MemoryMonitor: Started tracking agent '{agent.name}'")

    def record_snapshot(self, agent) -> Dict[str, Any]:
        """
        Record a snapshot of the agent's current memory state.

        Args:
            agent: TinyPerson agent to snapshot

        Returns:
            Dictionary containing the snapshot data
        """
        self.track_agent(agent)

        # Get current memory stats
        memory_stats = agent.episodic_memory.get_memory_stats()
        consolidation_metrics = agent.get_consolidation_metrics()

        snapshot = {
            'timestamp': datetime.now(),
            'memory_stats': memory_stats,
            'consolidation_metrics': consolidation_metrics,
            'episode_count': agent._current_episode_event_count if hasattr(agent, '_current_episode_event_count') else 0
        }

        self.agent_history[agent.name].append(snapshot)

        # Check for alerts
        self._check_alerts(agent.name, snapshot)

        return snapshot

    def _check_alerts(self, agent_name: str, snapshot: Dict[str, Any]) -> None:
        """
        Check if any alerts should be triggered based on the snapshot.

        Args:
            agent_name: Name of the agent
            snapshot: Current memory snapshot
        """
        memory_stats = snapshot['memory_stats']

        # Check memory threshold
        if memory_stats['usage_ratio'] is not None:
            if memory_stats['usage_ratio'] >= self.alert_threshold:
                self._trigger_alert(
                    agent_name=agent_name,
                    alert_type='threshold_exceeded',
                    severity='warning',
                    message=f"Memory usage at {memory_stats['usage_ratio']:.1%} (threshold: {self.alert_threshold:.1%})",
                    memory_stats=memory_stats
                )

        # Check for abnormal growth
        if len(self.agent_history[agent_name]) >= 2:
            prev_snapshot = self.agent_history[agent_name][-2]
            growth_rate = self._calculate_growth_rate(prev_snapshot, snapshot)

            if growth_rate > self.growth_rate_threshold:
                self._trigger_alert(
                    agent_name=agent_name,
                    alert_type='abnormal_growth',
                    severity='warning',
                    message=f"Abnormal memory growth detected: {growth_rate:.1f}x increase",
                    memory_stats=memory_stats
                )

        # Check consolidation effectiveness
        consolidation_metrics = snapshot['consolidation_metrics']
        if consolidation_metrics['total_consolidations'] > 0:
            avg_size = consolidation_metrics['average_consolidation_size']
            if avg_size > self.consolidation_frequency_threshold:
                self._trigger_alert(
                    agent_name=agent_name,
                    alert_type='consolidation_inefficient',
                    severity='info',
                    message=f"Large average consolidation size: {avg_size:.0f} memories",
                    memory_stats=memory_stats
                )

    def _calculate_growth_rate(self, prev_snapshot: Dict, current_snapshot: Dict) -> float:
        """
        Calculate memory growth rate between two snapshots.

        Args:
            prev_snapshot: Previous memory snapshot
            current_snapshot: Current memory snapshot

        Returns:
            Growth rate as a multiplier (e.g., 2.0 = 200% increase)
        """
        prev_size = prev_snapshot['memory_stats']['total_size']
        current_size = current_snapshot['memory_stats']['total_size']

        if prev_size == 0:
            return float('inf') if current_size > 0 else 0.0

        return current_size / prev_size

    def _trigger_alert(self, agent_name: str, alert_type: str, severity: str,
                      message: str, memory_stats: Dict) -> None:
        """
        Trigger a memory alert.

        Args:
            agent_name: Name of the agent
            alert_type: Type of alert
            severity: Alert severity level
            message: Alert message
            memory_stats: Memory statistics
        """
        alert = MemoryAlert(
            timestamp=datetime.now(),
            agent_name=agent_name,
            alert_type=alert_type,
            severity=severity,
            message=message,
            memory_stats=memory_stats.copy()
        )

        self.alerts.append(alert)
        logger.log(
            logging.WARNING if severity == 'warning' else logging.INFO,
            f"MemoryAlert: {alert}"
        )

        # Call registered callbacks
        for callback in self.alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                logger.error(f"Error in alert callback: {e}")

    def register_alert_callback(self, callback: Callable[[MemoryAlert], None]) -> None:
        """
        Register a callback function to be called when alerts are triggered.

        Args:
            callback: Function that takes a MemoryAlert as parameter
        """
        self.alert_callbacks.append(callback)

    def get_agent_stats(self, agent_name: str) -> Dict[str, Any]:
        """
        Get comprehensive statistics for an agent.

        Args:
            agent_name: Name of the agent

        Returns:
            Dictionary containing agent statistics
        """
        if agent_name not in self.agent_history:
            return {}

        history = self.agent_history[agent_name]
        if not history:
            return {}

        latest = history[-1]

        # Calculate trends
        memory_trend = self._calculate_trend([s['memory_stats']['total_size'] for s in history])
        consolidation_count = latest['consolidation_metrics']['total_consolidations']

        return {
            'agent_name': agent_name,
            'snapshots_count': len(history),
            'current_memory': latest['memory_stats'],
            'current_consolidation': latest['consolidation_metrics'],
            'memory_trend': memory_trend,
            'first_snapshot': history[0]['timestamp'],
            'last_snapshot': history[-1]['timestamp'],
            'total_alerts': len([a for a in self.alerts if a.agent_name == agent_name])
        }

    def _calculate_trend(self, values: List[float]) -> str:
        """
        Calculate trend direction from a list of values.

        Args:
            values: List of numeric values

        Returns:
            Trend direction: 'increasing', 'decreasing', 'stable'
        """
        if len(values) < 2:
            return 'stable'

        # Simple linear trend
        diffs = [values[i] - values[i-1] for i in range(1, len(values))]
        avg_diff = sum(diffs) / len(diffs)

        if avg_diff > 0.1:
            return 'increasing'
        elif avg_diff < -0.1:
            return 'decreasing'
        else:
            return 'stable'

    def get_alerts(self, agent_name: Optional[str] = None,
                   severity: Optional[str] = None) -> List[MemoryAlert]:
        """
        Get alerts, optionally filtered by agent and/or severity.

        Args:
            agent_name: Filter by agent name (optional)
            severity: Filter by severity level (optional)

        Returns:
            List of MemoryAlert objects
        """
        alerts = self.alerts

        if agent_name:
            alerts = [a for a in alerts if a.agent_name == agent_name]

        if severity:
            alerts = [a for a in alerts if a.severity == severity]

        return alerts

    def clear_alerts(self, agent_name: Optional[str] = None) -> None:
        """
        Clear alerts, optionally for a specific agent.

        Args:
            agent_name: Clear alerts for specific agent (optional)
        """
        if agent_name:
            self.alerts = [a for a in self.alerts if a.agent_name != agent_name]
        else:
            self.alerts = []

    def generate_report(self, agent_name: Optional[str] = None) -> str:
        """
        Generate a text report of memory monitoring data.

        Args:
            agent_name: Generate report for specific agent (optional)

        Returns:
            Formatted text report
        """
        lines = ["=" * 60, "Memory Monitoring Report", "=" * 60, ""]

        agents_to_report = [agent_name] if agent_name else list(self.agent_history.keys())

        for name in agents_to_report:
            stats = self.get_agent_stats(name)
            if not stats:
                continue

            lines.append(f"Agent: {name}")
            lines.append("-" * 40)
            lines.append(f"Snapshots: {stats['snapshots_count']}")
            lines.append(f"Memory Trend: {stats['memory_trend']}")
            lines.append(f"Current Memory: {stats['current_memory']['total_size']} / {stats['current_memory']['max_size']}")
            lines.append(f"Usage: {stats['current_memory']['usage_ratio']:.1%}" if stats['current_memory']['usage_ratio'] else "Usage: Unbounded")
            lines.append(f"Consolidations: {stats['current_consolidation']['total_consolidations']}")
            lines.append(f"  - Automatic: {stats['current_consolidation']['automatic_consolidations']}")
            lines.append(f"  - Manual: {stats['current_consolidation']['manual_consolidations']}")
            lines.append(f"Alerts: {stats['total_alerts']}")
            lines.append("")

        # Add alerts summary
        if self.alerts:
            lines.append("Recent Alerts:")
            lines.append("-" * 40)
            for alert in self.alerts[-5:]:  # Last 5 alerts
                lines.append(str(alert))
            lines.append("")

        lines.append("=" * 60)

        return "\n".join(lines)


class MemoryProfiler:
    """
    Decorator-based profiler for memory operations.

    Usage:
        >>> profiler = MemoryProfiler()
        >>>
        >>> @profiler.profile
        >>> def my_function(agent):
        >>>     agent.store_in_memory(...)
        >>>
        >>> profiler.print_stats()
    """

    def __init__(self):
        """Initialize the profiler."""
        self.profile_data: Dict[str, List[float]] = {}
        self.call_counts: Dict[str, int] = {}

    def profile(self, func: Callable) -> Callable:
        """
        Decorator to profile a function's execution time.

        Args:
            func: Function to profile

        Returns:
            Wrapped function
        """
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            duration = time.time() - start_time

            func_name = func.__name__
            if func_name not in self.profile_data:
                self.profile_data[func_name] = []
                self.call_counts[func_name] = 0

            self.profile_data[func_name].append(duration)
            self.call_counts[func_name] += 1

            return result

        return wrapper

    def get_stats(self, func_name: str) -> Dict[str, float]:
        """
        Get profiling statistics for a function.

        Args:
            func_name: Name of the function

        Returns:
            Dictionary with min, max, avg, total times and call count
        """
        if func_name not in self.profile_data:
            return {}

        times = self.profile_data[func_name]

        return {
            'calls': self.call_counts[func_name],
            'total_time': sum(times),
            'avg_time': sum(times) / len(times),
            'min_time': min(times),
            'max_time': max(times)
        }

    def print_stats(self) -> None:
        """Print profiling statistics for all profiled functions."""
        print("\n" + "=" * 60)
        print("Memory Profiling Statistics")
        print("=" * 60)

        for func_name in sorted(self.profile_data.keys()):
            stats = self.get_stats(func_name)
            print(f"\n{func_name}:")
            print(f"  Calls: {stats['calls']}")
            print(f"  Total Time: {stats['total_time']:.4f}s")
            print(f"  Avg Time: {stats['avg_time']:.4f}s")
            print(f"  Min Time: {stats['min_time']:.4f}s")
            print(f"  Max Time: {stats['max_time']:.4f}s")

        print("\n" + "=" * 60)

    def clear(self) -> None:
        """Clear all profiling data."""
        self.profile_data.clear()
        self.call_counts.clear()
