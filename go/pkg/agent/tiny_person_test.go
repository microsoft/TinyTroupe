package agent

import (
	"testing"

	"github.com/microsoft/TinyTroupe/go/pkg/config"
)

func TestTinyPersonCreation(t *testing.T) {
	cfg := config.DefaultConfig()
	person := NewTinyPerson("TestAgent", cfg)

	if person.Name != "TestAgent" {
		t.Errorf("Expected name 'TestAgent', got '%s'", person.Name)
	}

	if person.Persona.Name != "TestAgent" {
		t.Errorf("Expected persona name 'TestAgent', got '%s'", person.Persona.Name)
	}

	if person.MentalState.Emotions != "Feeling nothing in particular, just calm." {
		t.Errorf("Unexpected default emotion state")
	}
}

func TestPersonaDefinition(t *testing.T) {
	cfg := config.DefaultConfig()
	person := NewTinyPerson("TestAgent", cfg)

	// Test age definition
	person.Define("age", 25)
	if person.Persona.Age != 25 {
		t.Errorf("Expected age 25, got %d", person.Persona.Age)
	}

	// Test nationality definition
	person.Define("nationality", "American")
	if person.Persona.Nationality != "American" {
		t.Errorf("Expected nationality 'American', got '%s'", person.Persona.Nationality)
	}

	// Test interests definition
	interests := []string{"reading", "coding", "music"}
	person.Define("interests", interests)
	if len(person.Persona.Interests) != 3 {
		t.Errorf("Expected 3 interests, got %d", len(person.Persona.Interests))
	}
	if person.Persona.Interests[0] != "reading" {
		t.Errorf("Expected first interest 'reading', got '%s'", person.Persona.Interests[0])
	}

	// Test occupation definition
	occupation := map[string]interface{}{
		"title":        "Software Engineer",
		"organization": "Tech Corp",
	}
	person.Define("occupation", occupation)
	if occMap, ok := person.Persona.Occupation.(map[string]interface{}); ok {
		if occMap["title"] != "Software Engineer" {
			t.Errorf("Expected occupation title 'Software Engineer'")
		}
	} else {
		t.Errorf("Expected occupation to be a map")
	}
}

func TestListening(t *testing.T) {
	cfg := config.DefaultConfig()
	person := NewTinyPerson("TestAgent", cfg)

	// Test listening without source
	err := person.Listen("Hello, how are you?", nil)
	if err != nil {
		t.Errorf("Listen failed: %v", err)
	}

	// Check that memory was updated
	episode := person.EpisodicMemory.GetCurrentEpisode()
	if len(episode) != 1 {
		t.Errorf("Expected 1 memory item, got %d", len(episode))
	}

	if episode[0].Type != "stimulus" {
		t.Errorf("Expected stimulus type, got '%s'", episode[0].Type)
	}

	if episode[0].Role != "user" {
		t.Errorf("Expected user role, got '%s'", episode[0].Role)
	}
}

func TestListeningWithSource(t *testing.T) {
	cfg := config.DefaultConfig()
	person1 := NewTinyPerson("Alice", cfg)
	person2 := NewTinyPerson("Bob", cfg)

	// Test listening with source
	err := person1.Listen("Hello Alice!", person2)
	if err != nil {
		t.Errorf("Listen with source failed: %v", err)
	}

	// Check memory content
	episode := person1.EpisodicMemory.GetCurrentEpisode()
	if len(episode) != 1 {
		t.Errorf("Expected 1 memory item, got %d", len(episode))
	}

	stimuli, ok := episode[0].Content["stimuli"].([]interface{})
	if !ok {
		t.Errorf("Expected stimuli array in memory content")
	}

	if len(stimuli) != 1 {
		t.Errorf("Expected 1 stimulus, got %d", len(stimuli))
	}

	stimulus, ok := stimuli[0].(map[string]interface{})
	if !ok {
		t.Errorf("Expected stimulus to be a map")
	}

	if stimulus["source"] != "Bob" {
		t.Errorf("Expected source 'Bob', got '%v'", stimulus["source"])
	}

	if stimulus["content"] != "Hello Alice!" {
		t.Errorf("Expected content 'Hello Alice!', got '%v'", stimulus["content"])
	}
}

