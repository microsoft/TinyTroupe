// Package extraction provides data extraction and processing capabilities.
// This module handles simulation data extraction, analytics, and reporting.
package extraction

import (
	"context"
	"fmt"
	"regexp"
	"sort"
	"strconv"
	"strings"
	"time"
)

// ExtractionType represents different types of extraction operations
type ExtractionType string

const (
	ConversationExtraction ExtractionType = "conversation"
	MetricsExtraction      ExtractionType = "metrics"
	PatternsExtraction     ExtractionType = "patterns"
	SummaryExtraction      ExtractionType = "summary"
	TimelineExtraction     ExtractionType = "timeline"
)

// ExtractionRequest represents a request to extract data
type ExtractionRequest struct {
	Type     ExtractionType         `json:"type"`
	Source   interface{}            `json:"source"`
	Options  map[string]interface{} `json:"options,omitempty"`
	Filters  map[string]interface{} `json:"filters,omitempty"`
	Metadata map[string]interface{} `json:"metadata,omitempty"`
}

// ExtractionResult represents the result of an extraction operation
type ExtractionResult struct {
	Type      ExtractionType         `json:"type"`
	Data      interface{}            `json:"data"`
	Summary   map[string]interface{} `json:"summary"`
	Timestamp time.Time              `json:"timestamp"`
	Metadata  map[string]interface{} `json:"metadata,omitempty"`
}

// ConversationData represents extracted conversation data
type ConversationData struct {
	Messages     []MessageData          `json:"messages"`
	Participants []string               `json:"participants"`
	StartTime    time.Time              `json:"start_time"`
	EndTime      time.Time              `json:"end_time"`
	Topics       []string               `json:"topics"`
	Emotions     map[string][]string    `json:"emotions"`
	Statistics   map[string]interface{} `json:"statistics"`
}

// MessageData represents a single message in a conversation
type MessageData struct {
	Speaker   string                 `json:"speaker"`
	Content   string                 `json:"content"`
	Timestamp time.Time              `json:"timestamp"`
	Type      string                 `json:"type,omitempty"`
	Metadata  map[string]interface{} `json:"metadata,omitempty"`
}

// MetricsData represents extracted metrics
type MetricsData struct {
	AgentMetrics      map[string]AgentMetric   `json:"agent_metrics"`
	InteractionCounts map[string]int           `json:"interaction_counts"`
	TimeSpentByAgent  map[string]time.Duration `json:"time_spent_by_agent"`
	TotalMessages     int                      `json:"total_messages"`
	TotalDuration     time.Duration            `json:"total_duration"`
	PeakActivity      time.Time                `json:"peak_activity"`
	Summary           map[string]interface{}   `json:"summary"`
}

// AgentMetric represents metrics for a single agent
type AgentMetric struct {
	MessageCount    int                    `json:"message_count"`
	WordCount       int                    `json:"word_count"`
	AverageLength   float64                `json:"average_length"`
	EmotionalTone   map[string]int         `json:"emotional_tone"`
	ActivityPattern map[string]interface{} `json:"activity_pattern"`
}

// Extractor interface defines extraction capabilities
type Extractor interface {
	// Extract extracts data from the provided source
	Extract(ctx context.Context, req *ExtractionRequest) (*ExtractionResult, error)

	// GetSupportedTypes returns the extraction types this extractor supports
	GetSupportedTypes() []ExtractionType
}

// SimulationExtractor extracts data from simulation logs and agent interactions
type SimulationExtractor struct {
	patterns map[string]*regexp.Regexp
}

// NewSimulationExtractor creates a new simulation data extractor
func NewSimulationExtractor() *SimulationExtractor {
	patterns := map[string]*regexp.Regexp{
		"timestamp":  regexp.MustCompile(`(\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2})`),
		"agent_name": regexp.MustCompile(`\[([^\]]+)\]`),
		"action":     regexp.MustCompile(`(Listening to|Broadcasting|Added agent|Removed agent|Talk target)`),
		"message":    regexp.MustCompile(`Listening to: (.+)$`),
		"broadcast":  regexp.MustCompile(`Broadcasting: (.+)$`),
		"talk":       regexp.MustCompile(`([^:]+) -> ([^:]+): (.+)$`),
	}

	return &SimulationExtractor{
		patterns: patterns,
	}
}

