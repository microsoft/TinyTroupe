package main

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"os"
	"strings"
	"time"

	"github.com/microsoft/TinyTroupe/go/pkg/agent"
	"github.com/microsoft/TinyTroupe/go/pkg/config"
	"github.com/microsoft/TinyTroupe/go/pkg/environment"
	"github.com/microsoft/TinyTroupe/go/pkg/extraction"
)

func main() {
	fmt.Println("=== TinyTroupe Go Synthetic Data Generation Example ===")
	fmt.Println("")

	cfg := config.DefaultConfig()

	// Load agents for data generation
	fmt.Println("Loading agents for synthetic data generation...")

	lisa, err := loadAgentFromJSON("examples/agents/lisa.json", cfg)
	if err != nil {
		log.Fatalf("Failed to load Lisa: %v", err)
	}

	oscar, err := loadAgentFromJSON("examples/agents/oscar.json", cfg)
	if err != nil {
		log.Fatalf("Failed to load Oscar: %v", err)
	}

	lila, err := loadAgentFromJSON("examples/agents/Lila.agent.json", cfg)
	if err != nil {
		log.Fatalf("Failed to load Lila: %v", err)
	}

	fmt.Printf("✓ %s - %s\n", lisa.Name, getOccupationTitle(lisa))
	fmt.Printf("✓ %s - %s\n", oscar.Name, getOccupationTitle(oscar))
	fmt.Printf("✓ %s - %s\n", lila.Name, getOccupationTitle(lila))
	fmt.Println("")

	// Create environment for data generation
	fmt.Println("Setting up data generation environment...")
	world := environment.NewTinyWorld("DataGeneration", cfg)
	world.AddAgent(lisa)
	world.AddAgent(oscar)
	world.AddAgent(lila)
	world.MakeEveryoneAccessible()

	fmt.Printf("✓ Environment ready with %d agents\n", len(world.Agents))
	fmt.Println("")

	// Generate synthetic conversation data
	fmt.Println("=== Generating Synthetic Conversation Data ===")
	fmt.Println("")

	conversations := generateSyntheticConversations(world)

	// Extract and analyze the generated data
	fmt.Println("📊 Extracting insights from generated conversations...")

	extractor := extraction.NewSimulationExtractor()
	ctx := context.Background()

	// Extract conversation patterns
	request := &extraction.ExtractionRequest{
		Type:   extraction.ConversationExtraction,
		Source: conversations,
		Options: map[string]interface{}{
			"include_sentiment": true,
			"extract_topics":    true,
		},
	}

	result, err := extractor.Extract(ctx, request)
	if err != nil {
		log.Printf("Extraction failed: %v", err)
	} else {
		fmt.Printf("✓ Extracted conversation data with %d insights\n", len(result.Summary))
	}

	// Generate synthetic user feedback data
	fmt.Println("")
	fmt.Println("=== Generating Synthetic User Feedback ===")
	fmt.Println("")

	feedbackData := generateSyntheticFeedback(lisa, oscar, lila)

	// Extract patterns from feedback
	feedbackRequest := &extraction.ExtractionRequest{
		Type:   extraction.PatternsExtraction,
		Source: feedbackData,
		Options: map[string]interface{}{
			"pattern_type":       "user_satisfaction",
			"sentiment_analysis": true,
		},
	}

	feedbackResult, err := extractor.Extract(ctx, feedbackRequest)
	if err != nil {
		log.Printf("Feedback extraction failed: %v", err)
	} else {
		fmt.Printf("✓ Extracted feedback patterns: %v\n", feedbackResult.Summary)
	}

	// Generate synthetic behavioral data
	fmt.Println("")
	fmt.Println("=== Generating Synthetic Behavioral Data ===")
	fmt.Println("")

	behaviorData := generateSyntheticBehavior(lisa, oscar, lila)

	// Extract behavioral metrics
	behaviorRequest := &extraction.ExtractionRequest{
		Type:   extraction.MetricsExtraction,
		Source: behaviorData,
		Options: map[string]interface{}{
			"metric_types": []string{"engagement", "productivity", "collaboration"},
		},
	}

	behaviorResult, err := extractor.Extract(ctx, behaviorRequest)
	if err != nil {
		log.Printf("Behavior extraction failed: %v", err)
	} else {
		fmt.Printf("✓ Extracted behavioral metrics: %v\n", behaviorResult.Summary)
	}

	// Generate summary report
	fmt.Println("")
	fmt.Println("=== Synthetic Data Generation Summary ===")
	fmt.Println("")

	totalConversations := len(conversations)
	totalFeedback := len(feedbackData)
	totalBehaviorEvents := len(behaviorData)

	fmt.Printf("📈 Generated Synthetic Data:\n")
	fmt.Printf("   • %d conversation exchanges\n", totalConversations)
	fmt.Printf("   • %d user feedback entries\n", totalFeedback)
	fmt.Printf("   • %d behavioral data points\n", totalBehaviorEvents)
	fmt.Printf("   • %d unique agents involved\n", len(world.Agents))
	fmt.Println("")

	fmt.Printf("🔍 Extraction Results:\n")
	if result != nil {
		fmt.Printf("   • Conversation insights: %d patterns identified\n", len(result.Summary))
	}
	if feedbackResult != nil {
		fmt.Printf("   • Feedback patterns: Successfully extracted\n")
	}
	if behaviorResult != nil {
		fmt.Printf("   • Behavioral metrics: Successfully extracted\n")
	}
	fmt.Println("")

	fmt.Println("✅ Synthetic data generation demonstrates:")
	fmt.Println("   • Multi-agent conversation simulation")
	fmt.Println("   • Realistic user feedback generation")
	fmt.Println("   • Behavioral pattern synthesis")
	fmt.Println("   • Data extraction and analysis pipeline")
	fmt.Println("   • Scalable synthetic data creation")

	fmt.Println("")
	fmt.Println("=== Synthetic Data Generation Example Complete ===")
}

