# Sample Runs

This directory contains output logs from running all the TinyTroupe Go examples. These logs demonstrate the actual behavior and output you can expect when running the examples.

## Available Sample Runs

| Example | Log File | Description |
|---------|----------|-------------|
| Agent Creation | [`agent_creation.log`](agent_creation.log) | Shows different methods of creating and configuring agents |
| Simple Chat | [`simple_chat.log`](simple_chat.log) | LLM-driven conversation between two agents using the OpenAI API |
| Agent Validation | [`agent_validation.log`](agent_validation.log) | Shows validation scenarios and error handling |
| Product Brainstorming | [`product_brainstorming.log`](product_brainstorming.log) | Multi-agent collaborative brainstorming session |
| Synthetic Data Generation | [`synthetic_data_generation.log`](synthetic_data_generation.log) | Generates synthetic user data and profiles |
| A/B Testing | [`ab_testing.log`](ab_testing.log) | Simulates A/B testing scenarios with multiple user personas |

## How to Generate Your Own

To regenerate these logs or create new ones:

```bash
# Build all examples
make build

# Run individual example and capture output
go run examples/simple_chat.go > examples/sample-runs/simple_chat.log 2>&1

# Or run all examples
make examples
```

## Notes

- The **Simple Chat** example uses the OpenAI API and requires an `OPENAI_API_KEY` environment variable
- The **Simple Chat** log captures detailed OpenAI API errors to help diagnose issues like missing or invalid keys
- Other examples run entirely in simulation mode and do not require API keys
- The output includes timestamps, agent interactions, and simulation results
- Each log shows the complete execution flow from setup to completion
- The logs demonstrate TinyTroupe's agent-based simulation capabilities

## Sample Output Format

Each log typically includes:
- Example initialization and setup
- Agent loading and configuration
- Environment creation and agent placement
- Simulation execution with agent interactions
- Results summary and completion status

For the latest examples and to run them yourself, see the main [examples directory](../).
