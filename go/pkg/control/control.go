// Package control provides simulation control and orchestration capabilities.
// This is a core module for managing the lifecycle of TinyTroupe simulations.
package control

import (
	"context"
	"sync"
	"time"
)

// SimulationController manages the overall simulation lifecycle
type SimulationController interface {
	// Start begins the simulation
	Start(ctx context.Context) error

	// Stop gracefully stops the simulation
	Stop(ctx context.Context) error

	// Pause temporarily halts the simulation
	Pause() error

	// Resume continues a paused simulation
	Resume() error

	// GetStatus returns the current simulation status
	GetStatus() SimulationStatus

	// SetTimeAdvancement configures how simulation time progresses
	SetTimeAdvancement(advancement TimeAdvancement)
}

// SimulationStatus represents the current state of a simulation
type SimulationStatus struct {
	State       SimulationState
	StartTime   time.Time
	CurrentTime time.Time
	Duration    time.Duration
	StepCount   int64
}

// SimulationState represents possible simulation states
type SimulationState int

const (
	SimulationStateStopped SimulationState = iota
	SimulationStateRunning
	SimulationStatePaused
	SimulationStateError
)

func (s SimulationState) String() string {
	switch s {
	case SimulationStateStopped:
		return "stopped"
	case SimulationStateRunning:
		return "running"
	case SimulationStatePaused:
		return "paused"
	case SimulationStateError:
		return "error"
	default:
		return "unknown"
	}
}

// TimeAdvancement defines how simulation time progresses
type TimeAdvancement interface {
	// Advance returns the next time step
	Advance(current time.Time) time.Time

	// GetInterval returns the time interval between steps
	GetInterval() time.Duration
}

// LinearTimeAdvancement advances time by a fixed interval
type LinearTimeAdvancement struct {
	Interval time.Duration
}

// Advance implements TimeAdvancement
func (lta *LinearTimeAdvancement) Advance(current time.Time) time.Time {
	return current.Add(lta.Interval)
}

// GetInterval implements TimeAdvancement
func (lta *LinearTimeAdvancement) GetInterval() time.Duration {
	return lta.Interval
}

// SimulationConfig holds configuration for simulation control
type SimulationConfig struct {
	MaxSteps         int64
	MaxDuration      time.Duration
	TimeAdvancement  TimeAdvancement
	AutoSave         bool
	AutoSaveInterval time.Duration
}

// DefaultSimulationConfig returns a default simulation configuration
func DefaultSimulationConfig() *SimulationConfig {
	return &SimulationConfig{
		MaxSteps:         1000,
		MaxDuration:      time.Hour,
		TimeAdvancement:  &LinearTimeAdvancement{Interval: time.Minute},
		AutoSave:         true,
		AutoSaveInterval: 10 * time.Minute,
	}
}

// BasicSimulationController provides a simple implementation of SimulationController.
// It manages simulation time progression and basic lifecycle operations.
type BasicSimulationController struct {
	mu     sync.Mutex
	config *SimulationConfig
	status SimulationStatus
	ticker *time.Ticker
	cancel context.CancelFunc
	paused bool
}

// NewBasicSimulationController creates a controller with the provided configuration.
func NewBasicSimulationController(config *SimulationConfig) *BasicSimulationController {
	cfg := config
	if cfg == nil {
		cfg = DefaultSimulationConfig()
	}
	if cfg.TimeAdvancement == nil {
		cfg.TimeAdvancement = &LinearTimeAdvancement{Interval: time.Second}
	}
	return &BasicSimulationController{config: cfg}
}

// Start begins the simulation loop.
func (c *BasicSimulationController) Start(ctx context.Context) error {
	c.mu.Lock()
	defer c.mu.Unlock()

	if c.status.State == SimulationStateRunning {
		return nil
	}

	c.status.State = SimulationStateRunning
	c.status.StartTime = time.Now()
	c.status.CurrentTime = c.status.StartTime
	c.status.StepCount = 0

	var runCtx context.Context
	runCtx, c.cancel = context.WithCancel(ctx)
	c.ticker = time.NewTicker(c.config.TimeAdvancement.GetInterval())
	go c.run(runCtx)
	return nil
}

func (c *BasicSimulationController) run(ctx context.Context) {
	for {
		c.mu.Lock()
		ticker := c.ticker
		paused := c.paused
		c.mu.Unlock()

		if paused || ticker == nil {
			select {
			case <-ctx.Done():
				c.Stop(context.Background())
				return
			case <-time.After(10 * time.Millisecond):
				continue
			}
		}

		select {
		case <-ctx.Done():
			c.Stop(context.Background())
			return
		case <-ticker.C:
			c.step()
		}
	}
}

func (c *BasicSimulationController) step() {
	c.mu.Lock()
	defer c.mu.Unlock()

	if c.paused || c.status.State != SimulationStateRunning {
		return
	}

	c.status.StepCount++
	c.status.CurrentTime = c.config.TimeAdvancement.Advance(c.status.CurrentTime)
	c.status.Duration = time.Since(c.status.StartTime)

	if (c.config.MaxSteps > 0 && c.status.StepCount >= c.config.MaxSteps) ||
		(c.config.MaxDuration > 0 && c.status.Duration >= c.config.MaxDuration) {
		// trigger stop asynchronously to avoid deadlock
		go c.Stop(context.Background())
	}
}

// Stop terminates the simulation.
func (c *BasicSimulationController) Stop(ctx context.Context) error {
	c.mu.Lock()
	if c.status.State == SimulationStateStopped {
		c.mu.Unlock()
		return nil
	}
	if c.ticker != nil {
		c.ticker.Stop()
		c.ticker = nil
	}
	if c.cancel != nil {
		c.cancel()
		c.cancel = nil
	}
	c.status.State = SimulationStateStopped
	c.mu.Unlock()
	return nil
}

// Pause temporarily halts the simulation.
func (c *BasicSimulationController) Pause() error {
	c.mu.Lock()
	defer c.mu.Unlock()

	if c.status.State != SimulationStateRunning {
		return nil
	}
	c.paused = true
	c.status.State = SimulationStatePaused
	if c.ticker != nil {
		c.ticker.Stop()
		c.ticker = nil
	}
	return nil
}

// Resume continues a paused simulation.
func (c *BasicSimulationController) Resume() error {
	c.mu.Lock()
	defer c.mu.Unlock()

	if c.status.State != SimulationStatePaused {
		return nil
	}
	c.paused = false
	c.status.State = SimulationStateRunning
	if c.ticker == nil {
		c.ticker = time.NewTicker(c.config.TimeAdvancement.GetInterval())
		go c.run(context.Background())
	}
	return nil
}

// GetStatus returns the current simulation status.
func (c *BasicSimulationController) GetStatus() SimulationStatus {
	c.mu.Lock()
	defer c.mu.Unlock()
	return c.status
}

// SetTimeAdvancement configures how simulation time progresses.
func (c *BasicSimulationController) SetTimeAdvancement(advancement TimeAdvancement) {
	c.mu.Lock()
	defer c.mu.Unlock()

	if advancement == nil {
		return
	}
	c.config.TimeAdvancement = advancement
	if c.ticker != nil {
		c.ticker.Stop()
		c.ticker = time.NewTicker(advancement.GetInterval())
	}
}
