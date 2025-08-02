# TinyTroupe Go Tutorial

Welcome to TinyTroupe Go! This tutorial will guide you through the essential concepts and provide hands-on examples to get you started with AI-powered persona simulation.

## Table of Contents

1. [What is TinyTroupe?](#what-is-tinytroupe)
2. [Prerequisites](#prerequisites)
3. [Quick Setup](#quick-setup)
4. [Core Concepts](#core-concepts)
5. [Your First Agent](#your-first-agent)
6. [Agent Interactions](#agent-interactions)
7. [Working with Environments](#working-with-environments)
8. [Advanced Features](#advanced-features)
9. [Real-World Examples](#real-world-examples)
10. [Best Practices](#best-practices)
11. [Troubleshooting](#troubleshooting)

## What is TinyTroupe?

TinyTroupe is a multi-agent persona simulation toolkit that uses Large Language Models (LLMs) to create realistic AI agents with distinct personalities, memories, and behaviors. Think of it as creating digital personas that can:

- **Simulate realistic conversations** between different personality types
- **Test products and ideas** with diverse user perspectives
- **Generate synthetic data** for training and research
- **Brainstorm solutions** from multiple viewpoints
- **Create market research scenarios** without real participants

### Why Use the Go Version?

- **Better Performance**: Faster execution and lower memory usage
- **Type Safety**: Compile-time error detection and robust APIs
- **Concurrency**: Built-in support for parallel agent simulation
- **Easy Deployment**: Single binary with no runtime dependencies
- **Production Ready**: Suitable for high-scale simulations

## Prerequisites

- **Go 1.20+** - [Install Go](https://golang.org/doc/install)
- **OpenAI API Key** - [Get one here](https://platform.openai.com/api-keys)
- **Basic Go knowledge** - Understanding of structs, interfaces, and goroutines helps

## Quick Setup

### 1. Get the Code

```bash
git clone https://github.com/microsoft/TinyTroupe
cd TinyTroupe/go
```

### 2. Install Dependencies

```bash
make deps
```

### 3. Set Your API Key

```bash
export OPENAI_API_KEY=your_openai_api_key_here
```

### 4. Test the Installation

```bash
# Run tests to verify everything works
make test

# Try a simple example
make examples
```

### 5. Run Your First Demo

```bash
make demo
```

If everything is working, you should see agents having a conversation!

## Core Concepts

### Agents (TinyPerson)

An **agent** is a simulated person with:
- **Persona**: Age, occupation, personality traits, interests
- **Memory**: Remembers conversations and experiences
- **Behavior**: Acts according to their personality
- **Goals**: Has objectives that drive their actions

### Environments (TinyWorld)

An **environment** is where agents interact:
- **Shared Space**: All agents can communicate
- **State Management**: Tracks conversation history
- **Orchestration**: Manages turn-taking and simulation flow

### Memory System

Agents have sophisticated memory:
- **Episodic Memory**: Remembers specific events and conversations
- **Consolidation**: Summarizes long conversations into key points
- **Retrieval**: Recalls relevant memories during interactions

### Tools

Agents can use tools to:
- **Create documents** (reports, proposals, etc.)
- **Extract data** from conversations
- **Perform calculations** or analyses
- **Interact with external systems**

## Your First Agent

Let's create a simple agent step by step.

### Example 1: Basic Agent Creation

```go
package main

import (
    "fmt"
    "github.com/microsoft/TinyTroupe/go/pkg/agent"
    "github.com/microsoft/TinyTroupe/go/pkg/config"
)

func main() {
    // Create configuration
    cfg := config.DefaultConfig()
    
    // Create an agent
    alice := agent.NewTinyPerson("Alice", cfg)
    
    // Define personality traits
    alice.Define("age", 28)
    alice.Define("occupation", "Product Manager")
    alice.Define("nationality", "American")
    alice.Define("personality", map[string]interface{}{
        "openness": "high",
        "extraversion": "medium",
        "analytical": "high",
    })
    alice.Define("interests", []string{"technology", "design", "coffee"})
    alice.Define("goals", []string{
        "launch successful products",
        "understand user needs",
        "work with great teams",
    })
    
    fmt.Printf("Created agent: %s\n", alice.Name)
    fmt.Printf("Age: %d\n", alice.Persona.Age)
    fmt.Printf("Occupation: %s\n", alice.Persona.Occupation)
    fmt.Printf("Interests: %v\n", alice.Persona.Interests)
}
```

### Example 2: Loading from JSON

Instead of defining everything in code, you can load agent configurations from JSON files:

**alice.json:**
```json
{
  "type": "TinyPerson",
  "persona": {
    "name": "Alice Johnson",
    "age": 28,
    "nationality": "American",
    "residence": "San Francisco",
    "occupation": {
      "title": "Product Manager",
      "organization": "TechCorp",
      "department": "Consumer Products"
    },
    "personality": {
      "openness": "high",
      "extraversion": "medium",
      "conscientiousness": "high",
      "analytical_thinking": "very high"
    },
    "interests": [
      "user experience design",
      "data analysis",
      "coffee culture",
      "startup ecosystems"
    ],
    "goals": [
      "launch products that solve real problems",
      "understand customer needs deeply",
      "build data-driven product strategies"
    ]
  }
}
```

**Loading code:**
```go
func loadAgent() {
    cfg := config.DefaultConfig()
    
    alice, err := loadAgentFromJSON("alice.json", cfg)
    if err != nil {
        log.Fatal(err)
    }
    
    fmt.Printf("Loaded %s: %s at %s\n", 
        alice.Name, 
        alice.Persona.Occupation.(map[string]interface{})["title"],
        alice.Persona.Occupation.(map[string]interface{})["organization"])
}
```

## Agent Interactions

### Single Agent Actions

```go
func singleAgentExample() {
    cfg := config.DefaultConfig()
    alice := agent.NewTinyPerson("Alice", cfg)
    
    // Set up alice's personality...
    
    ctx := context.Background()
    
    // Have Alice respond to a scenario
    err := alice.ListenAndAct(ctx, 
        "You're in a product planning meeting. The team is discussing whether to add a new feature that would delay the launch by 2 months. What's your perspective?", 
        nil)
    
    if err != nil {
        log.Fatal(err)
    }
}
```

### Two-Agent Conversation

```go
func twoAgentConversation() {
    cfg := config.DefaultConfig()
    
    // Create two agents with different perspectives
    alice := agent.NewTinyPerson("Alice", cfg)
    alice.Define("occupation", "Product Manager")
    alice.Define("personality", map[string]interface{}{
        "risk_tolerance": "low",
        "decision_style": "data-driven",
    })
    
    bob := agent.NewTinyPerson("Bob", cfg)
    bob.Define("occupation", "Software Engineer") 
    bob.Define("personality", map[string]interface{}{
        "risk_tolerance": "high",
        "decision_style": "innovative",
    })
    
    // Make them aware of each other
    alice.MakeAgentAccessible(bob)
    bob.MakeAgentAccessible(alice)
    
    ctx := context.Background()
    
    // Start conversation
    alice.ListenAndAct(ctx, 
        "Hi Bob! I've been thinking about the new API design. What are your thoughts on prioritizing backward compatibility vs. clean architecture?", 
        nil)
    
    // Bob will automatically respond based on Alice's message
}
```

## Working with Environments

Environments make it easy to manage multi-agent interactions:

### Basic Environment Setup

```go
func environmentExample() {
    cfg := config.DefaultConfig()
    
    // Create agents
    alice := createProductManager(cfg)
    bob := createEngineer(cfg) 
    charlie := createDesigner(cfg)
    
    // Create environment
    world := environment.NewTinyWorld("Planning Meeting", cfg, alice, bob, charlie)
    world.MakeEveryoneAccessible()
    
    // Set the scene
    world.Broadcast(`
        You're in a product planning meeting for a new mobile app feature. 
        The goal is to decide on the core functionality and user experience.
        Please discuss your perspectives and try to reach consensus.
    `, nil)
    
    // Run simulation for several steps
    ctx := context.Background()
    steps := 5
    if err := world.Run(ctx, steps, nil); err != nil {
        log.Fatal(err)
    }
    
    // The agents will have a natural conversation!
}
```

### Environment with Custom Setup

```go
func marketResearchEnvironment() {
    cfg := config.DefaultConfig()
    
    // Create diverse user personas
    techEnthusiast := createTechEnthusiast(cfg)
    casualUser := createCasualUser(cfg)
    businessUser := createBusinessUser(cfg)
    
    world := environment.NewTinyWorld("Focus Group", cfg, 
        techEnthusiast, casualUser, businessUser)
    world.MakeEveryoneAccessible()
    
    // Present a product concept
    world.Broadcast(`
        We're showing you a new productivity app concept. 
        It combines calendar management, task tracking, and team collaboration.
        Please share your honest thoughts about:
        1. Would you use this app?
        2. What features excite you most?
        3. What concerns do you have?
        4. How much would you pay for it?
    `, nil)
    
    ctx := context.Background()
    world.Run(ctx, 6, nil)
}
```

## Advanced Features

### Memory and Context

Agents remember previous conversations:

```go
func memoryExample() {
    cfg := config.DefaultConfig()
    alice := agent.NewTinyPerson("Alice", cfg)
    
    ctx := context.Background()
    
    // First conversation
    alice.ListenAndAct(ctx, "Hi Alice, I'm working on a new project about sustainable energy.", nil)
    alice.ListenAndAct(ctx, "It involves solar panel optimization.", nil)
    
    // Later conversation - Alice will remember the context
    alice.ListenAndAct(ctx, "How do you think we should approach the efficiency problem we discussed?", nil)
    
    // Alice's response will reference the earlier conversation about solar panels
}
```

### Tool Usage

Agents can use tools to create documents, extract data, and more:

```go
func toolExample() {
    cfg := config.DefaultConfig()
    
    // Create an agent with tool access
    consultant := agent.NewTinyPerson("Elena Rodriguez", cfg)
    consultant.Define("occupation", "Business Consultant")
    consultant.Define("expertise", []string{"market research", "strategic planning"})
    
    // Register tools (document creation, data extraction, etc.)
    toolRegistry := setupTools()
    consultant.SetToolRegistry(toolRegistry)
    
    ctx := context.Background()
    
    // Ask the agent to create a document
    consultant.ListenAndAct(ctx, `
        Please create a market research report about digital transformation trends 
        for mid-size companies in Europe. Include key findings, recommendations, 
        and market opportunities.
    `, nil)
    
    // The agent will use document creation tools to generate a professional report
}
```

### Synthetic Data Generation

Generate realistic data for training and testing:

```go
func syntheticDataExample() {
    cfg := config.DefaultConfig()
    
    // Create diverse user personas
    users := []*agent.TinyPerson{
        createMillennialUser(cfg),
        createGenXUser(cfg), 
        createBabyBoomerUser(cfg),
    }
    
    world := environment.NewTinyWorld("User Research", cfg, users...)
    world.MakeEveryoneAccessible()
    
    // Generate user feedback data
    products := []string{
        "fitness tracking app",
        "meal planning service", 
        "online learning platform",
    }
    
    ctx := context.Background()
    
    for _, product := range products {
        world.Broadcast(fmt.Sprintf(`
            Please provide your honest feedback about this %s:
            - What features would you want?
            - What are your main concerns?
            - How much would you pay?
            - Rate your interest from 1-10
        `, product), nil)
        
        world.Run(ctx, 3, nil)
        
        // Extract structured data from responses
        data := extractUserFeedback(world)
        saveDataset(product, data)
    }
}
```

## Real-World Examples

### 1. Product Brainstorming Session

Run this example: `make build && ./bin/product_brainstorming`

This simulates a diverse team brainstorming new product ideas, demonstrating how different personality types contribute different perspectives.

### 2. A/B Testing Simulation

Run this example: `make build && ./bin/ab_testing`

This shows how to test different product concepts with simulated user groups, gathering quantitative and qualitative feedback.

### 3. Market Research

Run this example: `make build && ./bin/synthetic_data_generation`

This generates realistic user personas and feedback for market research scenarios.

### 4. Document Creation

Run this example: `make build && ./bin/document_creation`

This demonstrates how agents can use tools to create professional business documents like reports and proposals.

## Best Practices

### 1. Agent Design

**Create Rich Personas:**
```go
// Good: Detailed, realistic persona
alice.Define("background", "Former startup founder, now at enterprise company")
alice.Define("motivations", []string{"impact", "efficiency", "team growth"})
alice.Define("communication_style", "direct but collaborative")
alice.Define("decision_factors", []string{"data", "user benefit", "team capacity"})

// Avoid: Too generic
alice.Define("occupation", "manager")
```

**Give Agents Clear Goals:**
```go
alice.Define("current_objectives", []string{
    "launch Q3 product on time",
    "improve user retention by 15%", 
    "mentor junior team members",
})
```

### 2. Environment Management

**Set Clear Context:**
```go
world.Broadcast(`
    Context: Q3 planning meeting
    Goal: Finalize product roadmap priorities
    Constraints: Limited engineering resources
    Success criteria: Clear prioritized backlog
`, nil)
```

**Manage Conversation Flow:**
```go
// For focused discussions, limit participants
world := environment.NewTinyWorld("Design Review", cfg, designer, engineer, productManager)

// For diverse perspectives, include more voices
world := environment.NewTinyWorld("User Research", cfg, 
    youngUser, seniorUser, businessUser, casualUser)
```

### 3. Memory Management

**Let Conversations Develop Naturally:**
```go
// Run enough steps for meaningful interaction
world.Run(ctx, 8, nil) // Good for complex discussions

// But don't let conversations go on forever
if steps > 15 {
    // Summarize and conclude
}
```

### 4. Error Handling

**Always Handle API Errors:**
```go
if err := agent.ListenAndAct(ctx, message, nil); err != nil {
    if strings.Contains(err.Error(), "rate limit") {
        time.Sleep(time.Minute)
        // Retry logic
    } else {
        log.Printf("Agent error: %v", err)
    }
}
```

### 5. Configuration

**Use Environment Variables for Production:**
```bash
# Set in production environment
export OPENAI_API_KEY=prod_key
export TINYTROUPE_MODEL=gpt-4o
export TINYTROUPE_MAX_TOKENS=2048
export TINYTROUPE_TEMPERATURE=0.7
```

**Customize for Your Use Case:**
```go
cfg := config.DefaultConfig()
cfg.Temperature = 0.9  // More creative responses
cfg.MaxTokens = 500    // Shorter responses
cfg.Model = "gpt-4o"   // Higher quality model
```

## Troubleshooting

### Common Issues

#### 1. API Key Problems
```
Error: API key not found
```
**Solution:**
```bash
export OPENAI_API_KEY=your_key_here
# Or check if .env file is properly configured
```

#### 2. Rate Limiting
```
Error: rate limit exceeded
```
**Solution:**
```go
cfg.MaxAttempts = 3
cfg.Timeout = 30 // Increase timeout
// Add delays between requests
```

#### 3. Agent Not Responding Naturally
**Problem:** Agent responses seem robotic or inconsistent.

**Solution:**
- Add more personality details
- Include background and motivations
- Set clearer context in environments
- Use higher temperature for more creative responses

#### 4. Memory Issues
**Problem:** Agents forget previous context.

**Solution:**
```go
// Enable memory consolidation
cfg.EnableMemoryConsolidation = true
cfg.MaxEpisodeLength = 50

// Or explicitly reference previous conversations
alice.ListenAndAct(ctx, "Continuing our discussion about the API design...", nil)
```

#### 5. Performance Issues
**Problem:** Simulations running slowly.

**Solution:**
```go
// Enable parallel processing
cfg.ParallelActions = true

// Reduce token limits
cfg.MaxTokens = 256

// Use smaller model for development
cfg.Model = "gpt-4o-mini"
```

### Getting Help

1. **Check the logs** - Enable debug logging:
   ```go
   cfg.LogLevel = "DEBUG"
   ```

2. **Review examples** - Look at working examples in `examples/`

3. **Test components** - Run individual tests:
   ```bash
   go test ./pkg/agent -v
   ```

4. **Check configuration** - Verify your setup:
   ```bash
   make check
   ```

## Next Steps

Now that you understand the basics:

1. **Explore the examples** - Run `make examples` to see all available scenarios
2. **Try your own scenarios** - Modify the examples for your use cases  
3. **Read the source** - Check `pkg/` directories for advanced features
4. **Contribute** - Help port more features from the Python version

### Advanced Topics to Explore

- **Custom Tools** - Create specialized tools for your domain
- **Complex Environments** - Multi-room simulations with different contexts
- **Behavior Steering** - Real-time modification of agent behavior
- **Performance Optimization** - Parallel processing and memory management
- **Integration** - Connect with external systems and APIs

Happy simulating! 🚀

---

*This tutorial covers the essential concepts to get you started. For the latest updates and advanced features, see the [README.md](README.md) and explore the [examples](examples/) directory.*