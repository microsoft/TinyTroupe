import logging

import pytest

logger = logging.getLogger("tinytroupe")

import sys

sys.path.insert(0, "../../tinytroupe/")
sys.path.insert(0, "../../")
sys.path.insert(0, "..")

from testing_utils import *

from tinytroupe.agent import TinyPerson
from tinytroupe.clients import client
from tinytroupe.environment import TinyWorld


def test_openai_client_cost_tracking_methods_exist(setup):
    """Test that OpenAI client has all cost tracking methods."""
    cli = client()

    assert hasattr(cli, "get_cost_stats"), "Missing get_cost_stats method"
    assert hasattr(
        cli, "pretty_print_cost_stats"
    ), "Missing pretty_print_cost_stats method"
    assert hasattr(cli, "reset_cost_stats"), "Missing reset_cost_stats method"


def test_openai_client_get_cost_stats_structure(setup):
    """Test that get_cost_stats returns the correct structure."""
    cli = client()
    stats = cli.get_cost_stats()

    assert isinstance(stats, dict), "get_cost_stats should return a dict"
    assert "input_tokens" in stats, "Missing input_tokens in stats"
    assert "output_tokens" in stats, "Missing output_tokens in stats"
    assert "total_tokens" in stats, "Missing total_tokens in stats"
    assert "model_calls" in stats, "Missing model_calls in stats"
    assert "cached_calls" in stats, "Missing cached_calls in stats"

    # All values should be non-negative integers
    for key in [
        "input_tokens",
        "output_tokens",
        "total_tokens",
        "model_calls",
        "cached_calls",
    ]:
        assert isinstance(stats[key], int), f"{key} should be an integer"
        assert stats[key] >= 0, f"{key} should be non-negative"


def test_openai_client_reset_cost_stats(setup):
    """Test that reset_cost_stats works correctly."""
    cli = client()

    # Reset and verify all stats are zero
    cli.reset_cost_stats()
    stats = cli.get_cost_stats()

    assert stats["input_tokens"] == 0, "input_tokens should be 0 after reset"
    assert stats["output_tokens"] == 0, "output_tokens should be 0 after reset"
    assert stats["total_tokens"] == 0, "total_tokens should be 0 after reset"
    assert stats["model_calls"] == 0, "model_calls should be 0 after reset"
    assert stats["cached_calls"] == 0, "cached_calls should be 0 after reset"


def test_tinyworld_cost_tracking_methods_exist(setup):
    """Test that TinyWorld has all cost tracking methods."""
    world = TinyWorld("TestWorld")

    # Instance methods
    assert hasattr(world, "get_cost_stats"), "Missing get_cost_stats instance method"
    assert hasattr(
        world, "pretty_print_cost_stats"
    ), "Missing pretty_print_cost_stats instance method"

    # Static methods
    assert hasattr(
        TinyWorld, "get_global_cost_stats"
    ), "Missing get_global_cost_stats static method"
    assert hasattr(
        TinyWorld, "pretty_print_global_cost_stats"
    ), "Missing pretty_print_global_cost_stats static method"


def test_tinyworld_get_cost_stats_structure(setup):
    """Test that TinyWorld.get_cost_stats returns the correct structure."""
    world = TinyWorld("TestWorld")
    stats = world.get_cost_stats()

    assert isinstance(stats, dict), "get_cost_stats should return a dict"
    assert "base_stats" in stats, "Missing base_stats in stats"
    assert "num_agents" in stats, "Missing num_agents in stats"
    assert "num_steps" in stats, "Missing num_steps in stats"

    # base_stats should have the client structure
    assert isinstance(stats["base_stats"], dict), "base_stats should be a dict"
    assert "input_tokens" in stats["base_stats"], "Missing input_tokens in base_stats"
    assert "output_tokens" in stats["base_stats"], "Missing output_tokens in base_stats"
    assert "total_tokens" in stats["base_stats"], "Missing total_tokens in base_stats"
    assert "model_calls" in stats["base_stats"], "Missing model_calls in base_stats"
    assert "cached_calls" in stats["base_stats"], "Missing cached_calls in base_stats"


