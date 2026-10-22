package profiling

import (
	"context"
	"fmt"
	"testing"
	"time"
)

func TestSystemProfilerCreation(t *testing.T) {
	profiler := NewSystemProfiler()
	if profiler == nil {
		t.Fatal("NewSystemProfiler returned nil")
	}

	if profiler.IsRunning() {
		t.Error("New profiler should not be running")
	}
}

func TestDefaultProfilerConfig(t *testing.T) {
	config := DefaultProfilerConfig()
	if config == nil {
		t.Fatal("DefaultProfilerConfig returned nil")
	}

	if config.SampleInterval <= 0 {
		t.Error("Sample interval should be positive")
	}

	if config.MaxSamples <= 0 {
		t.Error("Max samples should be positive")
	}

	if !config.EnableMetrics["cpu"] {
		t.Error("CPU metrics should be enabled by default")
	}

	if !config.EnableMetrics["memory"] {
		t.Error("Memory metrics should be enabled by default")
	}
}

func TestProfilerStartStop(t *testing.T) {
	profiler := NewSystemProfiler()
	ctx := context.Background()

	// Test starting profiler
	err := profiler.Start(ctx, nil) // Use default config
	if err != nil {
		t.Fatalf("Failed to start profiler: %v", err)
	}

	if !profiler.IsRunning() {
		t.Error("Profiler should be running after start")
	}

	// Test starting again (should fail)
	err = profiler.Start(ctx, nil)
	if err == nil {
		t.Error("Starting profiler twice should return error")
	}

	// Let it run for a bit to collect samples
	time.Sleep(250 * time.Millisecond)

	// Test stopping profiler
	data, err := profiler.Stop()
	if err != nil {
		t.Fatalf("Failed to stop profiler: %v", err)
	}

	if profiler.IsRunning() {
		t.Error("Profiler should not be running after stop")
	}

	if data == nil {
		t.Fatal("Stop should return profile data")
	}

	// Test stopping again (should fail)
	_, err = profiler.Stop()
	if err == nil {
		t.Error("Stopping profiler twice should return error")
	}
}

func TestProfileDataCollection(t *testing.T) {
	profiler := NewSystemProfiler()
	ctx := context.Background()

	config := DefaultProfilerConfig()
	config.SampleInterval = 50 * time.Millisecond
	config.MaxSamples = 10

	err := profiler.Start(ctx, config)
	if err != nil {
		t.Fatalf("Failed to start profiler: %v", err)
	}

	// Let it collect some samples
	time.Sleep(300 * time.Millisecond)

	data, err := profiler.Stop()
	if err != nil {
		t.Fatalf("Failed to stop profiler: %v", err)
	}

	// Verify data structure
	if data.Type == "" {
		t.Error("Profile data should have a type")
	}

	if data.StartTime.IsZero() {
		t.Error("Profile data should have start time")
	}

	if data.EndTime.IsZero() {
		t.Error("Profile data should have end time")
	}

	if data.Duration <= 0 {
		t.Error("Profile data should have positive duration")
	}

	if len(data.Samples) == 0 {
		t.Error("Profile data should contain samples")
	}

	if data.Summary == nil {
		t.Error("Profile data should have summary")
	}

	// Check summary contents
	if sampleCount, exists := data.Summary["sample_count"]; !exists {
		t.Error("Summary should include sample count")
	} else if count, ok := sampleCount.(int); !ok || count <= 0 {
		t.Error("Sample count should be positive integer")
	}
}

