# TinyTroupe Go Makefile

.PHONY: build test clean demo lint deps help

# Go parameters
GOCMD=go
GOBUILD=$(GOCMD) build
GOCLEAN=$(GOCMD) clean
GOTEST=$(GOCMD) test
GOGET=$(GOCMD) get
GOMOD=$(GOCMD) mod
GOFMT=gofmt
GOVET=$(GOCMD) vet

# Build targets
DEMO_BINARY=./bin/demo
DEMO_SOURCE=./cmd/demo
EXAMPLES_BINARY=./bin/agent_creation
EXAMPLES_SOURCE=./examples

# Default target
all: deps test build

## help: Display this help message
help:
	@echo "Available targets:"
	@grep -E '^##.*:' $(MAKEFILE_LIST) | sed 's/##\s*\([^:]*\):\s*\(.*\)/  \1: \2/'

## deps: Download dependencies  
deps:
	@echo "Ensuring Go module mode is enabled..."
	@if echo "$$PWD" | grep -q "$$(go env GOPATH)"; then \
		echo "WARNING: Current directory is inside GOPATH ($$GOPATH)"; \
		echo "Forcing module mode by setting different GOPATH..."; \
		GOPATH=/tmp/gopath-temp GO111MODULE=on $(GOMOD) download; \
		GOPATH=/tmp/gopath-temp GO111MODULE=on $(GOMOD) tidy; \
		echo "✅ Dependencies downloaded successfully (warnings about go.mod in GOPATH are now resolved)"; \
	else \
		$(GOMOD) download; \
		$(GOMOD) tidy; \
		echo "✅ Dependencies downloaded successfully"; \
	fi

## build: Build all binaries
build: deps
	mkdir -p bin
	$(GOBUILD) -o $(DEMO_BINARY) $(DEMO_SOURCE)
	$(GOBUILD) -o $(EXAMPLES_BINARY) examples/agent_creation.go
	$(GOBUILD) -o ./bin/simple_chat examples/simple_chat.go
	$(GOBUILD) -o ./bin/agent_validation examples/agent_validation.go
	$(GOBUILD) -o ./bin/product_brainstorming examples/product_brainstorming.go
	$(GOBUILD) -o ./bin/synthetic_data_generation examples/synthetic_data_generation.go
	$(GOBUILD) -o ./bin/ab_testing examples/ab_testing.go
	$(GOBUILD) -o ./bin/simple_openai_example examples/simple_openai_example.go
	$(GOBUILD) -o ./bin/document_creation examples/document_creation.go

## test: Run tests
test:
	$(GOTEST) -v ./pkg/... ./cmd/...

## test-coverage: Run tests with coverage
test-coverage:
	$(GOTEST) -v -coverprofile=coverage.out ./pkg/... ./cmd/...
	$(GOCMD) tool cover -html=coverage.out -o coverage.html
	@echo "Coverage report generated: coverage.html"

## lint: Run linters
lint:
	$(GOFMT) -l -s .
	$(GOVET) ./...

## format: Format code
format:
	$(GOFMT) -l -s -w .

## examples: Run all example programs
examples: build
	@echo "=== Running TinyTroupe Go Examples ==="
	@echo ""
	@echo "1. Agent Creation Example:"
	$(EXAMPLES_BINARY)
	@echo ""
	@echo "2. Simple Chat Example:"
	./bin/simple_chat
	@echo ""
	@echo "3. Agent Validation Example:"
	./bin/agent_validation
	@echo ""
	@echo "4. Product Brainstorming Example:"
	./bin/product_brainstorming
	@echo ""
	@echo "5. Synthetic Data Generation Example:"
	./bin/synthetic_data_generation
	@echo ""
	@echo "6. A/B Testing Example:"
	./bin/ab_testing
	@echo ""
	@echo "=== All Examples Complete ==="

## demo: Run the demo (requires OPENAI_API_KEY)
demo: build
	@if [ -z "$(OPENAI_API_KEY)" ]; then \
		echo "Error: OPENAI_API_KEY environment variable is required"; \
		echo "Please set it with: export OPENAI_API_KEY=your_key_here"; \
		exit 1; \
	fi
	$(DEMO_BINARY)

## clean: Clean build artifacts
clean:
	$(GOCLEAN)
	rm -rf bin/
	rm -f coverage.out coverage.html

## check: Run all checks (format, lint, test)
check: format lint test

