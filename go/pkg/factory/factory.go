// Package factory provides agent creation patterns and templates.
// This module handles the creation and configuration of TinyPerson agents.
package factory

import (
	"encoding/json"
	"errors"
)

// AgentFactory creates and configures TinyPerson agents
type AgentFactory interface {
	// CreateAgent creates a new agent from a template
	CreateAgent(template AgentTemplate) (Agent, error)

	// CreateAgentFromJSON creates an agent from JSON configuration
	CreateAgentFromJSON(data []byte) (Agent, error)

	// ValidateTemplate validates an agent template
	ValidateTemplate(template AgentTemplate) error

	// ListTemplates returns available agent templates
	ListTemplates() []string

	// SaveTemplate saves an agent template for reuse
	SaveTemplate(name string, template AgentTemplate) error
}

// Agent represents a minimal interface for created agents
// This should align with the agent package's TinyPerson interface
type Agent interface {
	GetName() string
	Define(key string, value interface{})
	GetDefinition(key string) (interface{}, bool)
}

// AgentTemplate defines the structure for creating agents
type AgentTemplate struct {
	Name        string                 `json:"name"`
	Description string                 `json:"description"`
	Persona     map[string]interface{} `json:"persona"`
	Background  string                 `json:"background"`
	Goals       []string               `json:"goals"`
	Interests   []string               `json:"interests"`
	Skills      []string               `json:"skills"`
	Traits      []string               `json:"traits"`
}

// PersonaBuilder helps build agent personas programmatically
type PersonaBuilder struct {
	template AgentTemplate
}

// NewPersonaBuilder creates a new persona builder
func NewPersonaBuilder(name string) *PersonaBuilder {
	return &PersonaBuilder{
		template: AgentTemplate{
			Name:    name,
			Persona: make(map[string]interface{}),
		},
	}
}

// SetDescription sets the agent description
func (pb *PersonaBuilder) SetDescription(description string) *PersonaBuilder {
	pb.template.Description = description
	return pb
}

// SetBackground sets the agent background
func (pb *PersonaBuilder) SetBackground(background string) *PersonaBuilder {
	pb.template.Background = background
	return pb
}

// AddGoal adds a goal to the agent
func (pb *PersonaBuilder) AddGoal(goal string) *PersonaBuilder {
	pb.template.Goals = append(pb.template.Goals, goal)
	return pb
}

// AddGoals adds multiple goals to the agent
func (pb *PersonaBuilder) AddGoals(goals ...string) *PersonaBuilder {
	pb.template.Goals = append(pb.template.Goals, goals...)
	return pb
}

// AddInterest adds an interest to the agent
func (pb *PersonaBuilder) AddInterest(interest string) *PersonaBuilder {
	pb.template.Interests = append(pb.template.Interests, interest)
	return pb
}

// AddInterests adds multiple interests to the agent
func (pb *PersonaBuilder) AddInterests(interests ...string) *PersonaBuilder {
	pb.template.Interests = append(pb.template.Interests, interests...)
	return pb
}

// AddSkill adds a skill to the agent
func (pb *PersonaBuilder) AddSkill(skill string) *PersonaBuilder {
	pb.template.Skills = append(pb.template.Skills, skill)
	return pb
}

// AddSkills adds multiple skills to the agent
func (pb *PersonaBuilder) AddSkills(skills ...string) *PersonaBuilder {
	pb.template.Skills = append(pb.template.Skills, skills...)
	return pb
}

// AddTrait adds a personality trait to the agent
func (pb *PersonaBuilder) AddTrait(trait string) *PersonaBuilder {
	pb.template.Traits = append(pb.template.Traits, trait)
	return pb
}

// AddTraits adds multiple personality traits to the agent
func (pb *PersonaBuilder) AddTraits(traits ...string) *PersonaBuilder {
	pb.template.Traits = append(pb.template.Traits, traits...)
	return pb
}

// SetPersonaAttribute sets a custom persona attribute
func (pb *PersonaBuilder) SetPersonaAttribute(key string, value interface{}) *PersonaBuilder {
	pb.template.Persona[key] = value
	return pb
}

// Build returns the completed agent template
func (pb *PersonaBuilder) Build() AgentTemplate {
	return pb.template
}

// Common validation errors
var (
	ErrEmptyName        = errors.New("agent name cannot be empty")
	ErrInvalidPersona   = errors.New("persona contains invalid attributes")
	ErrTemplateNotFound = errors.New("agent template not found")
)

// ValidateAgentTemplate validates an agent template
func ValidateAgentTemplate(template AgentTemplate) error {
	if template.Name == "" {
		return ErrEmptyName
	}

	// Add more validation logic as needed
	return nil
}

// AgentTemplateFromJSON creates an agent template from JSON
func AgentTemplateFromJSON(data []byte) (AgentTemplate, error) {
	var template AgentTemplate
	err := json.Unmarshal(data, &template)
	if err != nil {
		return template, err
	}

	err = ValidateAgentTemplate(template)
	return template, err
}

// AgentTemplateToJSON converts an agent template to JSON
func AgentTemplateToJSON(template AgentTemplate) ([]byte, error) {
	return json.MarshalIndent(template, "", "  ")
}

// TODO: Implement concrete agent factory
// This will be implemented in future phases and will integrate with the agent package