func TestEventRecording(t *testing.T) {
	profiler := NewSystemProfiler()
	ctx := context.Background()

	// Test recording event when not running (should fail)
	err := profiler.RecordEvent("test_event", map[string]interface{}{"key": "value"})
	if err == nil {
		t.Error("Recording event when not running should fail")
	}

	// Start profiler
	err = profiler.Start(ctx, nil)
	if err != nil {
		t.Fatalf("Failed to start profiler: %v", err)
	}

	// Test recording events
	err = profiler.RecordEvent("agent_action", map[string]interface{}{
		"agent_id": "test_agent",
		"action":   "speak",
	})
	if err != nil {
		t.Errorf("Failed to record event: %v", err)
	}

	err = profiler.RecordEvent("simulation_step", map[string]interface{}{
		"step": 1,
		"time": time.Now(),
	})
	if err != nil {
		t.Errorf("Failed to record event: %v", err)
	}

	// Stop and check data
	data, err := profiler.Stop()
	if err != nil {
		t.Fatalf("Failed to stop profiler: %v", err)
	}

	// Verify events were recorded
	eventCount := 0
	for _, sample := range data.Samples {
		if sample.EventName != "" {
			eventCount++
		}
	}

	if eventCount < 2 {
		t.Errorf("Expected at least 2 events, got %d", eventCount)
	}

	// Check summary for events
	if events, exists := data.Summary["events"]; exists {
		eventMap, ok := events.(map[string]interface{})
		if !ok {
			t.Error("Events summary should be a map")
		} else {
			if eventCounts, exists := eventMap["event_counts"]; !exists {
				t.Error("Events summary should include event counts")
			} else if _, ok := eventCounts.(map[string]int); !ok {
				t.Error("Event counts should be a map of strings to ints")
			}
		}
	}
}

func TestCustomMetrics(t *testing.T) {
	profiler := NewSystemProfiler()
	ctx := context.Background()

	err := profiler.Start(ctx, nil)
	if err != nil {
		t.Fatalf("Failed to start profiler: %v", err)
	}

	// Add custom metrics
	err = profiler.AddMetric("test_metric", 42)
	if err != nil {
		t.Errorf("Failed to add metric: %v", err)
	}

	err = profiler.AddMetric("string_metric", "test_value")
	if err != nil {
		t.Errorf("Failed to add string metric: %v", err)
	}

	err = profiler.AddMetric("complex_metric", map[string]interface{}{
		"nested": "value",
		"number": 123,
	})
	if err != nil {
		t.Errorf("Failed to add complex metric: %v", err)
	}

	data, err := profiler.Stop()
	if err != nil {
		t.Fatalf("Failed to stop profiler: %v", err)
	}

	// Verify custom metrics in summary
	if customMetrics, exists := data.Summary["custom_metrics"]; exists {
		metricsMap, ok := customMetrics.(map[string]interface{})
		if !ok {
			t.Error("Custom metrics should be a map")
		} else {
			if metricsMap["test_metric"] != 42 {
				t.Error("Test metric value not preserved")
			}

			if metricsMap["string_metric"] != "test_value" {
				t.Error("String metric value not preserved")
			}

			if _, exists := metricsMap["complex_metric"]; !exists {
				t.Error("Complex metric not found")
			}
		}
	} else {
		t.Error("Custom metrics not found in summary")
	}
}

func TestSnapshot(t *testing.T) {
	profiler := NewSystemProfiler()
	ctx := context.Background()

	// Test snapshot when not running (should fail)
	_, err := profiler.GetSnapshot()
	if err == nil {
		t.Error("Getting snapshot when not running should fail")
	}

	// Start profiler
	err = profiler.Start(ctx, nil)
	if err != nil {
		t.Fatalf("Failed to start profiler: %v", err)
	}

	// Let it collect some data
	time.Sleep(150 * time.Millisecond)

	// Get snapshot
	snapshot, err := profiler.GetSnapshot()
	if err != nil {
		t.Errorf("Failed to get snapshot: %v", err)
	}

	if snapshot == nil {
		t.Fatal("Snapshot should not be nil")
	}

	if snapshot.Type != "snapshot" {
		t.Error("Snapshot should have type 'snapshot'")
	}

	// Profiler should still be running
	if !profiler.IsRunning() {
		t.Error("Profiler should still be running after snapshot")
	}

	// Stop profiler
	finalData, err := profiler.Stop()
	if err != nil {
		t.Fatalf("Failed to stop profiler: %v", err)
	}

	// Final data should have more or equal samples than snapshot
	if len(finalData.Samples) < len(snapshot.Samples) {
		t.Error("Final data should have at least as many samples as snapshot")
	}
}

