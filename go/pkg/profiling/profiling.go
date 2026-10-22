// Package profiling provides performance profiling and monitoring capabilities.
// This module handles performance monitoring, memory usage tracking, and bottleneck identification.
package profiling

import (
	"context"
	"fmt"
	"runtime"
	"sync"
	"time"
)

// ProfileType represents different types of profiling operations
type ProfileType string

const (
	CPUProfile    ProfileType = "cpu"
	MemoryProfile ProfileType = "memory"
	TimeProfile   ProfileType = "time"
	EventProfile  ProfileType = "event"
)

// ProfilerConfig holds configuration for profiling
type ProfilerConfig struct {
	SampleInterval time.Duration          `json:"sample_interval"`
	MaxSamples     int                    `json:"max_samples"`
	EnableMetrics  map[string]bool        `json:"enable_metrics"`
	OutputFormat   string                 `json:"output_format"`
	Metadata       map[string]interface{} `json:"metadata"`
}

// DefaultProfilerConfig returns a default configuration
func DefaultProfilerConfig() *ProfilerConfig {
	return &ProfilerConfig{
		SampleInterval: 100 * time.Millisecond,
		MaxSamples:     1000,
		EnableMetrics: map[string]bool{
			"cpu":    true,
			"memory": true,
			"time":   true,
			"events": true,
		},
		OutputFormat: "json",
		Metadata:     make(map[string]interface{}),
	}
}

// ProfileData represents collected profiling data
type ProfileData struct {
	Type      ProfileType            `json:"type"`
	StartTime time.Time              `json:"start_time"`
	EndTime   time.Time              `json:"end_time"`
	Duration  time.Duration          `json:"duration"`
	Samples   []Sample               `json:"samples"`
	Summary   map[string]interface{} `json:"summary"`
	Metadata  map[string]interface{} `json:"metadata"`
}

// Sample represents a single profiling sample
type Sample struct {
	Timestamp   time.Time              `json:"timestamp"`
	CPUUsage    float64                `json:"cpu_usage,omitempty"`
	MemoryUsage int64                  `json:"memory_usage,omitempty"`
	EventName   string                 `json:"event_name,omitempty"`
	EventData   map[string]interface{} `json:"event_data,omitempty"`
	Metadata    map[string]interface{} `json:"metadata,omitempty"`
}

// Profiler interface defines profiling capabilities
type Profiler interface {
	// Start begins profiling with the given configuration
	Start(ctx context.Context, config *ProfilerConfig) error

	// Stop ends profiling and returns results
	Stop() (*ProfileData, error)

	// RecordEvent records a custom event
	RecordEvent(name string, data map[string]interface{}) error

	// AddMetric adds a custom metric to the current profile
	AddMetric(name string, value interface{}) error

	// IsRunning returns whether profiling is currently active
	IsRunning() bool

	// GetSnapshot returns current profiling data without stopping
	GetSnapshot() (*ProfileData, error)
}

// SystemProfiler implements profiling for system metrics
type SystemProfiler struct {
	config      *ProfilerConfig
	isRunning   bool
	startTime   time.Time
	samples     []Sample
	events      []Sample
	metrics     map[string]interface{}
	mutex       sync.RWMutex
	stopChannel chan struct{}
	ctx         context.Context
	cancel      context.CancelFunc
}

// NewSystemProfiler creates a new system profiler
func NewSystemProfiler() *SystemProfiler {
	return &SystemProfiler{
		samples:     make([]Sample, 0),
		events:      make([]Sample, 0),
		metrics:     make(map[string]interface{}),
		stopChannel: make(chan struct{}),
	}
}

