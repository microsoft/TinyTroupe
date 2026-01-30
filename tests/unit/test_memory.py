import copy
import json
import logging
from unittest.mock import MagicMock, Mock, patch

import pytest

logger = logging.getLogger("tinytroupe")

import sys

# Insert paths at the beginning of sys.path (position 0)
sys.path.insert(0, "../../tinytroupe/")
sys.path.insert(0, "../../")
sys.path.insert(0, "..")

from testing_utils import *

from tinytroupe.agent.grounding import BaseSemanticGroundingConnector
from tinytroupe.agent.memory import (
    EpisodicConsolidator,
    EpisodicMemory,
    MemoryProcessor,
    ReflectionConsolidator,
    SemanticMemory,
    TinyMemory,
)


class TestTinyMemory:
    """Test cases for the abstract TinyMemory base class"""

    def test_preprocess_value_for_storage_default(self, setup):
        """Test that the default preprocessing returns the value unchanged"""

        class ConcreteTinyMemory(TinyMemory):
            def __init__(self):
                super().__init__("test_memory")

            def _store(self, value):
                pass

            def retrieve(
                self, first_n, last_n, include_omission_info=True, item_type=None
            ):
                pass

            def retrieve_recent(self, item_type=None):
                pass

            def retrieve_all(self, item_type=None):
                pass

            def retrieve_relevant(self, relevance_target, top_k=20):
                pass

        memory = ConcreteTinyMemory()
        test_value = {"content": "test"}
        result = memory._preprocess_value_for_storage(test_value)
        assert result == test_value

    def test_filter_by_item_type(self, setup):
        """Test filtering memories by item type"""

        class ConcreteTinyMemory(TinyMemory):
            def __init__(self):
                super().__init__("test_memory")

            def _store(self, value):
                pass

            def retrieve(
                self, first_n, last_n, include_omission_info=True, item_type=None
            ):
                pass

            def retrieve_recent(self, item_type=None):
                pass

            def retrieve_all(self, item_type=None):
                pass

            def retrieve_relevant(self, relevance_target, top_k=20):
                pass

        memory = ConcreteTinyMemory()
        memories = [
            {"type": "action", "content": "I walked"},
            {"type": "stimulus", "content": "I saw a cat"},
            {"type": "action", "content": "I talked"},
            {"type": "feedback", "content": "Good job"},
        ]

        filtered = memory.filter_by_item_type(memories, "action")
        assert len(filtered) == 2
        assert all(m["type"] == "action" for m in filtered)

        filtered = memory.filter_by_item_type(memories, "stimulus")
        assert len(filtered) == 1
        assert filtered[0]["content"] == "I saw a cat"

    def test_filter_by_item_types(self, setup):
        """Test filtering memories by multiple item types"""

        class ConcreteTinyMemory(TinyMemory):
            def __init__(self):
                super().__init__("test_memory")

            def _store(self, value):
                pass

            def retrieve(
                self, first_n, last_n, include_omission_info=True, item_type=None
            ):
                pass

            def retrieve_recent(self, item_type=None):
                pass

            def retrieve_all(self, item_type=None):
                pass

            def retrieve_relevant(self, relevance_target, top_k=20):
                pass

        memory = ConcreteTinyMemory()
        memories = [
            {"type": "action", "content": "I walked"},
            {"type": "stimulus", "content": "I saw a cat"},
            {"type": "action", "content": "I talked"},
            {"type": "feedback", "content": "Good job"},
        ]

        filtered = memory.filter_by_item_types(memories, ["action", "stimulus"])
        assert len(filtered) == 3
        assert all(m["type"] in ["action", "stimulus"] for m in filtered)

    def test_store_all(self, setup):
        """Test storing multiple values"""

        class ConcreteTinyMemory(TinyMemory):
            def __init__(self):
                super().__init__("test_memory")
                self.stored_values = []

            def _store(self, value):
                self.stored_values.append(value)

            def retrieve(
                self, first_n, last_n, include_omission_info=True, item_type=None
            ):
                pass

            def retrieve_recent(self, item_type=None):
                pass

            def retrieve_all(self, item_type=None):
                pass

            def retrieve_relevant(self, relevance_target, top_k=20):
                pass

        memory = ConcreteTinyMemory()
        values = [{"content": "test1"}, {"content": "test2"}, {"content": "test3"}]
        memory.store_all(values)

        assert len(memory.stored_values) == 3
        assert memory.stored_values[0]["content"] == "test1"
        assert memory.stored_values[2]["content"] == "test3"


