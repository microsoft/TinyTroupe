# Installation Guide

This guide covers installation and setup for TinyTroupe Go, a Go port of Microsoft's TinyTroupe multiagent persona simulation toolkit.

## Prerequisites

### Go Installation

**macOS (Homebrew):**
```bash
brew install go
```

**Other platforms:**
Download and install Go from [golang.org](https://golang.org/dl/)

**Verify installation:**
```bash
go version
```

## Project Setup

### 1. Clone the Repository and go to correct directory
```bash
git clone https://github.com/microsoft/TinyTroupe.git
cd TinyTroupe/go
```

### 2. Environment Check (Important!)
```bash
make env-check
```

This will check for potential Go environment issues. If you see warnings about GOPATH, run:
```bash
make env-fix
```

### 3. Install Dependencies
```bash
make deps
```

**The Makefile automatically handles GOPATH issues** - if your project is located within your `$GOPATH` directory, it will automatically use a workaround to ensure module mode works correctly.

### 4. Build the Project
```bash
make build
```

### 5. Run Tests
```bash
make test
```

## Configuration

### Environment Variables

For LLM-powered functionality, set up your API credentials:

**OpenAI:**
```bash
export OPENAI_API_KEY="your-api-key-here"
```

**Azure OpenAI:**
```bash
export AZURE_OPENAI_ENDPOINT="your-endpoint"
export AZURE_OPENAI_KEY="your-azure-key"
```

### Configuration File

Copy the example configuration:
```bash
cp config.example.env config.env
```

Edit `config.env` with your specific settings.

## Verification

### Testing OpenAI Integration

After setting up your `.env` file with `OPENAI_API_KEY`, test the integration with these recommended examples:

**1. Simple OpenAI API Test:**
```bash
# Direct OpenAI API call - fastest test
./bin/simple_openai_example
```

**2. Basic Agent Functionality:**
```bash
# Create and examine agents (works without API key)
./bin/agent_creation

# LLM-powered agent conversation (requires API key)
./bin/simple_chat
```

**3. Advanced Examples:**
```bash
# Run all examples
make examples

# Individual advanced examples
./bin/product_brainstorming
./bin/synthetic_data_generation
./bin/ab_testing
```

### Interactive Demo
```bash
make demo
```

**Note:** Examples work with mock responses without API keys, but require `OPENAI_API_KEY` for actual LLM interaction. Start with `simple_openai_example` to verify your API setup.

## Development Setup

### Code Quality Tools
```bash
# Install linting tools
make lint

# Format code
make format

# Run all quality checks
make check
```

### Testing
```bash
# Run tests with coverage
make test-coverage

# Test specific package
go test -v ./pkg/agent/...
```

## Troubleshooting

### Common Issues

1. **Missing Go modules:** Run `make deps` to install dependencies
2. **Build failures:** Ensure Go version is 1.19 or higher  
3. **API errors:** Verify your `OPENAI_API_KEY` is set correctly
4. **Test failures:** Check that all dependencies are installed
5. **GOPATH warnings:** If you see `go: warning: ignoring go.mod in $GOPATH`, run `make env-check` followed by `make env-fix`. The Makefile automatically handles this issue, but you can also manually resolve it by moving the project outside `$GOPATH` or setting `export GOPATH=""`

### Environment Issues

**If `make deps` fails:**
1. Run `make env-check` to diagnose the issue
2. Run `make env-fix` to apply automatic fixes
3. Try `make deps` again

**If Go modules aren't working:**
```bash
# Force module mode
export GO111MODULE=on
make deps
```

**If still having issues:**
```bash
# Check your Go environment
go env
# Look for GOPATH, GOROOT, GO111MODULE settings
```

### Getting Help

- Check the main [README.md](README.md) for usage examples
- Review [CLAUDE.md](CLAUDE.md) for development guidelines
- Run `make help` to see available commands

## Next Steps

After installation:
1. Explore the examples in `examples/`
2. Review agent definitions in `examples/agents/`
3. Try creating your own agent personas
4. Run the interactive demo to see the system in action