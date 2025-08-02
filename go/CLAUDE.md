# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

TinyTroupe Go is a Go port of Microsoft's TinyTroupe - an LLM-powered multiagent persona simulation toolkit. It enables simulation of people with specific personalities, interests, and goals using Large Language Models for business insights, product testing, and creative applications.

## Architecture

### Core Components
- **`pkg/agent/`** - TinyPerson implementation with personas, memory, and behaviors
- **`pkg/environment/`** - TinyWorld simulation environments where agents interact  
- **`pkg/memory/`** - Episodic memory systems with retrieval and consolidation
- **`pkg/openai/`** - LLM provider integration (OpenAI, Azure OpenAI)
- **`pkg/config/`** - Environment-based configuration management
- **`pkg/factory/`** - Agent creation patterns and JSON template loading
- **`pkg/validation/`** - Input validation and error handling

### Key Types
- **TinyPerson**: Simulated agents with `Persona` (traits) and `MentalState` (current context)
- **TinyWorld**: Environment managing agent interactions and simulation state
- **Action**: Structured actions agents can take (TALK, THINK, etc.)

### Examples Structure
- **`examples/`** - Complete demonstration programs showing different use cases
- **`examples/agents/`** - Pre-defined agent personas in JSON format
- **`examples/fragments/`** - Personality components for agent customization
- **`examples/sample-runs/`** - Actual output logs from running examples

## Prerequisites

### Go Installation
```bash
# macOS (Homebrew)
brew install go

# Verify installation
go version
```

## Key Commands

### Development
```bash
# Install dependencies
make deps

# Build all examples and demo
make build

# Run tests with coverage
make test-coverage

# Lint and format code  
make lint
make format

# Run all quality checks
make check
```

### Running Examples
```bash
# Run all examples sequentially
make examples

# Run individual examples
./bin/simple_chat
./bin/agent_creation
./bin/product_brainstorming
./bin/synthetic_data_generation
./bin/ab_testing
./bin/simple_openai_example  # Direct OpenAI API example

# Interactive demo (requires OPENAI_API_KEY)
make demo
```

### Testing
```bash
# Run all tests
make test

# Test specific package
go test -v ./pkg/agent/...

# Run with coverage report
make test-coverage
```

### Migration Tools
```bash
# Analyze module dependencies
make analyze-deps MODULE=pkg/agent

# Compare API compatibility
make compare-apis OLD=pkg/old NEW=pkg/new

# Show migration status
make migration-status
```

## Configuration

### Environment Variables
- **OPENAI_API_KEY**: Required for LLM-powered examples
- **AZURE_OPENAI_ENDPOINT**: For Azure OpenAI usage
- **AZURE_OPENAI_KEY**: Azure OpenAI API key

### Config Files
- **config.example.env**: Template configuration file
- Load with `config.DefaultConfig()` or from environment

## Agent Development Patterns

### Creating Agents Programmatically
```go
cfg := config.DefaultConfig()
alice := agent.NewTinyPerson("Alice", cfg)
alice.Define("age", 25)
alice.Define("occupation", "Software Engineer")
alice.Define("interests", []string{"AI", "music"})
```

### Loading from JSON
```go
agent, err := factory.LoadAgentFromJSON("examples/agents/lisa.json", cfg)
```

### Environment Setup
```go
world := environment.NewTinyWorld("Office", cfg)
world.AddAgent(alice)
world.AddAgent(bob)
world.MakeEveryoneAccessible()
```

## Migration Status

### ✅ Complete (Phase 0-1)
- Core agent system with personas and mental state
- Environment simulation with TinyWorld
- Memory management and consolidation
- OpenAI/Azure OpenAI integration
- Configuration and validation systems
- Agent factories and JSON loading
- Comprehensive examples and documentation

### 🚧 In Progress (Phase 2)
- **pkg/enrichment/**: Data augmentation and context enhancement
- **pkg/extraction/**: Analytics, reporting, and export capabilities  
- **pkg/tools/**: External tool usage and instrumentation
- **pkg/profiling/**: Performance monitoring

### ⏳ Planned (Phase 3)
- **pkg/ui/**: Web interface and visualization
- **pkg/steering/**: Real-time agent behavior modification
- **pkg/experimentation/**: A/B testing framework

## Important Notes

- All examples work without API keys (using mock responses) but require OPENAI_API_KEY for actual LLM interaction
- Agent personalities and behaviors are defined in JSON files under `examples/agents/`
- The project maintains API compatibility with the original Python TinyTroupe where possible
- Use `make migration-status` to see current implementation progress
- Test coverage target is >80% for all modules