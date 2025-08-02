package main

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"os"

	"github.com/atsentia/tinytroupe-go/pkg/agent"
	"github.com/atsentia/tinytroupe-go/pkg/config"
	"github.com/atsentia/tinytroupe-go/pkg/environment"
)

func main() {
	log.SetOutput(os.Stdout)
	fmt.Println("=== TinyTroupe Go LLM Chat Example ===")
	fmt.Println("")

	cfg := config.DefaultConfig()
	cfg.MaxTokens = 150

	// Load agents from JSON files
	fmt.Println("Loading agents...")
	lisa, err := loadAgentFromJSON("examples/agents/lisa.json", cfg)
	if err != nil {
		log.Fatalf("Failed to load Lisa: %v", err)
	}

	oscar, err := loadAgentFromJSON("examples/agents/oscar.json", cfg)
	if err != nil {
		log.Fatalf("Failed to load Oscar: %v", err)
	}

	fmt.Printf("✓ Loaded %s (%s)\n", lisa.Name, getOccupationTitle(lisa))
	fmt.Printf("✓ Loaded %s (%s)\n", oscar.Name, getOccupationTitle(oscar))
	fmt.Println("")

	// Create a shared environment for the chat
	fmt.Println("Setting up chat environment...")
	world := environment.NewTinyWorld("ChatRoom", cfg, lisa, oscar)
	world.MakeEveryoneAccessible()

	fmt.Printf("✓ Created chat room with %d participants\n", len(world.Agents))
	fmt.Println("")

	// Start conversation using OpenAI
	fmt.Println("=== Starting LLM Conversation ===")
	fmt.Println("")

	world.Broadcast("You are at a networking event. Introduce yourself and chat about your work and interests.", nil)

	ctx := context.Background()
	steps := 3
	if err := world.Run(ctx, steps, nil); err != nil {
		log.Fatalf("Simulation failed: %v", err)
	}

	fmt.Println("")
	fmt.Println("=== LLM Chat Example Complete ===")
}

// loadAgentFromJSON loads a TinyPerson from a JSON file
func loadAgentFromJSON(filename string, cfg *config.Config) (*agent.TinyPerson, error) {
	data, err := os.ReadFile(filename)
	if err != nil {
		return nil, fmt.Errorf("failed to read file: %w", err)
	}

	var agentSpec struct {
		Type    string        `json:"type"`
		Persona agent.Persona `json:"persona"`
	}

	if err := json.Unmarshal(data, &agentSpec); err != nil {
		return nil, fmt.Errorf("failed to parse JSON: %w", err)
	}

	if agentSpec.Type != "TinyPerson" {
		return nil, fmt.Errorf("invalid agent type: %s", agentSpec.Type)
	}

	// Create agent with the loaded persona
	person := agent.NewTinyPerson(agentSpec.Persona.Name, cfg)
	person.Persona = &agentSpec.Persona

	return person, nil
}

// getOccupationTitle extracts the occupation title from an agent's persona
func getOccupationTitle(person *agent.TinyPerson) string {
	if occupation, ok := person.Persona.Occupation.(map[string]interface{}); ok {
		if title, ok := occupation["title"].(string); ok {
			return title
		}
	}
	return "Unknown"
}
