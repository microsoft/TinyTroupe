import pytest
import logging
logger = logging.getLogger("tinytroupe")

import sys
sys.path.insert(0, '../../tinytroupe/')
sys.path.insert(0, '../../')
sys.path.insert(0, '..')

from tinytroupe.tools.tiny_tool import TinyTool
from tinytroupe.examples import create_oscar_the_architect, create_lisa_the_data_scientist
from tinytroupe.extraction import ArtifactExporter
from tinytroupe.enrichment import TinyEnricher
from testing_utils import *

class MockTool(TinyTool):
    """A mock tool implementation for testing."""
    
    def __init__(self, name="MockTool", description="A test tool", **kwargs):
        super().__init__(name, description, **kwargs)
        self.actions_processed = []
    
    def _process_action(self, agent, action: dict) -> bool:
        """Mock implementation that records processed actions."""
        self.actions_processed.append(action)
        return True
    
    def actions_definitions_prompt(self) -> str:
        """Mock implementation of action definitions."""
        return "MOCK_ACTION: Use this tool for testing purposes."
    
    def actions_constraints_prompt(self) -> str:
        """Mock implementation of action constraints."""
        return "Only use this tool during testing."

class DangerousMockTool(TinyTool):
    """A mock tool with real-world side effects for testing."""
    
    def __init__(self):
        super().__init__(
            name="DangerousTool",
            description="A tool with real-world side effects",
            real_world_side_effects=True
        )
    
    def _process_action(self, agent, action: dict) -> bool:
        return True
    
    def actions_definitions_prompt(self) -> str:
        return "DANGEROUS_ACTION: This action has real-world effects."
    
    def actions_constraints_prompt(self) -> str:
        return "Use with extreme caution."

def test_tiny_tool_initialization(setup):
    """Test TinyTool initialization with various parameters."""
    
    # Test basic initialization
    tool = MockTool()
    assert tool.name == "MockTool"
    assert tool.description == "A test tool"
    assert tool.owner is None
    assert tool.real_world_side_effects == False
    assert tool.exporter is None
    assert tool.enricher is None
    
    # Test initialization with all parameters
    agent = create_oscar_the_architect()
    exporter = ArtifactExporter(base_output_folder="test")
    enricher = TinyEnricher()
    
    tool = MockTool(
        name="CustomTool",
        description="Custom description",
        owner=agent,
        real_world_side_effects=True,
        exporter=exporter,
        enricher=enricher
    )
    
    assert tool.name == "CustomTool"
    assert tool.description == "Custom description"
    assert tool.owner == agent
    assert tool.real_world_side_effects == True
    assert tool.exporter == exporter
    assert tool.enricher == enricher

def test_tiny_tool_ownership(setup):
    """Test TinyTool ownership mechanisms."""
    
    oscar = create_oscar_the_architect()
    lisa = create_lisa_the_data_scientist()
    
    # Create tool owned by Oscar
    tool = MockTool(owner=oscar)
    
    # Test that Oscar can use the tool
    mock_action = {"type": "MOCK_ACTION", "content": "test"}
    result = tool.process_action(oscar, mock_action)
    assert result == True, "Owner should be able to use tool"
    
    # Test that Lisa cannot use the tool
    with pytest.raises(ValueError, match="does not own tool"):
        tool.process_action(lisa, mock_action)
    
    # Test setting owner
    tool.set_owner(lisa)
    assert tool.owner == lisa
    
    # Now Lisa should be able to use it
    result = tool.process_action(lisa, mock_action)
    assert result == True, "New owner should be able to use tool"

def test_tiny_tool_real_world_side_effects(setup):
    """Test TinyTool real-world side effects warning."""
    
    # Test tool without side effects
    safe_tool = MockTool(real_world_side_effects=False)
    agent = create_oscar_the_architect()
    
    # Should not raise warnings for safe tools
    mock_action = {"type": "MOCK_ACTION", "content": "test"}
    result = safe_tool.process_action(agent, mock_action)
    assert result == True
    
    # Test tool with side effects
    dangerous_tool = DangerousMockTool()
    
    # Should log warning (we can't easily test logging in unit tests,
    # but we can verify the tool still works)
    result = dangerous_tool.process_action(agent, mock_action)
    assert result == True