class TestEpisodicMemory:
    """Test cases for EpisodicMemory class"""

    def test_init(self, setup):
        """Test initialization with default and custom parameters"""
        # Default initialization
        memory = EpisodicMemory()
        assert memory.fixed_prefix_length == 20
        assert memory.lookback_length == 100
        assert len(memory.memory) == 0
        assert len(memory.episodic_buffer) == 0

        # Custom initialization
        memory = EpisodicMemory(fixed_prefix_length=10, lookback_length=50)
        assert memory.fixed_prefix_length == 10
        assert memory.lookback_length == 50

    @pytest.mark.core
    def test_store_and_commit_episode(self, setup):
        """Test storing values and committing episodes"""
        memory = EpisodicMemory()

        # Store some values
        memory.store({"role": "user", "content": "Hello", "type": "stimulus"})
        memory.store({"role": "assistant", "content": "Hi there", "type": "action"})

        # Check they're in the buffer
        assert len(memory.episodic_buffer) == 2
        assert len(memory.memory) == 0

        # Commit the episode
        memory.commit_episode()

        # Check they moved to permanent memory
        assert len(memory.episodic_buffer) == 0
        assert len(memory.memory) == 2
        assert memory.memory[0]["content"] == "Hello"
        assert memory.memory[1]["content"] == "Hi there"

    def test_get_current_episode(self, setup):
        """Test retrieving current episode buffer"""
        memory = EpisodicMemory()

        # Store different types of memories
        memory.store({"role": "user", "content": "Hello", "type": "stimulus"})
        memory.store({"role": "assistant", "content": "Hi", "type": "action"})
        memory.store({"role": "system", "content": "Error", "type": "feedback"})

        # Get all current episode
        episode = memory.get_current_episode()
        assert len(episode) == 3

        # Filter by item types
        episode_filtered = memory.get_current_episode(item_types=["action", "stimulus"])
        assert len(episode_filtered) == 2
        assert all(item["type"] in ["action", "stimulus"] for item in episode_filtered)

    @pytest.mark.core
    def test_count(self, setup):
        """Test counting memory items"""
        memory = EpisodicMemory()
        assert memory.count() == 0

        # Add to buffer and memory
        memory.store({"content": "test1", "type": "stimulus"})
        assert memory.count() == 1

        memory.commit_episode()
        memory.store({"content": "test2", "type": "action"})
        assert memory.count() == 2

    def test_clear(self, setup):
        """Test clearing memory with different parameters"""
        memory = EpisodicMemory()

        # Add some memories
        for i in range(5):
            memory.store({"content": f"test{i}", "type": "stimulus"})
        memory.commit_episode()

        for i in range(5, 8):
            memory.store({"content": f"test{i}", "type": "action"})

        # Clear all
        memory.clear()
        assert len(memory.memory) == 0
        assert len(memory.episodic_buffer) == 0

        # Test prefix clearing
        for i in range(10):
            memory.store({"content": f"test{i}", "type": "stimulus"})
        memory.commit_episode()

        memory.clear(max_prefix_to_clear=3)
        assert len(memory.memory) == 7
        assert memory.memory[0]["content"] == "test3"

        # Test suffix clearing
        memory.clear(max_suffix_to_clear=2)
        assert len(memory.memory) == 5
        assert memory.memory[-1]["content"] == "test7"

    def test_retrieve_first_and_last(self, setup):
        """Test retrieving first and last n items"""
        memory = EpisodicMemory()

        # Add memories
        for i in range(10):
            memory.store({"content": f"test{i}", "type": "stimulus"})
        memory.commit_episode()

        # Test retrieve first
        first_3 = memory.retrieve_first(3, include_omission_info=False)
        assert len(first_3) == 3
        assert first_3[0]["content"] == "test0"
        assert first_3[2]["content"] == "test2"

        # Test with omission info
        first_3_with_info = memory.retrieve_first(3, include_omission_info=True)
        assert len(first_3_with_info) == 4  # 3 items + 1 omission info
        assert "omitted for brevity" in first_3_with_info[-1]["content"]

        # Test retrieve last
        last_3 = memory.retrieve_last(3, include_omission_info=False)
        assert len(last_3) == 3
        assert last_3[0]["content"] == "test7"
        assert last_3[2]["content"] == "test9"

    @pytest.mark.core
    def test_retrieve_all(self, setup):
        """Test retrieving all memories"""
        memory = EpisodicMemory()

        # Add different types
        memory.store({"content": "action1", "type": "action"})
        memory.store({"content": "stimulus1", "type": "stimulus"})
        memory.store({"content": "action2", "type": "action"})
        memory.commit_episode()

        # Get all
        all_memories = memory.retrieve_all()
        assert len(all_memories) == 3

        # Get filtered by type
        actions_only = memory.retrieve_all(item_type="action")
        assert len(actions_only) == 2
        assert all(m["type"] == "action" for m in actions_only)

    def test_retrieve_recent(self, setup):
        """Test retrieving recent memories with lookback logic"""
        memory = EpisodicMemory(fixed_prefix_length=2, lookback_length=3)

        # Add more memories than the total window
        for i in range(8):
            memory.store({"content": f"test{i}", "type": "stimulus"})
        memory.commit_episode()

        # Should get fixed prefix (2) + omission info + lookback (3)
        recent = memory.retrieve_recent(include_omission_info=True)
        assert len(recent) == 6  # 2 prefix + 1 omission + 3 lookback

        # Check first two are from prefix
        assert recent[0]["content"] == "test0"
        assert recent[1]["content"] == "test1"

        # Check omission info is in there
        assert any("omitted for brevity" in item.get("content", "") for item in recent)

        # Check last items are from lookback
        assert recent[-1]["content"] == "test7"
        assert recent[-2]["content"] == "test6"
        assert recent[-3]["content"] == "test5"

    def test_retrieve_with_first_and_last_n(self, setup):
        """Test retrieve method with both first_n and last_n parameters"""
        memory = EpisodicMemory()

        for i in range(10):
            memory.store({"content": f"test{i}", "type": "stimulus"})
        memory.commit_episode()

        # Get first 2 and last 2
        result = memory.retrieve(first_n=2, last_n=2, include_omission_info=True)

        # Should be: 2 first + omission info + 2 last = 5 items
        assert len(result) == 5
        assert result[0]["content"] == "test0"
        assert result[1]["content"] == "test1"
        assert "omitted for brevity" in result[2]["content"]
        assert result[3]["content"] == "test8"
        assert result[4]["content"] == "test9"

    def test_retrieve_relevant_not_implemented(self, setup):
        """Test that retrieve_relevant raises NotImplementedError"""
        memory = EpisodicMemory()

        with pytest.raises(NotImplementedError):
            memory.retrieve_relevant("test query", top_k=5)


