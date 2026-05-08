// Package tools provides utility tools for simulation analysis and debugging.
// This module handles various tools for TinyTroupe simulations including analysis,
// debugging, visualization helpers, and development utilities.
package tools

import (
	"context"
	"encoding/json"
	"fmt"
	"time"
)

// ToolType represents different types of analysis tools
type ToolType string

const (
	ConversationAnalyzer ToolType = "conversation_analyzer"
	PerformanceAnalyzer  ToolType = "performance_analyzer"
	BehaviorAnalyzer     ToolType = "behavior_analyzer"
	SimulationDebugger   ToolType = "simulation_debugger"
	DataExporter         ToolType = "data_exporter"
	ReportGenerator      ToolType = "report_generator"
)

// AnalysisRequest represents a request for analysis
type AnalysisRequest struct {
	Type     ToolType               `json:"type"`
	Data     interface{}            `json:"data"`
	Options  map[string]interface{} `json:"options"`
	Context  map[string]interface{} `json:"context"`
	Metadata map[string]interface{} `json:"metadata"`
}

// AnalysisResult represents the result of an analysis
type AnalysisResult struct {
	Type        ToolType               `json:"type"`
	Insights    []Insight              `json:"insights"`
	Metrics     map[string]interface{} `json:"metrics"`
	Suggestions []Suggestion           `json:"suggestions"`
	Timestamp   time.Time              `json:"timestamp"`
	Metadata    map[string]interface{} `json:"metadata"`
}

// Insight represents a discovered insight from analysis
type Insight struct {
	Category    string                 `json:"category"`
	Title       string                 `json:"title"`
	Description string                 `json:"description"`
	Confidence  float64                `json:"confidence"`
	Evidence    []string               `json:"evidence"`
	Metadata    map[string]interface{} `json:"metadata"`
}

// Suggestion represents an actionable suggestion
type Suggestion struct {
	Title       string                 `json:"title"`
	Description string                 `json:"description"`
	Priority    string                 `json:"priority"` // "high", "medium", "low"
	Category    string                 `json:"category"`
	Action      string                 `json:"action"`
	Metadata    map[string]interface{} `json:"metadata"`
}

// Tool interface defines analysis tool capabilities
type Tool interface {
	// Analyze performs analysis on the provided data
	Analyze(ctx context.Context, req *AnalysisRequest) (*AnalysisResult, error)

	// GetSupportedTypes returns the tool types this analyzer supports
	GetSupportedTypes() []ToolType

	// GetName returns the name of the tool
	GetName() string

	// GetDescription returns a description of what the tool does
	GetDescription() string
}

// ConversationAnalysisTool analyzes conversation patterns and behaviors
type ConversationAnalysisTool struct {
	name        string
	description string
}

// NewConversationAnalysisTool creates a new conversation analysis tool
func NewConversationAnalysisTool() *ConversationAnalysisTool {
	return &ConversationAnalysisTool{
		name:        "Conversation Analyzer",
		description: "Analyzes conversation patterns, communication styles, and interaction dynamics",
	}
}

// Analyze implements the Tool interface for conversation analysis
func (cat *ConversationAnalysisTool) Analyze(ctx context.Context, req *AnalysisRequest) (*AnalysisResult, error) {
	if req == nil {
		return nil, fmt.Errorf("analysis request cannot be nil")
	}

	result := &AnalysisResult{
		Type:        req.Type,
		Insights:    make([]Insight, 0),
		Metrics:     make(map[string]interface{}),
		Suggestions: make([]Suggestion, 0),
		Timestamp:   time.Now(),
		Metadata:    make(map[string]interface{}),
	}

	switch req.Type {
	case ConversationAnalyzer:
		return cat.analyzeConversation(req.Data, req.Options, result)
	default:
		return nil, fmt.Errorf("unsupported analysis type: %s", req.Type)
	}
}

// GetSupportedTypes returns supported analysis types
func (cat *ConversationAnalysisTool) GetSupportedTypes() []ToolType {
	return []ToolType{ConversationAnalyzer}
}

// GetName returns the tool name
func (cat *ConversationAnalysisTool) GetName() string {
	return cat.name
}

// GetDescription returns the tool description
func (cat *ConversationAnalysisTool) GetDescription() string {
	return cat.description
}