## init: Initialize project dependencies
init:
	@echo "Initializing Go module..."
	@if echo "$$PWD" | grep -q "$$(go env GOPATH)"; then \
		echo "WARNING: Current directory is inside GOPATH ($$GOPATH)"; \
		echo "Forcing module mode for initialization..."; \
		GOPATH=/tmp/gopath-temp GO111MODULE=on $(GOMOD) init github.com/microsoft/TinyTroupe/go || true; \
		GOPATH=/tmp/gopath-temp GO111MODULE=on $(GOGET) github.com/sashabaranov/go-openai; \
	else \
		$(GOMOD) init github.com/microsoft/TinyTroupe/go || true; \
		$(GOGET) github.com/sashabaranov/go-openai; \
	fi

## docker-build: Build Docker image
docker-build:
	docker build -t tinytroupe-go .

## docker-run: Run Docker container (requires OPENAI_API_KEY)
docker-run:
	docker run --rm -e OPENAI_API_KEY=$(OPENAI_API_KEY) tinytroupe-go

## analyze-deps: Analyze dependencies for a module (usage: make analyze-deps MODULE=pkg/agent)
analyze-deps:
	@if [ -z "$(MODULE)" ]; then \
		echo "Usage: make analyze-deps MODULE=pkg/module-name"; \
		echo "Example: make analyze-deps MODULE=pkg/agent"; \
		exit 1; \
	fi
	go run cmd/analyze-deps/analyze-deps.go $(MODULE)

## compare-apis: Compare APIs between two modules (usage: make compare-apis OLD=pkg/old NEW=pkg/new)
compare-apis:
	@if [ -z "$(OLD)" ] || [ -z "$(NEW)" ]; then \
		echo "Usage: make compare-apis OLD=pkg/old-module NEW=pkg/new-module"; \
		echo "Example: make compare-apis OLD=pkg/agent NEW=pkg/agent_v2"; \
		exit 1; \
	fi
	go run cmd/compare-apis/compare-apis.go $(OLD) $(NEW)

## migration-status: Show migration status for all modules
migration-status:
	@echo "📊 TinyTroupe Go Migration Status"
	@echo "=================================="
	@echo ""
	@echo "✅ Phase 0 (Complete):"
	@echo "  • pkg/agent"
	@echo "  • pkg/config"
	@echo "  • pkg/environment"
	@echo "  • pkg/memory"
	@echo "  • pkg/openai"
	@echo ""
	@echo "🆕 Phase 1 (Foundation):"
	@echo "  • pkg/control - Interface defined"
	@echo "  • pkg/factory - Complete"
	@echo "  • pkg/utils - Complete"
	@echo "  • pkg/validation - Complete"
	@echo ""
	@echo "🚧 Phase 2 (Advanced):"
	@echo "  • pkg/enrichment - Placeholder"
	@echo "  • pkg/extraction - Placeholder"
	@echo "  • pkg/tools - Placeholder"
	@echo "  • pkg/profiling - Placeholder"
	@echo ""
	@echo "⏳ Phase 3 (UX):"
	@echo "  • pkg/ui - Placeholder"
	@echo "  • pkg/steering - Placeholder"
	@echo "  • pkg/experimentation - Placeholder"

# Development targets
.PHONY: dev-setup env-check env-fix
dev-setup: env-check deps
	@echo "Development environment setup complete"
	@echo "Run 'make help' to see available commands"

## env-check: Check Go environment configuration
env-check:
	@echo "=== Go Environment Check ==="
	@echo "Go version: $$(go version)"
	@echo "GOROOT: $$(go env GOROOT)"
	@echo "GOPATH: $$(go env GOPATH)"
	@echo "Current directory: $$PWD"
	@echo "Module mode: $$(go env GO111MODULE)"
	@if echo "$$PWD" | grep -q "$$(go env GOPATH)"; then \
		echo "⚠️  WARNING: Project is inside GOPATH - this may cause module issues"; \
		echo "   Consider running 'make env-fix' or moving project outside GOPATH"; \
	else \
		echo "✅ Project location is good (outside GOPATH)"; \
	fi
	@echo "=========================="

## env-fix: Fix common Go environment issues
env-fix:
	@echo "=== Fixing Go Environment ==="
	@echo "Setting GO111MODULE=on to force module mode..."
	@echo "export GO111MODULE=on" >> ~/.bashrc || echo "export GO111MODULE=on" >> ~/.zshrc || true
	@echo "✅ Added GO111MODULE=on to shell config"
	@echo "💡 Recommended: Move project outside GOPATH or unset GOPATH"
	@echo "   Run: export GOPATH=\"\" or move to ~/projects/tinytroupe-go"
	@echo "=========================="