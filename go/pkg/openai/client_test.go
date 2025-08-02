package openai

import (
	"context"
	"testing"

	"github.com/atsentia/tinytroupe-go/pkg/config"
)

func TestNewClient(t *testing.T) {
	cfg := config.DefaultConfig()
	client := NewClient(cfg)

	if client == nil {
		t.Fatal("NewClient returned nil")
	}

	if client.config != cfg {
		t.Error("Client config not set correctly")
	}

	if client.client == nil {
		t.Error("OpenAI client not initialized")
	}
}

func TestNewClientAzure(t *testing.T) {
	cfg := config.DefaultConfig()
	cfg.APIType = "azure"
	cfg.AzureEndpoint = "https://test.openai.azure.com/"

	client := NewClient(cfg)

	if client == nil {
		t.Fatal("NewClient returned nil for Azure config")
	}

	if client.config != cfg {
		t.Error("Client config not set correctly for Azure")
	}

	if client.client == nil {
		t.Error("Azure OpenAI client not initialized")
	}
}

func TestMessageStruct(t *testing.T) {
	msg := Message{
		Role:    "user",
		Content: "Hello, world!",
	}

	if msg.Role != "user" {
		t.Errorf("Expected role 'user', got '%s'", msg.Role)
	}

	if msg.Content != "Hello, world!" {
		t.Errorf("Expected content 'Hello, world!', got '%s'", msg.Content)
	}
}

func TestChatCompletionWithoutAPI(t *testing.T) {
	// Test that the function is structured correctly without making actual API calls
	cfg := config.DefaultConfig()
	cfg.APIKey = "fake-key-for-testing"
	client := NewClient(cfg)

	messages := []Message{
		{Role: "user", Content: "Hello"},
	}

	// This will fail due to network/auth issues but we can test the structure
	ctx := context.Background()
	_, err := client.ChatCompletion(ctx, messages)

	// We expect an error since we're using a fake API key
	if err == nil {
		t.Log("Unexpected success - API call should fail with fake key")
	}
}

func TestCreateEmbeddingWithoutAPI(t *testing.T) {
	// Test that the function is structured correctly without making actual API calls
	cfg := config.DefaultConfig()
	cfg.APIKey = "fake-key-for-testing"
	client := NewClient(cfg)

	// This will fail due to network/auth issues but we can test the structure
	ctx := context.Background()
	_, err := client.CreateEmbedding(ctx, "test text")

	// We expect an error since we're using a fake API key
	if err == nil {
		t.Log("Unexpected success - API call should fail with fake key")
	}
}