// analyzeConversation performs conversation-specific analysis
func (cat *ConversationAnalysisTool) analyzeConversation(data interface{}, options map[string]interface{}, result *AnalysisResult) (*AnalysisResult, error) {
	// Parse conversation data
	conversationData, err := cat.parseConversationData(data)
	if err != nil {
		return nil, fmt.Errorf("failed to parse conversation data: %w", err)
	}

	// Analyze conversation patterns
	insights := cat.identifyConversationPatterns(conversationData)
	result.Insights = append(result.Insights, insights...)

	// Calculate conversation metrics
	metrics := cat.calculateConversationMetrics(conversationData)
	result.Metrics = metrics

	// Generate suggestions
	suggestions := cat.generateConversationSuggestions(conversationData, insights)
	result.Suggestions = suggestions

	return result, nil
}

// PerformanceAnalysisTool analyzes simulation performance
type PerformanceAnalysisTool struct {
	name        string
	description string
}

// NewPerformanceAnalysisTool creates a new performance analysis tool
func NewPerformanceAnalysisTool() *PerformanceAnalysisTool {
	return &PerformanceAnalysisTool{
		name:        "Performance Analyzer",
		description: "Analyzes simulation performance, bottlenecks, and resource usage",
	}
}

// Analyze implements the Tool interface for performance analysis
func (pat *PerformanceAnalysisTool) Analyze(ctx context.Context, req *AnalysisRequest) (*AnalysisResult, error) {
	if req == nil {
		return nil, fmt.Errorf("analysis request cannot be nil")
	}

	result := &AnalysisResult{
		Type:        req.Type,
		Insights:    make([]Insight, 0),
		Metrics:     make(map[string]interface{}),
		Suggestions: make([]Suggestion, 0),
		Timestamp:   time.Now(),
		Metadata:    make(map[string]interface{}),
	}

	switch req.Type {
	case PerformanceAnalyzer:
		return pat.analyzePerformance(req.Data, req.Options, result)
	default:
		return nil, fmt.Errorf("unsupported analysis type: %s", req.Type)
	}
}

// GetSupportedTypes returns supported analysis types
func (pat *PerformanceAnalysisTool) GetSupportedTypes() []ToolType {
	return []ToolType{PerformanceAnalyzer}
}

// GetName returns the tool name
func (pat *PerformanceAnalysisTool) GetName() string {
	return pat.name
}

// GetDescription returns the tool description
func (pat *PerformanceAnalysisTool) GetDescription() string {
	return pat.description
}

// analyzePerformance performs performance-specific analysis
func (pat *PerformanceAnalysisTool) analyzePerformance(data interface{}, options map[string]interface{}, result *AnalysisResult) (*AnalysisResult, error) {
	// Parse performance data
	performanceData, err := pat.parsePerformanceData(data)
	if err != nil {
		return nil, fmt.Errorf("failed to parse performance data: %w", err)
	}

	// Identify performance issues
	insights := pat.identifyPerformanceIssues(performanceData)
	result.Insights = append(result.Insights, insights...)

	// Calculate performance metrics
	metrics := pat.calculatePerformanceMetrics(performanceData)
	result.Metrics = metrics

	// Generate optimization suggestions
	suggestions := pat.generateOptimizationSuggestions(performanceData, insights)
	result.Suggestions = suggestions

	return result, nil
}

// DebugTool provides debugging utilities for simulations
type DebugTool struct {
	name        string
	description string
}

// NewDebugTool creates a new debug tool
func NewDebugTool() *DebugTool {
	return &DebugTool{
		name:        "Simulation Debugger",
		description: "Provides debugging utilities and diagnostic information for simulations",
	}
}

// Analyze implements the Tool interface for debugging
func (dt *DebugTool) Analyze(ctx context.Context, req *AnalysisRequest) (*AnalysisResult, error) {
	if req == nil {
		return nil, fmt.Errorf("analysis request cannot be nil")
	}

	result := &AnalysisResult{
		Type:        req.Type,
		Insights:    make([]Insight, 0),
		Metrics:     make(map[string]interface{}),
		Suggestions: make([]Suggestion, 0),
		Timestamp:   time.Now(),
		Metadata:    make(map[string]interface{}),
	}

	switch req.Type {
	case SimulationDebugger:
		return dt.debugSimulation(req.Data, req.Options, result)
	default:
		return nil, fmt.Errorf("unsupported analysis type: %s", req.Type)
	}
}

// GetSupportedTypes returns supported analysis types
func (dt *DebugTool) GetSupportedTypes() []ToolType {
	return []ToolType{SimulationDebugger}
}

