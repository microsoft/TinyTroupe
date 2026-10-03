"""
Configuration validation system for TinyTroupe.

This module provides comprehensive validation for configuration settings
to prevent runtime errors and ensure proper system behavior.
"""

from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, validator
import logging
from pathlib import Path
import re

logger = logging.getLogger("tinytroupe")


class OpenAIConfig(BaseModel):
    """OpenAI API configuration validation."""
    
    api_type: str = Field(default="openai", description="API type: openai, azure, or ollama")
    model: str = Field(default="gpt-4o-mini", description="Main text generation model")
    reasoning_model: str = Field(default="o3-mini", description="Reasoning model for complex analysis")
    embedding_model: str = Field(default="text-embedding-3-small", description="Embedding model")
    
    max_tokens: int = Field(default=16000, ge=1, le=200000, description="Maximum tokens per request")
    temperature: float = Field(default=1.1, ge=0.0, le=2.0, description="Temperature for randomness")
    frequency_penalty: float = Field(default=0.1, ge=-2.0, le=2.0, description="Frequency penalty")
    presence_penalty: float = Field(default=0.1, ge=-2.0, le=2.0, description="Presence penalty")
    
    timeout: float = Field(default=480.0, gt=0, description="Request timeout in seconds")
    max_attempts: int = Field(default=5, ge=1, le=20, description="Maximum retry attempts")
    waiting_time: float = Field(default=1.0, ge=0, description="Wait time between retries")
    exponential_backoff_factor: float = Field(default=5.0, ge=1.0, description="Backoff factor")
    
    reasoning_effort: str = Field(default="high", description="Reasoning effort level")
    
    cache_api_calls: bool = Field(default=False, description="Enable API call caching")
    cache_file_name: str = Field(default="openai_api_cache.pickle", description="Cache file name")
    
    max_content_display_length: int = Field(default=4000, ge=100, description="Max content display length")
    
    # Azure-specific settings
    azure_api_version: Optional[str] = Field(default="2023-05-15", description="Azure API version")
    azure_embedding_model_api_version: Optional[str] = Field(default="2023-05-15", description="Azure embedding API version")
    
    # Ollama-specific settings
    ollama_base_url: Optional[str] = Field(default="http://localhost:11434/v1", description="Ollama base URL")
    
    @validator('api_type')
    def validate_api_type(cls, v):
        valid_types = ['openai', 'azure', 'ollama']
        if v not in valid_types:
            raise ValueError(f"api_type must be one of {valid_types}, got '{v}'")
        return v
    
    @validator('reasoning_effort')
    def validate_reasoning_effort(cls, v):
        valid_efforts = ['low', 'medium', 'high']
        if v not in valid_efforts:
            raise ValueError(f"reasoning_effort must be one of {valid_efforts}, got '{v}'")
        return v
    
    @validator('cache_file_name')
    def validate_cache_file_name(cls, v):
        # Basic file name validation
        if not v or len(v.strip()) == 0:
            raise ValueError("cache_file_name cannot be empty")
        
        # Check for dangerous characters
        dangerous_chars = ['..', '/', '\\', ':', '*', '?', '"', '<', '>', '|']
        for char in dangerous_chars:
            if char in v:
                raise ValueError(f"cache_file_name contains dangerous character: '{char}'")
        
        return v
    
    @validator('ollama_base_url')
    def validate_ollama_base_url(cls, v):
        if v is not None:
            # Basic URL validation
            url_pattern = re.compile(
                r'^https?://'  # http:// or https://
                r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
                r'localhost|'  # localhost...
                r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
                r'(?::\d+)?'  # optional port
                r'(?:/?|[/?]\S+)$', re.IGNORECASE)
            
            if not url_pattern.match(v):
                raise ValueError(f"Invalid URL format for ollama_base_url: '{v}'")
        
        return v


class SimulationConfig(BaseModel):
    """Simulation configuration validation."""
    
    parallel_agent_generation: bool = Field(default=True, description="Enable parallel agent generation")
    parallel_agent_actions: bool = Field(default=True, description="Enable parallel agent actions")
    
    rai_harmful_content_prevention: bool = Field(default=True, description="Enable harmful content prevention")
    rai_copyright_infringement_prevention: bool = Field(default=True, description="Enable copyright infringement prevention")


