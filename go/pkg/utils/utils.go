// Package utils provides common utilities and helper functions
// for the TinyTroupe Go implementation.
package utils

import (
	"crypto/rand"
	"encoding/hex"
	"fmt"
	"log"
	"os"
	"path/filepath"
	"reflect"
	"strconv"
	"strings"
	"time"
)

// Logger provides a structured logging interface
type Logger interface {
	Debug(msg string, args ...interface{})
	Info(msg string, args ...interface{})
	Warn(msg string, args ...interface{})
	Error(msg string, args ...interface{})
}

// DefaultLogger is a simple logger implementation
type DefaultLogger struct {
	prefix string
}

// NewLogger creates a new logger with the given prefix
func NewLogger(prefix string) *DefaultLogger {
	return &DefaultLogger{prefix: prefix}
}

// Debug logs a debug message
func (l *DefaultLogger) Debug(msg string, args ...interface{}) {
	log.Printf("[DEBUG][%s] %s", l.prefix, fmt.Sprintf(msg, args...))
}

// Info logs an info message
func (l *DefaultLogger) Info(msg string, args ...interface{}) {
	log.Printf("[INFO][%s] %s", l.prefix, fmt.Sprintf(msg, args...))
}

// Warn logs a warning message
func (l *DefaultLogger) Warn(msg string, args ...interface{}) {
	log.Printf("[WARN][%s] %s", l.prefix, fmt.Sprintf(msg, args...))
}

// Error logs an error message
func (l *DefaultLogger) Error(msg string, args ...interface{}) {
	log.Printf("[ERROR][%s] %s", l.prefix, fmt.Sprintf(msg, args...))
}

// StringUtils provides string manipulation utilities
type StringUtils struct{}

// TruncateString truncates a string to the specified length
func (StringUtils) TruncateString(s string, maxLen int) string {
	if len(s) <= maxLen {
		return s
	}
	if maxLen <= 3 {
		return s[:maxLen]
	}
	return s[:maxLen-3] + "..."
}

// NormalizeSpaces replaces multiple consecutive spaces with a single space
func (StringUtils) NormalizeSpaces(s string) string {
	return strings.Join(strings.Fields(s), " ")
}

// ToCamelCase converts a string to camelCase
func (StringUtils) ToCamelCase(s string) string {
	words := strings.Fields(strings.ToLower(s))
	if len(words) == 0 {
		return ""
	}

	result := words[0]
	for i := 1; i < len(words); i++ {
		result += strings.Title(words[i])
	}
	return result
}

// ToSnakeCase converts a string to snake_case
func (StringUtils) ToSnakeCase(s string) string {
	var result strings.Builder
	for i, r := range s {
		if i > 0 && 'A' <= r && r <= 'Z' {
			result.WriteByte('_')
		}
		result.WriteRune(r)
	}
	return strings.ToLower(result.String())
}

// FileUtils provides file system utilities
type FileUtils struct{}

// EnsureDir ensures that a directory exists, creating it if necessary
func (FileUtils) EnsureDir(dirPath string) error {
	return os.MkdirAll(dirPath, 0755)
}

// FileExists checks if a file exists
func (FileUtils) FileExists(filePath string) bool {
	_, err := os.Stat(filePath)
	return !os.IsNotExist(err)
}

// GetFileSize returns the size of a file in bytes
func (FileUtils) GetFileSize(filePath string) (int64, error) {
	info, err := os.Stat(filePath)
	if err != nil {
		return 0, err
	}
	return info.Size(), nil
}

// GetTempDir returns a temporary directory path
func (FileUtils) GetTempDir() string {
	return os.TempDir()
}

// JoinPath joins path elements
func (FileUtils) JoinPath(elements ...string) string {
	return filepath.Join(elements...)
}

// TimeUtils provides time-related utilities
type TimeUtils struct{}

// FormatDuration formats a duration in a human-readable way
func (TimeUtils) FormatDuration(d time.Duration) string {
	if d < time.Second {
		return fmt.Sprintf("%.0fms", d.Seconds()*1000)
	}
	if d < time.Minute {
		return fmt.Sprintf("%.1fs", d.Seconds())
	}
	if d < time.Hour {
		return fmt.Sprintf("%.1fm", d.Minutes())
	}
	return fmt.Sprintf("%.1fh", d.Hours())
}

// ParseDuration parses a duration string with support for additional units
func (TimeUtils) ParseDuration(s string) (time.Duration, error) {
	// First try standard parsing
	d, err := time.ParseDuration(s)
	if err == nil {
		return d, nil
	}

	// Try parsing with additional units
	if strings.HasSuffix(s, "d") {
		days, err := strconv.ParseFloat(s[:len(s)-1], 64)
		if err != nil {
			return 0, err
		}
		return time.Duration(days * 24 * float64(time.Hour)), nil
	}

	return 0, err
}

// GetCurrentTimestamp returns the current timestamp as a string
func (TimeUtils) GetCurrentTimestamp() string {
	return time.Now().Format(time.RFC3339)
}

// RandomUtils provides random generation utilities
type RandomUtils struct{}

// GenerateID generates a random hex ID of the specified length
func (RandomUtils) GenerateID(length int) string {
	bytes := make([]byte, length/2)
	if _, err := rand.Read(bytes); err != nil {
		// Fallback to timestamp-based ID if random fails
		return fmt.Sprintf("%d", time.Now().UnixNano())
	}
	return hex.EncodeToString(bytes)
}

// PickRandom picks a random element from a slice
func (RandomUtils) PickRandom(slice interface{}) (interface{}, error) {
	v := reflect.ValueOf(slice)
	if v.Kind() != reflect.Slice {
		return nil, fmt.Errorf("argument must be a slice")
	}

	if v.Len() == 0 {
		return nil, fmt.Errorf("slice is empty")
	}

	bytes := make([]byte, 1)
	if _, err := rand.Read(bytes); err != nil {
		return nil, err
	}

	index := int(bytes[0]) % v.Len()
	return v.Index(index).Interface(), nil
}

// ConversionUtils provides type conversion utilities
type ConversionUtils struct{}

// ToStringMap converts a map[string]interface{} safely
func (ConversionUtils) ToStringMap(m interface{}) (map[string]interface{}, error) {
	switch v := m.(type) {
	case map[string]interface{}:
		return v, nil
	case map[interface{}]interface{}:
		result := make(map[string]interface{})
		for key, value := range v {
			strKey, ok := key.(string)
			if !ok {
				return nil, fmt.Errorf("key %v is not a string", key)
			}
			result[strKey] = value
		}
		return result, nil
	default:
		return nil, fmt.Errorf("cannot convert %T to map[string]interface{}", m)
	}
}

// ToString converts various types to string
func (ConversionUtils) ToString(v interface{}) string {
	switch val := v.(type) {
	case string:
		return val
	case int, int32, int64:
		return fmt.Sprintf("%d", val)
	case float32, float64:
		return fmt.Sprintf("%g", val)
	case bool:
		return strconv.FormatBool(val)
	case nil:
		return ""
	default:
		return fmt.Sprintf("%v", val)
	}
}

// Global utility instances for easy access
var (
	Strings     = StringUtils{}
	Files       = FileUtils{}
	Times       = TimeUtils{}
	Random      = RandomUtils{}
	Conversions = ConversionUtils{}
)
