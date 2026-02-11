import configparser
import logging
import os

# add current path to sys.path
import sys

import rich  # for rich console output
import rich.jupyter

sys.path.append(".")
from tinytroupe import utils  # now we can import our utils

# AI disclaimers
print(
    """
!!!!
DISCLAIMER: TinyTroupe relies on Artificial Intelligence (AI) models to generate content. 
The AI models are not perfect and may produce inappropriate or inacurate results. 
For any serious or consequential use, please review the generated content before using it.
!!!!
"""
)


###########################################################################
# Configuration Management System
###########################################################################
class ConfigManager:
    """
    Manages configuration values with the ability to override defaults.
    Provides dynamic access to the latest config values.
    """

    # this is used in more than one place below, so we define it here
    # to avoid errors in later changes
    LOGLEVEL_KEY = "loglevel"
    LOGLEVEL_CONSOLE_KEY = "loglevel_console"
    LOGLEVEL_FILE_KEY = "loglevel_file"
    LOG_INCLUDE_THREAD_ID_KEY = "log_include_thread_id"

    def __init__(self):
        self._config = {}
        self._initialize_from_config()

    @staticmethod
    def _parse_concurrency_limit(value, default):
        """Parse the max concurrent model call limit allowing disable tokens."""
        if value is None:
            return default

        if isinstance(value, (int, float)):
            candidate = int(value)
        elif isinstance(value, str):
            candidate_str = value.strip()
            if candidate_str == "":
                return default
            upper = candidate_str.upper()
            if upper in {"NONE", "OFF", "DISABLE", "DISABLED"}:
                return None
            try:
                candidate = int(candidate_str)
            except ValueError:
                logging.warning(
                    "Invalid MAX_CONCURRENT_MODEL_CALLS value '%s'. Using default %s instead.",
                    value,
                    default,
                )
                return default
        else:
            return default

        if candidate <= 0:
            return None

        return candidate

    def _initialize_from_config(self):
        """Initialize default values from config file"""
        config = utils.read_config_file()

        self._config["api_type"] = config["OpenAI"].get("API_TYPE", "openai")
        self._config["azure_api_version"] = config["OpenAI"].get(
            "AZURE_API_VERSION", "2024-10-21"
        )
        self._config["base_url"] = config["OpenAI"].get(
            "BASE_URL", None
        )  # by default, we will not use a custom base URL

        self._config["model"] = config["OpenAI"].get("MODEL", "gpt-4o")
        self._config["embedding_model"] = config["OpenAI"].get(
            "EMBEDDING_MODEL", "text-embedding-3-small"
        )
        if config["OpenAI"].get("API_TYPE") == "azure":
            self._config["azure_embedding_model_api_version"] = config["OpenAI"].get(
                "AZURE_EMBEDDING_MODEL_API_VERSION", "2023-05-15"
            )
        self._config["reasoning_model"] = config["OpenAI"].get(
            "REASONING_MODEL", "o3-mini"
        )

        # Vision model: used for image understanding. Falls back to MODEL if not set.
        _vision_model_raw = config["OpenAI"].get("VISION_MODEL", None)
        self._config["vision_model"] = _vision_model_raw if _vision_model_raw else None

        # Vision detail level: auto, low, or high (controls token cost for images)
        self._config["vision_detail"] = config["OpenAI"].get("VISION_DETAIL", "auto")

        self._config["max_completion_tokens"] = int(
            config["OpenAI"].get("MAX_COMPLETION_TOKENS", "1024")
        )
        self._config["temperature"] = config["OpenAI"].getfloat("TEMPERATURE", None)
        self._config["top_p"] = config["OpenAI"].getfloat("TOP_P", None)
        self._config["frequency_penalty"] = config["OpenAI"].getfloat(
            "FREQ_PENALTY", None
        )
        self._config["presence_penalty"] = config["OpenAI"].getfloat(
            "PRESENCE_PENALTY", None
        )
        self._config["reasoning_effort"] = config["OpenAI"].get(
            "REASONING_EFFORT", "high"
        )

        self._config["num_ctx"] = int(config["OpenAI"].get("NUM_CTX", "32000"))

        self._config["timeout"] = float(config["OpenAI"].get("TIMEOUT", "30.0"))
        self._config["max_attempts"] = float(
            config["OpenAI"].get("MAX_ATTEMPTS", "0.0")
        )
        self._config["waiting_time"] = float(config["OpenAI"].get("WAITING_TIME", "1"))
        self._config["exponential_backoff_factor"] = float(
            config["OpenAI"].get("EXPONENTIAL_BACKOFF_FACTOR", "5")
        )

        self._config["max_concurrent_model_calls"] = self._parse_concurrency_limit(
            config["OpenAI"].get("MAX_CONCURRENT_MODEL_CALLS", None),
            default=4,
        )

        self._config["cache_api_calls"] = config["OpenAI"].getboolean(
            "CACHE_API_CALLS", False
        )
        self._config["cache_file_name"] = config["OpenAI"].get(
            "CACHE_FILE_NAME", "openai_api_cache.pickle"
        )

        self._config["max_content_display_length"] = config["OpenAI"].getint(
            "MAX_CONTENT_DISPLAY_LENGTH", 1024
        )

        self._config["parallel_agent_actions"] = config["Simulation"].getboolean(
            "PARALLEL_AGENT_ACTIONS", True
        )
        self._config["parallel_agent_generation"] = config["Simulation"].getboolean(
            "PARALLEL_AGENT_GENERATION", True
        )

        self._config["enable_memory_consolidation"] = config["Cognition"].getboolean(
            "ENABLE_MEMORY_CONSOLIDATION", True
        )
        self._config["enable_continuous_contextual_semantic_memory_retrieval"] = config[
            "Cognition"
        ].getboolean("ENABLE_CONTINUOUS_CONTEXTUAL_SEMANTIC_MEMORY_RETRIEVAL", True)
        self._config["min_episode_length"] = config["Cognition"].getint(
            "MIN_EPISODE_LENGTH", 30
        )
        self._config["max_episode_length"] = config["Cognition"].getint(
            "MAX_EPISODE_LENGTH", 100
        )
        self._config["episodic_memory_fixed_prefix_length"] = config[
            "Cognition"
        ].getint("EPISODIC_MEMORY_FIXED_PREFIX_LENGTH", 20)
        self._config["episodic_memory_lookback_length"] = config["Cognition"].getint(
            "EPISODIC_MEMORY_LOOKBACK_LENGTH", 20
        )

        self._config["action_generator_max_attempts"] = config[
            "ActionGenerator"
        ].getint("MAX_ATTEMPTS", 2)
        self._config["action_generator_enable_quality_checks"] = config[
            "ActionGenerator"
        ].getboolean("ENABLE_QUALITY_CHECKS", False)
        self._config["action_generator_enable_regeneration"] = config[
            "ActionGenerator"
        ].getboolean("ENABLE_REGENERATION", False)
        self._config["action_generator_enable_direct_correction"] = config[
            "ActionGenerator"
        ].getboolean("ENABLE_DIRECT_CORRECTION", False)

        self._config["action_generator_enable_quality_check_for_persona_adherence"] = (
            config["ActionGenerator"].getboolean(
                "ENABLE_QUALITY_CHECK_FOR_PERSONA_ADHERENCE", False
            )
        )
        self._config["action_generator_enable_quality_check_for_selfconsistency"] = (
            config["ActionGenerator"].getboolean(
                "ENABLE_QUALITY_CHECK_FOR_SELFCONSISTENCY", False
            )
        )
        self._config["action_generator_enable_quality_check_for_fluency"] = config[
            "ActionGenerator"
        ].getboolean("ENABLE_QUALITY_CHECK_FOR_FLUENCY", False)
        self._config["action_generator_enable_quality_check_for_suitability"] = config[
            "ActionGenerator"
        ].getboolean("ENABLE_QUALITY_CHECK_FOR_SUITABILITY", False)
        self._config["action_generator_enable_quality_check_for_similarity"] = config[
            "ActionGenerator"
        ].getboolean("ENABLE_QUALITY_CHECK_FOR_SIMILARITY", False)

        self._config["action_generator_continue_on_failure"] = config[
            "ActionGenerator"
        ].getboolean("CONTINUE_ON_FAILURE", True)
        self._config["action_generator_quality_threshold"] = config[
            "ActionGenerator"
        ].getint("QUALITY_THRESHOLD", 2)

        # LOGLEVELS
        default_loglevel = config["Logging"].get("LOGLEVEL", "INFO").upper()
        loglevel_console = (
            config["Logging"].get("LOGLEVEL_CONSOLE", default_loglevel).upper()
        )
        loglevel_file = config["Logging"].get("LOGLEVEL_FILE", default_loglevel).upper()

        self._config[ConfigManager.LOGLEVEL_KEY] = default_loglevel
        self._config[ConfigManager.LOGLEVEL_CONSOLE_KEY] = loglevel_console
        self._config[ConfigManager.LOGLEVEL_FILE_KEY] = loglevel_file
        self._config[ConfigManager.LOG_INCLUDE_THREAD_ID_KEY] = config["Logging"].getboolean(
            "LOG_INCLUDE_THREAD_ID", fallback=False
        )

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
        # make sure the key is always lowercase
        if isinstance(key, str):
            key = key.lower()

        if key in self._config:
            self._config[key] = value
            logging.info(f"Updated config: {key} = {value}")

            if key in (
                ConfigManager.LOGLEVEL_KEY,
                ConfigManager.LOGLEVEL_CONSOLE_KEY,
                ConfigManager.LOGLEVEL_FILE_KEY,
            ):
                normalized_value = (
                    value.upper()
                    if isinstance(value, str)
                    else logging.getLevelName(value)
                )
                self._config[key] = normalized_value

            # Special handling for loglevel - also update the logger immediately
            if key == ConfigManager.LOGLEVEL_KEY:
                utils.set_loglevel(value)
                # synchronize specific targets when the general level changes
                normalized = (
                    value.upper()
                    if isinstance(value, str)
                    else logging.getLevelName(value)
                )
                self._config[ConfigManager.LOGLEVEL_CONSOLE_KEY] = normalized
                self._config[ConfigManager.LOGLEVEL_FILE_KEY] = normalized
            elif key == ConfigManager.LOGLEVEL_CONSOLE_KEY:
                utils.set_console_loglevel(value)
            elif key == ConfigManager.LOGLEVEL_FILE_KEY:
                utils.set_file_loglevel(value)
            elif key == ConfigManager.LOG_INCLUDE_THREAD_ID_KEY:
                bool_value = (
                    value.strip().lower() in {"1", "true", "yes", "on"}
                    if isinstance(value, str)
                    else bool(value)
                )
                self._config[key] = bool_value
                utils.set_include_thread_info(bool_value)
            elif key == "max_concurrent_model_calls":
                parsed_value = self._parse_concurrency_limit(value, default=None)
                self._config[key] = parsed_value
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
        # make sure the key is always lowercase
        if isinstance(key, str):
            key = key.lower()

        return self._config.get(key, default)

    def get_with_fallback(self, key, fallback_key, default=None):
        """
        Get a configuration value, falling back to another key if the primary key is absent or None.

        Args:
            key (str): The primary configuration key to try first.
            fallback_key (str): The fallback configuration key if the primary is not set.
            default: The default value if neither key is found.

        Returns:
            The configuration value.
        """
        value = self.get(key)
        if value is not None:
            return value
        return self.get(fallback_key, default)

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
                    if (
                        param_name in bound_args.arguments
                        and bound_args.arguments[param_name] is None
                    ):
                        kwargs[param_name] = self.get(config_key)

                return func(*args, **kwargs)

            return wrapper

        return decorator