// generateSyntheticConversations creates realistic conversation data
func generateSyntheticConversations(world *environment.TinyWorld) []map[string]interface{} {
	conversations := []map[string]interface{}{}

	fmt.Println("🗣️  Generating conversation scenarios...")

	// Scenario 1: Team meeting discussion
	conversations = append(conversations, map[string]interface{}{
		"id":           "conv_1",
		"type":         "team_meeting",
		"participants": []string{"Lisa Carter", "Oscar Thompson"},
		"topic":        "Q4 Planning",
		"messages": []map[string]interface{}{
			{
				"speaker":   "Lisa Carter",
				"content":   "I've analyzed our Q3 data and identified key growth opportunities for next quarter.",
				"timestamp": time.Now().Add(-1 * time.Hour),
				"sentiment": "positive",
			},
			{
				"speaker":   "Oscar Thompson",
				"content":   "Excellent work, Lisa. What's the ROI projection for the initiatives you're proposing?",
				"timestamp": time.Now().Add(-58 * time.Minute),
				"sentiment": "positive",
			},
		},
	})

	// Scenario 2: Technical discussion
	conversations = append(conversations, map[string]interface{}{
		"id":           "conv_2",
		"type":         "technical_discussion",
		"participants": []string{"Lisa Carter", "Lila Rodriguez"},
		"topic":        "Machine Learning Pipeline",
		"messages": []map[string]interface{}{
			{
				"speaker":   "Lisa Carter",
				"content":   "We need to optimize our ML pipeline for better real-time performance.",
				"timestamp": time.Now().Add(-2 * time.Hour),
				"sentiment": "analytical",
			},
			{
				"speaker":   "Lila Rodriguez",
				"content":   "I agree. We could implement batch processing and caching mechanisms.",
				"timestamp": time.Now().Add(-115 * time.Minute),
				"sentiment": "collaborative",
			},
		},
	})

	fmt.Printf("   Generated %d conversation scenarios\n", len(conversations))
	return conversations
}

// generateSyntheticFeedback creates user feedback data
func generateSyntheticFeedback(agents ...*agent.TinyPerson) []map[string]interface{} {
	feedback := []map[string]interface{}{}

	fmt.Println("📝 Generating user feedback data...")

	for i, agent := range agents {
		// Generate positive feedback
		feedback = append(feedback, map[string]interface{}{
			"user_id":   fmt.Sprintf("user_%s", strings.ToLower(strings.Fields(agent.Name)[0])),
			"rating":    4 + i%2, // Ratings 4-5
			"comment":   fmt.Sprintf("Great experience working with %s. Very professional and knowledgeable.", agent.Name),
			"category":  "collaboration",
			"timestamp": time.Now().Add(-time.Duration(i*24) * time.Hour),
			"sentiment": "positive",
		})

		// Generate constructive feedback
		feedback = append(feedback, map[string]interface{}{
			"user_id":   fmt.Sprintf("user_%s_2", strings.ToLower(strings.Fields(agent.Name)[0])),
			"rating":    3 + i%2, // Ratings 3-4
			"comment":   "Could improve communication frequency, but overall good results.",
			"category":  "communication",
			"timestamp": time.Now().Add(-time.Duration(i*48) * time.Hour),
			"sentiment": "neutral",
		})
	}

	fmt.Printf("   Generated %d feedback entries\n", len(feedback))
	return feedback
}

// generateSyntheticBehavior creates behavioral data points
func generateSyntheticBehavior(agents ...*agent.TinyPerson) []map[string]interface{} {
	behavior := []map[string]interface{}{}

	fmt.Println("📊 Generating behavioral data...")

	for i, agent := range agents {
		// Generate interaction patterns
		behavior = append(behavior, map[string]interface{}{
			"agent_id":   agent.Name,
			"event_type": "task_completion",
			"metrics": map[string]interface{}{
				"completion_time":     45 + i*15, // minutes
				"quality_score":       0.85 + float64(i)*0.05,
				"collaboration_score": 0.8 + float64(i)*0.03,
			},
			"timestamp": time.Now().Add(-time.Duration(i*6) * time.Hour),
		})

		// Generate engagement metrics
		behavior = append(behavior, map[string]interface{}{
			"agent_id":   agent.Name,
			"event_type": "engagement",
			"metrics": map[string]interface{}{
				"messages_sent":         12 + i*3,
				"responses_received":    8 + i*2,
				"average_response_time": 5 + i*2, // minutes
			},
			"timestamp": time.Now().Add(-time.Duration(i*12) * time.Hour),
		})
	}

	fmt.Printf("   Generated %d behavioral data points\n", len(behavior))
	return behavior
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