// GetName returns the tool name
func (dt *DebugTool) GetName() string {
	return dt.name
}

// GetDescription returns the tool description
func (dt *DebugTool) GetDescription() string {
	return dt.description
}

// debugSimulation provides debugging analysis
func (dt *DebugTool) debugSimulation(data interface{}, options map[string]interface{}, result *AnalysisResult) (*AnalysisResult, error) {
	// Parse simulation data
	simData, err := dt.parseSimulationData(data)
	if err != nil {
		return nil, fmt.Errorf("failed to parse simulation data: %w", err)
	}

	// Identify potential issues
	insights := dt.identifySimulationIssues(simData)
	result.Insights = append(result.Insights, insights...)

	// Calculate debug metrics
	metrics := dt.calculateDebugMetrics(simData)
	result.Metrics = metrics

	// Generate debug suggestions
	suggestions := dt.generateDebugSuggestions(simData, insights)
	result.Suggestions = suggestions

	return result, nil
}

// Helper methods for ConversationAnalysisTool

func (cat *ConversationAnalysisTool) parseConversationData(data interface{}) (map[string]interface{}, error) {
	// Handle different data types
	switch d := data.(type) {
	case map[string]interface{}:
		return d, nil
	case string:
		// Try to parse as JSON
		var parsed map[string]interface{}
		if err := json.Unmarshal([]byte(d), &parsed); err != nil {
			// If not JSON, create a simple structure
			return map[string]interface{}{
				"raw_data": d,
				"type":     "string",
			}, nil
		}
		return parsed, nil
	case []interface{}:
		return map[string]interface{}{
			"messages": d,
			"type":     "message_list",
		}, nil
	default:
		return map[string]interface{}{
			"data": d,
			"type": "unknown",
		}, nil
	}
}

func (cat *ConversationAnalysisTool) identifyConversationPatterns(data map[string]interface{}) []Insight {
	insights := make([]Insight, 0)

	// Analyze message patterns
	if messages, exists := data["messages"]; exists {
		if msgList, ok := messages.([]interface{}); ok && len(msgList) > 0 {
			insights = append(insights, Insight{
				Category:    "conversation_flow",
				Title:       "Active Conversation Detected",
				Description: fmt.Sprintf("Conversation contains %d messages with active exchange", len(msgList)),
				Confidence:  0.9,
				Evidence:    []string{fmt.Sprintf("%d messages found", len(msgList))},
				Metadata:    map[string]interface{}{"message_count": len(msgList)},
			})
		}
	}

	// Analyze conversation diversity
	if participants, exists := data["participants"]; exists {
		if partList, ok := participants.([]interface{}); ok {
			if len(partList) > 2 {
				insights = append(insights, Insight{
					Category:    "participation",
					Title:       "Multi-Participant Conversation",
					Description: fmt.Sprintf("Conversation involves %d participants, indicating rich interaction", len(partList)),
					Confidence:  0.8,
					Evidence:    []string{fmt.Sprintf("%d unique participants", len(partList))},
					Metadata:    map[string]interface{}{"participant_count": len(partList)},
				})
			}
		}
	}

	// Analyze conversation topics
	if topics, exists := data["topics"]; exists {
		if topicList, ok := topics.([]interface{}); ok && len(topicList) > 0 {
			insights = append(insights, Insight{
				Category:    "content_analysis",
				Title:       "Diverse Topic Coverage",
				Description: fmt.Sprintf("Conversation covers %d distinct topics", len(topicList)),
				Confidence:  0.7,
				Evidence:    []string{fmt.Sprintf("Topics: %v", topicList)},
				Metadata:    map[string]interface{}{"topic_count": len(topicList)},
			})
		}
	}

	return insights
}

func (cat *ConversationAnalysisTool) calculateConversationMetrics(data map[string]interface{}) map[string]interface{} {
	metrics := make(map[string]interface{})

	// Basic metrics
	if messages, exists := data["messages"]; exists {
		if msgList, ok := messages.([]interface{}); ok {
			metrics["total_messages"] = len(msgList)
			metrics["conversation_activity"] = "active"
		}
	}

	if participants, exists := data["participants"]; exists {
		if partList, ok := participants.([]interface{}); ok {
			metrics["total_participants"] = len(partList)
			if len(partList) > 0 {
				if msgCount, exists := metrics["total_messages"]; exists {
					if count, ok := msgCount.(int); ok {
						metrics["messages_per_participant"] = float64(count) / float64(len(partList))
					}
				}
			}
		}
	}

	if topics, exists := data["topics"]; exists {
		if topicList, ok := topics.([]interface{}); ok {
			metrics["topic_diversity"] = len(topicList)
		}
	}

	return metrics
}

