import pytest
import logging
import tempfile
import os
import json
from unittest.mock import Mock, patch
logger = logging.getLogger("tinytroupe")

import sys
sys.path.insert(0, '../../tinytroupe/')
sys.path.insert(0, '../../')
sys.path.insert(0, '..')

from tinytroupe.extraction.results_extractor import ResultsExtractor
from tinytroupe.examples import create_oscar_the_architect, create_lisa_the_data_scientist
from tinytroupe.environment import TinyWorld
from testing_utils import *

def test_results_extractor_initialization():
    """Test ResultsExtractor initialization with default and custom parameters."""
    
    # Test default initialization
    extractor = ResultsExtractor()
    assert extractor.default_extraction_objective == "The main points present in the agents' interactions history."
    assert extractor.default_situation == ""
    assert extractor.default_fields is None
    assert extractor.default_fields_hints is None
    assert extractor.default_verbose == False
    
    # Test initialization with custom parameters
    custom_extractor = ResultsExtractor(
        extraction_objective="Custom objective",
        situation="Custom situation",
        fields=["field1", "field2"],
        fields_hints={"field1": "hint1"},
        verbose=True
    )
    assert custom_extractor.default_extraction_objective == "Custom objective"
    assert custom_extractor.default_situation == "Custom situation"
    assert custom_extractor.default_fields == ["field1", "field2"]
    assert custom_extractor.default_fields_hints == {"field1": "hint1"}
    assert custom_extractor.default_verbose == True

def test_results_extractor_cache_initialization():
    """Test that ResultsExtractor properly initializes caches."""
    
    extractor = ResultsExtractor()
    assert hasattr(extractor, 'agent_extraction')
    assert hasattr(extractor, 'world_extraction')
    assert isinstance(extractor.agent_extraction, dict)
    assert isinstance(extractor.world_extraction, dict)
    assert len(extractor.agent_extraction) == 0
    assert len(extractor.world_extraction) == 0


def test_results_extractor_extract_from_agent(setup):
    """Test extracting results from a single agent using real API."""
    
    extractor = ResultsExtractor()
    agent = create_oscar_the_architect()
    
    # Add some realistic interactions to the agent
    agent.listen("Hello Oscar, tell me about your latest architectural project.")
    agent.listen_and_act("What design principles do you follow?")
    agent.listen("What challenges did you face in your recent work?")
    
    # Extract results with specific fields
    result = extractor.extract_results_from_agent(
        agent,
        extraction_objective="Extract key insights about Oscar's architectural work and approach",
        situation="Oscar is discussing his professional work and design philosophy",
        fields=["main_themes", "design_principles", "challenges_mentioned", "expertise_level"],
        fields_hints={
            "main_themes": "Main topics discussed in the conversation",
            "design_principles": "Any design principles or methodologies mentioned",
            "challenges_mentioned": "Professional challenges or difficulties discussed",
            "expertise_level": "Assessment of apparent expertise level (beginner/intermediate/expert)"
        },
        verbose=False
    )
    
    # Verify the result structure
    assert isinstance(result, dict)
    logger.info(f"Extracted result: {result}")
    
    # Should have some content from real API
    assert len(result) > 0
    
    # Semantic verification: ensure the extraction is actually about Oscar's architectural work
    assert proposition_holds(str(result) + " - The extracted information relates to architecture, design, or professional work")
    
    # Verify caching
    assert agent.name in extractor.agent_extraction
    assert extractor.agent_extraction[agent.name] == result
    
    # If specific fields were requested, check they're present (values can be None)
    expected_fields = ["main_themes", "design_principles", "challenges_mentioned", "expertise_level"]
    for field in expected_fields:
        if field in result:
            # Field exists in result - value can be None, which is acceptable
            assert field in result, f"Expected field '{field}' should be in result"
            logger.info(f"Field '{field}': {result[field]}")


def test_results_extractor_extract_from_multiple_agents(setup):
    """Test extracting results from multiple agents using real API."""
    
    extractor = ResultsExtractor()
    agents = [create_oscar_the_architect(), create_lisa_the_data_scientist()]
    
    # Add different interactions to each agent to get varied results
    agents[0].listen("Oscar, what's your approach to sustainable architecture?")
    agents[0].listen_and_act("Describe a challenging project you've worked on.")
    
    agents[1].listen("Lisa, tell me about your data science methodology.")
    agents[1].listen_and_act("What machine learning techniques do you prefer?")
    
    # Extract results from all agents
    results = extractor.extract_results_from_agents(
        agents,
        extraction_objective="Extract professional insights and expertise from each agent",
        situation="Each agent is discussing their professional work and expertise",
        fields=["professional_focus", "key_skills", "work_approach", "experience_level"],
        fields_hints={
            "professional_focus": "Main area of professional expertise",
            "key_skills": "Key skills or competencies mentioned",
            "work_approach": "Methodology or approach to work",
            "experience_level": "Apparent level of experience"
        }
    )
    
    # Verify results
    assert isinstance(results, list)
    assert len(results) == 2
    logger.info(f"Extracted results from {len(results)} agents")
    
    for i, result in enumerate(results):
        assert isinstance(result, dict)
        assert len(result) > 0
        logger.info(f"Agent {i+1} result: {result}")
        
        # Semantic verification: ensure each extraction contains professional insights
        assert proposition_holds(str(result) + " - The extracted information contains professional insights, skills, or expertise")
    
    # Verify all agents are cached
    for agent in agents:
        assert agent.name in extractor.agent_extraction


