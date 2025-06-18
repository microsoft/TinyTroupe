import os
import logging
import configparser
import rich # for rich console output
import rich.jupyter

# add current path to sys.path
import sys
sys.path.append('.')
from tinytroupe import utils # now we can import our utils

# AI disclaimers
print(\
"""
!!!!
DISCLAIMER: TinyTroupe relies on Artificial Intelligence (AI) models to generate content. 
The AI models are not perfect and may produce inappropriate or inacurate results. 
For any serious or consequential use, please review the generated content before using it.
!!!!
""")


###########################################################################
# Configuration Management System
###########################################################################
class ConfigManager:
    """
    Manages configuration values with the ability to override defaults.
    Provides dynamic access to the latest config values.
    """
    def __init__(self):
        self._config = {}
        self._initialize_from_config()
    
    def _initialize_from_config(self):
        """Initialize default values from config file"""
        config = utils.read_config_file()
        
        self._config["model"] = config["OpenAI"].get("MODEL", "gpt-4o")
        self._config["embedding_model"] = config["OpenAI"].get("EMBEDDING_MODEL", "text-embedding-3-small")
        if config["OpenAI"].get("API_TYPE") == "azure":
            self._config["azure_embedding_model_api_version"] = config["OpenAI"].get("AZURE_EMBEDDING_MODEL_API_VERSION", "2023-05-15")
        self._config["reasoning_model"] = config["OpenAI"].get("REASONING_MODEL", "o3-mini")

        self._config["max_tokens"] = int(config["OpenAI"].get("MAX_TOKENS", "1024"))
        self._config["temperature"] = float(config["OpenAI"].get("TEMPERATURE", "1.0"))
        self._config["top_p"] = int(config["OpenAI"].get("TOP_P", "0"))
        self._config["frequency_penalty"] = float(config["OpenAI"].get("FREQ_PENALTY", "0.0"))
        self._config["presence_penalty"] = float(
            config["OpenAI"].get("PRESENCE_PENALTY", "0.0"))
        self._config["reasoning_effort"] = config["OpenAI"].get("REASONING_EFFORT", "high")

        self._config["timeout"] = float(config["OpenAI"].get("TIMEOUT", "30.0"))
        self._config["max_attempts"] = float(config["OpenAI"].get("MAX_ATTEMPTS", "0.0"))
        self._config["waiting_time"] = float(config["OpenAI"].get("WAITING_TIME", "1"))
        self._config["exponential_backoff_factor"] = float(config["OpenAI"].get("EXPONENTIAL_BACKOFF_FACTOR", "5"))

        self._config["cache_api_calls"] = config["OpenAI"].getboolean("CACHE_API_CALLS", False)
        self._config["cache_file_name"] = config["OpenAI"].get("CACHE_FILE_NAME", "openai_api_cache.pickle")

        self._config["max_content_display_length"] = config["OpenAI"].getint("MAX_CONTENT_DISPLAY_LENGTH", 1024)

        self._config["parallel_agent_actions"] = config["Simulation"].getboolean("PARALLEL_AGENT_ACTIONS", True)
        self._config["parallel_agent_generation"] = config["Simulation"].getboolean("PARALLEL_AGENT_GENERATION", True)

        self._config["action_generator_max_attempts"] = config["ActionGenerator"].getint("MAX_ATTEMPTS", 2)
        self._config["action_generator_enable_quality_checks"] = config["ActionGenerator"].getboolean("ENABLE_QUALITY_CHECKS", False)
        self._config["action_generator_enable_regeneration"] = config["ActionGenerator"].getboolean("ENABLE_REGENERATION", False)
        self._config["action_generator_enable_direct_correction"] = config["ActionGenerator"].getboolean("ENABLE_DIRECT_CORRECTION", False)

        self._config["action_generator_enable_quality_check_for_persona_adherence"] = config["ActionGenerator"].getboolean("ENABLE_QUALITY_CHECK_FOR_PERSONA_ADHERENCE", False)
        self._config["action_generator_enable_quality_check_for_selfconsistency"] = config["ActionGenerator"].getboolean("ENABLE_QUALITY_CHECK_FOR_SELFCONSISTENCY", False)
        self._config["action_generator_enable_quality_check_for_fluency"] = config["ActionGenerator"].getboolean("ENABLE_QUALITY_CHECK_FOR_FLUENCY", False)
        self._config["action_generator_enable_quality_check_for_suitability"] = config["ActionGenerator"].getboolean("ENABLE_QUALITY_CHECK_FOR_SUITABILITY", False)
        self._config["action_generator_enable_quality_check_for_similarity"] = config["ActionGenerator"].getboolean("ENABLE_QUALITY_CHECK_FOR_SIMILARITY", False)

        self._config["action_generator_continue_on_failure"] = config["ActionGenerator"].getboolean("CONTINUE_ON_FAILURE", True)
        self._config["action_generator_quality_threshold"] = config["ActionGenerator"].getint("QUALITY_THRESHOLD", 2)
        
        self._raw_config = config
    
    def update(self, key, value):
        """
        Update a configuration value.
        
        Args:
            key (str): The configuration key to update
            value: The new value to set
            
        Returns:
            None
        """
        if key in self._config:
            self._config[key] = value
            logging.info(f"Updated config: {key} = {value}")
        else:
            logging.warning(f"Attempted to update unknown config key: {key}")
    
    def update_multiple(self, config_dict):
        """
        Update multiple configuration values at once.
        
        Args:
            config_dict (dict): Dictionary of key-value pairs to update
            
        Returns:
            None
        """
        for key, value in config_dict.items():
            self.update(key, value)
    
    def get(self, key, default=None):
        """
        Get a configuration value.
        
        Args:
            key (str): The configuration key to retrieve
            default: The default value to return if key is not found
            
        Returns:
            The configuration value
        """
        return self._config.get(key, default)
    
    def reset(self):
        """Reset all configuration values to their original values from the config file."""
        self._initialize_from_config()
        logging.info("All configuration values have been reset to defaults")
    
    def __getitem__(self, key):
        """Allow dictionary-like access to configuration values."""
        return self.get(key)

    def config_defaults(self, **config_mappings):
        """
        Returns a decorator that replaces None default values with current config values.
        
        Args:
            **config_mappings: Mapping of parameter names to config keys
            
        Example:
            @config_manager.config_defaults(model="model", temp="temperature")
            def generate(prompt, model=None, temp=None):
                # model will be the current config value for "model" if None is passed
                # ...
        """
        import functools
        import inspect
        
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                # Get the function's signature
                sig = inspect.signature(func)
                bound_args = sig.bind_partial(*args, **kwargs)
                bound_args.apply_defaults()
                
                # For each parameter that maps to a config key
                for param_name, config_key in config_mappings.items():
                    # If the parameter is None, replace with config value
                    if param_name in bound_args.arguments and bound_args.arguments[param_name] is None:
                        kwargs[param_name] = self.get(config_key)
                
                return func(*args, **kwargs)
            
            return wrapper
        
        return decorator

