package main

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"os"
	"time"

	"github.com/microsoft/TinyTroupe/go/pkg/agent"
	"github.com/microsoft/TinyTroupe/go/pkg/config"
	"github.com/microsoft/TinyTroupe/go/pkg/experimentation"
)

func main() {
	fmt.Println("=== TinyTroupe Go A/B Testing Example ===")
	fmt.Println("")

	cfg := config.DefaultConfig()

	// Load agents for the experiment
	fmt.Println("Loading agents for A/B testing experiment...")

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

	lila, err := loadAgentFromJSON("examples/agents/Lila.agent.json", cfg)
	if err != nil {
		log.Fatalf("Failed to load Lila: %v", err)
	}

	fmt.Printf("✓ %s - %s\n", lisa.Name, getOccupationTitle(lisa))
	fmt.Printf("✓ %s - %s\n", oscar.Name, getOccupationTitle(oscar))
	fmt.Printf("✓ %s - %s\n", marcos.Name, getOccupationTitle(marcos))
	fmt.Printf("✓ %s - %s\n", lila.Name, getOccupationTitle(lila))
	fmt.Println("")

	// Set up experiment runner
	fmt.Println("Setting up A/B testing experiment...")
	runner := experimentation.NewExperimentRunner()

	// Define experiment configuration
	abConfig := &experimentation.ExperimentConfig{
		Type:         experimentation.ABTestExperiment,
		Name:         "Agent Collaboration Enhancement",
		Description:  "Testing the impact of enhanced collaboration prompts on agent performance",
		Duration:     time.Hour * 2, // Simulate 2-hour experiment
		SampleSize:   200,           // 200 simulated interactions
		Significance: 0.05,          // 95% confidence level
		Variables: map[string]interface{}{
			"control_prompt":   "standard collaboration prompt",
			"treatment_prompt": "enhanced collaboration prompt with empathy cues",
		},
		Metrics: []string{
			"engagement_score",
			"task_completion_rate",
			"response_time",
			"satisfaction_rating",
		},
		RandomSeed: 42,
	}

	// Create and register the A/B test experiment
	abExperiment := experimentation.NewABTestExperiment(abConfig)
	runner.RegisterExperiment("collaboration_test", abExperiment)

	fmt.Printf("✓ Created A/B test: %s\n", abConfig.Name)
	fmt.Printf("  Sample size: %d participants\n", abConfig.SampleSize)
	fmt.Printf("  Significance level: %.1f%%\n", (1-abConfig.Significance)*100)
	fmt.Printf("  Metrics: %v\n", abConfig.Metrics)
	fmt.Println("")

	// Run the experiment
	fmt.Println("=== Running A/B Test Experiment ===")
	fmt.Println("")

	ctx := context.Background()
	result, err := runner.RunExperiment(ctx, "collaboration_test")
	if err != nil {
		log.Fatalf("Failed to run experiment: %v", err)
	}

	// Display results
	fmt.Println("📊 Experiment Results:")
	fmt.Printf("  Duration: %v\n", result.Duration)
	fmt.Printf("  Sample size: %d\n", result.SampleSize)
	fmt.Printf("  Groups: %d (Control: %d, Treatment: %d)\n",
		len(result.Groups),
		result.Groups["control"].Size,
		result.Groups["treatment"].Size)
	fmt.Println("")

	// Show detailed metrics comparison
	fmt.Println("📈 Metrics Comparison:")
	for _, metric := range abConfig.Metrics {
		controlMean := result.Groups["control"].Summary[metric+"_mean"]
		treatmentMean := result.Groups["treatment"].Summary[metric+"_mean"]
		improvement := ((treatmentMean - controlMean) / controlMean) * 100

		fmt.Printf("  %s:\n", metric)
		fmt.Printf("    Control:   %.3f\n", controlMean)
		fmt.Printf("    Treatment: %.3f\n", treatmentMean)
		if improvement > 0 {
			fmt.Printf("    Improvement: +%.1f%%\n", improvement)
		} else {
			fmt.Printf("    Change: %.1f%%\n", improvement)
		}
		fmt.Println("")
	}

	// Show statistical analysis
	fmt.Println("🔬 Statistical Analysis:")
	analysis := result.Analysis
	fmt.Printf("  Method: %s\n", analysis.Method)
	fmt.Printf("  P-value: %.6f\n", analysis.PValue)
	fmt.Printf("  Test statistic: %.3f\n", analysis.TestStat)
	fmt.Printf("  Degrees of freedom: %d\n", analysis.DegreesOfFreedom)
	fmt.Printf("  Effect size (Cohen's d): %.3f\n", analysis.EffectSize)
	fmt.Printf("  Statistical power: %.1f%%\n", analysis.PowerAnalysis["power"]*100)
	fmt.Println("")

	// Interpret effect size
	fmt.Println("📏 Effect Size Interpretation:")
	effectSize := analysis.EffectSize
	if effectSize < 0.2 {
		fmt.Println("  Small effect (< 0.2)")
	} else if effectSize < 0.5 {
		fmt.Println("  Small to medium effect (0.2 - 0.5)")
	} else if effectSize < 0.8 {
		fmt.Println("  Medium to large effect (0.5 - 0.8)")
	} else {
		fmt.Println("  Large effect (> 0.8)")
	}
	fmt.Println("")

	// Show significance and conclusion
	fmt.Println("🎯 Experiment Conclusion:")
	if result.Significance {
		fmt.Printf("  ✅ STATISTICALLY SIGNIFICANT (p < %.2f)\n", abConfig.Significance)
	} else {
		fmt.Printf("  ❌ NOT STATISTICALLY SIGNIFICANT (p >= %.2f)\n", abConfig.Significance)
	}
	fmt.Printf("  Confidence level: %.1f%%\n", result.ConfidenceLevel*100)
	fmt.Println("")
	fmt.Printf("  📝 %s\n", result.Conclusion)
	fmt.Println("")

	// Show recommendations
	fmt.Println("💡 Recommendations:")
	for i, rec := range analysis.Recommendations {
		fmt.Printf("  %d. %s\n", i+1, rec)
	}
	fmt.Println("")

	// Demonstrate multiple experiments
	fmt.Println("=== Running Additional Experiment ===")
	fmt.Println("")

	// Create a second experiment focusing on response time
	rtConfig := &experimentation.ExperimentConfig{
		Type:         experimentation.ABTestExperiment,
		Name:         "Response Time Optimization",
		Description:  "Testing optimized prompts for faster agent responses",
		Duration:     time.Minute * 30,
		SampleSize:   150,
		Significance: 0.05,
		Variables: map[string]interface{}{
			"control_prompt":   "standard response prompt",
			"treatment_prompt": "optimized response prompt for speed",
		},
		Metrics: []string{
			"response_time",
			"task_completion_rate",
		},
		RandomSeed: 123,
	}

	rtExperiment := experimentation.NewABTestExperiment(rtConfig)
	runner.RegisterExperiment("response_time_test", rtExperiment)

	rtResult, err := runner.RunExperiment(ctx, "response_time_test")
	if err != nil {
		log.Printf("Failed to run response time experiment: %v", err)
	} else {
		fmt.Printf("✅ Response Time Experiment completed\n")
		fmt.Printf("   P-value: %.4f\n", rtResult.Analysis.PValue)
		fmt.Printf("   Significant: %t\n", rtResult.Significance)
		fmt.Printf("   Effect size: %.3f\n", rtResult.Analysis.EffectSize)
		fmt.Println("")
	}

	// Summary
	fmt.Println("=== A/B Testing Summary ===")
	fmt.Println("")
	fmt.Println("✅ Demonstrated A/B testing capabilities:")
	fmt.Println("   • Statistical significance testing with Welch's t-test")
	fmt.Println("   • Effect size calculation (Cohen's d)")
	fmt.Println("   • Power analysis for sample size validation")
	fmt.Println("   • Multiple metric tracking and comparison")
	fmt.Println("   • Automated recommendations based on results")
	fmt.Println("   • Support for multiple concurrent experiments")
	fmt.Println("")
	fmt.Printf("📊 Total experiments run: 2\n")
	fmt.Printf("📈 Agents available for testing: %d\n", 4)
	fmt.Println("🔬 Ready for production experimentation workflows")

	fmt.Println("")
	fmt.Println("=== A/B Testing Example Complete ===")
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