# Create global instance of the configuration manager
config = utils.read_config_file()
utils.pretty_print_tinytroupe_version()
utils.pretty_print_datetime()
utils.pretty_print_config(config)
utils.start_logger(config)

config_manager = ConfigManager()


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
# from llama_index.embeddings.huggingface import HuggingFaceEmbedding

if config_manager.get("api_type") == "azure":
    from llama_index.embeddings.azure_openai import AzureOpenAIEmbedding
else:
    from llama_index.embeddings.openai import OpenAIEmbedding

from llama_index.core import Document, Settings, SimpleDirectoryReader, VectorStoreIndex
from llama_index.readers.web import SimpleWebPageReader

# this will be cached locally by llama-index, in a OS-dependend location

##Settings.embed_model = HuggingFaceEmbedding(
##    model_name="BAAI/bge-small-en-v1.5"
##)

if config_manager.get("api_type") == "azure":
    llamaindex_openai_embed_model = AzureOpenAIEmbedding(
        model=config_manager.get("embedding_model"),
        deployment_name=config_manager.get("embedding_model"),
        api_version=config_manager.get("azure_embedding_model_api_version"),
        embed_batch_size=10,
    )
else:
    llamaindex_openai_embed_model = OpenAIEmbedding(
        model=config_manager.get("embedding_model"), embed_batch_size=10
    )
Settings.embed_model = llamaindex_openai_embed_model


###########################################################################
# Fixes and tweaks
###########################################################################

# fix an issue in the rich library: we don't want margins in Jupyter!
rich.jupyter.JUPYTER_HTML_FORMAT = utils.inject_html_css_style_prefix(
    rich.jupyter.JUPYTER_HTML_FORMAT, "margin:0px;"
)
