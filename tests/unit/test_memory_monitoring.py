"""
Tests for memory monitoring and visualization utilities.

This module tests the MemoryMonitor, MemoryAlert, and MemoryVisualizer classes.
"""
import pytest
import sys
sys.path.insert(0, '../../tinytroupe/')
sys.path.insert(0, '../../')
sys.path.insert(0, '..')

from tinytroupe.monitoring import MemoryMonitor, MemoryAlert, MemoryProfiler
from tinytroupe.visualization import MemoryVisualizer
from tinytroupe.agent.memory import EpisodicMemory
from unittest.mock import Mock, MagicMock
from datetime import datetime
import time


class TestMemoryAlert:
    """Test suite for MemoryAlert dataclass."""

    def test_alert_creation(self, setup):
        """Test that MemoryAlert can be created with proper fields."""
        alert = MemoryAlert(
            timestamp=datetime.now(),
            agent_name="TestAgent",
            alert_type="threshold_exceeded",
            severity="warning",
            message="Memory at 85%",
            memory_stats={'current_size': 850, 'max_size': 1000}
        )

        assert alert.agent_name == "TestAgent"
        assert alert.alert_type == "threshold_exceeded"
        assert alert.severity == "warning"
        assert "Memory at 85%" in alert.message

    def test_alert_string_representation(self, setup):
        """Test that MemoryAlert has proper string representation."""
        alert = MemoryAlert(
            timestamp=datetime.now(),
            agent_name="TestAgent",
            alert_type="threshold_exceeded",
            severity="warning",
            message="Memory at 85%"
        )

        alert_str = str(alert)
        assert "WARNING" in alert_str
        assert "TestAgent" in alert_str
        assert "Memory at 85%" in alert_str


