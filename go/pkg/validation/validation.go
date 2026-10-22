// Package validation provides input validation and error handling utilities
// for the TinyTroupe Go implementation.
package validation

import (
	"fmt"
	"net/url"
	"reflect"
	"regexp"
	"strconv"
	"strings"
	"time"
)

// Validator interface defines validation capabilities
type Validator interface {
	Validate(value interface{}) error
}

// ValidationError represents a validation error
type ValidationError struct {
	Field   string
	Value   interface{}
	Message string
}

// Error implements the error interface
func (ve *ValidationError) Error() string {
	return fmt.Sprintf("validation failed for field '%s': %s (value: %v)", ve.Field, ve.Message, ve.Value)
}

// ValidationErrors represents multiple validation errors
type ValidationErrors []ValidationError

// Error implements the error interface
func (ves ValidationErrors) Error() string {
	if len(ves) == 0 {
		return ""
	}
	if len(ves) == 1 {
		return ves[0].Error()
	}

	var messages []string
	for _, ve := range ves {
		messages = append(messages, ve.Error())
	}
	return fmt.Sprintf("multiple validation errors: %s", strings.Join(messages, "; "))
}

// IsEmpty checks if ValidationErrors is empty
func (ves ValidationErrors) IsEmpty() bool {
	return len(ves) == 0
}

// StringValidator validates string values
type StringValidator struct {
	MinLength     int
	MaxLength     int
	Pattern       *regexp.Regexp
	AllowedValues []string
	Required      bool
}

// Validate implements Validator interface
func (sv *StringValidator) Validate(value interface{}) error {
	str, ok := value.(string)
	if !ok {
		return &ValidationError{
			Value:   value,
			Message: "value must be a string",
		}
	}

	if sv.Required && str == "" {
		return &ValidationError{
			Value:   value,
			Message: "value is required and cannot be empty",
		}
	}

	if sv.MinLength > 0 && len(str) < sv.MinLength {
		return &ValidationError{
			Value:   value,
			Message: fmt.Sprintf("string length must be at least %d characters", sv.MinLength),
		}
	}

	if sv.MaxLength > 0 && len(str) > sv.MaxLength {
		return &ValidationError{
			Value:   value,
			Message: fmt.Sprintf("string length must not exceed %d characters", sv.MaxLength),
		}
	}

	if sv.Pattern != nil && !sv.Pattern.MatchString(str) {
		return &ValidationError{
			Value:   value,
			Message: fmt.Sprintf("string does not match required pattern: %s", sv.Pattern.String()),
		}
	}

	if len(sv.AllowedValues) > 0 {
		for _, allowed := range sv.AllowedValues {
			if str == allowed {
				return nil
			}
		}
		return &ValidationError{
			Value:   value,
			Message: fmt.Sprintf("value must be one of: %s", strings.Join(sv.AllowedValues, ", ")),
		}
	}

	return nil
}

// NumberValidator validates numeric values
type NumberValidator struct {
	Min      *float64
	Max      *float64
	Required bool
}

// Validate implements Validator interface
func (nv *NumberValidator) Validate(value interface{}) error {
	if value == nil {
		if nv.Required {
			return &ValidationError{
				Value:   value,
				Message: "value is required",
			}
		}
		return nil
	}

	var num float64
	switch v := value.(type) {
	case int:
		num = float64(v)
	case int32:
		num = float64(v)
	case int64:
		num = float64(v)
	case float32:
		num = float64(v)
	case float64:
		num = v
	case string:
		var err error
		num, err = strconv.ParseFloat(v, 64)
		if err != nil {
			return &ValidationError{
				Value:   value,
				Message: "value must be a valid number",
			}
		}
	default:
		return &ValidationError{
			Value:   value,
			Message: "value must be a number",
		}
	}

	if nv.Min != nil && num < *nv.Min {
		return &ValidationError{
			Value:   value,
			Message: fmt.Sprintf("value must be at least %g", *nv.Min),
		}
	}

	if nv.Max != nil && num > *nv.Max {
		return &ValidationError{
			Value:   value,
			Message: fmt.Sprintf("value must not exceed %g", *nv.Max),
		}
	}

	return nil
}

// EmailValidator validates email values using a simple regex pattern
type EmailValidator struct {
	Required bool
}

// Validate implements Validator interface
func (ev *EmailValidator) Validate(value interface{}) error {
	str, ok := value.(string)
	if !ok {
		return &ValidationError{
			Value:   value,
			Message: "value must be a string",
		}
	}

	if str == "" {
		if ev.Required {
			return &ValidationError{
				Value:   value,
				Message: "email is required",
			}
		}
		return nil
	}

	// Simple email regex pattern - basic validation
	emailPattern := regexp.MustCompile(`^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$`)
	if !emailPattern.MatchString(str) {
		return &ValidationError{
			Value:   value,
			Message: "value must be a valid email address",
		}
	}

	// Additional checks for common invalid patterns
	if strings.Contains(str, "..") || strings.Contains(str, " ") {
		return &ValidationError{
			Value:   value,
			Message: "value must be a valid email address",
		}
	}

	return nil
}

// URLValidator validates URL values
type URLValidator struct {
	RequireHTTPS bool
	Required     bool
}

// Validate implements Validator interface
func (uv *URLValidator) Validate(value interface{}) error {
	str, ok := value.(string)
	if !ok {
		return &ValidationError{
			Value:   value,
			Message: "value must be a string",
		}
	}

	if str == "" {
		if uv.Required {
			return &ValidationError{
				Value:   value,
				Message: "URL is required",
			}
		}
		return nil
	}

	u, err := url.Parse(str)
	if err != nil {
		return &ValidationError{
			Value:   value,
			Message: "value must be a valid URL",
		}
	}

	if u.Scheme == "" {
		return &ValidationError{
			Value:   value,
			Message: "URL must include a scheme (http:// or https://)",
		}
	}

	if uv.RequireHTTPS && u.Scheme != "https" {
		return &ValidationError{
			Value:   value,
			Message: "URL must use HTTPS",
		}
	}

	return nil
}