# Create global instance of the configuration manager
config = utils.read_config_file()
utils.pretty_print_config(config)
utils.start_logger(config)

config_manager = ConfigManager()

# For backwards compatibility, maintain the default dict
# but it's recommended to use config_manager instead
default = config_manager._config

# Helper function for method signatures
def get_config(key, override_value=None):
    """
    Get a configuration value, with optional override.
    Used in method signatures to get current config values.
    
    Args:
        key (str): The configuration key
        override_value: If provided, this value is used instead of the config value
        
    Returns:
        The configuration value or the override value
    """
    if override_value is not None:
        return override_value
    return config_manager.get(key)


## LLaMa-Index configs ########################################################
#from llama_index.embeddings.huggingface import HuggingFaceEmbedding

if config["OpenAI"].get("API_TYPE") == "azure":
    from llama_index.embeddings.azure_openai import AzureOpenAIEmbedding
else:
    from llama_index.embeddings.openai import OpenAIEmbedding

from llama_index.core import Settings, Document, VectorStoreIndex, SimpleDirectoryReader
from llama_index.readers.web import SimpleWebPageReader


# this will be cached locally by llama-index, in a OS-dependend location

##Settings.embed_model = HuggingFaceEmbedding(
##    model_name="BAAI/bge-small-en-v1.5"
##)

if config["OpenAI"].get("API_TYPE") == "azure":
    llamaindex_openai_embed_model = AzureOpenAIEmbedding(model=default["embedding_model"],
                                                        deployment_name=default["embedding_model"],
                                                        api_version=default["azure_embedding_model_api_version"],
                                                        embed_batch_size=10)
else:
    llamaindex_openai_embed_model = OpenAIEmbedding(model=default["embedding_model"], embed_batch_size=10)
Settings.embed_model = llamaindex_openai_embed_model


###########################################################################
# Fixes and tweaks
###########################################################################

# fix an issue in the rich library: we don't want margins in Jupyter!
rich.jupyter.JUPYTER_HTML_FORMAT = \
    utils.inject_html_css_style_prefix(rich.jupyter.JUPYTER_HTML_FORMAT, "margin:0px;")


