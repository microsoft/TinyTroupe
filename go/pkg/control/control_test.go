package control

import (
	"context"
	"testing"
	"time"
)

func TestLinearTimeAdvancement(t *testing.T) {
	lta := &LinearTimeAdvancement{Interval: time.Minute}

	current := time.Now()
	next := lta.Advance(current)

	if next.Sub(current) != time.Minute {
		t.Errorf("Expected advancement of 1 minute, got %v", next.Sub(current))
	}

	if lta.GetInterval() != time.Minute {
		t.Errorf("Expected interval of 1 minute, got %v", lta.GetInterval())
	}
}

func TestSimulationStateString(t *testing.T) {
	tests := []struct {
		state    SimulationState
		expected string
	}{
		{SimulationStateStopped, "stopped"},
		{SimulationStateRunning, "running"},
		{SimulationStatePaused, "paused"},
		{SimulationStateError, "error"},
	}

	for _, test := range tests {
		if test.state.String() != test.expected {
			t.Errorf("Expected %s, got %s", test.expected, test.state.String())
		}
	}
}

func TestDefaultSimulationConfig(t *testing.T) {
	config := DefaultSimulationConfig()

	if config.MaxSteps != 1000 {
		t.Errorf("Expected MaxSteps to be 1000, got %d", config.MaxSteps)
	}

	if config.MaxDuration != time.Hour {
		t.Errorf("Expected MaxDuration to be 1 hour, got %v", config.MaxDuration)
	}

	if !config.AutoSave {
		t.Error("Expected AutoSave to be true")
	}

	if config.AutoSaveInterval != 10*time.Minute {
		t.Errorf("Expected AutoSaveInterval to be 10 minutes, got %v", config.AutoSaveInterval)
	}

	if config.TimeAdvancement == nil {
		t.Error("Expected TimeAdvancement to be set")
	}
}

func TestBasicSimulationControllerLifecycle(t *testing.T) {
	cfg := &SimulationConfig{TimeAdvancement: &LinearTimeAdvancement{Interval: time.Millisecond}}
	controller := NewBasicSimulationController(cfg)
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	if err := controller.Start(ctx); err != nil {
		t.Fatalf("Start failed: %v", err)
	}
	time.Sleep(2 * time.Millisecond)
	if controller.GetStatus().State != SimulationStateRunning {
		t.Fatalf("Expected running state, got %v", controller.GetStatus().State)
	}

	if err := controller.Pause(); err != nil {
		t.Fatalf("Pause failed: %v", err)
	}
	if controller.GetStatus().State != SimulationStatePaused {
		t.Fatalf("Expected paused state, got %v", controller.GetStatus().State)
	}

	if err := controller.Resume(); err != nil {
		t.Fatalf("Resume failed: %v", err)
	}
	if controller.GetStatus().State != SimulationStateRunning {
		t.Fatalf("Expected running state after resume, got %v", controller.GetStatus().State)
	}

	if err := controller.Stop(ctx); err != nil {
		t.Fatalf("Stop failed: %v", err)
	}
	if controller.GetStatus().State != SimulationStateStopped {
		t.Fatalf("Expected stopped state, got %v", controller.GetStatus().State)
	}
}

func TestBasicSimulationControllerAutoStopByMaxSteps(t *testing.T) {
	cfg := &SimulationConfig{MaxSteps: 3, TimeAdvancement: &LinearTimeAdvancement{Interval: time.Millisecond}}
	controller := NewBasicSimulationController(cfg)
	if err := controller.Start(context.Background()); err != nil {
		t.Fatalf("Start failed: %v", err)
	}

	time.Sleep(10 * time.Millisecond)
	status := controller.GetStatus()
	if status.StepCount != 3 {
		t.Fatalf("Expected 3 steps, got %d", status.StepCount)
	}
	if status.State != SimulationStateStopped {
		t.Fatalf("Expected stopped state, got %v", status.State)
	}
}