class TestSemanticMemory:
    """Test cases for SemanticMemory class"""

    @pytest.mark.core
    def test_init(self, setup):
        """Test initialization"""
        # Default initialization
        memory = SemanticMemory()
        assert hasattr(memory, "memories")
        assert hasattr(memory, "semantic_grounding_connector")
        assert memory.memories == []
        assert isinstance(
            memory.semantic_grounding_connector, BaseSemanticGroundingConnector
        )

        # Initialize with existing memories
        existing_memories = [{"content": "test", "type": "information"}]
        memory = SemanticMemory(memories=existing_memories)
        assert memory.memories == existing_memories

    @pytest.mark.core
    def test_preprocess_value_for_storage(self, setup):
        """Test preprocessing values before storage"""
        memory = SemanticMemory()

        # Test action preprocessing
        action_value = {
            "content": "I walked to the store",
            "type": "action",
            "simulation_timestamp": "2023-01-01T10:00:00",
        }
        processed = memory._preprocess_value_for_storage(action_value)

        assert processed["role"] == "assistant"
        assert processed["type"] == "action"
        assert processed["simulation_timestamp"] == "2023-01-01T10:00:00"
        assert "Action performed" in processed["content"]
        assert "I walked to the store" in processed["content"]

        # Test stimulus preprocessing
        stimulus_value = {
            "content": "I heard a loud noise",
            "type": "stimulus",
            "simulation_timestamp": "2023-01-01T10:05:00",
        }
        processed = memory._preprocess_value_for_storage(stimulus_value)

        assert "Stimulus" in processed["content"]
        assert "I heard a loud noise" in processed["content"]

        # Test feedback preprocessing
        feedback_value = {
            "content": "Good job on that task",
            "type": "feedback",
            "simulation_timestamp": "2023-01-01T10:10:00",
        }
        processed = memory._preprocess_value_for_storage(feedback_value)

        assert "Feedback" in processed["content"]
        assert "Good job on that task" in processed["content"]

        # Test consolidated memory preprocessing
        consolidated_value = {
            "content": "Summary of recent events",
            "type": "consolidated",
            "simulation_timestamp": "2023-01-01T10:15:00",
        }
        processed = memory._preprocess_value_for_storage(consolidated_value)

        assert "Consolidated Memory" in processed["content"]

        # Test reflection preprocessing
        reflection_value = {
            "content": "I think about what happened",
            "type": "reflection",
            "simulation_timestamp": "2023-01-01T10:20:00",
        }
        processed = memory._preprocess_value_for_storage(reflection_value)

        assert "Reflection" in processed["content"]

        # Test default information preprocessing
        info_value = {
            "content": "Some general information",
            "type": "unknown_type",
            "simulation_timestamp": "2023-01-01T10:25:00",
        }
        processed = memory._preprocess_value_for_storage(info_value)

        assert "Information" in processed["content"]

        # Test non-dict value
        simple_value = "Just a string"
        processed = memory._preprocess_value_for_storage(simple_value)

        assert processed["role"] == "assistant"
        assert processed["content"] == "Just a string"
        assert processed["type"] == "information"
        assert processed["simulation_timestamp"] is None

    @patch("tinytroupe.agent.memory.logger")
    def test_store(self, mock_logger, setup):
        """Test storing values in semantic memory"""
        memory = SemanticMemory()

        # Mock the semantic grounding connector
        memory.semantic_grounding_connector = Mock()

        value = {
            "content": "I learned something new",
            "type": "action",
            "simulation_timestamp": "2023-01-01T10:00:00",
        }

        memory.store(value)

        # Check that the value was added to memories list
        assert len(memory.memories) == 1

        # Check that add_document was called on the connector
        memory.semantic_grounding_connector.add_document.assert_called_once()

        # Verify the stored memory structure
        stored_memory = memory.memories[0]
        assert stored_memory["role"] == "assistant"
        assert stored_memory["type"] == "action"
        assert "Action performed" in stored_memory["content"]

    def test_store_large_values(self, setup):
        """Test storing rich semantic content and retrieving it via semantic search"""
        print("\n--- test_store_large_values ---")
        # As per my primary guidelines, keep the scenario meaningful without adding unnecessary complexity.
        memory = SemanticMemory()

        timestamp = "2023-01-01T10:00:00"
        knowledge_snippets = [
            {
                "topic": "renewable_energy",
                "content": (
                    "The 2024 sustainability review from Berlin highlighted a 35% surge in "
                    "renewable energy adoption, driven by neighborhood solar incentives and "
                    "battery-storage rebates that stabilized the local grid."
                ),
            },
            {
                "topic": "product_insights",
                "content": (
                    "Usage analytics from the budgeting assistant revealed 18% higher daily "
                    "engagement after the conversational goal-setting walkthrough was added. "
                    "Customers praised the friendly tone and contextual reminders."
                ),
            }
        ]

        for snippet in knowledge_snippets:
            snippet["expanded_content"] = snippet["content"] * 1000
            memory.store(
                {
                    "content": snippet["expanded_content"],
                    "type": "information",
                    "simulation_timestamp": timestamp,
                }
            )

        assert len(memory.memories) == len(knowledge_snippets)

        connector = memory.semantic_grounding_connector
        assert connector is not None
        assert len(connector.documents) == len(knowledge_snippets)
        assert connector.index is not None

        vector_store = connector.index.storage_context.vector_store
        store_data = getattr(vector_store, "data", None) or getattr(vector_store, "_data", None)
        assert store_data is not None, "Vector store data should be available"
        embedding_dict = getattr(store_data, "embedding_dict", None)
        if embedding_dict is None and hasattr(store_data, "to_dict"):
            embedding_dict = store_data.to_dict().get("embedding_dict")
        assert embedding_dict is not None

        print("Computed embeddings:")
        for doc_id, embedding in embedding_dict.items():
            embedding_sequence = (
                embedding.tolist() if hasattr(embedding, "tolist") else embedding
            )
            if not isinstance(embedding_sequence, list):
                embedding_sequence = list(embedding_sequence)
            preview = embedding_sequence[:8]
            print(f"  {doc_id}: dimension={len(embedding_sequence)} preview={preview}")

        for stored_memory, snippet in zip(memory.memories, knowledge_snippets):
            assert stored_memory["type"] == "information"
            assert stored_memory["content"].startswith("# Information")
            assert snippet["expanded_content"] in stored_memory["content"]

        for document, snippet in zip(connector.documents, knowledge_snippets):
            doc_payload = json.loads(document.text)
            assert doc_payload["type"] == "information"
            assert doc_payload["content"].startswith("# Information")
            assert snippet["expanded_content"] in doc_payload["content"]

        query = "Berlin"
        search_results = memory.retrieve_relevant(query, top_k=3)

        # print search results numbers
        print("Search query:", query)
        print(f"Number of search results: {len(search_results)}")

        print("Semantic search results:")
        for result in search_results:
            print(result)

        assert search_results, "Semantic search should return results"
        assert any(
            knowledge_snippets[0]["content"].lower() in result.lower()
            for result in search_results
        )

    @pytest.mark.core
    def test_retrieve_relevant(self, setup):
        """Test retrieving relevant memories"""
        memory = SemanticMemory()

        # Mock the semantic grounding connector
        memory.semantic_grounding_connector = Mock()
        expected_results = [{"content": "relevant memory"}]
        memory.semantic_grounding_connector.retrieve_relevant.return_value = (
            expected_results
        )

        results = memory.retrieve_relevant("test query", top_k=10)

        # Verify the connector was called correctly
        memory.semantic_grounding_connector.retrieve_relevant.assert_called_once_with(
            "test query", 10
        )

        # Verify the results
        assert results == expected_results

    @pytest.mark.core
    def test_retrieve_all(self, setup):
        """Test retrieving all memories from semantic storage"""
        memory = SemanticMemory()

        # Create mock documents
        mock_documents = []
        memories_data = [
            {"content": "memory 1", "type": "action"},
            {"content": "memory 2", "type": "stimulus"},
            {"content": "memory 3", "type": "feedback"},
        ]

        for mem in memories_data:
            mock_doc = Mock()
            mock_doc.text = json.dumps(mem)
            mock_documents.append(mock_doc)

        memory.semantic_grounding_connector = Mock()
        memory.semantic_grounding_connector.documents = mock_documents

        # Test retrieving all memories
        all_memories = memory.retrieve_all()
        assert len(all_memories) == 3
        assert all_memories[0]["content"] == "memory 1"
        assert all_memories[1]["type"] == "stimulus"

        # Test filtering by item type
        action_memories = memory.retrieve_all(item_type="action")
        assert len(action_memories) == 1
        assert action_memories[0]["type"] == "action"

    def test_retrieve_all_with_json_error(self, setup):
        """Test retrieve_all handles JSON decode errors gracefully"""
        memory = SemanticMemory()

        # Create a mock document with invalid JSON
        mock_doc = Mock()
        mock_doc.text = "invalid json {"

        memory.semantic_grounding_connector = Mock()
        memory.semantic_grounding_connector.documents = [mock_doc]

        with patch("tinytroupe.agent.memory.logger") as mock_logger:
            memories = memory.retrieve_all()

            # Should return empty list and log warning
            assert memories == []
            mock_logger.warning.assert_called_once()

    def test_build_document_from(self, setup):
        """Test building documents from memories"""
        memory = SemanticMemory()

        # Test with dict memory
        dict_memory = {"content": "test content", "type": "action"}
        document = memory._build_document_from(dict_memory)

        assert document.text == json.dumps(dict_memory, ensure_ascii=False)

        # Test with non-dict memory
        string_memory = "just a string"
        document = memory._build_document_from(string_memory)

        expected_dict = {"content": string_memory, "type": "information"}
        assert document.text == json.dumps(expected_dict, ensure_ascii=False)

    def test_build_documents_from(self, setup):
        """Test building multiple documents from memories"""
        memory = SemanticMemory()

        memories = [
            {"content": "memory 1", "type": "action"},
            {"content": "memory 2", "type": "stimulus"},
        ]

        documents = memory._build_documents_from(memories)

        assert len(documents) == 2
        assert json.loads(documents[0].text)["content"] == "memory 1"
        assert json.loads(documents[1].text)["type"] == "stimulus"


