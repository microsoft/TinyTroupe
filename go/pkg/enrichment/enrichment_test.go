package enrichment

import (
	"context"
	"testing"
	"time"
)

func TestContextEnricherCreation(t *testing.T) {
	enricher := NewContextEnricher()
	if enricher == nil {
		t.Fatal("NewContextEnricher returned nil")
	}

	supportedTypes := enricher.GetSupportedTypes()
	if len(supportedTypes) != 4 {
		t.Errorf("Expected 4 supported types, got %d", len(supportedTypes))
	}

	expectedTypes := []EnrichmentType{
		ContextEnrichment,
		TemporalEnrichment,
		PersonalityEnrichment,
		BackgroundEnrichment,
	}

	for _, expectedType := range expectedTypes {
		found := false
		for _, supportedType := range supportedTypes {
			if supportedType == expectedType {
				found = true
				break
			}
		}
		if !found {
			t.Errorf("Expected type %s not found in supported types", expectedType)
		}
	}
}

func TestEnrichmentRequestValidation(t *testing.T) {
	enricher := NewContextEnricher()
	ctx := context.Background()

	// Test nil request
	result, err := enricher.Enrich(ctx, nil)
	if err == nil {
		t.Error("Expected error for nil request")
	}
	if result != nil {
		t.Error("Expected nil result for nil request")
	}
}

func TestContextEnrichment(t *testing.T) {
	enricher := NewContextEnricher()
	ctx := context.Background()

	req := &EnrichmentRequest{
		Type: ContextEnrichment,
		Data: "Hello, how are you doing today?",
		Context: map[string]interface{}{
			"location": "San Francisco",
			"time":     "morning",
		},
		AgentID: "test-agent",
	}

	result, err := enricher.Enrich(ctx, req)
	if err != nil {
		t.Fatalf("Enrichment failed: %v", err)
	}

	if result == nil {
		t.Fatal("Result is nil")
	}

	// Check basic result properties
	if result.Type != ContextEnrichment {
		t.Errorf("Expected type %s, got %s", ContextEnrichment, result.Type)
	}

	if result.OriginalData != req.Data {
		t.Error("Original data doesn't match input")
	}

	// Check that enriched data contains location context
	enrichedText, ok := result.EnrichedData.(string)
	if !ok {
		t.Fatal("Enriched data is not a string")
	}

	if !contains(enrichedText, "San Francisco") {
		t.Error("Enriched text doesn't contain location context")
	}

	// Check additions
	if result.Additions["inferred_location"] != "San Francisco" {
		t.Error("Location not added to additions")
	}

	if result.Additions["inferred_time"] != "morning" {
		t.Error("Time not added to additions")
	}

	// Check metadata
	if result.Metadata["agent_id"] != "test-agent" {
		t.Error("Agent ID not added to metadata")
	}
}

func TestTemporalEnrichment(t *testing.T) {
	enricher := NewContextEnricher()
	ctx := context.Background()

	req := &EnrichmentRequest{
		Type:    TemporalEnrichment,
		Data:    "Good morning everyone!",
		Context: map[string]interface{}{},
	}

	result, err := enricher.Enrich(ctx, req)
	if err != nil {
		t.Fatalf("Temporal enrichment failed: %v", err)
	}

	// Check that temporal information was added
	if result.Additions["enrichment_timestamp"] == nil {
		t.Error("Enrichment timestamp not added")
	}

	if result.Additions["time_of_day"] == nil {
		t.Error("Time of day not added")
	}

	if result.Additions["day_of_week"] == nil {
		t.Error("Day of week not added")
	}

	// Verify timestamp is recent
	timestamp, ok := result.Additions["enrichment_timestamp"].(time.Time)
	if !ok {
		t.Error("Enrichment timestamp is not a time.Time")
	} else if time.Since(timestamp) > time.Minute {
		t.Error("Enrichment timestamp is not recent")
	}
}

