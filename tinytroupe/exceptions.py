"""
Custom exception classes for TinyTroupe library.

This module defines a hierarchy of custom exceptions to provide better
error handling and debugging capabilities throughout the TinyTroupe codebase.
"""


class TinyTroupeError(Exception):
    """Base exception class for all TinyTroupe-related errors."""
    
    def __init__(self, message: str, error_code: str = None, context: dict = None):
        super().__init__(message)
        self.error_code = error_code
        self.context = context or {}
        
    def __str__(self):
        base_msg = super().__str__()
        if self.error_code:
            base_msg = f"[{self.error_code}] {base_msg}"
        if self.context:
            base_msg += f" (Context: {self.context})"
        return base_msg


# Configuration and Setup Errors
class ConfigurationError(TinyTroupeError):
    """Raised when there are configuration-related issues."""
    pass


class ValidationError(TinyTroupeError):
    """Raised when validation fails."""
    pass


# Agent-related Errors
class AgentError(TinyTroupeError):
    """Base class for agent-related errors."""
    pass


class AgentLoopError(AgentError):
    """Raised when an agent is detected to be in an infinite loop."""
    
    def __init__(self, agent_name: str, loop_type: str, message: str = None):
        self.agent_name = agent_name
        self.loop_type = loop_type
        default_message = f"Agent '{agent_name}' detected in {loop_type} loop"
        super().__init__(message or default_message, "AGENT_LOOP", {
            'agent_name': agent_name,
            'loop_type': loop_type
        })


class AgentActionError(AgentError):
    """Raised when an agent action fails."""
    
    def __init__(self, agent_name: str, action_type: str, message: str = None):
        self.agent_name = agent_name
        self.action_type = action_type
        default_message = f"Agent '{agent_name}' failed to execute action '{action_type}'"
        super().__init__(message or default_message, "AGENT_ACTION", {
            'agent_name': agent_name,
            'action_type': action_type
        })


class AgentMemoryError(AgentError):
    """Raised when agent memory operations fail."""
    pass


class AgentPersonaError(AgentError):
    """Raised when agent persona validation fails."""
    pass


# Environment-related Errors
class EnvironmentError(TinyTroupeError):
    """Base class for environment-related errors."""
    pass


class WorldStepError(EnvironmentError):
    """Raised when a world step fails to execute."""
    pass


# LLM and Communication Errors
class LLMError(TinyTroupeError):
    """Base class for LLM-related errors."""
    pass


class LLMResponseError(LLMError):
    """Raised when LLM response cannot be parsed or is invalid."""
    
    def __init__(self, response_text: str = None, parsing_error: str = None):
        self.response_text = response_text
        self.parsing_error = parsing_error
        message = "Failed to parse LLM response"
        if parsing_error:
            message += f": {parsing_error}"
        super().__init__(message, "LLM_RESPONSE", {
            'response_preview': response_text[:200] + "..." if response_text and len(response_text) > 200 else response_text,
            'parsing_error': parsing_error
        })


class LLMTimeoutError(LLMError):
    """Raised when LLM request times out."""
    pass


class LLMQuotaError(LLMError):
    """Raised when LLM quota is exceeded."""
    pass


# JSON and Data Processing Errors
class JSONExtractionError(TinyTroupeError):
    """Raised when JSON extraction from text fails."""
    
    def __init__(self, text: str = None, strategies_tried: list = None):
        self.text = text
        self.strategies_tried = strategies_tried or []
        message = "Failed to extract valid JSON from text"
        super().__init__(message, "JSON_EXTRACTION", {
            'text_preview': text[:200] + "..." if text and len(text) > 200 else text,
            'strategies_tried': strategies_tried
        })


# Simulation and Control Errors
class SimulationError(TinyTroupeError):
    """Base class for simulation-related errors."""
    pass


class SimulationStateError(SimulationError):
    """Raised when simulation state is invalid."""
    pass


class CacheError(SimulationError):
    """Raised when cache operations fail."""
    pass


class TransactionError(SimulationError):
    """Raised when transactional operations fail."""
    pass


# Security and Safety Errors
class SecurityError(TinyTroupeError):
    """Raised when security violations are detected."""
    pass


class InputValidationError(SecurityError):
    """Raised when input validation fails for security reasons."""
    pass


class ContentSafetyError(SecurityError):
    """Raised when content safety checks fail."""
    pass


# Factory and Creation Errors
class FactoryError(TinyTroupeError):
    """Base class for factory-related errors."""
    pass


class AgentCreationError(FactoryError):
    """Raised when agent creation fails."""
    pass


# Testing and Validation Errors
class TestingError(TinyTroupeError):
    """Raised during testing operations."""
    pass


class PropositionError(TinyTroupeError):
    """Raised when proposition validation fails."""
    pass


# Utility Functions for Error Handling
def handle_error_with_context(error: Exception, context: dict = None, 
                            logger=None, reraise: bool = True):
    """
    Handle an error with additional context and logging.
    
    Args:
        error: The exception to handle
        context: Additional context information
        logger: Logger instance to use for logging
        reraise: Whether to reraise the exception after handling
    """
    if isinstance(error, TinyTroupeError):
        # Already a TinyTroupe error, just add context if provided
        if context:
            error.context.update(context)
    else:
        # Wrap in a generic TinyTroupe error
        error = TinyTroupeError(
            f"Unexpected error: {str(error)}", 
            "UNEXPECTED", 
            context or {}
        )
    
    if logger:
        logger.error(f"Error occurred: {error}")
        if hasattr(error, 'context') and error.context:
            logger.debug(f"Error context: {error.context}")
    
    if reraise:
        raise error
    
    return error


def create_error_context(agent=None, environment=None, action=None, **kwargs):
    """
    Create a standard error context dictionary.
    
    Args:
        agent: TinyPerson instance
        environment: TinyWorld instance  
        action: Action dictionary
        **kwargs: Additional context items
    """
    context = {}
    
    if agent:
        context['agent_name'] = getattr(agent, 'name', 'unknown')
        context['agent_id'] = getattr(agent, 'id', 'unknown')
    
    if environment:
        context['environment_name'] = getattr(environment, 'name', 'unknown')
        context['environment_id'] = getattr(environment, 'id', 'unknown')
    
    if action:
        context['action_type'] = action.get('type', 'unknown')
        context['action_id'] = action.get('id', 'unknown')
    
    context.update(kwargs)
    return context