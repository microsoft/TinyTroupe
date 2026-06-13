"""
Custom exceptions for TinyTroupe with enhanced security and error handling.
"""


class TinyTroupeException(Exception):
    """Base exception for all TinyTroupe errors."""
    pass


class SecurityException(TinyTroupeException):
    """Exception raised for security-related errors."""
    pass


class ValidationException(TinyTroupeException):
    """Exception raised when input validation fails."""
    pass


class LLMException(TinyTroupeException):
    """Exception raised for LLM-related errors."""
    pass


class MemoryException(TinyTroupeException):
    """Exception raised for memory-related errors."""
    pass