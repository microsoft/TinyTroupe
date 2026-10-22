package utils

import (
	"strings"
	"testing"
	"time"
)

func TestStringUtils(t *testing.T) {
	// Test TruncateString
	result := Strings.TruncateString("Hello World", 5)
	if result != "He..." {
		t.Errorf("Expected 'He...', got '%s'", result)
	}

	// Test short string
	result = Strings.TruncateString("Hi", 10)
	if result != "Hi" {
		t.Errorf("Expected 'Hi', got '%s'", result)
	}

	// Test NormalizeSpaces
	result = Strings.NormalizeSpaces("  Hello    World  ")
	if result != "Hello World" {
		t.Errorf("Expected 'Hello World', got '%s'", result)
	}

	// Test ToCamelCase
	result = Strings.ToCamelCase("hello world test")
	if result != "helloWorldTest" {
		t.Errorf("Expected 'helloWorldTest', got '%s'", result)
	}

	// Test ToSnakeCase
	result = Strings.ToSnakeCase("HelloWorldTest")
	if result != "hello_world_test" {
		t.Errorf("Expected 'hello_world_test', got '%s'", result)
	}
}

func TestFileUtils(t *testing.T) {
	// Test JoinPath
	path := Files.JoinPath("home", "user", "documents")
	// On Windows, this might be different, but for testing we'll use forward slashes
	if !strings.Contains(path, "user") || !strings.Contains(path, "documents") {
		t.Errorf("Path join failed: got '%s'", path)
	}

	// Test GetTempDir
	tempDir := Files.GetTempDir()
	if tempDir == "" {
		t.Error("Expected non-empty temp directory")
	}
}

func TestTimeUtils(t *testing.T) {
	// Test FormatDuration
	tests := []struct {
		duration time.Duration
		contains string
	}{
		{100 * time.Millisecond, "ms"},
		{5 * time.Second, "s"},
		{2 * time.Minute, "m"},
		{1 * time.Hour, "h"},
	}

	for _, test := range tests {
		result := Times.FormatDuration(test.duration)
		if !strings.Contains(result, test.contains) {
			t.Errorf("Expected duration '%v' to contain '%s', got '%s'", test.duration, test.contains, result)
		}
	}

	// Test ParseDuration with days
	duration, err := Times.ParseDuration("2d")
	if err != nil {
		t.Errorf("Failed to parse '2d': %v", err)
	}
	expected := 48 * time.Hour
	if duration != expected {
		t.Errorf("Expected %v, got %v", expected, duration)
	}

	// Test GetCurrentTimestamp
	timestamp := Times.GetCurrentTimestamp()
	if timestamp == "" {
		t.Error("Expected non-empty timestamp")
	}

	// Verify it's a valid RFC3339 timestamp
	_, err = time.Parse(time.RFC3339, timestamp)
	if err != nil {
		t.Errorf("Invalid timestamp format: %v", err)
	}
}

func TestRandomUtils(t *testing.T) {
	// Test GenerateID
	id := Random.GenerateID(16)
	if len(id) != 16 {
		t.Errorf("Expected ID length 16, got %d", len(id))
	}

	// Test PickRandom with string slice
	slice := []string{"a", "b", "c"}
	result, err := Random.PickRandom(slice)
	if err != nil {
		t.Errorf("Failed to pick random: %v", err)
	}

	str, ok := result.(string)
	if !ok {
		t.Error("Expected string result")
	}

	found := false
	for _, item := range slice {
		if item == str {
			found = true
			break
		}
	}
	if !found {
		t.Errorf("Random pick '%s' not found in original slice", str)
	}

	// Test PickRandom with empty slice
	empty := []string{}
	_, err = Random.PickRandom(empty)
	if err == nil {
		t.Error("Expected error for empty slice")
	}

	// Test PickRandom with non-slice
	_, err = Random.PickRandom("not a slice")
	if err == nil {
		t.Error("Expected error for non-slice")
	}
}

func TestConversionUtils(t *testing.T) {
	// Test ToString
	tests := []struct {
		input    interface{}
		expected string
	}{
		{"hello", "hello"},
		{42, "42"},
		{3.14, "3.14"},
		{true, "true"},
		{nil, ""},
	}

	for _, test := range tests {
		result := Conversions.ToString(test.input)
		if result != test.expected {
			t.Errorf("ToString(%v): expected '%s', got '%s'", test.input, test.expected, result)
		}
	}

	// Test ToStringMap
	stringMap := map[string]interface{}{"key": "value"}
	result, err := Conversions.ToStringMap(stringMap)
	if err != nil {
		t.Errorf("Failed to convert string map: %v", err)
	}
	if result["key"] != "value" {
		t.Errorf("Expected 'value', got '%v'", result["key"])
	}

	// Test ToStringMap with interface{} keys
	interfaceMap := map[interface{}]interface{}{"key": "value"}
	result, err = Conversions.ToStringMap(interfaceMap)
	if err != nil {
		t.Errorf("Failed to convert interface map: %v", err)
	}
	if result["key"] != "value" {
		t.Errorf("Expected 'value', got '%v'", result["key"])
	}

	// Test ToStringMap with invalid input
	_, err = Conversions.ToStringMap("not a map")
	if err == nil {
		t.Error("Expected error for invalid input")
	}
}

func TestDefaultLogger(t *testing.T) {
	logger := NewLogger("test")

	// These don't return anything, just ensure they don't panic
	logger.Debug("Debug message")
	logger.Info("Info message")
	logger.Warn("Warning message")
	logger.Error("Error message")
}
