package tools

import (
	"context"
	"strings"
	"testing"
)

func TestConversationAnalysisTool(t *testing.T) {
	tool := NewConversationAnalysisTool()
	ctx := context.Background()

	if tool.GetName() != "Conversation Analyzer" {
		t.Error("Incorrect tool name")
	}

	if len(tool.GetDescription()) == 0 {
		t.Error("Tool should have a description")
	}

	supportedTypes := tool.GetSupportedTypes()
	if len(supportedTypes) != 1 || supportedTypes[0] != ConversationAnalyzer {
		t.Error("Tool should support ConversationAnalyzer type")
	}

	// Test with nil request
	_, err := tool.Analyze(ctx, nil)
	if err == nil {
		t.Error("Should return error for nil request")
	}

	// Test with valid conversation data
	conversationData := map[string]interface{}{
		"messages": []interface{}{
			"Hello there!",
			"Hi, how are you?",
			"I'm doing great, thanks!",
		},
		"participants": []interface{}{"Alice", "Bob", "Charlie"},
		"topics":       []interface{}{"greetings", "wellbeing"},
	}

	req := &AnalysisRequest{
		Type: ConversationAnalyzer,
		Data: conversationData,
		Options: map[string]interface{}{
			"analyze_sentiment": true,
		},
	}

	result, err := tool.Analyze(ctx, req)
	if err != nil {
		t.Fatalf("Analysis failed: %v", err)
	}

	if result == nil {
		t.Fatal("Result should not be nil")
	}

	if result.Type != ConversationAnalyzer {
		t.Error("Result type should match request type")
	}

	if len(result.Insights) == 0 {
		t.Error("Should generate insights for conversation data")
	}

	if len(result.Metrics) == 0 {
		t.Error("Should generate metrics for conversation data")
	}

	// Check specific insights
	foundConversationFlow := false
	foundParticipation := false
	for _, insight := range result.Insights {
		if insight.Category == "conversation_flow" {
			foundConversationFlow = true
		}
		if insight.Category == "participation" {
			foundParticipation = true
		}
	}

	if !foundConversationFlow {
		t.Error("Should detect conversation flow insights")
	}

	if !foundParticipation {
		t.Error("Should detect participation insights")
	}
}

func TestPerformanceAnalysisTool(t *testing.T) {
	tool := NewPerformanceAnalysisTool()
	ctx := context.Background()

	if tool.GetName() != "Performance Analyzer" {
		t.Error("Incorrect tool name")
	}

	supportedTypes := tool.GetSupportedTypes()
	if len(supportedTypes) != 1 || supportedTypes[0] != PerformanceAnalyzer {
		t.Error("Tool should support PerformanceAnalyzer type")
	}

	// Test with performance data showing high memory usage
	performanceData := map[string]interface{}{
		"memory": map[string]interface{}{
			"max_bytes":     int64(200 * 1024 * 1024), // 200MB
			"average_bytes": int64(150 * 1024 * 1024), // 150MB
		},
		"cpu": map[string]interface{}{
			"max_percent":     85.5,
			"average_percent": 60.0,
		},
		"duration":     "5m30s",
		"sample_count": 100,
	}

	req := &AnalysisRequest{
		Type: PerformanceAnalyzer,
		Data: performanceData,
	}

	result, err := tool.Analyze(ctx, req)
	if err != nil {
		t.Fatalf("Analysis failed: %v", err)
	}

	if result.Type != PerformanceAnalyzer {
		t.Error("Result type should match request type")
	}

	// Should detect high memory and CPU usage
	foundMemoryIssue := false
	foundCPUIssue := false
	for _, insight := range result.Insights {
		if insight.Category == "memory_usage" {
			foundMemoryIssue = true
		}
		if insight.Category == "cpu_usage" {
			foundCPUIssue = true
		}
	}

	if !foundMemoryIssue {
		t.Error("Should detect high memory usage")
	}

	if !foundCPUIssue {
		t.Error("Should detect high CPU usage")
	}

	// Should generate optimization suggestions
	foundMemoryOptimization := false
	foundCPUOptimization := false
	for _, suggestion := range result.Suggestions {
		if suggestion.Category == "optimization" && suggestion.Action == "reduce_memory_footprint" {
			foundMemoryOptimization = true
		}
		if suggestion.Category == "optimization" && suggestion.Action == "optimize_cpu_usage" {
			foundCPUOptimization = true
		}
	}

	if !foundMemoryOptimization {
		t.Error("Should suggest memory optimization")
	}

	if !foundCPUOptimization {
		t.Error("Should suggest CPU optimization")
	}
}

