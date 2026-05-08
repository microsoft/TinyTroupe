package main

import (
	"encoding/json"
	"fmt"
	"os"

	"github.com/microsoft/TinyTroupe/go/pkg/agent"
	"github.com/microsoft/TinyTroupe/go/pkg/config"
	"github.com/microsoft/TinyTroupe/go/pkg/validation"
)

func main() {
	fmt.Println("=== TinyTroupe Go Agent Validation Example ===")
	fmt.Println("")

	cfg := config.DefaultConfig()

	// Example 1: Create and validate a programmatically defined agent
	fmt.Println("1. Creating and validating a programmatic agent:")
	alice := agent.NewTinyPerson("Alice", cfg)
	alice.Define("age", 25)
	alice.Define("nationality", "American")
	alice.Define("occupation", "Software Engineer")
	alice.Define("residence", "San Francisco")
	alice.Define("interests", []string{"programming", "AI", "music"})
	alice.Define("goals", []string{"become a senior engineer", "learn Go programming"})

	// Validate Alice's persona
	if err := validateAgent(alice); err != nil {
		fmt.Printf("   ❌ Validation failed for %s: %v\n", alice.Name, err)
	} else {
		fmt.Printf("   ✅ %s passed all validation checks\n", alice.Name)
	}
	fmt.Println("")

	// Example 2: Load and validate agents from JSON files
	fmt.Println("2. Loading and validating agents from JSON files:")

	agentFiles := []string{
		"examples/agents/lisa.json",
		"examples/agents/oscar.json",
		"examples/agents/Friedrich_Wolf.agent.json",
		"examples/agents/Lila.agent.json",
		"examples/agents/Marcos.agent.json",
		"examples/agents/Sophie_Lefevre.agent.json",
	}

	validAgents := 0
	totalAgents := len(agentFiles)

	for _, filename := range agentFiles {
		agent, err := loadAgentFromJSON(filename, cfg)
		if err != nil {
			fmt.Printf("   ❌ Failed to load %s: %v\n", filename, err)
			continue
		}

		if err := validateAgent(agent); err != nil {
			fmt.Printf("   ❌ Validation failed for %s: %v\n", agent.Name, err)
		} else {
			fmt.Printf("   ✅ %s passed validation (%s)\n", agent.Name, getOccupationTitle(agent))
			validAgents++
		}
	}

	fmt.Printf("\n   Summary: %d/%d agents passed validation\n", validAgents, totalAgents)
	fmt.Println("")

	// Example 3: Test validation with intentionally invalid data
	fmt.Println("3. Testing validation with invalid data:")

	invalidAgent := agent.NewTinyPerson("Invalid Bob", cfg)
	invalidAgent.Define("age", -5)         // Invalid age
	invalidAgent.Define("nationality", "") // Empty nationality
	// Missing required fields like occupation

	if err := validateAgent(invalidAgent); err != nil {
		fmt.Printf("   ✅ Expected validation failure for %s: %v\n", invalidAgent.Name, err)
	} else {
		fmt.Printf("   ❌ Unexpected: %s passed validation when it should have failed\n", invalidAgent.Name)
	}
	fmt.Println("")

	// Example 4: Validate specific persona fields
	fmt.Println("4. Individual field validation examples:")

	// Test various field validations
	testCases := []struct {
		field string
		value interface{}
		rule  string
	}{
		{"age", 25, "valid age"},
		{"age", -5, "invalid negative age"},
		{"name", "John Doe", "valid name"},
		{"name", "", "invalid empty name"},
		{"email", "test@example.com", "valid email format"},
		{"email", "invalid-email", "invalid email format"},
	}

	for _, tc := range testCases {
		var err error
		switch tc.field {
		case "age":
			if age, ok := tc.value.(int); ok && age > 0 && age < 150 {
				err = nil
			} else {
				err = fmt.Errorf("age must be between 1 and 149")
			}
		case "name":
			err = validation.RequiredString.Validate(tc.value)
		case "email":
			if str, ok := tc.value.(string); ok {
				err = validation.RequiredEmail.Validate(str)
			}
		}

		if err != nil {
			fmt.Printf("   ❌ %s (%v): %v\n", tc.rule, tc.value, err)
		} else {
			fmt.Printf("   ✅ %s (%v): passed\n", tc.rule, tc.value)
		}
	}

	fmt.Println("")
	fmt.Println("=== Agent Validation Example Complete ===")
}

// validateAgent performs comprehensive validation on a TinyPerson agent
func validateAgent(person *agent.TinyPerson) error {
	// Validate basic persona fields
	if err := validation.RequiredString.Validate(person.Name); err != nil {
		return fmt.Errorf("name validation failed: %w", err)
	}

	if person.Persona == nil {
		return fmt.Errorf("persona is required")
	}

	// Validate age
	if person.Persona.Age <= 0 || person.Persona.Age > 150 {
		return fmt.Errorf("age must be between 1 and 150, got %d", person.Persona.Age)
	}

	// Validate nationality
	if err := validation.RequiredString.Validate(person.Persona.Nationality); err != nil {
		return fmt.Errorf("nationality validation failed: %w", err)
	}

	// Validate residence if present
	if person.Persona.Residence != "" {
		if err := validation.RequiredString.Validate(person.Persona.Residence); err != nil {
			return fmt.Errorf("residence validation failed: %w", err)
		}
	}

	// Validate occupation structure
	if person.Persona.Occupation != nil {
		if occupation, ok := person.Persona.Occupation.(map[string]interface{}); ok {
			if title, exists := occupation["title"]; exists {
				if err := validation.RequiredString.Validate(title); err != nil {
					return fmt.Errorf("occupation title validation failed: %w", err)
				}
			}
		}
	}

	// Validate interests if present
	if len(person.Persona.Interests) > 20 {
		return fmt.Errorf("too many interests (max 20), got %d", len(person.Persona.Interests))
	}

	// Validate goals if present
	if len(person.Persona.Goals) > 10 {
		return fmt.Errorf("too many goals (max 10), got %d", len(person.Persona.Goals))
	}

	return nil
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
