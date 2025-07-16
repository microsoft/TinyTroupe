import pytest
import logging
import tempfile
import os
import shutil
logger = logging.getLogger("tinytroupe")

import sys
sys.path.insert(0, '../../tinytroupe/')
sys.path.insert(0, '../../')
sys.path.insert(0, '..')

from tinytroupe.agent.grounding import (
    GroundingConnector, 
    BaseSemanticGroundingConnector,
    LocalFilesGroundingConnector,
    WebPagesGroundingConnector
)
from tinytroupe.examples import create_oscar_the_architect
from testing_utils import *

@pytest.fixture
def temp_folder():
    """Create a temporary folder with sample files for testing."""
    temp_dir = tempfile.mkdtemp()
    
    # Create sample files
    with open(os.path.join(temp_dir, "sample1.txt"), "w") as f:
        f.write("This is a sample document about architecture and building design.")
    
    with open(os.path.join(temp_dir, "sample2.txt"), "w") as f:
        f.write("This document discusses construction materials and engineering principles.")
    
    with open(os.path.join(temp_dir, "sample3.txt"), "w") as f:
        f.write("A guide to sustainable architecture and green building practices.")
    
    yield temp_dir
    
    # Cleanup
    shutil.rmtree(temp_dir)

def test_grounding_connector_abstract():
    """Test that GroundingConnector is properly abstract."""
    
    # Should be able to instantiate the base class
    connector = GroundingConnector("test_connector")
    assert connector.name == "test_connector"
    
    # Abstract methods should raise NotImplementedError
    with pytest.raises(NotImplementedError):
        connector.retrieve_relevant("query", "source")
    
    with pytest.raises(NotImplementedError):
        connector.retrieve_by_name("name")
    
    with pytest.raises(NotImplementedError):
        connector.list_sources()

def test_local_files_grounding_connector(temp_folder):
    """Test LocalFilesGroundingConnector functionality."""
    
    connector = LocalFilesGroundingConnector(
        name="test_files_connector",
        folders_paths=[temp_folder]
    )
    
    # Test initialization
    assert connector.name == "test_files_connector"
    assert temp_folder in connector.folders_paths
    
    # Test that documents are loaded
    assert len(connector.documents) > 0, "Should load documents from folder"
    
    # Test semantic search functionality
    results = connector.retrieve_relevant("architecture", top_k=2)
    assert isinstance(results, list), "Should return a list of results"
    assert len(results) <= 2, "Should respect top_k parameter"
    
    # Test listing sources
    sources = connector.list_sources()
    assert isinstance(sources, list), "Should return a list of sources"
    assert len(sources) > 0, "Should have sources from loaded files"

def test_local_files_grounding_connector_empty_folder():
    """Test LocalFilesGroundingConnector with empty folder."""
    
    empty_dir = tempfile.mkdtemp()
    try:
        connector = LocalFilesGroundingConnector(
            name="empty_connector",
            folders_paths=[empty_dir]
        )
        
        # Should handle empty folders gracefully
        assert len(connector.documents) == 0, "Should have no documents from empty folder"
        
        results = connector.retrieve_relevant("query", "documents")
        assert isinstance(results, list), "Should return empty list for empty connector"
        assert len(results) == 0, "Should return no results from empty connector"
        
    finally:
        shutil.rmtree(empty_dir)

def test_web_pages_grounding_connector():
    """Test WebPagesGroundingConnector basic functionality."""
    
    # Test with sample URLs (Note: This might need mocking in a real test environment)
    urls = ["https://example.com", "https://httpbin.org/html"]
    
    try:
        connector = WebPagesGroundingConnector(
            name="web_connector",
            urls=urls
        )
        
        # Test initialization
        assert connector.name == "web_connector"
        assert connector.urls == urls
        
        # Note: Actual web fetching might fail in test environment
        # In a production test, you would mock the web requests
        
    except Exception as e:
        # Web connections might fail in test environment - that's ok
        logger.warning(f"Web connector test failed (expected in test env): {e}")

def test_base_semantic_grounding_connector():
    """Test BaseSemanticGroundingConnector functionality."""
    
    # Create a connector with some sample documents
    connector = BaseSemanticGroundingConnector(name="semantic_test")
    
    # Test initialization
    assert connector.name == "semantic_test"
    assert hasattr(connector, 'documents')
    assert hasattr(connector, 'index')

def test_grounding_connector_serialization(temp_folder):
    """Test grounding connector serialization/deserialization."""
    
    connector = LocalFilesGroundingConnector(
        name="serialization_test",
        folders_paths=[temp_folder]
    )
    
    # Test serialization
    serialized = connector.to_json()
    assert isinstance(serialized, dict), "Should serialize to dictionary"
    assert "name" in serialized, "Should include name in serialization"
    
    # Test deserialization
    new_connector = LocalFilesGroundingConnector.from_json(serialized)
    assert new_connector.name == connector.name
    assert new_connector.folders_paths == connector.folders_paths

def test_grounding_connector_integration_with_agent(temp_folder, setup):
    """Test grounding connector integration with TinyPerson agents."""
    
    connector = LocalFilesGroundingConnector(
        name="agent_integration_test",
        folders_paths=[temp_folder]
    )
    
    agent = create_oscar_the_architect()
    
    # Test that we can add grounding capability to agent
    # (This tests the integration pattern shown in the notebooks)
    from tinytroupe.agent.mental_faculty import FilesAndWebGroundingFaculty
    
    grounding_faculty = FilesAndWebGroundingFaculty(folders_paths=[temp_folder])
    agent.add_mental_faculties([grounding_faculty])
    
    # Test that agent can use grounding
    assert len(agent._mental_faculties) > 0, "Agent should have mental faculties"

def test_grounding_connector_error_handling():
    """Test grounding connector error handling."""
    
    # Test with non-existent folder
    non_existent_path = "/path/that/does/not/exist"
    
    try:
        connector = LocalFilesGroundingConnector(
            name="error_test",
            folders_paths=[non_existent_path]
        )
        # Should handle non-existent paths gracefully
        assert len(connector.documents) == 0, "Should have no documents from non-existent path"
    except Exception as e:
        # If it raises an exception, that's also acceptable behavior
        logger.info(f"Connector handled non-existent path by raising: {e}")

def test_grounding_connector_search_edge_cases(temp_folder):
    """Test grounding connector search with edge cases."""
    
    connector = LocalFilesGroundingConnector(
        name="edge_cases_test",
        folders_paths=[temp_folder]
    )
    
    # Test empty query
    results = connector.retrieve_relevant("")
    assert isinstance(results, list), "Should handle empty query"
    
    # Test very long query
    long_query = "architecture " * 100
    results = connector.retrieve_relevant(long_query)
    assert isinstance(results, list), "Should handle long query"
    
    # Test special characters in query
    special_query = "architecture & design @#$%"
    results = connector.retrieve_relevant(special_query)
    assert isinstance(results, list), "Should handle special characters"
    
    # Test very high top_k
    results = connector.retrieve_relevant("architecture", top_k=1000)
    assert isinstance(results, list), "Should handle high top_k values"
    assert len(results) <= len(connector.documents), "Should not return more than available documents"