// Extract implements the Extractor interface
func (se *SimulationExtractor) Extract(ctx context.Context, req *ExtractionRequest) (*ExtractionResult, error) {
	if req == nil {
		return nil, fmt.Errorf("extraction request cannot be nil")
	}

	result := &ExtractionResult{
		Type:      req.Type,
		Timestamp: time.Now(),
		Summary:   make(map[string]interface{}),
		Metadata:  make(map[string]interface{}),
	}

	switch req.Type {
	case ConversationExtraction:
		data, err := se.extractConversation(req.Source, req.Options)
		if err != nil {
			return nil, fmt.Errorf("conversation extraction failed: %w", err)
		}
		result.Data = data
		result.Summary = se.summarizeConversation(data)

	case MetricsExtraction:
		data, err := se.extractMetrics(req.Source, req.Options)
		if err != nil {
			return nil, fmt.Errorf("metrics extraction failed: %w", err)
		}
		result.Data = data
		result.Summary = se.summarizeMetrics(data)

	case PatternsExtraction:
		data, err := se.extractPatterns(req.Source, req.Options)
		if err != nil {
			return nil, fmt.Errorf("patterns extraction failed: %w", err)
		}
		result.Data = data
		result.Summary = se.summarizePatterns(data)

	case SummaryExtraction:
		data, err := se.extractSummary(req.Source, req.Options)
		if err != nil {
			return nil, fmt.Errorf("summary extraction failed: %w", err)
		}
		result.Data = data
		result.Summary = map[string]interface{}{"extracted_summaries": len(data.([]map[string]interface{}))}

	case TimelineExtraction:
		data, err := se.extractTimeline(req.Source, req.Options)
		if err != nil {
			return nil, fmt.Errorf("timeline extraction failed: %w", err)
		}
		result.Data = data
		result.Summary = se.summarizeTimeline(data)

	default:
		return nil, fmt.Errorf("unsupported extraction type: %s", req.Type)
	}

	// Add request metadata to result
	if req.Metadata != nil {
		for k, v := range req.Metadata {
			result.Metadata[k] = v
		}
	}

	return result, nil
}

// GetSupportedTypes returns the extraction types this extractor supports
func (se *SimulationExtractor) GetSupportedTypes() []ExtractionType {
	return []ExtractionType{
		ConversationExtraction,
		MetricsExtraction,
		PatternsExtraction,
		SummaryExtraction,
		TimelineExtraction,
	}
}