class TestMemoryMonitor:
    """Test suite for MemoryMonitor class."""

    def test_monitor_initialization(self, setup):
        """Test that MemoryMonitor initializes with correct defaults."""
        monitor = MemoryMonitor()

        assert monitor.alert_threshold == 0.8
        assert monitor.growth_rate_threshold == 2.0
        assert len(monitor.agent_history) == 0
        assert len(monitor.alerts) == 0

    def test_monitor_custom_thresholds(self, setup):
        """Test that MemoryMonitor accepts custom thresholds."""
        monitor = MemoryMonitor(
            alert_threshold=0.9,
            growth_rate_threshold=3.0,
            consolidation_frequency_threshold=200
        )

        assert monitor.alert_threshold == 0.9
        assert monitor.growth_rate_threshold == 3.0
        assert monitor.consolidation_frequency_threshold == 200

    def test_track_agent(self, setup):
        """Test that track_agent initializes tracking for an agent."""
        monitor = MemoryMonitor()
        mock_agent = Mock()
        mock_agent.name = "TestAgent"

        monitor.track_agent(mock_agent)

        assert "TestAgent" in monitor.agent_history
        assert len(monitor.agent_history["TestAgent"]) == 0

    def test_record_snapshot(self, setup):
        """Test that record_snapshot captures agent state."""
        monitor = MemoryMonitor()

        # Create mock agent with memory and consolidation metrics
        mock_agent = Mock()
        mock_agent.name = "TestAgent"
        mock_agent._current_episode_event_count = 10

        # Mock episodic memory
        mock_memory = Mock()
        mock_memory.get_memory_stats.return_value = {
            'current_size': 50,
            'buffer_size': 10,
            'total_size': 60,
            'max_size': 100,
            'usage_ratio': 0.5,
            'is_bounded': True,
            'approaching_limit': False
        }
        mock_agent.episodic_memory = mock_memory

        # Mock consolidation metrics
        mock_agent.get_consolidation_metrics.return_value = {
            'total_consolidations': 2,
            'automatic_consolidations': 1,
            'manual_consolidations': 1,
            'total_memories_consolidated': 100,
            'average_consolidation_size': 50.0
        }

        snapshot = monitor.record_snapshot(mock_agent)

        assert snapshot is not None
        assert 'timestamp' in snapshot
        assert 'memory_stats' in snapshot
        assert 'consolidation_metrics' in snapshot
        assert len(monitor.agent_history["TestAgent"]) == 1

    def test_threshold_alert_triggered(self, setup):
        """Test that alert is triggered when memory threshold is exceeded."""
        monitor = MemoryMonitor(alert_threshold=0.7)

        mock_agent = Mock()
        mock_agent.name = "TestAgent"
        mock_agent._current_episode_event_count = 10

        mock_memory = Mock()
        mock_memory.get_memory_stats.return_value = {
            'current_size': 80,
            'buffer_size': 0,
            'total_size': 80,
            'max_size': 100,
            'usage_ratio': 0.8,  # Above threshold of 0.7
            'is_bounded': True,
            'approaching_limit': True
        }
        mock_agent.episodic_memory = mock_memory

        mock_agent.get_consolidation_metrics.return_value = {
            'total_consolidations': 0,
            'automatic_consolidations': 0,
            'manual_consolidations': 0,
            'total_memories_consolidated': 0,
            'average_consolidation_size': 0.0
        }

        monitor.record_snapshot(mock_agent)

        # Check that alert was triggered
        assert len(monitor.alerts) > 0
        alert = monitor.alerts[0]
        assert alert.agent_name == "TestAgent"
        assert alert.alert_type == "threshold_exceeded"
        assert alert.severity == "warning"

    def test_abnormal_growth_detection(self, setup):
        """Test that abnormal memory growth triggers alert."""
        monitor = MemoryMonitor(growth_rate_threshold=1.5)

        mock_agent = Mock()
        mock_agent.name = "TestAgent"
        mock_agent._current_episode_event_count = 10

        # First snapshot
        mock_memory = Mock()
        mock_memory.get_memory_stats.return_value = {
            'current_size': 50,
            'buffer_size': 0,
            'total_size': 50,
            'max_size': 100,
            'usage_ratio': 0.5,
            'is_bounded': True,
            'approaching_limit': False
        }
        mock_agent.episodic_memory = mock_memory
        mock_agent.get_consolidation_metrics.return_value = {
            'total_consolidations': 0,
            'automatic_consolidations': 0,
            'manual_consolidations': 0,
            'total_memories_consolidated': 0,
            'average_consolidation_size': 0.0
        }

        monitor.record_snapshot(mock_agent)

        # Second snapshot with 2x growth
        mock_memory.get_memory_stats.return_value = {
            'current_size': 100,
            'buffer_size': 0,
            'total_size': 100,  # 2x growth from 50
            'max_size': 100,
            'usage_ratio': 1.0,
            'is_bounded': True,
            'approaching_limit': True
        }

        monitor.record_snapshot(mock_agent)

        # Check for abnormal growth alert
        growth_alerts = [a for a in monitor.alerts if a.alert_type == "abnormal_growth"]
        assert len(growth_alerts) > 0

    def test_get_agent_stats(self, setup):
        """Test that get_agent_stats returns comprehensive statistics."""
        monitor = MemoryMonitor()

        mock_agent = Mock()
        mock_agent.name = "TestAgent"
        mock_agent._current_episode_event_count = 10

        mock_memory = Mock()
        mock_memory.get_memory_stats.return_value = {
            'current_size': 50,
            'buffer_size': 10,
            'total_size': 60,
            'max_size': 100,
            'usage_ratio': 0.5,
            'is_bounded': True,
            'approaching_limit': False
        }
        mock_agent.episodic_memory = mock_memory

        mock_agent.get_consolidation_metrics.return_value = {
            'total_consolidations': 2,
            'automatic_consolidations': 1,
            'manual_consolidations': 1,
            'total_memories_consolidated': 100,
            'average_consolidation_size': 50.0
        }

        # Record a few snapshots
        for _ in range(3):
            monitor.record_snapshot(mock_agent)
            time.sleep(0.01)  # Small delay to ensure different timestamps

        stats = monitor.get_agent_stats("TestAgent")

        assert stats['agent_name'] == "TestAgent"
        assert stats['snapshots_count'] == 3
        assert 'current_memory' in stats
        assert 'current_consolidation' in stats
        assert stats['memory_trend'] in ['increasing', 'decreasing', 'stable']

    def test_alert_callbacks(self, setup):
        """Test that alert callbacks are triggered."""
        monitor = MemoryMonitor(alert_threshold=0.5)

        callback_called = {'count': 0, 'alert': None}

        def test_callback(alert):
            callback_called['count'] += 1
            callback_called['alert'] = alert

        monitor.register_alert_callback(test_callback)

        # Trigger an alert
        mock_agent = Mock()
        mock_agent.name = "TestAgent"
        mock_agent._current_episode_event_count = 10

        mock_memory = Mock()
        mock_memory.get_memory_stats.return_value = {
            'current_size': 60,
            'buffer_size': 0,
            'total_size': 60,
            'max_size': 100,
            'usage_ratio': 0.6,  # Above threshold
            'is_bounded': True,
            'approaching_limit': False
        }
        mock_agent.episodic_memory = mock_memory

        mock_agent.get_consolidation_metrics.return_value = {
            'total_consolidations': 0,
            'automatic_consolidations': 0,
            'manual_consolidations': 0,
            'total_memories_consolidated': 0,
            'average_consolidation_size': 0.0
        }

        monitor.record_snapshot(mock_agent)

        assert callback_called['count'] > 0
        assert callback_called['alert'] is not None

    def test_generate_report(self, setup):
        """Test that generate_report produces a text report."""
        monitor = MemoryMonitor()

        mock_agent = Mock()
        mock_agent.name = "TestAgent"
        mock_agent._current_episode_event_count = 10

        mock_memory = Mock()
        mock_memory.get_memory_stats.return_value = {
            'current_size': 50,
            'buffer_size': 10,
            'total_size': 60,
            'max_size': 100,
            'usage_ratio': 0.5,
            'is_bounded': True,
            'approaching_limit': False
        }
        mock_agent.episodic_memory = mock_memory

        mock_agent.get_consolidation_metrics.return_value = {
            'total_consolidations': 2,
            'automatic_consolidations': 1,
            'manual_consolidations': 1,
            'total_memories_consolidated': 100,
            'average_consolidation_size': 50.0
        }

        monitor.record_snapshot(mock_agent)

        report = monitor.generate_report("TestAgent")

        assert "Memory Monitoring Report" in report
        assert "TestAgent" in report
        assert "50 / 100" in report  # Memory usage


