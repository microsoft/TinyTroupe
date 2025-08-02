package main

import (
	"context"
	"log"
	"os"
	"time"

	"github.com/atsentia/tinytroupe-go/pkg/agent"
	"github.com/atsentia/tinytroupe-go/pkg/config"
	"github.com/atsentia/tinytroupe-go/pkg/environment"
)

func main() {
	// Check for API key
	if os.Getenv("OPENAI_API_KEY") == "" {
		log.Println("Warning: OPENAI_API_KEY not set. This example may not work properly.")
		log.Println("Please set your OpenAI API key as an environment variable.")
		return
	}

	// Create configuration
	cfg := config.DefaultConfig()

	// Create agents
	lisa := agent.NewTinyPerson("Lisa", cfg)
	lisa.Define("age", 28)
	lisa.Define("nationality", "Canadian")
	lisa.Define("residence", "USA")
	lisa.Define("occupation", map[string]interface{}{
		"title":        "Data Scientist",
		"organization": "Microsoft",
		"description":  "Works on M365 Search team, analyzing user behavior and building ML models.",
	})
	lisa.Define("interests", []string{
		"Artificial intelligence and machine learning",
		"Natural language processing",
		"Cooking and trying new recipes",
		"Playing the piano",
	})

	oscar := agent.NewTinyPerson("Oscar", cfg)
	oscar.Define("age", 30)
	oscar.Define("nationality", "German")
	oscar.Define("residence", "Germany")
	oscar.Define("occupation", map[string]interface{}{
		"title":        "Architect",
		"organization": "Awesome Inc.",
		"description":  "Focuses on designing standard elements for new apartment buildings.",
	})
	oscar.Define("interests", []string{
		"Modernist architecture",
		"Sustainable design",
		"Travel to exotic places",
		"Playing guitar",
		"Science fiction books",
	})

	// Create world and add agents
	world := environment.NewTinyWorld("Chat Room", cfg, lisa, oscar)
	world.MakeEveryoneAccessible()

	log.Println("=== TinyTroupe Go Demo ===")
	log.Printf("Created world '%s' with agents: %s, %s", world.GetName(), lisa.Name, oscar.Name)

	// Create context with timeout
	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Minute)
	defer cancel()

	// Start conversation
	log.Println("\n--- Starting Conversation ---")

	// Lisa initiates conversation
	_, err := lisa.ListenAndAct(ctx, "Talk to Oscar to know more about him", nil)
	if err != nil {
		log.Printf("Error with Lisa's action: %v", err)
		return
	}

	// Run simulation for a few steps to let them interact
	log.Println("\n--- Running Simulation ---")
	timeDelta := 1 * time.Minute
	err = world.Run(ctx, 3, &timeDelta)
	if err != nil {
		log.Printf("Error running simulation: %v", err)
		return
	}

	log.Println("\n--- Simulation Complete ---")
	log.Println("Check the logs above to see the conversation between Lisa and Oscar!")

	// Example of broadcasting a message
	log.Println("\n--- Broadcasting Message ---")
	err = world.Broadcast("This is the end of our demo session. Thank you for participating!", nil)
	if err != nil {
		log.Printf("Error broadcasting: %v", err)
		return
	}

	// Let agents respond to the broadcast
	err = world.Run(ctx, 1, &timeDelta)
	if err != nil {
		log.Printf("Error in final step: %v", err)
		return
	}

	log.Println("\n=== Demo Complete ===")
}
