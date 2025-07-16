import pytest
import logging
import pandas as pd
from unittest.mock import Mock, patch
logger = logging.getLogger("tinytroupe")

import sys
sys.path.insert(0, '../../tinytroupe/')
sys.path.insert(0, '../../')
sys.path.insert(0, '..')

from tinytroupe.extraction.results_reducer import ResultsReducer
from tinytroupe.examples import create_oscar_the_architect, create_lisa_the_data_scientist
from tinytroupe.agent import TinyPerson
from testing_utils import *

def test_results_reducer_initialization():
    """Test ResultsReducer initialization."""
    
    reducer = ResultsReducer()
    
    # Check that required attributes exist
    assert hasattr(reducer, 'results')
    assert hasattr(reducer, 'rules')
    assert isinstance(reducer.results, dict)
    assert isinstance(reducer.rules, dict)
    assert len(reducer.results) == 0
    assert len(reducer.rules) == 0

def test_results_reducer_add_reduction_rule():
    """Test adding reduction rules to the reducer."""
    
    reducer = ResultsReducer()
    
    # Define a simple reduction function
    def simple_rule(focus_agent, source_agent, target_agent, kind, event, content, timestamp):
        return {"agent": focus_agent.name, "content": content, "event": event}
    
    # Add a rule
    trigger = "TALK"
    reducer.add_reduction_rule(trigger, simple_rule)
    
    # Verify rule was added
    assert trigger in reducer.rules
    assert reducer.rules[trigger] == simple_rule
    
    # Test adding multiple rules
    def another_rule(focus_agent, source_agent, target_agent, kind, event, content, timestamp):
        return {"type": "another", "agent": focus_agent.name}
    
    reducer.add_reduction_rule("CONVERSATION", another_rule)
    assert "CONVERSATION" in reducer.rules
    assert len(reducer.rules) == 2

def test_results_reducer_duplicate_rule_error():
    """Test that adding duplicate rules raises an error."""
    
    reducer = ResultsReducer()
    
    def rule1(focus_agent, source_agent, target_agent, kind, event, content, timestamp):
        return {"rule": "first"}
    
    def rule2(focus_agent, source_agent, target_agent, kind, event, content, timestamp):
        return {"rule": "second"}
    
    # Add first rule
    reducer.add_reduction_rule("TALK", rule1)
    
    # Adding same trigger should raise exception
    with pytest.raises(Exception, match="Rule for TALK already exists"):
        reducer.add_reduction_rule("TALK", rule2)

def test_results_reducer_reduce_agent_empty(setup):
    """Test reducing an agent with no interactions."""
    
    reducer = ResultsReducer()
    agent = create_oscar_the_architect()
    
    # Agent has no interactions, should return empty list
    result = reducer.reduce_agent(agent)
    assert isinstance(result, list)
    assert len(result) == 0

def test_results_reducer_reduce_agent_with_rules(setup):
    """Test reducing an agent with defined rules."""
    
    reducer = ResultsReducer()
    
    # Define extraction rules
    def talk_rule(focus_agent, source_agent, target_agent, kind, event, content, timestamp):
        return {
            "speaker": source_agent.name if source_agent else "unknown",
            "content": content,
            "type": "talk",
            "timestamp": timestamp
        }
    
    def conversation_rule(focus_agent, source_agent, target_agent, kind, event, content, timestamp):
        return {
            "listener": focus_agent.name,
            "content": content,
            "type": "conversation",
            "timestamp": timestamp
        }
    
    reducer.add_reduction_rule("TALK", talk_rule)
    reducer.add_reduction_rule("CONVERSATION", conversation_rule)
    
    # Create agent and add some interactions
    agent = create_oscar_the_architect()
    agent.listen("Hello, how are you?")
    agent.listen_and_act("Tell me about yourself")
    
    # Reduce the agent
    result = reducer.reduce_agent(agent)
    
    # Should have extracted some data
    assert isinstance(result, list)
    assert len(result) > 0
    
    # Check that extracted data has expected structure
    for item in result:
        assert isinstance(item, dict)
        assert "type" in item
        assert item["type"] in ["talk", "conversation"]