// Start begins profiling with the given configuration
func (sp *SystemProfiler) Start(ctx context.Context, config *ProfilerConfig) error {
	sp.mutex.Lock()
	defer sp.mutex.Unlock()

	if sp.isRunning {
		return fmt.Errorf("profiler is already running")
	}

	if config == nil {
		config = DefaultProfilerConfig()
	}

	sp.config = config
	sp.isRunning = true
	sp.startTime = time.Now()
	sp.samples = make([]Sample, 0, config.MaxSamples)
	sp.events = make([]Sample, 0)
	// Don't reinitialize metrics - preserve any metrics added before Start
	if sp.metrics == nil {
		sp.metrics = make(map[string]interface{})
	}

	// Create cancellable context
	sp.ctx, sp.cancel = context.WithCancel(ctx)

	// Start background sampling
	go sp.backgroundSampling()

	return nil
}

// Stop ends profiling and returns results
func (sp *SystemProfiler) Stop() (*ProfileData, error) {
	sp.mutex.Lock()
	defer sp.mutex.Unlock()

	if !sp.isRunning {
		return nil, fmt.Errorf("profiler is not running")
	}

	// Signal stop and wait for background goroutine
	sp.cancel()
	close(sp.stopChannel)
	sp.isRunning = false

	endTime := time.Now()
	duration := endTime.Sub(sp.startTime)

	// Combine samples and events
	allSamples := make([]Sample, 0, len(sp.samples)+len(sp.events))
	allSamples = append(allSamples, sp.samples...)
	allSamples = append(allSamples, sp.events...)

	// Generate summary
	summary := sp.generateSummary(allSamples, duration)

	profileData := &ProfileData{
		Type:      "combined",
		StartTime: sp.startTime,
		EndTime:   endTime,
		Duration:  duration,
		Samples:   allSamples,
		Summary:   summary,
		Metadata:  sp.config.Metadata,
	}

	return profileData, nil
}

// RecordEvent records a custom event
func (sp *SystemProfiler) RecordEvent(name string, data map[string]interface{}) error {
	sp.mutex.Lock()
	defer sp.mutex.Unlock()

	return sp.recordEventUnsafe(name, data)
}

// recordEventUnsafe records an event without acquiring the mutex (internal use)
func (sp *SystemProfiler) recordEventUnsafe(name string, data map[string]interface{}) error {
	if !sp.isRunning {
		return fmt.Errorf("profiler is not running")
	}

	event := Sample{
		Timestamp: time.Now(),
		EventName: name,
		EventData: data,
		Metadata:  map[string]interface{}{"type": "event"},
	}

	sp.events = append(sp.events, event)
	return nil
}

// AddMetric adds a custom metric to the current profile
func (sp *SystemProfiler) AddMetric(name string, value interface{}) error {
	sp.mutex.Lock()
	defer sp.mutex.Unlock()

	if !sp.isRunning {
		return fmt.Errorf("profiler is not running")
	}

	sp.metrics[name] = value
	return nil
}

// IsRunning returns whether profiling is currently active
func (sp *SystemProfiler) IsRunning() bool {
	sp.mutex.RLock()
	defer sp.mutex.RUnlock()
	return sp.isRunning
}

// GetSnapshot returns current profiling data without stopping
func (sp *SystemProfiler) GetSnapshot() (*ProfileData, error) {
	sp.mutex.RLock()
	defer sp.mutex.RUnlock()

	if !sp.isRunning {
		return nil, fmt.Errorf("profiler is not running")
	}

	now := time.Now()
	duration := now.Sub(sp.startTime)

	// Create snapshot of current samples
	snapshotSamples := make([]Sample, len(sp.samples)+len(sp.events))
	copy(snapshotSamples, sp.samples)
	copy(snapshotSamples[len(sp.samples):], sp.events)

	summary := sp.generateSummary(snapshotSamples, duration)

	profileData := &ProfileData{
		Type:      "snapshot",
		StartTime: sp.startTime,
		EndTime:   now,
		Duration:  duration,
		Samples:   snapshotSamples,
		Summary:   summary,
		Metadata:  sp.config.Metadata,
	}

	return profileData, nil
}

// backgroundSampling runs in the background collecting system metrics
func (sp *SystemProfiler) backgroundSampling() {
	ticker := time.NewTicker(sp.config.SampleInterval)
	defer ticker.Stop()

	for {
		select {
		case <-sp.ctx.Done():
			return
		case <-sp.stopChannel:
			return
		case <-ticker.C:
			sp.collectSample()
		}
	}
}