func (cat *ConversationAnalysisTool) generateConversationSuggestions(data map[string]interface{}, insights []Insight) []Suggestion {
	suggestions := make([]Suggestion, 0)

	// Analyze insights to generate suggestions
	for _, insight := range insights {
		switch insight.Category {
		case "conversation_flow":
			if count, exists := insight.Metadata["message_count"]; exists {
				if msgCount, ok := count.(int); ok && msgCount < 5 {
					suggestions = append(suggestions, Suggestion{
						Title:       "Increase Conversation Length",
						Description: "Consider running the simulation longer to generate more natural conversation flow",
						Priority:    "medium",
						Category:    "simulation_tuning",
						Action:      "extend_simulation_duration",
						Metadata:    map[string]interface{}{"current_messages": msgCount},
					})
				}
			}
		case "participation":
			suggestions = append(suggestions, Suggestion{
				Title:       "Monitor Participation Balance",
				Description: "Ensure all agents are participating actively in the conversation",
				Priority:    "low",
				Category:    "agent_behavior",
				Action:      "check_agent_engagement",
				Metadata:    map[string]interface{}{"insight_source": insight.Title},
			})
		}
	}

	return suggestions
}

// Helper methods for PerformanceAnalysisTool

func (pat *PerformanceAnalysisTool) parsePerformanceData(data interface{}) (map[string]interface{}, error) {
	// Similar parsing logic for performance data
	switch d := data.(type) {
	case map[string]interface{}:
		return d, nil
	case string:
		var parsed map[string]interface{}
		if err := json.Unmarshal([]byte(d), &parsed); err != nil {
			return map[string]interface{}{
				"raw_data": d,
				"type":     "string",
			}, nil
		}
		return parsed, nil
	default:
		return map[string]interface{}{
			"data": d,
			"type": "unknown",
		}, nil
	}
}

func (pat *PerformanceAnalysisTool) identifyPerformanceIssues(data map[string]interface{}) []Insight {
	insights := make([]Insight, 0)

	// Check for memory usage patterns
	if memory, exists := data["memory"]; exists {
		if memMap, ok := memory.(map[string]interface{}); ok {
			if maxBytes, exists := memMap["max_bytes"]; exists {
				if max, ok := maxBytes.(int64); ok && max > 100*1024*1024 { // 100MB
					insights = append(insights, Insight{
						Category:    "memory_usage",
						Title:       "High Memory Usage Detected",
						Description: fmt.Sprintf("Peak memory usage reached %d MB", max/(1024*1024)),
						Confidence:  0.8,
						Evidence:    []string{fmt.Sprintf("Max memory: %d bytes", max)},
						Metadata:    map[string]interface{}{"max_memory_bytes": max},
					})
				}
			}
		}
	}

	// Check for CPU usage patterns
	if cpu, exists := data["cpu"]; exists {
		if cpuMap, ok := cpu.(map[string]interface{}); ok {
			if maxPercent, exists := cpuMap["max_percent"]; exists {
				if max, ok := maxPercent.(float64); ok && max > 80 {
					insights = append(insights, Insight{
						Category:    "cpu_usage",
						Title:       "High CPU Usage Detected",
						Description: fmt.Sprintf("Peak CPU usage reached %.1f%%", max),
						Confidence:  0.8,
						Evidence:    []string{fmt.Sprintf("Max CPU: %.1f%%", max)},
						Metadata:    map[string]interface{}{"max_cpu_percent": max},
					})
				}
			}
		}
	}

	return insights
}

func (pat *PerformanceAnalysisTool) calculatePerformanceMetrics(data map[string]interface{}) map[string]interface{} {
	metrics := make(map[string]interface{})

	// Extract performance metrics
	if duration, exists := data["duration"]; exists {
		metrics["total_duration"] = duration
	}

	if sampleCount, exists := data["sample_count"]; exists {
		metrics["sample_count"] = sampleCount
	}

	// Calculate efficiency metrics
	if memory, exists := data["memory"]; exists {
		if memMap, ok := memory.(map[string]interface{}); ok {
			if avg, exists := memMap["average_bytes"]; exists {
				metrics["average_memory_usage"] = avg
			}
		}
	}

	return metrics
}