def test_tinyworld_derivative_stats_calculation(setup):
    """Test that derivative statistics are calculated correctly."""
    world = TinyWorld("TestWorld")
    stats = world.get_cost_stats()

    # With no agents and no steps, derivative stats should be None
    assert stats["num_agents"] == 0, "Empty world should have 0 agents"
    assert stats["num_steps"] == 0, "New world should have 0 steps"
    assert stats["per_agent"] is None, "per_agent should be None when num_agents is 0"
    assert stats["per_step"] is None, "per_step should be None when num_steps is 0"
    assert (
        stats["per_agent_per_step"] is None
    ), "per_agent_per_step should be None when num_agents or num_steps is 0"


def test_tinyworld_global_cost_stats_structure(setup):
    """Test that TinyWorld.get_global_cost_stats returns the correct structure."""
    stats = TinyWorld.get_global_cost_stats()

    assert isinstance(stats, dict), "get_global_cost_stats should return a dict"
    assert "base_stats" in stats, "Missing base_stats in global stats"
    assert "total_agents" in stats, "Missing total_agents in global stats"
    assert "total_steps" in stats, "Missing total_steps in global stats"
    assert "total_environments" in stats, "Missing total_environments in global stats"


def test_tinyperson_cost_tracking_methods_exist(setup):
    """Test that TinyPerson has all cost tracking static methods."""
    assert hasattr(
        TinyPerson, "get_global_cost_stats"
    ), "Missing get_global_cost_stats static method"
    assert hasattr(
        TinyPerson, "pretty_print_global_cost_stats"
    ), "Missing pretty_print_global_cost_stats static method"


def test_tinyperson_get_global_cost_stats_structure(setup):
    """Test that TinyPerson.get_global_cost_stats returns the correct structure."""
    stats = TinyPerson.get_global_cost_stats()

    assert isinstance(stats, dict), "get_global_cost_stats should return a dict"
    assert "base_stats" in stats, "Missing base_stats in stats"
    assert "total_agents" in stats, "Missing total_agents in stats"

    # base_stats should have the client structure
    assert isinstance(stats["base_stats"], dict), "base_stats should be a dict"
    assert "input_tokens" in stats["base_stats"], "Missing input_tokens in base_stats"
    assert "output_tokens" in stats["base_stats"], "Missing output_tokens in base_stats"


def test_cost_tracking_with_minimal_simulation(setup):
    """Test that cost tracking works with a minimal simulation that actually uses tokens."""
    # Reset cost stats to start fresh
    cli = client()
    cli.reset_cost_stats()

    # Verify we start at zero
    initial_stats = cli.get_cost_stats()
    assert initial_stats["total_tokens"] == 0, "Should start with 0 tokens"
    assert initial_stats["model_calls"] == 0, "Should start with 0 model calls"

    # Create a simple agent
    agent = TinyPerson("TestAgent")
    agent.define("age", 30)
    agent.define("occupation", "Software Engineer")
    agent.define("personality", {"traits": ["analytical"]})

    # Give the agent a simple stimulus and let it act
    agent.listen("What is 2+2?")
    agent.act()

    # Check that tokens were used
    after_stats = cli.get_cost_stats()
    assert (
        after_stats["total_tokens"] > 0
    ), "Should have used some tokens after agent action"
    assert after_stats["input_tokens"] > 0, "Should have used input tokens"
    assert after_stats["output_tokens"] > 0, "Should have used output tokens"
    assert (
        after_stats["model_calls"] > 0 or after_stats["cached_calls"] > 0
    ), "Should have made at least one call"