func TestDebugTool(t *testing.T) {
	tool := NewDebugTool()
	ctx := context.Background()

	if tool.GetName() != "Simulation Debugger" {
		t.Error("Incorrect tool name")
	}

	supportedTypes := tool.GetSupportedTypes()
	if len(supportedTypes) != 1 || supportedTypes[0] != SimulationDebugger {
		t.Error("Tool should support SimulationDebugger type")
	}

	// Test with simulation data showing errors and inactive agents
	simulationData := map[string]interface{}{
		"errors": []interface{}{
			"Agent timeout error",
			"Connection failed",
		},
		"agents": []interface{}{
			map[string]interface{}{"id": "agent1", "active": true},
			map[string]interface{}{"id": "agent2", "active": false},
			map[string]interface{}{"id": "agent3", "active": false},
		},
	}

	req := &AnalysisRequest{
		Type: SimulationDebugger,
		Data: simulationData,
	}

	result, err := tool.Analyze(ctx, req)
	if err != nil {
		t.Fatalf("Analysis failed: %v", err)
	}

	if result.Type != SimulationDebugger {
		t.Error("Result type should match request type")
	}

	// Should detect errors and inactive agents
	foundErrors := false
	foundInactiveAgents := false
	for _, insight := range result.Insights {
		if insight.Category == "errors" {
			foundErrors = true
		}
		if insight.Category == "agent_state" {
			foundInactiveAgents = true
		}
	}

	if !foundErrors {
		t.Error("Should detect simulation errors")
	}

	if !foundInactiveAgents {
		t.Error("Should detect inactive agents")
	}

	// Check debug metrics
	if errorCount, exists := result.Metrics["error_count"]; !exists || errorCount != 2 {
		t.Error("Should count errors correctly")
	}

	if agentCount, exists := result.Metrics["total_agents"]; !exists || agentCount != 3 {
		t.Error("Should count agents correctly")
	}
}

func TestToolRegistry(t *testing.T) {
	registry := NewToolRegistry()

	// Check that default tools are registered
	tools := registry.ListTools()
	if len(tools) != 3 {
		t.Errorf("Expected 3 default tools, got %d", len(tools))
	}

	expectedTypes := []ToolType{ConversationAnalyzer, PerformanceAnalyzer, SimulationDebugger}
	for _, expectedType := range expectedTypes {
		if _, exists := tools[expectedType]; !exists {
			t.Errorf("Expected tool type %s not found", expectedType)
		}
	}

	// Test getting a tool
	conversationTool, err := registry.GetTool(ConversationAnalyzer)
	if err != nil {
		t.Errorf("Failed to get conversation tool: %v", err)
	}

	if conversationTool.GetName() != "Conversation Analyzer" {
		t.Error("Retrieved tool has incorrect name")
	}

	// Test getting non-existent tool
	_, err = registry.GetTool("non_existent")
	if err == nil {
		t.Error("Should return error for non-existent tool")
	}

	// Test registering a new tool
	customTool := NewDebugTool() // Reuse debug tool for simplicity
	registry.RegisterTool("custom_tool", customTool)

	retrievedTool, err := registry.GetTool("custom_tool")
	if err != nil {
		t.Errorf("Failed to get custom tool: %v", err)
	}

	if retrievedTool != customTool {
		t.Error("Retrieved custom tool is not the same instance")
	}
}