// collectSample collects a single sample of system metrics
func (sp *SystemProfiler) collectSample() {
	sp.mutex.Lock()
	defer sp.mutex.Unlock()

	if !sp.isRunning || len(sp.samples) >= sp.config.MaxSamples {
		return
	}

	var memStats runtime.MemStats
	runtime.ReadMemStats(&memStats)

	sample := Sample{
		Timestamp:   time.Now(),
		MemoryUsage: int64(memStats.Alloc),
		CPUUsage:    sp.estimateCPUUsage(),
		Metadata: map[string]interface{}{
			"type":         "system_sample",
			"heap_objects": memStats.HeapObjects,
			"gc_cycles":    memStats.NumGC,
			"goroutines":   runtime.NumGoroutine(),
		},
	}

	sp.samples = append(sp.samples, sample)
}

// estimateCPUUsage provides a simple CPU usage estimation
func (sp *SystemProfiler) estimateCPUUsage() float64 {
	// Simple CPU usage estimation based on goroutine count
	// In a real implementation, you'd use more sophisticated methods
	goroutines := float64(runtime.NumGoroutine())
	cpus := float64(runtime.NumCPU())

	// Rough estimation: more goroutines = higher CPU usage
	usage := (goroutines / (cpus * 10)) * 100
	if usage > 100 {
		usage = 100
	}

	return usage
}

// generateSummary creates a summary of profiling data
func (sp *SystemProfiler) generateSummary(samples []Sample, duration time.Duration) map[string]interface{} {
	summary := map[string]interface{}{
		"sample_count": len(samples),
		"duration":     duration.String(),
		"start_time":   sp.startTime,
	}

	if len(samples) == 0 {
		// Even with no samples, we should include custom metrics
		if len(sp.metrics) > 0 {
			summary["custom_metrics"] = sp.metrics
		}
		return summary
	}

	// Calculate memory statistics
	var totalMemory, maxMemory, minMemory int64
	var totalCPU, maxCPU, minCPU float64
	var memorySamples, cpuSamples int

	maxMemory = 0
	minMemory = int64(^uint64(0) >> 1) // Max int64
	maxCPU = 0
	minCPU = 100

	eventCounts := make(map[string]int)

	for _, sample := range samples {
		if sample.EventName != "" {
			eventCounts[sample.EventName]++
		} else {
			// System metric sample
			if sample.MemoryUsage > 0 {
				totalMemory += sample.MemoryUsage
				memorySamples++
				if sample.MemoryUsage > maxMemory {
					maxMemory = sample.MemoryUsage
				}
				if sample.MemoryUsage < minMemory {
					minMemory = sample.MemoryUsage
				}
			}

			if sample.CPUUsage >= 0 {
				totalCPU += sample.CPUUsage
				cpuSamples++
				if sample.CPUUsage > maxCPU {
					maxCPU = sample.CPUUsage
				}
				if sample.CPUUsage < minCPU {
					minCPU = sample.CPUUsage
				}
			}
		}
	}

	// Add memory statistics
	if memorySamples > 0 {
		summary["memory"] = map[string]interface{}{
			"average_bytes": totalMemory / int64(memorySamples),
			"max_bytes":     maxMemory,
			"min_bytes":     minMemory,
			"sample_count":  memorySamples,
		}
	}

	// Add CPU statistics
	if cpuSamples > 0 {
		summary["cpu"] = map[string]interface{}{
			"average_percent": totalCPU / float64(cpuSamples),
			"max_percent":     maxCPU,
			"min_percent":     minCPU,
			"sample_count":    cpuSamples,
		}
	}

	// Add event statistics
	if len(eventCounts) > 0 {
		summary["events"] = map[string]interface{}{
			"event_counts":  eventCounts,
			"total_events":  len(eventCounts),
			"unique_events": len(eventCounts),
		}
	}

	// Add custom metrics
	if len(sp.metrics) > 0 {
		summary["custom_metrics"] = sp.metrics
	}

	return summary
}

