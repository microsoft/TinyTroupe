// Package enrichment provides data enrichment capabilities for TinyTroupe simulations.
// This module handles data augmentation, context enhancement, and background knowledge integration.
package enrichment

import (
	"context"
	"fmt"
	"strings"
	"time"
)

// EnrichmentType represents different types of enrichment operations
type EnrichmentType string

const (
	ContextEnrichment     EnrichmentType = "context"
	TemporalEnrichment    EnrichmentType = "temporal"
	PersonalityEnrichment EnrichmentType = "personality"
	BackgroundEnrichment  EnrichmentType = "background"
)

// EnrichmentRequest represents a request to enrich some data
type EnrichmentRequest struct {
	Type     EnrichmentType         `json:"type"`
	Data     interface{}            `json:"data"`
	Context  map[string]interface{} `json:"context,omitempty"`
	AgentID  string                 `json:"agent_id,omitempty"`
	Metadata map[string]interface{} `json:"metadata,omitempty"`
}

// EnrichmentResult represents the result of an enrichment operation
type EnrichmentResult struct {
	OriginalData interface{}            `json:"original_data"`
	EnrichedData interface{}            `json:"enriched_data"`
	Additions    map[string]interface{} `json:"additions"`
	Type         EnrichmentType         `json:"type"`
	Timestamp    time.Time              `json:"timestamp"`
	Metadata     map[string]interface{} `json:"metadata,omitempty"`
}

// Enricher interface defines enrichment capabilities
type Enricher interface {
	// Enrich enhances the provided data with additional context
	Enrich(ctx context.Context, req *EnrichmentRequest) (*EnrichmentResult, error)

	// GetSupportedTypes returns the enrichment types this enricher supports
	GetSupportedTypes() []EnrichmentType
}

// ContextEnricher enriches data with contextual information
type ContextEnricher struct {
	knowledgeBase map[string]interface{}
}

// NewContextEnricher creates a new context enricher
func NewContextEnricher() *ContextEnricher {
	return &ContextEnricher{
		knowledgeBase: make(map[string]interface{}),
	}
}

// Enrich implements the Enricher interface for context enrichment
func (ce *ContextEnricher) Enrich(ctx context.Context, req *EnrichmentRequest) (*EnrichmentResult, error) {
	if req == nil {
		return nil, fmt.Errorf("enrichment request cannot be nil")
	}

	result := &EnrichmentResult{
		OriginalData: req.Data,
		Type:         req.Type,
		Timestamp:    time.Now(),
		Additions:    make(map[string]interface{}),
		Metadata:     make(map[string]interface{}),
	}

	switch req.Type {
	case ContextEnrichment:
		enriched, additions := ce.enrichContext(req.Data, req.Context)
		result.EnrichedData = enriched
		result.Additions = additions

	case TemporalEnrichment:
		enriched, additions := ce.enrichTemporal(req.Data, req.Context)
		result.EnrichedData = enriched
		result.Additions = additions

	case PersonalityEnrichment:
		enriched, additions := ce.enrichPersonality(req.Data, req.Context)
		result.EnrichedData = enriched
		result.Additions = additions

	case BackgroundEnrichment:
		enriched, additions := ce.enrichBackground(req.Data, req.Context)
		result.EnrichedData = enriched
		result.Additions = additions

	default:
		result.EnrichedData = req.Data
	}

	if req.AgentID != "" {
		result.Metadata["agent_id"] = req.AgentID
	}

	return result, nil
}

// GetSupportedTypes returns the enrichment types this enricher supports
func (ce *ContextEnricher) GetSupportedTypes() []EnrichmentType {
	return []EnrichmentType{
		ContextEnrichment,
		TemporalEnrichment,
		PersonalityEnrichment,
		BackgroundEnrichment,
	}
}

// enrichContext adds contextual information to data
func (ce *ContextEnricher) enrichContext(data interface{}, context map[string]interface{}) (interface{}, map[string]interface{}) {
	additions := make(map[string]interface{})

	// If data is a string (like a conversation message), enhance it with context
	if text, ok := data.(string); ok {
		enriched := text

		// Add location context if available
		if location, exists := context["location"]; exists {
			additions["inferred_location"] = location
			enriched = fmt.Sprintf("[Location: %v] %s", location, enriched)
		}

		// Add time context if available
		if timeCtx, exists := context["time"]; exists {
			additions["inferred_time"] = timeCtx
		}

		// Add emotional context if detectable
		if emotions := ce.detectEmotions(text); emotions != nil {
			additions["detected_emotions"] = emotions
		}

		return enriched, additions
	}

	return data, additions
}

// enrichTemporal adds temporal context and references
func (ce *ContextEnricher) enrichTemporal(data interface{}, context map[string]interface{}) (interface{}, map[string]interface{}) {
	additions := make(map[string]interface{})

	// Add timestamp information
	additions["enrichment_timestamp"] = time.Now()

	// Add day/time context
	now := time.Now()
	additions["time_of_day"] = getTimeOfDay(now)
	additions["day_of_week"] = now.Weekday().String()

	if text, ok := data.(string); ok {
		// Add temporal references if context suggests it
		enriched := text
		timeOfDay := getTimeOfDay(now)

		if strings.Contains(strings.ToLower(text), "morning") && timeOfDay != "morning" {
			additions["temporal_mismatch"] = "mentioned morning but it's " + timeOfDay
		}

		return enriched, additions
	}

	return data, additions
}