def test_world_cost_tracking_with_simulation_steps(setup):
    """Test that TinyWorld tracks simulation steps and computes per-step statistics."""
    # Reset cost stats
    cli = client()
    cli.reset_cost_stats()

    # Create a world with an agent
    agent = TinyPerson("Alice")
    agent.define("age", 25)
    agent.define("occupation", "Researcher")

    world = TinyWorld("TestWorld", [agent])

    # Verify initial state
    initial_world_stats = world.get_cost_stats()
    assert initial_world_stats["num_steps"] == 0, "Should start with 0 steps"
    assert initial_world_stats["num_agents"] == 1, "Should have 1 agent"

    # Run a couple of simulation steps
    world.run(2)

    # Check that steps were tracked
    after_world_stats = world.get_cost_stats()
    assert after_world_stats["num_steps"] == 2, "Should have completed 2 steps"

    # Check that tokens were used
    after_client_stats = cli.get_cost_stats()
    assert (
        after_client_stats["total_tokens"] > 0
    ), "Should have used tokens during simulation"

    # Check that per-step statistics are computed
    if after_world_stats["per_step"] is not None:
        assert (
            after_world_stats["per_step"]["total_tokens"] > 0
        ), "Per-step tokens should be positive"

    # Check that per-agent-per-step statistics are computed
    if after_world_stats["per_agent_per_step"] is not None:
        assert (
            after_world_stats["per_agent_per_step"]["total_tokens"] > 0
        ), "Per-agent-per-step tokens should be positive"


def test_derivative_stats_with_multiple_agents(setup):
    """Test derivative statistics calculation with multiple agents."""
    # Reset cost stats
    cli = client()
    cli.reset_cost_stats()

    # Create a world with two agents
    agent1 = TinyPerson("Bob")
    agent1.define("age", 30)
    agent1.define("occupation", "Engineer")

    agent2 = TinyPerson("Carol")
    agent2.define("age", 28)
    agent2.define("occupation", "Designer")

    world = TinyWorld("MultiAgentWorld", [agent1, agent2])

    # Run simulation
    world.run(1)

    # Get statistics
    world_stats = world.get_cost_stats()
    client_stats = cli.get_cost_stats()

    # Verify counts
    assert world_stats["num_agents"] == 2, "Should have 2 agents"
    assert world_stats["num_steps"] >= 1, "Should have at least 1 step"

    # Verify tokens were used
    assert client_stats["total_tokens"] > 0, "Should have used tokens"

    # Verify per-agent calculation
    if world_stats["per_agent"] is not None and client_stats["total_tokens"] > 0:
        expected_per_agent = client_stats["total_tokens"] / 2
        assert (
            abs(world_stats["per_agent"]["total_tokens"] - expected_per_agent) < 0.01
        ), "Per-agent calculation should divide total by number of agents"


def test_global_stats_aggregation(setup):
    """Test that global statistics aggregate correctly across worlds and agents."""
    # Reset cost stats
    cli = client()
    cli.reset_cost_stats()

    # Clear existing agents and worlds to start fresh
    TinyPerson.clear_agents()
    TinyWorld.clear_environments()

    # Create two worlds with agents
    agent1 = TinyPerson("Agent1")
    agent1.define("age", 30)
    world1 = TinyWorld("World1", [agent1])

    agent2 = TinyPerson("Agent2")
    agent2.define("age", 25)
    world2 = TinyWorld("World2", [agent2])

    # Run simulations
    world1.run(1)
    world2.run(1)

    # Get global statistics
    global_world_stats = TinyWorld.get_global_cost_stats()
    global_agent_stats = TinyPerson.get_global_cost_stats()

    # Verify aggregation
    assert global_world_stats["total_environments"] == 2, "Should have 2 environments"
    assert global_world_stats["total_agents"] == 2, "Should have 2 agents across worlds"
    assert global_world_stats["total_steps"] >= 2, "Should have at least 2 total steps"

    assert global_agent_stats["total_agents"] == 2, "Should have 2 total agents"

    # Verify tokens were used
    assert (
        global_world_stats["base_stats"]["total_tokens"] > 0
    ), "Should have used tokens"
    assert (
        global_agent_stats["base_stats"]["total_tokens"] > 0
    ), "Should have used tokens"