def test_tiny_tool_action_processing(setup):
    """Test TinyTool action processing functionality."""
    
    tool = MockTool()
    agent = create_oscar_the_architect()
    
    # Test processing different types of actions
    actions = [
        {"type": "MOCK_ACTION", "content": "action 1"},
        {"type": "MOCK_ACTION", "content": "action 2"},
        {"type": "OTHER_ACTION", "content": "action 3"}
    ]
    
    for action in actions:
        result = tool.process_action(agent, action)
        assert result == True, "Should process actions successfully"
    
    # Verify actions were recorded
    assert len(tool.actions_processed) == 3, "Should have processed all actions"
    assert tool.actions_processed[0]["content"] == "action 1"
    assert tool.actions_processed[1]["content"] == "action 2"
    assert tool.actions_processed[2]["content"] == "action 3"

def test_tiny_tool_prompts():
    """Test TinyTool prompt generation methods."""
    
    tool = MockTool()
    
    # Test action definitions prompt
    definitions = tool.actions_definitions_prompt()
    assert isinstance(definitions, str), "Should return string"
    assert len(definitions) > 0, "Should not be empty"
    assert "MOCK_ACTION" in definitions, "Should contain action definition"
    
    # Test action constraints prompt
    constraints = tool.actions_constraints_prompt()
    assert isinstance(constraints, str), "Should return string"
    assert len(constraints) > 0, "Should not be empty"

def test_tiny_tool_serialization():
    """Test TinyTool serialization/deserialization."""
    
    tool = MockTool(
        name="SerializationTest",
        description="Test serialization",
        real_world_side_effects=True
    )
    
    # Test serialization
    serialized = tool.to_json()
    assert isinstance(serialized, dict), "Should serialize to dictionary"
    assert "name" in serialized, "Should include name"
    assert "description" in serialized, "Should include description"
    assert "real_world_side_effects" in serialized, "Should include side effects flag"
    
    # Test deserialization
    new_tool = MockTool.from_json(serialized)
    assert new_tool.name == tool.name
    assert new_tool.description == tool.description
    assert new_tool.real_world_side_effects == tool.real_world_side_effects

def test_tiny_tool_with_exporter_and_enricher(setup):
    """Test TinyTool with exporter and enricher components."""
    
    exporter = ArtifactExporter(base_output_folder="test")
    enricher = TinyEnricher()
    
    tool = MockTool(
        exporter=exporter,
        enricher=enricher
    )
    
    assert tool.exporter == exporter, "Should store exporter"
    assert tool.enricher == enricher, "Should store enricher"
    
    # Test that tool can still process actions with these components
    agent = create_oscar_the_architect()
    mock_action = {"type": "MOCK_ACTION", "content": "test with components"}
    
    result = tool.process_action(agent, mock_action)
    assert result == True, "Should work with exporter and enricher"

def test_tiny_tool_abstract_methods(setup):
    """Test that TinyTool properly enforces abstract methods."""
    
    # Create a tool without implementing required methods
    class IncompleteTool(TinyTool):
        pass
    
    incomplete_tool = IncompleteTool("incomplete", "missing methods")
    agent = create_oscar_the_architect()
    
    # Should raise NotImplementedError for unimplemented methods
    with pytest.raises(NotImplementedError):
        incomplete_tool._process_action(agent, {})
    
    with pytest.raises(NotImplementedError):
        incomplete_tool.actions_definitions_prompt()
    
    with pytest.raises(NotImplementedError):
        incomplete_tool.actions_constraints_prompt()

def test_tiny_tool_edge_cases(setup):
    """Test TinyTool edge cases and error handling."""
    
    tool = MockTool()
    agent = create_oscar_the_architect()
    
    # Test with None action
    result = tool.process_action(agent, None)
    assert result == True, "Should handle None action gracefully"
    
    # Test with empty action
    result = tool.process_action(agent, {})
    assert result == True, "Should handle empty action gracefully"
    
    # Test with malformed action
    malformed_action = {"invalid": "structure"}
    result = tool.process_action(agent, malformed_action)
    assert result == True, "Should handle malformed action gracefully"

def test_tiny_tool_multiple_agents(setup):
    """Test TinyTool with multiple agents."""
    
    tool = MockTool()  # No owner, so any agent can use it
    oscar = create_oscar_the_architect()
    lisa = create_lisa_the_data_scientist()
    
    # Both agents should be able to use the tool
    oscar_action = {"type": "MOCK_ACTION", "content": "Oscar's action"}
    lisa_action = {"type": "MOCK_ACTION", "content": "Lisa's action"}
    
    result1 = tool.process_action(oscar, oscar_action)
    result2 = tool.process_action(lisa, lisa_action)
    
    assert result1 == True, "Oscar should be able to use tool"
    assert result2 == True, "Lisa should be able to use tool"
    
    # Verify both actions were processed
    assert len(tool.actions_processed) == 2
    assert tool.actions_processed[0]["content"] == "Oscar's action"
    assert tool.actions_processed[1]["content"] == "Lisa's action"
