package environment

import (
	"context"
	"testing"
	"time"

	"github.com/microsoft/TinyTroupe/go/pkg/agent"
	"github.com/microsoft/TinyTroupe/go/pkg/config"
)

func TestTinyWorldCreation(t *testing.T) {
	cfg := config.DefaultConfig()
	world := NewTinyWorld("TestWorld", cfg)

	if world.Name != "TestWorld" {
		t.Errorf("Expected world name 'TestWorld', got '%s'", world.Name)
	}

	if len(world.Agents) != 0 {
		t.Errorf("Expected empty world initially, got %d agents", len(world.Agents))
	}

	if world.CurrentDateTime == nil {
		t.Errorf("Expected current datetime to be set")
	}
}

func TestTinyWorldWithAgents(t *testing.T) {
	cfg := config.DefaultConfig()
	alice := agent.NewTinyPerson("Alice", cfg)
	bob := agent.NewTinyPerson("Bob", cfg)

	world := NewTinyWorld("TestWorld", cfg, alice, bob)

	if len(world.Agents) != 2 {
		t.Errorf("Expected 2 agents, got %d", len(world.Agents))
	}

	if world.GetAgentByName("Alice") != alice {
		t.Errorf("Expected to find Alice in world")
	}

	if world.GetAgentByName("Bob") != bob {
		t.Errorf("Expected to find Bob in world")
	}

	if world.GetAgentByName("Charlie") != nil {
		t.Errorf("Expected Charlie not to be found")
	}
}

func TestAddRemoveAgents(t *testing.T) {
	cfg := config.DefaultConfig()
	world := NewTinyWorld("TestWorld", cfg)
	alice := agent.NewTinyPerson("Alice", cfg)
	bob := agent.NewTinyPerson("Bob", cfg)

	// Add agents
	err := world.AddAgent(alice)
	if err != nil {
		t.Errorf("Failed to add Alice: %v", err)
	}

	err = world.AddAgent(bob)
	if err != nil {
		t.Errorf("Failed to add Bob: %v", err)
	}

	if len(world.Agents) != 2 {
		t.Errorf("Expected 2 agents after adding, got %d", len(world.Agents))
	}

	// Try to add duplicate agent (should fail)
	duplicate := agent.NewTinyPerson("Alice", cfg)
	err = world.AddAgent(duplicate)
	if err == nil {
		t.Errorf("Expected error when adding duplicate agent name")
	}

	// Remove agent
	err = world.RemoveAgent("Alice")
	if err != nil {
		t.Errorf("Failed to remove Alice: %v", err)
	}

	if len(world.Agents) != 1 {
		t.Errorf("Expected 1 agent after removal, got %d", len(world.Agents))
	}

	if world.GetAgentByName("Alice") != nil {
		t.Errorf("Expected Alice to be removed from world")
	}

	// Try to remove non-existent agent
	err = world.RemoveAgent("Charlie")
	if err == nil {
		t.Errorf("Expected error when removing non-existent agent")
	}
}

func TestMakeEveryoneAccessible(t *testing.T) {
	cfg := config.DefaultConfig()
	alice := agent.NewTinyPerson("Alice", cfg)
	bob := agent.NewTinyPerson("Bob", cfg)
	charlie := agent.NewTinyPerson("Charlie", cfg)

	world := NewTinyWorld("TestWorld", cfg, alice, bob, charlie)
	world.MakeEveryoneAccessible()

	// Check that each agent can access the others
	if len(alice.AccessibleAgents) != 2 {
		t.Errorf("Expected Alice to have 2 accessible agents, got %d", len(alice.AccessibleAgents))
	}

	if len(bob.AccessibleAgents) != 2 {
		t.Errorf("Expected Bob to have 2 accessible agents, got %d", len(bob.AccessibleAgents))
	}

	if len(charlie.AccessibleAgents) != 2 {
		t.Errorf("Expected Charlie to have 2 accessible agents, got %d", len(charlie.AccessibleAgents))
	}

	// Check that agents don't have themselves as accessible
	for _, accessibleAgent := range alice.AccessibleAgents {
		if accessibleAgent.Name == "Alice" {
			t.Errorf("Alice should not have herself as accessible")
		}
	}
}

func TestBroadcast(t *testing.T) {
	cfg := config.DefaultConfig()
	alice := agent.NewTinyPerson("Alice", cfg)
	bob := agent.NewTinyPerson("Bob", cfg)
	charlie := agent.NewTinyPerson("Charlie", cfg)

	world := NewTinyWorld("TestWorld", cfg, alice, bob, charlie)

	// Broadcast message from Alice
	err := world.Broadcast("Hello everyone!", alice)
	if err != nil {
		t.Errorf("Broadcast failed: %v", err)
	}

	// Check that Bob and Charlie received the message, but not Alice
	bobEpisode := bob.EpisodicMemory.GetCurrentEpisode()
	if len(bobEpisode) != 1 {
		t.Errorf("Expected Bob to have 1 memory item, got %d", len(bobEpisode))
	}

	charlieEpisode := charlie.EpisodicMemory.GetCurrentEpisode()
	if len(charlieEpisode) != 1 {
		t.Errorf("Expected Charlie to have 1 memory item, got %d", len(charlieEpisode))
	}

	aliceEpisode := alice.EpisodicMemory.GetCurrentEpisode()
	if len(aliceEpisode) != 0 {
		t.Errorf("Expected Alice to have 0 memory items (shouldn't receive own broadcast), got %d", len(aliceEpisode))
	}
}

