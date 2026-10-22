package main

import (
	"encoding/json"
	"fmt"
	"log"
	"os"

	"github.com/microsoft/TinyTroupe/go/pkg/agent"
	"github.com/microsoft/TinyTroupe/go/pkg/config"
)

func main() {
	fmt.Println("=== TinyTroupe Go Agent Creation Examples ===")
	fmt.Println("")

	cfg := config.DefaultConfig()

	// Example 1: Creating an agent programmatically
	fmt.Println("1. Creating agent programmatically:")
	alice := agent.NewTinyPerson("Alice", cfg)
	alice.Define("age", 25)
	alice.Define("nationality", "American")
	alice.Define("occupation", "Software Engineer")
	alice.Define("interests", []string{"programming", "AI", "music"})

	fmt.Printf("   Created %s, age %d, from %s\n",
		alice.Name, alice.Persona.Age, alice.Persona.Nationality)
	fmt.Printf("   Interests: %v\n\n", alice.Persona.Interests)

	// Example 2: Loading an agent from JSON file
	fmt.Println("2. Loading agent from JSON file:")
	lisa, err := loadAgentFromJSON("examples/agents/lisa.json", cfg)
	if err != nil {
		log.Printf("Failed to load Lisa: %v", err)
	} else {
		fmt.Printf("   Loaded %s, age %d, %s living in %s\n",
			lisa.Name, lisa.Persona.Age, lisa.Persona.Nationality, lisa.Persona.Residence)

		if occupation, ok := lisa.Persona.Occupation.(map[string]interface{}); ok {
			fmt.Printf("   Occupation: %s at %s\n",
				occupation["title"], occupation["organization"])
		}
		fmt.Printf("   Goals: %v\n\n", lisa.Persona.Goals)
	}

	// Example 3: Loading another agent from JSON
	fmt.Println("3. Loading another agent from JSON:")
	oscar, err := loadAgentFromJSON("examples/agents/oscar.json", cfg)
	if err != nil {
		log.Printf("Failed to load Oscar: %v", err)
	} else {
		fmt.Printf("   Loaded %s, age %d, %s living in %s\n",
			oscar.Name, oscar.Persona.Age, oscar.Persona.Nationality, oscar.Persona.Residence)

		if occupation, ok := oscar.Persona.Occupation.(map[string]interface{}); ok {
			fmt.Printf("   Occupation: %s at %s\n",
				occupation["title"], occupation["organization"])
		}
		fmt.Printf("   Interests: %v\n\n", oscar.Persona.Interests[:3]) // Show first 3 interests
	}

	// Example 4: Modifying an agent after creation
	fmt.Println("4. Modifying agent after creation:")
	alice.Define("residence", "San Francisco")
	alice.Define("goals", []string{"become a senior engineer", "learn Go programming"})

	fmt.Printf("   Updated %s's residence to: %s\n", alice.Name, alice.Persona.Residence)
	fmt.Printf("   Updated goals: %v\n\n", alice.Persona.Goals)

	// Example 5: Creating agents with relationships
	fmt.Println("5. Setting up agent relationships:")
	if lisa != nil && oscar != nil {
		alice.MakeAgentAccessible(lisa)
		alice.MakeAgentAccessible(oscar)
		lisa.MakeAgentAccessible(alice)
		oscar.MakeAgentAccessible(alice)

		fmt.Printf("   %s can now interact with %d other agents\n",
			alice.Name, len(alice.AccessibleAgents))
		fmt.Printf("   %s can now interact with %d other agents\n",
			lisa.Name, len(lisa.AccessibleAgents))
		fmt.Printf("   %s can now interact with %d other agents\n",
			oscar.Name, len(oscar.AccessibleAgents))
	}

	fmt.Println("\n=== Agent Creation Examples Complete ===")
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
