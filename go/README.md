# TinyTroupe Go

A Go port of Microsoft's [TinyTroupe](https://github.com/microsoft/TinyTroupe) - an LLM-powered multiagent persona simulation toolkit for imagination enhancement and business insights.

## Table of Contents
- [About](#about)
- [Key Features](#key-features)
- [Getting Started](#getting-started)
- [Examples](#examples)
- [Sample Runs](#sample-runs)
- [Project Status](#project-status)
- [Development](#development)
- [Contributing](#contributing)
- [License](#license)

## About

TinyTroupe allows simulation of people with specific personalities, interests, and goals using Large Language Models (LLMs). This Go port aims to provide the same capabilities with Go's performance and concurrency benefits, enabling you to create AI-powered simulations for business insights, product testing, and creative applications.

### Why Go?

- **Performance**: Better memory management and execution speed
- **Concurrency**: Leverage Go's goroutines for parallel agent simulation
- **Type Safety**: Compile-time error detection and stronger guarantees
- **Deployment**: Single binary deployment with no runtime dependencies
- **Ecosystem**: Rich standard library and growing AI/ML ecosystem

## Key Features

### Core Components
- **TinyPerson**: Simulated agents with detailed personas, memories, and behaviors
- **TinyWorld**: Environments where agents can interact and evolve
- **Memory Management**: Sophisticated memory systems with consolidation and retrieval
- **Agent Factories**: Template-based agent creation with validation
- **Simulation Control**: Advanced orchestration and lifecycle management

### Business Applications
- **Advertisement Evaluation**: Test marketing messages with simulated audiences
- **Software Testing**: Generate diverse user scenarios and feedback
- **Product Development**: Brainstorm ideas and validate concepts
- **Market Research**: Simulate focus groups and customer interviews
- **Document Creation**: Generate business proposals, reports, and strategic content
- **Synthetic Data Generation**: Create realistic datasets for training and testing

### Technical Features
- **Multi-Provider LLM Support**: OpenAI, Azure OpenAI, and extensible for others
- **Concurrent Execution**: Parallel agent processing using goroutines
- **Structured Configuration**: Environment-based configuration with validation
- **Comprehensive Testing**: High test coverage with benchmarks
- **Developer Tools**: Migration utilities, dependency analysis, and profiling

## Getting Started

### Prerequisites
- Go 1.20 or later
- OpenAI API key or Azure OpenAI credentials (for LLM-powered examples)

### Installation

```bash
# Clone the repository
git clone https://github.com/microsoft/TinyTroupe
cd TinyTroupe/go

# Install dependencies
make deps

# Run tests
make test

# Build all examples
make build
```

### Configuration

For examples that use actual LLMs, set your OpenAI API key:
```bash
export OPENAI_API_KEY=your_openai_api_key_here
```

Or copy and edit the example configuration:
```bash
cp config.example.env .env
# Edit .env with your configuration
```

### Quick Start

#### 1. Run the Demo
```bash
# Interactive demo (requires API key)
make demo
```

#### 2. Run All Examples
```bash
# Run all example programs
make examples
```

#### 3. Programmatic Usage
```go
package main

import (
    "context"
    "fmt"
    "github.com/microsoft/TinyTroupe/go/pkg/agent"
    "github.com/microsoft/TinyTroupe/go/pkg/config"
    "github.com/microsoft/TinyTroupe/go/pkg/environment"
)

func main() {
    cfg := config.DefaultConfig()
    
    // Create agents with personas
    alice := agent.NewTinyPerson("Alice", cfg)
    alice.Define("age", 25)
    alice.Define("occupation", "Software Engineer")
    alice.Define("interests", []string{"AI", "music", "cooking"})
    
    bob := agent.NewTinyPerson("Bob", cfg)
    bob.Define("age", 30)
    bob.Define("occupation", "Data Scientist")
    bob.Define("interests", []string{"machine learning", "hiking"})
    
    // Create world and setup interaction
    world := environment.NewTinyWorld("Office", cfg)
    world.AddAgent(alice)
    world.AddAgent(bob)
    world.MakeEveryoneAccessible()
    
    // Start conversation
    ctx := context.Background()
    alice.ListenAndAct(ctx, "Hi Bob, how's your day going?", nil)
    
    // Run simulation for 3 steps
    world.Run(ctx, 3, nil)
}
```

## Examples

This repository includes comprehensive examples demonstrating various TinyTroupe capabilities:

| Example | Description | Key Features |
|---------|-------------|--------------|
| [`simple_chat.go`](examples/simple_chat.go) | Basic conversation between two agents | Agent interaction, environment setup |
| [`agent_creation.go`](examples/agent_creation.go) | Different ways to create and configure agents | JSON loading, programmatic creation |
| [`agent_validation.go`](examples/agent_validation.go) | Agent validation and error handling | Validation system, error recovery |
| [`product_brainstorming.go`](examples/product_brainstorming.go) | Multi-agent product ideation session | Collaborative thinking, idea generation |
| [`synthetic_data_generation.go`](examples/synthetic_data_generation.go) | Generate synthetic user data | Data extraction, pattern generation |
| [`ab_testing.go`](examples/ab_testing.go) | A/B testing with simulated users | Experimental design, statistical analysis |
| [`document_creation.go`](examples/document_creation.go) | Document creation using agent tools | Tool integration, business content generation |

### Agent Assets
- **Pre-defined Agents**: [`examples/agents/`](examples/agents/) contains ready-to-use agent personas
- **Business Personas**: [`examples/personas/`](examples/personas/) provides detailed business role templates
- **Agent Fragments**: [`examples/fragments/`](examples/fragments/) provides personality components for customization

### Python Examples Migration Status
The following Python notebook examples are planned for Go implementation:

| Python Notebook | Go Example | Status |
|------------------|------------|--------|
| Simple Chat.ipynb | ✅ `simple_chat.go` | Complete |
| Creating and Validating Agents.ipynb | ✅ `agent_validation.go` | Complete |
| Product Brainstorming.ipynb | ✅ `product_brainstorming.go` | Complete |
| Synthetic Data Generation.ipynb | ✅ `synthetic_data_generation.go` | Complete |
| A/B Testing scenarios | ✅ `ab_testing.go` | Complete |
| Bottled Gazpacho Market Research | 🚧 `gazpacho_market_research.go` | Planned |
| Travel Product Market Research | 🚧 `travel_market_research.go` | Planned |
| Story telling (long narratives) | 🚧 `story_telling.go` | Planned |

## Sample Runs

Explore the [`examples/sample-runs/`](examples/sample-runs/) directory to see actual output from each example:

- [`simple_chat.log`](examples/sample-runs/simple_chat.log) - Basic agent conversation
- [`agent_creation.log`](examples/sample-runs/agent_creation.log) - Agent creation patterns
- [`agent_validation.log`](examples/sample-runs/agent_validation.log) - Validation scenarios
- [`product_brainstorming.log`](examples/sample-runs/product_brainstorming.log) - Multi-agent brainstorming
- [`synthetic_data_generation.log`](examples/sample-runs/synthetic_data_generation.log) - Data generation output
- [`ab_testing.log`](examples/sample-runs/ab_testing.log) - A/B testing results
- [`document_creation.log`](examples/sample-runs/document_creation.log) - Tool-based document generation

These logs show the exact output you can expect when running the examples and demonstrate the simulation capabilities.

## Project Status

🚧 **Work in Progress** - This is an active port implementing core functionality with high fidelity to the original Python implementation.

### ✅ Implemented (Core Foundation)
- **Agent System**: TinyPerson with personas, memory, and behavior
- **Environment System**: TinyWorld with agent interaction and state management
- **Memory Management**: Episodic memory with retrieval and consolidation
- **Configuration**: Environment-based config with validation
- **LLM Integration**: OpenAI and Azure OpenAI support
- **Agent Factories**: Template-based creation with JSON support
- **Validation System**: Comprehensive input and agent state validation
- **Tool Integration**: Document creation, data export, and agent tool system
- **Business Personas**: Rich templates for realistic business simulations
- **Utilities**: String manipulation, logging, time handling, random generation

### 🚧 In Progress (Advanced Features)
- **Enrichment System**: Data augmentation and context enhancement
- **Performance Profiling**: Monitoring and bottleneck identification
- **Advanced Tool Ecosystem**: Extended tool library and integrations

### ⏳ Planned (User Experience)
- **UI Components**: Web interface and visualization tools
- **Behavior Steering**: Real-time modification and control
- **Experimentation Framework**: A/B testing and hypothesis testing
- **Advanced Examples**: Complex multi-agent scenarios

See [`MIGRATION_PLAN.md`](MIGRATION_PLAN.md) for detailed technical migration roadmap and implementation phases.

## Development

### Project Structure
```
pkg/
├── agent/          # TinyPerson implementation and behaviors
├── config/         # Configuration management
├── control/        # Simulation control and orchestration  
├── environment/    # TinyWorld and environment management
├── factory/        # Agent creation patterns and templates
├── memory/         # Memory systems and consolidation
├── openai/         # LLM provider integration
├── tools/          # Agent tool system and implementations
├── utils/          # Common utilities and helpers
├── validation/     # Input validation and error handling
└── ...            # Additional modules (see MIGRATION_PLAN.md)
```

### Development Commands
```bash
# Install dependencies
make deps

# Run tests with coverage
make test-coverage

# Lint and format code
make lint
make format

# Build all binaries
make build

# Run all examples
make examples

# Migration utilities
make analyze-deps MODULE=pkg/agent
make migration-status
```

### Quality Standards
- **Test Coverage**: >80% for all modules
- **Linting**: Code passes `golangci-lint` checks
- **Documentation**: All public APIs documented
- **Error Handling**: Explicit error handling with typed errors
- **Performance**: Benchmarks and profiling for optimization

### Migration Tools
For developers working on the Python-to-Go migration:

```bash
# Analyze module dependencies
make analyze-deps MODULE=pkg/module-name

# Create new module with template
./scripts/migrate-module.sh new-module 2

# Compare API compatibility
make compare-apis OLD=pkg/old NEW=pkg/new

# Check overall migration status
make migration-status
```

## Contributing

This project welcomes contributions! Whether you're:
- Porting features from the Python implementation
- Adding Go-specific optimizations
- Improving documentation and examples
- Fixing bugs or adding tests

### Getting Started with Contributing
1. Check the [migration plan](MIGRATION_PLAN.md) for priority areas
2. Fork the repository and create a feature branch
3. Follow the existing code patterns and quality standards
4. Add tests for any new functionality
5. Update documentation as needed
6. Submit a pull request with a clear description

### Reference
- Original TinyTroupe: https://github.com/microsoft/TinyTroupe
- Python documentation and examples for feature reference
- Go best practices: https://golang.org/doc/effective_go.html

## License

MIT License - same as the original TinyTroupe project.

This project maintains compatibility with the original TinyTroupe while leveraging Go's strengths for better performance, type safety, and deployment simplicity.