func TestSimulationProfiler(t *testing.T) {
	profiler := NewSimulationProfiler()
	ctx := context.Background()

	if profiler == nil {
		t.Fatal("NewSimulationProfiler returned nil")
	}

	err := profiler.Start(ctx, nil)
	if err != nil {
		t.Fatalf("Failed to start simulation profiler: %v", err)
	}

	// Record agent actions
	err = profiler.RecordAgentAction("agent1", "message", 100*time.Millisecond)
	if err != nil {
		t.Errorf("Failed to record agent action: %v", err)
	}

	err = profiler.RecordAgentAction("agent1", "think", 50*time.Millisecond)
	if err != nil {
		t.Errorf("Failed to record agent action: %v", err)
	}

	err = profiler.RecordAgentAction("agent2", "message", 200*time.Millisecond)
	if err != nil {
		t.Errorf("Failed to record agent action: %v", err)
	}

	// Record world steps
	err = profiler.RecordWorldStep("test_world", 1, 2)
	if err != nil {
		t.Errorf("Failed to record world step: %v", err)
	}

	err = profiler.RecordWorldStep("test_world", 2, 2)
	if err != nil {
		t.Errorf("Failed to record world step: %v", err)
	}

	// Get agent profile
	agent1Profile, err := profiler.GetAgentProfile("agent1")
	if err != nil {
		t.Errorf("Failed to get agent profile: %v", err)
	}

	if agent1Profile.AgentID != "agent1" {
		t.Error("Agent profile should have correct agent ID")
	}

	if agent1Profile.ActionCount != 2 {
		t.Errorf("Agent1 should have 2 actions, got %d", agent1Profile.ActionCount)
	}

	if agent1Profile.MessageCount != 1 {
		t.Errorf("Agent1 should have 1 message, got %d", agent1Profile.MessageCount)
	}

	if len(agent1Profile.ResponseTimes) != 2 {
		t.Errorf("Agent1 should have 2 response times, got %d", len(agent1Profile.ResponseTimes))
	}

	// Get world profile
	worldProfile := profiler.GetWorldProfile()
	if worldProfile == nil {
		t.Fatal("World profile should not be nil")
	}

	if worldProfile.WorldID != "test_world" {
		t.Error("World profile should have correct world ID")
	}

	if worldProfile.AgentCount != 2 {
		t.Errorf("World should have 2 agents, got %d", worldProfile.AgentCount)
	}

	if worldProfile.SimulationSteps != 2 {
		t.Errorf("World should have 2 steps, got %d", worldProfile.SimulationSteps)
	}

	// Test getting non-existent agent profile
	_, err = profiler.GetAgentProfile("non_existent")
	if err == nil {
		t.Error("Getting non-existent agent profile should return error")
	}

	// Stop profiler
	data, err := profiler.Stop()
	if err != nil {
		t.Fatalf("Failed to stop simulation profiler: %v", err)
	}

	// Verify events were recorded
	agentActionEvents := 0
	worldStepEvents := 0

	for _, sample := range data.Samples {
		switch sample.EventName {
		case "agent_action":
			agentActionEvents++
		case "world_step":
			worldStepEvents++
		}
	}

	if agentActionEvents != 3 {
		t.Errorf("Expected 3 agent action events, got %d", agentActionEvents)
	}

	if worldStepEvents != 2 {
		t.Errorf("Expected 2 world step events, got %d", worldStepEvents)
	}
}