// TimeValidator validates time values
type TimeValidator struct {
	After    *time.Time
	Before   *time.Time
	Required bool
}

// Validate implements Validator interface
func (tv *TimeValidator) Validate(value interface{}) error {
	if value == nil {
		if tv.Required {
			return &ValidationError{
				Value:   value,
				Message: "time value is required",
			}
		}
		return nil
	}

	var t time.Time
	switch v := value.(type) {
	case time.Time:
		t = v
	case string:
		var err error
		t, err = time.Parse(time.RFC3339, v)
		if err != nil {
			return &ValidationError{
				Value:   value,
				Message: "time must be in RFC3339 format",
			}
		}
	default:
		return &ValidationError{
			Value:   value,
			Message: "value must be a time.Time or RFC3339 string",
		}
	}

	if tv.After != nil && t.Before(*tv.After) {
		return &ValidationError{
			Value:   value,
			Message: fmt.Sprintf("time must be after %s", tv.After.Format(time.RFC3339)),
		}
	}

	if tv.Before != nil && t.After(*tv.Before) {
		return &ValidationError{
			Value:   value,
			Message: fmt.Sprintf("time must be before %s", tv.Before.Format(time.RFC3339)),
		}
	}

	return nil
}

// StructValidator validates struct fields using tags
type StructValidator struct{}

// Validate validates a struct using field tags
func (sv *StructValidator) Validate(value interface{}) error {
	v := reflect.ValueOf(value)
	if v.Kind() == reflect.Ptr {
		v = v.Elem()
	}

	if v.Kind() != reflect.Struct {
		return &ValidationError{
			Value:   value,
			Message: "value must be a struct",
		}
	}

	var errors ValidationErrors
	t := v.Type()

	for i := 0; i < v.NumField(); i++ {
		field := v.Field(i)
		fieldType := t.Field(i)

		// Skip unexported fields
		if !field.CanInterface() {
			continue
		}

		tag := fieldType.Tag.Get("validate")
		if tag == "" {
			continue
		}

		err := sv.validateField(fieldType.Name, field.Interface(), tag)
		if err != nil {
			if ve, ok := err.(*ValidationError); ok {
				ve.Field = fieldType.Name
				errors = append(errors, *ve)
			} else if ves, ok := err.(ValidationErrors); ok {
				for _, ve := range ves {
					ve.Field = fieldType.Name
					errors = append(errors, ve)
				}
			}
		}
	}

	if len(errors) > 0 {
		return errors
	}

	return nil
}

// validateField validates a single field based on validation tags
func (sv *StructValidator) validateField(fieldName string, value interface{}, tag string) error {
	rules := strings.Split(tag, ",")

	for _, rule := range rules {
		rule = strings.TrimSpace(rule)
		if rule == "" {
			continue
		}

		parts := strings.SplitN(rule, "=", 2)
		ruleName := parts[0]
		ruleValue := ""
		if len(parts) == 2 {
			ruleValue = parts[1]
		}

		err := sv.validateRule(value, ruleName, ruleValue)
		if err != nil {
			return err
		}
	}

	return nil
}

// validateRule applies a specific validation rule
func (sv *StructValidator) validateRule(value interface{}, ruleName, ruleValue string) error {
	switch ruleName {
	case "required":
		if value == nil || (reflect.ValueOf(value).Kind() == reflect.String && value.(string) == "") {
			return &ValidationError{
				Value:   value,
				Message: "field is required",
			}
		}
	case "min":
		min, err := strconv.ParseFloat(ruleValue, 64)
		if err != nil {
			return &ValidationError{
				Value:   value,
				Message: "invalid min validation rule",
			}
		}
		validator := &NumberValidator{Min: &min}
		return validator.Validate(value)
	case "max":
		max, err := strconv.ParseFloat(ruleValue, 64)
		if err != nil {
			return &ValidationError{
				Value:   value,
				Message: "invalid max validation rule",
			}
		}
		validator := &NumberValidator{Max: &max}
		return validator.Validate(value)
	case "minlen":
		minLen, err := strconv.Atoi(ruleValue)
		if err != nil {
			return &ValidationError{
				Value:   value,
				Message: "invalid minlen validation rule",
			}
		}
		validator := &StringValidator{MinLength: minLen}
		return validator.Validate(value)
	case "maxlen":
		maxLen, err := strconv.Atoi(ruleValue)
		if err != nil {
			return &ValidationError{
				Value:   value,
				Message: "invalid maxlen validation rule",
			}
		}
		validator := &StringValidator{MaxLength: maxLen}
		return validator.Validate(value)
	case "url":
		validator := &URLValidator{}
		return validator.Validate(value)
	case "https":
		validator := &URLValidator{RequireHTTPS: true}
		return validator.Validate(value)
	case "email":
		validator := &EmailValidator{}
		return validator.Validate(value)
	}

	return nil
}

// Common validator instances
var (
	RequiredString = &StringValidator{Required: true}
	RequiredNumber = &NumberValidator{Required: true}
	RequiredURL    = &URLValidator{Required: true}
	RequiredEmail  = &EmailValidator{Required: true}
	HTTPSOnly      = &URLValidator{RequireHTTPS: true, Required: true}
	Struct         = &StructValidator{}
)

// Helper functions
func Min(value float64) *float64 {
	return &value
}

func Max(value float64) *float64 {
	return &value
}

func After(t time.Time) *time.Time {
	return &t
}

func Before(t time.Time) *time.Time {
	return &t
}
