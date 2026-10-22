package config

import (
	"os"
	"testing"
	"time"
)

func TestDefaultConfig(t *testing.T) {
	cfg := DefaultConfig()

	if cfg.Model != "gpt-4o-mini" {
		t.Errorf("Expected default model 'gpt-4o-mini', got '%s'", cfg.Model)
	}

	if cfg.MaxTokens != 1024 {
		t.Errorf("Expected default max tokens 1024, got %d", cfg.MaxTokens)
	}

	if cfg.Temperature != 1.0 {
		t.Errorf("Expected default temperature 1.0, got %f", cfg.Temperature)
	}

	if cfg.ParallelAgentActions != true {
		t.Errorf("Expected parallel agent actions to be true by default")
	}
}

func TestEnvironmentVariableOverrides(t *testing.T) {
	// Set environment variables
	os.Setenv("TINYTROUPE_MODEL", "gpt-4")
	os.Setenv("TINYTROUPE_MAX_TOKENS", "2048")
	os.Setenv("TINYTROUPE_TEMPERATURE", "0.5")
	os.Setenv("TINYTROUPE_PARALLEL_ACTIONS", "false")

	defer func() {
		// Clean up
		os.Unsetenv("TINYTROUPE_MODEL")
		os.Unsetenv("TINYTROUPE_MAX_TOKENS")
		os.Unsetenv("TINYTROUPE_TEMPERATURE")
		os.Unsetenv("TINYTROUPE_PARALLEL_ACTIONS")
	}()

	cfg := DefaultConfig()

	if cfg.Model != "gpt-4" {
		t.Errorf("Expected model override 'gpt-4', got '%s'", cfg.Model)
	}

	if cfg.MaxTokens != 2048 {
		t.Errorf("Expected max tokens override 2048, got %d", cfg.MaxTokens)
	}

	if cfg.Temperature != 0.5 {
		t.Errorf("Expected temperature override 0.5, got %f", cfg.Temperature)
	}

	if cfg.ParallelAgentActions != false {
		t.Errorf("Expected parallel agent actions override to be false")
	}
}

func TestTimeoutParsing(t *testing.T) {
	os.Setenv("TINYTROUPE_TIMEOUT", "60")
	defer os.Unsetenv("TINYTROUPE_TIMEOUT")

	cfg := DefaultConfig()
	expected := 60 * time.Second

	if cfg.Timeout != expected {
		t.Errorf("Expected timeout %v, got %v", expected, cfg.Timeout)
	}
}
