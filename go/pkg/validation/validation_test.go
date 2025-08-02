package validation

import (
	"testing"
	"time"
)

func TestStringValidator(t *testing.T) {
	// Test required string
	validator := &StringValidator{Required: true}

	err := validator.Validate("")
	if err == nil {
		t.Error("Expected error for empty required string")
	}

	err = validator.Validate("valid")
	if err != nil {
		t.Errorf("Expected no error for valid string, got %v", err)
	}

	// Test min/max length
	validator = &StringValidator{MinLength: 5, MaxLength: 10}

	err = validator.Validate("sh")
	if err == nil {
		t.Error("Expected error for string too short")
	}

	err = validator.Validate("this string is too long")
	if err == nil {
		t.Error("Expected error for string too long")
	}

	err = validator.Validate("perfect")
	if err != nil {
		t.Errorf("Expected no error for valid length, got %v", err)
	}

	// Test allowed values
	validator = &StringValidator{AllowedValues: []string{"apple", "banana", "orange"}}

	err = validator.Validate("grape")
	if err == nil {
		t.Error("Expected error for disallowed value")
	}

	err = validator.Validate("apple")
	if err != nil {
		t.Errorf("Expected no error for allowed value, got %v", err)
	}

	// Test non-string input
	err = validator.Validate(123)
	if err == nil {
		t.Error("Expected error for non-string input")
	}
}

func TestNumberValidator(t *testing.T) {
	min := 0.0
	max := 100.0
	validator := &NumberValidator{Min: &min, Max: &max}

	// Test valid numbers
	err := validator.Validate(50)
	if err != nil {
		t.Errorf("Expected no error for valid int, got %v", err)
	}

	err = validator.Validate(75.5)
	if err != nil {
		t.Errorf("Expected no error for valid float, got %v", err)
	}

	err = validator.Validate("25")
	if err != nil {
		t.Errorf("Expected no error for valid string number, got %v", err)
	}

	// Test invalid range
	err = validator.Validate(-10)
	if err == nil {
		t.Error("Expected error for number below minimum")
	}

	err = validator.Validate(150)
	if err == nil {
		t.Error("Expected error for number above maximum")
	}

	// Test invalid input
	err = validator.Validate("not a number")
	if err == nil {
		t.Error("Expected error for invalid string number")
	}

	err = validator.Validate([]int{1, 2, 3})
	if err == nil {
		t.Error("Expected error for non-numeric input")
	}
}

func TestEmailValidator(t *testing.T) {
	validator := &EmailValidator{}

	// Test valid emails
	validEmails := []string{
		"test@example.com",
		"user.name@domain.co.uk",
		"first.last+tag@subdomain.example.org",
		"email123@test123.com",
	}

	for _, email := range validEmails {
		err := validator.Validate(email)
		if err != nil {
			t.Errorf("Expected no error for valid email %s, got %v", email, err)
		}
	}

	// Test invalid emails
	invalidEmails := []string{
		"invalid-email",
		"@example.com",
		"test@",
		"test..test@example.com", // Double dots
		"test @example.com",      // Space
	}

	for _, email := range invalidEmails {
		err := validator.Validate(email)
		if err == nil {
			t.Errorf("Expected error for invalid email %s", email)
		}
	}

	// Test empty string for non-required validator
	err := validator.Validate("")
	if err != nil {
		t.Errorf("Expected no error for empty non-required email, got %v", err)
	}

	// Test required email
	requiredValidator := &EmailValidator{Required: true}

	err = requiredValidator.Validate("")
	if err == nil {
		t.Error("Expected error for empty required email")
	}

	err = requiredValidator.Validate("test@example.com")
	if err != nil {
		t.Errorf("Expected no error for valid required email, got %v", err)
	}

	// Test non-string input
	err = validator.Validate(123)
	if err == nil {
		t.Error("Expected error for non-string input")
	}
}

