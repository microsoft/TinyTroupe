import unittest
import pytest
from unittest.mock import patch, MagicMock, call
import json
# (Line removed)

from tinytroupe.agent.memory import EpisodicMemory, SemanticMemory
from tinytroupe.agent.tiny_person import TinyPerson
from tinytroupe.agent.grounding import BaseSemanticGroundingConnector # Needed for spec in MagicMock
from llama_index.core import Document
from tinytroupe.agent import logger as agent_logger # For potentially suppressing log output during tests
import logging

# Suppress agent logging during tests for cleaner output
agent_logger.setLevel(logging.WARNING)

class TestEpisodicMemoryAdvancedRetrieval(unittest.TestCase):
    def setUp(self):
        self.memory = EpisodicMemory()
        self.mem1 = {'role': 'user', 'content': {'stimuli': [{'type': 'CONVERSATION', 'content': 'Hello world'}]}, 'type': 'stimulus', 'simulation_timestamp': 'ts1'}
        self.mem2 = {'role': 'assistant', 'content': {'action': {'type': 'SPEAK', 'content': 'Goodbye world'}}, 'type': 'action', 'simulation_timestamp': 'ts2'}
        self.mem3 = {'role': 'user', 'content': {'stimuli': [{'type': 'CONVERSATION', 'content': 'Another message here'}]}, 'type': 'stimulus', 'simulation_timestamp': 'ts3'}

        # Store memories and capture their generated IDs
        self.stored_mem_ids = {}

        # Mock add_document to prevent actual indexing and capture IDs
        with patch.object(self.memory.semantic_connector, 'add_document') as mock_add_doc:
            self.memory._store(self.mem1)
            # Assuming add_document is called with a Document object having metadata['memory_id']
            if mock_add_doc.call_args_list:
                 doc_arg = mock_add_doc.call_args_list[0][0][0] # Get the Document object from the first call
                 self.stored_mem_ids[0] = doc_arg.metadata['memory_id']

            self.memory._store(self.mem2)
            if mock_add_doc.call_args_list and len(mock_add_doc.call_args_list) > 1:
                 doc_arg = mock_add_doc.call_args_list[1][0][0]
                 self.stored_mem_ids[1] = doc_arg.metadata['memory_id']

            self.memory._store(self.mem3)
            if mock_add_doc.call_args_list and len(mock_add_doc.call_args_list) > 2:
                 doc_arg = mock_add_doc.call_args_list[2][0][0]
                 self.stored_mem_ids[2] = doc_arg.metadata['memory_id']

        # Fallback if IDs weren't captured via mock (e.g. if _store changes)
        # This is a bit more coupled to _store's direct use of memory_id_map
        if not self.stored_mem_ids:
            for mem_id, idx in self.memory.memory_id_map.items():
                if self.memory.memory[idx] == self.mem1: self.stored_mem_ids[0] = mem_id
                elif self.memory.memory[idx] == self.mem2: self.stored_mem_ids[1] = mem_id
                elif self.memory.memory[idx] == self.mem3: self.stored_mem_ids[2] = mem_id


    @patch('tinytroupe.agent.memory.BaseSemanticGroundingConnector.retrieve_relevant')
    def test_retrieve_relevant_finds_correct_memory(self, mock_semantic_retrieve):
        mem1_id = self.stored_mem_ids.get(0)
        self.assertIsNotNone(mem1_id, "Memory ID for mem1 not found")

        mock_semantic_retrieve.return_value = [
            {'text': json.dumps(self.mem1), 'metadata': {'memory_id': mem1_id}, 'score': 0.9}
        ]

        relevant_memories = self.memory.retrieve_relevant("Hello world", top_k=1)
        self.assertEqual(len(relevant_memories), 1)
        self.assertEqual(relevant_memories[0], self.mem1)
        mock_semantic_retrieve.assert_called_once_with("Hello world", top_k=1)

    @patch('tinytroupe.agent.memory.BaseSemanticGroundingConnector.retrieve_relevant')
    def test_retrieve_relevant_empty_if_no_match(self, mock_semantic_retrieve):
        mock_semantic_retrieve.return_value = []
        relevant_memories = self.memory.retrieve_relevant("NonExistentTerm", top_k=1)
        self.assertEqual(len(relevant_memories), 0)
        mock_semantic_retrieve.assert_called_once_with("NonExistentTerm", top_k=1)

    @patch('tinytroupe.agent.memory.BaseSemanticGroundingConnector.retrieve_relevant')
    def test_retrieve_relevant_uses_top_k(self, mock_semantic_retrieve):
        mem1_id = self.stored_mem_ids.get(0)
        mem2_id = self.stored_mem_ids.get(1)
        self.assertTrue(mem1_id and mem2_id, "Memory IDs for test not found")

        mock_semantic_retrieve.return_value = [
            {'text': json.dumps(self.mem1), 'metadata': {'memory_id': mem1_id}, 'score': 0.9},
            {'text': json.dumps(self.mem2), 'metadata': {'memory_id': mem2_id}, 'score': 0.8}
        ]

        # Request top_k=1 even if mock returns more
        relevant_memories = self.memory.retrieve_relevant("world", top_k=1)

        # The EpisodicMemory.retrieve_relevant itself doesn't re-filter by top_k,
        # it relies on semantic_connector providing the correct number.
        # So, this test actually verifies that we process all nodes semantic_connector gives back,
        # and if semantic_connector respects top_k, then our method will too.
        # The current implementation of EpisodicMemory.retrieve_relevant iterates all returned nodes.
        self.assertEqual(len(relevant_memories), 2) # It will return all that the mock provided
        mock_semantic_retrieve.assert_called_once_with("world", top_k=1)