// extractConversation extracts conversation data from logs or agent histories
func (se *SimulationExtractor) extractConversation(source interface{}, options map[string]interface{}) (*ConversationData, error) {
	var logLines []string

	// Handle different source types
	switch s := source.(type) {
	case string:
		logLines = strings.Split(s, "\n")
	case []string:
		logLines = s
	case []interface{}:
		for _, line := range s {
			if str, ok := line.(string); ok {
				logLines = append(logLines, str)
			}
		}
	default:
		return nil, fmt.Errorf("unsupported source type for conversation extraction")
	}

	conversation := &ConversationData{
		Messages:     []MessageData{},
		Participants: []string{},
		Topics:       []string{},
		Emotions:     make(map[string][]string),
		Statistics:   make(map[string]interface{}),
	}

	participantSet := make(map[string]bool)
	topicSet := make(map[string]bool)

	for _, line := range logLines {
		line = strings.TrimSpace(line)
		if line == "" {
			continue
		}

		// Parse timestamp
		timestampMatch := se.patterns["timestamp"].FindStringSubmatch(line)
		var timestamp time.Time
		if len(timestampMatch) > 1 {
			// Parse timestamp (format: 2025/08/02 11:01:01)
			t, err := time.Parse("2006/01/02 15:04:05", timestampMatch[1])
			if err == nil {
				timestamp = t
			}
		}

		// Extract message content
		if messageMatch := se.patterns["message"].FindStringSubmatch(line); len(messageMatch) > 1 {
			// Extract agent name
			agentMatch := se.patterns["agent_name"].FindStringSubmatch(line)
			if len(agentMatch) > 1 {
				speaker := agentMatch[1]
				content := messageMatch[1]

				message := MessageData{
					Speaker:   speaker,
					Content:   content,
					Timestamp: timestamp,
					Type:      "message",
					Metadata:  make(map[string]interface{}),
				}

				conversation.Messages = append(conversation.Messages, message)
				participantSet[speaker] = true

				// Extract topics from content
				topics := se.extractTopicsFromText(content)
				for _, topic := range topics {
					topicSet[topic] = true
				}

				// Extract emotions
				emotions := se.extractEmotionsFromText(content)
				if len(emotions) > 0 {
					conversation.Emotions[speaker] = append(conversation.Emotions[speaker], emotions...)
				}
			}
		}

		// Extract broadcast messages
		if broadcastMatch := se.patterns["broadcast"].FindStringSubmatch(line); len(broadcastMatch) > 1 {
			agentMatch := se.patterns["agent_name"].FindStringSubmatch(line)
			if len(agentMatch) > 1 {
				speaker := agentMatch[1]
				content := broadcastMatch[1]

				message := MessageData{
					Speaker:   speaker,
					Content:   content,
					Timestamp: timestamp,
					Type:      "broadcast",
					Metadata:  make(map[string]interface{}),
				}

				conversation.Messages = append(conversation.Messages, message)
				participantSet[speaker] = true
			}
		}

		// Extract direct talk messages
		if talkMatch := se.patterns["talk"].FindStringSubmatch(line); len(talkMatch) > 3 {
			speaker := talkMatch[1]
			target := talkMatch[2]
			content := talkMatch[3]

			message := MessageData{
				Speaker:   speaker,
				Content:   content,
				Timestamp: timestamp,
				Type:      "direct_talk",
				Metadata: map[string]interface{}{
					"target": target,
				},
			}

			conversation.Messages = append(conversation.Messages, message)
			participantSet[speaker] = true
			participantSet[target] = true
		}
	}

	// Convert sets to slices
	for participant := range participantSet {
		conversation.Participants = append(conversation.Participants, participant)
	}
	sort.Strings(conversation.Participants)

	for topic := range topicSet {
		conversation.Topics = append(conversation.Topics, topic)
	}
	sort.Strings(conversation.Topics)

	// Set time bounds
	if len(conversation.Messages) > 0 {
		conversation.StartTime = conversation.Messages[0].Timestamp
		conversation.EndTime = conversation.Messages[len(conversation.Messages)-1].Timestamp
	}

	// Calculate statistics
	conversation.Statistics["message_count"] = len(conversation.Messages)
	conversation.Statistics["participant_count"] = len(conversation.Participants)
	conversation.Statistics["topic_count"] = len(conversation.Topics)
	if !conversation.EndTime.IsZero() && !conversation.StartTime.IsZero() {
		conversation.Statistics["duration_minutes"] = conversation.EndTime.Sub(conversation.StartTime).Minutes()
	}

	return conversation, nil
}