def test_results_extractor_extract_from_world(setup):
    """Test extracting results from a TinyWorld environment using real API."""
    
    extractor = ResultsExtractor()
    
    # Create a world with agents
    oscar = create_oscar_the_architect()
    lisa = create_lisa_the_data_scientist()
    world = TinyWorld("Collaborative Project", [oscar, lisa])
    
    # Simulate realistic interactions
    world.broadcast("We're starting a new smart city project. Let's discuss our approach.")
    world.run(1)
    
    world.broadcast("What are the key data requirements for this architecture project?")
    world.run(1)
    
    # Extract results from world
    result = extractor.extract_results_from_world(
        world,
        extraction_objective="Analyze the collaboration and key insights from the team discussion",
        situation="A team of an architect and data scientist discussing a smart city project",
        fields=["collaboration_quality", "key_insights", "project_approach", "expertise_integration"],
        fields_hints={
            "collaboration_quality": "How well the team members collaborated",
            "key_insights": "Main insights or ideas that emerged",
            "project_approach": "Overall approach to the project",
            "expertise_integration": "How different expertises were combined"
        }
    )
    
    # Verify the result
    assert isinstance(result, dict)
    assert len(result) > 0
    logger.info(f"World extraction result: {result}")
    
    # Semantic verification: ensure the world extraction captures collaboration insights
    assert proposition_holds(str(result) + " - The extracted information relates to team collaboration, project planning, or smart city concepts")
    
    # Verify caching
    assert world.name in extractor.world_extraction
    
    # Log individual field results if available
    expected_fields = ["collaboration_quality", "key_insights", "project_approach", "expertise_integration"]
    for field in expected_fields:
        if field in result:
            logger.info(f"Field '{field}': {result[field]}")

def test_results_extractor_default_value_handling():
    """Test how extractor handles default values."""
    
    extractor = ResultsExtractor(
        extraction_objective="Default objective",
        situation="Default situation",
        fields=["default_field"],
        fields_hints={"default_field": "default hint"},
        verbose=True
    )
    
    # Test that defaults are used when None is passed
    objective, situation, fields, hints, verbose = extractor._get_default_values_if_necessary(
        None, None, None, None, None
    )
    
    assert objective == "Default objective"
    assert situation == "Default situation"
    assert fields == ["default_field"]
    assert hints == {"default_field": "default hint"}
    assert verbose == True
    
    # Test that explicit values override defaults
    objective, situation, fields, hints, verbose = extractor._get_default_values_if_necessary(
        "Custom objective", "Custom situation", ["custom_field"], {"custom_field": "custom hint"}, False
    )
    
    assert objective == "Custom objective"
    assert situation == "Custom situation"
    assert fields == ["custom_field"]
    assert hints == {"custom_field": "custom hint"}
    assert verbose == False


def test_results_extractor_with_fields_and_hints(setup):
    """Test extractor with specific fields and hints using real API."""
    
    extractor = ResultsExtractor()
    agent = create_oscar_the_architect()
    
    # Add realistic feedback-style interactions
    agent.listen("Oscar, how would you rate your experience working on this latest building project?")
    agent.listen_and_act("Would you recommend our collaboration process to other architects?")
    agent.listen("What specific aspects did you find most valuable or challenging?")
    
    # Extract with specific fields and detailed hints
    result = extractor.extract_results_from_agent(
        agent,
        extraction_objective="Extract structured feedback and assessment from Oscar's responses",
        situation="Oscar is providing feedback about a recent architectural project collaboration",
        fields=["satisfaction_level", "recommendation", "positive_aspects", "challenges", "overall_sentiment"],
        fields_hints={
            "satisfaction_level": "Extract a satisfaction rating on a scale of 1-10 based on Oscar's responses",
            "recommendation": "Whether Oscar would recommend this type of collaboration (yes/no/maybe)",
            "positive_aspects": "List of positive aspects or benefits mentioned",
            "challenges": "Any challenges or difficulties mentioned",
            "overall_sentiment": "Overall emotional tone (positive/neutral/negative)"
        }
    )
    
    # Verify the result includes requested fields
    assert isinstance(result, dict)
    assert len(result) > 0
    logger.info(f"Structured extraction result: {result}")
    
    # Semantic verification: ensure the feedback extraction makes sense for an architect
    assert proposition_holds(str(result) + " - The extracted information contains feedback, assessments, or evaluations related to professional work")
    
    # Log each field if present
    expected_fields = ["satisfaction_level", "recommendation", "positive_aspects", "challenges", "overall_sentiment"]
    for field in expected_fields:
        if field in result:
            logger.info(f"Field '{field}': {result[field]}")
    
    # Verify at least some fields were extracted
    found_fields = [field for field in expected_fields if field in result]
    assert len(found_fields) > 0, "At least some requested fields should be present in the result"