func TestPersonalityEnrichment(t *testing.T) {
	enricher := NewContextEnricher()
	ctx := context.Background()

	testCases := []struct {
		text               string
		expectedIndicators []string
		expectedStyle      string
	}{
		{
			text:               "I think the data analysis shows interesting patterns",
			expectedIndicators: []string{"analytical"},
			expectedStyle:      "balanced",
		},
		{
			text:               "Let's work together as a team on this creative project!",
			expectedIndicators: []string{"collaborative", "creative"},
			expectedStyle:      "enthusiastic",
		},
		{
			text:               "Ok",
			expectedIndicators: nil,
			expectedStyle:      "concise",
		},
	}

	for _, tc := range testCases {
		req := &EnrichmentRequest{
			Type:    PersonalityEnrichment,
			Data:    tc.text,
			Context: map[string]interface{}{},
		}

		result, err := enricher.Enrich(ctx, req)
		if err != nil {
			t.Fatalf("Personality enrichment failed for '%s': %v", tc.text, err)
		}

		// Check communication style
		if style, exists := result.Additions["communication_style"]; exists {
			if style != tc.expectedStyle {
				t.Errorf("For text '%s', expected style '%s', got '%s'", tc.text, tc.expectedStyle, style)
			}
		}

		// Check personality indicators
		if tc.expectedIndicators != nil {
			indicators, exists := result.Additions["personality_indicators"]
			if !exists {
				t.Errorf("For text '%s', expected personality indicators but none found", tc.text)
			} else {
				indicatorList, ok := indicators.([]string)
				if !ok {
					t.Errorf("Personality indicators is not a string slice")
				} else {
					for _, expected := range tc.expectedIndicators {
						found := false
						for _, actual := range indicatorList {
							if actual == expected {
								found = true
								break
							}
						}
						if !found {
							t.Errorf("For text '%s', expected indicator '%s' not found", tc.text, expected)
						}
					}
				}
			}
		}
	}
}

func TestBackgroundEnrichment(t *testing.T) {
	enricher := NewContextEnricher()
	ctx := context.Background()

	req := &EnrichmentRequest{
		Type:    BackgroundEnrichment,
		Data:    "I love programming and software technology, and I also enjoy playing music",
		Context: map[string]interface{}{},
	}

	result, err := enricher.Enrich(ctx, req)
	if err != nil {
		t.Fatalf("Background enrichment failed: %v", err)
	}

	// Check that topics were detected
	topics, exists := result.Additions["detected_topics"]
	if !exists {
		t.Error("No topics detected")
	} else {
		topicList, ok := topics.([]string)
		if !ok {
			t.Error("Topics is not a string slice")
		} else {
			expectedTopics := []string{"technology", "music"}
			for _, expected := range expectedTopics {
				found := false
				for _, actual := range topicList {
					if actual == expected {
						found = true
						break
					}
				}
				if !found {
					t.Errorf("Expected topic '%s' not found", expected)
				}
			}
		}
	}

	// Check that background information was added
	backgroundInfo, exists := result.Additions["background_info"]
	if !exists {
		t.Error("No background information added")
	} else {
		infoMap, ok := backgroundInfo.(map[string]interface{})
		if !ok {
			t.Error("Background info is not a map")
		} else {
			if _, exists := infoMap["technology"]; !exists {
				t.Error("Technology background info not found")
			}
			if _, exists := infoMap["music"]; !exists {
				t.Error("Music background info not found")
			}
		}
	}
}

