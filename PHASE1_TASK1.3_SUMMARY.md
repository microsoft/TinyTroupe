# Phase 1, Task 1.3: Memory Usage Monitoring Implementation

## Summary

Created comprehensive memory monitoring and visualization utilities that provide real-time tracking, alerting, and visualization of memory usage patterns for TinyTroupe agents. This completes the Memory Management Foundation (Week 1-2) of Phase 1.

## Changes Made

### 1. Memory Monitoring Module (`tinytroupe/monitoring/memory_monitor.py`)

#### Classes Implemented

**MemoryAlert** (Dataclass)
- Represents a memory usage alert with timestamp, agent name, type, severity, and message
- Provides clean string representation for logging
- Stores memory statistics at time of alert

**MemoryMonitor**
- Tracks memory usage for multiple agents over time
- Detects abnormal growth patterns
- Triggers configurable alerts
- Supports custom alert callbacks
- Generates comprehensive text reports

Key Features:
- **Threshold Monitoring**: Alerts when memory usage exceeds configured ratio
- **Growth Detection**: Identifies abnormal memory growth rates
- **Consolidation Tracking**: Monitors consolidation effectiveness
- **Historical Tracking**: Maintains snapshots of memory state over time
- **Trend Analysis**: Calculates memory usage trends (increasing/decreasing/stable)

**MemoryProfiler**
- Decorator-based profiling for memory operations
- Tracks execution time statistics (min, max, avg, total)
- Provides performance insights for memory-intensive functions

#### Key Methods

```python
# MemoryMonitor
monitor = MemoryMonitor(alert_threshold=0.8)
monitor.track_agent(agent)
monitor.record_snapshot(agent)
stats = monitor.get_agent_stats(agent.name)
alerts = monitor.get_alerts(severity="warning")
report = monitor.generate_report(agent.name)

# MemoryProfiler
profiler = MemoryProfiler()

@profiler.profile
def my_function():
    # Your memory-intensive code
    pass

profiler.print_stats()
```

### 2. Visualization Module (`tinytroupe/visualization/memory_viz.py`)

#### Classes Implemented

**MemoryVisualizer**
- Prepares data for visualization
- Generates HTML reports with embedded charts
- Exports data to JSON for external tools
- Creates ASCII charts for console display

Key Features:
- **Timeline Preparation**: Organizes memory data for time-series visualization
- **Consolidation Visualization**: Tracks consolidation patterns over time
- **Alert Timeline**: Visualizes alert history
- **HTML Reports**: Generates interactive HTML reports (Chart.js ready)
- **JSON Export**: Exports data for Jupyter, Plotly, or other tools
- **ASCII Charts**: Console-friendly visualization for quick checks

#### Key Methods

```python
viz = MemoryVisualizer(monitor)

# Prepare data for charting
timeline_data = viz.prepare_memory_timeline_data(agent.name)
consolidation_data = viz.prepare_consolidation_data(agent.name)

# Generate reports
html_report = viz.generate_html_report(agent.name)
json_export = viz.export_data_json(agent.name)
ascii_chart = viz.print_ascii_chart(agent.name, metric='memory_size')
```

### 3. Tests (`tests/unit/test_memory_monitoring.py`)

Created comprehensive test suite covering:

**TestMemoryAlert**
- Alert creation and validation
- String representation

**TestMemoryMonitor**
- Initialization with custom thresholds
- Agent tracking
- Snapshot recording
- Threshold alert triggering
- Abnormal growth detection
- Statistics generation
- Alert callbacks
- Report generation

**TestMemoryProfiler**
- Function profiling
- Statistics tracking
- Data clearing

**TestMemoryVisualizer**
- Timeline data preparation
- JSON export
- ASCII chart generation

Total: **15+ test cases** covering all major functionality

### 4. Module Structure

```
tinytroupe/
├── monitoring/
│   ├── __init__.py (NEW)
│   └── memory_monitor.py (NEW)
└── visualization/
    ├── __init__.py (NEW)
    └── memory_viz.py (NEW)

tests/unit/
└── test_memory_monitoring.py (NEW)
```

## Usage Examples

### Example 1: Basic Memory Monitoring

```python
from tinytroupe.monitoring import MemoryMonitor
from tinytroupe.agent import TinyPerson

# Create monitor
monitor = MemoryMonitor(alert_threshold=0.8)

# Create and track agent
agent = TinyPerson("Alice")
monitor.track_agent(agent)

# During simulation, record snapshots
for i in range(100):
    agent.store_in_memory({
        'content': f'Memory {i}',
        'type': 'action',
        'simulation_timestamp': f'2024-01-{i:03d}'
    })

    # Record snapshot every 10 memories
    if i % 10 == 0:
        monitor.record_snapshot(agent)

# Check statistics
stats = monitor.get_agent_stats("Alice")
print(f"Memory trend: {stats['memory_trend']}")
print(f"Total alerts: {stats['total_alerts']}")

# Get alerts
alerts = monitor.get_alerts(agent_name="Alice", severity="warning")
for alert in alerts:
    print(alert)

# Generate report
report = monitor.generate_report("Alice")
print(report)
```

### Example 2: Real-Time Alert Callbacks

