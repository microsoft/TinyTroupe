package extraction

import (
	"context"
	"testing"
	"time"
)

func TestSimulationExtractorCreation(t *testing.T) {
	extractor := NewSimulationExtractor()
	if extractor == nil {
		t.Fatal("NewSimulationExtractor returned nil")
	}

	supportedTypes := extractor.GetSupportedTypes()
	if len(supportedTypes) != 5 {
		t.Errorf("Expected 5 supported types, got %d", len(supportedTypes))
	}

	expectedTypes := []ExtractionType{
		ConversationExtraction,
		MetricsExtraction,
		PatternsExtraction,
		SummaryExtraction,
		TimelineExtraction,
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

func TestExtractionRequestValidation(t *testing.T) {
	extractor := NewSimulationExtractor()
	ctx := context.Background()

	// Test nil request
	result, err := extractor.Extract(ctx, nil)
	if err == nil {
		t.Error("Expected error for nil request")
	}
	if result != nil {
		t.Error("Expected nil result for nil request")
	}
}

func TestConversationExtraction(t *testing.T) {
	extractor := NewSimulationExtractor()
	ctx := context.Background()

	// Sample log data from TinyTroupe simulation
	logData := []string{
		"2025/08/02 11:01:01 [Alice] Listening to: Hello Bob, how are you today?",
		"2025/08/02 11:01:02 [Bob] Listening to: Hi Alice! I'm doing great, thanks for asking.",
		"2025/08/02 11:01:03 [TestWorld] Alice -> Bob: What are you working on?",
		"2025/08/02 11:01:04 [TestWorld] Broadcasting: Welcome everyone to the chat!",
		"2025/08/02 11:01:05 [Charlie] Listening to: Thanks for the welcome!",
	}

	req := &ExtractionRequest{
		Type:   ConversationExtraction,
		Source: logData,
		Options: map[string]interface{}{
			"include_metadata": true,
		},
	}

	result, err := extractor.Extract(ctx, req)
	if err != nil {
		t.Fatalf("Conversation extraction failed: %v", err)
	}

	if result == nil {
		t.Fatal("Result is nil")
	}

	if result.Type != ConversationExtraction {
		t.Errorf("Expected type %s, got %s", ConversationExtraction, result.Type)
	}

	// Check that we got conversation data
	conversationData, ok := result.Data.(*ConversationData)
	if !ok {
		t.Fatal("Result data is not ConversationData")
	}

	// Verify messages were extracted
	if len(conversationData.Messages) == 0 {
		t.Error("No messages extracted")
	}

	// Verify participants were identified
	if len(conversationData.Participants) == 0 {
		t.Error("No participants identified")
	}

	// Check for specific participants
	expectedParticipants := []string{"Alice", "Bob", "Charlie"}
	for _, expected := range expectedParticipants {
		found := false
		for _, participant := range conversationData.Participants {
			if participant == expected {
				found = true
				break
			}
		}
		if !found {
			t.Errorf("Expected participant %s not found", expected)
		}
	}

	// Verify statistics
	if conversationData.Statistics["message_count"] == 0 {
		t.Error("Message count not calculated")
	}

	// Check summary
	if len(result.Summary) == 0 {
		t.Error("No summary generated")
	}
}

func TestMetricsExtraction(t *testing.T) {
	extractor := NewSimulationExtractor()
	ctx := context.Background()

	logData := []string{
		"2025/08/02 11:01:01 [Alice] Listening to: Hello everyone! I'm excited to be here.",
		"2025/08/02 11:01:02 [Bob] Listening to: Hi Alice, nice to meet you!",
		"2025/08/02 11:01:03 [Alice] Listening to: How is everyone doing today?",
		"2025/08/02 11:01:04 [Charlie] Listening to: I'm doing great, thanks for asking Alice.",
		"2025/08/02 11:01:05 [Bob] Listening to: Same here, having a wonderful day!",
	}

	req := &ExtractionRequest{
		Type:   MetricsExtraction,
		Source: logData,
	}

	result, err := extractor.Extract(ctx, req)
	if err != nil {
		t.Fatalf("Metrics extraction failed: %v", err)
	}

	metricsData, ok := result.Data.(*MetricsData)
	if !ok {
		t.Fatal("Result data is not MetricsData")
	}

	// Check that metrics were calculated
	if len(metricsData.AgentMetrics) == 0 {
		t.Error("No agent metrics calculated")
	}

	if metricsData.TotalMessages == 0 {
		t.Error("Total message count not calculated")
	}

	// Verify specific agent metrics
	if aliceMetrics, exists := metricsData.AgentMetrics["Alice"]; exists {
		if aliceMetrics.MessageCount != 2 {
			t.Errorf("Expected Alice to have 2 messages, got %d", aliceMetrics.MessageCount)
		}

		if aliceMetrics.WordCount == 0 {
			t.Error("Alice's word count not calculated")
		}

		if aliceMetrics.AverageLength == 0 {
			t.Error("Alice's average message length not calculated")
		}
	} else {
		t.Error("Alice metrics not found")
	}

	// Check interaction counts
	if len(metricsData.InteractionCounts) == 0 {
		t.Error("Interaction counts not calculated")
	}
}

func TestPatternsExtraction(t *testing.T) {
	extractor := NewSimulationExtractor()
	ctx := context.Background()

	logData := []string{
		"2025/08/02 09:01:01 [Alice] Listening to: Good morning everyone!",
		"2025/08/02 09:01:02 [Bob] Listening to: Morning Alice!",
		"2025/08/02 14:01:03 [Alice] Listening to: How's the afternoon going?",
		"2025/08/02 14:01:04 [Charlie] Listening to: Pretty good, thanks!",
		"2025/08/02 18:01:05 [Bob] Listening to: Getting close to evening now.",
	}

	req := &ExtractionRequest{
		Type:   PatternsExtraction,
		Source: logData,
	}

	result, err := extractor.Extract(ctx, req)
	if err != nil {
		t.Fatalf("Patterns extraction failed: %v", err)
	}

	patterns, ok := result.Data.(map[string]interface{})
	if !ok {
		t.Fatal("Result data is not a patterns map")
	}

	// Check that pattern categories exist
	expectedCategories := []string{
		"conversation_patterns",
		"temporal_patterns",
		"linguistic_patterns",
		"interaction_patterns",
	}

	for _, category := range expectedCategories {
		if _, exists := patterns[category]; !exists {
			t.Errorf("Pattern category %s not found", category)
		}
	}

	// Verify temporal patterns include activity analysis
	if temporalPatterns, exists := patterns["temporal_patterns"]; exists {
		temporalMap, ok := temporalPatterns.(map[string]interface{})
		if !ok {
			t.Error("Temporal patterns is not a map")
		} else {
			if _, exists := temporalMap["activity_by_hour"]; !exists {
				t.Error("Activity by hour not found in temporal patterns")
			}
		}
	}
}

func TestSummaryExtraction(t *testing.T) {
	extractor := NewSimulationExtractor()
	ctx := context.Background()

	logData := []string{
		"2025/08/02 11:01:01 [Alice] Listening to: Let's discuss technology and programming today.",
		"2025/08/02 11:01:02 [Bob] Listening to: Great idea! I love talking about software development.",
		"2025/08/02 11:01:03 [Charlie] Listening to: I'm also interested in AI and machine learning.",
	}

	req := &ExtractionRequest{
		Type:   SummaryExtraction,
		Source: logData,
	}

	result, err := extractor.Extract(ctx, req)
	if err != nil {
		t.Fatalf("Summary extraction failed: %v", err)
	}

	summaries, ok := result.Data.([]map[string]interface{})
	if !ok {
		t.Fatal("Result data is not a summaries slice")
	}

	if len(summaries) == 0 {
		t.Error("No summaries generated")
	}

	// Check that different summary types are present
	summaryTypes := make(map[string]bool)
	for _, summary := range summaries {
		if summaryType, exists := summary["type"]; exists {
			if typeStr, ok := summaryType.(string); ok {
				summaryTypes[typeStr] = true
			}
		}
	}

	expectedTypes := []string{"overview", "key_topics", "participant_activity"}
	for _, expectedType := range expectedTypes {
		if !summaryTypes[expectedType] {
			t.Errorf("Summary type %s not found", expectedType)
		}
	}
}

func TestTimelineExtraction(t *testing.T) {
	extractor := NewSimulationExtractor()
	ctx := context.Background()

	logData := []string{
		"2025/08/02 11:01:01 [Alice] Listening to: First message",
		"2025/08/02 11:01:02 [Bob] Listening to: Second message",
		"2025/08/02 11:01:03 [TestWorld] Alice -> Bob: Direct message",
		"2025/08/02 11:01:04 [TestWorld] Broadcasting: Broadcast message",
	}

	req := &ExtractionRequest{
		Type:   TimelineExtraction,
		Source: logData,
	}

	result, err := extractor.Extract(ctx, req)
	if err != nil {
		t.Fatalf("Timeline extraction failed: %v", err)
	}

	timeline, ok := result.Data.([]map[string]interface{})
	if !ok {
		t.Fatal("Result data is not a timeline slice")
	}

	if len(timeline) == 0 {
		t.Error("No timeline events generated")
	}

	// Verify timeline events have required fields
	for i, event := range timeline {
		if _, exists := event["timestamp"]; !exists {
			t.Errorf("Timeline event %d missing timestamp", i)
		}

		if _, exists := event["type"]; !exists {
			t.Errorf("Timeline event %d missing type", i)
		}

		if _, exists := event["actor"]; !exists {
			t.Errorf("Timeline event %d missing actor", i)
		}

		if _, exists := event["content"]; !exists {
			t.Errorf("Timeline event %d missing content", i)
		}
	}

	// Check chronological order
	var lastTime time.Time
	for i, event := range timeline {
		if timestamp, exists := event["timestamp"]; exists {
			if eventTime, ok := timestamp.(time.Time); ok {
				if i > 0 && eventTime.Before(lastTime) {
					t.Error("Timeline events are not in chronological order")
				}
				lastTime = eventTime
			}
		}
	}
}

func TestUnsupportedExtractionType(t *testing.T) {
	extractor := NewSimulationExtractor()
	ctx := context.Background()

	req := &ExtractionRequest{
		Type:   "unsupported_type",
		Source: "test data",
	}

	result, err := extractor.Extract(ctx, req)
	if err == nil {
		t.Error("Expected error for unsupported extraction type")
	}
	if result != nil {
		t.Error("Expected nil result for unsupported extraction type")
	}
}

func TestEmotionExtraction(t *testing.T) {
	extractor := NewSimulationExtractor()

	testCases := []struct {
		text             string
		expectedEmotions []string
	}{
		{
			text:             "I'm so happy and excited about this project!",
			expectedEmotions: []string{"positive"},
		},
		{
			text:             "I'm confident this will definitely work.",
			expectedEmotions: []string{"confident"},
		},
		{
			text:             "I'm curious and fascinated by this problem.",
			expectedEmotions: []string{"curious"},
		},
		{
			text:             "I'm unsure, maybe we should think about this.",
			expectedEmotions: []string{"uncertain"},
		},
		{
			text:             "This is a neutral technical statement.",
			expectedEmotions: []string{},
		},
	}

	for _, tc := range testCases {
		emotions := extractor.extractEmotionsFromText(tc.text)

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

func TestTopicExtraction(t *testing.T) {
	extractor := NewSimulationExtractor()

	testCases := []struct {
		text           string
		expectedTopics []string
	}{
		{
			text:           "I love programming and software development with AI technology.",
			expectedTopics: []string{"technology"},
		},
		{
			text:           "Let's discuss our work project and upcoming meeting.",
			expectedTopics: []string{"work"},
		},
		{
			text:           "I enjoy cooking recipes and trying new food at restaurants.",
			expectedTopics: []string{"food"},
		},
		{
			text:           "Playing piano and guitar music is my hobby.",
			expectedTopics: []string{"music", "personal"}, // contains both "piano/music" and "hobby"
		},
		{
			text:           "This is a generic conversation without specific topics.",
			expectedTopics: []string{},
		},
	}

	for _, tc := range testCases {
		topics := extractor.extractTopicsFromText(tc.text)

		if len(topics) != len(tc.expectedTopics) {
			t.Errorf("For text '%s', expected %d topics, got %d", tc.text, len(tc.expectedTopics), len(topics))
			continue
		}

		for _, expected := range tc.expectedTopics {
			found := false
			for _, actual := range topics {
				if actual == expected {
					found = true
					break
				}
			}
			if !found {
				t.Errorf("For text '%s', expected topic '%s' not found", tc.text, expected)
			}
		}
	}
}

func TestDifferentSourceTypes(t *testing.T) {
	extractor := NewSimulationExtractor()
	ctx := context.Background()

	testCases := []struct {
		name   string
		source interface{}
		valid  bool
	}{
		{
			name:   "string_source",
			source: "2025/08/02 11:01:01 [Alice] Listening to: Hello world",
			valid:  true,
		},
		{
			name:   "string_slice_source",
			source: []string{"2025/08/02 11:01:01 [Alice] Listening to: Hello world"},
			valid:  true,
		},
		{
			name:   "interface_slice_source",
			source: []interface{}{"2025/08/02 11:01:01 [Alice] Listening to: Hello world"},
			valid:  true,
		},
		{
			name:   "invalid_source",
			source: 12345,
			valid:  false,
		},
	}

	for _, tc := range testCases {
		t.Run(tc.name, func(t *testing.T) {
			req := &ExtractionRequest{
				Type:   ConversationExtraction,
				Source: tc.source,
			}

			result, err := extractor.Extract(ctx, req)

			if tc.valid {
				if err != nil {
					t.Errorf("Expected no error for valid source, got: %v", err)
				}
				if result == nil {
					t.Error("Expected result for valid source")
				}
			} else {
				if err == nil {
					t.Error("Expected error for invalid source")
				}
			}
		})
	}
}

func TestMetadataHandling(t *testing.T) {
	extractor := NewSimulationExtractor()
	ctx := context.Background()

	metadata := map[string]interface{}{
		"session_id":  "test-session-123",
		"environment": "test-env",
		"experiment":  "conversation-analysis",
	}

	req := &ExtractionRequest{
		Type:     ConversationExtraction,
		Source:   "2025/08/02 11:01:01 [Alice] Listening to: Test message",
		Metadata: metadata,
	}

	result, err := extractor.Extract(ctx, req)
	if err != nil {
		t.Fatalf("Extraction failed: %v", err)
	}

	// Verify metadata was preserved in result
	for key, expectedValue := range metadata {
		if actualValue, exists := result.Metadata[key]; !exists {
			t.Errorf("Metadata key %s not found in result", key)
		} else if actualValue != expectedValue {
			t.Errorf("Metadata key %s: expected %v, got %v", key, expectedValue, actualValue)
		}
	}
}

func TestConversationStatistics(t *testing.T) {
	extractor := NewSimulationExtractor()
	ctx := context.Background()

	logData := []string{
		"2025/08/02 11:01:01 [Alice] Listening to: Hello",
		"2025/08/02 11:01:02 [Bob] Listening to: Hi there",
		"2025/08/02 11:01:03 [Charlie] Listening to: Good morning",
		"2025/08/02 11:05:01 [Alice] Listening to: How is everyone?",
	}

	req := &ExtractionRequest{
		Type:   ConversationExtraction,
		Source: logData,
	}

	result, err := extractor.Extract(ctx, req)
	if err != nil {
		t.Fatalf("Extraction failed: %v", err)
	}

	conversationData, ok := result.Data.(*ConversationData)
	if !ok {
		t.Fatal("Result data is not ConversationData")
	}

	// Check that duration was calculated
	if conversationData.Statistics["duration_minutes"] == nil {
		t.Error("Duration not calculated")
	}

	duration, ok := conversationData.Statistics["duration_minutes"].(float64)
	if !ok {
		t.Error("Duration is not a float64")
	} else if duration <= 0 {
		t.Error("Duration should be positive")
	}

	// Check message count
	if conversationData.Statistics["message_count"] != len(conversationData.Messages) {
		t.Error("Message count in statistics doesn't match actual messages")
	}

	// Check participant count
	if conversationData.Statistics["participant_count"] != len(conversationData.Participants) {
		t.Error("Participant count in statistics doesn't match actual participants")
	}
}