func TestProfilerWithCustomConfig(t *testing.T) {
	profiler := NewSystemProfiler()
	ctx := context.Background()

	config := &ProfilerConfig{
		SampleInterval: 25 * time.Millisecond,
		MaxSamples:     5,
		EnableMetrics: map[string]bool{
			"cpu":    true,
			"memory": false,
			"time":   true,
		},
		OutputFormat: "custom",
		Metadata: map[string]interface{}{
			"test_run":    "custom_config_test",
			"environment": "testing",
		},
	}

	err := profiler.Start(ctx, config)
	if err != nil {
		t.Fatalf("Failed to start profiler with custom config: %v", err)
	}

	// Let it collect samples
	time.Sleep(200 * time.Millisecond)

	data, err := profiler.Stop()
	if err != nil {
		t.Fatalf("Failed to stop profiler: %v", err)
	}

	// Verify custom metadata was preserved
	if data.Metadata["test_run"] != "custom_config_test" {
		t.Error("Custom metadata not preserved")
	}

	if data.Metadata["environment"] != "testing" {
		t.Error("Custom metadata not preserved")
	}

	// Should have limited samples due to MaxSamples setting
	systemSampleCount := 0
	for _, sample := range data.Samples {
		if sample.EventName == "" { // System samples don't have event names
			systemSampleCount++
		}
	}

	if systemSampleCount > 5 {
		t.Errorf("Should have at most 5 system samples due to MaxSamples, got %d", systemSampleCount)
	}
}

func TestProfilerMemoryMetrics(t *testing.T) {
	profiler := NewSystemProfiler()
	ctx := context.Background()

	config := DefaultProfilerConfig()
	config.SampleInterval = 30 * time.Millisecond

	err := profiler.Start(ctx, config)
	if err != nil {
		t.Fatalf("Failed to start profiler: %v", err)
	}

	// Allocate some memory to see changes
	data := make([][]byte, 100)
	for i := range data {
		data[i] = make([]byte, 1024) // 1KB each
	}

	// Let profiler collect samples
	time.Sleep(200 * time.Millisecond)

	profileData, err := profiler.Stop()
	if err != nil {
		t.Fatalf("Failed to stop profiler: %v", err)
	}

	// Check memory statistics in summary
	if memory, exists := profileData.Summary["memory"]; exists {
		memoryMap, ok := memory.(map[string]interface{})
		if !ok {
			t.Error("Memory summary should be a map")
		} else {
			if _, exists := memoryMap["average_bytes"]; !exists {
				t.Error("Memory summary should include average bytes")
			}

			if _, exists := memoryMap["max_bytes"]; !exists {
				t.Error("Memory summary should include max bytes")
			}

			if _, exists := memoryMap["min_bytes"]; !exists {
				t.Error("Memory summary should include min bytes")
			}

			if sampleCount, exists := memoryMap["sample_count"]; !exists {
				t.Error("Memory summary should include sample count")
			} else if count, ok := sampleCount.(int); !ok || count <= 0 {
				t.Error("Memory sample count should be positive")
			}
		}
	} else {
		t.Error("Summary should include memory statistics")
	}

	// Keep reference to prevent GC
	_ = data
}

func TestConcurrentProfilerAccess(t *testing.T) {
	profiler := NewSystemProfiler()
	ctx := context.Background()

	err := profiler.Start(ctx, nil)
	if err != nil {
		t.Fatalf("Failed to start profiler: %v", err)
	}

	// Test concurrent access
	done := make(chan struct{}, 3)

	// Goroutine 1: Record events
	go func() {
		for i := 0; i < 10; i++ {
			profiler.RecordEvent("test_event", map[string]interface{}{"iteration": i})
			time.Sleep(10 * time.Millisecond)
		}
		done <- struct{}{}
	}()

	// Goroutine 2: Add metrics
	go func() {
		for i := 0; i < 10; i++ {
			profiler.AddMetric(fmt.Sprintf("metric_%d", i), i*10)
			time.Sleep(15 * time.Millisecond)
		}
		done <- struct{}{}
	}()

	// Goroutine 3: Take snapshots
	go func() {
		for i := 0; i < 5; i++ {
			_, err := profiler.GetSnapshot()
			if err != nil {
				t.Errorf("Snapshot failed: %v", err)
			}
			time.Sleep(25 * time.Millisecond)
		}
		done <- struct{}{}
	}()

	// Wait for all goroutines
	for i := 0; i < 3; i++ {
		<-done
	}

	data, err := profiler.Stop()
	if err != nil {
		t.Fatalf("Failed to stop profiler: %v", err)
	}

	// Should have recorded events and metrics without errors
	if len(data.Samples) == 0 {
		t.Error("Should have collected samples during concurrent access")
	}
}