// extractMetrics extracts performance and interaction metrics
func (se *SimulationExtractor) extractMetrics(source interface{}, options map[string]interface{}) (*MetricsData, error) {
	// First extract conversation data to analyze
	conversation, err := se.extractConversation(source, options)
	if err != nil {
		return nil, fmt.Errorf("failed to extract conversation for metrics: %w", err)
	}

	metrics := &MetricsData{
		AgentMetrics:      make(map[string]AgentMetric),
		InteractionCounts: make(map[string]int),
		TimeSpentByAgent:  make(map[string]time.Duration),
		TotalMessages:     len(conversation.Messages),
		Summary:           make(map[string]interface{}),
	}

	if len(conversation.Messages) > 0 {
		metrics.TotalDuration = conversation.EndTime.Sub(conversation.StartTime)
	}

	// Calculate per-agent metrics
	for _, participant := range conversation.Participants {
		agentMetric := AgentMetric{
			EmotionalTone:   make(map[string]int),
			ActivityPattern: make(map[string]interface{}),
		}

		messageCount := 0
		totalWords := 0

		// Track activity by hour
		hourlyActivity := make(map[int]int)

		for _, message := range conversation.Messages {
			if message.Speaker == participant {
				messageCount++
				wordCount := len(strings.Fields(message.Content))
				totalWords += wordCount

				// Track hourly activity
				hour := message.Timestamp.Hour()
				hourlyActivity[hour]++

				// Analyze emotional tone
				emotions := se.extractEmotionsFromText(message.Content)
				for _, emotion := range emotions {
					agentMetric.EmotionalTone[emotion]++
				}
			}
		}

		agentMetric.MessageCount = messageCount
		agentMetric.WordCount = totalWords
		if messageCount > 0 {
			agentMetric.AverageLength = float64(totalWords) / float64(messageCount)
		}

		// Store activity pattern
		agentMetric.ActivityPattern["hourly_distribution"] = hourlyActivity
		agentMetric.ActivityPattern["most_active_hour"] = se.getMostActiveHour(hourlyActivity)

		metrics.AgentMetrics[participant] = agentMetric
		metrics.InteractionCounts[participant] = messageCount
	}

	// Find peak activity time
	if len(conversation.Messages) > 0 {
		hourCounts := make(map[int]int)
		for _, message := range conversation.Messages {
			hour := message.Timestamp.Hour()
			hourCounts[hour]++
		}

		maxCount := 0
		peakHour := 0
		for hour, count := range hourCounts {
			if count > maxCount {
				maxCount = count
				peakHour = hour
			}
		}

		// Create a time representing the peak hour
		metrics.PeakActivity = time.Date(2023, 1, 1, peakHour, 0, 0, 0, time.UTC)
	}

	// Generate summary
	metrics.Summary["total_participants"] = len(conversation.Participants)
	metrics.Summary["average_messages_per_participant"] = float64(metrics.TotalMessages) / float64(len(conversation.Participants))

	return metrics, nil
}

// extractPatterns identifies communication and behavioral patterns
func (se *SimulationExtractor) extractPatterns(source interface{}, options map[string]interface{}) (interface{}, error) {
	conversation, err := se.extractConversation(source, options)
	if err != nil {
		return nil, fmt.Errorf("failed to extract conversation for patterns: %w", err)
	}

	patterns := map[string]interface{}{
		"conversation_patterns": se.analyzeConversationPatterns(conversation),
		"temporal_patterns":     se.analyzeTemporalPatterns(conversation),
		"linguistic_patterns":   se.analyzeLinguisticPatterns(conversation),
		"interaction_patterns":  se.analyzeInteractionPatterns(conversation),
	}

	return patterns, nil
}

// extractSummary generates summaries of simulation data
func (se *SimulationExtractor) extractSummary(source interface{}, options map[string]interface{}) (interface{}, error) {
	conversation, err := se.extractConversation(source, options)
	if err != nil {
		return nil, fmt.Errorf("failed to extract conversation for summary: %w", err)
	}

	summaries := []map[string]interface{}{
		{
			"type":     "overview",
			"content":  se.generateOverviewSummary(conversation),
			"metadata": map[string]interface{}{"generated_at": time.Now()},
		},
		{
			"type":     "key_topics",
			"content":  conversation.Topics,
			"metadata": map[string]interface{}{"count": len(conversation.Topics)},
		},
		{
			"type":     "participant_activity",
			"content":  se.generateParticipantSummary(conversation),
			"metadata": map[string]interface{}{"participant_count": len(conversation.Participants)},
		},
	}

	return summaries, nil
}

// extractTimeline creates a chronological timeline of events
func (se *SimulationExtractor) extractTimeline(source interface{}, options map[string]interface{}) (interface{}, error) {
	conversation, err := se.extractConversation(source, options)
	if err != nil {
		return nil, fmt.Errorf("failed to extract conversation for timeline: %w", err)
	}

	timeline := make([]map[string]interface{}, 0, len(conversation.Messages))

	for _, message := range conversation.Messages {
		event := map[string]interface{}{
			"timestamp": message.Timestamp,
			"type":      "message",
			"actor":     message.Speaker,
			"content":   message.Content,
			"metadata":  message.Metadata,
		}

		if message.Type != "" {
			event["message_type"] = message.Type
		}

		timeline = append(timeline, event)
	}

	return timeline, nil
}