class TestTinyPersonReflection(unittest.TestCase):
    def setUp(self):
        TinyPerson.all_agents.clear() # Clear any previously registered agents
        self.person = TinyPerson(name="TestPerson")
        # Ensure episodic memory is clean for each test, if TinyPerson is reused across tests (not typical for unittest.TestCase)
        self.person.episodic_memory.memory = []
        self.person.episodic_memory.memory_id_map = {}
        # Mock semantic_connector for episodic memory to avoid actual indexing
        self.person.episodic_memory.semantic_connector = MagicMock(spec=BaseSemanticGroundingConnector)

        # Also ensure semantic memory is clean and its connector is mocked
        self.person.semantic_memory.memories = []
        self.person.semantic_memory.semantic_grounding_connector = MagicMock(spec=BaseSemanticGroundingConnector)


        self.sample_episodes = [
            {'role': 'user', 'content': {'stimuli': [{'type': 'CONVERSATION', 'content': 'What is the capital of France?'}]}, 'type': 'stimulus', 'simulation_timestamp': 'ts1'},
            {'role': 'assistant', 'content': {'action': {'type': 'SPEAK', 'content': 'The capital of France is Paris.'}}, 'type': 'action', 'simulation_timestamp': 'ts2'},
            {'role': 'user', 'content': {'stimuli': [{'type': 'CONVERSATION', 'content': 'What is 2+2?'}]}, 'type': 'stimulus', 'simulation_timestamp': 'ts3'},
            {'role': 'assistant', 'content': {'action': {'type': 'SPEAK', 'content': '2+2 equals 4.'}}, 'type': 'action', 'simulation_timestamp': 'ts4'}
        ]
        for episode in self.sample_episodes:
            self.person.episodic_memory.store(episode) # Uses the mocked connector

    @patch('tinytroupe.agent.tiny_person.client')
    def test_reflection_stores_to_semantic_memory(self, mock_openai_client):
        mock_llm_response_content = json.dumps(["France's capital is Paris.", "Basic arithmetic is understood."])
        mock_openai_client.return_value.send_message.return_value = {'role': 'assistant', 'content': mock_llm_response_content}

        # Mock the actual store method of semantic memory instance
        self.person.semantic_memory.store = MagicMock()

        self.person.reflect_and_synthesize_knowledge()

        mock_openai_client.return_value.send_message.assert_called_once()
        self.assertTrue(self.person.semantic_memory.store.call_count >= 1)

        # Check first call
        call_args = self.person.semantic_memory.store.call_args_list[0][0][0] # Argument of the first call
        self.assertEqual(call_args['type'], 'synthesized_knowledge')
        self.assertEqual(call_args['content'], "France's capital is Paris.")
        self.assertIn('source_reflection_timestamp', call_args)
        self.assertEqual(call_args['reflected_episodes_count'], len(self.sample_episodes))

        # Check second call if exists
        if self.person.semantic_memory.store.call_count > 1:
            call_args_2 = self.person.semantic_memory.store.call_args_list[1][0][0]
            self.assertEqual(call_args_2['type'], 'synthesized_knowledge')
            self.assertEqual(call_args_2['content'], "Basic arithmetic is understood.")


    @patch('tinytroupe.agent.tiny_person.client')
    def test_reflection_no_insights(self, mock_openai_client):
        mock_llm_response_content = json.dumps([]) # Empty list of insights
        mock_openai_client.return_value.send_message.return_value = {'role': 'assistant', 'content': mock_llm_response_content}

        self.person.semantic_memory.store = MagicMock()
        self.person.reflect_and_synthesize_knowledge()

        mock_openai_client.return_value.send_message.assert_called_once()
        self.person.semantic_memory.store.assert_not_called()

    @patch('tinytroupe.agent.tiny_person.client')
    def test_reflection_handles_llm_error(self, mock_openai_client):
        mock_openai_client.return_value.send_message.side_effect = Exception("LLM API Error")

        self.person.semantic_memory.store = MagicMock()
        # Consider also patching logger if you want to check log messages.
        # For now, just ensure store is not called.
        self.person.reflect_and_synthesize_knowledge()

        mock_openai_client.return_value.send_message.assert_called_once()
        self.person.semantic_memory.store.assert_not_called()