func TestToolRegistryAnalyzeWith(t *testing.T) {
	registry := NewToolRegistry()
	ctx := context.Background()

	// Test conversation analysis through registry
	conversationData := map[string]interface{}{
		"messages":     []interface{}{"Hello", "Hi there", "How are you?"},
		"participants": []interface{}{"Alice", "Bob"},
	}

	req := &AnalysisRequest{
		Data: conversationData,
		Options: map[string]interface{}{
			"detailed": true,
		},
	}

	result, err := registry.AnalyzeWith(ctx, ConversationAnalyzer, req)
	if err != nil {
		t.Fatalf("Registry analysis failed: %v", err)
	}

	if result.Type != ConversationAnalyzer {
		t.Error("Result type should be set correctly by registry")
	}

	if len(result.Insights) == 0 {
		t.Error("Should generate insights through registry")
	}
}

func TestComprehensiveReport(t *testing.T) {
	registry := NewToolRegistry()
	ctx := context.Background()

	// Test data that should trigger analysis from multiple tools
	testData := map[string]interface{}{
		"messages": []interface{}{
			"Hello everyone!",
			"Hi there, how are you doing?",
			"I'm doing great, thanks for asking!",
		},
		"participants": []interface{}{"Alice", "Bob", "Charlie"},
		"topics":       []interface{}{"greetings", "wellbeing"},
		"memory": map[string]interface{}{
			"max_bytes": int64(50 * 1024 * 1024), // 50MB (below threshold)
		},
		"cpu": map[string]interface{}{
			"max_percent": 45.0, // Below threshold
		},
		"errors": []interface{}{}, // No errors
		"agents": []interface{}{
			map[string]interface{}{"id": "agent1", "active": true},
			map[string]interface{}{"id": "agent2", "active": true},
		},
	}

	options := map[string]interface{}{
		"comprehensive":       true,
		"include_suggestions": true,
	}

	report, err := registry.GenerateReport(ctx, testData, options)
	if err != nil {
		t.Fatalf("Failed to generate comprehensive report: %v", err)
	}

	if report == nil {
		t.Fatal("Report should not be nil")
	}

	if report.Timestamp.IsZero() {
		t.Error("Report should have a timestamp")
	}

	// Should have sections for each tool that could analyze the data
	if len(report.Sections) == 0 {
		t.Error("Report should have analysis sections")
	}

	// Check that conversation analysis section exists
	if _, exists := report.Sections["conversation_analyzer"]; !exists {
		t.Error("Report should include conversation analysis section")
	}

	// Check summary
	if report.Summary == nil {
		t.Error("Report should have a summary")
	}

	if totalInsights, exists := report.Summary["total_insights"]; !exists {
		t.Error("Summary should include total insights count")
	} else if count, ok := totalInsights.(int); !ok || count < 0 {
		t.Error("Total insights should be a non-negative integer")
	}

	if sectionsAnalyzed, exists := report.Summary["sections_analyzed"]; !exists {
		t.Error("Summary should include sections analyzed count")
	} else if count, ok := sectionsAnalyzed.(int); !ok || count <= 0 {
		t.Error("Sections analyzed should be a positive integer")
	}
}

func TestDifferentDataTypes(t *testing.T) {
	tool := NewConversationAnalysisTool()
	ctx := context.Background()

	testCases := []struct {
		name        string
		data        interface{}
		expectError bool
	}{
		{
			name:        "string_data",
			data:        "This is a conversation string",
			expectError: false,
		},
		{
			name:        "json_string",
			data:        `{"messages": ["hello", "hi"], "participants": ["Alice", "Bob"]}`,
			expectError: false,
		},
		{
			name:        "slice_data",
			data:        []interface{}{"message1", "message2", "message3"},
			expectError: false,
		},
		{
			name: "map_data",
			data: map[string]interface{}{
				"messages":     []interface{}{"hello", "hi"},
				"participants": []interface{}{"Alice", "Bob"},
			},
			expectError: false,
		},
		{
			name:        "number_data",
			data:        12345,
			expectError: false, // Should handle gracefully
		},
	}

	for _, tc := range testCases {
		t.Run(tc.name, func(t *testing.T) {
			req := &AnalysisRequest{
				Type: ConversationAnalyzer,
				Data: tc.data,
			}

			result, err := tool.Analyze(ctx, req)

			if tc.expectError && err == nil {
				t.Error("Expected error but got none")
			}

			if !tc.expectError && err != nil {
				t.Errorf("Unexpected error: %v", err)
			}

			if !tc.expectError && result == nil {
				t.Error("Result should not be nil for valid data")
			}
		})
	}
}