class CognitionConfig(BaseModel):
    """Cognition and memory configuration validation."""
    
    enable_memory_consolidation: bool = Field(default=True, description="Enable memory consolidation")
    
    min_episode_length: int = Field(default=15, ge=1, le=1000, description="Minimum episode length")
    max_episode_length: int = Field(default=50, ge=1, le=1000, description="Maximum episode length")
    
    episodic_memory_fixed_prefix_length: int = Field(default=10, ge=0, le=100, description="Fixed prefix length")
    episodic_memory_lookback_length: int = Field(default=20, ge=1, le=200, description="Lookback length")
    
    @validator('max_episode_length')
    def validate_episode_lengths(cls, v, values):
        if 'min_episode_length' in values and v < values['min_episode_length']:
            raise ValueError("max_episode_length must be >= min_episode_length")
        return v


class ActionGeneratorConfig(BaseModel):
    """Action generator configuration validation."""
    
    max_attempts: int = Field(default=2, ge=1, le=10, description="Maximum generation attempts")
    
    enable_quality_checks: bool = Field(default=False, description="Enable quality checks")
    enable_regeneration: bool = Field(default=True, description="Enable regeneration on failure")
    enable_direct_correction: bool = Field(default=False, description="Enable direct correction")
    
    enable_quality_check_for_persona_adherence: bool = Field(default=True, description="Check persona adherence")
    enable_quality_check_for_selfconsistency: bool = Field(default=False, description="Check self-consistency")
    enable_quality_check_for_fluency: bool = Field(default=False, description="Check fluency")
    enable_quality_check_for_suitability: bool = Field(default=False, description="Check suitability")
    enable_quality_check_for_similarity: bool = Field(default=False, description="Check similarity")
    
    continue_on_failure: bool = Field(default=True, description="Continue on failure")
    quality_threshold: int = Field(default=5, ge=0, le=10, description="Quality threshold (0-10)")


class LoggingConfig(BaseModel):
    """Logging configuration validation."""

    loglevel: str = Field(default="ERROR", description="Logging level")
    llm_telemetry_enabled: bool = Field(default=False, description="Emit structured telemetry for LLM calls")
    llm_telemetry_path: str = Field(default="logs/llm_telemetry.jsonl", description="Path to append LLM telemetry JSONL events")

    @validator('loglevel')
    def validate_loglevel(cls, v):
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f"loglevel must be one of {valid_levels}, got '{v}'")
        return v.upper()


class ModerationConfig(BaseModel):
    """Content moderation configuration."""

    enable_moderation: bool = Field(default=False, description="Toggle OpenAI moderation checks")
    moderation_action: str = Field(default="warn", description="Action on flagged content: warn or block")
    moderation_model: str = Field(default="omni-moderation-latest", description="Moderation model to call")
    moderation_block_message: str = Field(default="[BLOCKED BY MODERATION]", description="Message returned when blocking")

    @validator('moderation_action')
    def validate_moderation_action(cls, v):
        allowed = ['warn', 'block']
        if v not in allowed:
            raise ValueError(f"moderation_action must be one of {allowed}, got '{v}'")
        return v