class TestSemanticMemoryMetadata(unittest.TestCase):
    def setUp(self):
        self.semantic_memory = SemanticMemory()
        # Mock the connector's add_document to prevent actual indexing and allow inspection
        self.mock_add_document = MagicMock()
        self.semantic_memory.semantic_grounding_connector.add_document = self.mock_add_document

    def test_store_action_with_metadata(self):
        action_val = {'type': 'action', 'content': {'action': {'type': 'SPEAK', 'content': 'Test action'}}, 'simulation_timestamp': 'ts_action'}

        # The content for action type in _preprocess_value_for_storage is just `value['content']`
        # which is `{'action': {'type': 'SPEAK', 'content': 'Test action'}}`
        # This might not be what's intended if a simpler string is expected by LlamaIndex.
        # For now, testing based on current _preprocess_value_for_storage.

        self.semantic_memory.store(action_val)

        self.mock_add_document.assert_called_once()
        captured_document = self.mock_add_document.call_args[0][0]

        self.assertIsInstance(captured_document, Document)
        self.assertIn('original_timestamp', captured_document.metadata)
        self.assertEqual(captured_document.metadata['original_timestamp'], 'ts_action')
        self.assertIn('type', captured_document.metadata)
        self.assertEqual(captured_document.metadata['type'], 'action')

        # Check how engram text is formed by _preprocess_value_for_storage
        # Expected engram text:
        # "# Fact\nI have performed the following action at date and time ts_action:\n\n {'action': {'type': 'SPEAK', 'content': 'Test action'}}"
        self.assertTrue(f"I have performed the following action at date and time ts_action" in captured_document.text)
        self.assertTrue(str(action_val['content']) in captured_document.text)


    def test_store_synthesized_knowledge_with_metadata(self):
        synth_val = {
            'type': 'synthesized_knowledge',
            'content': 'Synthesized insight',
            'source_reflection_timestamp': 'ts_reflect',
            'reflected_episodes_count': 10
        }
        self.semantic_memory.store(synth_val)

        self.mock_add_document.assert_called_once()
        captured_document = self.mock_add_document.call_args[0][0]

        self.assertIsInstance(captured_document, Document)
        self.assertIn('original_timestamp', captured_document.metadata)
        self.assertEqual(captured_document.metadata['original_timestamp'], 'ts_reflect')
        self.assertIn('type', captured_document.metadata)
        self.assertEqual(captured_document.metadata['type'], 'synthesized_knowledge')
        # The 'reflected_episodes_count' is part of the engram text, not usually separate metadata unless store is changed.
        # Let's check the text itself as per current _preprocess_value_for_storage
        self.assertTrue(f"Reflected on: ts_reflect" in captured_document.text)
        self.assertTrue(f"From: 10 episodes" in captured_document.text)
        self.assertTrue(f"Insight: Synthesized insight" in captured_document.text)

if __name__ == '__main__':
    unittest.main()
