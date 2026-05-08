package main

import (
	"encoding/json"
	"fmt"
	"log"
	"os"

	"github.com/microsoft/TinyTroupe/go/pkg/agent"
	"github.com/microsoft/TinyTroupe/go/pkg/config"
	"github.com/microsoft/TinyTroupe/go/pkg/environment"
)

func main() {
	fmt.Println("=== TinyTroupe Go Product Brainstorming Example ===")
	fmt.Println("")

	cfg := config.DefaultConfig()

	// Load a diverse set of agents for brainstorming
	fmt.Println("Loading brainstorming team...")

	lisa, err := loadAgentFromJSON("examples/agents/lisa.json", cfg)
	if err != nil {
		log.Fatalf("Failed to load Lisa: %v", err)
	}

	oscar, err := loadAgentFromJSON("examples/agents/oscar.json", cfg)
	if err != nil {
		log.Fatalf("Failed to load Oscar: %v", err)
	}

	marcos, err := loadAgentFromJSON("examples/agents/Marcos.agent.json", cfg)
	if err != nil {
		log.Fatalf("Failed to load Marcos: %v", err)
	}

	fmt.Printf("✓ %s - %s (Data & AI perspective)\n", lisa.Name, getOccupationTitle(lisa))
	fmt.Printf("✓ %s - %s (Financial perspective)\n", oscar.Name, getOccupationTitle(oscar))
	fmt.Printf("✓ %s - %s (Engineering perspective)\n", marcos.Name, getOccupationTitle(marcos))
	fmt.Println("")

	// Create brainstorming environment
	fmt.Println("Setting up brainstorming session...")
	world := environment.NewTinyWorld("BrainstormingRoom", cfg)
	world.AddAgent(lisa)
	world.AddAgent(oscar)
	world.AddAgent(marcos)
	world.MakeEveryoneAccessible()

	fmt.Printf("✓ Created brainstorming room with %d participants\n", len(world.Agents))
	fmt.Println("")

	// Start the brainstorming session
	fmt.Println("=== Product Brainstorming Session: Next-Gen Productivity App ===")
	fmt.Println("")

	// Introduce the challenge
	fmt.Println("🎯 Challenge Introduction:")
	world.Broadcast("Welcome to our brainstorming session! Today we're designing a next-generation productivity app that uses AI to help remote teams collaborate more effectively. Let's think about innovative features that could revolutionize how people work together.", lisa)
	fmt.Println("")

	// Lisa shares her data science perspective
	fmt.Printf("💡 %s (Data Science perspective):\n", lisa.Name)
	talkAction := agent.Action{
		Type:    "TALK",
		Target:  oscar.Name,
		Content: "From my experience with search and data analytics, I think we should focus on intelligent content discovery. The app could use NLP to automatically surface relevant documents, conversations, and insights based on what the team is currently working on. Machine learning could predict what information each person needs before they even search for it.",
	}
	world.HandleAction(lisa, talkAction)
	fmt.Println("")

	// Oscar responds with financial and business insights
	fmt.Printf("💰 %s (Business & Finance perspective):\n", oscar.Name)
	talkAction = agent.Action{
		Type:    "TALK",
		Target:  marcos.Name,
		Content: "That's a great foundation, Lisa! From a business model perspective, I'd suggest we also include intelligent resource allocation features. The app could analyze team productivity patterns and budget constraints to recommend optimal team compositions for different projects. We could also add predictive analytics for project timelines and costs.",
	}
	world.HandleAction(oscar, talkAction)
	fmt.Println("")

	// Marcos adds the engineering perspective
	fmt.Printf("⚙️ %s (Engineering perspective):\n", marcos.Name)
	talkAction = agent.Action{
		Type:    "TALK",
		Target:  lisa.Name,
		Content: "Both excellent ideas! On the technical side, I'm thinking about real-time collaborative coding environments and automated code review suggestions. We could integrate version control with AI-powered conflict resolution. Also, what about intelligent meeting scheduling that considers time zones, workload, and even team members' peak productivity hours?",
	}
	world.HandleAction(marcos, talkAction)
	fmt.Println("")

	// Build on each other's ideas
	fmt.Printf("🔄 %s building on the discussion:\n", lisa.Name)
	talkAction = agent.Action{
		Type:    "TALK",
		Target:  marcos.Name,
		Content: "Marcos, your mention of productivity hours is brilliant! We could combine that with sentiment analysis of team communications to detect when someone might be overwhelmed or when a team is hitting a creative block. The app could then suggest breaks, team building activities, or even recommend bringing in additional expertise.",
	}
	world.HandleAction(lisa, talkAction)
	fmt.Println("")

	fmt.Printf("📊 %s synthesizing business value:\n", oscar.Name)
	talkAction = agent.Action{
		Type:    "TALK",
		Target:  lisa.Name,
		Content: "I love how this is shaping up! All these features could be packaged into different subscription tiers. Basic tier for small teams, Professional tier with advanced AI features, and Enterprise tier with custom integrations. We could also offer consulting services to help organizations optimize their workflows using the app's insights.",
	}
	world.HandleAction(oscar, talkAction)
	fmt.Println("")

	fmt.Printf("🚀 %s proposing implementation strategy:\n", marcos.Name)
	talkAction = agent.Action{
		Type:    "TALK",
		Target:  oscar.Name,
		Content: "For the technical roadmap, I suggest we start with a minimum viable product focusing on the intelligent content discovery and basic collaboration features. We could use microservices architecture to ensure scalability, and implement the AI features progressively. Perhaps we could even open-source some components to build a developer community around the platform.",
	}
	world.HandleAction(marcos, talkAction)
	fmt.Println("")

	// Final synthesis
	fmt.Println("=== Brainstorming Summary ===")
	fmt.Println("")
	fmt.Println("🎉 Product Concept: AI-Powered Team Productivity Platform")
	fmt.Println("")
	fmt.Println("Key Features Identified:")
	fmt.Println("• Intelligent content discovery with NLP")
	fmt.Println("• Predictive resource allocation and project analytics")
	fmt.Println("• Real-time collaborative development environments")
	fmt.Println("• AI-powered scheduling and workload optimization")
	fmt.Println("• Team sentiment analysis and wellness monitoring")
	fmt.Println("• Automated conflict resolution and code review")
	fmt.Println("")
	fmt.Println("Business Model:")
	fmt.Println("• Tiered subscription model (Basic/Professional/Enterprise)")
	fmt.Println("• Professional services and optimization consulting")
	fmt.Println("• Open-source components for community building")
	fmt.Println("")
	fmt.Println("Technical Strategy:")
	fmt.Println("• Microservices architecture for scalability")
	fmt.Println("• Progressive AI feature implementation")
	fmt.Println("• MVP focused on core collaboration and discovery")
	fmt.Println("")

	fmt.Printf("✅ Successful brainstorming session with %d team members\n", len(world.Agents))
	fmt.Println("   Each participant contributed unique domain expertise")
	fmt.Println("   Ideas were built upon collaboratively")
	fmt.Println("   Clear product vision and roadmap emerged")

	fmt.Println("")
	fmt.Println("=== Product Brainstorming Example Complete ===")
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
