package environment

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"math/rand"
	"sync"
	"time"

	"github.com/atsentia/tinytroupe-go/pkg/agent"
	"github.com/atsentia/tinytroupe-go/pkg/config"
)

// TinyWorld represents a simulation environment where agents interact
type TinyWorld struct {
	Name            string
	Agents          []*agent.TinyPerson
	nameToAgent     map[string]*agent.TinyPerson
	CurrentDateTime *time.Time
	config          *config.Config
	mutex           sync.RWMutex
}

// NewTinyWorld creates a new simulation environment
func NewTinyWorld(name string, cfg *config.Config, agents ...*agent.TinyPerson) *TinyWorld {
	now := time.Now()
	world := &TinyWorld{
		Name:            name,
		Agents:          make([]*agent.TinyPerson, 0),
		nameToAgent:     make(map[string]*agent.TinyPerson),
		CurrentDateTime: &now,
		config:          cfg,
	}

	world.AddAgents(agents...)
	return world
}

// GetName returns the environment name (implements agent.Environment interface)
func (tw *TinyWorld) GetName() string {
	return tw.Name
}

// GetCurrentDateTime returns current simulation time (implements agent.Environment interface)
func (tw *TinyWorld) GetCurrentDateTime() *time.Time {
	return tw.CurrentDateTime
}

// AddAgent adds an agent to the environment
func (tw *TinyWorld) AddAgent(ag *agent.TinyPerson) error {
	tw.mutex.Lock()
	defer tw.mutex.Unlock()

	// Check if agent name is unique
	if _, exists := tw.nameToAgent[ag.Name]; exists {
		return fmt.Errorf("agent name %s already exists in environment", ag.Name)
	}

	tw.Agents = append(tw.Agents, ag)
	tw.nameToAgent[ag.Name] = ag
	ag.SetEnvironment(tw)

	log.Printf("[%s] Added agent: %s", tw.Name, ag.Name)
	return nil
}

// AddAgents adds multiple agents to the environment
func (tw *TinyWorld) AddAgents(agents ...*agent.TinyPerson) error {
	for _, ag := range agents {
		if err := tw.AddAgent(ag); err != nil {
			return err
		}
	}
	return nil
}

// RemoveAgent removes an agent from the environment
func (tw *TinyWorld) RemoveAgent(agentName string) error {
	tw.mutex.Lock()
	defer tw.mutex.Unlock()

	for i, ag := range tw.Agents {
		if ag.Name == agentName {
			tw.Agents = append(tw.Agents[:i], tw.Agents[i+1:]...)
			delete(tw.nameToAgent, agentName)
			ag.SetEnvironment(nil)
			log.Printf("[%s] Removed agent: %s", tw.Name, agentName)
			return nil
		}
	}

	return fmt.Errorf("agent %s not found in environment", agentName)
}

// GetAgentByName returns an agent by name
func (tw *TinyWorld) GetAgentByName(name string) *agent.TinyPerson {
	tw.mutex.RLock()
	defer tw.mutex.RUnlock()

	return tw.nameToAgent[name]
}

// MakeEveryoneAccessible makes all agents accessible to each other
func (tw *TinyWorld) MakeEveryoneAccessible() {
	tw.mutex.RLock()
	defer tw.mutex.RUnlock()

	for _, agent1 := range tw.Agents {
		for _, agent2 := range tw.Agents {
			if agent1.Name != agent2.Name {
				agent1.MakeAgentAccessible(agent2)
			}
		}
	}

	log.Printf("[%s] Made all agents accessible to each other", tw.Name)
}

// Broadcast sends a message to all agents in the environment
func (tw *TinyWorld) Broadcast(message string, source *agent.TinyPerson) error {
	tw.mutex.RLock()
	defer tw.mutex.RUnlock()

	log.Printf("[%s] Broadcasting: %s", tw.Name, message)

	for _, ag := range tw.Agents {
		if ag != source { // Don't send to the source
			if err := ag.Listen(message, source); err != nil {
				log.Printf("[%s] Failed to deliver broadcast to %s: %v", tw.Name, ag.Name, err)
			}
		}
	}

	return nil
}

// HandleAction processes actions from agents (implements agent.Environment interface)
func (tw *TinyWorld) HandleAction(source *agent.TinyPerson, action agent.Action) error {
	switch action.Type {
	case "TALK":
		return tw.handleTalk(source, action)
	case "REACH_OUT":
		return tw.handleReachOut(source, action)
	default:
		// Other actions don't need environment intervention
		return nil
	}
}

// contentToString converts action content to string for communication
func contentToString(content interface{}) string {
	switch v := content.(type) {
	case string:
		return v
	case map[string]interface{}, []interface{}:
		// Convert complex content to JSON string
		if jsonBytes, err := json.Marshal(v); err == nil {
			return string(jsonBytes)
		}
		return fmt.Sprintf("%v", v)
	default:
		return fmt.Sprintf("%v", v)
	}
}

