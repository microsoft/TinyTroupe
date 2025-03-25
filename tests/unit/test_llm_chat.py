import sys
import pytest
from typing import List, Dict, Union
from pydantic import BaseModel

sys.path.append('../../tinytroupe/')
sys.path.append('../../')
sys.path.append('..')

from tinytroupe.utils.llm import LLMChat

class TestLLMChat:
    def test_initialization(self):
        """Test that LLMChat can be initialized with system and user prompts."""
        chat = LLMChat(
            system_prompt="You are a helpful assistant.",
            user_prompt="Tell me a joke."
        )
        assert chat.system_prompt == "You are a helpful assistant."
        assert chat.user_prompt == "Tell me a joke."
        assert chat.messages == []
        
    def test_simple_call(self):
        """Test that LLMChat can make a simple API call and get a response."""
        chat = LLMChat(
            system_prompt="You are a helpful assistant.",
            user_prompt="Tell me a joke about programming."
        )
        response = chat.call()
        assert isinstance(response, str)
        assert len(response) > 0
        assert len(chat.messages) > 0  # Messages should be populated after call
        assert len(chat.conversation_history) > 0  # Conversation history should be tracked
        
    def test_bool_output(self):
        """Test that LLMChat can return boolean output."""
        chat = LLMChat(
            system_prompt="You are a helpful assistant.",
            user_prompt="Is the sky blue on a clear day?",
            output_type=bool
        )
        response = chat.call()
        assert isinstance(response, bool)
        assert chat.response_justification is not None
        assert isinstance(chat.response_confidence, float)
        
    def test_int_output(self):
        """Test that LLMChat can return integer output."""
        chat = LLMChat(
            system_prompt="You are a mathematical assistant.",
            user_prompt="What is the result of 5 + 7?",
            output_type=int
        )
        response = chat.call()
        assert isinstance(response, int)
        assert response == 12
        
    def test_float_output(self):
        """Test that LLMChat can return float output."""
        chat = LLMChat(
            system_prompt="You are a mathematical assistant.",
            user_prompt="What is the approximate value of pi to 2 decimal places?",
            output_type=float
        )
        response = chat.call()
        assert isinstance(response, float)
        assert 3.13 < response < 3.15  # Allow small variation
        
    def test_enum_output(self):
        """Test that LLMChat can return an option from a predefined list."""
        options = ["red", "blue", "green"]
        chat = LLMChat(
            system_prompt="You are a color assistant.",
            user_prompt="Which of these colors is considered a primary color: red, blue, green?",
            output_type=options
        )
        response = chat.call()
        assert response in options
        
    def test_dict_output(self):
        """Test that LLMChat can return dictionary output."""
        chat = LLMChat(
            system_prompt="You are a data processing assistant.",
            user_prompt="Give me information about a book in JSON format with title and author fields.",
            output_type=dict
        )
        response = chat.call()
        assert isinstance(response, dict)
        assert len(response) > 0
        
    def test_list_output(self):
        """Test that LLMChat can return list output."""
        chat = LLMChat(
            system_prompt="You are a list-making assistant.",
            user_prompt="Give me a list of three countries.",
            output_type=list
        )
        response = chat.call()
        assert isinstance(response, list)
        assert len(response) > 0
        
    def test_pydantic_model_output(self):
        """Test that LLMChat can return a Pydantic model output."""
        class Book(BaseModel):
            title: str
            author: str
            year: int
            
        chat = LLMChat(
            system_prompt="You are a book information assistant.",
            user_prompt="Give me information about the book '1984' by George Orwell.",
            output_type=Book
        )
        response = chat.call()
        assert isinstance(response, Book)
        assert response.title
        assert response.author
        assert isinstance(response.year, int)
        
    def test_multi_turn_conversation(self):
        """Test that LLMChat supports multi-turn conversations."""
        chat = LLMChat(
            system_prompt="You are a helpful assistant.",
            user_prompt="Hello, who are you?"
        )
        
        # First turn
        response1 = chat.call()
        assert isinstance(response1, str)
        
        # Add user message and get response
        chat.add_user_message("What can you help me with?")
        response2 = chat.call()
        assert isinstance(response2, str)
        assert len(chat.messages) >= 4  # Should have system, user, assistant, user messages
        
    def test_continue_conversation(self):
        """Test the continue_conversation helper method."""
        chat = LLMChat(
            system_prompt="You are a helpful assistant.",
            user_prompt="Hello, who are you?"
        )
        
        # First turn
        response1 = chat.call()
        
        # Continue conversation with a new user message
        response2 = chat.continue_conversation("What can you help me with?")
        assert isinstance(response2, str)
        assert len(chat.messages) >= 4  # Should have multiple messages now
        
    def test_reset_conversation(self):
        """Test that conversation state can be reset."""
        chat = LLMChat(
            system_prompt="You are a helpful assistant.",
            user_prompt="Tell me a joke."
        )
        
        # Make a call
        response = chat.call()
        assert len(chat.messages) > 0
        
        # Reset conversation
        chat.reset_conversation()
        assert chat.messages == []
        assert chat.response_raw is None
        assert chat.response_value is None
        
    def test_add_messages(self):
        """Test adding different types of messages to the conversation."""
        chat = LLMChat(
            system_prompt="You are a helpful assistant.",
            user_prompt="Initial message."
        )
        
        # Add messages of different types
        chat.add_system_message("Additional system instruction.")
        chat.add_user_message("User follow-up question.")
        chat.add_assistant_message("Predefined assistant response.")
        
        # Check that messages were added correctly
        assert len(chat.messages) == 3
        assert chat.messages[0]["role"] == "system"
        assert chat.messages[1]["role"] == "user"
        assert chat.messages[2]["role"] == "assistant"
        
        # Make a call and verify conversation works
        response = chat.call()
        assert isinstance(response, str)