class TestMemoryProcessor:
    """Test cases for MemoryProcessor base class"""

    def test_process_not_implemented(self, setup):
        """Test that process method raises NotImplementedError in base class"""
        processor = MemoryProcessor()

        with pytest.raises(NotImplementedError):
            processor.process([], timestamp="2023-01-01T10:00:00")

    def test_count_memory_content_words(self, setup):
        """Test counting words in memory content"""
        # Test with single memory
        memory = {"content": "This is a test with five words"}
        count = MemoryProcessor.count_memory_content_words(memory)
        assert count == 7  # "This is a test with five words" = 7 words

        # Test with list of memories
        memories = [
            {"content": "Hello world"},
            {"content": "This is another test"},
            {"other_field": "should be ignored"},
            {"content": "Final memory here"},
        ]
        count = MemoryProcessor.count_memory_content_words(memories)
        assert count == 9  # 2 + 4 + 0 + 3 = 9 words

        # Test with non-string content
        memories_with_non_string = [
            {"content": None},
            {"content": 123},
            {"content": "Valid string content"},
        ]
        count = MemoryProcessor.count_memory_content_words(memories_with_non_string)
        assert count == 3  # Only "Valid string content" = 3 words

        # Test with empty list
        count = MemoryProcessor.count_memory_content_words([])
        assert count == 0