// handleTalk processes TALK actions
func (tw *TinyWorld) handleTalk(source *agent.TinyPerson, action agent.Action) error {
	contentStr := contentToString(action.Content)
	
	if action.Target == "" {
		// Broadcast if no target specified
		return tw.Broadcast(contentStr, source)
	}

	target := tw.GetAgentByName(action.Target)
	if target == nil {
		log.Printf("[%s] Talk target %s not found, broadcasting instead", tw.Name, action.Target)
		return tw.Broadcast(contentStr, source)
	}

	log.Printf("[%s] %s -> %s: %s", tw.Name, source.Name, target.Name, contentStr)
	return target.Listen(contentStr, source)
}

// handleReachOut processes REACH_OUT actions
func (tw *TinyWorld) handleReachOut(source *agent.TinyPerson, action agent.Action) error {
	target := tw.GetAgentByName(action.Target)
	if target == nil {
		return fmt.Errorf("reach out target %s not found", action.Target)
	}

	// Make agents accessible to each other
	source.MakeAgentAccessible(target)
	target.MakeAgentAccessible(source)

	// Notify both agents
	successMsg := fmt.Sprintf("%s was successfully reached out, and is now available for interaction.", target.Name)
	if err := source.Listen(successMsg, nil); err != nil {
		log.Printf("[%s] Failed to notify source of successful reach out: %v", tw.Name, err)
	}

	reachedMsg := fmt.Sprintf("%s reached out to you, and is now available for interaction.", source.Name)
	if err := target.Listen(reachedMsg, nil); err != nil {
		log.Printf("[%s] Failed to notify target of reach out: %v", tw.Name, err)
	}

	log.Printf("[%s] %s reached out to %s", tw.Name, source.Name, target.Name)
	return nil
}

// Step runs one simulation step
func (tw *TinyWorld) Step(ctx context.Context, timeDelta *time.Duration) error {
	// Advance time if specified
	if timeDelta != nil {
		tw.mutex.Lock()
		*tw.CurrentDateTime = tw.CurrentDateTime.Add(*timeDelta)
		tw.mutex.Unlock()
		log.Printf("[%s] Advanced time to %s", tw.Name, tw.CurrentDateTime.Format(time.RFC3339))
	}

	if tw.config.ParallelAgentActions {
		return tw.stepParallel(ctx)
	}
	return tw.stepSequential(ctx)
}

// stepSequential runs agents sequentially
func (tw *TinyWorld) stepSequential(ctx context.Context) error {
	tw.mutex.RLock()
	agents := make([]*agent.TinyPerson, len(tw.Agents))
	copy(agents, tw.Agents)
	tw.mutex.RUnlock()

	// Randomize order for fairness
	rand.Shuffle(len(agents), func(i, j int) {
		agents[i], agents[j] = agents[j], agents[i]
	})

	for _, ag := range agents {
		log.Printf("[%s] Agent %s is acting", tw.Name, ag.Name)

		actions, err := ag.Act(ctx)
		if err != nil {
			log.Printf("[%s] Agent %s failed to act: %v", tw.Name, ag.Name, err)
			continue
		}

		// Handle actions
		for _, action := range actions {
			if err := tw.HandleAction(ag, action); err != nil {
				log.Printf("[%s] Failed to handle action from %s: %v", tw.Name, ag.Name, err)
			}
		}

		// Clear agent's action buffer
		ag.PopLatestActions()
	}

	return nil
}

// stepParallel runs agents in parallel
func (tw *TinyWorld) stepParallel(ctx context.Context) error {
	tw.mutex.RLock()
	agents := make([]*agent.TinyPerson, len(tw.Agents))
	copy(agents, tw.Agents)
	tw.mutex.RUnlock()

	var wg sync.WaitGroup
	actionsChan := make(chan struct {
		agent   *agent.TinyPerson
		actions []agent.Action
		err     error
	}, len(agents))

	// Run all agents in parallel
	for _, ag := range agents {
		wg.Add(1)
		go func(ag *agent.TinyPerson) {
			defer wg.Done()

			log.Printf("[%s] Agent %s is acting (parallel)", tw.Name, ag.Name)
			actions, err := ag.Act(ctx)

			actionsChan <- struct {
				agent   *agent.TinyPerson
				actions []agent.Action
				err     error
			}{ag, actions, err}
		}(ag)
	}

	// Wait for all agents to complete
	go func() {
		wg.Wait()
		close(actionsChan)
	}()

	// Process all actions
	for result := range actionsChan {
		if result.err != nil {
			log.Printf("[%s] Agent %s failed to act: %v", tw.Name, result.agent.Name, result.err)
			continue
		}

		// Handle actions
		for _, action := range result.actions {
			if err := tw.HandleAction(result.agent, action); err != nil {
				log.Printf("[%s] Failed to handle action from %s: %v", tw.Name, result.agent.Name, err)
			}
		}

		// Clear agent's action buffer
		result.agent.PopLatestActions()
	}

	return nil
}

// Run executes multiple simulation steps
func (tw *TinyWorld) Run(ctx context.Context, steps int, timeDelta *time.Duration) error {
	for i := 0; i < steps; i++ {
		log.Printf("[%s] Running step %d of %d", tw.Name, i+1, steps)

		if err := tw.Step(ctx, timeDelta); err != nil {
			return fmt.Errorf("step %d failed: %w", i+1, err)
		}

		// Check if context was cancelled
		select {
		case <-ctx.Done():
			return ctx.Err()
		default:
		}
	}

	log.Printf("[%s] Completed %d steps", tw.Name, steps)
	return nil
}
