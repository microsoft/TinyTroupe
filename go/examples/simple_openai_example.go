package main

import (
	"bufio"
	"context"
	"fmt"
	"log"
	"os"
	"strings"

	"github.com/microsoft/TinyTroupe/go/pkg/config"
	"github.com/microsoft/TinyTroupe/go/pkg/openai"
)

// loadEnvFile loads environment variables from a .env file
func loadEnvFile(filename string) error {
	file, err := os.Open(filename)
	if err != nil {
		return err
	}
	defer file.Close()

	scanner := bufio.NewScanner(file)
	for scanner.Scan() {
		line := strings.TrimSpace(scanner.Text())
		if line == "" || strings.HasPrefix(line, "#") {
			continue
		}

		parts := strings.SplitN(line, "=", 2)
		if len(parts) != 2 {
			continue
		}

		key := strings.TrimSpace(parts[0])
		value := strings.TrimSpace(parts[1])
		
		// Remove quotes if present
		if (strings.HasPrefix(value, "\"") && strings.HasSuffix(value, "\"")) ||
			(strings.HasPrefix(value, "'") && strings.HasSuffix(value, "'")) {
			value = value[1 : len(value)-1]
		}

		os.Setenv(key, value)
	}

	return scanner.Err()
}

func main() {
	// Try to load .env file (ignore error if file doesn't exist)
	if err := loadEnvFile(".env"); err != nil {
		log.Printf("Note: Could not load .env file: %v", err)
		log.Println("Will use environment variables or defaults")
	} else {
		log.Println("Loaded configuration from .env file")
	}

	// Check for API key after loading .env
	if os.Getenv("OPENAI_API_KEY") == "" {
		log.Println("Error: OPENAI_API_KEY not found in environment or .env file")
		log.Println("Please set it as: export OPENAI_API_KEY=your_key_here")
		log.Println("Or add it to a .env file: OPENAI_API_KEY=your_key_here")
		os.Exit(1)
	}

	fmt.Println("=== Simple OpenAI API Example ===")
	fmt.Println("Generating a flying saucer email...")
	fmt.Println()

	// Create configuration
	cfg := config.DefaultConfig()
	cfg.Model = "gpt-4.1" // Use the model from the user's example
	cfg.Temperature = 1.0
	cfg.MaxTokens = 2048

	// Create OpenAI client
	client := openai.NewClient(cfg)

	// Create the system message with complex content structure
	systemMessage := openai.NewComplexMessage("system", `Write an email about a flying saucer. 
- Your email should follow standard email conventions: include a greeting, a concise and relevant body, and a clear closing.
- The topic of the email must center around a flying saucer. You may choose the context (e.g., reporting a sighting, inviting someone to a UFO event, sharing an article, etc.), but ensure the message is clear and appropriate to your chosen scenario.
- Maintain professionalism or creativity as appropriate to your context.
- Think step-by-step about the intended recipient, the purpose, the details to include about the flying saucer (such as appearance, event, time, and place), and any follow-up actions or calls to action needed before composing the full email.
- Ensure your reasoning and planning appear internally (and not as part of the email output). The final output should only be the complete, formatted email.

**Required Output Format:**  
A single, well-structured email (greeting, body, closing) as regular text. No additional explanations or sections.

**Example:**  
(Short sample, real outputs should be more detailed)

Subject: Unusual Sight in the Sky!

Hi Jamie,

I wanted to let you know that I saw something unbelievable last night—a flying saucer hovering over the park near my house! It had blinking lights and moved silently across the sky. Have you ever seen anything like that? Let me know if you hear of any other sightings.

Best,  
Sam

---

**Reminder:**  
- Compose a realistic email about a flying saucer, including an appropriate greeting, details, and a closing.  
- Use a standard email format (subject, greeting, body, closing).  
- Do your reasoning step-by-step internally before producing the email.  
- Output only the final, formatted email.`)

	messages := []openai.Message{systemMessage}

	// Set up options matching the user's example
	options := &openai.ChatCompletionOptions{
		ResponseFormat: &openai.ResponseFormat{
			Type: "text",
		},
		Tools:               []interface{}{}, // Empty tools array
		MaxCompletionTokens: &cfg.MaxTokens,
	}

	// Create context
	ctx := context.Background()

	// Make the API call
	fmt.Println("Making OpenAI API call...")
	response, err := client.ChatCompletionWithOptions(ctx, messages, options)
	if err != nil {
		log.Fatalf("OpenAI API call failed: %v", err)
	}

	// Display the result
	fmt.Println("=== Generated Email ===")
	fmt.Println()
	fmt.Println(response.Content)
	fmt.Println()
	
	// Display usage information
	fmt.Printf("=== API Usage ===\n")
	fmt.Printf("Prompt tokens: %d\n", response.Usage.PromptTokens)
	fmt.Printf("Completion tokens: %d\n", response.Usage.CompletionTokens)
	fmt.Printf("Total tokens: %d\n", response.Usage.TotalTokens)
	fmt.Println()
	fmt.Println("=== Example Complete ===")
}