func (pat *PerformanceAnalysisTool) generateOptimizationSuggestions(data map[string]interface{}, insights []Insight) []Suggestion {
	suggestions := make([]Suggestion, 0)

	for _, insight := range insights {
		switch insight.Category {
		case "memory_usage":
			suggestions = append(suggestions, Suggestion{
				Title:       "Optimize Memory Usage",
				Description: "Consider implementing memory pooling or reducing agent state complexity",
				Priority:    "high",
				Category:    "optimization",
				Action:      "reduce_memory_footprint",
				Metadata:    map[string]interface{}{"insight_source": insight.Title},
			})
		case "cpu_usage":
			suggestions = append(suggestions, Suggestion{
				Title:       "Optimize CPU Usage",
				Description: "Consider reducing simulation frequency or optimizing agent decision algorithms",
				Priority:    "medium",
				Category:    "optimization",
				Action:      "optimize_cpu_usage",
				Metadata:    map[string]interface{}{"insight_source": insight.Title},
			})
		}
	}

	return suggestions
}

// Helper methods for DebugTool

func (dt *DebugTool) parseSimulationData(data interface{}) (map[string]interface{}, error) {
	// Similar parsing logic for simulation debug data
	switch d := data.(type) {
	case map[string]interface{}:
		return d, nil
	case string:
		var parsed map[string]interface{}
		if err := json.Unmarshal([]byte(d), &parsed); err != nil {
			return map[string]interface{}{
				"raw_data": d,
				"type":     "string",
			}, nil
		}
		return parsed, nil
	default:
		return map[string]interface{}{
			"data": d,
			"type": "unknown",
		}, nil
	}
}

func (dt *DebugTool) identifySimulationIssues(data map[string]interface{}) []Insight {
	insights := make([]Insight, 0)

	// Check for simulation errors
	if errors, exists := data["errors"]; exists {
		if errorList, ok := errors.([]interface{}); ok && len(errorList) > 0 {
			insights = append(insights, Insight{
				Category:    "errors",
				Title:       "Simulation Errors Detected",
				Description: fmt.Sprintf("Found %d errors during simulation", len(errorList)),
				Confidence:  1.0,
				Evidence:    []string{fmt.Sprintf("%d errors logged", len(errorList))},
				Metadata:    map[string]interface{}{"error_count": len(errorList)},
			})
		}
	}

	// Check for agent state issues
	if agents, exists := data["agents"]; exists {
		if agentList, ok := agents.([]interface{}); ok {
			inactiveAgents := 0
			for _, agent := range agentList {
				if agentMap, ok := agent.(map[string]interface{}); ok {
					if active, exists := agentMap["active"]; exists {
						if isActive, ok := active.(bool); ok && !isActive {
							inactiveAgents++
						}
					}
				}
			}

			if inactiveAgents > 0 {
				insights = append(insights, Insight{
					Category:    "agent_state",
					Title:       "Inactive Agents Detected",
					Description: fmt.Sprintf("%d out of %d agents are inactive", inactiveAgents, len(agentList)),
					Confidence:  0.9,
					Evidence:    []string{fmt.Sprintf("%d inactive agents", inactiveAgents)},
					Metadata:    map[string]interface{}{"inactive_count": inactiveAgents},
				})
			}
		}
	}

	return insights
}

func (dt *DebugTool) calculateDebugMetrics(data map[string]interface{}) map[string]interface{} {
	metrics := make(map[string]interface{})

	if errors, exists := data["errors"]; exists {
		if errorList, ok := errors.([]interface{}); ok {
			metrics["error_count"] = len(errorList)
		}
	}

	if agents, exists := data["agents"]; exists {
		if agentList, ok := agents.([]interface{}); ok {
			metrics["total_agents"] = len(agentList)
		}
	}

	return metrics
}

func (dt *DebugTool) generateDebugSuggestions(data map[string]interface{}, insights []Insight) []Suggestion {
	suggestions := make([]Suggestion, 0)

	for _, insight := range insights {
		switch insight.Category {
		case "errors":
			suggestions = append(suggestions, Suggestion{
				Title:       "Investigate Simulation Errors",
				Description: "Review error logs and fix issues causing simulation failures",
				Priority:    "high",
				Category:    "debugging",
				Action:      "review_error_logs",
				Metadata:    map[string]interface{}{"insight_source": insight.Title},
			})
		case "agent_state":
			suggestions = append(suggestions, Suggestion{
				Title:       "Activate Inactive Agents",
				Description: "Check agent configuration and ensure all agents are properly initialized",
				Priority:    "medium",
				Category:    "debugging",
				Action:      "check_agent_initialization",
				Metadata:    map[string]interface{}{"insight_source": insight.Title},
			})
		}
	}

	return suggestions
}