func TestEmotionDetection(t *testing.T) {
	enricher := NewContextEnricher()

	testCases := []struct {
		text             string
		expectedEmotions []string
	}{
		{
			text:             "I'm so happy and excited about this!",
			expectedEmotions: []string{"positive"},
		},
		{
			text:             "I'm sad and disappointed about the results",
			expectedEmotions: []string{"negative"},
		},
		{
			text:             "I'm curious about this interesting phenomenon",
			expectedEmotions: []string{"curious"},
		},
		{
			text:             "I'm happy but curious about this interesting development",
			expectedEmotions: []string{"positive", "curious"},
		},
		{
			text:             "This is a neutral statement",
			expectedEmotions: []string{},
		},
	}

	for _, tc := range testCases {
		emotions := enricher.detectEmotions(tc.text)

		if len(emotions) != len(tc.expectedEmotions) {
			t.Errorf("For text '%s', expected %d emotions, got %d", tc.text, len(tc.expectedEmotions), len(emotions))
			continue
		}

		for _, expected := range tc.expectedEmotions {
			found := false
			for _, actual := range emotions {
				if actual == expected {
					found = true
					break
				}
			}
			if !found {
				t.Errorf("For text '%s', expected emotion '%s' not found", tc.text, expected)
			}
		}
	}
}

func TestTimeOfDay(t *testing.T) {
	testCases := []struct {
		hour     int
		expected string
	}{
		{hour: 6, expected: "morning"},
		{hour: 10, expected: "morning"},
		{hour: 12, expected: "afternoon"},
		{hour: 15, expected: "afternoon"},
		{hour: 18, expected: "evening"},
		{hour: 20, expected: "evening"},
		{hour: 23, expected: "night"},
		{hour: 2, expected: "night"},
	}

	for _, tc := range testCases {
		// Create a time with the specific hour
		testTime := time.Date(2023, 1, 1, tc.hour, 0, 0, 0, time.UTC)
		result := getTimeOfDay(testTime)

		if result != tc.expected {
			t.Errorf("For hour %d, expected '%s', got '%s'", tc.hour, tc.expected, result)
		}
	}
}

func TestKnowledgeManagement(t *testing.T) {
	enricher := NewContextEnricher()

	// Test adding knowledge
	enricher.AddKnowledge("test_key", "test_value")
	enricher.AddKnowledge("complex_key", map[string]interface{}{
		"nested": "value",
		"number": 42,
	})

	// Test retrieving knowledge
	value, exists := enricher.GetKnowledge("test_key")
	if !exists {
		t.Error("Knowledge not found after adding")
	}
	if value != "test_value" {
		t.Errorf("Expected 'test_value', got '%v'", value)
	}

	// Test complex knowledge
	complexValue, exists := enricher.GetKnowledge("complex_key")
	if !exists {
		t.Error("Complex knowledge not found after adding")
	}

	complexMap, ok := complexValue.(map[string]interface{})
	if !ok {
		t.Error("Complex value is not a map")
	} else {
		if complexMap["nested"] != "value" {
			t.Error("Nested value not preserved")
		}
		if complexMap["number"] != 42 {
			t.Error("Number value not preserved")
		}
	}

	// Test non-existent knowledge
	_, exists = enricher.GetKnowledge("non_existent")
	if exists {
		t.Error("Non-existent knowledge reported as existing")
	}
}

func TestUnsupportedEnrichmentType(t *testing.T) {
	enricher := NewContextEnricher()
	ctx := context.Background()

	req := &EnrichmentRequest{
		Type:    "unsupported_type",
		Data:    "test data",
		Context: map[string]interface{}{},
	}

	result, err := enricher.Enrich(ctx, req)
	if err != nil {
		t.Fatalf("Enrichment should not fail for unsupported type: %v", err)
	}

	// Should return original data unchanged
	if result.EnrichedData != req.Data {
		t.Error("Unsupported enrichment type should return original data")
	}
}

// Helper function to check if a string contains a substring
func contains(s, substr string) bool {
	return len(s) >= len(substr) && (s == substr || len(substr) == 0 ||
		(len(s) > len(substr) && (s[:len(substr)] == substr || s[len(s)-len(substr):] == substr ||
			containsMiddle(s, substr))))
}

func containsMiddle(s, substr string) bool {
	for i := 1; i <= len(s)-len(substr); i++ {
		if s[i:i+len(substr)] == substr {
			return true
		}
	}
	return false
}