func TestAgentAccessibility(t *testing.T) {
	cfg := config.DefaultConfig()
	alice := NewTinyPerson("Alice", cfg)
	bob := NewTinyPerson("Bob", cfg)

	// Initially, agents should not be accessible to each other
	if len(alice.AccessibleAgents) != 0 {
		t.Errorf("Expected 0 accessible agents initially, got %d", len(alice.AccessibleAgents))
	}

	// Make Bob accessible to Alice
	alice.MakeAgentAccessible(bob)

	if len(alice.AccessibleAgents) != 1 {
		t.Errorf("Expected 1 accessible agent, got %d", len(alice.AccessibleAgents))
	}

	if alice.AccessibleAgents[0].Name != "Bob" {
		t.Errorf("Expected accessible agent 'Bob', got '%s'", alice.AccessibleAgents[0].Name)
	}

	// Check mental state was updated
	if len(alice.MentalState.Accessible) != 1 {
		t.Errorf("Expected 1 accessible agent in mental state, got %d", len(alice.MentalState.Accessible))
	}

	// Adding the same agent again should not create duplicates
	alice.MakeAgentAccessible(bob)
	if len(alice.AccessibleAgents) != 1 {
		t.Errorf("Expected still 1 accessible agent after duplicate add, got %d", len(alice.AccessibleAgents))
	}
}

func TestActionBuffer(t *testing.T) {
	cfg := config.DefaultConfig()
	person := NewTinyPerson("TestAgent", cfg)

	// Initially buffer should be empty
	actions := person.PopLatestActions()
	if len(actions) != 0 {
		t.Errorf("Expected empty action buffer initially, got %d actions", len(actions))
	}

	// Add some actions manually (simulating what Act() would do)
	action1 := Action{Type: "TALK", Content: "Hello", Target: "Someone"}
	action2 := Action{Type: "THINK", Content: "I should respond"}

	person.ActionsBuffer = append(person.ActionsBuffer, action1, action2)

	// Pop actions
	actions = person.PopLatestActions()
	if len(actions) != 2 {
		t.Errorf("Expected 2 actions, got %d", len(actions))
	}

	if actions[0].Type != "TALK" {
		t.Errorf("Expected first action type 'TALK', got '%s'", actions[0].Type)
	}

	if actions[1].Type != "THINK" {
		t.Errorf("Expected second action type 'THINK', got '%s'", actions[1].Type)
	}

	// Buffer should be empty after pop
	actions = person.PopLatestActions()
	if len(actions) != 0 {
		t.Errorf("Expected empty buffer after pop, got %d actions", len(actions))
	}
}

func TestCognitiveStateUpdate(t *testing.T) {
	cfg := config.DefaultConfig()
	person := NewTinyPerson("TestAgent", cfg)

	// Update cognitive state
	state := map[string]interface{}{
		"emotions": "feeling excited",
		"goals":    []interface{}{"learn Go", "build AI"},
		"context":  []interface{}{"programming", "testing"},
	}

	person.updateCognitiveState(state)

	if person.MentalState.Emotions != "feeling excited" {
		t.Errorf("Expected emotions 'feeling excited', got '%s'", person.MentalState.Emotions)
	}

	if len(person.MentalState.Goals) != 2 {
		t.Errorf("Expected 2 goals, got %d", len(person.MentalState.Goals))
	}

	if person.MentalState.Goals[0] != "learn Go" {
		t.Errorf("Expected first goal 'learn Go', got '%s'", person.MentalState.Goals[0])
	}

	if len(person.MentalState.Context) != 2 {
		t.Errorf("Expected 2 context items, got %d", len(person.MentalState.Context))
	}

	if person.MentalState.Context[0] != "programming" {
		t.Errorf("Expected first context 'programming', got '%s'", person.MentalState.Context[0])
	}
}