// Helper methods for analysis

func (se *SimulationExtractor) extractTopicsFromText(text string) []string {
	topics := []string{}
	lower := strings.ToLower(text)

	topicKeywords := map[string][]string{
		"technology": {"technology", "software", "programming", "AI", "artificial intelligence"},
		"work":       {"work", "job", "project", "task", "meeting"},
		"personal":   {"family", "home", "hobby", "interest", "free time"},
		"travel":     {"travel", "trip", "vacation", "journey", "visit"},
		"food":       {"food", "cooking", "recipe", "restaurant", "meal"},
		"music":      {"music", "song", "piano", "guitar", "concert"},
	}

	for topic, keywords := range topicKeywords {
		for _, keyword := range keywords {
			if strings.Contains(lower, keyword) {
				topics = append(topics, topic)
				break
			}
		}
	}

	return topics
}

func (se *SimulationExtractor) extractEmotionsFromText(text string) []string {
	emotions := []string{}
	lower := strings.ToLower(text)

	// Add word boundaries to ensure exact word matching
	words := strings.Fields(lower)
	wordSet := make(map[string]bool)
	for _, word := range words {
		// Remove punctuation from words
		cleanWord := strings.Trim(word, ".,!?;:")
		wordSet[cleanWord] = true
	}

	emotionKeywords := map[string][]string{
		"positive":  {"happy", "excited", "great", "wonderful", "amazing", "love", "enjoy"},
		"negative":  {"sad", "upset", "disappointed", "frustrated", "angry", "hate"},
		"curious":   {"curious", "wonder", "interesting", "fascinated", "intrigued"},
		"confident": {"confident", "sure", "certain", "definitely", "absolutely"},
		"uncertain": {"unsure", "maybe", "perhaps", "might"},
	}

	for emotion, keywords := range emotionKeywords {
		for _, keyword := range keywords {
			if wordSet[keyword] {
				emotions = append(emotions, emotion)
				break // Only add each emotion category once
			}
		}
	}

	// Special case for multi-word phrases
	if strings.Contains(lower, "could be") {
		// Check if uncertain is already added
		found := false
		for _, emotion := range emotions {
			if emotion == "uncertain" {
				found = true
				break
			}
		}
		if !found {
			emotions = append(emotions, "uncertain")
		}
	}

	return emotions
}

func (se *SimulationExtractor) getMostActiveHour(hourlyActivity map[int]int) int {
	maxActivity := 0
	mostActiveHour := 0

	for hour, activity := range hourlyActivity {
		if activity > maxActivity {
			maxActivity = activity
			mostActiveHour = hour
		}
	}

	return mostActiveHour
}

// Analysis methods for patterns

func (se *SimulationExtractor) analyzeConversationPatterns(conversation *ConversationData) map[string]interface{} {
	patterns := map[string]interface{}{
		"message_distribution":   se.calculateMessageDistribution(conversation),
		"response_time_patterns": se.analyzeResponseTimes(conversation),
		"conversation_flow":      se.analyzeConversationFlow(conversation),
		"topic_transitions":      se.analyzeTopicTransitions(conversation),
	}

	return patterns
}

func (se *SimulationExtractor) analyzeTemporalPatterns(conversation *ConversationData) map[string]interface{} {
	patterns := map[string]interface{}{
		"activity_by_hour":    se.getActivityByHour(conversation),
		"conversation_length": len(conversation.Messages),
		"peak_activity_time":  se.getPeakActivityTime(conversation),
		"quiet_periods":       se.identifyQuietPeriods(conversation),
	}

	return patterns
}

func (se *SimulationExtractor) analyzeLinguisticPatterns(conversation *ConversationData) map[string]interface{} {
	patterns := map[string]interface{}{
		"average_message_length": se.calculateAverageMessageLength(conversation),
		"vocabulary_diversity":   se.calculateVocabularyDiversity(conversation),
		"communication_styles":   se.identifyCommunicationStyles(conversation),
		"common_phrases":         se.findCommonPhrases(conversation),
	}

	return patterns
}