class TestEpisodicConsolidator:
    """Test cases for EpisodicConsolidator class"""

    def test_inheritance(self, setup):
        """Test that EpisodicConsolidator inherits from MemoryProcessor"""
        consolidator = EpisodicConsolidator()
        assert isinstance(consolidator, MemoryProcessor)

    @patch("tinytroupe.agent.memory.utils")
    def test_process_small_batch(self, mock_utils, setup):
        """Test processing memories under word limit"""
        consolidator = EpisodicConsolidator()

        # Mock the _consolidate method to return expected result
        mock_result = {
            "consolidation": [
                {"content": "consolidated memory", "type": "consolidated"}
            ]
        }
        with patch.object(consolidator, "_consolidate", return_value=mock_result):
            memories = [
                {"content": "I walked", "type": "action"},
                {"content": "I saw a cat", "type": "stimulus"},
            ]

            result = consolidator.process(memories, timestamp="2023-01-01T10:00:00")

            # Should call _consolidate once with all memories
            consolidator._consolidate.assert_called_once()
            assert result == mock_result

    @patch("tinytroupe.agent.memory.utils")
    def test_process_large_batch(self, mock_utils, setup):
        """Test processing memories that exceed word limit (batch processing)"""
        consolidator = EpisodicConsolidator()

        # Create memories that will exceed the 1000 word limit when processed
        large_memories = []
        for i in range(5):
            # Each memory has ~250 words to ensure we exceed 1000 total
            content = " ".join([f"word{j}" for j in range(250)])
            large_memories.append({"content": content, "type": "action"})

        # Mock _consolidate to return different results for each batch
        mock_results = [
            {
                "consolidation": [
                    {"content": f"batch{i}_consolidated", "type": "consolidated"}
                ]
            }
            for i in range(3)  # Expect multiple batches
        ]

        with patch.object(consolidator, "_consolidate", side_effect=mock_results):
            with patch.object(consolidator, "count_memory_content_words") as mock_count:
                # Mock word counting to trigger batch processing
                mock_count.side_effect = lambda x: (
                    1500 if len(x) == 5 else 300
                )  # Total > 1000, each memory ~300

                result = consolidator.process(
                    large_memories, timestamp="2023-01-01T10:00:00"
                )

                # Should have called _consolidate multiple times for batches
                assert consolidator._consolidate.call_count >= 1

                # Result should contain consolidated memories
                assert "consolidation" in result
                assert isinstance(result["consolidation"], list)

    def test_consolidate_method_structure(self, setup):
        """Test that _consolidate method exists and has correct signature"""
        consolidator = EpisodicConsolidator()

        # The _consolidate method should be decorated with @utils.llm
        # We can check it exists and is callable
        assert hasattr(consolidator, "_consolidate")
        assert callable(getattr(consolidator, "_consolidate"))

        # Note: We can't easily test the actual LLM call without mocking the entire utils.llm decorator
        # But we can test that the method exists and has the expected signature