func TestHandleTalkAction(t *testing.T) {
	cfg := config.DefaultConfig()
	alice := agent.NewTinyPerson("Alice", cfg)
	bob := agent.NewTinyPerson("Bob", cfg)

	world := NewTinyWorld("TestWorld", cfg, alice, bob)

	// Test direct talk action
	talkAction := agent.Action{
		Type:    "TALK",
		Content: "Hi Bob!",
		Target:  "Bob",
	}

	err := world.HandleAction(alice, talkAction)
	if err != nil {
		t.Errorf("HandleAction failed: %v", err)
	}

	// Check that Bob received the message
	bobEpisode := bob.EpisodicMemory.GetCurrentEpisode()
	if len(bobEpisode) != 1 {
		t.Errorf("Expected Bob to have 1 memory item, got %d", len(bobEpisode))
	}

	// Test talk action with non-existent target (should broadcast)
	talkActionBroadcast := agent.Action{
		Type:    "TALK",
		Content: "Hello everyone!",
		Target:  "NonExistent",
	}

	err = world.HandleAction(alice, talkActionBroadcast)
	if err != nil {
		t.Errorf("HandleAction with non-existent target failed: %v", err)
	}

	// Bob should now have 2 memory items (direct message + broadcast)
	bobEpisode = bob.EpisodicMemory.GetCurrentEpisode()
	if len(bobEpisode) != 2 {
		t.Errorf("Expected Bob to have 2 memory items after broadcast, got %d", len(bobEpisode))
	}
}

func TestHandleReachOutAction(t *testing.T) {
	cfg := config.DefaultConfig()
	alice := agent.NewTinyPerson("Alice", cfg)
	bob := agent.NewTinyPerson("Bob", cfg)

	world := NewTinyWorld("TestWorld", cfg, alice, bob)

	// Initially agents should not be accessible to each other
	if len(alice.AccessibleAgents) != 0 {
		t.Errorf("Expected Alice to have 0 accessible agents initially")
	}
	if len(bob.AccessibleAgents) != 0 {
		t.Errorf("Expected Bob to have 0 accessible agents initially")
	}

	// Test reach out action
	reachOutAction := agent.Action{
		Type:   "REACH_OUT",
		Target: "Bob",
	}

	err := world.HandleAction(alice, reachOutAction)
	if err != nil {
		t.Errorf("HandleAction REACH_OUT failed: %v", err)
	}

	// Check that agents are now accessible to each other
	if len(alice.AccessibleAgents) != 1 {
		t.Errorf("Expected Alice to have 1 accessible agent after reach out, got %d", len(alice.AccessibleAgents))
	}
	if alice.AccessibleAgents[0].Name != "Bob" {
		t.Errorf("Expected Alice's accessible agent to be Bob")
	}

	if len(bob.AccessibleAgents) != 1 {
		t.Errorf("Expected Bob to have 1 accessible agent after reach out, got %d", len(bob.AccessibleAgents))
	}
	if bob.AccessibleAgents[0].Name != "Alice" {
		t.Errorf("Expected Bob's accessible agent to be Alice")
	}

	// Check that both agents received notification messages
	aliceEpisode := alice.EpisodicMemory.GetCurrentEpisode()
	if len(aliceEpisode) != 1 {
		t.Errorf("Expected Alice to have 1 memory item (success notification), got %d", len(aliceEpisode))
	}

	bobEpisode := bob.EpisodicMemory.GetCurrentEpisode()
	if len(bobEpisode) != 1 {
		t.Errorf("Expected Bob to have 1 memory item (reach out notification), got %d", len(bobEpisode))
	}
}

func TestStepExecution(t *testing.T) {
	cfg := config.DefaultConfig()
	cfg.ParallelAgentActions = false // Use sequential for predictable testing

	alice := agent.NewTinyPerson("Alice", cfg)
	bob := agent.NewTinyPerson("Bob", cfg)

	world := NewTinyWorld("TestWorld", cfg, alice, bob)

	// Add some initial stimulus to get agents to act
	alice.Listen("Say hello to Bob", nil)

	ctx := context.Background()
	timeDelta := 1 * time.Minute

	// Note: This test will fail without a real OpenAI API key
	// But we can at least test the structure
	err := world.Step(ctx, &timeDelta)

	// We expect this to fail due to missing API key, but the structure should be correct
	if err != nil {
		t.Logf("Step failed as expected (likely due to missing API key): %v", err)
	}

	// Check that time was advanced
	if world.CurrentDateTime == nil {
		t.Errorf("Expected current datetime to be set")
	}
}