class TinyTroupeConfig(BaseModel):
    """Complete TinyTroupe configuration validation."""

    openai: OpenAIConfig = Field(default_factory=OpenAIConfig)
    simulation: SimulationConfig = Field(default_factory=SimulationConfig)
    cognition: CognitionConfig = Field(default_factory=CognitionConfig)
    action_generator: ActionGeneratorConfig = Field(default_factory=ActionGeneratorConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    moderation: ModerationConfig = Field(default_factory=ModerationConfig)
    
    class Config:
        extra = 'forbid'  # Don't allow extra fields
        validate_assignment = True  # Validate on assignment


def validate_config_dict(config_dict: Dict[str, Any]) -> TinyTroupeConfig:
    """
    Validate a configuration dictionary and return a validated config object.
    
    Args:
        config_dict: Dictionary containing configuration values
        
    Returns:
        Validated TinyTroupeConfig object
        
    Raises:
        ValidationError: If configuration is invalid
    """
    try:
        # Convert nested dictionaries to match the model structure
        formatted_config = {}
        
        # Map flat config sections to nested structure
        section_mapping = {
            'OpenAI': 'openai',
            'Simulation': 'simulation',
            'Cognition': 'cognition',
            'ActionGenerator': 'action_generator',
            'Logging': 'logging',
            'Moderation': 'moderation'
        }
        
        for section_name, section_data in config_dict.items():
            if section_name in section_mapping:
                # Convert keys to lowercase with underscores
                formatted_section = {}
                for key, value in section_data.items():
                    # Convert CamelCase to snake_case
                    snake_key = re.sub(r'(?<!^)(?=[A-Z])', '_', key).lower()
                    formatted_section[snake_key] = value
                
                formatted_config[section_mapping[section_name]] = formatted_section
        
        return TinyTroupeConfig(**formatted_config)
        
    except Exception as e:
        from tinytroupe.exceptions import ValidationError
        raise ValidationError(f"Configuration validation failed: {str(e)}", "CONFIG_VALIDATION")


def validate_environment_variables() -> Dict[str, str]:
    """
    Validate environment variables for security.
    
    Returns:
        Dictionary of validated environment variables
        
    Raises:
        SecurityError: If dangerous environment variables are detected
    """
    import os
    from tinytroupe.exceptions import SecurityError
    
    validated_vars = {}
    
    # Check for required API keys
    api_key_vars = ['OPENAI_API_KEY', 'AZURE_OPENAI_API_KEY', 'OLLAMA_API_KEY']
    
    for var_name in api_key_vars:
        value = os.getenv(var_name)
        if value:
            # Basic validation for API keys
            if len(value) < 10:
                raise SecurityError(f"API key {var_name} appears to be too short", "INVALID_API_KEY")
            
            # Check for obvious dummy values
            dummy_patterns = ['dummy', 'test', 'example', 'placeholder', '...', 'xxx']
            if any(pattern in value.lower() for pattern in dummy_patterns):
                raise SecurityError(f"API key {var_name} appears to be a placeholder", "PLACEHOLDER_API_KEY")
            
            validated_vars[var_name] = value
    
    # Check for endpoint URLs
    endpoint_vars = ['AZURE_OPENAI_ENDPOINT', 'OLLAMA_BASE_URL']
    
    for var_name in endpoint_vars:
        value = os.getenv(var_name)
        if value:
            # Basic URL validation
            if not (value.startswith('http://') or value.startswith('https://')):
                raise SecurityError(f"Endpoint {var_name} must start with http:// or https://", "INVALID_ENDPOINT")
            
            validated_vars[var_name] = value
    
    return validated_vars


def create_default_config() -> TinyTroupeConfig:
    """Create a default configuration with safe values."""
    return TinyTroupeConfig()


def load_and_validate_config(config_file_path: Optional[str] = None) -> TinyTroupeConfig:
    """
    Load configuration from file and validate it.
    
    Args:
        config_file_path: Path to configuration file
        
    Returns:
        Validated configuration object
    """
    import configparser
    from tinytroupe.exceptions import ConfigurationError
    
    try:
        # Use default path if not provided
        if config_file_path is None:
            config_file_path = Path(__file__).parent / "config.ini"
        
        if not Path(config_file_path).exists():
            logger.warning(f"Config file not found: {config_file_path}, using defaults")
            return create_default_config()
        
        # Load configuration file
        config_parser = configparser.ConfigParser()
        config_parser.read(config_file_path)
        
        # Convert to dictionary
        config_dict = {section: dict(config_parser[section]) for section in config_parser.sections()}
        
        # Validate and return
        return validate_config_dict(config_dict)
        
    except Exception as e:
        raise ConfigurationError(f"Failed to load configuration: {str(e)}", "CONFIG_LOAD")


# Export validation functions
__all__ = [
    'TinyTroupeConfig',
    'OpenAIConfig', 
    'SimulationConfig',
    'CognitionConfig',
    'ActionGeneratorConfig',
    'LoggingConfig',
    'validate_config_dict',
    'validate_environment_variables',
    'create_default_config',
    'load_and_validate_config'
]