// ToolRegistry manages multiple analysis tools
type ToolRegistry struct {
	tools map[ToolType]Tool
}

// NewToolRegistry creates a new tool registry with default tools
func NewToolRegistry() *ToolRegistry {
	registry := &ToolRegistry{
		tools: make(map[ToolType]Tool),
	}

	// Register default tools
	registry.RegisterTool(ConversationAnalyzer, NewConversationAnalysisTool())
	registry.RegisterTool(PerformanceAnalyzer, NewPerformanceAnalysisTool())
	registry.RegisterTool(SimulationDebugger, NewDebugTool())

	return registry
}

// RegisterTool registers a tool for a specific type
func (tr *ToolRegistry) RegisterTool(toolType ToolType, tool Tool) {
	tr.tools[toolType] = tool
}

// GetTool returns a tool for the specified type
func (tr *ToolRegistry) GetTool(toolType ToolType) (Tool, error) {
	tool, exists := tr.tools[toolType]
	if !exists {
		return nil, fmt.Errorf("no tool registered for type: %s", toolType)
	}
	return tool, nil
}

// ListTools returns all registered tools
func (tr *ToolRegistry) ListTools() map[ToolType]Tool {
	return tr.tools
}

// AnalyzeWith performs analysis using the specified tool type
func (tr *ToolRegistry) AnalyzeWith(ctx context.Context, toolType ToolType, req *AnalysisRequest) (*AnalysisResult, error) {
	tool, err := tr.GetTool(toolType)
	if err != nil {
		return nil, err
	}

	// Set the type in the request if not already set
	if req.Type == "" {
		req.Type = toolType
	}

	return tool.Analyze(ctx, req)
}

// GenerateReport creates a comprehensive analysis report
func (tr *ToolRegistry) GenerateReport(ctx context.Context, data interface{}, options map[string]interface{}) (*ComprehensiveReport, error) {
	report := &ComprehensiveReport{
		Timestamp: time.Now(),
		Sections:  make(map[string]*AnalysisResult),
		Summary:   make(map[string]interface{}),
		Metadata:  make(map[string]interface{}),
	}

	// Run analysis with each available tool
	for toolType, tool := range tr.tools {
		req := &AnalysisRequest{
			Type:     toolType,
			Data:     data,
			Options:  options,
			Metadata: map[string]interface{}{"report_generation": true},
		}

		result, err := tool.Analyze(ctx, req)
		if err != nil {
			// Log error but continue with other tools
			report.Metadata[fmt.Sprintf("%s_error", toolType)] = err.Error()
			continue
		}

		report.Sections[string(toolType)] = result
	}

	// Generate overall summary
	report.Summary = tr.generateReportSummary(report.Sections)

	return report, nil
}

// ComprehensiveReport represents a multi-tool analysis report
type ComprehensiveReport struct {
	Timestamp time.Time                  `json:"timestamp"`
	Sections  map[string]*AnalysisResult `json:"sections"`
	Summary   map[string]interface{}     `json:"summary"`
	Metadata  map[string]interface{}     `json:"metadata"`
}

// generateReportSummary creates an overall summary from all analysis results
func (tr *ToolRegistry) generateReportSummary(sections map[string]*AnalysisResult) map[string]interface{} {
	summary := make(map[string]interface{})

	totalInsights := 0
	totalSuggestions := 0
	categories := make(map[string]int)
	priorities := make(map[string]int)

	for sectionName, result := range sections {
		totalInsights += len(result.Insights)
		totalSuggestions += len(result.Suggestions)

		// Count insight categories
		for _, insight := range result.Insights {
			categories[insight.Category]++
		}

		// Count suggestion priorities
		for _, suggestion := range result.Suggestions {
			priorities[suggestion.Priority]++
		}

		// Include section-specific metrics
		summary[fmt.Sprintf("%s_insights", sectionName)] = len(result.Insights)
		summary[fmt.Sprintf("%s_suggestions", sectionName)] = len(result.Suggestions)
	}

	summary["total_insights"] = totalInsights
	summary["total_suggestions"] = totalSuggestions
	summary["insight_categories"] = categories
	summary["suggestion_priorities"] = priorities
	summary["sections_analyzed"] = len(sections)

	return summary
}