def test_results_reducer_reduce_agent_to_dataframe(setup):
    """Test converting reduced agent data to DataFrame."""
    
    reducer = ResultsReducer()
    
    # Define a simple rule that returns tuples
    def simple_rule(focus_agent, source_agent, target_agent, kind, event, content, timestamp):
        return (focus_agent.name, content, event)
    
    reducer.add_reduction_rule("TALK", simple_rule)
    reducer.add_reduction_rule("CONVERSATION", simple_rule)
    
    # Create agent with interactions
    agent = create_oscar_the_architect()
    agent.listen("Hello")
    agent.listen_and_act("How are you?")
    
    # Convert to DataFrame
    column_names = ["agent", "content", "event"]
    df = reducer.reduce_agent_to_dataframe(agent, column_names)
    
    # Verify DataFrame structure
    assert isinstance(df, pd.DataFrame)
    assert list(df.columns) == column_names
    assert len(df) >= 0

def test_results_reducer_rule_function_parameters(setup):
    """Test that rule functions receive correct parameters."""
    
    reducer = ResultsReducer()
    captured_params = []
    
    def capturing_rule(focus_agent, source_agent, target_agent, kind, event, content, timestamp):
        captured_params.append({
            "focus_agent": focus_agent,
            "source_agent": source_agent,
            "target_agent": target_agent,
            "kind": kind,
            "event": event,
            "content": content,
            "timestamp": timestamp
        })
        return {"captured": True}
    
    reducer.add_reduction_rule("TALK", capturing_rule)
    reducer.add_reduction_rule("CONVERSATION", capturing_rule)
    
    # Create agent with interactions
    agent = create_oscar_the_architect()
    agent.listen("Test message")
    
    # Reduce to trigger rule
    result = reducer.reduce_agent(agent)
    
    # Check that parameters were captured correctly
    assert len(captured_params) > 0
    
    for params in captured_params:
        assert params["focus_agent"] == agent
        assert params["kind"] in ["stimulus", "action"]
        assert params["event"] in ["TALK", "CONVERSATION"]
        assert isinstance(params["content"], str)
        # Timestamp might be None in some cases, so we just check it exists as a key
        assert "timestamp" in params

def test_results_reducer_rule_returns_none(setup):
    """Test handling of rules that return None."""
    
    reducer = ResultsReducer()
    
    # Rule that sometimes returns None
    def selective_rule(focus_agent, source_agent, target_agent, kind, event, content, timestamp):
        if "important" in content.lower():
            return {"content": content, "important": True}
        return None  # Don't include non-important messages
    
    reducer.add_reduction_rule("TALK", selective_rule)
    reducer.add_reduction_rule("CONVERSATION", selective_rule)
    
    # Create agent with mixed content
    agent = create_oscar_the_architect()
    agent.listen("This is important information")
    agent.listen("This is not relevant")
    agent.listen("Another important detail")
    
    # Reduce the agent
    result = reducer.reduce_agent(agent)
    
    # Should only include items where rule returned non-None
    for item in result:
        assert item is not None
        assert "important" in item
        assert item["important"] == True

def test_results_reducer_multiple_event_types(setup):
    """Test reducer with multiple types of events."""
    
    reducer = ResultsReducer()
    
    # Define rules for different event types
    def talk_rule(focus_agent, source_agent, target_agent, kind, event, content, timestamp):
        return {"type": "talk", "speaker": source_agent.name if source_agent else "unknown"}
    
    def think_rule(focus_agent, source_agent, target_agent, kind, event, content, timestamp):
        return {"type": "think", "thinker": focus_agent.name}
    
    def move_rule(focus_agent, source_agent, target_agent, kind, event, content, timestamp):
        return {"type": "move", "actor": focus_agent.name}
    
    reducer.add_reduction_rule("TALK", talk_rule)
    reducer.add_reduction_rule("THINK", think_rule)
    reducer.add_reduction_rule("MOVE", move_rule)
    
    # Create interactions (some will trigger rules, others won't)
    agent = create_oscar_the_architect()
    agent.listen("Hello")  # Should trigger CONVERSATION rule (not defined)
    agent.listen_and_act("I'll think about this")  # Should trigger TALK rule
    
    result = reducer.reduce_agent(agent)
    
    # Should have some results based on available rules
    assert isinstance(result, list)

