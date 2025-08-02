package main

import (
	"context"
	"fmt"
	"log"
	"os"
	"time"

	"github.com/atsentia/tinytroupe-go/pkg/agent"
	"github.com/atsentia/tinytroupe-go/pkg/config"
	"github.com/atsentia/tinytroupe-go/pkg/environment"
	"github.com/atsentia/tinytroupe-go/pkg/tools"
)

// ToolRegistryAdapter adapts the tools registry to the agent interface
type ToolRegistryAdapter struct {
	registry *tools.AgentToolRegistry
}

func (tra *ToolRegistryAdapter) ProcessAction(ctx context.Context, agentInfo agent.ToolAgentInfo, action agent.ToolAction, toolName string) (bool, error) {
	// Convert agent types
	toolAgentInfo := tools.AgentInfo{
		Name: agentInfo.Name,
		ID:   agentInfo.ID,
	}
	
	toolAction := tools.Action{
		Type:    action.Type,
		Content: action.Content,
		Target:  action.Target,
		Options: action.Options,
	}
	
	return tra.registry.ProcessAction(ctx, toolAgentInfo, toolAction, toolName)
}

func (tra *ToolRegistryAdapter) GetToolForAction(actionType string) (agent.Tool, error) {
	tool, err := tra.registry.GetToolForAction(actionType)
	if err != nil {
		return nil, err
	}
	
	return &ToolAdapter{tool: tool}, nil
}

// ToolAdapter adapts individual tools to the agent interface
type ToolAdapter struct {
	tool tools.AgentTool
}

func (ta *ToolAdapter) GetName() string {
	return ta.tool.GetName()
}

func (ta *ToolAdapter) ProcessAction(ctx context.Context, agentInfo agent.ToolAgentInfo, action agent.ToolAction) (bool, error) {
	// Convert types
	toolAgentInfo := tools.AgentInfo{
		Name: agentInfo.Name,
		ID:   agentInfo.ID,
	}
	
	toolAction := tools.Action{
		Type:    action.Type,
		Content: action.Content,
		Target:  action.Target,
		Options: action.Options,
	}
	
	return ta.tool.ProcessAction(ctx, toolAgentInfo, toolAction)
}

func main() {
	log.SetOutput(os.Stdout)
	fmt.Println("=== TinyTroupe Go Document Creation Example ===")
	fmt.Println("")

	cfg := config.DefaultConfig()
	cfg.MaxTokens = 300

	// Create tool registry
	toolRegistry := tools.NewAgentToolRegistry(cfg)
	adapter := &ToolRegistryAdapter{registry: toolRegistry}

	// Create a business consultant agent
	consultant := agent.NewTinyPerson("Elena Rodriguez", cfg)
	consultant.Define("age", 35)
	consultant.Define("nationality", "Spanish")
	consultant.Define("residence", "Madrid, Spain")
	consultant.Define("occupation", map[string]interface{}{
		"title":        "Senior Business Consultant",
		"organization": "Strategic Solutions Inc.",
		"experience":   "12 years",
		"specialties":  []string{"Digital Transformation", "Process Optimization", "Change Management"},
	})
	consultant.Define("interests", []string{
		"Business strategy and innovation",
		"Technology trends and AI adoption",
		"Cross-cultural business practices",
		"Leadership development",
	})
	consultant.Define("goals", []string{
		"Help clients achieve digital transformation",
		"Create actionable business insights",
		"Build lasting client relationships",
	})

	// Set up tool registry for the agent
	consultant.SetToolRegistry(adapter)

	// Create environment
	_ = environment.NewTinyWorld("Business Office", cfg, consultant)

	fmt.Printf("✓ Created business consultant: %s\n", consultant.Name)
	fmt.Println("")

	// Scenario 1: Strategic Business Proposal
	fmt.Println("=== Scenario 1: Business Proposal Creation ===")
	fmt.Println("")

	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Minute)
	defer cancel()

	// Request strategic proposal
	proposalRequest := `You need to create a strategic business proposal for a client who wants to implement AI automation in their customer service department. 
	
	Create a comprehensive proposal document that includes:
	- Executive summary of the AI automation opportunity
	- Implementation strategy and timeline
	- Expected benefits and ROI
	- Risk mitigation strategies
	
	Use the WRITE_DOCUMENT action to create this proposal.`

	fmt.Println("📋 Request: Strategic AI automation proposal")
	actions, err := consultant.ListenAndAct(ctx, proposalRequest, nil)
	if err != nil {
		log.Printf("Error: %v", err)
	} else {
		fmt.Printf("✓ Elena completed %d action(s)\n", len(actions))
	}

	fmt.Println("")
	time.Sleep(2 * time.Second)

	// Scenario 2: Market Research Report
	fmt.Println("=== Scenario 2: Market Research Report ===")
	fmt.Println("")

	researchRequest := `Based on your expertise, create a market research report about the current trends in digital transformation for mid-size companies in Europe.

	The report should cover:
	- Key market trends and drivers
	- Technology adoption patterns
	- Challenges and opportunities
	- Strategic recommendations

	Use the WRITE_DOCUMENT action to create this report.`

	fmt.Println("📊 Request: Digital transformation market research")
	actions, err = consultant.ListenAndAct(ctx, researchRequest, nil)
	if err != nil {
		log.Printf("Error: %v", err)
	} else {
		fmt.Printf("✓ Elena completed %d action(s)\n", len(actions))
	}

	fmt.Println("")
	time.Sleep(2 * time.Second)

	// Scenario 3: Data Export of Insights
	fmt.Println("=== Scenario 3: Export Business Insights ===")
	fmt.Println("")

	exportRequest := `You need to export key business insights from your recent work for the executive team. 

	Create a data export containing:
	- Summary of top 5 business recommendations
	- Client satisfaction metrics
	- ROI projections for proposed solutions
	- Implementation timelines

	Use the EXPORT_DATA action to save this information in JSON format.`

	fmt.Println("💾 Request: Export business insights")
	actions, err = consultant.ListenAndAct(ctx, exportRequest, nil)
	if err != nil {
		log.Printf("Error: %v", err)
	} else {
		fmt.Printf("✓ Elena completed %d action(s)\n", len(actions))
	}

	fmt.Println("")
	fmt.Println("=== Document Creation Summary ===")
	fmt.Println("")
	fmt.Println("✅ Business consultant demonstrated:")
	fmt.Println("   • Strategic proposal writing with structured format")
	fmt.Println("   • Market research report creation")
	fmt.Println("   • Business data export and analysis")
	fmt.Println("   • Professional document generation using AI tools")
	fmt.Println("")
	fmt.Println("📁 Generated files can be found in:")
	fmt.Println("   • ./documents/ - Business proposals and reports")
	fmt.Println("   • ./exports/ - Data exports and insights")
	fmt.Println("")
	fmt.Println("=== Document Creation Example Complete ===")
}