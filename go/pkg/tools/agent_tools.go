package tools

import (
	"context"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"time"

	"github.com/atsentia/tinytroupe-go/pkg/config"
)

// AgentTool represents a tool that agents can use to perform actions
type AgentTool interface {
	// GetName returns the tool's name
	GetName() string
	
	// GetDescription returns what the tool does
	GetDescription() string
	
	// ProcessAction processes an agent action and returns success/failure
	ProcessAction(ctx context.Context, agent AgentInfo, action Action) (bool, error)
	
	// GetSupportedActions returns the action types this tool supports
	GetSupportedActions() []string
}

// AgentInfo represents basic agent information for tool usage
type AgentInfo struct {
	Name string `json:"name"`
	ID   string `json:"id,omitempty"`
}

// Action represents an action an agent wants to perform
type Action struct {
	Type    string                 `json:"type"`
	Content interface{}            `json:"content"`
	Target  string                 `json:"target,omitempty"`
	Options map[string]interface{} `json:"options,omitempty"`
}

// DocumentSpec represents a document creation specification
type DocumentSpec struct {
	Title   string      `json:"title"`
	Content interface{} `json:"content"`
	Author  string      `json:"author,omitempty"`
	Type    string      `json:"type,omitempty"` // "proposal", "report", "memo", etc.
}

// ExportFormat represents output format for documents
type ExportFormat string

const (
	FormatMarkdown ExportFormat = "md"
	FormatJSON     ExportFormat = "json"
	FormatText     ExportFormat = "txt"
)

// TinyWordProcessor implements document creation and management for agents
type TinyWordProcessor struct {
	name          string
	description   string
	outputDir     string
	enableEnrich  bool
	enableExport  bool
	supportedFormats []ExportFormat
}

// NewTinyWordProcessor creates a new word processor tool
func NewTinyWordProcessor(outputDir string) *TinyWordProcessor {
	if outputDir == "" {
		outputDir = "./documents"
	}
	
	return &TinyWordProcessor{
		name:        "wordprocessor",
		description: "A document creation tool that allows agents to write and export documents",
		outputDir:   outputDir,
		enableEnrich: true,
		enableExport: true,
		supportedFormats: []ExportFormat{FormatMarkdown, FormatJSON, FormatText},
	}
}

// GetName implements AgentTool interface
func (wp *TinyWordProcessor) GetName() string {
	return wp.name
}

// GetDescription implements AgentTool interface
func (wp *TinyWordProcessor) GetDescription() string {
	return wp.description
}

// GetSupportedActions implements AgentTool interface
func (wp *TinyWordProcessor) GetSupportedActions() []string {
	return []string{"WRITE_DOCUMENT", "CREATE_REPORT", "DRAFT_PROPOSAL"}
}

// ProcessAction implements AgentTool interface
func (wp *TinyWordProcessor) ProcessAction(ctx context.Context, agent AgentInfo, action Action) (bool, error) {
	switch action.Type {
	case "WRITE_DOCUMENT", "CREATE_REPORT", "DRAFT_PROPOSAL":
		return wp.writeDocument(ctx, agent, action)
	default:
		return false, fmt.Errorf("unsupported action type: %s", action.Type)
	}
}

// writeDocument processes document writing actions
func (wp *TinyWordProcessor) writeDocument(ctx context.Context, agent AgentInfo, action Action) (bool, error) {
	// Parse document specification from action content
	docSpec, err := wp.parseDocumentSpec(action.Content)
	if err != nil {
		return false, fmt.Errorf("failed to parse document specification: %w", err)
	}

	// Set default author if not specified
	if docSpec.Author == "" {
		docSpec.Author = agent.Name
	}

	// Enrich content if enabled
	if wp.enableEnrich {
		docSpec.Content = wp.enrichContent(docSpec.Content, docSpec.Type)
	}

	// Export document if enabled
	if wp.enableExport {
		err = wp.exportDocument(docSpec)
		if err != nil {
			return false, fmt.Errorf("failed to export document: %w", err)
		}
	}

	return true, nil
}

// parseDocumentSpec converts action content to DocumentSpec
func (wp *TinyWordProcessor) parseDocumentSpec(content interface{}) (*DocumentSpec, error) {
	switch v := content.(type) {
	case string:
		// Try to parse as JSON first
		var spec DocumentSpec
		if err := json.Unmarshal([]byte(v), &spec); err == nil {
			return &spec, nil
		}
		
		// If not JSON, treat as plain content
		return &DocumentSpec{
			Title:   "Untitled Document",
			Content: v,
			Type:    "document",
		}, nil
		
	case map[string]interface{}:
		// Convert map to DocumentSpec
		jsonBytes, err := json.Marshal(v)
		if err != nil {
			return nil, fmt.Errorf("failed to marshal content map: %w", err)
		}
		
		var spec DocumentSpec
		if err := json.Unmarshal(jsonBytes, &spec); err != nil {
			return nil, fmt.Errorf("failed to unmarshal to DocumentSpec: %w", err)
		}
		
		return &spec, nil
		
	case DocumentSpec:
		return &v, nil
		
	default:
		return nil, fmt.Errorf("unsupported content type: %T", content)
	}
}