func TestInsightAndSuggestionStructure(t *testing.T) {
	tool := NewConversationAnalysisTool()
	ctx := context.Background()

	conversationData := map[string]interface{}{
		"messages":     []interface{}{"Hello", "Hi"},
		"participants": []interface{}{"Alice", "Bob"},
		"topics":       []interface{}{"greetings"},
	}

	req := &AnalysisRequest{
		Type: ConversationAnalyzer,
		Data: conversationData,
	}

	result, err := tool.Analyze(ctx, req)
	if err != nil {
		t.Fatalf("Analysis failed: %v", err)
	}

	// Check insight structure
	for i, insight := range result.Insights {
		if insight.Category == "" {
			t.Errorf("Insight %d should have a category", i)
		}

		if insight.Title == "" {
			t.Errorf("Insight %d should have a title", i)
		}

		if insight.Description == "" {
			t.Errorf("Insight %d should have a description", i)
		}

		if insight.Confidence < 0 || insight.Confidence > 1 {
			t.Errorf("Insight %d confidence should be between 0 and 1, got %f", i, insight.Confidence)
		}

		if len(insight.Evidence) == 0 {
			t.Errorf("Insight %d should have evidence", i)
		}

		if insight.Metadata == nil {
			t.Errorf("Insight %d should have metadata", i)
		}
	}

	// Check suggestion structure
	for i, suggestion := range result.Suggestions {
		if suggestion.Title == "" {
			t.Errorf("Suggestion %d should have a title", i)
		}

		if suggestion.Description == "" {
			t.Errorf("Suggestion %d should have a description", i)
		}

		if suggestion.Priority == "" {
			t.Errorf("Suggestion %d should have a priority", i)
		}

		validPriorities := []string{"high", "medium", "low"}
		found := false
		for _, valid := range validPriorities {
			if suggestion.Priority == valid {
				found = true
				break
			}
		}
		if !found {
			t.Errorf("Suggestion %d has invalid priority: %s", i, suggestion.Priority)
		}

		if suggestion.Category == "" {
			t.Errorf("Suggestion %d should have a category", i)
		}

		if suggestion.Action == "" {
			t.Errorf("Suggestion %d should have an action", i)
		}
	}
}

func TestUnsupportedAnalysisType(t *testing.T) {
	tool := NewConversationAnalysisTool()
	ctx := context.Background()

	req := &AnalysisRequest{
		Type: "unsupported_type",
		Data: map[string]interface{}{"test": "data"},
	}

	_, err := tool.Analyze(ctx, req)
	if err == nil {
		t.Error("Should return error for unsupported analysis type")
	}

	if !strings.Contains(err.Error(), "unsupported analysis type") {
		t.Errorf("Error message should mention unsupported type, got: %v", err)
	}
}

func TestEmptyData(t *testing.T) {
	tool := NewConversationAnalysisTool()
	ctx := context.Background()

	// Test with empty data
	req := &AnalysisRequest{
		Type: ConversationAnalyzer,
		Data: map[string]interface{}{},
	}

	result, err := tool.Analyze(ctx, req)
	if err != nil {
		t.Fatalf("Should handle empty data gracefully: %v", err)
	}

	if result == nil {
		t.Fatal("Result should not be nil")
	}

	// Should still have basic structure even with empty data
	if result.Metrics == nil {
		t.Error("Result should have metrics map even with empty data")
	}

	if result.Insights == nil {
		t.Error("Result should have insights slice even with empty data")
	}

	if result.Suggestions == nil {
		t.Error("Result should have suggestions slice even with empty data")
	}
}
