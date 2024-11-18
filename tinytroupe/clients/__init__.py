from .openai_client import OpenAIClient
import logging
from tinytroupe import utils
from .azure_client import AzureClient
import logging
from tinytroupe import utils
logger = logging.getLogger("tinytroupe")

# We'll use various configuration elements below
config = utils.read_config_file()

###########################################################################
# default_params parameter values
###########################################################################
default_params = {}
default_params["model"] = config["OpenAI"].get("MODEL", "gpt-4")
default_params["max_tokens"] = int(config["OpenAI"].get("MAX_TOKENS", "1024"))
default_params["temperature"] = float(config["OpenAI"].get("TEMPERATURE", "0.3"))
default_params["top_p"] = int(config["OpenAI"].get("TOP_P", "0"))
default_params["frequency_penalty"] = float(config["OpenAI"].get("FREQ_PENALTY", "0.0"))
default_params["presence_penalty"] = float(
    config["OpenAI"].get("PRESENCE_PENALTY", "0.0"))
default_params["timeout"] = float(config["OpenAI"].get("TIMEOUT", "30.0"))
default_params["max_attempts"] = float(config["OpenAI"].get("MAX_ATTEMPTS", "0.0"))
default_params["waiting_time"] = float(config["OpenAI"].get("WAITING_TIME", "0.5"))
default_params["exponential_backoff_factor"] = float(config["OpenAI"].get("EXPONENTIAL_BACKOFF_FACTOR", "5"))

default_params["embedding_model"] = config["OpenAI"].get("EMBEDDING_MODEL", "text-embedding-3-small")

default_params["cache_api_calls"] = config["OpenAI"].getboolean("CACHE_API_CALLS", False)
default_params["cache_file_name"] = config["OpenAI"].get("CACHE_FILE_NAME", "openai_api_cache.pickle")

###########################################################################
# Model calling helpers
###########################################################################

# TODO under development
class LLMCall:
    """
    A class that represents an LLM model call. It contains the input messages, the model configuration, and the model output.
    """
    def __init__(self, system_template_name:str, user_template_name:str=None, **model_params):
        """
        Initializes an LLMCall instance with the specified system and user templates.
        """
        self.system_template_name = system_template_name
        self.user_template_name = user_template_name
        self.model_params = model_params
    
    def call(self, **rendering_configs):
        """
        Calls the LLM model with the specified rendering configurations.
        """
        self.messages = utils.compose_initial_LLM_messages_with_templates(self.system_template_name, self.user_template_name, rendering_configs)
        

        # call the LLM model
        self.model_output = client().send_message(self.messages, **self.model_params)

        if 'content' in self.model_output:
            return self.model_output['content']
        else:
            logger.error(f"Model output does not contain 'content' key: {self.model_output}")
            return None


    def __repr__(self):
        return f"LLMCall(messages={self.messages}, model_config={self.model_config}, model_output={self.model_output})"


class InvalidRequestError(Exception):
    """
    Exception raised when the request to the OpenAI API is invalid.
    """
    pass

class NonTerminalError(Exception):
    """
    Exception raised when an unspecified error occurs but we know we can retry.
    """
    pass

_api_type_to_client = {}
_api_type_override = None

def register_client(api_type, client):
    """
    Registers a client for the given API type.

    Args:
    api_type (str): The API type for which we want to register the client.
    client: The client to register.
    """
    _api_type_to_client[api_type] = client

def _get_client_for_api_type(api_type):
    """
    Returns the client for the given API type.

    Args:
    api_type (str): The API type for which we want to get the client.
    """
    try:
        return _api_type_to_client[api_type]
    except KeyError:
        raise ValueError(f"API type {api_type} is not supported. Please check the 'config.ini' file.")

def client():
    """
    Returns the client for the configured API type.
    """
    api_type = config["OpenAI"]["API_TYPE"] if _api_type_override is None else _api_type_override
    
    logger.debug(f"Using  API type {api_type}.")
    return _get_client_for_api_type(api_type)


# TODO simplify the custom configuration methods below

def force_api_type(api_type):
    """
    Forces the use of the given API type, thus overriding any other configuration.

    Args:
    api_type (str): The API type to use.
    """
    global _api_type_override
    _api_type_override = api_type

def force_api_cache(cache_api_calls, cache_file_name=default_params["cache_file_name"]):
    """
    Forces the use of the given API cache configuration, thus overriding any other configuration.

    Args:
    cache_api_calls (bool): Whether to cache API calls.
    cache_file_name (str): The name of the file to use for caching API calls.
    """
    # set the cache parameters on all clients
    for client in _api_type_to_client.values():
        client.set_api_cache(cache_api_calls, cache_file_name)

def force_default_value(key, value):
    """
    Forces the use of the given default configuration value for the specified key, thus overriding any other configuration.

    Args:
    key (str): The key to override.
    value: The value to use for the key.
    """
    global default

    # check if the key actually exists
    if key in default:
        default[key] = value
    else:
        raise ValueError(f"Key {key} is not a valid configuration key.")

# default client
register_client("openai", OpenAIClient())
register_client("azure", AzureClient())