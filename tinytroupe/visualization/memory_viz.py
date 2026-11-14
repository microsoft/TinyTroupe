"""
Memory visualization utilities for TinyTroupe.

Provides tools to visualize memory usage patterns, consolidation effectiveness,
and other memory-related metrics.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import json


class MemoryVisualizer:
    """
    Visualizes memory usage and consolidation patterns for TinyPerson agents.

    Can generate:
    - Memory usage over time charts
    - Consolidation effectiveness visualizations
    - Memory growth trend graphs
    - Alert timeline visualizations

    Note: This implementation provides data preparation. For actual plotting,
    integrate with matplotlib, plotly, or other visualization libraries.

    Example:
        >>> from tinytroupe.monitoring import MemoryMonitor
        >>> from tinytroupe.visualization import MemoryVisualizer
        >>>
        >>> monitor = MemoryMonitor()
        >>> monitor.record_snapshot(agent)
        >>>
        >>> viz = MemoryVisualizer(monitor)
        >>> chart_data = viz.prepare_memory_timeline_data(agent.name)
    """

    def __init__(self, memory_monitor=None):
        """
        Initialize the visualizer.

        Args:
            memory_monitor: MemoryMonitor instance to visualize data from
        """
        self.monitor = memory_monitor

    def prepare_memory_timeline_data(self, agent_name: str) -> Dict[str, List]:
        """
        Prepare data for memory usage timeline visualization.

        Args:
            agent_name: Name of the agent

        Returns:
            Dictionary with 'timestamps', 'memory_size', 'buffer_size', 'usage_ratio'
        """
        if not self.monitor or agent_name not in self.monitor.agent_history:
            return {'timestamps': [], 'memory_size': [], 'buffer_size': [], 'usage_ratio': []}

        history = self.monitor.agent_history[agent_name]

        data = {
            'timestamps': [],
            'memory_size': [],
            'buffer_size': [],
            'usage_ratio': []
        }

        for snapshot in history:
            stats = snapshot['memory_stats']
            data['timestamps'].append(snapshot['timestamp'])
            data['memory_size'].append(stats['current_size'])
            data['buffer_size'].append(stats['buffer_size'])
            data['usage_ratio'].append(stats['usage_ratio'] if stats['usage_ratio'] else 0)

        return data

    def prepare_consolidation_data(self, agent_name: str) -> Dict[str, Any]:
        """
        Prepare data for consolidation visualization.

        Args:
            agent_name: Name of the agent

        Returns:
            Dictionary with consolidation metrics over time
        """
        if not self.monitor or agent_name not in self.monitor.agent_history:
            return {}

        history = self.monitor.agent_history[agent_name]

        data = {
            'timestamps': [],
            'total_consolidations': [],
            'automatic_consolidations': [],
            'manual_consolidations': [],
            'average_size': []
        }

        for snapshot in history:
            metrics = snapshot['consolidation_metrics']
            data['timestamps'].append(snapshot['timestamp'])
            data['total_consolidations'].append(metrics['total_consolidations'])
            data['automatic_consolidations'].append(metrics['automatic_consolidations'])
            data['manual_consolidations'].append(metrics['manual_consolidations'])
            data['average_size'].append(metrics['average_consolidation_size'])

        return data

    def prepare_alert_timeline_data(self, agent_name: Optional[str] = None) -> Dict[str, List]:
        """
        Prepare data for alert timeline visualization.

        Args:
            agent_name: Filter by agent name (optional)

        Returns:
            Dictionary with alert data grouped by severity
        """
        if not self.monitor:
            return {}

        alerts = self.monitor.get_alerts(agent_name=agent_name)

        data = {
            'info': [],
            'warning': [],
            'critical': []
        }

        for alert in alerts:
            entry = {
                'timestamp': alert.timestamp,
                'agent': alert.agent_name,
                'type': alert.alert_type,
                'message': alert.message
            }
            data[alert.severity].append(entry)

        return data

    def generate_html_report(self, agent_name: Optional[str] = None) -> str:
        """
        Generate an HTML report with memory usage visualizations.

        Args:
            agent_name: Generate report for specific agent (optional)

        Returns:
            HTML string with embedded charts (requires Chart.js)
        """
        if not self.monitor:
            return "<p>No monitor data available</p>"

        agents_to_report = [agent_name] if agent_name else list(self.monitor.agent_history.keys())

        html_parts = [
            "<!DOCTYPE html>",
            "<html>",
            "<head>",
            "    <title>Memory Usage Report</title>",
            "    <script src='https://cdn.jsdelivr.net/npm/chart.js'></script>",
            "    <style>",
            "        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }",
            "        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }",
            "        h1 { color: #333; border-bottom: 2px solid #4CAF50; padding-bottom: 10px; }",
            "        h2 { color: #666; margin-top: 30px; }",
            "        .chart-container { margin: 20px 0; height: 400px; }",
            "        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 20px 0; }",
            "        .stat-card { background: #f9f9f9; padding: 15px; border-radius: 5px; border-left: 4px solid #4CAF50; }",
            "        .stat-value { font-size: 24px; font-weight: bold; color: #4CAF50; }",
            "        .stat-label { color: #666; font-size: 14px; }",
            "        .alert { padding: 10px; margin: 5px 0; border-radius: 4px; }",
            "        .alert-info { background: #d1ecf1; border-left: 4px solid #0c5460; }",
            "        .alert-warning { background: #fff3cd; border-left: 4px solid #856404; }",
            "        .alert-critical { background: #f8d7da; border-left: 4px solid #721c24; }",
            "    </style>",
            "</head>",
            "<body>",
            "    <div class='container'>",
            "        <h1>Memory Usage Report</h1>",
            f"        <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>"
        ]

        for agent in agents_to_report:
            stats = self.monitor.get_agent_stats(agent)
            if not stats:
                continue

            # Add agent statistics
            html_parts.extend([
                f"        <h2>Agent: {agent}</h2>",
                "        <div class='stats-grid'>",
                f"            <div class='stat-card'><div class='stat-value'>{stats['current_memory']['total_size']}</div><div class='stat-label'>Total Memories</div></div>",
                f"            <div class='stat-card'><div class='stat-value'>{stats['current_consolidation']['total_consolidations']}</div><div class='stat-label'>Consolidations</div></div>",
                f"            <div class='stat-card'><div class='stat-value'>{stats['memory_trend']}</div><div class='stat-label'>Trend</div></div>",
                f"            <div class='stat-card'><div class='stat-value'>{stats['total_alerts']}</div><div class='stat-label'>Alerts</div></div>",
                "        </div>"
            ])

            # Add charts (data only - actual rendering would need Chart.js)
            timeline_data = self.prepare_memory_timeline_data(agent)
            consolidation_data = self.prepare_consolidation_data(agent)

            html_parts.extend([
                "        <div class='chart-container'>",
                f"            <canvas id='memory-chart-{agent}'></canvas>",
                "        </div>",
                "        <script>",
                f"            const memoryData_{agent.replace(' ', '_')} = {json.dumps({k: [str(v) if isinstance(v, datetime) else v for v in vals] for k, vals in timeline_data.items()})};",
                "            // Chart.js configuration would go here",
                "        </script>"
            ])

        # Add alerts section
        alerts = self.monitor.get_alerts(agent_name=agent_name)
        if alerts:
            html_parts.extend([
                "        <h2>Recent Alerts</h2>"
            ])

            for alert in alerts[-10:]:  # Last 10 alerts
                severity_class = f"alert-{alert.severity}"
                html_parts.append(f"        <div class='alert {severity_class}'>{alert}</div>")

        html_parts.extend([
            "    </div>",
            "</body>",
            "</html>"
        ])

        return "\n".join(html_parts)

    def export_data_json(self, agent_name: Optional[str] = None) -> str:
        """
        Export monitoring data as JSON for external visualization tools.

        Args:
            agent_name: Export data for specific agent (optional)

        Returns:
            JSON string with monitoring data
        """
        if not self.monitor:
            return "{}"

        agents_to_export = [agent_name] if agent_name else list(self.monitor.agent_history.keys())

        export_data = {
            'generated_at': datetime.now().isoformat(),
            'agents': {}
        }

        for agent in agents_to_export:
            timeline = self.prepare_memory_timeline_data(agent)
            consolidation = self.prepare_consolidation_data(agent)
            stats = self.monitor.get_agent_stats(agent)

            # Convert datetime objects to strings for JSON serialization
            timeline_serializable = {
                k: [v.isoformat() if isinstance(v, datetime) else v for v in vals]
                for k, vals in timeline.items()
            }

            consolidation_serializable = {
                k: [v.isoformat() if isinstance(v, datetime) else v for v in vals]
                for k, vals in consolidation.items()
            }

            export_data['agents'][agent] = {
                'stats': stats,
                'timeline': timeline_serializable,
                'consolidation': consolidation_serializable
            }

        # Add alerts
        alerts = self.monitor.get_alerts(agent_name=agent_name)
        export_data['alerts'] = [
            {
                'timestamp': alert.timestamp.isoformat(),
                'agent': alert.agent_name,
                'type': alert.alert_type,
                'severity': alert.severity,
                'message': alert.message
            }
            for alert in alerts
        ]

        return json.dumps(export_data, indent=2)

    def print_ascii_chart(self, agent_name: str, metric: str = 'memory_size', width: int = 60, height: int = 15) -> str:
        """
        Generate an ASCII art chart of memory usage (for console display).

        Args:
            agent_name: Name of the agent
            metric: Metric to chart ('memory_size', 'usage_ratio', etc.)
            width: Chart width in characters
            height: Chart height in characters

        Returns:
            ASCII art string
        """
        timeline_data = self.prepare_memory_timeline_data(agent_name)

        if metric not in timeline_data or not timeline_data[metric]:
            return "No data available"

        values = timeline_data[metric]
        if not values:
            return "No data points"

        # Normalize values to chart height
        max_val = max(values) if max(values) > 0 else 1
        min_val = min(values)
        range_val = max_val - min_val if max_val > min_val else 1

        normalized = [(v - min_val) / range_val * (height - 1) for v in values]

        # Compress data points to fit width
        points_per_char = max(1, len(normalized) // width)
        compressed = [max(normalized[i:i+points_per_char]) if i+points_per_char <= len(normalized)
                     else normalized[i] for i in range(0, len(normalized), points_per_char)]

        # Build chart
        lines = []
        lines.append(f"Memory {metric.replace('_', ' ').title()} - {agent_name}")
        lines.append("─" * (width + 10))

        for row in range(height - 1, -1, -1):
            y_val = min_val + (row / (height - 1)) * range_val
            line = f"{y_val:6.1f} │ "

            for col in range(min(width, len(compressed))):
                if compressed[col] >= row - 0.5:
                    line += "█"
                else:
                    line += " "

            lines.append(line)

        lines.append("       └" + "─" * width)
        lines.append(f"        {len(values)} data points")

        return "\n".join(lines)
