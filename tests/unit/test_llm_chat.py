import sys
import pytest
from typing import List, Dict, Union
from pydantic import BaseModel
from unittest.mock import Mock, patch, MagicMock
import json

# Insert paths at the beginning of sys.path (position 0)
sys.path.insert(0, '..')
sys.path.insert(0, '../../')
sys.path.insert(0, '../../tinytroupe/')

from tinytroupe.utils.llm import LLMChat, LLMScalarWithJustificationResponse, LLMScalarWithJustificationAndReasoningResponse
from testing_utils import proposition_holds

class TestLLMChat:
    """Comprehensive tests for the LLMChat class covering all functionality."""
    
    # ==== BASIC INITIALIZATION AND CONFIGURATION TESTS ====
    
    def test_initialization(self):
        """Test that LLMChat can be initialized with system and user prompts."""
        chat = LLMChat(
            system_prompt="You are a helpful assistant.",
            user_prompt="Tell me a joke."
        )
        assert chat.system_prompt == "You are a helpful assistant."
        assert chat.user_prompt == "Tell me a joke."
        assert chat.messages == []
    
    def test_initialization_with_templates(self):
        """Test initialization with template names."""
        chat = LLMChat(
            system_template_name="test_system.mustache",
            user_template_name="test_user.mustache"
        )
        assert chat.system_template_name == "test_system.mustache"
        assert chat.user_template_name == "test_user.mustache"
        assert chat.system_prompt is None
        assert chat.user_prompt is None
    
    def test_initialization_validation_errors(self):
        """Test that initialization properly validates input parameters."""
        # Both template and prompt specified should raise error
        with pytest.raises(ValueError, match="Either the template or the prompt must be specified"):
            LLMChat(
                system_template_name="test.mustache",
                system_prompt="Test prompt"
            )
        
        # Neither template nor prompt specified should raise error  
        with pytest.raises(ValueError, match="Either the template or the prompt must be specified"):
            LLMChat()
    
    def test_initialization_with_configuration_options(self):
        """Test initialization with various configuration options."""
        chat = LLMChat(
            system_prompt="Test system",
            user_prompt="Test user",
            output_type=str,
            enable_json_output_format=False,
            enable_justification_step=False,
            enable_reasoning_step=False,
            temperature=0.7,
            max_tokens=100
        )
        
        assert chat.enable_json_output_format == False
        assert chat.enable_justification_step == False
        assert chat.enable_reasoning_step == False
        assert chat.model_params["temperature"] == 0.7
        assert chat.model_params["max_tokens"] == 100
    
    # ==== BASIC FUNCTIONALITY TESTS ====
        
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
        
        # Semantic verification: check that the response is actually a programming joke
        assert proposition_holds(f"The following text is a joke about programming or coding: '{response}'"), \
            f"Response should be a programming joke but got: {response}"
    
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

    # ==== OUTPUT TYPE TESTS ====
        
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
        
        # Semantic verification: check that the response contains book-related information
        response_str = str(response).lower()
        # Check for typical book-related fields
        assert any(key in response_str for key in ['title', 'author', 'book']), \
            f"Response should contain book information but got: {response}"
        
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
        
        # Semantic verification: check that the response contains country names
        response_str = str(response)
        assert proposition_holds(f"The following list contains names of countries: '{response_str}'"), \
            f"Response should contain country names but got: {response}"
        
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

    # ==== COERCION METHOD TESTS ====
    
    def test_coerce_to_bool_valid_inputs(self):
        """Test boolean coercion with valid inputs."""
        chat = LLMChat(system_prompt="Test", user_prompt="Test")
        
        # Test various true values
        assert chat._coerce_to_bool("True") == True
        assert chat._coerce_to_bool("true") == True
        assert chat._coerce_to_bool("TRUE") == True
        assert chat._coerce_to_bool("Yes") == True
        assert chat._coerce_to_bool("yes") == True
        assert chat._coerce_to_bool("Positive") == True
        assert chat._coerce_to_bool("positive") == True
        
        # Test various false values
        assert chat._coerce_to_bool("False") == False
        assert chat._coerce_to_bool("false") == False
        assert chat._coerce_to_bool("FALSE") == False
        assert chat._coerce_to_bool("No") == False
        assert chat._coerce_to_bool("no") == False
        assert chat._coerce_to_bool("Negative") == False
        assert chat._coerce_to_bool("negative") == False
        
        # Test with additional text (should pick first occurrence)
        assert chat._coerce_to_bool("Yes, that is correct") == True
        assert chat._coerce_to_bool("No, that is wrong") == False
        
        # Test with boolean input (should pass through)
        assert chat._coerce_to_bool(True) == True
        assert chat._coerce_to_bool(False) == False
    
    def test_coerce_to_bool_invalid_inputs(self):
        """Test boolean coercion with invalid inputs."""
        chat = LLMChat(system_prompt="Test", user_prompt="Test")
        
        with pytest.raises(ValueError, match="Cannot convert"):
            chat._coerce_to_bool("maybe")
            
        with pytest.raises(ValueError, match="Cannot convert"):
            chat._coerce_to_bool("123")
            
        with pytest.raises(ValueError, match="Cannot convert"):
            chat._coerce_to_bool("")
    
    def test_coerce_to_integer_valid_inputs(self):
        """Test integer coercion with valid inputs."""
        chat = LLMChat(system_prompt="Test", user_prompt="Test")
        
        assert chat._coerce_to_integer("42") == 42
        assert chat._coerce_to_integer("-17") == -17
        assert chat._coerce_to_integer("0") == 0
        assert chat._coerce_to_integer("  123  ") == 123  # with whitespace
        assert chat._coerce_to_integer("The answer is 42") == 42  # embedded number
        assert chat._coerce_to_integer(25) == 25  # already int
        assert chat._coerce_to_integer(3.0) == 3  # float that's whole number
    
    def test_coerce_to_integer_invalid_inputs(self):
        """Test integer coercion with invalid inputs."""
        chat = LLMChat(system_prompt="Test", user_prompt="Test")
        
        with pytest.raises(ValueError, match="Cannot convert"):
            chat._coerce_to_integer("not a number")
            
        with pytest.raises(ValueError, match="Cannot convert"):
            chat._coerce_to_integer("3.14")  # float with decimals
            
        with pytest.raises(ValueError, match="Cannot convert"):
            chat._coerce_to_integer("")
    
    def test_coerce_to_float_valid_inputs(self):
        """Test float coercion with valid inputs."""
        chat = LLMChat(system_prompt="Test", user_prompt="Test")
        
        assert chat._coerce_to_float("3.14") == 3.14
        assert chat._coerce_to_float("42") == 42.0
        assert chat._coerce_to_float("-17.5") == -17.5
        assert chat._coerce_to_float("0.0") == 0.0
        assert chat._coerce_to_float("  2.5  ") == 2.5  # with whitespace
        assert chat._coerce_to_float("The value is 3.14") == 3.14  # embedded number
        assert chat._coerce_to_float(2.5) == 2.5  # already float
        assert chat._coerce_to_float(42) == 42.0  # int input
    
    def test_coerce_to_float_invalid_inputs(self):
        """Test float coercion with invalid inputs."""
        chat = LLMChat(system_prompt="Test", user_prompt="Test")
        
        with pytest.raises(ValueError, match="Cannot convert"):
            chat._coerce_to_float("not a number")
            
        with pytest.raises(ValueError, match="Cannot convert"):
            chat._coerce_to_float("")
    
    def test_coerce_to_enumerable_valid_inputs(self):
        """Test enumerable coercion with valid inputs."""
        chat = LLMChat(system_prompt="Test", user_prompt="Test")
        options = ["red", "blue", "green"]
        
        assert chat._coerce_to_enumerable("red", options) == "red"
        assert chat._coerce_to_enumerable("RED", options) == "red"  # case insensitive
        assert chat._coerce_to_enumerable("Blue", options) == "blue"
        assert chat._coerce_to_enumerable("I choose green", options) == "green"  # embedded
    
    def test_coerce_to_enumerable_invalid_inputs(self):
        """Test enumerable coercion with invalid inputs."""
        chat = LLMChat(system_prompt="Test", user_prompt="Test")
        options = ["red", "blue", "green"]
        
        with pytest.raises(ValueError, match="Cannot find any of"):
            chat._coerce_to_enumerable("yellow", options)
            
        with pytest.raises(ValueError, match="Cannot find any of"):
            chat._coerce_to_enumerable("", options)
    
    def test_coerce_to_dict_or_list_valid_inputs(self):
        """Test dict/list coercion with valid inputs."""
        chat = LLMChat(system_prompt="Test", user_prompt="Test")
        
        # Valid JSON object
        json_obj = '{"name": "John", "age": 30}'
        result = chat._coerce_to_dict_or_list(json_obj)
        assert result == {"name": "John", "age": 30}
        
        # Valid JSON array
        json_array = '[{"name": "John"}, {"name": "Jane"}]'
        result = chat._coerce_to_dict_or_list(json_array)
        assert result == [{"name": "John"}, {"name": "Jane"}]
        
        # Already a dict
        dict_input = {"key": "value"}
        result = chat._coerce_to_dict_or_list(dict_input)
        assert result == dict_input
        
        # Already a list
        list_input = [1, 2, 3]
        result = chat._coerce_to_dict_or_list(list_input)
        assert result == list_input
    
    def test_coerce_to_dict_or_list_invalid_inputs(self):
        """Test dict/list coercion with invalid inputs."""
        chat = LLMChat(system_prompt="Test", user_prompt="Test")
        
        with pytest.raises(ValueError, match="Cannot convert"):
            chat._coerce_to_dict_or_list("not json")
            
        with pytest.raises(ValueError, match="Cannot convert"):
            chat._coerce_to_dict_or_list("42")  # valid JSON but not dict/list
    
    def test_coerce_to_list_valid_inputs(self):
        """Test list coercion with valid inputs."""
        chat = LLMChat(system_prompt="Test", user_prompt="Test")
        
        # Valid JSON array
        json_array = '["apple", "banana", "cherry"]'
        result = chat._coerce_to_list(json_array)
        assert result == ["apple", "banana", "cherry"]
        
        # Already a list
        list_input = [1, 2, 3]
        result = chat._coerce_to_list(list_input)
        assert result == list_input
    
    def test_coerce_to_list_invalid_inputs(self):
        """Test list coercion with invalid inputs."""
        chat = LLMChat(system_prompt="Test", user_prompt="Test")
        
        with pytest.raises(ValueError, match="Cannot convert"):
            chat._coerce_to_list("not json")
            
        with pytest.raises(ValueError, match="Cannot convert"):
            chat._coerce_to_list('{"key": "value"}')  # valid JSON but not list

    # ==== MOCKED RESPONSE TESTS ====
    
    @patch('tinytroupe.openai_utils.client')
    def test_call_with_mock_response(self, mock_client):
        """Test the call method with mocked responses."""
        # Setup mock
        mock_client_instance = MagicMock()
        mock_client.return_value = mock_client_instance
        mock_client_instance.send_message.return_value = {"content": "Test response"}
        
        chat = LLMChat(
            system_prompt="Test system",
            user_prompt="Test user"
        )
        
        result = chat.call()
        
        assert result == "Test response"
        assert chat.response_raw == "Test response"
        assert chat.response_value == "Test response"
        assert len(chat.messages) > 0
        mock_client_instance.send_message.assert_called_once()
    
    @patch('tinytroupe.openai_utils.client')
    def test_call_with_json_output_and_justification(self, mock_client):
        """Test call with JSON output and justification enabled."""
        # Setup mock
        mock_client_instance = MagicMock()
        mock_client.return_value = mock_client_instance
        mock_response = {
            "content": '{"justification": "This is correct", "value": true, "confidence": 0.9}'
        }
        mock_client_instance.send_message.return_value = mock_response
        
        chat = LLMChat(
            system_prompt="Test system",
            user_prompt="Test user",
            output_type=bool,
            enable_json_output_format=True,
            enable_justification_step=True
        )
        
        result = chat.call()
        
        assert result == True
        assert chat.response_justification == "This is correct"
        assert chat.response_confidence == 0.9
        assert chat.response_value == True
    
    @patch('tinytroupe.openai_utils.client')
    def test_call_with_reasoning_step(self, mock_client):
        """Test call with reasoning step enabled."""
        # Setup mock
        mock_client_instance = MagicMock()
        mock_client.return_value = mock_client_instance
        mock_response = {
            "content": '{"reasoning": "First I think...", "justification": "This is correct", "value": 42, "confidence": 0.95}'
        }
        mock_client_instance.send_message.return_value = mock_response
        
        chat = LLMChat(
            system_prompt="Test system",
            user_prompt="Test user",
            output_type=int,
            enable_json_output_format=True,
            enable_justification_step=True,
            enable_reasoning_step=True
        )
        
        result = chat.call()
        
        assert result == 42
        assert chat.response_reasoning == "First I think..."
        assert chat.response_justification == "This is correct"
        assert chat.response_confidence == 0.95
        assert chat.response_value == 42

    # ==== ERROR HANDLING TESTS ====
    
    @patch('tinytroupe.openai_utils.client')
    def test_call_error_handling(self, mock_client):
        """Test error handling during LLM calls."""
        # Setup mock to raise exception
        mock_client_instance = MagicMock()
        mock_client.return_value = mock_client_instance
        mock_client_instance.send_message.side_effect = Exception("API Error")
        
        chat = LLMChat(
            system_prompt="Test system",
            user_prompt="Test user"
        )
        
        result = chat.call()
        
        # Should return None on error, not raise exception
        assert result is None
    
    @patch('tinytroupe.openai_utils.client')
    def test_call_with_invalid_response_format(self, mock_client):
        """Test handling of invalid response format."""
        # Setup mock with missing content
        mock_client_instance = MagicMock()
        mock_client.return_value = mock_client_instance
        mock_client_instance.send_message.return_value = {"error": "No content"}
        
        chat = LLMChat(
            system_prompt="Test system",
            user_prompt="Test user"
        )
        
        result = chat.call()
        
        # Should return None when content is missing
        assert result is None
    
    def test_add_user_message_validation(self):
        """Test validation when adding user messages."""
        chat = LLMChat(system_prompt="Test", user_prompt="Test")
        
        # Both message and template should raise error
        with pytest.raises(ValueError, match="Either message or template_name must be specified"):
            chat.add_user_message(message="Test", template_name="test.mustache")
    
    def test_add_system_message_validation(self):
        """Test validation when adding system messages."""
        chat = LLMChat(system_prompt="Test", user_prompt="Test")
        
        # Both message and template should raise error
        with pytest.raises(ValueError, match="Either message or template_name must be specified"):
            chat.add_system_message(message="Test", template_name="test.mustache")
    
    def test_add_assistant_message_validation(self):
        """Test validation when adding assistant messages."""
        chat = LLMChat(system_prompt="Test", user_prompt="Test")
        
        # Both message and template should raise error
        with pytest.raises(ValueError, match="Either message or template_name must be specified"):
            chat.add_assistant_message(message="Test", template_name="test.mustache")
    
    def test_unsupported_output_type(self):
        """Test handling of unsupported output types."""
        chat = LLMChat(
            system_prompt="Test",
            user_prompt="Test",
            output_type=set  # unsupported type
        )
        
        with pytest.raises(ValueError, match="Unsupported output type"):
            chat.call()

    # ==== UTILITY AND CONVENIENCE TESTS ====
    
    def test_method_chaining(self):
        """Test that methods support chaining."""
        chat = LLMChat(system_prompt="Test", user_prompt="Test")
        
        # Test that methods return self for chaining
        result = chat.add_user_message("Test message").add_system_message("System message")
        assert result is chat
        
        result = chat.reset_conversation()
        assert result is chat
    
    def test_conversation_history_tracking(self):
        """Test that conversation history is properly tracked."""
        chat = LLMChat(system_prompt="Test", user_prompt="Test")
        
        # Initially empty
        assert len(chat.get_conversation_history()) == 0
        
        # Add messages
        chat.add_user_message("User message")
        chat.add_system_message("System message")
        
        history = chat.get_conversation_history()
        assert len(history) == 2
        assert history[0]["role"] == "user"
        assert history[1]["role"] == "system"
    
    def test_response_state_tracking(self):
        """Test that response state is properly tracked."""
        chat = LLMChat(system_prompt="Test", user_prompt="Test")
        
        # Initially None
        assert chat.response_raw is None
        assert chat.response_json is None
        assert chat.response_value is None
        assert chat.response_justification is None
        assert chat.response_confidence is None
        assert chat.response_reasoning is None
    
    def test_callable_interface(self):
        """Test that LLMChat can be called as a function."""
        chat = LLMChat(system_prompt="Test", user_prompt="Test")
        
        # Should be able to call chat() which delegates to call()
        with patch.object(chat, 'call', return_value="test") as mock_call:
            result = chat("arg1", kwarg1="value1")
            assert result == "test"
            mock_call.assert_called_once_with("arg1", kwarg1="value1")
    
    def test_request_message_methods(self):
        """Test the _request_*_llm_message methods."""
        chat = LLMChat(system_prompt="Test", user_prompt="Test")
        
        # Test each request method returns proper message format
        bool_msg = chat._request_bool_llm_message()
        assert bool_msg["content"]
        assert "True" in bool_msg["content"] and "False" in bool_msg["content"]
        
        int_msg = chat._request_integer_llm_message()
        assert int_msg["content"]
        assert "integer" in int_msg["content"].lower()
        
        float_msg = chat._request_float_llm_message()
        assert float_msg["content"]
        assert "number" in float_msg["content"].lower() or "float" in float_msg["content"].lower()
        
        str_msg = chat._request_str_llm_message()
        assert str_msg["content"]
        
        dict_msg = chat._request_dict_llm_message()
        assert dict_msg["content"]
        assert "JSON" in dict_msg["content"] or "object" in dict_msg["content"]
        
        list_msg = chat._request_list_llm_message()
        assert list_msg["content"]
        assert "list" in list_msg["content"] or "array" in list_msg["content"]
        
        list_of_dict_msg = chat._request_list_of_dict_llm_message()
        assert list_of_dict_msg["content"]
        
        # Test enumerable message with options
        options = ["red", "blue", "green"]
        enum_msg = chat._request_enumerable_llm_message(options)
        assert enum_msg["content"]
        for option in options:
            assert option in enum_msg["content"]