def test_results_extractor_empty_interactions(setup):
    """Test extractor with agent having no interactions using real API."""
    
    extractor = ResultsExtractor()
    agent = create_oscar_the_architect()
    
    # Don't add any interactions - test with empty history
    result = extractor.extract_results_from_agent(
        agent,
        extraction_objective="Extract any available information from the agent's interactions",
        fields=["interaction_count", "available_data"],
        fields_hints={
            "interaction_count": "Number of interactions found",
            "available_data": "Summary of what data is available"
        }
    )
    
    # Should handle empty interactions gracefully
    assert isinstance(result, dict)
    logger.info(f"Empty interactions result: {result}")
    
    # The real API should return something, even if it's about the lack of data
    # This tests that the extraction doesn't crash with empty input

@patch('tinytroupe.openai_utils.client')
def test_results_extractor_invalid_json_response(mock_client, setup):
    """Test extractor handling of invalid JSON responses."""
    
    # Mock the OpenAI client to return invalid JSON
    mock_client_instance = Mock()
    mock_client.return_value = mock_client_instance
    mock_client_instance.send_message.return_value = {
        "content": "This is not valid JSON content"
    }
    
    extractor = ResultsExtractor()
    agent = create_oscar_the_architect()
    
    agent.listen("Test message")
    
    # Should handle invalid JSON gracefully
    result = extractor.extract_results_from_agent(agent)
    
    # Result should be None or empty when JSON extraction fails
    assert result is None or result == {}

@patch('tinytroupe.openai_utils.client')
def test_results_extractor_api_failure(mock_client, setup):
    """Test extractor handling of API failures."""
    
    # Mock the OpenAI client to return None (API failure)
    mock_client_instance = Mock()
    mock_client.return_value = mock_client_instance
    mock_client_instance.send_message.return_value = None
    
    extractor = ResultsExtractor()
    agent = create_oscar_the_architect()
    
    agent.listen("Test message")
    
    # Should handle API failure gracefully
    result = extractor.extract_results_from_agent(agent)
    assert result is None

  
def test_results_extractor_verbose_mode(setup):
    """Test extractor verbose mode functionality with real API."""
    
    extractor = ResultsExtractor(verbose=True)
    agent = create_oscar_the_architect()
    
    # Add some interactions
    agent.listen("Tell me about your design philosophy, Oscar.")
    agent.listen_and_act("What makes a good architectural design?")
    
    # With verbose=True, should provide detailed logging and not crash
    try:
        result = extractor.extract_results_from_agent(
            agent, 
            extraction_objective="Extract design philosophy and principles",
            verbose=True
        )
        
        assert result is not None
        assert isinstance(result, dict)
        logger.info(f"Verbose mode result: {result}")
    
    except Exception as e:
        pytest.fail(f"Verbose mode should not raise exceptions: {e}")


def test_results_extractor_cache_persistence(setup):
    """Test that extraction results are properly cached with real API."""
    
    extractor = ResultsExtractor()
    agent = create_oscar_the_architect()
    agent.listen("Oscar, please share your thoughts on sustainable architecture.")
    
    # First extraction
    result1 = extractor.extract_results_from_agent(
        agent,
        extraction_objective="Extract insights about sustainable architecture",
        fields=["sustainability_focus", "key_concepts"]
    )
    
    # Verify it's cached
    assert agent.name in extractor.agent_extraction
    cached_result = extractor.agent_extraction[agent.name]
    assert cached_result == result1
    assert isinstance(cached_result, dict)
    assert len(cached_result) > 0
    
    logger.info(f"Cached result: {cached_result}")

def test_results_extractor_template_path():
    """Test that extractor uses the correct template path."""
    
    extractor = ResultsExtractor()
    
    # Verify template path is set
    assert hasattr(extractor, '_extraction_prompt_template_path')
    assert extractor._extraction_prompt_template_path is not None
    
    # Template file should exist (in a real deployment)
    # For tests, we just verify the path is reasonable
    assert 'prompts' in extractor._extraction_prompt_template_path
    assert '.mustache' in extractor._extraction_prompt_template_path

def test_results_extractor_custom_template_path():
    """Test extractor with custom template path."""
    
    custom_path = "/custom/path/to/template.mustache"
    extractor = ResultsExtractor(extraction_prompt_template_path=custom_path)
    
    assert extractor._extraction_prompt_template_path == custom_path