func (se *SimulationExtractor) analyzeInteractionPatterns(conversation *ConversationData) map[string]interface{} {
	patterns := map[string]interface{}{
		"interaction_matrix":    se.buildInteractionMatrix(conversation),
		"conversation_starters": se.identifyConversationStarters(conversation),
		"most_responsive_agent": se.findMostResponsiveAgent(conversation),
		"interaction_frequency": se.calculateInteractionFrequency(conversation),
	}

	return patterns
}

// Summary generation methods

func (se *SimulationExtractor) generateOverviewSummary(conversation *ConversationData) string {
	if len(conversation.Messages) == 0 {
		return "No conversation data available."
	}

	summary := fmt.Sprintf("Conversation involved %d participants exchanging %d messages over %.1f minutes. ",
		len(conversation.Participants),
		len(conversation.Messages),
		conversation.EndTime.Sub(conversation.StartTime).Minutes())

	if len(conversation.Topics) > 0 {
		summary += fmt.Sprintf("Main topics discussed: %s.", strings.Join(conversation.Topics, ", "))
	}

	return summary
}

func (se *SimulationExtractor) generateParticipantSummary(conversation *ConversationData) map[string]interface{} {
	summary := make(map[string]interface{})

	for _, participant := range conversation.Participants {
		messageCount := 0
		totalWords := 0

		for _, message := range conversation.Messages {
			if message.Speaker == participant {
				messageCount++
				totalWords += len(strings.Fields(message.Content))
			}
		}

		summary[participant] = map[string]interface{}{
			"message_count":      messageCount,
			"total_words":        totalWords,
			"average_length":     float64(totalWords) / float64(messageCount),
			"participation_rate": float64(messageCount) / float64(len(conversation.Messages)),
		}
	}

	return summary
}

// Helper methods for summarization

func (se *SimulationExtractor) summarizeConversation(data *ConversationData) map[string]interface{} {
	return map[string]interface{}{
		"message_count":     len(data.Messages),
		"participant_count": len(data.Participants),
		"topic_count":       len(data.Topics),
		"duration_minutes":  data.EndTime.Sub(data.StartTime).Minutes(),
		"participants":      data.Participants,
		"topics":            data.Topics,
	}
}

func (se *SimulationExtractor) summarizeMetrics(data *MetricsData) map[string]interface{} {
	return map[string]interface{}{
		"total_messages":     data.TotalMessages,
		"participant_count":  len(data.AgentMetrics),
		"total_duration":     data.TotalDuration.String(),
		"peak_activity_hour": data.PeakActivity.Hour(),
		"most_active_agent":  se.findMostActiveAgent(data),
	}
}

func (se *SimulationExtractor) summarizePatterns(data interface{}) map[string]interface{} {
	patterns, ok := data.(map[string]interface{})
	if !ok {
		return map[string]interface{}{"error": "invalid patterns data"}
	}

	return map[string]interface{}{
		"pattern_types": len(patterns),
		"analyzed":      true,
	}
}

func (se *SimulationExtractor) summarizeTimeline(data interface{}) map[string]interface{} {
	timeline, ok := data.([]map[string]interface{})
	if !ok {
		return map[string]interface{}{"error": "invalid timeline data"}
	}

	return map[string]interface{}{
		"event_count":      len(timeline),
		"timeline_created": true,
	}
}

// Additional helper methods (simplified implementations)

func (se *SimulationExtractor) calculateMessageDistribution(conversation *ConversationData) map[string]int {
	distribution := make(map[string]int)
	for _, message := range conversation.Messages {
		distribution[message.Speaker]++
	}
	return distribution
}

func (se *SimulationExtractor) analyzeResponseTimes(conversation *ConversationData) map[string]interface{} {
	// Simplified implementation
	return map[string]interface{}{
		"average_response_time": "analysis_placeholder",
		"response_patterns":     "quick_responses_detected",
	}
}

func (se *SimulationExtractor) analyzeConversationFlow(conversation *ConversationData) map[string]interface{} {
	// Simplified implementation
	return map[string]interface{}{
		"flow_type":          "natural",
		"interruptions":      0,
		"conversation_turns": len(conversation.Messages),
	}
}

func (se *SimulationExtractor) analyzeTopicTransitions(conversation *ConversationData) []string {
	// Simplified implementation
	return conversation.Topics
}