class TestLLMPydanticModels:
    """Test the Pydantic models used for structured responses."""
    
    def test_llm_scalar_with_justification_response(self):
        """Test LLMScalarWithJustificationResponse model."""
        response = LLMScalarWithJustificationResponse(
            justification="This is my reasoning",
            value="test_value",
            confidence=0.85
        )
        
        assert response.justification == "This is my reasoning"
        assert response.value == "test_value"
        assert response.confidence == 0.85
    
    def test_llm_scalar_with_justification_and_reasoning_response(self):
        """Test LLMScalarWithJustificationAndReasoningResponse model."""
        response = LLMScalarWithJustificationAndReasoningResponse(
            reasoning="First I consider...",
            justification="This is my reasoning",
            value=42,
            confidence=0.9
        )
        
        assert response.reasoning == "First I consider..."
        assert response.justification == "This is my reasoning"
        assert response.value == 42
        assert response.confidence == 0.9
    
    def test_pydantic_model_validation(self):
        """Test that Pydantic models properly validate inputs."""
        # Missing required field should raise error
        with pytest.raises(Exception):  # Pydantic validation error
            LLMScalarWithJustificationResponse(
                justification="Test",
                # missing value and confidence
            )
        
        # Invalid confidence type should raise error
        with pytest.raises(Exception):  # Pydantic validation error
            LLMScalarWithJustificationResponse(
                justification="Test",
                value="test",
                confidence="not_a_number"
            )
