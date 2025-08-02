package agent

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"strings"
	"time"

	"github.com/atsentia/tinytroupe-go/pkg/config"
	"github.com/atsentia/tinytroupe-go/pkg/memory"
	"github.com/atsentia/tinytroupe-go/pkg/openai"
)

// Action represents an action that an agent can take
type Action struct {
	Type    string      `json:"type"`
	Content interface{} `json:"content"`
	Target  string      `json:"target,omitempty"`
}

// Persona defines the characteristics of an agent
type Persona struct {
	Name        string                 `json:"name"`
	Age         int                    `json:"age,omitempty"`
	Nationality string                 `json:"nationality,omitempty"`
	Residence   string                 `json:"residence,omitempty"`
	Occupation  interface{}            `json:"occupation,omitempty"` // can be string or map
	Personality map[string]interface{} `json:"personality,omitempty"`
	Interests   []string               `json:"interests,omitempty"`
	Goals       []string               `json:"goals,omitempty"`
}

// MentalState represents the current mental state of an agent
type MentalState struct {
	DateTime   *time.Time               `json:"datetime,omitempty"`
	Location   string                   `json:"location,omitempty"`
	Context    []string                 `json:"context,omitempty"`
	Goals      []string                 `json:"goals,omitempty"`
	Attention  string                   `json:"attention,omitempty"`
	Emotions   string                   `json:"emotions"`
	Accessible []map[string]interface{} `json:"accessible_agents,omitempty"`
}

// ToolRegistry interface for agent tool access
type ToolRegistry interface {
	ProcessAction(ctx context.Context, agent ToolAgentInfo, action ToolAction, toolName string) (bool, error)
	GetToolForAction(actionType string) (Tool, error)
}

// Tool interface for agent tools  
type Tool interface {
	GetName() string
	ProcessAction(ctx context.Context, agent ToolAgentInfo, action ToolAction) (bool, error)
}

// ToolAgentInfo represents agent info for tool usage
type ToolAgentInfo struct {
	Name string `json:"name"`
	ID   string `json:"id,omitempty"`
}

// ToolAction represents an action for tool processing
type ToolAction struct {
	Type    string                 `json:"type"`
	Content interface{}            `json:"content"`
	Target  string                 `json:"target,omitempty"`
	Options map[string]interface{} `json:"options,omitempty"`
}

// TinyPerson represents a simulated person
type TinyPerson struct {
	Name              string
	Persona           *Persona
	MentalState       *MentalState
	EpisodicMemory    *memory.EpisodicMemory
	SemanticMemory    *memory.SemanticMemory
	Environment       Environment // Interface to be defined
	AccessibleAgents  []*TinyPerson
	ActionsBuffer     []Action
	currentMessages   []openai.Message
	client            *openai.Client
	config            *config.Config
	episodeEventCount int
	toolRegistry      ToolRegistry
}

// Environment interface that agents can be placed in
type Environment interface {
	GetName() string
	HandleAction(source *TinyPerson, action Action) error
	GetCurrentDateTime() *time.Time
}

// NewTinyPerson creates a new TinyPerson agent
func NewTinyPerson(name string, cfg *config.Config) *TinyPerson {
	return &TinyPerson{
		Name:             name,
		Persona:          &Persona{Name: name},
		MentalState:      &MentalState{Emotions: "Feeling nothing in particular, just calm."},
		EpisodicMemory:   memory.NewEpisodicMemory(20, 20),
		SemanticMemory:   memory.NewSemanticMemory(),
		AccessibleAgents: make([]*TinyPerson, 0),
		ActionsBuffer:    make([]Action, 0),
		currentMessages:  make([]openai.Message, 0),
		client:           openai.NewClient(cfg),
		config:           cfg,
	}
}

// Define sets a persona attribute
func (tp *TinyPerson) Define(key string, value interface{}) {
	switch key {
	case "age":
		if age, ok := value.(int); ok {
			tp.Persona.Age = age
		}
	case "nationality":
		if nationality, ok := value.(string); ok {
			tp.Persona.Nationality = nationality
		}
	case "residence":
		if residence, ok := value.(string); ok {
			tp.Persona.Residence = residence
		}
	case "occupation":
		tp.Persona.Occupation = value
	case "personality":
		if personality, ok := value.(map[string]interface{}); ok {
			tp.Persona.Personality = personality
		}
	case "interests":
		if interests, ok := value.([]string); ok {
			tp.Persona.Interests = interests
		}
	case "goals":
		if goals, ok := value.([]string); ok {
			tp.Persona.Goals = goals
		}
	}
}

// generateSystemPrompt creates the system prompt for the agent
func (tp *TinyPerson) generateSystemPrompt() string {
	prompt := fmt.Sprintf(`You are %s, a simulated person in the TinyTroupe universe.

PERSONA:
%s

MENTAL STATE:
%s

You must respond with valid JSON containing an "action" field and optionally a "cognitive_state" field.

Available actions:
- TALK: Communicate with another agent (requires "target" and "content")
- THINK: Internal thought process (requires "content")
- WRITE_DOCUMENT: Create a document (requires "content" with title, content, and optionally type)
- EXPORT_DATA: Export data or insights (requires "content" with data, filename, and format)
- DONE: Finish acting for now

Example response:
{
  "action": {
    "type": "TALK",
    "content": "Hello, how are you?",
    "target": "AgentName"
  },
  "cognitive_state": {
    "emotions": "feeling curious",
    "goals": ["learn about other agents"],
    "context": ["in conversation"]
  }
}`, tp.Name, tp.personaToString(), tp.mentalStateToString())

	return prompt
}