func (se *SimulationExtractor) getActivityByHour(conversation *ConversationData) map[string]int {
	activity := make(map[string]int)
	for _, message := range conversation.Messages {
		hour := strconv.Itoa(message.Timestamp.Hour())
		activity[hour]++
	}
	return activity
}

func (se *SimulationExtractor) getPeakActivityTime(conversation *ConversationData) string {
	hourCounts := make(map[int]int)
	for _, message := range conversation.Messages {
		hourCounts[message.Timestamp.Hour()]++
	}

	maxCount := 0
	peakHour := 0
	for hour, count := range hourCounts {
		if count > maxCount {
			maxCount = count
			peakHour = hour
		}
	}

	return fmt.Sprintf("%d:00", peakHour)
}

func (se *SimulationExtractor) identifyQuietPeriods(conversation *ConversationData) []string {
	// Simplified implementation
	return []string{"no_quiet_periods_detected"}
}

func (se *SimulationExtractor) calculateAverageMessageLength(conversation *ConversationData) float64 {
	if len(conversation.Messages) == 0 {
		return 0
	}

	totalWords := 0
	for _, message := range conversation.Messages {
		totalWords += len(strings.Fields(message.Content))
	}

	return float64(totalWords) / float64(len(conversation.Messages))
}

func (se *SimulationExtractor) calculateVocabularyDiversity(conversation *ConversationData) int {
	words := make(map[string]bool)
	for _, message := range conversation.Messages {
		for _, word := range strings.Fields(strings.ToLower(message.Content)) {
			words[word] = true
		}
	}
	return len(words)
}

func (se *SimulationExtractor) identifyCommunicationStyles(conversation *ConversationData) map[string]string {
	styles := make(map[string]string)
	for _, participant := range conversation.Participants {
		// Simplified style detection
		styles[participant] = "conversational"
	}
	return styles
}

func (se *SimulationExtractor) findCommonPhrases(conversation *ConversationData) []string {
	// Simplified implementation
	return []string{"hello", "how are you", "thank you"}
}

func (se *SimulationExtractor) buildInteractionMatrix(conversation *ConversationData) map[string]map[string]int {
	matrix := make(map[string]map[string]int)

	for _, participant := range conversation.Participants {
		matrix[participant] = make(map[string]int)
		for _, other := range conversation.Participants {
			matrix[participant][other] = 0
		}
	}

	// Count direct interactions
	for _, message := range conversation.Messages {
		if target, exists := message.Metadata["target"]; exists {
			if targetStr, ok := target.(string); ok {
				matrix[message.Speaker][targetStr]++
			}
		}
	}

	return matrix
}

func (se *SimulationExtractor) identifyConversationStarters(conversation *ConversationData) []string {
	starters := []string{}
	if len(conversation.Messages) > 0 {
		starters = append(starters, conversation.Messages[0].Speaker)
	}
	return starters
}

func (se *SimulationExtractor) findMostResponsiveAgent(conversation *ConversationData) string {
	if len(conversation.Participants) == 0 {
		return ""
	}

	responseCounts := make(map[string]int)
	for _, message := range conversation.Messages {
		responseCounts[message.Speaker]++
	}

	maxResponses := 0
	mostResponsive := ""
	for agent, count := range responseCounts {
		if count > maxResponses {
			maxResponses = count
			mostResponsive = agent
		}
	}

	return mostResponsive
}

func (se *SimulationExtractor) calculateInteractionFrequency(conversation *ConversationData) map[string]float64 {
	frequency := make(map[string]float64)
	totalMessages := float64(len(conversation.Messages))

	for _, participant := range conversation.Participants {
		count := 0
		for _, message := range conversation.Messages {
			if message.Speaker == participant {
				count++
			}
		}
		frequency[participant] = float64(count) / totalMessages
	}

	return frequency
}

func (se *SimulationExtractor) findMostActiveAgent(data *MetricsData) string {
	maxMessages := 0
	mostActive := ""

	for agent, metric := range data.AgentMetrics {
		if metric.MessageCount > maxMessages {
			maxMessages = metric.MessageCount
			mostActive = agent
		}
	}

	return mostActive
}