// SimulationProfiler is a specialized profiler for TinyTroupe simulations
type SimulationProfiler struct {
	*SystemProfiler
	agentMetrics map[string]*AgentProfile
	worldMetrics *WorldProfile
}

// AgentProfile holds profiling data for a single agent
type AgentProfile struct {
	AgentID       string                 `json:"agent_id"`
	MessageCount  int                    `json:"message_count"`
	ActionCount   int                    `json:"action_count"`
	ResponseTimes []time.Duration        `json:"response_times"`
	LastActivity  time.Time              `json:"last_activity"`
	Metadata      map[string]interface{} `json:"metadata"`
}

// WorldProfile holds profiling data for the simulation world
type WorldProfile struct {
	WorldID         string                 `json:"world_id"`
	AgentCount      int                    `json:"agent_count"`
	TotalMessages   int                    `json:"total_messages"`
	SimulationSteps int                    `json:"simulation_steps"`
	StartTime       time.Time              `json:"start_time"`
	Metadata        map[string]interface{} `json:"metadata"`
}

// NewSimulationProfiler creates a new simulation-specific profiler
func NewSimulationProfiler() *SimulationProfiler {
	return &SimulationProfiler{
		SystemProfiler: NewSystemProfiler(),
		agentMetrics:   make(map[string]*AgentProfile),
		worldMetrics: &WorldProfile{
			Metadata: make(map[string]interface{}),
		},
	}
}

// RecordAgentAction records an action performed by an agent
func (sp *SimulationProfiler) RecordAgentAction(agentID string, actionType string, responseTime time.Duration) error {
	sp.mutex.Lock()
	defer sp.mutex.Unlock()

	if !sp.isRunning {
		return fmt.Errorf("profiler is not running")
	}

	// Get or create agent profile
	agentProfile, exists := sp.agentMetrics[agentID]
	if !exists {
		agentProfile = &AgentProfile{
			AgentID:       agentID,
			ResponseTimes: make([]time.Duration, 0),
			Metadata:      make(map[string]interface{}),
		}
		sp.agentMetrics[agentID] = agentProfile
	}

	// Update agent metrics
	agentProfile.ActionCount++
	agentProfile.ResponseTimes = append(agentProfile.ResponseTimes, responseTime)
	agentProfile.LastActivity = time.Now()

	if actionType == "message" {
		agentProfile.MessageCount++
	}

	// Record as event
	return sp.recordEventUnsafe("agent_action", map[string]interface{}{
		"agent_id":      agentID,
		"action_type":   actionType,
		"response_time": responseTime,
	})
}

// RecordWorldStep records a simulation step
func (sp *SimulationProfiler) RecordWorldStep(worldID string, stepNumber int, agentCount int) error {
	sp.mutex.Lock()
	defer sp.mutex.Unlock()

	if !sp.isRunning {
		return fmt.Errorf("profiler is not running")
	}

	// Update world metrics
	sp.worldMetrics.WorldID = worldID
	sp.worldMetrics.AgentCount = agentCount
	sp.worldMetrics.SimulationSteps = stepNumber

	// Record as event
	return sp.recordEventUnsafe("world_step", map[string]interface{}{
		"world_id":    worldID,
		"step_number": stepNumber,
		"agent_count": agentCount,
	})
}

// GetAgentProfile returns profiling data for a specific agent
func (sp *SimulationProfiler) GetAgentProfile(agentID string) (*AgentProfile, error) {
	sp.mutex.RLock()
	defer sp.mutex.RUnlock()

	profile, exists := sp.agentMetrics[agentID]
	if !exists {
		return nil, fmt.Errorf("no profile found for agent %s", agentID)
	}

	return profile, nil
}

// GetWorldProfile returns profiling data for the simulation world
func (sp *SimulationProfiler) GetWorldProfile() *WorldProfile {
	sp.mutex.RLock()
	defer sp.mutex.RUnlock()

	return sp.worldMetrics
}