// personaToString converts persona to string representation
func (tp *TinyPerson) personaToString() string {
	var parts []string

	if tp.Persona.Age > 0 {
		parts = append(parts, fmt.Sprintf("Age: %d", tp.Persona.Age))
	}
	if tp.Persona.Nationality != "" {
		parts = append(parts, fmt.Sprintf("Nationality: %s", tp.Persona.Nationality))
	}
	if tp.Persona.Residence != "" {
		parts = append(parts, fmt.Sprintf("Residence: %s", tp.Persona.Residence))
	}
	if tp.Persona.Occupation != nil {
		parts = append(parts, fmt.Sprintf("Occupation: %v", tp.Persona.Occupation))
	}
	if len(tp.Persona.Interests) > 0 {
		parts = append(parts, fmt.Sprintf("Interests: %s", strings.Join(tp.Persona.Interests, ", ")))
	}
	if len(tp.Persona.Goals) > 0 {
		parts = append(parts, fmt.Sprintf("Goals: %s", strings.Join(tp.Persona.Goals, ", ")))
	}

	return strings.Join(parts, "\n")
}

// mentalStateToString converts mental state to string representation
func (tp *TinyPerson) mentalStateToString() string {
	var parts []string

	if tp.MentalState.Location != "" {
		parts = append(parts, fmt.Sprintf("Location: %s", tp.MentalState.Location))
	}
	if len(tp.MentalState.Context) > 0 {
		parts = append(parts, fmt.Sprintf("Context: %s", strings.Join(tp.MentalState.Context, ", ")))
	}
	if len(tp.MentalState.Goals) > 0 {
		parts = append(parts, fmt.Sprintf("Current Goals: %s", strings.Join(tp.MentalState.Goals, ", ")))
	}
	if tp.MentalState.Emotions != "" {
		parts = append(parts, fmt.Sprintf("Emotions: %s", tp.MentalState.Emotions))
	}

	return strings.Join(parts, "\n")
}

// resetPrompt rebuilds the conversation context
func (tp *TinyPerson) resetPrompt() {
	systemPrompt := tp.generateSystemPrompt()

	tp.currentMessages = []openai.Message{
		{Role: "system", Content: systemPrompt},
		{Role: "system", Content: "The next messages are your recent episodic memories to help contextualize your actions."},
	}

	// Add recent memories
	recentMemories := tp.EpisodicMemory.RetrieveRecent()
	for _, memory := range recentMemories {
		content := ""
		if memory.Type == "stimulus" {
			content = fmt.Sprintf("STIMULUS: %v", memory.Content)
		} else if memory.Type == "action" {
			content = fmt.Sprintf("ACTION: %v", memory.Content)
		}

		if content != "" {
			tp.currentMessages = append(tp.currentMessages, openai.Message{
				Role:    memory.Role,
				Content: content,
			})
		}
	}
}

// Listen processes incoming speech/stimuli
func (tp *TinyPerson) Listen(speech string, source *TinyPerson) error {
	stimulus := map[string]interface{}{
		"type":    "CONVERSATION",
		"content": speech,
		"source":  "",
	}

	if source != nil {
		stimulus["source"] = source.Name
	}

	content := map[string]interface{}{
		"stimuli": []interface{}{stimulus},
	}

	memoryItem := memory.MemoryItem{
		Role:                "user",
		Content:             content,
		Type:                "stimulus",
		SimulationTimestamp: time.Now(),
	}

	tp.EpisodicMemory.Store(memoryItem)
	tp.episodeEventCount++

	log.Printf("[%s] Listening to: %s", tp.Name, speech)
	return nil
}

// Act generates and executes actions
func (tp *TinyPerson) Act(ctx context.Context) ([]Action, error) {
	tp.resetPrompt()

	// Generate action using LLM
	response, err := tp.client.ChatCompletion(ctx, tp.currentMessages)
	if err != nil {
		return nil, fmt.Errorf("failed to generate action: %w", err)
	}

	// Parse JSON response
	var actionResponse struct {
		Action         Action                 `json:"action"`
		CognitiveState map[string]interface{} `json:"cognitive_state,omitempty"`
	}

	if err := json.Unmarshal([]byte(response.Content), &actionResponse); err != nil {
		return nil, fmt.Errorf("failed to parse action response: %w", err)
	}

	action := actionResponse.Action

	// Store action in memory
	memoryContent := map[string]interface{}{
		"action": action,
	}
	if actionResponse.CognitiveState != nil {
		memoryContent["cognitive_state"] = actionResponse.CognitiveState
	}

	memoryItem := memory.MemoryItem{
		Role:                "assistant",
		Content:             memoryContent,
		Type:                "action",
		SimulationTimestamp: time.Now(),
	}

	tp.EpisodicMemory.Store(memoryItem)
	tp.episodeEventCount++

	// Update cognitive state if provided
	if actionResponse.CognitiveState != nil {
		tp.updateCognitiveState(actionResponse.CognitiveState)
	}

	// Try to process action with tools first
	toolProcessed, toolErr := tp.processToolAction(ctx, action)
	if toolErr != nil {
		log.Printf("[%s] Tool processing error: %v", tp.Name, toolErr)
	}

	// Add to actions buffer
	tp.ActionsBuffer = append(tp.ActionsBuffer, action)

	// Check if episode is too long
	if tp.episodeEventCount >= tp.config.MaxEpisodeLength {
		tp.consolidateEpisode()
	}

	if toolProcessed {
		log.Printf("[%s] Action: %s - %v (processed by tool)", tp.Name, action.Type, action.Content)
	} else {
		log.Printf("[%s] Action: %s - %v", tp.Name, action.Type, action.Content)
	}
	return []Action{action}, nil
}