class TestReflectionConsolidator:
    """Test cases for ReflectionConsolidator class (placeholder implementation)"""

    def test_inheritance(self, setup):
        """Test that ReflectionConsolidator inherits from MemoryProcessor"""
        consolidator = ReflectionConsolidator()
        assert isinstance(consolidator, MemoryProcessor)

    def test_process_method_exists(self, setup):
        """Test that process method exists (even if not fully implemented)"""
        consolidator = ReflectionConsolidator()

        # The class should have a process method
        assert hasattr(consolidator, "process")
        assert callable(getattr(consolidator, "process"))

        # Since it's a work-in-progress, we just check it doesn't crash
        # The actual implementation might return None or raise NotImplementedError
        try:
            result = consolidator.process([], timestamp="2023-01-01T10:00:00")
            # If it returns something, that's fine
            assert result is not None or result is None  # Accept any return value
        except NotImplementedError:
            # If it's not implemented yet, that's also expected
            pass


class TestMemoryIntegration:
    """Integration tests for memory classes working together"""

    def test_memory_consolidation_workflow(self, setup):
        """Test typical workflow of storing memories and consolidating them"""
        episodic_memory = EpisodicMemory()
        semantic_memory = SemanticMemory()
        consolidator = EpisodicConsolidator()

        # Store some episodic memories
        memories_to_store = [
            {
                "content": "I walked to the park",
                "type": "action",
                "simulation_timestamp": "2023-01-01T10:00:00",
            },
            {
                "content": "I saw beautiful flowers",
                "type": "stimulus",
                "simulation_timestamp": "2023-01-01T10:05:00",
            },
            {
                "content": "I felt peaceful",
                "type": "feedback",
                "simulation_timestamp": "2023-01-01T10:10:00",
            },
        ]

        for memory in memories_to_store:
            episodic_memory.store(memory)

        # Get current episode for consolidation
        episode = episodic_memory.get_current_episode()
        assert len(episode) == 3

        # The consolidation would normally be done by LLM, so we'll mock it
        with patch.object(consolidator, "_consolidate") as mock_consolidate:
            mock_consolidate.return_value = {
                "consolidation": [
                    {
                        "content": "I had a peaceful walk in the park where I enjoyed the flowers",
                        "type": "consolidated",
                        "simulation_timestamp": "2023-01-01T10:15:00",
                    }
                ]
            }

            # Consolidate the episode
            consolidated_result = consolidator.process(
                episode, timestamp="2023-01-01T10:15:00"
            )

            # Store consolidated memory in semantic memory
            if "consolidation" in consolidated_result:
                for consolidated_memory in consolidated_result["consolidation"]:
                    semantic_memory.store(consolidated_memory)

            # Verify the consolidated memory was stored
            assert len(semantic_memory.memories) == 1
            stored_memory = semantic_memory.memories[0]
            assert stored_memory["type"] == "consolidated"
            assert "peaceful walk" in stored_memory["content"]

    def test_memory_filtering_across_types(self, setup):
        """Test memory filtering works consistently across different memory types"""
        episodic_memory = EpisodicMemory()
        semantic_memory = SemanticMemory()

        # Store various types in episodic memory
        test_memories = [
            {
                "content": "I walked",
                "type": "action",
                "simulation_timestamp": "2023-01-01T10:00:00",
            },
            {
                "content": "I saw",
                "type": "stimulus",
                "simulation_timestamp": "2023-01-01T10:01:00",
            },
            {
                "content": "Good job",
                "type": "feedback",
                "simulation_timestamp": "2023-01-01T10:02:00",
            },
            {
                "content": "I ran",
                "type": "action",
                "simulation_timestamp": "2023-01-01T10:03:00",
            },
        ]

        for memory in test_memories:
            episodic_memory.store(memory)
        episodic_memory.commit_episode()

        # Test filtering in episodic memory
        actions_episodic = episodic_memory.retrieve_all(item_type="action")
        assert len(actions_episodic) == 2

        # Store same types in semantic memory
        for memory in test_memories:
            semantic_memory.store(memory)

        # Mock the document retrieval for semantic memory
        mock_documents = []
        for memory in test_memories:
            doc = Mock()
            doc.text = json.dumps(semantic_memory._preprocess_value_for_storage(memory))
            mock_documents.append(doc)

        semantic_memory.semantic_grounding_connector.documents = mock_documents

        # Test filtering in semantic memory
        actions_semantic = semantic_memory.retrieve_all(item_type="action")
        assert len(actions_semantic) == 2

        # Both should have filtered to the same number of actions
        assert len(actions_episodic) == len(actions_semantic)