// enrichContent expands and enhances document content
func (wp *TinyWordProcessor) enrichContent(content interface{}, docType string) string {
	if !wp.enableEnrich {
		return wp.contentToString(content)
	}

	// Convert content to string first
	contentStr := wp.contentToString(content)
	
	// Basic content enrichment - in a full implementation, this would use LLM
	enriched := contentStr
	
	// Add structure based on document type
	switch docType {
	case "proposal":
		if !strings.Contains(enriched, "## Executive Summary") {
			enriched = "## Executive Summary\n\n" + enriched
		}
		if !strings.Contains(enriched, "## Implementation Plan") {
			enriched += "\n\n## Implementation Plan\n\nDetailed implementation steps will be provided upon approval."
		}
		if !strings.Contains(enriched, "## Budget Considerations") {
			enriched += "\n\n## Budget Considerations\n\nCost analysis and budget allocation details to be determined."
		}
		
	case "report":
		if !strings.Contains(enriched, "## Overview") {
			enriched = "## Overview\n\n" + enriched
		}
		if !strings.Contains(enriched, "## Findings") {
			enriched += "\n\n## Findings\n\nKey insights and analysis results."
		}
		if !strings.Contains(enriched, "## Recommendations") {
			enriched += "\n\n## Recommendations\n\nActionable recommendations based on the analysis."
		}
		
	case "memo":
		if !strings.Contains(enriched, "**Subject:**") {
			enriched = "**Subject:** Important Update\n\n" + enriched
		}
		if !strings.Contains(enriched, "**Action Required:**") {
			enriched += "\n\n**Action Required:** Please review and provide feedback."
		}
	}
	
	// Add timestamp
	if !strings.Contains(enriched, "Generated on") {
		timestamp := time.Now().Format("January 2, 2006 at 3:04 PM")
		enriched += fmt.Sprintf("\n\n---\n*Generated on %s*", timestamp)
	}
	
	return enriched
}

// contentToString converts interface{} content to string
func (wp *TinyWordProcessor) contentToString(content interface{}) string {
	switch v := content.(type) {
	case string:
		return v
	case map[string]interface{}:
		// Convert structured content to formatted text
		var parts []string
		for key, value := range v {
			parts = append(parts, fmt.Sprintf("## %s\n\n%v", key, value))
		}
		return strings.Join(parts, "\n\n")
	case []interface{}:
		// Convert array to numbered list
		var parts []string
		for i, item := range v {
			parts = append(parts, fmt.Sprintf("%d. %v", i+1, item))
		}
		return strings.Join(parts, "\n")
	default:
		// Convert anything else to string
		return fmt.Sprintf("%v", v)
	}
}

// exportDocument saves the document in specified formats
func (wp *TinyWordProcessor) exportDocument(spec *DocumentSpec) error {
	// Ensure output directory exists
	if err := os.MkdirAll(wp.outputDir, 0755); err != nil {
		return fmt.Errorf("failed to create output directory: %w", err)
	}

	// Generate base filename
	baseFilename := wp.sanitizeFilename(spec.Title)
	if spec.Author != "" {
		baseFilename = fmt.Sprintf("%s.%s", baseFilename, wp.sanitizeFilename(spec.Author))
	}

	// Export in supported formats
	for _, format := range wp.supportedFormats {
		filename := fmt.Sprintf("%s.%s", baseFilename, string(format))
		filepath := filepath.Join(wp.outputDir, filename)
		
		var content []byte
		var err error
		
		switch format {
		case FormatMarkdown:
			content, err = wp.formatAsMarkdown(spec)
		case FormatJSON:
			content, err = wp.formatAsJSON(spec)
		case FormatText:
			content, err = wp.formatAsText(spec)
		default:
			continue
		}
		
		if err != nil {
			return fmt.Errorf("failed to format document as %s: %w", format, err)
		}
		
		if err := os.WriteFile(filepath, content, 0644); err != nil {
			return fmt.Errorf("failed to write %s file: %w", format, err)
		}
	}
	
	return nil
}