// ListenAndAct combines listening and acting
func (tp *TinyPerson) ListenAndAct(ctx context.Context, speech string, source *TinyPerson) ([]Action, error) {
	if err := tp.Listen(speech, source); err != nil {
		return nil, err
	}
	return tp.Act(ctx)
}

// PopLatestActions returns and clears the actions buffer
func (tp *TinyPerson) PopLatestActions() []Action {
	actions := tp.ActionsBuffer
	tp.ActionsBuffer = make([]Action, 0)
	return actions
}

// updateCognitiveState updates the agent's mental state
func (tp *TinyPerson) updateCognitiveState(state map[string]interface{}) {
	if emotions, ok := state["emotions"].(string); ok {
		tp.MentalState.Emotions = emotions
	}
	if goals, ok := state["goals"].([]interface{}); ok {
		tp.MentalState.Goals = make([]string, len(goals))
		for i, goal := range goals {
			if goalStr, ok := goal.(string); ok {
				tp.MentalState.Goals[i] = goalStr
			}
		}
	}
	if context, ok := state["context"].([]interface{}); ok {
		tp.MentalState.Context = make([]string, len(context))
		for i, ctx := range context {
			if ctxStr, ok := ctx.(string); ok {
				tp.MentalState.Context[i] = ctxStr
			}
		}
	}
}

// consolidateEpisode commits current episode to long-term memory
func (tp *TinyPerson) consolidateEpisode() {
	if tp.episodeEventCount >= tp.config.MinEpisodeLength {
		log.Printf("[%s] Consolidating episode with %d events", tp.Name, tp.episodeEventCount)

		// TODO: Implement semantic memory consolidation using LLM
		episode := tp.EpisodicMemory.GetCurrentEpisode()
		if len(episode) > 0 {
			// For now, just create a simple summary
			summary := fmt.Sprintf("Episode with %d events involving %s", len(episode), tp.Name)
			tp.SemanticMemory.Store(summary)
		}

		tp.EpisodicMemory.CommitEpisode()
		tp.episodeEventCount = 0
	}
}

// MakeAgentAccessible adds another agent to the accessible list
func (tp *TinyPerson) MakeAgentAccessible(agent *TinyPerson) {
	// Check if already accessible
	for _, existing := range tp.AccessibleAgents {
		if existing.Name == agent.Name {
			return
		}
	}

	tp.AccessibleAgents = append(tp.AccessibleAgents, agent)

	// Update mental state
	tp.MentalState.Accessible = append(tp.MentalState.Accessible, map[string]interface{}{
		"name":                 agent.Name,
		"relation_description": "An agent I can currently interact with.",
	})
}

// SetEnvironment sets the environment for this agent
func (tp *TinyPerson) SetEnvironment(env Environment) {
	tp.Environment = env
}

// SetToolRegistry sets the tool registry for this agent
func (tp *TinyPerson) SetToolRegistry(registry ToolRegistry) {
	tp.toolRegistry = registry
}

// processToolAction attempts to process an action with available tools
func (tp *TinyPerson) processToolAction(ctx context.Context, action Action) (bool, error) {
	if tp.toolRegistry == nil {
		return false, nil // No tools available
	}

	// Convert Action to ToolAction
	toolAction := ToolAction{
		Type:    action.Type,
		Content: action.Content,
		Target:  action.Target,
		Options: make(map[string]interface{}),
	}

	// Create agent info
	agentInfo := ToolAgentInfo{
		Name: tp.Name,
		ID:   tp.Name, // Using name as ID for now
	}

	// Try to find appropriate tool for this action
	tool, err := tp.toolRegistry.GetToolForAction(action.Type)
	if err != nil {
		return false, nil // No tool found for this action type
	}

	// Process action with the tool
	success, err := tool.ProcessAction(ctx, agentInfo, toolAction)
	if err != nil {
		log.Printf("[%s] Tool processing failed: %v", tp.Name, err)
		return false, err
	}

	if success {
		log.Printf("[%s] Successfully processed %s action with tool %s", tp.Name, action.Type, tool.GetName())
	}

	return success, nil
}
