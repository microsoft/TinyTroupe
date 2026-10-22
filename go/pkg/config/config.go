package config

import (
	"bufio"
	"os"
	"strconv"
	"strings"
	"time"
)

// Config holds all configuration values for TinyTroupe
type Config struct {
	// OpenAI Configuration
	APIType          string
	APIKey           string
	AzureEndpoint    string
	Model            string
	EmbeddingModel   string
	MaxTokens        int
	Temperature      float64
	TopP             float64
	FrequencyPenalty float64
	PresencePenalty  float64
	Timeout          time.Duration
	MaxAttempts      int

	// Simulation Configuration
	ParallelAgentActions bool

	// Memory Configuration
	EnableMemoryConsolidation bool
	MinEpisodeLength          int
	MaxEpisodeLength          int

	// Logging
	LogLevel string

	// Display
	MaxContentDisplayLength int
}

// LoadEnvFile loads environment variables from a .env file
func LoadEnvFile(filename string) error {
	file, err := os.Open(filename)
	if err != nil {
		return err
	}
	defer file.Close()

	scanner := bufio.NewScanner(file)
	for scanner.Scan() {
		line := strings.TrimSpace(scanner.Text())
		if line == "" || strings.HasPrefix(line, "#") {
			continue
		}

		parts := strings.SplitN(line, "=", 2)
		if len(parts) != 2 {
			continue
		}

		key := strings.TrimSpace(parts[0])
		value := strings.TrimSpace(parts[1])
		
		// Remove quotes if present
		if (strings.HasPrefix(value, "\"") && strings.HasSuffix(value, "\"")) ||
			(strings.HasPrefix(value, "'") && strings.HasSuffix(value, "'")) {
			value = value[1 : len(value)-1]
		}

		os.Setenv(key, value)
	}

	return scanner.Err()
}

// DefaultConfig returns the default configuration
func DefaultConfig() *Config {
	// Try to load .env file automatically
	LoadEnvFile(".env")
	
	return defaultConfigInternal()
}

// DefaultConfigWithoutEnv returns default config without loading .env
func DefaultConfigWithoutEnv() *Config {
	return defaultConfigInternal()
}

// defaultConfigInternal contains the actual config creation logic
func defaultConfigInternal() *Config {
	return &Config{
		APIType:                   getEnvOrDefault("TINYTROUPE_API_TYPE", "openai"),
		APIKey:                    os.Getenv("OPENAI_API_KEY"),
		AzureEndpoint:             os.Getenv("AZURE_OPENAI_ENDPOINT"),
		Model:                     getEnvOrDefault("TINYTROUPE_MODEL", "gpt-4o-mini"),
		EmbeddingModel:            getEnvOrDefault("TINYTROUPE_EMBEDDING_MODEL", "text-embedding-3-small"),
		MaxTokens:                 getEnvIntOrDefault("TINYTROUPE_MAX_TOKENS", 1024),
		Temperature:               getEnvFloatOrDefault("TINYTROUPE_TEMPERATURE", 1.0),
		TopP:                      getEnvFloatOrDefault("TINYTROUPE_TOP_P", 1.0),
		FrequencyPenalty:          getEnvFloatOrDefault("TINYTROUPE_FREQ_PENALTY", 0.0),
		PresencePenalty:           getEnvFloatOrDefault("TINYTROUPE_PRESENCE_PENALTY", 0.0),
		Timeout:                   time.Duration(getEnvIntOrDefault("TINYTROUPE_TIMEOUT", 30)) * time.Second,
		MaxAttempts:               getEnvIntOrDefault("TINYTROUPE_MAX_ATTEMPTS", 3),
		ParallelAgentActions:      getEnvBoolOrDefault("TINYTROUPE_PARALLEL_ACTIONS", true),
		EnableMemoryConsolidation: getEnvBoolOrDefault("TINYTROUPE_ENABLE_MEMORY_CONSOLIDATION", true),
		MinEpisodeLength:          getEnvIntOrDefault("TINYTROUPE_MIN_EPISODE_LENGTH", 15),
		MaxEpisodeLength:          getEnvIntOrDefault("TINYTROUPE_MAX_EPISODE_LENGTH", 50),
		LogLevel:                  getEnvOrDefault("TINYTROUPE_LOG_LEVEL", "INFO"),
		MaxContentDisplayLength:   getEnvIntOrDefault("TINYTROUPE_MAX_CONTENT_DISPLAY_LENGTH", 1024),
	}
}

// getEnvOrDefault returns environment variable value or default
func getEnvOrDefault(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}

// getEnvIntOrDefault returns environment variable as int or default
func getEnvIntOrDefault(key string, defaultValue int) int {
	if value := os.Getenv(key); value != "" {
		if intValue, err := strconv.Atoi(value); err == nil {
			return intValue
		}
	}
	return defaultValue
}

// getEnvFloatOrDefault returns environment variable as float64 or default
func getEnvFloatOrDefault(key string, defaultValue float64) float64 {
	if value := os.Getenv(key); value != "" {
		if floatValue, err := strconv.ParseFloat(value, 64); err == nil {
			return floatValue
		}
	}
	return defaultValue
}

// getEnvBoolOrDefault returns environment variable as bool or default
func getEnvBoolOrDefault(key string, defaultValue bool) bool {
	if value := os.Getenv(key); value != "" {
		if boolValue, err := strconv.ParseBool(value); err == nil {
			return boolValue
		}
	}
	return defaultValue
}