// enrichPersonality adds personality-based context and insights
func (ce *ContextEnricher) enrichPersonality(data interface{}, context map[string]interface{}) (interface{}, map[string]interface{}) {
	additions := make(map[string]interface{})

	if text, ok := data.(string); ok {
		// Analyze personality indicators in text
		indicators := ce.analyzePersonalityIndicators(text)
		if len(indicators) > 0 {
			additions["personality_indicators"] = indicators
		}

		// Add communication style analysis
		style := ce.analyzeCommunicationStyle(text)
		if style != "" {
			additions["communication_style"] = style
		}

		return text, additions
	}

	return data, additions
}

// enrichBackground adds background knowledge and context
func (ce *ContextEnricher) enrichBackground(data interface{}, context map[string]interface{}) (interface{}, map[string]interface{}) {
	additions := make(map[string]interface{})

	if text, ok := data.(string); ok {
		// Detect topics and add background context
		topics := ce.detectTopics(text)
		if len(topics) > 0 {
			additions["detected_topics"] = topics

			// Add background information for detected topics
			background := make(map[string]interface{})
			for _, topic := range topics {
				if info := ce.getBackgroundInfo(topic); info != "" {
					background[topic] = info
				}
			}
			if len(background) > 0 {
				additions["background_info"] = background
			}
		}

		return text, additions
	}

	return data, additions
}

// Helper functions for enrichment

func (ce *ContextEnricher) detectEmotions(text string) []string {
	emotions := []string{}
	lower := strings.ToLower(text)

	// Simple emotion detection based on keywords
	if strings.Contains(lower, "happy") || strings.Contains(lower, "joy") || strings.Contains(lower, "excited") {
		emotions = append(emotions, "positive")
	}
	if strings.Contains(lower, "sad") || strings.Contains(lower, "upset") || strings.Contains(lower, "disappointed") {
		emotions = append(emotions, "negative")
	}
	if strings.Contains(lower, "curious") || strings.Contains(lower, "interesting") || strings.Contains(lower, "wonder") {
		emotions = append(emotions, "curious")
	}

	return emotions
}

func getTimeOfDay(t time.Time) string {
	hour := t.Hour()
	switch {
	case hour >= 5 && hour < 12:
		return "morning"
	case hour >= 12 && hour < 17:
		return "afternoon"
	case hour >= 17 && hour < 21:
		return "evening"
	default:
		return "night"
	}
}

func (ce *ContextEnricher) analyzePersonalityIndicators(text string) []string {
	indicators := []string{}
	lower := strings.ToLower(text)

	// Simple personality trait detection
	if strings.Contains(lower, "i think") || strings.Contains(lower, "analysis") || strings.Contains(lower, "data") {
		indicators = append(indicators, "analytical")
	}
	if strings.Contains(lower, "team") || strings.Contains(lower, "together") || strings.Contains(lower, "collaboration") {
		indicators = append(indicators, "collaborative")
	}
	if strings.Contains(lower, "new") || strings.Contains(lower, "innovative") || strings.Contains(lower, "creative") {
		indicators = append(indicators, "creative")
	}

	return indicators
}

func (ce *ContextEnricher) analyzeCommunicationStyle(text string) string {
	if len(text) < 20 {
		return "concise"
	}
	if strings.Count(text, "!") >= 1 {
		return "enthusiastic"
	}
	if strings.Count(text, "?") > 1 {
		return "inquisitive"
	}
	if len(text) > 200 {
		return "detailed"
	}
	return "balanced"
}

func (ce *ContextEnricher) detectTopics(text string) []string {
	topics := []string{}
	lower := strings.ToLower(text)

	// Simple topic detection
	if strings.Contains(lower, "technology") || strings.Contains(lower, "software") || strings.Contains(lower, "programming") {
		topics = append(topics, "technology")
	}
	if strings.Contains(lower, "architecture") || strings.Contains(lower, "design") || strings.Contains(lower, "building") {
		topics = append(topics, "architecture")
	}
	if strings.Contains(lower, "music") || strings.Contains(lower, "piano") || strings.Contains(lower, "guitar") {
		topics = append(topics, "music")
	}
	if strings.Contains(lower, "travel") || strings.Contains(lower, "places") || strings.Contains(lower, "journey") {
		topics = append(topics, "travel")
	}

	return topics
}

func (ce *ContextEnricher) getBackgroundInfo(topic string) string {
	// Simple background knowledge base
	backgrounds := map[string]string{
		"technology":   "Technology encompasses software, hardware, and digital innovation",
		"architecture": "Architecture involves designing and planning buildings and spaces",
		"music":        "Music is an art form involving organized sound and rhythm",
		"travel":       "Travel involves moving between different locations for various purposes",
	}

	return backgrounds[topic]
}

// AddKnowledge allows adding knowledge to the enricher's knowledge base
func (ce *ContextEnricher) AddKnowledge(key string, value interface{}) {
	ce.knowledgeBase[key] = value
}

// GetKnowledge retrieves knowledge from the enricher's knowledge base
func (ce *ContextEnricher) GetKnowledge(key string) (interface{}, bool) {
	value, exists := ce.knowledgeBase[key]
	return value, exists
}
