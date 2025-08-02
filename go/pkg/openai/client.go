package openai

import (
	"context"
	"errors"
	"fmt"
	"log"
	"time"

	"github.com/atsentia/tinytroupe-go/pkg/config"
	"github.com/sashabaranov/go-openai"
)

// Client wraps the OpenAI client with TinyTroupe-specific functionality
type Client struct {
	client *openai.Client
	config *config.Config
}

// NewClient creates a new OpenAI client
func NewClient(cfg *config.Config) *Client {
	var client *openai.Client

	if cfg.APIType == "azure" {
		clientConfig := openai.DefaultAzureConfig(cfg.APIKey, cfg.AzureEndpoint)
		client = openai.NewClientWithConfig(clientConfig)
	} else {
		client = openai.NewClient(cfg.APIKey)
	}

	return &Client{
		client: client,
		config: cfg,
	}
}

// ContentPart represents a part of message content
type ContentPart struct {
	Type string `json:"type"`
	Text string `json:"text"`
}

// MessageContent can be either a string or an array of ContentParts
type MessageContent interface{}

// Message represents a conversation message with flexible content
type Message struct {
	Role    string         `json:"role"`
	Content MessageContent `json:"content"`
}

// NewSimpleMessage creates a message with simple string content
func NewSimpleMessage(role, content string) Message {
	return Message{
		Role:    role,
		Content: content,
	}
}

// NewComplexMessage creates a message with structured content
func NewComplexMessage(role, text string) Message {
	return Message{
		Role: role,
		Content: []ContentPart{
			{Type: "text", Text: text},
		},
	}
}

// ResponseFormat represents the response format configuration
type ResponseFormat struct {
	Type string `json:"type"`
}

// ChatCompletionOptions provides additional options for chat completion
type ChatCompletionOptions struct {
	ResponseFormat       *ResponseFormat `json:"response_format,omitempty"`
	Tools               []interface{}   `json:"tools,omitempty"`
	MaxCompletionTokens *int            `json:"max_completion_tokens,omitempty"`
}

// ChatResponse represents the response from a chat completion
type ChatResponse struct {
	Content string
	Usage   openai.Usage
}

// ChatCompletion sends a chat completion request
func (c *Client) ChatCompletion(ctx context.Context, messages []Message) (*ChatResponse, error) {
	return c.ChatCompletionWithOptions(ctx, messages, nil)
}

// ChatCompletionWithOptions sends a chat completion request with additional options
func (c *Client) ChatCompletionWithOptions(ctx context.Context, messages []Message, options *ChatCompletionOptions) (*ChatResponse, error) {
	// Convert our messages to OpenAI format
	openaiMessages := make([]openai.ChatCompletionMessage, len(messages))
	for i, msg := range messages {
		openaiMsg := openai.ChatCompletionMessage{
			Role: msg.Role,
		}
		
		// Handle different content types
		switch content := msg.Content.(type) {
		case string:
			openaiMsg.Content = content
		case []ContentPart:
			// Convert ContentParts to OpenAI format
			parts := make([]openai.ChatMessagePart, len(content))
			for j, part := range content {
				parts[j] = openai.ChatMessagePart{
					Type: openai.ChatMessagePartType(part.Type),
					Text: part.Text,
				}
			}
			openaiMsg.MultiContent = parts
		default:
			return nil, fmt.Errorf("unsupported content type: %T", content)
		}
		
		openaiMessages[i] = openaiMsg
	}

	req := openai.ChatCompletionRequest{
		Model:            c.config.Model,
		Messages:         openaiMessages,
		Temperature:      float32(c.config.Temperature),
		TopP:             float32(c.config.TopP),
		FrequencyPenalty: float32(c.config.FrequencyPenalty),
		PresencePenalty:  float32(c.config.PresencePenalty),
	}
	
	// Handle max tokens - prefer MaxCompletionTokens if provided in options
	if options != nil && options.MaxCompletionTokens != nil {
		req.MaxTokens = *options.MaxCompletionTokens
	} else {
		req.MaxTokens = c.config.MaxTokens
	}
	
	// Add optional parameters if provided
	if options != nil {
		if options.ResponseFormat != nil {
			// Note: The go-openai library may need to be updated to support response_format
			// This is a placeholder for when the library supports it
		}
		if len(options.Tools) > 0 {
			// Note: Tools support would need to be added here when the library supports it
		}
	}

	// Add timeout to context
	timeoutCtx, cancel := context.WithTimeout(ctx, c.config.Timeout)
	defer cancel()

	// Retry logic
	var resp openai.ChatCompletionResponse
	var err error

	for attempt := 0; attempt < c.config.MaxAttempts; attempt++ {
		resp, err = c.client.CreateChatCompletion(timeoutCtx, req)
		if err == nil {
			break
		}

		var apiErr *openai.APIError
		if errors.As(err, &apiErr) {
			log.Printf("OpenAI API error (attempt %d/%d): type=%s code=%v msg=%s",
				attempt+1, c.config.MaxAttempts, apiErr.Type, apiErr.Code, apiErr.Message)
		} else {
			log.Printf("OpenAI request failed (attempt %d/%d): %v",
				attempt+1, c.config.MaxAttempts, err)
		}

		if attempt < c.config.MaxAttempts-1 {
			// Exponential backoff
			waitTime := time.Duration(attempt+1) * time.Second
			log.Printf("Retrying in %v", waitTime)
			time.Sleep(waitTime)
		}
	}

	if err != nil {
		return nil, fmt.Errorf("openai request failed after %d attempts: %w", c.config.MaxAttempts, err)
	}

	if len(resp.Choices) == 0 {
		return nil, fmt.Errorf("no choices returned from OpenAI")
	}

	return &ChatResponse{
		Content: resp.Choices[0].Message.Content,
		Usage:   resp.Usage,
	}, nil
}

// CreateEmbedding creates an embedding for the given text
func (c *Client) CreateEmbedding(ctx context.Context, text string) ([]float32, error) {
	req := openai.EmbeddingRequest{
		Input: []string{text},
		Model: openai.EmbeddingModel(c.config.EmbeddingModel),
	}

	timeoutCtx, cancel := context.WithTimeout(ctx, c.config.Timeout)
	defer cancel()

	resp, err := c.client.CreateEmbeddings(timeoutCtx, req)
	if err != nil {
		return nil, fmt.Errorf("embedding request failed: %w", err)
	}

	if len(resp.Data) == 0 {
		return nil, fmt.Errorf("no embeddings returned")
	}

	return resp.Data[0].Embedding, nil
}
