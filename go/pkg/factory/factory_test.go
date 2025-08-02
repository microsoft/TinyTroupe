package factory

import (
	"testing"
)

func TestPersonaBuilder(t *testing.T) {
	builder := NewPersonaBuilder("TestAgent")
	template := builder.
		SetDescription("Test agent for unit testing").
		SetBackground("Created in a test environment").
		AddGoals("Test goal 1", "Test goal 2").
		AddInterests("Testing", "Quality Assurance").
		AddSkills("Unit Testing", "Integration Testing").
		AddTraits("Methodical", "Detail-oriented").
		SetPersonaAttribute("experience", "5 years").
		Build()

	if template.Name != "TestAgent" {
		t.Errorf("Expected name 'TestAgent', got '%s'", template.Name)
	}

	if len(template.Goals) != 2 {
		t.Errorf("Expected 2 goals, got %d", len(template.Goals))
	}

	if len(template.Interests) != 2 {
		t.Errorf("Expected 2 interests, got %d", len(template.Interests))
	}

	if len(template.Skills) != 2 {
		t.Errorf("Expected 2 skills, got %d", len(template.Skills))
	}

	if len(template.Traits) != 2 {
		t.Errorf("Expected 2 traits, got %d", len(template.Traits))
	}

	if template.Persona["experience"] != "5 years" {
		t.Errorf("Expected experience '5 years', got '%v'", template.Persona["experience"])
	}
}

func TestValidateAgentTemplate(t *testing.T) {
	// Test empty name
	template := AgentTemplate{}
	err := ValidateAgentTemplate(template)
	if err != ErrEmptyName {
		t.Errorf("Expected ErrEmptyName, got %v", err)
	}

	// Test valid template
	template.Name = "ValidAgent"
	err = ValidateAgentTemplate(template)
	if err != nil {
		t.Errorf("Expected no error for valid template, got %v", err)
	}
}

func TestAgentTemplateJSON(t *testing.T) {
	original := AgentTemplate{
		Name:        "JSONTestAgent",
		Description: "Agent for JSON testing",
		Persona:     map[string]interface{}{"key": "value"},
		Background:  "Test background",
		Goals:       []string{"goal1", "goal2"},
		Interests:   []string{"interest1"},
		Skills:      []string{"skill1"},
		Traits:      []string{"trait1"},
	}

	// Test marshal
	data, err := AgentTemplateToJSON(original)
	if err != nil {
		t.Fatalf("Failed to marshal template: %v", err)
	}

	// Test unmarshal
	parsed, err := AgentTemplateFromJSON(data)
	if err != nil {
		t.Fatalf("Failed to unmarshal template: %v", err)
	}

	// Verify data integrity
	if parsed.Name != original.Name {
		t.Errorf("Name mismatch: expected '%s', got '%s'", original.Name, parsed.Name)
	}

	if len(parsed.Goals) != len(original.Goals) {
		t.Errorf("Goals length mismatch: expected %d, got %d", len(original.Goals), len(parsed.Goals))
	}

	if parsed.Persona["key"] != original.Persona["key"] {
		t.Errorf("Persona mismatch: expected '%v', got '%v'", original.Persona["key"], parsed.Persona["key"])
	}
}

func TestAgentTemplateFromInvalidJSON(t *testing.T) {
	invalidJSON := []byte(`{"name": "test", "invalid": }`)

	_, err := AgentTemplateFromJSON(invalidJSON)
	if err == nil {
		t.Error("Expected error for invalid JSON, got none")
	}
}