// formatAsMarkdown formats document as Markdown
func (wp *TinyWordProcessor) formatAsMarkdown(spec *DocumentSpec) ([]byte, error) {
	var content strings.Builder
	
	// Title
	content.WriteString(fmt.Sprintf("# %s\n\n", spec.Title))
	
	// Author and metadata
	if spec.Author != "" {
		content.WriteString(fmt.Sprintf("**Author:** %s\n", spec.Author))
	}
	if spec.Type != "" {
		content.WriteString(fmt.Sprintf("**Type:** %s\n", spec.Type))
	}
	content.WriteString(fmt.Sprintf("**Created:** %s\n\n", time.Now().Format("2006-01-02 15:04:05")))
	
	// Main content
	contentStr := wp.contentToString(spec.Content)
	content.WriteString(contentStr)
	
	return []byte(content.String()), nil
}

// formatAsJSON formats document as JSON
func (wp *TinyWordProcessor) formatAsJSON(spec *DocumentSpec) ([]byte, error) {
	contentStr := wp.contentToString(spec.Content)
	doc := map[string]interface{}{
		"title":     spec.Title,
		"content":   spec.Content,
		"content_text": contentStr,
		"author":    spec.Author,
		"type":      spec.Type,
		"created":   time.Now().Format(time.RFC3339),
		"word_count": len(strings.Fields(contentStr)),
	}
	
	return json.MarshalIndent(doc, "", "  ")
}

// formatAsText formats document as plain text
func (wp *TinyWordProcessor) formatAsText(spec *DocumentSpec) ([]byte, error) {
	var content strings.Builder
	
	// Header
	content.WriteString(strings.ToUpper(spec.Title))
	content.WriteString("\n")
	content.WriteString(strings.Repeat("=", len(spec.Title)))
	content.WriteString("\n\n")
	
	// Metadata
	if spec.Author != "" {
		content.WriteString(fmt.Sprintf("Author: %s\n", spec.Author))
	}
	if spec.Type != "" {
		content.WriteString(fmt.Sprintf("Type: %s\n", spec.Type))
	}
	content.WriteString(fmt.Sprintf("Created: %s\n\n", time.Now().Format("2006-01-02 15:04:05")))
	
	// Content (strip markdown formatting for plain text)
	contentStr := wp.contentToString(spec.Content)
	plainContent := strings.ReplaceAll(contentStr, "##", "")
	plainContent = strings.ReplaceAll(plainContent, "**", "")
	plainContent = strings.ReplaceAll(plainContent, "*", "")
	content.WriteString(plainContent)
	
	return []byte(content.String()), nil
}

// sanitizeFilename removes invalid characters from filenames
func (wp *TinyWordProcessor) sanitizeFilename(filename string) string {
	// Replace invalid characters
	invalid := []string{"/", "\\", ":", "*", "?", "\"", "<", ">", "|"}
	sanitized := filename
	
	for _, char := range invalid {
		sanitized = strings.ReplaceAll(sanitized, char, "_")
	}
	
	// Replace spaces with underscores
	sanitized = strings.ReplaceAll(sanitized, " ", "_")
	
	// Limit length
	if len(sanitized) > 100 {
		sanitized = sanitized[:100]
	}
	
	return sanitized
}

// AgentToolRegistry manages agent tools
type AgentToolRegistry struct {
	tools map[string]AgentTool
	config *config.Config
}

// NewAgentToolRegistry creates a new agent tool registry
func NewAgentToolRegistry(cfg *config.Config) *AgentToolRegistry {
	registry := &AgentToolRegistry{
		tools:  make(map[string]AgentTool),
		config: cfg,
	}
	
	// Register default tools
	registry.RegisterTool(NewTinyWordProcessor("./documents"))
	registry.RegisterTool(NewAgentDataExporter("./exports"))
	
	return registry
}

// RegisterTool registers an agent tool
func (atr *AgentToolRegistry) RegisterTool(tool AgentTool) {
	atr.tools[tool.GetName()] = tool
}

// GetTool returns a tool by name
func (atr *AgentToolRegistry) GetTool(name string) (AgentTool, error) {
	tool, exists := atr.tools[name]
	if !exists {
		return nil, fmt.Errorf("tool not found: %s", name)
	}
	return tool, nil
}

// ProcessAction processes an action with the appropriate tool
func (atr *AgentToolRegistry) ProcessAction(ctx context.Context, agent AgentInfo, action Action, toolName string) (bool, error) {
	tool, err := atr.GetTool(toolName)
	if err != nil {
		return false, err
	}
	
	return tool.ProcessAction(ctx, agent, action)
}