```python
from tinytroupe.monitoring import MemoryMonitor

def handle_alert(alert):
    """Custom alert handler."""
    if alert.severity == "critical":
        print(f"CRITICAL: {alert.message}")
        # Take action (e.g., force consolidation, save state, etc.)
    elif alert.severity == "warning":
        print(f"WARNING: {alert.message}")

# Set up monitoring with callback
monitor = MemoryMonitor()
monitor.register_alert_callback(handle_alert)

# Alerts will automatically trigger callback
monitor.track_agent(agent)
monitor.record_snapshot(agent)  # May trigger alerts
```

### Example 3: Memory Visualization

```python
from tinytroupe.monitoring import MemoryMonitor
from tinytroupe.visualization import MemoryVisualizer

# Set up monitoring
monitor = MemoryMonitor()
monitor.track_agent(agent)

# Record multiple snapshots
for _ in range(50):
    agent.act()  # Simulate agent activity
    monitor.record_snapshot(agent)

# Visualize
viz = MemoryVisualizer(monitor)

# Generate ASCII chart for quick view
print(viz.print_ascii_chart("Alice", metric='memory_size'))

# Export to JSON for Jupyter/Plotly
json_data = viz.export_data_json("Alice")
with open('memory_data.json', 'w') as f:
    f.write(json_data)

# Generate HTML report
html_report = viz.generate_html_report("Alice")
with open('memory_report.html', 'w') as f:
    f.write(html_report)
```

### Example 4: Performance Profiling

```python
from tinytroupe.monitoring import MemoryProfiler

profiler = MemoryProfiler()

@profiler.profile
def consolidate_memories(agent):
    """Profiled consolidation function."""
    agent.consolidate_episode_memories()

@profiler.profile
def store_memories(agent, count):
    """Profiled storage function."""
    for i in range(count):
        agent.store_in_memory({
            'content': f'Memory {i}',
            'type': 'action',
            'simulation_timestamp': f'2024-01-{i:03d}'
        })

# Use profiled functions
consolidate_memories(agent)
store_memories(agent, 100)

# Print statistics
profiler.print_stats()
```

## Benefits

1. **Real-Time Monitoring**: Track memory usage as simulation runs
2. **Proactive Alerts**: Get notified before memory issues occur
3. **Performance Insights**: Identify bottlenecks and optimization opportunities
4. **Visual Analysis**: Multiple visualization options (HTML, JSON, ASCII)
5. **Custom Actions**: Alert callbacks enable automated responses
6. **Comprehensive Stats**: Detailed statistics for debugging and optimization
7. **Easy Integration**: Works seamlessly with existing TinyPerson agents

## Integration with Previous Tasks

This task builds on and complements Tasks 1.1 and 1.2:

- **Task 1.1 Integration**:
  - Uses `get_memory_stats()` for snapshot data
  - Monitors `usage_ratio` and `approaching_limit` flags
  - Tracks effectiveness of cleanup strategies

- **Task 1.2 Integration**:
  - Uses `get_consolidation_metrics()` for consolidation tracking
  - Monitors consolidation frequency and effectiveness
  - Alerts on inefficient consolidation patterns

## Success Metrics (from Roadmap)

- ✅ `get_memory_stats()` method available (Task 1.1)
- ✅ Memory size, age, consolidation frequency tracked
- ✅ Memory metrics available for reports
- ✅ Memory usage visualization tools created
- ✅ Memory alerts for abnormal growth implemented
- ✅ Memory profiling decorator available
- ✅ Comprehensive tests added (15+ test cases)
- ✅ Documentation complete

## Files Created

- `tinytroupe/monitoring/__init__.py`: Module exports
- `tinytroupe/monitoring/memory_monitor.py`: Core monitoring classes (450+ lines)
- `tinytroupe/visualization/__init__.py`: Module exports
- `tinytroupe/visualization/memory_viz.py`: Visualization utilities (350+ lines)
- `tests/unit/test_memory_monitoring.py`: Comprehensive test suite (400+ lines)

## Configuration Used

Uses existing configuration from Tasks 1.1 and 1.2:
- Memory thresholds from `[Memory]` section
- Alert threshold configurable per monitor instance
- Growth rate threshold configurable
- Consolidation frequency threshold configurable

## Performance Impact

- **Minimal Overhead**: Snapshot recording is ~O(1)
- **Optional Tracking**: Only tracks agents you explicitly register
- **Efficient Storage**: Stores only summary statistics, not full history
- **Lazy Visualization**: Charts generated on-demand

## Next Steps

With Tasks 1.1, 1.2, and 1.3 complete, **Week 1-2: Memory Management** is finished!

**Next**: Move to Week 2-3: Parallel Agent Processing
- Task 2.1: Thread-safe agent actions
- Task 2.2: Parallel world execution
- Task 2.3: Performance benchmarking suite

## Estimated Time

- Planned: 2 days
- Actual: ~2-3 hours

## Testing

Tests can be run with:
```bash
pytest tests/unit/test_memory_monitoring.py -v
```

## Related Documentation

- `IMPLEMENTATION_ROADMAP.md`: Phase 1, Week 1-2, Task 1.3
- `EXPANSION_PLAN.md`: Phase 1 objectives
- `PHASE1_TASK1.1_SUMMARY.md`: Memory size limits (prerequisite)
- `PHASE1_TASK1.2_SUMMARY.md`: Automatic consolidation (prerequisite)