func TestURLValidator(t *testing.T) {
	validator := &URLValidator{}

	// Test valid URLs
	err := validator.Validate("https://example.com")
	if err != nil {
		t.Errorf("Expected no error for valid HTTPS URL, got %v", err)
	}

	err = validator.Validate("http://example.com")
	if err != nil {
		t.Errorf("Expected no error for valid HTTP URL, got %v", err)
	}

	// Test invalid URLs
	err = validator.Validate("not a url")
	if err == nil {
		t.Error("Expected error for invalid URL")
	}

	err = validator.Validate("example.com")
	if err == nil {
		t.Error("Expected error for URL without scheme")
	}

	// Test HTTPS requirement
	httpsValidator := &URLValidator{RequireHTTPS: true}

	err = httpsValidator.Validate("http://example.com")
	if err == nil {
		t.Error("Expected error for HTTP URL when HTTPS required")
	}

	err = httpsValidator.Validate("https://example.com")
	if err != nil {
		t.Errorf("Expected no error for HTTPS URL, got %v", err)
	}

	// Test non-string input
	err = validator.Validate(123)
	if err == nil {
		t.Error("Expected error for non-string input")
	}
}

func TestTimeValidator(t *testing.T) {
	now := time.Now()
	after := now.Add(time.Hour)
	before := now.Add(-time.Hour)

	validator := &TimeValidator{After: &before, Before: &after}

	// Test valid time
	err := validator.Validate(now)
	if err != nil {
		t.Errorf("Expected no error for valid time, got %v", err)
	}

	// Test RFC3339 string
	err = validator.Validate(now.Format(time.RFC3339))
	if err != nil {
		t.Errorf("Expected no error for valid RFC3339 string, got %v", err)
	}

	// Test time before range
	err = validator.Validate(before.Add(-time.Hour))
	if err == nil {
		t.Error("Expected error for time before allowed range")
	}

	// Test time after range
	err = validator.Validate(after.Add(time.Hour))
	if err == nil {
		t.Error("Expected error for time after allowed range")
	}

	// Test invalid input
	err = validator.Validate("not a time")
	if err == nil {
		t.Error("Expected error for invalid time string")
	}

	err = validator.Validate(123)
	if err == nil {
		t.Error("Expected error for non-time input")
	}
}

func TestStructValidator(t *testing.T) {
	type TestStruct struct {
		Name  string `validate:"required,minlen=2,maxlen=50"`
		Age   int    `validate:"required,min=0,max=150"`
		Email string `validate:"required,email"`
		URL   string `validate:"url"`
	}

	validator := &StructValidator{}

	// Test valid struct
	valid := TestStruct{
		Name:  "John Doe",
		Age:   30,
		Email: "john@example.com",
		URL:   "https://example.com",
	}

	err := validator.Validate(valid)
	if err != nil {
		t.Errorf("Expected no error for valid struct, got %v", err)
	}

	// Test invalid struct
	invalid := TestStruct{
		Name:  "",              // Required field empty
		Age:   -5,              // Below minimum
		Email: "invalid-email", // Invalid email format
		URL:   "not a url",
	}

	err = validator.Validate(invalid)
	if err == nil {
		t.Error("Expected error for invalid struct")
	}

	// Check that it's ValidationErrors
	if _, ok := err.(ValidationErrors); !ok {
		t.Errorf("Expected ValidationErrors, got %T", err)
	}

	// Test non-struct input
	err = validator.Validate("not a struct")
	if err == nil {
		t.Error("Expected error for non-struct input")
	}
}

func TestValidationErrors(t *testing.T) {
	errors := ValidationErrors{
		ValidationError{Field: "field1", Message: "error1"},
		ValidationError{Field: "field2", Message: "error2"},
	}

	if errors.IsEmpty() {
		t.Error("Expected ValidationErrors to not be empty")
	}

	errorMsg := errors.Error()
	if errorMsg == "" {
		t.Error("Expected non-empty error message")
	}

	// Test empty ValidationErrors
	empty := ValidationErrors{}
	if !empty.IsEmpty() {
		t.Error("Expected empty ValidationErrors to be empty")
	}

	if empty.Error() != "" {
		t.Error("Expected empty error message for empty ValidationErrors")
	}
}

func TestHelperFunctions(t *testing.T) {
	// Test Min/Max helpers
	min := Min(10.5)
	if min == nil || *min != 10.5 {
		t.Errorf("Expected Min to return pointer to 10.5, got %v", min)
	}

	max := Max(100.0)
	if max == nil || *max != 100.0 {
		t.Errorf("Expected Max to return pointer to 100.0, got %v", max)
	}

	// Test After/Before helpers
	now := time.Now()
	after := After(now)
	if after == nil || !after.Equal(now) {
		t.Errorf("Expected After to return pointer to time, got %v", after)
	}

	before := Before(now)
	if before == nil || !before.Equal(now) {
		t.Errorf("Expected Before to return pointer to time, got %v", before)
	}
}