// ListTools returns all available tools
func (atr *AgentToolRegistry) ListTools() map[string]AgentTool {
	return atr.tools
}

// GetToolForAction finds the appropriate tool for an action type
func (atr *AgentToolRegistry) GetToolForAction(actionType string) (AgentTool, error) {
	for _, tool := range atr.tools {
		for _, supportedAction := range tool.GetSupportedActions() {
			if supportedAction == actionType {
				return tool, nil
			}
		}
	}
	
	return nil, fmt.Errorf("no tool found for action type: %s", actionType)
}

// AgentDataExporter implements data export functionality for agents
type AgentDataExporter struct {
	name        string
	description string
	outputDir   string
}

// NewAgentDataExporter creates a new data exporter tool
func NewAgentDataExporter(outputDir string) *AgentDataExporter {
	if outputDir == "" {
		outputDir = "./exports"
	}
	
	return &AgentDataExporter{
		name:        "dataexporter",
		description: "Export simulation data, insights, and results to various formats",
		outputDir:   outputDir,
	}
}

// GetName implements AgentTool interface
func (de *AgentDataExporter) GetName() string {
	return de.name
}

// GetDescription implements AgentTool interface
func (de *AgentDataExporter) GetDescription() string {
	return de.description
}

// GetSupportedActions implements AgentTool interface
func (de *AgentDataExporter) GetSupportedActions() []string {
	return []string{"EXPORT_DATA", "SAVE_INSIGHTS", "GENERATE_REPORT"}
}

// ProcessAction implements AgentTool interface
func (de *AgentDataExporter) ProcessAction(ctx context.Context, agent AgentInfo, action Action) (bool, error) {
	switch action.Type {
	case "EXPORT_DATA", "SAVE_INSIGHTS", "GENERATE_REPORT":
		return de.exportData(ctx, agent, action)
	default:
		return false, fmt.Errorf("unsupported action type: %s", action.Type)
	}
}

// ExportSpec represents data export specification
type ExportSpec struct {
	Data     interface{} `json:"data"`
	Filename string      `json:"filename"`
	Format   string      `json:"format"` // "json", "csv", "txt"
	Title    string      `json:"title,omitempty"`
	Summary  string      `json:"summary,omitempty"`
}

// exportData processes data export actions
func (de *AgentDataExporter) exportData(ctx context.Context, agent AgentInfo, action Action) (bool, error) {
	// Parse export specification
	exportSpec, err := de.parseExportSpec(action.Content)
	if err != nil {
		return false, fmt.Errorf("failed to parse export specification: %w", err)
	}

	// Set default filename if not specified
	if exportSpec.Filename == "" {
		timestamp := time.Now().Format("2006-01-02_15-04-05")
		exportSpec.Filename = fmt.Sprintf("%s_export_%s", agent.Name, timestamp)
	}

	// Export data
	err = de.performExport(exportSpec, agent)
	if err != nil {
		return false, fmt.Errorf("failed to export data: %w", err)
	}

	return true, nil
}

// parseExportSpec converts action content to ExportSpec
func (de *AgentDataExporter) parseExportSpec(content interface{}) (*ExportSpec, error) {
	switch v := content.(type) {
	case string:
		// Try to parse as JSON first
		var spec ExportSpec
		if err := json.Unmarshal([]byte(v), &spec); err == nil {
			return &spec, nil
		}
		
		// If not JSON, treat as data to export
		return &ExportSpec{
			Data:   v,
			Format: "txt",
		}, nil
		
	case map[string]interface{}:
		// Convert map to ExportSpec
		jsonBytes, err := json.Marshal(v)
		if err != nil {
			return nil, fmt.Errorf("failed to marshal content map: %w", err)
		}
		
		var spec ExportSpec
		if err := json.Unmarshal(jsonBytes, &spec); err != nil {
			// If conversion fails, use the map as data
			return &ExportSpec{
				Data:   v,
				Format: "json",
			}, nil
		}
		
		return &spec, nil
		
	case ExportSpec:
		return &v, nil
		
	default:
		// Export any other data type as JSON
		return &ExportSpec{
			Data:   v,
			Format: "json",
		}, nil
	}
}

