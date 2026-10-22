#!/bin/bash

# migrate-module.sh - Template for creating new TinyTroupe Go modules
# Usage: ./scripts/migrate-module.sh <module-name> <phase>

set -e

MODULE_NAME="$1"
PHASE="$2"

if [ -z "$MODULE_NAME" ]; then
    echo "Usage: $0 <module-name> <phase>"
    echo "Example: $0 control 1"
    exit 1
fi

if [ -z "$PHASE" ]; then
    PHASE="1"
fi

# Module directory
MODULE_DIR="pkg/$MODULE_NAME"

# Check if module already exists
if [ -d "$MODULE_DIR" ]; then
    echo "Module $MODULE_NAME already exists at $MODULE_DIR"
    exit 1
fi

echo "Creating module: $MODULE_NAME (Phase $PHASE)"

# Create module directory
mkdir -p "$MODULE_DIR"

# Create basic Go file
cat > "$MODULE_DIR/$MODULE_NAME.go" << EOF
// Package $MODULE_NAME provides [MODULE_DESCRIPTION].
// This module is part of Phase $PHASE of the Python to Go migration plan.
package $MODULE_NAME

// TODO: This package is part of Phase $PHASE migration.
// Implement the functionality based on the original Python TinyTroupe module.

// [MODULE_NAME_CAPITALIZED]Interface defines the main interface for this module
type ${MODULE_NAME^}Interface interface {
	// TODO: Define interface methods
}

// ${MODULE_NAME^}Config holds configuration for this module
type ${MODULE_NAME^}Config struct {
	// TODO: Define configuration fields
}

// Default${MODULE_NAME^}Config returns default configuration
func Default${MODULE_NAME^}Config() *${MODULE_NAME^}Config {
	return &${MODULE_NAME^}Config{
		// TODO: Set default values
	}
}
EOF

# Create basic test file
cat > "$MODULE_DIR/${MODULE_NAME}_test.go" << EOF
package $MODULE_NAME

import (
	"testing"
)

func TestDefault${MODULE_NAME^}Config(t *testing.T) {
	config := Default${MODULE_NAME^}Config()
	if config == nil {
		t.Error("Expected non-nil config")
	}
}

// TODO: Add more tests as functionality is implemented
EOF

echo "✅ Created module $MODULE_NAME at $MODULE_DIR"
echo "📝 Next steps:"
echo "   1. Edit $MODULE_DIR/$MODULE_NAME.go to implement functionality"
echo "   2. Add comprehensive tests to $MODULE_DIR/${MODULE_NAME}_test.go"
echo "   3. Update go.mod if new dependencies are needed"
echo "   4. Run 'make test' to verify implementation"
echo "   5. Update MIGRATION_PLAN.md to track progress"