class TestMemoryProfiler:
    """Test suite for MemoryProfiler class."""

    def test_profiler_initialization(self, setup):
        """Test that MemoryProfiler initializes correctly."""
        profiler = MemoryProfiler()

        assert len(profiler.profile_data) == 0
        assert len(profiler.call_counts) == 0

    def test_profile_decorator(self, setup):
        """Test that @profile decorator tracks function execution."""
        profiler = MemoryProfiler()

        @profiler.profile
        def test_function():
            time.sleep(0.01)
            return "result"

        # Call function multiple times
        for _ in range(3):
            result = test_function()
            assert result == "result"

        stats = profiler.get_stats("test_function")

        assert stats['calls'] == 3
        assert stats['total_time'] > 0
        assert stats['avg_time'] > 0
        assert stats['min_time'] > 0
        assert stats['max_time'] > 0

    def test_profiler_clear(self, setup):
        """Test that profiler can be cleared."""
        profiler = MemoryProfiler()

        @profiler.profile
        def test_function():
            pass

        test_function()
        assert len(profiler.profile_data) > 0

        profiler.clear()
        assert len(profiler.profile_data) == 0
        assert len(profiler.call_counts) == 0


class TestMemoryVisualizer:
    """Test suite for MemoryVisualizer class."""

    def test_visualizer_initialization(self, setup):
        """Test that MemoryVisualizer initializes correctly."""
        viz = MemoryVisualizer()
        assert viz.monitor is None

        monitor = MemoryMonitor()
        viz_with_monitor = MemoryVisualizer(monitor)
        assert viz_with_monitor.monitor == monitor

    def test_prepare_memory_timeline_data(self, setup):
        """Test timeline data preparation."""
        monitor = MemoryMonitor()
        viz = MemoryVisualizer(monitor)

        mock_agent = Mock()
        mock_agent.name = "TestAgent"
        mock_agent._current_episode_event_count = 10

        mock_memory = Mock()
        mock_memory.get_memory_stats.return_value = {
            'current_size': 50,
            'buffer_size': 10,
            'total_size': 60,
            'max_size': 100,
            'usage_ratio': 0.5,
            'is_bounded': True,
            'approaching_limit': False
        }
        mock_agent.episodic_memory = mock_memory

        mock_agent.get_consolidation_metrics.return_value = {
            'total_consolidations': 0,
            'automatic_consolidations': 0,
            'manual_consolidations': 0,
            'total_memories_consolidated': 0,
            'average_consolidation_size': 0.0
        }

        # Record some snapshots
        for _ in range(3):
            monitor.record_snapshot(mock_agent)
            time.sleep(0.01)

        timeline_data = viz.prepare_memory_timeline_data("TestAgent")

        assert 'timestamps' in timeline_data
        assert 'memory_size' in timeline_data
        assert 'buffer_size' in timeline_data
        assert 'usage_ratio' in timeline_data
        assert len(timeline_data['timestamps']) == 3

    def test_export_data_json(self, setup):
        """Test JSON export functionality."""
        monitor = MemoryMonitor()
        viz = MemoryVisualizer(monitor)

        mock_agent = Mock()
        mock_agent.name = "TestAgent"
        mock_agent._current_episode_event_count = 10

        mock_memory = Mock()
        mock_memory.get_memory_stats.return_value = {
            'current_size': 50,
            'buffer_size': 10,
            'total_size': 60,
            'max_size': 100,
            'usage_ratio': 0.5,
            'is_bounded': True,
            'approaching_limit': False
        }
        mock_agent.episodic_memory = mock_memory

        mock_agent.get_consolidation_metrics.return_value = {
            'total_consolidations': 0,
            'automatic_consolidations': 0,
            'manual_consolidations': 0,
            'total_memories_consolidated': 0,
            'average_consolidation_size': 0.0
        }

        monitor.record_snapshot(mock_agent)

        json_data = viz.export_data_json("TestAgent")

        assert isinstance(json_data, str)
        assert "TestAgent" in json_data
        assert "generated_at" in json_data

    def test_ascii_chart_generation(self, setup):
        """Test ASCII chart generation."""
        monitor = MemoryMonitor()
        viz = MemoryVisualizer(monitor)

        mock_agent = Mock()
        mock_agent.name = "TestAgent"
        mock_agent._current_episode_event_count = 10

        mock_memory = Mock()
        mock_memory.get_memory_stats.return_value = {
            'current_size': 50,
            'buffer_size': 10,
            'total_size': 60,
            'max_size': 100,
            'usage_ratio': 0.5,
            'is_bounded': True,
            'approaching_limit': False
        }
        mock_agent.episodic_memory = mock_memory

        mock_agent.get_consolidation_metrics.return_value = {
            'total_consolidations': 0,
            'automatic_consolidations': 0,
            'manual_consolidations': 0,
            'total_memories_consolidated': 0,
            'average_consolidation_size': 0.0
        }

        # Record some snapshots
        for i in range(10):
            monitor.record_snapshot(mock_agent)
            time.sleep(0.01)

        chart = viz.print_ascii_chart("TestAgent", metric='memory_size')

        assert "Memory Memory Size - TestAgent" in chart
        assert "data points" in chart


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