// performExport saves data in the specified format
func (de *AgentDataExporter) performExport(spec *ExportSpec, agent AgentInfo) error {
	// Ensure output directory exists
	if err := os.MkdirAll(de.outputDir, 0755); err != nil {
		return fmt.Errorf("failed to create output directory: %w", err)
	}

	// Normalize format to lowercase
	format := strings.ToLower(spec.Format)
	
	// Generate filename with extension
	filename := spec.Filename
	if !strings.Contains(filename, ".") {
		filename = fmt.Sprintf("%s.%s", filename, format)
	}
	
	filepath := filepath.Join(de.outputDir, filename)
	
	// Format and write data
	var content []byte
	var err error
	
	switch format {
	case "json":
		content, err = de.formatAsJSON(spec, agent)
	case "csv":
		content, err = de.formatAsCSV(spec, agent)
	case "txt", "text":
		content, err = de.formatAsText(spec, agent)
	default:
		return fmt.Errorf("unsupported export format: %s (supported: json, csv, txt)", spec.Format)
	}
	
	if err != nil {
		return fmt.Errorf("failed to format data: %w", err)
	}
	
	if err := os.WriteFile(filepath, content, 0644); err != nil {
		return fmt.Errorf("failed to write file: %w", err)
	}
	
	return nil
}

// formatAsJSON formats export data as JSON
func (de *AgentDataExporter) formatAsJSON(spec *ExportSpec, agent AgentInfo) ([]byte, error) {
	export := map[string]interface{}{
		"metadata": map[string]interface{}{
			"exported_by": agent.Name,
			"exported_at": time.Now().Format(time.RFC3339),
			"title":       spec.Title,
			"summary":     spec.Summary,
		},
		"data": spec.Data,
	}
	
	return json.MarshalIndent(export, "", "  ")
}

// formatAsCSV formats export data as CSV (basic implementation)
func (de *AgentDataExporter) formatAsCSV(spec *ExportSpec, agent AgentInfo) ([]byte, error) {
	var content strings.Builder
	
	// Header
	content.WriteString(fmt.Sprintf("# Exported by: %s\n", agent.Name))
	content.WriteString(fmt.Sprintf("# Exported at: %s\n", time.Now().Format(time.RFC3339)))
	if spec.Title != "" {
		content.WriteString(fmt.Sprintf("# Title: %s\n", spec.Title))
	}
	if spec.Summary != "" {
		content.WriteString(fmt.Sprintf("# Summary: %s\n", spec.Summary))
	}
	content.WriteString("\n")
	
	// Convert data to CSV format (simplified)
	switch data := spec.Data.(type) {
	case []interface{}:
		// Array of data
		for i, item := range data {
			if itemMap, ok := item.(map[string]interface{}); ok {
				if i == 0 {
					// Write headers
					var headers []string
					for key := range itemMap {
						headers = append(headers, key)
					}
					content.WriteString(strings.Join(headers, ",") + "\n")
				}
				
				// Write values
				var values []string
				for _, key := range []string{} { // Would need to maintain order
					if val, exists := itemMap[key]; exists {
						values = append(values, fmt.Sprintf("%v", val))
					}
				}
				content.WriteString(strings.Join(values, ",") + "\n")
			} else {
				content.WriteString(fmt.Sprintf("%v\n", item))
			}
		}
	case map[string]interface{}:
		// Key-value pairs
		content.WriteString("Key,Value\n")
		for key, value := range data {
			content.WriteString(fmt.Sprintf("%s,%v\n", key, value))
		}
	default:
		// Fallback to string representation
		content.WriteString("Data\n")
		content.WriteString(fmt.Sprintf("%v\n", data))
	}
	
	return []byte(content.String()), nil
}

// formatAsText formats export data as plain text
func (de *AgentDataExporter) formatAsText(spec *ExportSpec, agent AgentInfo) ([]byte, error) {
	var content strings.Builder
	
	// Header
	if spec.Title != "" {
		content.WriteString(strings.ToUpper(spec.Title))
		content.WriteString("\n")
		content.WriteString(strings.Repeat("=", len(spec.Title)))
		content.WriteString("\n\n")
	}
	
	// Metadata
	content.WriteString(fmt.Sprintf("Exported by: %s\n", agent.Name))
	content.WriteString(fmt.Sprintf("Exported at: %s\n", time.Now().Format("2006-01-02 15:04:05")))
	
	if spec.Summary != "" {
		content.WriteString(fmt.Sprintf("Summary: %s\n", spec.Summary))
	}
	content.WriteString("\n")
	
	// Data content
	content.WriteString("DATA:\n")
	content.WriteString("-----\n")
	
	// Format data based on type
	switch data := spec.Data.(type) {
	case string:
		content.WriteString(data)
	case map[string]interface{}:
		for key, value := range data {
			content.WriteString(fmt.Sprintf("%s: %v\n", key, value))
		}
	case []interface{}:
		for i, item := range data {
			content.WriteString(fmt.Sprintf("%d. %v\n", i+1, item))
		}
	default:
		content.WriteString(fmt.Sprintf("%v", data))
	}
	
	return []byte(content.String()), nil
}