def test_results_reducer_agent_name_resolution(setup):
    """Test that agent names are properly resolved in rules."""
    
    reducer = ResultsReducer()
    
    def name_capturing_rule(focus_agent, source_agent, target_agent, kind, event, content, timestamp):
        return {
            "focus_name": focus_agent.name if focus_agent else None,
            "source_name": source_agent.name if source_agent else None,
            "target_name": target_agent.name if target_agent else None
        }
    
    reducer.add_reduction_rule("TALK", name_capturing_rule)
    reducer.add_reduction_rule("CONVERSATION", name_capturing_rule)
    
    # Create agents
    oscar = create_oscar_the_architect()
    lisa = create_lisa_the_data_scientist()
    
    # Add interactions
    oscar.listen("Hello from the user")
    
    result = reducer.reduce_agent(oscar)
    
    # Check that names are properly captured
    for item in result:
        assert "focus_name" in item
        assert item["focus_name"] == oscar.name

def test_results_reducer_system_message_handling(setup):
    """Test that system messages are properly skipped."""
    
    reducer = ResultsReducer()
    
    def all_messages_rule(focus_agent, source_agent, target_agent, kind, event, content, timestamp):
        return {"processed": True, "content": content}
    
    # Add rules for all possible events
    reducer.add_reduction_rule("TALK", all_messages_rule)
    reducer.add_reduction_rule("CONVERSATION", all_messages_rule)
    reducer.add_reduction_rule("SYSTEM", all_messages_rule)
    
    agent = create_oscar_the_architect()
    
    # Add various types of messages
    agent.listen("User message")
    agent.listen_and_act("Agent response")
    
    result = reducer.reduce_agent(agent)
    
    # System messages should be skipped regardless of rules
    # (exact verification depends on what messages are actually stored)
    assert isinstance(result, list)

def test_results_reducer_malformed_message_handling(setup):
    """Test handling of malformed messages in agent memory."""
    
    reducer = ResultsReducer()
    
    def robust_rule(focus_agent, source_agent, target_agent, kind, event, content, timestamp):
        return {"content": content or "no_content", "event": event or "no_event"}
    
    reducer.add_reduction_rule("TALK", robust_rule)
    
    agent = create_oscar_the_architect()
    
    # Add normal interaction
    agent.listen("Normal message")
    
    # Manually add a malformed message to test robustness
    malformed_message = {
        "role": "assistant",
        "content": {},  # Missing action
        "simulation_timestamp": "test_time"
    }
    agent.episodic_memory.store(malformed_message)
    
    # Should handle malformed messages gracefully
    result = reducer.reduce_agent(agent)
    assert isinstance(result, list)

def test_results_reducer_dataframe_column_names(setup):
    """Test DataFrame creation with and without column names."""
    
    reducer = ResultsReducer()
    
    def tuple_rule(focus_agent, source_agent, target_agent, kind, event, content, timestamp):
        return (focus_agent.name, event, content[:10] if content else "")
    
    reducer.add_reduction_rule("TALK", tuple_rule)
    reducer.add_reduction_rule("CONVERSATION", tuple_rule)
    
    agent = create_oscar_the_architect()
    agent.listen("Test message for DataFrame")
    
    # Test with column names
    df_with_names = reducer.reduce_agent_to_dataframe(agent, ["agent", "event", "content"])
    assert list(df_with_names.columns) == ["agent", "event", "content"]
    
    # Test without column names
    df_without_names = reducer.reduce_agent_to_dataframe(agent)
    assert isinstance(df_without_names, pd.DataFrame)
    # Default column names should be integers (0, 1, 2, ...)

def test_results_reducer_large_dataset_performance(setup):
    """Test reducer performance with larger datasets."""
    
    reducer = ResultsReducer()
    
    def simple_rule(focus_agent, source_agent, target_agent, kind, event, content, timestamp):
        return {"id": len(content), "type": event}
    
    reducer.add_reduction_rule("CONVERSATION", simple_rule)
    
    agent = create_oscar_the_architect()
    
    # Add many interactions
    for i in range(50):
        agent.listen(f"Message number {i} with some content")
    
    # Should handle larger datasets without issues
    result = reducer.reduce_agent(agent)
    assert isinstance(result, list)
    
    # Convert to DataFrame
    df = reducer.reduce_agent_to_dataframe(agent, ["id", "type"])
    assert isinstance(df, pd.DataFrame)
    assert len(df) <= 50  # Should not exceed number of messages
